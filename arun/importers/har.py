from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse, parse_qsl

from .base import ImportedCase, ImportedStep


def parse_har(text: str, *, case_name: Optional[str] = None, base_url: Optional[str] = None) -> ImportedCase:
    data = json.loads(text)
    log = data.get("log") or {}
    entries = log.get("entries") or []
    steps: List[ImportedStep] = []
    base_guess: Optional[str] = None

    for ent in entries:
        req = ent.get("request") or {}
        method = (req.get("method") or "GET").upper()
        url = req.get("url") or "/"
        u = urlparse(url)
        if u.scheme and u.netloc and not base_guess:
            base_guess = f"{u.scheme}://{u.netloc}"
        path = u.path or "/"
        params = dict(parse_qsl(u.query, keep_blank_values=True)) or None
        headers = {h.get("name"): h.get("value") for h in (req.get("headers") or []) if h.get("name")}
        body = None
        data_raw = None
        postData = req.get("postData") or {}
        if postData:
            mime = (postData.get("mimeType") or "").split(";")[0]
            text = postData.get("text")
            if text:
                if mime == "application/json":
                    try:
                        body = json.loads(text)
                    except Exception:
                        data_raw = text
                else:
                    data_raw = text

        name = f"{method} {path}"
        steps.append(ImportedStep(name=name, method=method, url=path, params=params, headers=headers or None, body=body, data=data_raw))

    return ImportedCase(name=case_name or "Imported HAR", base_url=base_url or base_guess, steps=steps)

