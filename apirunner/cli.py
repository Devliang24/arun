from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Dict, List, Optional

import typer
import yaml

from apirunner.loader.collector import discover, match_tags
from apirunner.loader.yaml_loader import expand_parameters, load_yaml_file
from apirunner.loader.hooks import get_functions_for
from apirunner.loader.env import load_environment
from apirunner.models.case import Case
from apirunner.models.report import RunReport
from apirunner.reporter.json_reporter import write_json
from apirunner.reporter.merge import merge_reports
from apirunner.runner.runner import Runner
from apirunner.templating.engine import TemplateEngine
from apirunner.utils.logging import setup_logging, get_logger
import time


app = typer.Typer(add_completion=False, help="APIRunner - Minimal HTTP API test runner (MVP)")


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


@app.command()
def run(
    path: str = typer.Argument(..., help="File or directory to run"),
    k: Optional[str] = typer.Option(None, "-k", help="Tag filter expression (and/or/not)"),
    vars: List[str] = typer.Option([], "--vars", help="Variable overrides k=v (repeatable)"),
    failfast: bool = typer.Option(False, "--failfast", help="Stop on first failure"),
    report: Optional[str] = typer.Option(None, "--report", help="Write JSON report to file"),
    html: Optional[str] = typer.Option(None, "--html", help="Write HTML report to file (default reports/report-<timestamp>.html)"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
    env_file: Optional[str] = typer.Option(None, "--env-file", help=".env file path (default .env)"),
    log_file: Optional[str] = typer.Option(None, "--log-file", help="Write console logs to file (default logs/run-<ts>.log)"),
    httpx_logs: bool = typer.Option(False, "--httpx-logs/--no-httpx-logs", help="Show httpx internal request logs", show_default=False),
    reveal_secrets: bool = typer.Option(True, "--reveal-secrets/--mask-secrets", help="Show sensitive fields (password, tokens) in plaintext logs and reports", show_default=True),
    notify: Optional[str] = typer.Option(None, "--notify", help="Notify channels, comma-separated: feishu,email"),
    notify_only: str = typer.Option("failed", "--notify-only", help="Notify policy: failed|always"),
    notify_attach_html: bool = typer.Option(False, "--notify-attach-html/--no-notify-attach-html", help="Attach HTML report in email (if email enabled)", show_default=False),
):
    # default log file path
    ts = time.strftime("%Y%m%d-%H%M%S")
    default_log = log_file or f"logs/run-{ts}.log"
    setup_logging(log_level, log_file=default_log)
    log = get_logger("apirunner.cli")
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
            log.info(f"[CASE] Start: {c.config.name or 'Unnamed'} | params={ps}")
            res = runner.run_case(c, global_vars=global_vars, params=ps, funcs=funcs, envmap=env_store)
            log.info(f"[CASE] Result: {res.name} | status={res.status} | duration={res.duration_ms:.1f}ms")
            instance_results.append(res)
            if failfast and res.status == "failed":
                break

    report_obj: RunReport = runner.build_report(instance_results)
    # Print summary
    s = report_obj.summary
    typer.echo(f"Total: {s['total']} Passed: {s.get('passed',0)} Failed: {s.get('failed',0)} Skipped: {s.get('skipped',0)} Duration: {s.get('duration_ms',0):.1f}ms")

    html_target = html or f"reports/report-{ts}.html"

    if report:
        write_json(report_obj, report)
        typer.echo(f"JSON report written to {report}")
    from apirunner.reporter.html_reporter import write_html
    write_html(report_obj, html_target)
    typer.echo(f"HTML report written to {html_target}")

    # Notifications (best-effort)
    try:
        from apirunner.notifier import (
            NotifyContext,
            FeishuNotifier,
            EmailNotifier,
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

            for n in notifiers:
                try:
                    n.send(report_obj, ctx)
                except Exception:
                    pass
    except Exception:
        # never break main flow for notifications
        pass

    typer.echo(f"Logs written to {default_log}")
    if s.get("failed", 0) > 0:
        raise typer.Exit(code=1)


@app.command("report")
def report_merge(
    inputs: List[str] = typer.Argument(..., help="Input JSON reports"),
    output: str = typer.Option("reports/merged.json", "-o", "--output", help="Output JSON filepath"),
):
    merged = merge_reports(inputs)
    write_json(merged, output)
    typer.echo(f"Merged report written to {output}")


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
    path: str = typer.Argument(..., help="File or directory to auto-fix YAML (move hooks to config.*)"),
):
    """Auto-fix YAML files to the new hooks convention.

    - Suite-level hooks must be under `config.setup_hooks/config.teardown_hooks`.
    - Case-level hooks must be under `config.setup_hooks/config.teardown_hooks`.
    """
    files = discover([path])
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
        # Suite vs Case
        if "cases" in obj and isinstance(obj["cases"], list):
            cfg = obj.get("config") or {}
            if not isinstance(cfg, dict):
                cfg = {}
            # move suite top-level hooks into config
            if _merge_hooks(cfg, obj, level="suite"):
                obj["config"] = cfg
                modified = True
            # each case inside suite
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
            # single case file
            cfg = obj.get("config") or {}
            if not isinstance(cfg, dict):
                cfg = {}
            if _merge_hooks(cfg, obj, level="case"):
                obj["config"] = cfg
                modified = True
        else:
            # not a recognized test file
            continue

        if modified:
            Path(f).write_text(_yaml.safe_dump(obj, sort_keys=False, allow_unicode=True), encoding="utf-8")
            changed_files.append(str(f))
        # steps spacing fix always attempted
        if _fix_steps_spacing(Path(f)) and str(f) not in changed_files:
            changed_files.append(str(f))

    if changed_files:
        typer.echo("Fixed files:")
        for p in changed_files:
            typer.echo(f"- {p}")
    else:
        typer.echo("No changes needed.")

if __name__ == "__main__":
    app()
