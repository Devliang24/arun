from __future__ import annotations

import json
import os
import shlex
from typing import Any, Dict, List, Tuple, Optional
from urllib.parse import urlparse, parse_qsl

from .base import ImportedCase, ImportedStep


def _read_file_payload(spec: str) -> Optional[str]:
    # spec like @file.json or just file path
    p = spec.lstrip("@")
    if not p:
        return None
    if os.path.exists(p) and os.path.isfile(p):
        try:
            return open(p, "r", encoding="utf-8").read()
        except Exception:
            return None
    return None


def _parse_one(tokens: List[str]) -> Tuple[Optional[ImportedStep], Optional[str]]:
    """Parse a single curl command tokens (without the leading 'curl').
    Returns (ImportedStep, base_url_guess)
    """
    method: Optional[str] = None
    url: Optional[str] = None
    headers: Dict[str, str] = {}
    body_text: Optional[str] = None
    data_obj: Any = None
    files: Any = None
    auth: Dict[str, str] | None = None
    verify: Optional[bool] = None
    allow_redirects: Optional[bool] = None

    # Normalize tokens to handle curl commands split across multiple lines with trailing '\'.
    # These produce entries like " -H" after shlex.split; trim leading/trailing whitespace
    # so option matching works as expected. Keep original order and drop empty fragments.
    tokens = [tok for tok in (t.strip() for t in tokens) if tok]

    it = iter(range(len(tokens)))
    i = 0
    while i < len(tokens):
        t = tokens[i]
        if t == "-X" or t == "--request":
            i += 1
            method = tokens[i].upper()
        elif t in ("-H", "--header"):
            i += 1
            hv = tokens[i]
            if ":" in hv:
                k, v = hv.split(":", 1)
                headers[k.strip()] = v.strip()
        elif t in ("-d", "--data", "--data-raw", "--data-urlencode", "--data-binary"):
            i += 1
            dv = tokens[i]
            if dv.startswith("@"):
                read = _read_file_payload(dv)
                if read is not None:
                    body_text = read
                else:
                    body_text = dv
            else:
                body_text = dv
        elif t in ("-F", "--form"):
            i += 1
            # Keep form data as-is; rough mapping
            fv = tokens[i]
            data_obj = data_obj or {}
            if "=" in fv:
                k, v = fv.split("=", 1)
                data_obj[k] = v
        elif t in ("-u", "--user"):
            i += 1
            uv = tokens[i]
            if ":" in uv:
                u, p = uv.split(":", 1)
                auth = {"type": "basic", "username": u, "password": p}
        elif t in ("-k", "--insecure"):
            verify = False
        elif t in ("-L", "--location"):
            allow_redirects = True
        elif t.startswith("http://") or t.startswith("https://"):
            url = t
        elif t and not t.startswith("-") and url is None:
            # positional URL
            url = t
        i += 1

    # default method
    if method is None:
        method = "POST" if body_text or data_obj else "GET"

    base_guess: Optional[str] = None
    params: Dict[str, Any] | None = None
    path_or_full = url or "/"
    if url:
        u = urlparse(url)
        if u.scheme and u.netloc:
            base_guess = f"{u.scheme}://{u.netloc}"
            path_or_full = u.path or "/"
            q = dict(parse_qsl(u.query, keep_blank_values=True))
            params = q or None

    body: Any | None = None
    data: Any | None = None
    if body_text is not None:
        # try json
        try:
            body = json.loads(body_text)
        except Exception:
            data = body_text

    name = f"{method} {path_or_full or '/'}"
    step = ImportedStep(
        name=name,
        method=method,
        url=path_or_full,
        params=params,
        headers=headers or None,
        body=body,
        data=data_obj or data,
        files=files,
        auth=auth,
    )
    return step, base_guess


def parse_curl_text(text: str, *, case_name: Optional[str] = None, base_url: Optional[str] = None) -> ImportedCase:
    # Split text into commands by detecting lines starting with 'curl ' or 'curl\t'
    # Fallback: treat whole text as one command
    pieces: List[str] = []
    buf: List[str] = []
    for line in text.splitlines():
        ls = line.strip()
        if ls.startswith("curl ") and buf:
            pieces.append(" ".join(buf))
            buf = [ls]
        else:
            if ls:
                buf.append(ls)
    if buf:
        pieces.append(" ".join(buf))
    if not pieces and text.strip():
        pieces = [text.strip()]

    steps: List[ImportedStep] = []
    base_guess: Optional[str] = None
    for cmd in pieces:
        s = cmd.strip()
        if s.startswith("curl"):
            s = s[len("curl"):].strip()
        try:
            tokens = shlex.split(s, posix=True)
        except Exception:
            tokens = s.split()
        step, bg = _parse_one(tokens)
        steps.append(step)
        if not base_guess and bg:
            base_guess = bg

    case = ImportedCase(name=case_name or "Imported Case", base_url=base_url or base_guess, steps=steps)
    return case
