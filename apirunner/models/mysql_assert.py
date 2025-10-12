from __future__ import annotations

from typing import Any, Dict, Mapping, Sequence

from pydantic import BaseModel, Field, model_validator


class MySQLAssertConfig(BaseModel):
    """Configuration for a MySQL assertion executed after a step response."""

    query: str
    expect: Dict[str, Any] | Sequence[Any] | None = None
    store: Dict[str, str] | None = None
    allow_empty: bool = Field(default=False)
    dsn: Mapping[str, Any] | str | None = None

    @model_validator(mode="after")
    def _validate_expect(self) -> "MySQLAssertConfig":
        if self.expect is not None and not isinstance(self.expect, (Mapping, Sequence)):
            raise TypeError("mysql_assert.expect must be a mapping or comparator list")
        if self.store is not None and not isinstance(self.store, Mapping):
            raise TypeError("mysql_assert.store must be a mapping of var -> column")
        return self

    @model_validator(mode="before")
    @classmethod
    def _normalize_input(cls, data: Any) -> Any:
        if isinstance(data, Mapping):
            if "params" in data:
                raise ValueError("mysql_assert does not support 'params' field; use \"query: 'SQL | params=...'\" format.")
            if "optional" in data and "allow_empty" not in data:
                data = {**data, "allow_empty": data["optional"]}
        return data
