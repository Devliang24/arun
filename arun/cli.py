from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import typer
import yaml

from arun.loader.collector import discover, match_tags
from arun.loader.yaml_loader import expand_parameters, load_yaml_file
from arun.loader.hooks import get_functions_for
from arun.loader.env import load_environment
from arun.models.case import Case
from arun.models.report import RunReport
from arun.reporter.json_reporter import write_json
from arun.runner.runner import Runner
from arun.templating.engine import TemplateEngine
from arun.utils.logging import setup_logging, get_logger
import time


app = typer.Typer(add_completion=False, help="ARun · Zero-code HTTP API test framework", rich_markup_mode=None)
import_app = typer.Typer()
export_app = typer.Typer()
app.add_typer(import_app, name="import")
app.add_typer(export_app, name="export")

# Importers / exporters (lazy optional imports inside functions where needed)


def _emit_tag_list(tags: set[str], case_count: int) -> None:
    """Pretty-print collected tag information."""
    if not tags:
        typer.echo(f"No tags defined in {case_count} cases.")
        return
    typer.echo(f"Cases scanned: {case_count}")
    typer.echo("Tags:")
    for tag in sorted(tags):
        typer.echo(f"  - {tag}")


def parse_kv(items: List[str]) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for it in items:
        if "=" not in it:
            continue
        k, v = it.split("=", 1)
        out[k] = v
    return out


def load_env_file(path: Optional[str]) -> Dict[str, str]:
    # Kept for backward compat; now handled in load_environment
    if not path:
        return {}
    p = Path(path)
    if not p.exists():
        return {}
    # fallback simple parser
    data: Dict[str, str] = {}
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            k, v = line.split("=", 1)
            data[k.strip()] = v.strip()
    return data


def _to_yaml_case_dict(case: Case) -> Dict[str, object]:
    # Dump with aliases and prune fields loader forbids at top-level.
    d = case.model_dump(by_alias=True, exclude_none=True)
    for k in ("setup_hooks", "teardown_hooks", "suite_setup_hooks", "suite_teardown_hooks"):
        if k in d and not d.get(k):
            d.pop(k, None)
    return d


@import_app.command("curl")
def import_curl(
    infile: str = typer.Argument(..., help="Path to file with curl commands or '-' for stdin"),
    outfile: Optional[str] = typer.Option(None, "--outfile", help="Write to new YAML file (default stdout)"),
    into: Optional[str] = typer.Option(None, "--into", help="Append into existing YAML (case or suite)"),
    case_name: Optional[str] = typer.Option(None, "--case-name", help="Case name; default 'Imported Case'"),
    base_url: Optional[str] = typer.Option(None, "--base-url", help="Override base_url in generated case"),
) -> None:
    from arun.importers.curl import parse_curl_text
    from arun.models.case import Case
    from arun.models.config import Config
    from arun.models.step import Step
    from arun.models.request import StepRequest

    # Read input
    if infile == "-":
        text = typer.get_text_stream("stdin").read()
    else:
        # Enforce .curl suffix for curl files
        pth = Path(infile)
        if pth.suffix.lower() != ".curl":
            typer.echo(f"[IMPORT] Refusing to read '{infile}': curl file must have '.curl' suffix.")
            raise typer.Exit(code=2)
        text = pth.read_text(encoding="utf-8")

    icase = parse_curl_text(text, case_name=case_name, base_url=base_url)

    steps: List[Step] = []
    for s in icase.steps:
        req = StepRequest(
            method=s.method,
            url=s.url,
            params=s.params,
            headers=s.headers,
            body=s.body,
            data=s.data,
            files=s.files,
            auth=s.auth,
        )
        step = Step(name=s.name, request=req, validate=[{"eq": ["status_code", 200]}])
        steps.append(step)

    case = Case(config=Config(name=icase.name, base_url=icase.base_url), steps=steps)
    out_dict = _to_yaml_case_dict(case)

    import yaml as _yaml

    def _dump(obj: Dict[str, object]) -> str:
        return _yaml.safe_dump(obj, allow_unicode=True, sort_keys=False)

    if into:
        # Append into existing YAML
        p = Path(into)
        if not p.exists():
            p.write_text(_dump(out_dict), encoding="utf-8")
            typer.echo(f"[IMPORT] Created new case file: {into}")
            return
        data = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if "config" in data and "steps" in data:
            # case file
            steps_existing = data.get("steps") or []
            steps_existing.extend(out_dict.get("steps") or [])
            data["steps"] = steps_existing
            p.write_text(_dump(data), encoding="utf-8")
            typer.echo(f"[IMPORT] Appended {len(out_dict.get('steps', []))} steps into case: {into}")
            return
        elif "cases" in data:
            cases = data.get("cases") or []
            cases.append(out_dict)
            data["cases"] = cases
            p.write_text(_dump(data), encoding="utf-8")
            typer.echo(f"[IMPORT] Added case into suite: {into}")
            return
        else:
            # Unknown structure -> overwrite or error. Choose overwrite for simplicity.
            p.write_text(_dump(out_dict), encoding="utf-8")
            typer.echo(f"[IMPORT] Replaced file with generated case: {into}")
            return

    # Write to outfile or stdout
    s = _dump(out_dict)
    if outfile:
        Path(outfile).write_text(s, encoding="utf-8")
        typer.echo(f"[IMPORT] Wrote YAML to {outfile}")
    else:
        typer.echo(s)


