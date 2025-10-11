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
from apirunner.reporter.junit_reporter import write_junit
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
    junit: Optional[str] = typer.Option(None, "--junit", help="Write JUnit XML to file"),
    html: Optional[str] = typer.Option(None, "--html", help="Write HTML report to file"),
    log_level: str = typer.Option("INFO", "--log-level", help="Logging level"),
    env_file: Optional[str] = typer.Option(None, "--env-file", help=".env file path"),
    log_file: Optional[str] = typer.Option(None, "--log-file", help="Write console logs to file (default logs/run-<ts>.log)"),
    httpx_logs: bool = typer.Option(False, "--httpx-logs/--no-httpx-logs", help="Show httpx internal request logs", show_default=False),
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

    # Global variables from env file and CLI overrides
    # Unified env loading (HttpRunner-like): --env <name> YAML + --env-file (kv or yaml) + OS ENV
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
    runner = Runner(log=log, failfast=failfast, log_debug=(log_level.upper() == "DEBUG"))
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

    if report:
        write_json(report_obj, report)
        typer.echo(f"JSON report written to {report}")
    if junit:
        write_junit(report_obj, junit)
        typer.echo(f"JUnit written to {junit}")
    if html:
        from apirunner.reporter.html_reporter import write_html
        write_html(report_obj, html)
        typer.echo(f"HTML report written to {html}")

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


if __name__ == "__main__":
    app()
