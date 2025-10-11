from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from .config import Config
from .step import Step


class Case(BaseModel):
    config: Config = Field(default_factory=Config)
    parameters: Optional[Any] = None  # list[dict] or dict[str, list]
    steps: List[Step]


class Suite(BaseModel):
    config: Config = Field(default_factory=Config)
    cases: List[Case]