@import_app.command("postman")
def import_postman(
    collection: str = typer.Argument(..., help="Postman collection v2 JSON file"),
    outfile: Optional[str] = typer.Option(None, "--outfile"),
    into: Optional[str] = typer.Option(None, "--into"),
    case_name: Optional[str] = typer.Option(None, "--case-name"),
    base_url: Optional[str] = typer.Option(None, "--base-url"),
) -> None:
    from arun.importers.postman import parse_postman
    from arun.models.case import Case
    from arun.models.config import Config
    from arun.models.step import Step
    from arun.models.request import StepRequest
    import yaml as _yaml

    text = Path(collection).read_text(encoding="utf-8")
    icase = parse_postman(text, case_name=case_name, base_url=base_url)

    steps: List[Step] = []
    for s in icase.steps:
        req = StepRequest(method=s.method, url=s.url, params=s.params, headers=s.headers, body=s.body, data=s.data)
        steps.append(Step(name=s.name, request=req, validate=[{"eq": ["status_code", 200]}]))

    case = Case(config=Config(name=icase.name, base_url=icase.base_url), steps=steps)
    out_dict = _to_yaml_case_dict(case)
    out_text = _yaml.safe_dump(out_dict, allow_unicode=True, sort_keys=False)
    if into:
        p = Path(into)
        if p.exists():
            data = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if "config" in data and "steps" in data:
                data["steps"] = (data.get("steps") or []) + (out_dict.get("steps") or [])
            elif "cases" in data:
                data["cases"] = (data.get("cases") or []) + [out_dict]
            else:
                data = out_dict
            p.write_text(_yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            typer.echo(f"[IMPORT] Appended into {into}")
            return
    if outfile:
        Path(outfile).write_text(out_text, encoding="utf-8")
        typer.echo(f"[IMPORT] Wrote YAML to {outfile}")
    else:
        typer.echo(out_text)


@import_app.command("har")
def import_har(
    harfile: str = typer.Argument(..., help="HAR file to import"),
    outfile: Optional[str] = typer.Option(None, "--outfile"),
    into: Optional[str] = typer.Option(None, "--into"),
    case_name: Optional[str] = typer.Option(None, "--case-name"),
    base_url: Optional[str] = typer.Option(None, "--base-url"),
) -> None:
    from arun.importers.har import parse_har
    from arun.models.case import Case
    from arun.models.config import Config
    from arun.models.step import Step
    from arun.models.request import StepRequest
    import yaml as _yaml

    text = Path(harfile).read_text(encoding="utf-8")
    icase = parse_har(text, case_name=case_name, base_url=base_url)
    steps: List[Step] = []
    for s in icase.steps:
        req = StepRequest(method=s.method, url=s.url, params=s.params, headers=s.headers, body=s.body, data=s.data)
        steps.append(Step(name=s.name, request=req, validate=[{"eq": ["status_code", 200]}]))
    case = Case(config=Config(name=icase.name, base_url=icase.base_url), steps=steps)
    out_dict = _to_yaml_case_dict(case)
    out_text = _yaml.safe_dump(out_dict, allow_unicode=True, sort_keys=False)
    if into:
        p = Path(into)
        if p.exists():
            data = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}
            if "config" in data and "steps" in data:
                data["steps"] = (data.get("steps") or []) + (out_dict.get("steps") or [])
            elif "cases" in data:
                data["cases"] = (data.get("cases") or []) + [out_dict]
            else:
                data = out_dict
            p.write_text(_yaml.safe_dump(data, allow_unicode=True, sort_keys=False), encoding="utf-8")
            typer.echo(f"[IMPORT] Appended into {into}")
            return
    if outfile:
        Path(outfile).write_text(out_text, encoding="utf-8")
        typer.echo(f"[IMPORT] Wrote YAML to {outfile}")
    else:
        typer.echo(out_text)
