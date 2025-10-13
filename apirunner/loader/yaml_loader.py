from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple

import yaml

from apirunner.models.case import Case, Suite
from apirunner.models.step import Step
from apirunner.models.validators import normalize_validators
from apirunner.utils.errors import LoadError


def _is_suite(doc: Dict[str, Any]) -> bool:
    return "cases" in doc


def _normalize_case_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    dd = dict(d)
    # Allow case-level hooks declared inside config as aliases, e.g.:
    # config:
    #   setup_hooks: ["${func()}"]
    #   teardown_hooks: ["${func()}"]
    promoted_from_config: set[str] = set()
    if "config" in dd and isinstance(dd["config"], dict):
        for hk_field in ("setup_hooks", "teardown_hooks"):
            if hk_field in dd["config"]:
                items = dd["config"].get(hk_field)
                if items is None:
                    items = []
                if not isinstance(items, list):
                    raise LoadError(f"Invalid config.{hk_field} entry type {type(items).__name__}; expected list of '${{func(...)}}'")
                # validate expressions and promote to case-level
                for item in items:
                    if not isinstance(item, str):
                        raise LoadError(f"Invalid {hk_field} entry type {type(item).__name__}; expected string like '${{func(...)}}'")
                    text = item.strip()
                    if not text:
                        raise LoadError(f"Invalid empty {hk_field} entry")
                    if not (text.startswith("${") and text.endswith("}")):
                        raise LoadError(f"Invalid {hk_field} entry '{item}': must use expression syntax '${{func(...)}}'")
                dd[hk_field] = list(items)
                promoted_from_config.add(hk_field)
                # remove from config to avoid model validation issues
                dd["config"].pop(hk_field, None)
    if "steps" in dd and isinstance(dd["steps"], list):
        new_steps: List[Dict[str, Any]] = []
        for s in dd["steps"]:
            ss = dict(s)
            # Disallow legacy request.json field (no compatibility)
            if isinstance(ss.get("request"), dict) and "json" in ss["request"]:
                raise LoadError("Invalid request field 'json': use 'body' instead")
            if "validate" in ss:
                ss["validate"] = [v.model_dump() for v in normalize_validators(ss["validate"])]
                # enforce $-only for body checks
                for v in ss["validate"]:
                    chk = v.get("check")
                    if isinstance(chk, str) and chk.startswith("body."):
                        raise LoadError(f"Invalid check '{chk}': use '$' syntax e.g. '$.path.to.field'")
            # enforce $-only for extract
            if "extract" in ss and isinstance(ss["extract"], dict):
                for k, ex in ss["extract"].items():
                    if isinstance(ex, str) and ex.startswith("body."):
                        raise LoadError(f"Invalid extract '{ex}' for '{k}': use '$' syntax e.g. '$.path.to.field'")
            # hooks field: enforce "${...}" expression form
            for hk_field in ("setup_hooks", "teardown_hooks"):
                if hk_field in ss and isinstance(ss[hk_field], list):
                    for item in ss[hk_field]:
                        if not isinstance(item, str):
                            raise LoadError(f"Invalid {hk_field} entry type {type(item).__name__}; expected string like \"${{func(...)}}\"")
                        text = item.strip()
                        if not text:
                            raise LoadError(f"Invalid empty {hk_field} entry")
                        if not (text.startswith("${") and text.endswith("}")):
                            raise LoadError(f"Invalid {hk_field} entry '{item}': must use expression syntax \"${{func(...)}}\"")
            new_steps.append(ss)
        dd["steps"] = new_steps
    # Disallow old-style case-level hooks at top-level; allow if just promoted from config
    for hk_field in ("setup_hooks", "teardown_hooks"):
        if hk_field in dd and hk_field not in promoted_from_config:
            raise LoadError(
                f"Invalid top-level '{hk_field}': case-level hooks must be declared under 'config.{hk_field}'."
            )
    return dd


