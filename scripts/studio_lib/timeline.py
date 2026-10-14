"""Narration-driven timeline.

Scene duration = lead + narration + tail (or min_duration), quantised to whole
frames so video and audio never drift. Word timings are shifted into scene time
so element cues ("cue:collapsed") land on the spoken word.
"""
from __future__ import annotations

from .config import FPS


def frames(sec: float, fps: int = FPS) -> int:
    return max(1, int(round(sec * fps)))


def build(scenes: list[dict], narr: dict[str, dict], fps: int = FPS, target: float | None = None,
          tolerance: float = 0.05, fit: bool = False) -> dict:
    rows = []
    t = 0.0
    for s in scenes:
        n = narr.get(s["id"])
        lead = float(s.get("pad", {}).get("lead", 0.35))
        tail = float(s.get("pad", {}).get("tail", 0.55))
        nd = n["duration"] if n else 0.0
        dur = max(float(s.get("min_duration", 0)), lead + nd + tail)
        if s.get("max_duration"):
            dur = min(dur, float(s["max_duration"]))
        rows.append({"id": s["id"], "lead": lead, "narr": nd, "dur": dur})
    total = sum(r["dur"] for r in rows)
    fit_note = None
    if fit and target and total < target * (1 - tolerance):
        # add breathing room (max +2.5 s per scene) to visual holds, never to narration
        short = target - total
        per = min(2.5, short / max(1, len(rows)))
        for r in rows:
            r["dur"] += per
        fit_note = f"added {per:.2f}s hold to each of {len(rows)} scenes"
    out = []
    for r, s in zip(rows, scenes):
        nf = frames(r["dur"], fps)
        dur = nf / fps
        n = narr.get(s["id"])
        words = [(r["lead"] + w_t, w) for w_t, w in (n["words"] if n else [])]
        out.append({"id": s["id"], "chapter": s.get("chapter"), "start": round(t, 4), "end": round(t + dur, 4),
                    "duration": dur, "frames": nf, "lead": r["lead"], "narration_duration": r["narr"],
                    "words": words})
        t += dur
    total = t
    status = "n/a"
    dev = None
    if target:
        dev = (total - target) / target
        status = "ok" if abs(dev) <= tolerance else ("short" if dev < 0 else "long")
    return {"fps": fps, "total": round(total, 3), "target": target, "deviation": dev, "status": status,
            "fit": fit_note, "scenes": out}


def fmt_ts(sec: float) -> str:
    sec = int(sec)
    h, m, s = sec // 3600, (sec % 3600) // 60, sec % 60
    return f"{h}:{m:02d}:{s:02d}" if h else f"{m}:{s:02d}"