@export_app.command("curl")
def export_curl(
    path: str = typer.Argument(..., help="Case/Suite YAML file or directory to export"),
    case_name: Optional[str] = typer.Option(None, "--case-name", help="Only export a specific case name"),
    steps: Optional[str] = typer.Option(None, "--steps", help="Step indexes, e.g., '1,3-5' (1-based)"),
    multiline: bool = typer.Option(False, "--multiline/--one-line", help="Format curl on multiple lines with continuations"),
    shell: str = typer.Option("sh", "--shell", help="Line continuation style: sh|ps"),
    redact: Optional[str] = typer.Option(None, "--redact", help="Comma-separated header names to mask, e.g., Authorization,Cookie"),
    with_comments: bool = typer.Option(True, "--with-comments/--no-comments", help="Prepend '# Case/Step' comments to each curl"),
    outfile: Optional[str] = typer.Option(None, "--outfile", help="Write output to file (must end with .curl when provided)"),
) -> None:
    from arun.exporters.curl import case_to_curls, step_to_curl, step_placeholders
    out_lines: List[str] = []

    files: List[str] = []
    p = Path(path)
    if p.is_dir():
        from arun.loader.collector import discover
        files = discover([path])
    else:
        files = [path]

    def parse_steps_spec(spec: Optional[str], maxn: int) -> List[int]:
        if not spec:
            return list(range(maxn))
        out: List[int] = []
        for part in spec.split(','):
            part = part.strip()
            if not part:
                continue
            if '-' in part:
                a, b = part.split('-', 1)
                try:
                    ia = max(1, int(a))
                    ib = min(maxn, int(b))
                except Exception:
                    continue
                out.extend(list(range(ia-1, ib)))
            else:
                try:
                    i = int(part)
                    if 1 <= i <= maxn:
                        out.append(i-1)
                except Exception:
                    pass
        # dedupe preserve order
        seen=set(); res=[]
        for i in out:
            if i not in seen:
                res.append(i); seen.add(i)
        return res

    redact_list = [x.strip() for x in (redact or '').split(',') if x.strip()]

    if outfile and not outfile.lower().endswith('.curl'):
        typer.echo(f"[EXPORT] Outfile must end with '.curl': {outfile}")
        raise typer.Exit(code=2)

    from pathlib import Path as _Path
    for f in files:
        cases, _meta = load_yaml_file(_Path(f))
        if case_name:
            cases = [c for c in cases if (c.config.name or "") == case_name]
        for c in cases:
            idxs = parse_steps_spec(steps, len(c.steps))
            for j, idx in enumerate(idxs, start=1):
                if with_comments:
                    cname = c.config.name or 'Unnamed'
                    sname = c.steps[idx].name or f"Step {idx+1}"
                    out_lines.append(f"# Case: {cname} | Step {idx+1}: {sname}")
                    # Add placeholder annotations such as $token or ${...}
                    vars_set, exprs_set = step_placeholders(c, idx)
                    if vars_set:
                        out_lines.append("# Vars: " + " ".join(sorted(vars_set)))
                    if exprs_set:
                        out_lines.append("# Exprs: " + " ".join(sorted(exprs_set)))
                out_lines.append(step_to_curl(c, idx, multiline=multiline, shell=shell, redact=redact_list))

    output = "\n\n".join(out_lines)
    if outfile:
        Path(outfile).write_text(output, encoding="utf-8")
        typer.echo(f"[EXPORT] Wrote {len(out_lines)} curl commands to {outfile}")
    else:
        typer.echo(output)
