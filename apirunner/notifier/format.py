from __future__ import annotations

from typing import List, Tuple

from apirunner.models.report import RunReport, CaseInstanceResult, StepResult


def collect_failures(report: RunReport, topn: int = 5) -> List[Tuple[str, str, str]]:
    out: List[Tuple[str, str, str]] = []
    for c in report.cases:
        if c.status != "failed":
            continue
        step_name = ""
        message = ""
        for s in c.steps:
            if s.status == "failed":
                step_name = s.name
                # prefer assertion message
                for a in s.asserts:
                    if not a.passed:
                        message = a.message or "assertion failed"
                        break
                if not message and s.error:
                    message = s.error
                break
        out.append((c.name, step_name or "(unknown step)", message or "(no message)"))
        if len(out) >= max(1, int(topn)):
            break
    return out


def build_summary_text(report: RunReport, *, html_path: str | None, log_path: str | None, topn: int = 5) -> str:
    s = report.summary or {}
    total = s.get("total", 0)
    passed = s.get("passed", 0)
    failed = s.get("failed", 0)
    skipped = s.get("skipped", 0)
    dur_ms = s.get("duration_ms", 0.0)
    lines: List[str] = []
    lines.append(f"APIRunner 执行完成：总 {total} | 通过 {passed} | 失败 {failed} | 跳过 {skipped} | {dur_ms/1000.0:.1f}s")
    fails = collect_failures(report, topn=topn)
    if fails:
        lines.append("失败用例：")
        for name, step, msg in fails:
            # clamp message length
            m = str(msg)
            if len(m) > 200:
                m = m[:200] + "..."
            lines.append(f"- {name}: {step} -> {m}")
    if html_path:
        lines.append(f"报告: {html_path}")
    if log_path:
        lines.append(f"日志: {log_path}")
    return "\n".join(lines)


def build_text_message(report: RunReport, *, html_path: str | None, log_path: str | None, topn: int = 5) -> str:
    # Only Dollar-style rendering is supported for test templates; notifications use built-in summary text
    return build_summary_text(report, html_path=html_path, log_path=log_path, topn=topn)
