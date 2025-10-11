from __future__ import annotations

import shlex
from typing import Any, Dict


def to_curl(method: str, url: str, *, headers: Dict[str, str] | None = None, data: Any | None = None) -> str:
    parts = ["curl", "-X", method.upper(), shlex.quote(url)]
    for k, v in (headers or {}).items():
        parts += ["-H", shlex.quote(f"{k}: {v}")]
    if data is not None:
        if isinstance(data, (dict, list)):
            import json

            payload = json.dumps(data, ensure_ascii=False)
        else:
            payload = str(data)
        parts += ["--data", shlex.quote(payload)]
    return " ".join(parts)