@app.command("tags")
def list_tags(
    path: str = typer.Argument("testcases", help="File or directory to scan for YAML test cases"),
) -> None:
    """List all unique tags used by the discovered test cases."""
    files = discover([path])
    if not files:
        typer.echo("No YAML test files found.")
        raise typer.Exit(code=2)

    collected: Dict[str, set[tuple[str, str]]] = {}
    case_count = 0
    diagnostics: List[str] = []

    for f in files:
        try:
            cases, _meta = load_yaml_file(f)
        except Exception as exc:  # pragma: no cover - defensive
            diagnostics.append(f"[WARN] Failed to parse {f}: {exc}")
            continue
        if not cases:
            diagnostics.append(f"[INFO] No cases found in {f}")
            continue
        diagnostics.append(f"[OK] {f} -> {len(cases)} cases")
        for c in cases:
            case_count += 1
            tags = c.config.tags or []
            case_name = c.config.name or "Unnamed"
            entry = (case_name, str(f))
            if not tags:
                collected.setdefault("<no-tag>", set()).add(entry)
            for tag in tags:
                collected.setdefault(tag, set()).add(entry)

    for line in diagnostics:
        typer.echo(line)
    # Detailed tag summary
    typer.echo("\nTag Summary:")
    for tag, cases_for_tag in sorted(collected.items(), key=lambda item: item[0]):
        typer.echo(f"- {tag}: {len(cases_for_tag)} cases")
        for case_name, case_path in sorted(cases_for_tag):
            typer.echo(f"    • {case_name} -> {case_path}")


