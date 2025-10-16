from __future__ import annotations

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple

import yaml
from pydantic import ValidationError

from arun.models.case import Case, Suite
from arun.models.config import Config
from arun.models.step import Step
from arun.models.validators import normalize_validators
from arun.utils.errors import LoadError


def _is_suite(doc: Dict[str, Any]) -> bool:
    return "cases" in doc


def _is_testsuite_reference(doc: Dict[str, Any]) -> bool:
    return isinstance(doc, dict) and isinstance(doc.get("testcases"), list)


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
    # New-style reference testsuite: { config: {}, testcases: [ {testcase: path, name?, variables?, parameters?, tags?}, ... ] }
    if _is_testsuite_reference(obj):
        promoted_from_config: set[str] = set()
        suite_setup_hooks: List[str] = []
        suite_teardown_hooks: List[str] = []
        if isinstance(obj.get("config"), dict):
            for hk_field in ("setup_hooks", "teardown_hooks"):
                if hk_field in obj["config"]:
                    items = obj["config"].get(hk_field)
                    if items is None:
                        items = []
                    if not isinstance(items, list):
                        raise LoadError(
                            f"Invalid config.{hk_field} entry type {type(items).__name__}; expected list of '${{func(...)}}'"
                        )
                    for item in items:
                        if not isinstance(item, str):
                            raise LoadError(
                                f"Invalid suite {hk_field} entry type {type(item).__name__}; expected string like '${{func(...)}}'"
                            )
                        text = item.strip()
                        if not text:
                            raise LoadError(f"Invalid empty suite {hk_field} entry")
                        if not (text.startswith("${") and text.endswith("}")):
                            raise LoadError(
                                f"Invalid suite {hk_field} entry '{item}': must use expression syntax '${{func(...)}}'"
                            )
                    if hk_field == "setup_hooks":
                        suite_setup_hooks = list(items)
                    else:
                        suite_teardown_hooks = list(items)
                    promoted_from_config.add(hk_field)
                    obj["config"].pop(hk_field, None)
        for hk_field in ("setup_hooks", "teardown_hooks"):
            if hk_field in obj and hk_field not in promoted_from_config:
                raise LoadError(
                    f"Invalid top-level '{hk_field}': suite-level hooks must be declared under 'config.{hk_field}'."
                )

        suite_cfg = Config.model_validate(obj.get("config") or {})
        # iterate referenced testcases
        items = obj.get("testcases") or []
        if not isinstance(items, list):
            raise LoadError("Invalid testsuite: 'testcases' must be a list")

        for idx, it in enumerate(items):
            # item can be a string path or a dict
            if isinstance(it, str):
                tc_path = it
                item_name = None
                item_vars: Dict[str, Any] = {}
                item_params: Any = None
                item_tags: List[str] = []
            elif isinstance(it, dict):
                tc_path = it.get("testcase") or it.get("path") or it.get("file")
                if not tc_path:
                    raise LoadError(f"Invalid testsuite item at index {idx}: missing 'testcase' path")
                item_name = it.get("name")
                item_vars = dict(it.get("variables") or {})
                item_params = it.get("parameters")
                item_tags = list(it.get("tags") or [])
            else:
                raise LoadError(f"Invalid testsuite item type at index {idx}: {type(it).__name__}")

            # resolve referenced path relative to testsuite file
            ref = Path(tc_path)
            if not ref.is_absolute():
                candidate = (path.parent / ref).resolve()
                if candidate.exists():
                    ref = candidate
                else:
                    ref = (Path.cwd() / ref).resolve()
            if not ref.exists():
                raise LoadError(f"Referenced testcase not found: {tc_path}")

            loaded_cases, _meta = load_yaml_file(ref)
            if len(loaded_cases) != 1:
                raise LoadError(
                    f"Referenced testcase '{tc_path}' resolved to {len(loaded_cases)} cases; expected exactly 1."
                )
            base_case = loaded_cases[0]
            merged = base_case.model_copy(deep=True)
            # inherit/merge from suite config
            if not merged.config.base_url:
                merged.config.base_url = suite_cfg.base_url
            merged.config.variables = {
                **(suite_cfg.variables or {}),
                **(merged.config.variables or {}),
                **(item_vars or {}),
            }
            merged.config.headers = {**(suite_cfg.headers or {}), **(merged.config.headers or {})}
            merged.config.tags = list({*(suite_cfg.tags or []), *merged.config.tags, *item_tags})
            # item-level name override
            if item_name:
                merged.config.name = item_name
            # item-level parameters override (simple override to avoid ambiguous compositions)
            if item_params is not None:
                merged.parameters = item_params
            # inherit suite hooks
            merged.suite_setup_hooks = list(suite_setup_hooks or [])
            merged.suite_teardown_hooks = list(suite_teardown_hooks or [])
            cases.append(merged)

    elif _is_suite(obj):
        # Legacy inline suite with 'cases:' is no longer supported
        raise LoadError("Legacy inline suite ('cases:') is not supported. Please use reference testsuite with 'testcases:'.")
    else:
        # single case file: normalize validators
        obj = _normalize_case_dict(obj)
        try:
            case = Case.model_validate(obj)
        except ValidationError as exc:
            raise LoadError(_format_case_validation_error(exc, obj, path, raw)) from exc
        cases.append(case)

    meta = {"file": str(path)}
    return cases, meta


