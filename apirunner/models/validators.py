from __future__ import annotations

from typing import Any, List, Tuple
from pydantic import BaseModel


class Validator(BaseModel):
    # triplet: [check, comparator, expect]
    check: Any
    comparator: str
    expect: Any


def normalize_validators(items: List[Any]) -> List[Validator]:
    out: List[Validator] = []
    for it in items or []:
        if isinstance(it, (list, tuple)) and len(it) == 3:
            out.append(Validator(check=it[0], comparator=str(it[1]), expect=it[2]))
        elif isinstance(it, dict) and {"check", "comparator", "expect"}.issubset(set(it.keys())):
            out.append(Validator(**it))
        else:
            raise ValueError(f"Invalid validator item: {it!r}")
    return out

