"""Narration-timed multi-scene pieces.

An authored piece (an animate crosshatch film, a lemo page) can draw several
scenes, one era per scene. Scenes opt in with `params.era: true` (or the era id).
After the timeline is built from real narration timing, every piece gets its own
clock: the eras of its scenes laid end to end in timeline order, each exactly as
long as its scene. Each scene then renders the piece at `offset = era start` for
its own duration, so the concatenated scenes equal the continuous piece.

`bridge_next` is true only when the next scene on the final timeline is the next
era of the same piece; otherwise the piece must cut cleanly (no half morph).
"""
from __future__ import annotations


def _key(scene: dict) -> tuple | None:
    prm = scene.get("params") or {}
    if not prm.get("era"):
        return None
    src = prm.get("piece") or prm.get("page")
    return (scene.get("engine"), src) if src else None


def assign(scenes: list[dict], tl_scenes: list[dict], fps: int) -> dict:
    """Mutates scene params (timing, offset, era); returns {piece key: timing} for reporting."""
    rows = {r["id"]: r for r in tl_scenes}
    order = [s for s in scenes if s["id"] in rows]
    groups: dict[tuple, list[dict]] = {}
    for s in order:
        k = _key(s)
        if k:
            groups.setdefault(k, []).append(s)
    out = {}
    for k, members in groups.items():
        t, eras = 0.0, []
        for s in members:
            d = rows[s["id"]]["frames"] / fps  # exact frame count of the scene
            # the era id names the piece's content: a Short segment keeps its source scene's era
            eras.append({"id": s.get("_source") or s["id"], "start": round(t, 6), "end": round(t + d, 6),
                         "bridge_next": False, "_scene": s["id"]})
            t += d
        ids = [s["id"] for s in order]
        for a, b in zip(eras, eras[1:]):
            ia = ids.index(a["_scene"])
            a["bridge_next"] = ia + 1 < len(ids) and ids[ia + 1] == b["_scene"]
        for e in eras:
            del e["_scene"]
        timing = {"fps": fps, "scenes": eras}
        for s, e in zip(members, eras):
            s["params"]["era"] = e["id"]
            s["params"]["timing"] = timing
            s["params"]["offset"] = e["start"]
        out[f"{k[0]}:{k[1]}"] = timing
    return out
