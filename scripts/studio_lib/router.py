"""Smart animation router: picks an engine per scene, with an explicit fallback chain.

Inputs considered: project category, scene purpose, emotion, information density
(data elements), narration cues, aspect ratio, assets present, measured render
cost, and which engines are actually available on this machine.

Explicit `engine` in the scene always wins (still gets fallbacks).
"""
from __future__ import annotations

import re

from .engines import FALLBACKS, TIER, availability, is_premium


class EngineUnavailable(RuntimeError):
    """A premium scene has no authentic engine available; never silently degraded."""

# measured on the dev machine (1080p, ms/frame, single core) — see references/rendering.md
COST_MS = {"kinetic": 115, "motion": 115, "whiteboard": 120, "handdrawn": 135, "artistic": 145,
           "image_whiteboard": 160, "archival": 140, "huashu_clip": 60, "animate_piece": 400, "html_seek": 400,
           "sweety_draw": 220}
# engines whose upstream pages are authored for one aspect only (unless the scene says otherwise)
LANDSCAPE_ONLY = {"html_seek"}

PURPOSE_PREF = {
    "hook": ["kinetic", "artistic", "motion"],
    "title": ["kinetic", "motion"],
    "explain": ["whiteboard", "handdrawn", "motion"],
    "process": ["whiteboard", "motion"],
    "data": ["motion", "huashu_clip", "whiteboard"],
    "comparison": ["motion", "whiteboard"],
    "timeline": ["motion", "whiteboard", "handdrawn"],
    "story": ["handdrawn", "artistic", "whiteboard"],
    "character": ["handdrawn", "whiteboard"],
    "metaphor": ["artistic", "handdrawn"],
    "atmosphere": ["artistic"],
    "reveal": ["artistic", "kinetic", "motion"],
    "evidence": ["motion", "whiteboard"],
    "quote": ["kinetic", "motion"],
    "recreation": ["archival", "handdrawn", "artistic"],
    "tutorial": ["whiteboard", "motion"],
    "cta": ["kinetic", "motion"],
    "illustration": ["image_whiteboard", "handdrawn"],
}

CATEGORY_BIAS = {
    "business": {"motion": 2, "artistic": 1, "kinetic": 1},
    "technology": {"motion": 2, "kinetic": 1},
    "history": {"handdrawn": 2, "archival": 1, "artistic": 1},
    "startups": {"motion": 2, "kinetic": 1},
    "science": {"whiteboard": 2, "motion": 1},
    "diy": {"whiteboard": 2, "motion": 1},
}

DATA_TYPES = {"bar_chart", "line_chart", "donut", "counter", "network", "timeline"}
DRAW_TYPES = {"icon", "arrow", "process", "character", "shape"}


def route(scene: dict, project: dict, avail: dict | None = None, aspect: str = "16:9") -> dict:
    avail = avail or availability()
    ok = {k for k, v in avail.items() if v.get("ok")}
    if aspect == "9:16" and not scene.get("params", {}).get("vertical_ok"):
        ok -= LANDSCAPE_ONLY
    explicit = scene.get("engine", "auto")
    chain: list[str]
    reason: str
    if explicit != "auto":
        chain = [explicit] + FALLBACKS.get(explicit, [])
        reason = "explicit"
    else:
        scores: dict[str, float] = {}
        purpose = scene.get("purpose") or scene.get("intent") or "explain"
        for rank, e in enumerate(PURPOSE_PREF.get(purpose, PURPOSE_PREF["explain"])):
            scores[e] = scores.get(e, 0) + 6 - 2 * rank
        for e, b in CATEGORY_BIAS.get(project.get("category", ""), {}).items():
            scores[e] = scores.get(e, 0) + b
        types = [el.get("type") for el in scene.get("elements", [])]
        n_data = sum(t in DATA_TYPES for t in types)
        n_draw = sum(t in DRAW_TYPES for t in types)
        if n_data:
            scores["motion"] = scores.get("motion", 0) + 2 + n_data
        if n_draw >= 2:
            scores["whiteboard"] = scores.get("whiteboard", 0) + 2
            scores["handdrawn"] = scores.get("handdrawn", 0) + 1
        emotion = (scene.get("emotion") or "").lower()
        if emotion in ("dread", "tension", "awe", "melancholy", "suspense"):
            scores["artistic"] = scores.get("artistic", 0) + 3
        if emotion in ("urgency", "shock", "surprise"):
            scores["kinetic"] = scores.get("kinetic", 0) + 2
        density = len(types) + sum(len(e.get("bars", []) or e.get("nodes", []) or e.get("items", [])) for e in scene.get("elements", []))
        if density >= 8:  # dense information: clean vector rendering reads best
            scores["motion"] = scores.get("motion", 0) + 3
            scores["artistic"] = scores.get("artistic", 0) - 3
            scores["handdrawn"] = scores.get("handdrawn", 0) - 1
        if not types and str(scene.get("narration", "")).strip():
            scores["kinetic"] = scores.get("kinetic", 0) + 3  # nothing to draw: let the words carry it
        if scene.get("params", {}).get("src"):
            scores["image_whiteboard"] = scores.get("image_whiteboard", 0) + 8
            scores["sweety_draw"] = scores.get("sweety_draw", 0) + 9  # part-ordered strokes + brush paint
        # cost: mild penalty for expensive engines on long scenes
        dur_hint = max(4.0, len(str(scene.get("narration", "")).split()) / 2.6)
        for e in list(scores):
            scores[e] -= COST_MS.get(e, 150) / 1000 * dur_hint * 0.15
        ranked = sorted(scores, key=lambda e: -scores[e])
        chain = ranked + [f for e in ranked for f in FALLBACKS.get(e, []) if f not in ranked]
        reason = "auto: " + ", ".join(f"{e}={scores[e]:.1f}" for e in ranked[:3])
    seen, final = set(), []
    for e in chain:
        if e not in seen:
            seen.add(e)
            final.append(e)
    usable = [e for e in final if e in ok]
    strict = is_premium(project) and not scene.get("allow_native")
    excluded = []
    if strict:
        # premium: never route to (or silently fall back to) a native drawing engine
        excluded = [e for e in usable if TIER.get(e) != "authentic"]
        usable = [e for e in usable if TIER.get(e) == "authentic"]
        if not usable:
            missing = [e for e in final if TIER.get(e) == "authentic" and e not in ok]
            raise EngineUnavailable(
                f"scene {scene.get('id')}: no authentic engine available for quality_profile="
                f"{project.get('quality_profile')!r} (requested {explicit!r}; unavailable: {missing or 'none in chain'}; "
                f"native engines excluded: {excluded}). Fix the dependency or set allow_native + native_reason.")
    if not usable:
        usable = ["motion"]
    return {"engine": usable[0], "fallbacks": usable[1:4], "requested": explicit, "reason": reason, "aspect": aspect,
            "skipped_unavailable": [e for e in final if e not in ok], "strict": strict,
            "excluded_native": excluded, "tier": TIER.get(usable[0]),
            "est_ms_per_frame": COST_MS.get(usable[0])}
