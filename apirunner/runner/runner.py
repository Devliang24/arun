from __future__ import annotations

import json
import time
from typing import Any, Dict, List, Optional

from apirunner.engine.http import HTTPClient
from apirunner.models.case import Case
from apirunner.models.report import AssertionResult, CaseInstanceResult, RunReport, StepResult
from apirunner.models.step import Step
from apirunner.templating.context import VarContext
from apirunner.templating.engine import TemplateEngine
from apirunner.runner.extractors import extract_from_body
from apirunner.runner.assertions import compare
from apirunner.utils.curl import to_curl
from apirunner.utils.mask import mask_body, mask_headers
from apirunner.db.mysql_assert import run_mysql_asserts


class Runner:
    def __init__(self, *, log, failfast: bool = False, log_debug: bool = False, reveal_secrets: bool = True) -> None:
        self.log = log
        self.failfast = failfast
        self.log_debug = log_debug
        self.reveal = reveal_secrets
        self.templater = TemplateEngine()

    def _render(self, data: Any, variables: Dict[str, Any], functions: Dict[str, Any] | None = None, envmap: Dict[str, Any] | None = None) -> Any:
        return self.templater.render_value(data, variables, functions, envmap)

    def _build_client(self, case: Case) -> HTTPClient:
        cfg = case.config
        return HTTPClient(base_url=cfg.base_url, timeout=cfg.timeout, verify=cfg.verify, headers=cfg.headers)

    def _request_dict(self, step: Step) -> Dict[str, Any]:
        return step.request.model_dump(exclude_none=True, by_alias=True)

    def _fmt_json(self, obj: Any) -> str:
        try:
            return json.dumps(obj, ensure_ascii=False, indent=2)
        except Exception:
            return str(obj)

    def _fmt_aligned(self, section: str, label: str, text: str) -> str:
        """Return a single string where multiline content is aligned with fixed small indent.

        Example:
        [REQUEST] json: {
          "a": 1,
          "b": 2
        }
        """
        section_label = {
            "REQ": "REQUEST",
            "RESP": "RESPONSE",
        }.get(section, section)
        header = f"[{section_label}] {label}: "
        lines = (text or "").splitlines() or [""]
        if len(lines) == 1:
            return header + lines[0]
        # Use fixed 2-space indent instead of aligning to header length
        pad = "  "
        tail_lines = lines[1:]
        # Calculate minimum leading spaces to preserve relative indentation
        leading_spaces = [len(ln) - len(ln.lstrip(" ")) for ln in tail_lines if ln.strip()]
        trim = min(leading_spaces) if leading_spaces else 0
        adjusted = []
        for ln in tail_lines:
            if ln.strip():
                # Preserve relative indentation by only trimming common prefix
                content = ln[trim:] if trim and len(ln) >= trim else ln
                adjusted.append(pad + content)
            else:
                adjusted.append("")  # Empty lines don't need padding
        return header + lines[0].lstrip() + "\n" + "\n".join(adjusted)

    def _resolve_check(self, check: str, resp: Dict[str, Any]) -> Any:
        # $-style check support
        if isinstance(check, str) and check.strip().startswith("$"):
            return self._eval_extract(check, resp)
        if check == "status_code":
            return resp.get("status_code")
        if check.startswith("headers."):
            key = check.split(".", 1)[1]
            headers = resp.get("headers") or {}
            # HTTP headers are case-insensitive, do case-insensitive lookup
            key_lower = key.lower()
            for h_key, h_val in headers.items():
                if h_key.lower() == key_lower:
                    return h_val
            return None
        # unsupported check format (body.* no longer supported)
        return None

    def _eval_extract(self, expr: Any, resp: Dict[str, Any]) -> Any:
        # Only support string expressions starting with $ (HttpRunner-style)
        if not isinstance(expr, str):
            return None
        e = expr.strip()
        if not e.startswith("$"):
            return None
        if e in ("$", "$body"):
            return resp.get("body")
        if e == "$headers":
            return resp.get("headers")
        if e == "$status_code":
            return resp.get("status_code")
        if e == "$elapsed_ms":
            return resp.get("elapsed_ms")
        if e == "$url":
            return resp.get("url")
        if e == "$method":
            return resp.get("method")
        if e.startswith("$headers."):
            key = e.split(".", 1)[1]
            headers = resp.get("headers") or {}
            key_lower = key.lower()
            for h_key, h_val in headers.items():
                if h_key.lower() == key_lower:
                    return h_val
            return None
        # JSON body via JSONPath-like: $.a.b or $[0].id -> jmespath a.b / [0].id
        body = resp.get("body")
        if e.startswith("$."):
            jexpr = e[2:]
            return extract_from_body(body, jexpr)
        if e.startswith("$["):
            jexpr = e[1:]  # e.g. $[0].id -> [0].id
            return extract_from_body(body, jexpr)
        # Fallback: remove leading $ and try
        return extract_from_body(body, e.lstrip("$"))

    def _run_setup_hooks(self, names: List[str], *, funcs: Dict[str, Any] | None, req: Dict[str, Any], variables: Dict[str, Any], envmap: Dict[str, Any] | None) -> Dict[str, Any]:
        updated: Dict[str, Any] = {}
        fdict = funcs or {}
        for entry in names or []:
            if isinstance(entry, str) and entry.strip().startswith("${"):
                # expression style
                if self.log:
                    self.log.info(f"[HOOK] setup expr -> {entry}")
                import re as _re
                m = _re.match(r"^\$\{\s*([A-Za-z_][A-Za-z0-9_]*)", entry.strip())
                if not (m and m.group(1).startswith("setup_hook_")):
                    raise ValueError(f"setup hook function in expression must start with 'setup_hook_': {entry}")
                ret = self.templater.eval_expr(entry, variables, fdict, envmap, extra_ctx={"request": req, "variables": variables, "env": envmap})
            else:
                # function name style
                name = entry
                # enforce naming convention
                if not (isinstance(name, str) and name.startswith("setup_hook_")):
                    raise ValueError(f"setup hook function name must start with 'setup_hook_': {name}")
                fn = fdict.get(name)
                if not callable(fn):
                    if self.log:
                        self.log.error(f"[HOOK] setup '{name}' not found")
                    continue
                if self.log:
                    self.log.info(f"[HOOK] setup -> {name}()")
                ret = fn(request=req, variables=variables, env=envmap)
            if isinstance(ret, dict):
                updated.update(ret)
        return updated

    def _run_teardown_hooks(self, names: List[str], *, funcs: Dict[str, Any] | None, resp: Dict[str, Any], variables: Dict[str, Any], envmap: Dict[str, Any] | None) -> Dict[str, Any]:
        updated: Dict[str, Any] = {}
        fdict = funcs or {}
        for entry in names or []:
            if isinstance(entry, str) and entry.strip().startswith("${"):
                if self.log:
                    self.log.info(f"[HOOK] teardown expr -> {entry}")
                import re as _re
                m = _re.match(r"^\$\{\s*([A-Za-z_][A-Za-z0-9_]*)", entry.strip())
                if not (m and m.group(1).startswith("teardown_hook_")):
                    raise ValueError(f"teardown hook function in expression must start with 'teardown_hook_': {entry}")
                ret = self.templater.eval_expr(entry, variables, fdict, envmap, extra_ctx={"response": resp, "variables": variables, "env": envmap})
            else:
                name = entry
                if not (isinstance(name, str) and name.startswith("teardown_hook_")):
                    raise ValueError(f"teardown hook function name must start with 'teardown_hook_': {name}")
                fn = fdict.get(name)
                if not callable(fn):
                    if self.log:
                        self.log.error(f"[HOOK] teardown '{name}' not found")
                    continue
                if self.log:
                    self.log.info(f"[HOOK] teardown -> {name}()")
                ret = fn(response=resp, variables=variables, env=envmap)
            if isinstance(ret, dict):
                updated.update(ret)
        return updated

    def run_case(self, case: Case, global_vars: Dict[str, Any], params: Dict[str, Any], *, funcs: Dict[str, Any] | None = None, envmap: Dict[str, Any] | None = None) -> CaseInstanceResult:
        name = case.config.name or "Unnamed Case"
        t0 = time.perf_counter()
        steps_results: List[StepResult] = []
        status = "passed"

        # Evaluate case-level variables once to fix values across steps
        base_vars_raw: Dict[str, Any] = {**(case.config.variables or {}), **(params or {})}
        rendered_base = self._render(base_vars_raw, {}, funcs, envmap)
        if not isinstance(rendered_base, dict):
            rendered_base = base_vars_raw
        ctx = VarContext(rendered_base)
        client = self._build_client(case)

        try:
            # Suite + Case setup hooks
            try:
                # suite-level
                if getattr(case, "suite_setup_hooks", None):
                    new_vars_suite = self._run_setup_hooks(case.suite_setup_hooks, funcs=funcs, req={}, variables={}, envmap=envmap)
                    for k, v in (new_vars_suite or {}).items():
                        ctx.set_base(k, v)
                        if self.log:
                            self.log.info(f"[HOOK] suite set var: {k} = {v!r}")
                # case-level
                if getattr(case, "setup_hooks", None):
                    new_vars_case = self._run_setup_hooks(case.setup_hooks, funcs=funcs, req={}, variables={}, envmap=envmap)
                    for k, v in (new_vars_case or {}).items():
                        ctx.set_base(k, v)
                        if self.log:
                            self.log.info(f"[HOOK] case set var: {k} = {v!r}")
            except Exception as e:
                status = "failed"
                steps_results.append(StepResult(name="case setup hooks", status="failed", error=f"{e}"))
                raise

            for step in case.steps:
                # skip handling
                if step.skip:
                    if self.log:
                        self.log.info(f"[STEP] Skip: {step.name} | reason={step.skip}")
                    steps_results.append(StepResult(name=step.name, status="skipped"))
                    continue

                # variables: case -> step -> CLI/global overrides
                ctx.push(step.variables)
                variables = ctx.get_merged(global_vars)
                # render step-level variables so expressions like ${token} inside values are resolved
                rendered_locals = self._render(step.variables, variables, funcs, envmap)
                ctx.pop()
                ctx.push(rendered_locals if isinstance(rendered_locals, dict) else (step.variables or {}))
                variables = ctx.get_merged(global_vars)

                # render request
                req_dict = self._request_dict(step)
                req_rendered = self._render(req_dict, variables, funcs, envmap)
                # run setup hooks (mutation allowed)
                try:
                    new_vars = self._run_setup_hooks(step.setup_hooks, funcs=funcs, req=req_rendered, variables=variables, envmap=envmap)
                    for k, v in (new_vars or {}).items():
                        ctx.set_base(k, v)
                        if self.log:
                            self.log.info(f"[HOOK] set var: {k} = {v!r}")
                    variables = ctx.get_merged(global_vars)
                except Exception as e:
                    status = "failed"
                    if self.log:
                        self.log.error(f"[HOOK] setup error: {e}")
                    steps_results.append(StepResult(name=step.name, status="failed", error=f"setup hook error: {e}"))
                    if self.failfast:
                        break
                    ctx.pop()
                    continue
                # sanitize headers to avoid illegal values (e.g., Bearer <empty>)
                if isinstance(req_rendered.get("headers"), dict):
                    headers = dict(req_rendered["headers"])  # type: ignore[index]
                    for hk, hv in list(headers.items()):
                        if hv is None:
                            headers.pop(hk, None)
                        elif isinstance(hv, str) and (hv.strip() == "" or hv.strip().lower() in {"bearer", "bearer none"}):
                            headers.pop(hk, None)
                    req_rendered["headers"] = headers
                # Auto-inject Authorization if token is available and no header set
                if (not (isinstance(req_rendered.get("headers"), dict) and any(k.lower()=="authorization" for k in req_rendered["headers"]))):
                    tok = variables.get("token") if isinstance(variables, dict) else None
                    if isinstance(tok, str) and tok.strip():
                        hdrs = dict(req_rendered.get("headers") or {})
                        hdrs["Authorization"] = f"Bearer {tok}"
                        req_rendered["headers"] = hdrs

                if self.log:
                    self.log.info(f"[STEP] Start: {step.name}")
                    # brief request line
                    self.log.info(f"[REQUEST] {req_rendered.get('method','GET')} {req_rendered.get('url')}")
                    if req_rendered.get("params") is not None:
                        self.log.info(self._fmt_aligned("REQ", "params", self._fmt_json(req_rendered.get("params"))))
                    if req_rendered.get("headers"):
                        hdrs_out = req_rendered.get("headers")
                        if not self.reveal:
                            hdrs_out = mask_headers(hdrs_out)
                        self.log.info(self._fmt_aligned("REQ", "headers", self._fmt_json(hdrs_out)))
                    if req_rendered.get("json") is not None:
                        body = req_rendered.get("json")
                        if isinstance(body, (dict, list)) and not self.reveal:
                            body = mask_body(body)
                        self.log.info(self._fmt_aligned("REQ", "json", self._fmt_json(body)))
                    if req_rendered.get("data") is not None:
                        data = req_rendered.get("data")
                        if isinstance(data, (dict, list)) and not self.reveal:
                            data = mask_body(data)
                        self.log.info(self._fmt_aligned("REQ", "data", self._fmt_json(data)))

                # send with retry
                last_error: Optional[str] = None
                attempt = 0
                resp_obj: Optional[Dict[str, Any]] = None
                while attempt <= max(step.retry, 0):
                    try:
                        resp_obj = client.request(req_rendered)
                        last_error = None
                        break
                    except Exception as e:
                        last_error = str(e)
                        if attempt >= step.retry:
                            break
                        backoff = min(step.retry_backoff * (2 ** attempt), 2.0)
                        time.sleep(backoff)
                        attempt += 1

                if last_error:
                    status = "failed"
                    if self.log:
                        self.log.error(f"[STEP] Request error: {last_error}")
                    steps_results.append(
                        StepResult(
                            name=step.name,
                            status="failed",
                            error=f"Request error: {last_error}",
                        )
                    )
                    if self.failfast:
                        break
                    ctx.pop()
                    continue

                assert resp_obj is not None
                if self.log:
                    hdrs = resp_obj.get("headers") or {}
                    if not self.reveal:
                        hdrs = mask_headers(hdrs)
                    self.log.info(f"[RESPONSE] status={resp_obj.get('status_code')} elapsed={resp_obj.get('elapsed_ms'):.1f}ms")
                    self.log.info(self._fmt_aligned("RESP", "headers", self._fmt_json(hdrs)))
                    body_preview = resp_obj.get("body")
                    if isinstance(body_preview, (dict, list)):
                        out_body = body_preview
                        if not self.reveal:
                            out_body = mask_body(out_body)
                        self.log.info(self._fmt_aligned("RESP", "body", self._fmt_json(out_body)))
                    elif body_preview is not None:
                        text = str(body_preview)
                        if len(text) > 2000:
                            text = text[:2000] + "..."
                        self.log.info(self._fmt_aligned("RESP", "text", text))

                # assertions
                assertions: List[AssertionResult] = []
                step_failed = False
                for v in step.validators:
                    actual = self._resolve_check(str(v.check), resp_obj)
                    passed, err = compare(v.comparator, actual, v.expect)
                    msg = err
                    if not passed and msg is None:
                        addon = ""
                        if isinstance(v.check, str) and v.check.startswith("body."):
                            addon = " | unsupported 'body.' syntax; use '$' (e.g., $.path.to.field)"
                        msg = f"Assertion failed: {v.check} {v.comparator} {v.expect!r} (actual={actual!r}){addon}"
                    assertions.append(
                        AssertionResult(
                            check=str(v.check),
                            comparator=v.comparator,
                            expect=v.expect,
                            actual=actual,
                            passed=bool(passed),
                            message=msg,
                        )
                    )
                    if not passed:
                        step_failed = True
                        if self.log:
                            self.log.error(f"[VALIDATION] {v.check} {v.comparator} {v.expect!r} => actual={actual!r} | FAIL | {msg}")
                    else:
                        if self.log:
                            self.log.info(f"[VALIDATION] {v.check} {v.comparator} {v.expect!r} => actual={actual!r} | PASS")

                if step.mysql_asserts:
                    mysql_updates_total: Dict[str, Any] = {}
                    temp_vars = dict(variables)
                    for idx, mysql_cfg in enumerate(step.mysql_asserts):
                        try:
                            rendered_cfg = self._render(mysql_cfg.model_dump(), temp_vars, funcs, envmap)
                        except Exception as e:
                            step_failed = True
                            err_msg = f"MySQL assert render error: {e}"
                            assertions.append(
                                AssertionResult(
                                    check=f"mysql.config[{idx}]",
                                    comparator="render",
                                    expect=None,
                                    actual=None,
                                    passed=False,
                                    message=err_msg,
                                )
                            )
                            if self.log:
                                self.log.error(f"[MYSQL] render error: {e}")
                            continue
                        try:
                            mysql_results, mysql_updates = run_mysql_asserts(
                                [rendered_cfg],
                                response=resp_obj,
                                variables=temp_vars,
                                env=envmap or {},
                                render=None,
                                logger=self.log,
                            )
                        except Exception as e:
                            step_failed = True
                            err_msg = f"MySQL assert error: {e}"
                            assertions.append(
                                AssertionResult(
                                    check=f"mysql.exec[{idx}]",
                                    comparator="execute",
                                    expect=None,
                                    actual=None,
                                    passed=False,
                                    message=err_msg,
                                )
                            )
                            if self.log:
                                self.log.error(f"[MYSQL] execution error: {e}")
                            continue
                        for res in mysql_results:
                            assertions.append(res)
                            if not res.passed:
                                step_failed = True
                        mysql_updates_total.update(mysql_updates)
                        temp_vars.update(mysql_updates)
                    if mysql_updates_total:
                        for k, v in mysql_updates_total.items():
                            ctx.set_base(k, v)
                            if self.log:
                                self.log.info(f"[MYSQL] set var: {k} = {v!r}")
                        variables = ctx.get_merged(global_vars)

                # extracts ($-only syntax)
                extracts: Dict[str, Any] = {}
                for var, expr in (step.extract or {}).items():
                    val = self._eval_extract(expr, resp_obj)
                    extracts[var] = val
                    ctx.set_base(var, val)
                    if self.log:
                        self.log.info(f"[EXTRACT] {var} = {val!r} from {expr}")

                # teardown hooks
                try:
                    new_vars_td = self._run_teardown_hooks(step.teardown_hooks, funcs=funcs, resp=resp_obj, variables=variables, envmap=envmap)
                    for k, v in (new_vars_td or {}).items():
                        ctx.set_base(k, v)
                        if self.log:
                            self.log.info(f"[HOOK] set var: {k} = {v!r}")
                    variables = ctx.get_merged(global_vars)
                except Exception as e:
                    step_failed = True
                    if self.log:
                        self.log.error(f"[HOOK] teardown error: {e}")

                # build result
                masked_headers = resp_obj.get("headers") or {}
                body_masked = resp_obj.get("body")
                if not self.reveal:
                    masked_headers = mask_headers(masked_headers)
                    body_masked = mask_body(body_masked)
                curl = None
                if self.log_debug:
                    url_rendered = resp_obj.get("url") or req_rendered.get("url")
                    curl = to_curl(req_rendered.get("method", "GET"), url_rendered, headers=req_rendered.get("headers"), data=req_rendered.get("json") or req_rendered.get("data"))
                    self.log.debug("cURL: %s", curl)

                sr = StepResult(
                    name=step.name,
                    status="failed" if step_failed else "passed",
                    request={
                        k: v for k, v in req_rendered.items() if k in ("method", "url", "params", "headers", "json", "data")
                    },
                    response={
                        "status_code": resp_obj.get("status_code"),
                        "headers": masked_headers,
                        "body": body_masked if isinstance(body_masked, (dict, list)) else (str(body_masked)[:2048] if body_masked else None),
                    },
                    asserts=assertions,
                    extracts=extracts,
                    duration_ms=resp_obj.get("elapsed_ms") or 0.0,
                )
                steps_results.append(sr)
                if step_failed:
                    status = "failed"
                    if self.log:
                        self.log.error(f"[STEP] Result: {step.name} | FAILED")
                    if self.failfast:
                        ctx.pop()
                        break
                else:
                    if self.log:
                        self.log.info(f"[STEP] Result: {step.name} | PASSED")
                ctx.pop()

        finally:
            # Suite + Case teardown hooks (best-effort)
            try:
                if getattr(case, "teardown_hooks", None):
                    _ = self._run_teardown_hooks(case.teardown_hooks, funcs=funcs, resp={}, variables=ctx.get_merged(global_vars), envmap=envmap)
                if getattr(case, "suite_teardown_hooks", None):
                    _ = self._run_teardown_hooks(case.suite_teardown_hooks, funcs=funcs, resp={}, variables=ctx.get_merged(global_vars), envmap=envmap)
            except Exception as e:
                steps_results.append(StepResult(name="case teardown hooks", status="failed", error=f"{e}"))
            client.close()

        total_ms = (time.perf_counter() - t0) * 1000.0

        # Final validation: ensure if any step failed, the case is marked as failed
        if any(sr.status == "failed" for sr in steps_results):
            status = "failed"

        return CaseInstanceResult(name=name, parameters=params or {}, steps=steps_results, status=status, duration_ms=total_ms)

    def build_report(self, results: List[CaseInstanceResult]) -> RunReport:
        total = len(results)
        failed = sum(1 for r in results if r.status == "failed")
        skipped = sum(1 for r in results if r.status == "skipped")
        passed = total - failed - skipped
        duration = sum(r.duration_ms for r in results)
        return RunReport(
            summary={"total": total, "passed": passed, "failed": failed, "skipped": skipped, "duration_ms": duration},
            cases=results,
        )
