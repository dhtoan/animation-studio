"""Minimal JSON Schema validator (the subset our schemas use), stdlib only.

Supports: type (incl. lists), enum, required, properties, items, $ref (#/$defs/..),
minItems/maxItems, minLength, pattern, minimum/maximum/exclusiveMinimum.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_T = {"object": dict, "array": list, "string": str, "boolean": bool, "null": type(None)}


def _is(v, t):
    if t == "integer":
        return isinstance(v, int) and not isinstance(v, bool)
    if t == "number":
        return isinstance(v, (int, float)) and not isinstance(v, bool)
    return isinstance(v, _T[t])


def validate(inst, schema: dict, root: dict | None = None, path: str = "$") -> list[str]:
    root = root or schema
    errs: list[str] = []
    if "$ref" in schema:
        ref = schema["$ref"]
        node = root
        for part in ref.lstrip("#/").split("/"):
            node = node[part]
        return validate(inst, node, root, path)
    t = schema.get("type")
    if t:
        ts = t if isinstance(t, list) else [t]
        if not any(_is(inst, x) for x in ts):
            return [f"{path}: expected {t}, got {type(inst).__name__}"]
    if "enum" in schema and inst not in schema["enum"]:
        errs.append(f"{path}: {inst!r} not in {schema['enum']}")
    if isinstance(inst, dict):
        for k in schema.get("required", []):
            if k not in inst:
                errs.append(f"{path}: missing required '{k}'")
        for k, sub in schema.get("properties", {}).items():
            if k in inst:
                errs += validate(inst[k], sub, root, f"{path}.{k}")
    if isinstance(inst, list):
        if "minItems" in schema and len(inst) < schema["minItems"]:
            errs.append(f"{path}: fewer than {schema['minItems']} items")
        if "maxItems" in schema and len(inst) > schema["maxItems"]:
            errs.append(f"{path}: more than {schema['maxItems']} items")
        if "items" in schema:
            for i, x in enumerate(inst):
                errs += validate(x, schema["items"], root, f"{path}[{i}]")
    if isinstance(inst, str):
        if "minLength" in schema and len(inst) < schema["minLength"]:
            errs.append(f"{path}: shorter than {schema['minLength']}")
        if "pattern" in schema and not re.search(schema["pattern"], inst):
            errs.append(f"{path}: does not match {schema['pattern']}")
    if _is(inst, "number"):
        if "minimum" in schema and inst < schema["minimum"]:
            errs.append(f"{path}: < {schema['minimum']}")
        if "maximum" in schema and inst > schema["maximum"]:
            errs.append(f"{path}: > {schema['maximum']}")
        if "exclusiveMinimum" in schema and inst <= schema["exclusiveMinimum"]:
            errs.append(f"{path}: <= {schema['exclusiveMinimum']}")
    return errs


def validate_file(inst_path: Path, schema_path: Path) -> list[str]:
    return validate(json.loads(Path(inst_path).read_text(encoding="utf-8")),
                    json.loads(Path(schema_path).read_text(encoding="utf-8")))