@app.command()
def run(
    path: str = typer.Argument(..., help="File or directory to run"),
    k: Optional[str] = typer.Option(None, "-k", help="Tag filter expression (and/or/not)"),
    vars: List[str] = typer.Option([], "--vars", help="Variable overrides k=v (repeatable)"),
    failfast: bool = typer.Option(False, "--failfast", help="Stop on first failure"),
    report: Optional[str] = typer.Option(None, "--report", help="Write JSON report to file"),
    html: Optional[str] = typer.Option(None, "--html", help="Write HTML report to file (default reports/report-<timestamp>.html)"),
    allure_results: Optional[str] = typer.Option(None, "--allure-results", help="Write Allure results to directory (for allure generate)"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
    env_file: Optional[str] = typer.Option(None, "--env-file", help=".env file path (default .env)"),
    log_file: Optional[str] = typer.Option(None, "--log-file", help="Write console logs to file (default logs/run-<ts>.log)"),
    httpx_logs: bool = typer.Option(False, "--httpx-logs/--no-httpx-logs", help="Show httpx internal request logs", show_default=False),
    reveal_secrets: bool = typer.Option(True, "--reveal-secrets/--mask-secrets", help="Show sensitive fields (password, tokens) in plaintext logs and reports", show_default=True),
    notify: Optional[str] = typer.Option(None, "--notify", help="Notify channels, comma-separated: feishu,email,dingtalk"),
    notify_only: str = typer.Option("failed", "--notify-only", help="Notify policy: failed|always"),
    notify_attach_html: bool = typer.Option(False, "--notify-attach-html/--no-notify-attach-html", help="Attach HTML report in email (if email enabled)", show_default=False),
):
    # default log file path
    ts = time.strftime("%Y%m%d-%H%M%S")
    default_log = log_file or f"logs/run-{ts}.log"
    setup_logging(log_level, log_file=default_log)
    log = get_logger("arun.cli")
    # unify httpx logs: default suppress, unless enabled
    import logging as _logging
    _httpx_logger = _logging.getLogger("httpx")
    _httpx_logger.setLevel(_logging.INFO if httpx_logs else _logging.WARNING)

    # Default env file (.env) when not provided
    env_file_explicit = env_file is not None
    env_file = env_file or ".env"
    if not env_file_explicit:
        log.info(f"[ENV] Using default env file: {env_file}")

    # Global variables from env file and CLI overrides
    # Unified env loading: --env <name> YAML + --env-file (kv or yaml) + OS ENV
    env_name: Optional[str] = os.environ.get("ARUN_ENV")  # optional default via env var
    env_store = load_environment(env_name, env_file)
    # Preflight: warn when default env file is missing and no BASE_URL provided anywhere
    from pathlib import Path as _Path
    _env_exists = _Path(env_file).exists() if env_file else False
    _base_any = os.environ.get("BASE_URL") or os.environ.get("base_url") or None
    if not _base_any:
        _base_any = env_store.get("BASE_URL") or env_store.get("base_url")
    if (not _env_exists) and (not env_file_explicit) and (not _base_any):
        log.warning(
            "[ENV] Default .env not found and BASE_URL is missing. Relative URLs may fail. "
            "Create a .env or pass --env-file/--vars. Example .env:\n"
            "BASE_URL=http://localhost:8000\nUSER_USERNAME=test_user\nUSER_PASSWORD=test_pass\nSHIPPING_ADDRESS=Test Address"
        )
    cli_vars = parse_kv(vars)
    # Only CLI --vars go into templating variables directly
    global_vars: Dict[str, str] = {}
    for k2, v2 in cli_vars.items():
        global_vars[k2] = v2
        global_vars[k2.lower()] = v2

    # Workaround: some environments leak env keys into -k unexpectedly; neutralize if k equals a known env key
    if k and k in (set(env_store.keys()) | {kk.lower() for kk in env_store.keys()}):
        # only override when it's clearly an env key, not an actual filter
        k = None
    # Discover files
    typer.echo(f"Filter expression: {k!r}")
    files = discover([path])
    if not files:
        typer.echo("No YAML test files found.")
        raise typer.Exit(code=2)

    # Load cases
    items: List[tuple[Case, Dict[str, str]]] = []
    debug_info: List[str] = []
    for f in files:
        loaded, meta = load_yaml_file(f)
        debug_info.append(f"file={f} cases={len(loaded)}")
        # tag filter on case level
        for c in loaded:
            tags = c.config.tags or []
            m = match_tags(tags, k)
            debug_info.append(f"  case={c.config.name!r} tags={tags} match={m}")
            if m:
                items.append((c, meta))

    if not items:
        typer.echo("No cases matched tag expression.")
        # extra diagnostics
        for line in debug_info:
            typer.echo(line)
        raise typer.Exit(code=2)

    # Execute
    runner = Runner(log=log, failfast=failfast, log_debug=(log_level.upper() == "DEBUG"), reveal_secrets=reveal_secrets)
    templater = TemplateEngine()
    instance_results = []
    log.info(f"[RUN] Discovered files: {len(files)} | Matched cases: {len(items)} | Failfast={failfast}")
    # Sanity check: ensure cases with relative step URLs have a base_url from any source
    def _need_base_url(case: Case) -> bool:
        try:
            for st in case.steps:
                u = (st.request.url or "").strip()
                # if not absolute (no scheme), we treat it as relative and require base_url
                if not (u.startswith("http://") or u.startswith("https://")):
                    return True
            return False
        except Exception:
            return False

    for c, meta in items:
        funcs = get_functions_for(Path(meta.get("file", path)).resolve())
        param_sets = expand_parameters(c.parameters)
        for ps in param_sets:
            # Promote BASE_URL to base_url if not set
            if (not c.config.base_url) and (base := global_vars.get("BASE_URL") or global_vars.get("base_url") or env_store.get("BASE_URL") or env_store.get("base_url")):
                c.config.base_url = base
            # Render base_url if it contains template syntax
            if c.config.base_url and ("{{" in c.config.base_url or "${" in c.config.base_url):
                c.config.base_url = templater.render_value(c.config.base_url, global_vars, funcs, envmap=env_store)
            # If case has relative URLs but still no base_url after all sources, print a clear guidance and exit
            if _need_base_url(c) and not (c.config.base_url and str(c.config.base_url).strip()):
                msg_lines = [
                    "[ERROR] base_url is required for cases using relative URLs.",
                    f"        Case: {c.config.name or 'Unnamed'} | Source: {meta.get('file', path)}",
                    "        Provide base_url in one of the following ways:",
                    f"          - Create an env file: {env_file} (recommended)",
                    "              BASE_URL=http://localhost:8000",
                    "              USER_USERNAME=test_user",
                    "              USER_PASSWORD=test_pass",
                    "              SHIPPING_ADDRESS=Test Address",
                    "          - Or pass CLI vars: --vars base_url=http://localhost:8000",
                    "          - Or export env:   export BASE_URL=http://localhost:8000",
                    "        Tip: use --env-file <path> to specify a different env file.",
                ]
                for line in msg_lines:
                    typer.echo(line)
                raise typer.Exit(code=2)
            log.info(f"[CASE] Start: {c.config.name or 'Unnamed'} | params={ps}")
            res = runner.run_case(c, global_vars=global_vars, params=ps, funcs=funcs, envmap=env_store, source=meta.get("file"))
            log.info(f"[CASE] Result: {res.name} | status={res.status} | duration={res.duration_ms:.1f}ms")
            instance_results.append(res)
            if failfast and res.status == "failed":
                break

    report_obj: RunReport = runner.build_report(instance_results)
    # Print summary (standardized log format)
    s = report_obj.summary
    log.info(
        "[CASE] Total: %s Passed: %s Failed: %s Skipped: %s Duration: %.1fms",
        s["total"], s.get("passed", 0), s.get("failed", 0), s.get("skipped", 0), s.get("duration_ms", 0.0)
    )
    if "steps_total" in s:
        log.info(
            "[STEP] Total: %s Passed: %s Failed: %s Skipped: %s",
            s.get("steps_total", 0),
            s.get("steps_passed", 0),
            s.get("steps_failed", 0),
            s.get("steps_skipped", 0),
        )

    html_target = html or f"reports/report-{ts}.html"

    if report:
        write_json(report_obj, report)
        log.info("[CASE] JSON report written to %s", report)
    from arun.reporter.html_reporter import write_html
    write_html(report_obj, html_target)
    log.info("[CASE] HTML report written to %s", html_target)

    if allure_results:
        try:
            from arun.reporter.allure_reporter import write_allure_results
            write_allure_results(report_obj, allure_results)
            log.info("[CASE] Allure results written to %s", allure_results)
        except Exception as e:
            log = get_logger("arun.cli")
            log.error(f"Failed to write Allure results: {e}")

    # Notifications (best-effort)
    try:
        from arun.notifier import (
            NotifyContext,
            FeishuNotifier,
            EmailNotifier,
            DingTalkNotifier,
            build_summary_text,
        )

        channels = [c.strip().lower() for c in (notify or os.environ.get("ARUN_NOTIFY", "")).split(",") if c.strip()]
        policy = (notify_only or os.environ.get("ARUN_NOTIFY_ONLY", "failed")).strip().lower()
        topn = int(os.environ.get("NOTIFY_TOPN", "5") or "5")

        should_send = (
            (policy == "always") or (policy == "failed" and (s.get("failed", 0) or 0) > 0)
        )
        if channels and should_send:
            ctx = NotifyContext(html_path=html_target, log_path=default_log, notify_only=policy, topn=topn)
            notifiers = []

            if "feishu" in channels:
                fw = os.environ.get("FEISHU_WEBHOOK", "").strip()
                if fw:
                    fs = os.environ.get("FEISHU_SECRET")
                    fm = os.environ.get("FEISHU_MENTION")
                    style = os.environ.get("FEISHU_STYLE", "text").lower().strip()
                    notifiers.append(FeishuNotifier(webhook=fw, secret=fs, mentions=fm, style=style))

            if "email" in channels:
                host = os.environ.get("SMTP_HOST", "").strip()
                if host:
                    notifiers.append(
                        EmailNotifier(
                            smtp_host=host,
                            smtp_port=int(os.environ.get("SMTP_PORT", "465") or 465),
                            smtp_user=os.environ.get("SMTP_USER"),
                            smtp_pass=os.environ.get("SMTP_PASS"),
                            mail_from=os.environ.get("MAIL_FROM"),
                            mail_to=os.environ.get("MAIL_TO"),
                            use_ssl=(os.environ.get("SMTP_SSL", "true").lower() != "false"),
                            attach_html=bool(notify_attach_html or (os.environ.get("NOTIFY_ATTACH_HTML", "").lower() in {"1","true","yes"})),
                            html_body=(os.environ.get("NOTIFY_HTML_BODY", "true").lower() != "false"),
                        )
                    )

            if "dingtalk" in channels:
                dw = os.environ.get("DINGTALK_WEBHOOK", "").strip()
                if dw:
                    ds = os.environ.get("DINGTALK_SECRET")
                    mobiles = os.environ.get("DINGTALK_AT_MOBILES", "").strip()
                    at_mobiles = [m.strip() for m in mobiles.split(",") if m.strip()]
                    at_all = os.environ.get("DINGTALK_AT_ALL", "").lower() in {"1", "true", "yes"}
                    style = os.environ.get("DINGTALK_STYLE", "text").lower().strip()
                    notifiers.append(
                        DingTalkNotifier(webhook=dw, secret=ds, at_mobiles=at_mobiles, at_all=at_all, style=style)
                    )

            for n in notifiers:
                try:
                    n.send(report_obj, ctx)
                except Exception:
                    pass
    except Exception:
        # never break main flow for notifications
        pass

    log.info("[CASE] Logs written to %s", default_log)
    if s.get("failed", 0) > 0:
        raise typer.Exit(code=1)


@app.command("check")
def check(
    path: str = typer.Argument(..., help="File or directory to validate"),
):
    """Validate YAML tests for syntax and style without executing.

    Enforces:
    - Extract uses only `$` syntax
    - Check uses `$` for body, and `status_code`/`headers.*` for metadata
    - Hooks function-name style has required prefixes
    """
    files = discover([path])
    if not files:
        typer.echo("No YAML test files found.")
        raise typer.Exit(code=2)
    # spacing check helper
    def _check_steps_spacing(filepath: Path) -> tuple[bool, str | None]:
        try:
            text = Path(filepath).read_text(encoding="utf-8")
        except Exception as e:
            return False, f"read error: {e}"
        lines = text.splitlines()
        import re as _re
        i = 0
        while i < len(lines):
            m = _re.match(r"^(\s*)steps:\s*$", lines[i])
            if not m:
                i += 1
                continue
            base = len(m.group(1))
            step_indent = base + 2
            seen_first = False
            j = i + 1
            while j < len(lines):
                ln = lines[j]
                # end steps block
                if ln.strip() and (len(ln) - len(ln.lstrip(" ")) <= base) and not ln.lstrip().startswith("-"):
                    break
                if ln.startswith(" " * step_indent + "-"):
                    if seen_first:
                        prev = lines[j - 1] if j - 1 >= 0 else ""
                        if prev.strip() != "":
                            return False, f"steps spacing error near line {j+1}: add a blank line between step items"
                    else:
                        seen_first = True
                j += 1
            i = j
        return True, None

    ok = 0
    for f in files:
        try:
            load_yaml_file(f)
            spacing_ok, spacing_msg = _check_steps_spacing(Path(f))
            if not spacing_ok:
                typer.echo(f"FAIL: {f} -> {spacing_msg}")
                raise typer.Exit(code=2)
            ok += 1
            typer.echo(f"OK: {f}")
        except Exception as e:
            typer.echo(f"FAIL: {f} -> {e}")
            raise typer.Exit(code=2)
    typer.echo(f"Validated {ok} file(s).")


@app.command("fix")
def fix(
    paths: List[str] = typer.Argument(..., help="File(s) or directories to auto-fix YAML (move hooks to config.* / spacing)", metavar="PATH..."),
    only_spacing: bool = typer.Option(False, "--only-spacing", help="Only fix steps spacing (do not move hooks)"),
    only_hooks: bool = typer.Option(False, "--only-hooks", help="Only move hooks into config.* (do not change spacing)"),
):
    """Auto-fix YAML files for style and structure.

    - Move suite/case-level hooks under `config.setup_hooks/config.teardown_hooks`.
    - Ensure a single blank line between adjacent steps items under `steps:`.
    """
    files = discover(paths)
    if not files:
        typer.echo("No YAML test files found.")
        raise typer.Exit(code=2)

    def _merge_hooks(dst_cfg: dict, src_obj: dict, level: str) -> bool:
        changed = False
        for hk in ("setup_hooks", "teardown_hooks"):
            if hk in src_obj and isinstance(src_obj.get(hk), list):
                items = [it for it in src_obj.get(hk) or []]
                if items:
                    # merge with existing config hooks (config first, then moved)
                    existing = list(dst_cfg.get(hk) or [])
                    dst_cfg[hk] = existing + items
                    changed = True
                src_obj.pop(hk, None)
        return changed

    import yaml as _yaml
    import re as _re
    def _fix_steps_spacing(filepath: Path) -> bool:
        try:
            text = Path(filepath).read_text(encoding="utf-8")
        except Exception:
            return False
        lines = text.splitlines()
        changed = False
        i = 0
        while i < len(lines):
            m = _re.match(r"^(\s*)steps:\s*$", lines[i])
            if not m:
                i += 1
                continue
            base = len(m.group(1))
            step_indent = base + 2
            seen_first = False
            j = i + 1
            while j < len(lines):
                ln = lines[j]
                if ln.strip() and (len(ln) - len(ln.lstrip(" ")) <= base) and not ln.lstrip().startswith("-"):
                    break
                if ln.startswith(" " * step_indent + "-"):
                    if seen_first:
                        prev = lines[j - 1] if j - 1 >= 0 else ""
                        if prev.strip() != "":
                            lines.insert(j, "")
                            changed = True
                            j += 1
                    else:
                        seen_first = True
                j += 1
            i = j
        if changed:
            Path(filepath).write_text("\n".join(lines) + ("\n" if text.endswith("\n") else ""), encoding="utf-8")
        return changed
    changed_files = []
    for f in files:
        raw = Path(f).read_text(encoding="utf-8")
        try:
            obj = _yaml.safe_load(raw) or {}
        except Exception:
            # skip invalid YAML
            continue
        if not isinstance(obj, dict):
            continue
        modified = False
        if not only_spacing:
            # Suite vs Case: move hooks
            if "cases" in obj and isinstance(obj["cases"], list):
                cfg = obj.get("config") or {}
                if not isinstance(cfg, dict):
                    cfg = {}
                if _merge_hooks(cfg, obj, level="suite"):
                    obj["config"] = cfg
                    modified = True
                new_cases = []
                for c in obj["cases"]:
                    if not isinstance(c, dict):
                        new_cases.append(c)
                        continue
                    c_cfg = c.get("config") or {}
                    if not isinstance(c_cfg, dict):
                        c_cfg = {}
                    if _merge_hooks(c_cfg, c, level="case"):
                        c["config"] = c_cfg
                        modified = True
                    new_cases.append(c)
                obj["cases"] = new_cases
            elif "steps" in obj and isinstance(obj["steps"], list):
                cfg = obj.get("config") or {}
                if not isinstance(cfg, dict):
                    cfg = {}
                if _merge_hooks(cfg, obj, level="case"):
                    obj["config"] = cfg
                    modified = True
            else:
                # not a recognized test file; still attempt spacing fix later
                pass

        if modified and not only_spacing:
            Path(f).write_text(_yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")
            changed_files.append(str(f))
        # steps spacing fix unless only_hooks
        if not only_hooks and _fix_steps_spacing(Path(f)) and str(f) not in changed_files:
            changed_files.append(str(f))

    if changed_files:
        typer.echo("Fixed files:")
        for p in changed_files:
            typer.echo(f"- {p}")
    else:
        typer.echo("No changes needed.")

if __name__ == "__main__":
    app()
