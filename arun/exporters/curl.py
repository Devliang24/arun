from __future__ import annotations

import json
from typing import List, Dict, Optional, Iterable, Tuple, Set, Any
import re
from urllib.parse import urljoin, urlencode

from arun.models.case import Case


def _full_url(case: Case, url: str) -> str:
    u = (url or "").strip()
    if u.startswith("http://") or u.startswith("https://"):
        return u
    base = (case.config.base_url or "").strip()
    if base:
        return urljoin(base if base.endswith('/') else base + '/', u.lstrip('/'))
    return u


def _quote(token: str) -> str:
    if token == "\\":
        return token
    if any(ch in token for ch in [' ', '"', "'", '\n', '\t']):
        q = token.replace("'", "'\\''")
        return f"'{q}'"
    return token


def _build_parts(case: Case, idx: int, redact: Optional[Iterable[str]] = None) -> List[str]:
    step = case.steps[idx]
    req = step.request
    parts: List[str] = ["curl"]
    method = (req.method or "GET").upper()
    parts += ["-X", method]
    # headers
    redact_set = set(h.lower() for h in (redact or []))
    for k, v in (req.headers or {}).items():
        vv = v
        if k.lower() in redact_set:
            vv = "***"
        parts += ["-H", f"{k}: {vv}"]
    # params -> query
    url = _full_url(case, req.url or "/")
    if req.params:
        qs = urlencode(req.params, doseq=True)
        sep = '&' if ('?' in url) else '?'
        url = f"{url}{sep}{qs}"

    # body / data
    if req.body is not None:
        try:
            s = json.dumps(req.body, ensure_ascii=False)
        except Exception:
            s = str(req.body)
        parts += ["--data", s]
    elif req.data is not None:
        parts += ["--data", str(req.data)]

    parts.append(url)
    return parts


def step_to_curl(case: Case, idx: int, *, multiline: bool = False, shell: str = "sh", redact: Optional[Iterable[str]] = None) -> str:
    parts = _build_parts(case, idx, redact=redact)
    if not multiline:
        return " ".join(_quote(p) for p in parts)
    # multiline formatting
    cont = "\\" if shell in ("sh", "bash", "zsh") else ("`" if shell in ("ps", "powershell") else "\\")
    lines: List[str] = []
    it = iter(parts)
    first = next(it)
    lines.append(first)
    for p in it:
        lines.append(f"  {cont} {_quote(p)}")
    return "\n".join(lines)


def case_to_curls(case: Case, *, steps: Optional[Iterable[int]] = None, multiline: bool = False, shell: str = "sh", redact: Optional[Iterable[str]] = None) -> List[str]:
    idxs = list(steps) if steps is not None else range(len(case.steps))
    return [step_to_curl(case, i, multiline=multiline, shell=shell, redact=redact) for i in idxs]


_VAR_RE = re.compile(r"\$[A-Za-z_][A-Za-z0-9_]*")
_EXPR_RE = re.compile(r"\$\{[^}]+\}")


def _collect_from_value(val: Any, vars_set: Set[str], exprs_set: Set[str]) -> None:
    if val is None:
        return
    if isinstance(val, str):
        for m in _VAR_RE.findall(val):
            vars_set.add(m)
        for m in _EXPR_RE.findall(val):
            exprs_set.add(m)
        return
    if isinstance(val, dict):
        for v in val.values():
            _collect_from_value(v, vars_set, exprs_set)
        return
    if isinstance(val, (list, tuple)):
        for v in val:
            _collect_from_value(v, vars_set, exprs_set)
        return


def step_placeholders(case: Case, idx: int) -> Tuple[Set[str], Set[str]]:
    """Return ($var placeholders, ${...} expressions) found in URL/params/headers/body/data."""
    req = case.steps[idx].request
    vars_set: Set[str] = set()
    exprs_set: Set[str] = set()
    _collect_from_value(req.url or "", vars_set, exprs_set)
    _collect_from_value(req.params or {}, vars_set, exprs_set)
    _collect_from_value(req.headers or {}, vars_set, exprs_set)
    _collect_from_value(req.body, vars_set, exprs_set)
    _collect_from_value(req.data, vars_set, exprs_set)
    return vars_set, exprs_set