def _format_case_validation_error(exc: ValidationError, obj: Dict[str, Any], path: Path, raw_text: str) -> str:
    """Provide user-friendly messages for common authoring mistakes."""

    def _step_name(idx: int) -> str:
        steps = obj.get("steps") if isinstance(obj.get("steps"), list) else []
        if isinstance(steps, list) and 0 <= idx < len(steps):
            step = steps[idx] or {}
            name = step.get("name") if isinstance(step, dict) else None
            if name:
                return str(name)
        return f"steps[{idx + 1}]"

    for err in exc.errors():
        loc = err.get("loc") or ()
        err_type = err.get("type")

        # Friendly message when fields (extract/validate/...) are indented under request
        if (
            err_type == "extra_forbidden"
            and len(loc) >= 4
            and loc[0] == "steps"
            and isinstance(loc[1], int)
            and loc[2] == "request"
        ):
            field = loc[3]
            if field in {"extract", "validate", "setup_hooks", "teardown_hooks", "sql_validate"}:
                step_label = _step_name(loc[1])
                line_info = _find_step_field_location(raw_text, loc[1], field)
                if line_info:
                    line_no, actual_indent, expected_indent, line_text = line_info
                    indent_hint = (
                        f"line {line_no}: '{line_text.strip()}' uses {actual_indent} leading spaces; "
                        f"expected {expected_indent}."
                    )
                    return (
                        f"Invalid YAML indentation in {path}: step '{step_label}' has '{field}' nested under 'request'. "
                        f"Move '{field}' out to align with 'request' (indent {expected_indent} spaces).\n"
                        f"Hint → {indent_hint}\n"
                        "Example:\n"
                        "  - name: Example\n"
                        "    request:\n"
                        "      ...\n"
                        "    extract: { token: $.data.token }\n"
                        "    validate: [ { eq: [status_code, 200] } ]"
                    )
                return (
                    f"Invalid YAML indentation in {path}: step '{step_label}' has '{field}' nested under 'request'. "
                    "Check indentation — 'extract'/'validate' blocks belong alongside 'request', not inside it."
                )

    # Fallback to default detail when we cannot produce a custom hint
    return f"Failed to load {path}: {exc}"


def _find_step_field_location(raw_text: str, step_index: int, field: str) -> tuple[int, int, int, str] | None:
    """Locate the line/indentation for a field inside a step for better diagnostics."""

    lines = raw_text.splitlines()
    step_pattern = re.compile(r"^\s*-\s+name\s*:")
    current_step = -1
    step_indent = None
    step_start = None

    for idx, line in enumerate(lines):
        if step_pattern.match(line):
            current_step += 1
            if current_step == step_index:
                step_indent = len(line) - len(line.lstrip(" "))
                step_start = idx
                break

    if step_start is None or step_indent is None:
        return None

    expected_indent = step_indent + 2
    field_prefix = f"{field}:"

    for idx in range(step_start + 1, len(lines)):
        line = lines[idx]
        stripped = line.lstrip()
        indent = len(line) - len(stripped)
        if step_pattern.match(line) and indent <= step_indent:
            break
        if not stripped:
            continue
        if stripped.startswith(field_prefix):
            if indent > expected_indent:
                return idx + 1, indent, expected_indent, line.rstrip()
            return None

    return None


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
