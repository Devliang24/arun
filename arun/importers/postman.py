from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qsl

from .base import ImportedCase, ImportedStep


def _pm_headers(arr: List[Dict[str, Any]] | None) -> Dict[str, str] | None:
    if not arr:
        return None
    out: Dict[str, str] = {}
    for h in arr:
        k = h.get("key")
        v = h.get("value")
        if k and v is not None:
            out[str(k)] = str(v)
    return out or None


def _pm_url_parts(uobj: Any) -> tuple[Optional[str], str, Dict[str, Any] | None]:
    # Return (base_url, path_or_full, params)
    if isinstance(uobj, str):
        u = urlparse(uobj)
        base = f"{u.scheme}://{u.netloc}" if (u.scheme and u.netloc) else None
        path = u.path or "/"
        q = dict(parse_qsl(u.query, keep_blank_values=True)) or None
        return base, path, q
    if isinstance(uobj, dict):
        raw = uobj.get("raw")
        if raw:
            return _pm_url_parts(raw)
        protocol = uobj.get("protocol")
        host = uobj.get("host")
        if isinstance(host, list):
            host = ".".join(host)
        base = f"{protocol}://{host}" if protocol and host else None
        path_list = uobj.get("path") or []
        path = "/" + "/".join(str(x) for x in path_list) if path_list else "/"
        params = None
        if uobj.get("query"):
            params = {q.get("key"): q.get("value") for q in uobj["query"] if q.get("key")}
        return base, path, params
    return None, "/", None


def parse_postman(text: str, *, case_name: Optional[str] = None, base_url: Optional[str] = None) -> ImportedCase:
    data = json.loads(text)
    name = case_name or (data.get("info", {}).get("name") if isinstance(data, dict) else None) or "Imported Postman"
    steps: List[ImportedStep] = []
    base_guess: Optional[str] = None

    def visit(items: List[Dict[str, Any]]):
        nonlocal base_guess
        for it in items or []:
            if "item" in it and isinstance(it["item"], list):
                visit(it["item"])  # folder
                continue
            req = it.get("request") or {}
            method = (req.get("method") or "GET").upper()
            url_obj = req.get("url")
            b, path, params = _pm_url_parts(url_obj)
            if not base_guess and b:
                base_guess = b
            headers = _pm_headers(req.get("header"))
            body = None
            data_raw = None
            body_obj = req.get("body") or {}
            if body_obj.get("mode") == "raw":
                data_raw = body_obj.get("raw")
                try:
                    body = json.loads(data_raw)
                    data_raw = None
                except Exception:
                    pass

            step_name = it.get("name") or f"{method} {path}"
            steps.append(
                ImportedStep(name=step_name, method=method, url=path, params=params, headers=headers, body=body, data=data_raw)
            )

    visit(data.get("item") or [])
    return ImportedCase(name=name, base_url=base_url or base_guess, steps=steps)