def load_yaml_file(path: Path) -> Tuple[List[Case], Dict[str, Any]]:
    try:
        raw = path.read_text(encoding="utf-8")
        obj = yaml.safe_load(raw) or {}
    except Exception as e:
        raise LoadError(f"Failed to parse YAML: {path}: {e}")

    cases: List[Case] = []
    if _is_suite(obj):
        # Promote suite-level hooks declared under config.* and forbid old top-level style
        promoted_from_config: set[str] = set()
        if isinstance(obj.get("config"), dict):
            for hk_field in ("setup_hooks", "teardown_hooks"):
                if hk_field in obj["config"]:
                    items = obj["config"].get(hk_field)
                    if items is None:
                        items = []
                    if not isinstance(items, list):
                        raise LoadError(f"Invalid config.{hk_field} entry type {type(items).__name__}; expected list of '${{func(...)}}'")
                    # validate expressions and promote to suite-level
                    for item in items:
                        if not isinstance(item, str):
                            raise LoadError(f"Invalid suite {hk_field} entry type {type(item).__name__}; expected string like '${{func(...)}}'")
                        text = item.strip()
                        if not text:
                            raise LoadError(f"Invalid empty suite {hk_field} entry")
                        if not (text.startswith("${") and text.endswith("}")):
                            raise LoadError(f"Invalid suite {hk_field} entry '{item}': must use expression syntax '${{func(...)}}'")
                    obj[hk_field] = list(items)
                    promoted_from_config.add(hk_field)
                    obj["config"].pop(hk_field, None)
        # Disallow old top-level suite hooks (unless just promoted from config)
        for hk_field in ("setup_hooks", "teardown_hooks"):
            if hk_field in obj and hk_field not in promoted_from_config:
                raise LoadError(
                    f"Invalid top-level '{hk_field}': suite-level hooks must be declared under 'config.{hk_field}'."
                )
        # pre-normalize validators in nested cases
        if "cases" in obj and isinstance(obj["cases"], list):
            obj = {**obj, "cases": [_normalize_case_dict(c) for c in obj["cases"]]}
        suite = Suite.model_validate(obj)
        base_cfg = suite.config
        for c in suite.cases:
            # inherit suite config fields if not set in case
            merged = c.model_copy(deep=True)
            if not merged.config.base_url:
                merged.config.base_url = base_cfg.base_url
            merged.config.variables = {**(base_cfg.variables or {}), **(merged.config.variables or {})}
            merged.config.headers = {**(base_cfg.headers or {}), **(merged.config.headers or {})}
            merged.config.tags = list({*base_cfg.tags, *merged.config.tags})
            # inherit suite hooks and enforce naming at suite level
            merged.suite_setup_hooks = list(suite.setup_hooks or [])
            merged.suite_teardown_hooks = list(suite.teardown_hooks or [])
        # suite-level hooks: enforce "${...}" expression form
        for hk_field in ("setup_hooks", "teardown_hooks"):
            items = getattr(suite, hk_field, []) or []
            for item in items:
                if not isinstance(item, str):
                    raise LoadError(f"Invalid suite {hk_field} entry type {type(item).__name__}; expected string like \"${{func(...)}}\"")
                text = item.strip()
                if not text:
                    raise LoadError(f"Invalid empty suite {hk_field} entry")
                if not (text.startswith("${") and text.endswith("}")):
                    raise LoadError(f"Invalid suite {hk_field} entry '{item}': must use expression syntax \"${{func(...)}}\"")
            cases.append(merged)
    else:
        # single case file: normalize validators
        obj = _normalize_case_dict(obj)
        case = Case.model_validate(obj)
        cases.append(case)

    meta = {"file": str(path)}
    return cases, meta


def expand_parameters(parameters: Any) -> List[Dict[str, Any]]:
    """Expand parameterization to a list of param dicts.

    Supported forms:
    1) Dict of lists (cartesian):
       parameters: { a: [1,2], b: [3,4] }
    2) List of dict-of-lists (cartesian across items):
       parameters:
         - a: [1,2]
         - b: [3,4]
    3) Zipped groups (hyphen-joined variable names):
       parameters:
         - a-b:
             - [1,3]
             - [2,4]
       (Supports multiple groups; final result is cartesian product across groups)
    4) Enumeration of concrete dicts:
       parameters:
         - {a: 1, b: 3}
         - {a: 2, b: 4}
    """
    if not parameters:
        return [{}]

    # 4) enumeration of concrete dicts (all items are dicts and values are not lists/tuples)
    if isinstance(parameters, list):
        if parameters and all(
            isinstance(it, dict)
            and all(not isinstance(v, (list, tuple, dict)) for v in it.values())
            and all("-" not in k for k in it.keys())
            for it in parameters
        ):
            return [dict(p) for p in parameters]

        # General composition: iteratively combine groups
        combos: List[Dict[str, Any]] = [{}]

        def product_append(base: List[Dict[str, Any]], unit: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            out: List[Dict[str, Any]] = []
            for b in base:
                for u in unit:
                    out.append({**b, **u})
            return out

        for item in parameters:
            if not isinstance(item, dict):
                raise LoadError(f"Invalid parameters list item: {item!r}")
            # 3) zipped groups: key like "a-b-c": [[v1,v2,v3], ...]
            if len(item) == 1 and any("-" in k for k in item.keys()):
                key = next(iter(item.keys()))
                rows = item[key]
                if not isinstance(rows, list):
                    raise LoadError(f"Zipped parameters for {key!r} must be a list of lists")
                names = [n.strip() for n in key.split("-") if n.strip()]
                unit: List[Dict[str, Any]] = []
                for row in rows:
                    if not isinstance(row, (list, tuple)) or len(row) != len(names):
                        raise LoadError(f"Row {row!r} does not match variables {names}")
                    unit.append({n: v for n, v in zip(names, row)})
                combos = product_append(combos, unit)
            else:
                # 2) dict-of-lists group (cartesian within the group)
                if not all(isinstance(v, list) for v in item.values()):
                    raise LoadError(f"Parameters item must be lists: {item!r}")
                    
                keys = list(item.keys())
                vals = [list(v) for v in item.values()]
                unit: List[Dict[str, Any]] = []
                def rec(i: int, acc: Dict[str, Any]):
                    if i == len(keys):
                        unit.append(dict(acc))
                        return
                    k = keys[i]
                    for vv in vals[i]:
                        acc[k] = vv
                        rec(i + 1, acc)
                rec(0, {})
                combos = product_append(combos, unit)
        return combos

    # 1) dict of lists (cartesian)
    if isinstance(parameters, dict):
        keys = list(parameters.keys())
        values = [list(v) for v in parameters.values()]
        combos: List[Dict[str, Any]] = []
        def rec(idx: int, acc: Dict[str, Any]):
            if idx == len(keys):
                combos.append(dict(acc))
                return
            k = keys[idx]
            for v in values[idx]:
                acc[k] = v
                rec(idx + 1, acc)
        rec(0, {})
        return combos

    raise LoadError(f"Unsupported parameters type: {type(parameters)}")
