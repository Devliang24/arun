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


class Runner:
    def __init__(self, *, log, failfast: bool = False, log_debug: bool = False) -> None:
        self.log = log
        self.failfast = failfast
        self.log_debug = log_debug
        self.templater = TemplateEngine()

    def _render(self, data: Any, variables: Dict[str, Any], functions: Dict[str, Any] | None = None, envmap: Dict[str, Any] | None = None) -> Any:
        return self.templater.render_value(data, variables, functions, envmap)

    def _build_client(self, case: Case) -> HTTPClient:
        cfg = case.config
        return HTTPClient(base_url=cfg.base_url, timeout=cfg.timeout, verify=cfg.verify, headers=cfg.headers)

    def _request_dict(self, step: Step) -> Dict[str, Any]:
        return step.request.model_dump(exclude_none=True, by_alias=True)

    def _resolve_check(self, check: str, resp: Dict[str, Any]) -> Any:
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
        # default: body.* jmespath
        body = resp.get("body")
        expr = check.split("body.", 1)[1] if check.startswith("body.") else check
        return extract_from_body(body, expr)

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
                if self.log:
                    self.log.info(f"[STEP] Start: {step.name}")
                    # brief request line
                    self.log.info(f"[REQ] {req_rendered.get('method','GET')} {req_rendered.get('url')}")
                    if req_rendered.get("params"):
                        self.log.info(f"[REQ] params: {req_rendered.get('params')}")
                    if req_rendered.get("headers"):
                        self.log.info(f"[REQ] headers: {mask_headers(req_rendered.get('headers'))}")
                    if req_rendered.get("json") is not None:
                        self.log.info(f"[REQ] json: {req_rendered.get('json')}")
                    if req_rendered.get("data") is not None:
                        self.log.info(f"[REQ] data: {req_rendered.get('data')}")

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
                    hdrs = mask_headers(resp_obj.get("headers") or {})
                    self.log.info(f"[RESP] status={resp_obj.get('status_code')} elapsed={resp_obj.get('elapsed_ms'):.1f}ms")
                    self.log.info(f"[RESP] headers: {hdrs}")
                    body_preview = resp_obj.get("body")
                    if isinstance(body_preview, (dict, list)):
                        self.log.info(f"[RESP] body: {str(body_preview)[:1000]}")
                    elif body_preview is not None:
                        self.log.info(f"[RESP] text: {str(body_preview)[:1000]}")

                # assertions
                assertions: List[AssertionResult] = []
                step_failed = False
                for v in step.validators:
                    actual = self._resolve_check(str(v.check), resp_obj)
                    passed, err = compare(v.comparator, actual, v.expect)
                    msg = err
                    if not passed and msg is None:
                        msg = f"Assertion failed: {v.check} {v.comparator} {v.expect!r} (actual={actual!r})"
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
                            self.log.error(f"[VALID] {v.check} {v.comparator} {v.expect!r} => actual={actual!r} | FAIL | {msg}")
                    else:
                        if self.log:
                            self.log.info(f"[VALID] {v.check} {v.comparator} {v.expect!r} => actual={actual!r} | PASS")

                # extracts
                extracts: Dict[str, Any] = {}
                for var, expr in (step.extract or {}).items():
                    extracts[var] = extract_from_body(resp_obj.get("body"), expr)
                    ctx.set(var, extracts[var])
                    if self.log:
                        self.log.info(f"[EXTRACT] {var} = {extracts[var]!r} from {expr}")

                # build result
                masked_headers = mask_headers(resp_obj.get("headers") or {})
                body_masked = mask_body(resp_obj.get("body"))
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
            client.close()

        total_ms = (time.perf_counter() - t0) * 1000.0
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
