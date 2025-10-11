"""
示例 hooks：在 YAML 模板中可调用以下函数。

支持用法：
- Jinja2: {{ ts() }}, {{ md5('abc') }}, {{ sign('demo', 123) }}
- HttpRunner: ${ts()}, ${md5('abc')}, ${sign('demo', 123)}
"""

import hashlib
import time
import uuid
from typing import Any


def ts() -> int:
    return int(time.time())


def md5(s: str) -> str:
    return hashlib.md5(s.encode()).hexdigest()


def sign(app_key: str, ts: int) -> str:
    return md5(f"{app_key}{ts}")


def uuid4() -> str:
    return str(uuid.uuid4())


def echo(x: Any) -> Any:
    return x


def sum_two_int(a: int, b: int) -> int:
    return int(a) + int(b)


def uid() -> str:
    """Hex-only unique id (32 chars)."""
    return uuid.uuid4().hex


def short_uid(n: int = 8) -> str:
    """Short hex id, default 8 chars (alphanumeric)."""
    n = int(n)
    if n < 1:
        n = 1
    if n > 32:
        n = 32
    return uuid.uuid4().hex[:n]
