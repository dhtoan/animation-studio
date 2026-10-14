"""documentary-story-architect: structure, budgets and checks for long documentaries.

The agent writes the words; this module gives it a runtime-aware skeleton
(section budgets, word counts, scene counts), scaffolds project.json chapters
and scenes from a research dossier, and checks a finished script against the
structure (opening hook, context, development, complications, resolution with
stated uncertainty, significance, next-episode bridge).
"""
from __future__ import annotations

STRUCTURE = [
    # id, share of runtime, purpose, guidance
    ("opening", 0.06, "hook", "A documented fact, decision or conflict in the first 30–60 s; state the viewer promise."),
    ("setup", 0.14, "explain", "Historical context, place, people, stakes. Dates and names on screen."),
    ("development", 0.38, "story", "Chronological discoveries; each chapter opens with a question it answers."),
    ("complications", 0.20, "evidence", "Decisions, consequences, conflicting evidence — attribute contested claims."),
    ("resolution", 0.12, "reveal", "What happened, and what remains uncertain (say so explicitly)."),
    ("significance", 0.07, "metaphor", "Why it matters beyond the event; connect to the viewer's world."),
    ("next_episode", 0.03, "cta", "A natural, specific invitation to a related documentary."),
]

FORMATS = {"12-15": (12, 15), "15-20": (15, 20), "20-30": (20, 30), "30-45": (30, 45)}
DEFAULT_FORMAT = "15-20"
WPM = {"sapi": 130, "edge-tts": 140, "human": 145}


def plan(minutes: float = 20.0, voice: str = "edge-tts", scene_sec: float = 22.0) -> dict:
    total = minutes * 60
    wpm = WPM.get(voice, 140)
    rows = []
    for sid, share, purpose, guide in STRUCTURE:
        sec = total * share
        rows.append({"section": sid, "seconds": round(sec), "words": int(sec / 60 * wpm * 0.93),
                     "scenes": max(1, round(sec / scene_sec)), "purpose": purpose, "guidance": guide})
    return {"minutes": minutes, "wpm": wpm, "total_words": sum(r["words"] for r in rows),
            "total_scenes": sum(r["scenes"] for r in rows), "sections": rows,
            "note": "0.93 leaves room for ~0.9 s scene pads; real timing is measured from TTS."}


def scaffold(dossier: dict, minutes: float = 18.0, voice: str = "edge-tts") -> dict:
    """Chapters from the dossier's suggested chapters; one placeholder scene per planned beat."""
    pl = plan(minutes, voice)
    chapters = [{"id": f"ch{i + 1}", "title": c["title"], "mood": "tension" if i in (0, 3) else "wonder"}
                for i, c in enumerate(dossier.get("suggested_chapters", []))]
    scenes = []
    k = 0
    for ci, ch in enumerate(dossier.get("suggested_chapters", [])):
        claims = ch.get("claim_ids", [])
        for j in range(max(1, len(claims) // 2)):
            k += 1
            scenes.append({"id": f"s{k:02d}", "chapter": f"ch{ci + 1}", "purpose": "story", "narration": "",
                           "claims": claims[j * 2:(j + 1) * 2], "visual": "", "engine": "auto", "elements": []})
    return {"plan": pl, "chapters": chapters, "scenes": scenes}


def check(p: dict, tl: dict | None = None) -> dict:
    issues, notes = [], []
    scenes = p.get("scenes", [])
    purposes = [s.get("purpose") for s in scenes]
    if not scenes or purposes[0] not in ("hook", "reveal", "atmosphere"):
        issues.append("first scene is not a hook (opening must start on a documented fact/conflict)")
    if "cta" not in purposes[-2:]:
        issues.append("no next-episode bridge in the last two scenes")
    text = " ".join(s.get("narration", "") for s in scenes).lower()
    if not any(w in text for w in ("remains unclear", "we don't know", "historians disagree", "uncertain",
                                     "no one knows", "still debated", "unknown", "disputed", "estimates vary")):
        issues.append("resolution does not state what remains uncertain")
    if tl:
        mins = tl["total"] / 60
        lo, hi = next(((a, b) for a, b in sorted(FORMATS.values(), reverse=True) if a <= mins <= b + 0.5), (None, None))
        notes.append(f"runtime {mins:.1f} min" + (f" fits the {lo}–{hi} min format" if lo else " outside standard formats"))
    if any(not s.get("claims") for s in scenes if s.get("purpose") in ("evidence", "story", "explain")):
        notes.append("some factual scenes reference no claim ids")
    return {"issues": issues, "notes": notes, "status": "ok" if not issues else "needs_attention"}
