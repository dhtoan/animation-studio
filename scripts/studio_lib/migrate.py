"""Schema migrations for project.json (non-destructive).

v1 -> v2 adds the V2 scene fields (purpose, attention objective, art style,
shot plan, image/motion prompts, character references, validation status).
Old fields are kept untouched. `studio.py migrate` writes the migrated file
and keeps the original as project.v1.bak.json.
"""
from __future__ import annotations

import copy

CURRENT = 2


def _v1_to_v2(p: dict) -> dict:
    p = copy.deepcopy(p)
    for s in p.get("scenes", []):
        s.setdefault("purpose", s.get("intent", "explain"))
        s.setdefault("attention", "")
        s.setdefault("art_style", None)
        s.setdefault("shot", {"type": "medium", "angle": "eye-level"})
        s.setdefault("image_prompt", "")
        s.setdefault("motion_prompt", "")
        s.setdefault("characters", [])
        s.setdefault("validation", {"status": "unvalidated"})
    p.setdefault("art_direction", {})
    p["schema_version"] = 2
    return p


STEPS = {1: _v1_to_v2}


def migrate(p: dict) -> tuple[dict, list[str]]:
    v = int(p.get("schema_version", 1))
    log = []
    while v < CURRENT:
        p = STEPS[v](p)
        log.append(f"migrated schema v{v} -> v{v + 1}")
        v += 1
    return p, log
