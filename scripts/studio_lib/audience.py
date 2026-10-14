"""audience-50plus-intelligence: a *testable* presentation profile, not a stereotype.

The profile encodes comfortable defaults that also follow general accessibility
guidance (WCAG 2.2 contrast ratios, caption reading speed, legible type), and
`audit(project, timeline)` measures a project against it. Preferences must be
validated with real retention data (`analytics.py`) — the A/B variants below
exist precisely so the channel can test pacing and style instead of assuming.
"""
from __future__ import annotations

import re

from .design import TYPE_SCALE, Theme

PROFILE_50PLUS = {
    "narration_wpm": [125, 150],          # comfortable documentary pace
    "min_text_role": "body",              # nothing smaller than body (3.4 % of short side ≈ 37 px @1080)
    "min_contrast": 4.5,                  # WCAG AA for normal text
    "caption_max_cps": 17,                # characters per second
    "caption_min_duration": 1.2,
    "min_scene_seconds": 6.0,             # avoid rapid-fire cutting
    "max_special_transitions_per_10min": 6,
    "music_duck_db": -18,                 # music well under narration
    "loudness_lufs": -14,
    "dates_and_names_on_screen": True,    # chronology support
    "chapter_recaps": True,
}

AB_VARIANTS = {
    "pace": {"A": {"voice_rate": -1, "pad_tail": 0.7}, "B": {"voice_rate": 0, "pad_tail": 0.5}},
    "visual_density": {"A": "one idea per scene", "B": "two ideas per scene"},
    "style_mix": {"A": "illustration-led (handdrawn/archival)", "B": "data-led (motion/maps)"},
    "how_to_test": "Publish comparable episodes with each variant; compare average percentage viewed and "
                   "returning viewers for the 55–64 and 65+ age groups in YouTube Analytics. Change one variable at a time.",
}


def _lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    r, g, b = c
    return 0.2126 * ch(r) + 0.7152 * ch(g) + 0.0722 * ch(b)


def contrast(a, b) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return round((la + 0.05) / (lb + 0.05), 2)


from .design import ENGINE_BG  # noqa: E402  (single source of truth)
ENGINE_FG = {"whiteboard": "ink", "handdrawn": "ink", "motion": "light", "kinetic": "light", "artistic": "light",
             "image_whiteboard": "ink", "archival": "ink"}


def audit(p: dict, tl: dict | None = None, profile: dict = PROFILE_50PLUS) -> dict:
    th = Theme(p.get("theme", "documentary"), p.get("theme_overrides", {}))
    issues, notes = [], []
    small = ("label", "small", "caption")
    for s in p.get("scenes", []):
        eng = s.get("engine")
        bgr = ENGINE_BG.get(eng, "night")
        bg = bgr if isinstance(bgr, tuple) else th.c(bgr)
        for e in s.get("elements", []):
            if e.get("type") == "text":
                if e.get("style") in small and len(e.get("text", "")) > 18:
                    issues.append(f"{s['id']}: long text at '{e.get('style')}' size — use body or larger")
                from .design import ensure_contrast

                fg = th.c(e.get("color"), ENGINE_FG.get(eng, "ink"))
                if not (s.get("params") or {}).get("allow_low_contrast"):
                    fg = ensure_contrast(fg, bg, profile["min_contrast"])  # the renderer applies the same correction
                cr = contrast(fg, bg)
                if cr < profile["min_contrast"]:
                    issues.append(f"{s['id']}: text '{e.get('text', '')[:24]}' contrast {cr}:1 < {profile['min_contrast']}:1")
    if tl:
        words = sum(len(s.get("narration", "").split()) for s in p.get("scenes", []))
        narr_sec = sum(r["narration_duration"] for r in tl["scenes"])
        wpm = round(words / max(1e-6, narr_sec) * 60, 1)
        lo, hi = profile["narration_wpm"]
        (issues if not lo - 10 <= wpm <= hi + 10 else notes).append(
            f"narration pace {wpm} wpm (comfortable range {lo}–{hi})")
        short = [r["id"] for r in tl["scenes"] if r["duration"] < profile["min_scene_seconds"]]
        if len(short) > max(2, len(tl["scenes"]) // 6):
            notes.append(f"{len(short)} scenes under {profile['min_scene_seconds']} s: {', '.join(short[:8])}")
        minutes = tl["total"] / 60
        special = sum(1 for s in p["scenes"] if str((s.get("transition") or {}).get("type") if isinstance(s.get("transition"), dict)
                                                       else s.get("transition")) in ("whip", "glitch", "crash_zoom", "flash_cut", "zoom_through"))
        if special > profile["max_special_transitions_per_10min"] * max(1, minutes / 10):
            issues.append(f"{special} high-energy transitions in {minutes:.1f} min — calmer pacing recommended")
    years = sum(1 for s in p.get("scenes", []) for e in s.get("elements", [])
                if re.search(r"\b(1[6-9]\d\d|20\d\d)\b", str(e.get("text", "")) + str(e.get("events", ""))))
    if profile["dates_and_names_on_screen"] and p.get("category") == "history" and years == 0:
        issues.append("no dates on screen in a history project — show dates/names to support chronology")
    return {"profile": profile, "issues": issues, "notes": notes, "ab_variants": AB_VARIANTS,
            "status": "ok" if not issues else "needs_attention"}
