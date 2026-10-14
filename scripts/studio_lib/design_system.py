"""Documentary design system: named looks over authentic engines + shared tokens.

`styles/design-system.json` defines palettes, colour semantics, typography roles,
motion and layout rules, and `looks` (historical-illustrated, kinetic-type,
data-editorial, premium-whiteboard, hand-drawn-illustration, technical-blueprint, ...).
A scene opts in with `"look": "<name>"`; the look fills `engine` and default
`params` (scene values always win) and, for huashu grammars, the palette as `theme`.
"""
from __future__ import annotations

import json
from functools import lru_cache

from .config import SKILL_ROOT

DS = SKILL_ROOT / "styles" / "design-system.json"


@lru_cache(maxsize=1)
def load() -> dict:
    return json.loads(DS.read_text(encoding="utf-8"))


def palette(name: str) -> dict:
    return dict(load()["tokens"]["palettes"][name])


def _merge(base: dict, over: dict) -> dict:
    out = dict(base)
    for k, v in over.items():
        out[k] = _merge(out[k], v) if isinstance(v, dict) and isinstance(out.get(k), dict) else v
    return out


def apply_look(scene: dict) -> dict:
    """Fill engine/params from scene['look']; raises KeyError for unknown looks."""
    name = scene.get("look")
    if not name:
        return scene
    looks = load()["looks"]
    if name not in looks:
        raise KeyError(f"unknown look {name!r}; known: {', '.join(sorted(looks))}")
    lk = looks[name]
    if lk.get("status") == "pending":
        raise KeyError(f"look {name!r} is not available yet ({lk.get('upstream')})")
    if scene.get("engine") in (None, "auto"):
        scene["engine"] = lk["engine"]
    params = _merge(lk.get("params", {}), scene.get("params", {}))
    pal = load()["tokens"]["palettes"].get(lk.get("palette", ""))
    if scene["engine"] == "huashu_clip" and pal and "theme" not in params and "shots" not in params:
        params["theme"] = {k: v for k, v in pal.items() if k != "alert"}
    scene["params"] = params
    return scene


def project_fonts() -> list[str]:
    """Font families the design system allows (engine-internal faces are reported separately)."""
    return sorted({r["family"] for r in load()["tokens"]["typography"]["roles"].values()})
