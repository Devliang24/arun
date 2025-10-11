from __future__ import annotations

from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree

from apirunner.models.report import RunReport


def write_junit(report: RunReport, outfile: str | Path) -> None:
    tests = report.summary.get("total", 0)
    failures = report.summary.get("failed", 0)
    skipped = report.summary.get("skipped", 0)

    testsuite = Element(
        "testsuite",
        attrib={
            "name": "apirunner",
            "tests": str(tests),
            "failures": str(failures),
            "skipped": str(skipped),
        },
    )

    for c in report.cases:
        tc = SubElement(testsuite, "testcase", attrib={"name": c.name, "time": f"{c.duration_ms/1000.0:.3f}"})
        if c.status == "skipped":
            SubElement(tc, "skipped")
        elif c.status == "failed":
            # collect first failed assertion to message
            msg = ""
            for s in c.steps:
                for a in s.asserts:
                    if not a.passed:
                        msg = a.message or "Assertion failed"
                        break
                if msg:
                    break
            SubElement(tc, "failure", attrib={"message": msg})

    p = Path(outfile)
    p.parent.mkdir(parents=True, exist_ok=True)
    ElementTree(testsuite).write(p, encoding="utf-8", xml_declaration=True)

