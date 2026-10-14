"""Art direction + shot planning + continuity (V2).

* `style_bible(project)`  palette roles, type, characters, lighting per chapter mood
* `propose_styles(project)` 1 recommended + 2 alternative looks from operational styles
* `plan_shots(project)`   fills missing shot type / camera / transition from purpose + emotion,
                          following an energy arc per chapter (no edits to explicit choices)
* `continuity(project)`   checks: engine streaks, repeated shot types, transition budget,
                          character colour consistency, chapter openers, impact budget

Shot grammar distilled (paraphrased, Apache-2.0 attribution in THIRD_PARTY_NOTICES)
from video-shotcraft's aesthetic rules and energy-arc sequence guide, and from
lemo-opuscar DIRECTOR.md's treatment -> shot list -> cue map process (MIT).
"""
from __future__ import annotations

from . import styles as ST

LIGHTING = {"tension": "low-key, cool shadows, single warm accent", "wonder": "high-key, warm, open sky",
            "dark": "night, pools of light, desaturated", "resolve": "dawn light, warm rising", "drive": "bright, crisp, high contrast"}

SHOT_BY_PURPOSE = {
    "hook": ("insert", "push_in"), "title": ("wide", "drift"), "reveal": ("close", "push_in"),
    "explain": ("medium", "drift"), "process": ("wide", "pan_right"), "data": ("medium", "push_in"),
    "comparison": ("medium", "static"), "timeline": ("wide", "pan_right"), "story": ("medium", "pan_right"),
    "character": ("medium", "push_in"), "metaphor": ("wide", "pull_out"), "atmosphere": ("establishing", "pull_out"),
    "evidence": ("close", "push_in"), "quote": ("close", "static"), "recreation": ("wide", "drift"),
    "tutorial": ("close", "static"), "cta": ("medium", "static"), "illustration": ("wide", "drift"),
}
ENERGY = {"hook": 3, "reveal": 3, "data": 2, "story": 2, "explain": 1, "process": 1, "metaphor": 2, "atmosphere": 1,
          "evidence": 2, "timeline": 1, "quote": 2, "cta": 1, "character": 2, "comparison": 2, "tutorial": 1,
          "recreation": 2, "illustration": 1, "title": 2}
IMPACT_TYPES = {"stamp"}


def style_bible(p: dict) -> dict:
    from .design import Theme

    th = Theme(p.get("theme", "documentary"), p.get("theme_overrides", {}))
    ad = p.get("art_direction", {})
    return {
        "theme": th.name, "palette": th.colors,
        "colour_meaning": {"accent": "attention", "negative": "loss / failure", "positive": "growth / cash in",
                           "cool": "systems / neutral"},
        "typography": {"data": "sans / sans_bold", "kinetic": "display", "drawn": "hand / hand_bold", "artistic": "serif"},
        "characters": ad.get("characters", {}),
        "lighting_by_chapter": {c["id"]: LIGHTING.get(c.get("mood", "tension")) for c in p.get("chapters", [])},
        "rules": ad.get("rules", []),
        "style_id": ad.get("style_id"),
    }


def propose_styles(p: dict, n_alt: int = 2) -> dict:
    """Score operational styles against the project's scene purposes."""
    purposes = [s.get("purpose", "explain") for s in p.get("scenes", [])] or ["explain"]
    scored = []
    for s in ST.load():
        if ST.status(s["id"]) != "operational":
            continue
        fit = sum(1 for x in purposes if x in s.get("best_for", []))
        cat_bonus = 2 if p.get("category") in s.get("best_for", []) else 0
        cost = (s.get("perf_ms") or 300) / 1000
        scored.append((fit + cat_bonus - cost, s["id"]))
    scored.sort(reverse=True)
    ids = [i for _, i in scored]
    return {"recommended": ids[:1], "alternatives": ids[1:1 + n_alt], "considered": len(ids),
            "note": "only styles verified as operational on this machine are proposed"}


def plan_shots(p: dict) -> list[str]:
    """Fill missing shot / camera / transition from purpose + chapter structure.
    Explicit values in the spec are never changed. Returns a log of what was filled."""
    log = []
    prev_ch = None
    for i, s in enumerate(p.get("scenes", [])):
        shot_t, cam = SHOT_BY_PURPOSE.get(s.get("purpose", "explain"), ("medium", "drift"))
        if not s.get("shot"):
            s["shot"] = {"type": shot_t, "angle": "eye-level"}
            log.append(f"{s['id']}: shot={shot_t}")
        if not s.get("camera"):
            s["camera"] = {"move": cam, "amount": 0.06}
            log.append(f"{s['id']}: camera={cam}")
        if not s.get("transition"):
            if i > 0 and s.get("chapter") != prev_ch:
                s["transition"] = "fade_black" if ENERGY.get(s.get("purpose"), 1) <= 1 else "crossfade"
            else:
                s["transition"] = "cut"
            log.append(f"{s['id']}: transition={s['transition']}")
        prev_ch = s.get("chapter")
    return log


def continuity(p: dict) -> dict:
    scenes = p.get("scenes", [])
    issues, notes = [], []
    # engine streaks
    streak = 1
    for a, b in zip(scenes, scenes[1:]):
        if a.get("engine") == b.get("engine") and a.get("engine") not in (None, "auto"):
            streak += 1
            if streak == 4:
                issues.append(f"{b['id']}: 4+ consecutive '{b['engine']}' scenes (vary the look)")
        else:
            streak = 1
    # shot repetition
    for x, y, z in zip(scenes, scenes[1:], scenes[2:]):
        ts = [(s.get("shot") or {}).get("type") for s in (x, y, z)]
        if ts[0] and ts[0] == ts[1] == ts[2]:
            notes.append(f"{z['id']}: three '{ts[0]}' shots in a row")
    # transitions budget (special = not cut/crossfade/fade)
    special = {}
    for s in scenes:
        tr = s.get("transition", "cut")
        tr = tr.get("type") if isinstance(tr, dict) else tr
        if tr not in ("cut", "crossfade", "fade", "fade_black", None):
            special.setdefault(s.get("chapter"), []).append(tr)
    for ch, trs in special.items():
        if len(trs) > 2:
            notes.append(f"chapter {ch}: {len(trs)} special transitions ({', '.join(trs)}) — budget is 1–2")
    # impacts
    impacts = sum(1 for s in scenes for e in s.get("elements", []) if e.get("type") in IMPACT_TYPES)
    if impacts > 3:
        notes.append(f"{impacts} full-frame impacts (stamps) — house rule is <= 3 per video")
    # character colour consistency
    colours = {}
    for s in scenes:
        for e in s.get("elements", []):
            if e.get("type") == "character":
                for c in s.get("characters", []) or ["_unnamed"]:
                    colours.setdefault(c, set()).add(e.get("color", "cool"))
    for c, cs in colours.items():
        if len(cs) > 1:
            issues.append(f"character {c}: inconsistent colours {sorted(cs)}")
    # energy arc per chapter: chapter opener should not be the lowest-energy scene of its chapter
    by_ch = {}
    for s in scenes:
        by_ch.setdefault(s.get("chapter"), []).append(ENERGY.get(s.get("purpose"), 1))
    for ch, es in by_ch.items():
        if len(es) > 2 and es[0] < max(es) - 1:
            notes.append(f"chapter {ch}: opener energy {es[0]} vs chapter peak {max(es)} — consider a stronger re-hook")
    return {"issues": issues, "notes": notes, "impacts": impacts}
