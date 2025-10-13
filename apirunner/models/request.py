from __future__ import annotations

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from pydantic.config import ConfigDict


class StepRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    method: str
    url: str
    params: Optional[Dict[str, Any]] = None
    headers: Optional[Dict[str, str]] = None
    # Request body (JSON or raw), previously named 'json' in YAML
    body: Optional[Any] = None
    data: Optional[Any] = None
    files: Optional[Any] = None
    auth: Optional[Dict[str, str]] = None  # {type: basic|bearer, username, password, token}
    timeout: Optional[float] = None
    verify: Optional[bool] = None
    allow_redirects: Optional[bool] = None
