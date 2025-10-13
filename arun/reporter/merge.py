from __future__ import annotations

import json
from pathlib import Path
from typing import List

from arun.models.report import RunReport, CaseInstanceResult


def merge_reports(files: List[str | Path]) -> RunReport:
    cases: List[CaseInstanceResult] = []
    total = failed = skipped = 0
    duration = 0.0
    for f in files:
        data = json.loads(Path(f).read_text(encoding="utf-8"))
        rr = RunReport.model_validate(data)
        cases.extend(rr.cases)
        total += rr.summary.get("total", 0)
        failed += rr.summary.get("failed", 0)
        skipped += rr.summary.get("skipped", 0)
        duration += rr.summary.get("duration_ms", 0.0)
    return RunReport(summary={"total": total, "failed": failed, "skipped": skipped, "passed": total - failed - skipped, "duration_ms": duration}, cases=cases)
