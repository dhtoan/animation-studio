"""Cached, resumable, parallel scene rendering with retries and engine fallback.

Each scene is rendered to its own MP4 keyed by a content hash of everything that
affects its pixels (scene spec, resolved timing, word timings, theme, render
settings, engine code version, and the previous scene when a transition blends
with it). Unchanged scenes are never re-rendered; an interrupted build resumes
where it stopped because finished scenes are already on disk.
"""
from __future__ import annotations

import hashlib
import json
import time
import traceback
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

from . import VERSION
from .config import SKILL_ROOT, RenderSettings
from .design import Theme

_ENGINE_SRC = None


def engine_code_hash() -> str:
    global _ENGINE_SRC
    if _ENGINE_SRC is None:
        h = hashlib.sha256()
        files = sorted((SKILL_ROOT / "scripts" / "studio_lib" / "engines").glob("*.py"))
        files += [SKILL_ROOT / "scripts" / "studio_lib" / f for f in ("draw.py", "design.py")]
        for f in files:
            h.update(f.read_bytes())
        _ENGINE_SRC = h.hexdigest()[:12]
    return _ENGINE_SRC


_SKIP_DIRS = {"node_modules", "renders", "dist", ".git", "__pycache__", "_work"}


def asset_fingerprint(scene: dict) -> str | None:
    """Content hash of the local files a scene's engine reads (piece dirs, pages, images), so editing
    a film.js / scenes.js / illustration re-renders the scene instead of reusing a stale cache."""
    prm = scene.get("params") or {}
    base = Path(scene.get("_project_dir", "."))
    h = hashlib.sha256()
    found = False
    for key in ("piece", "page", "src", "timeline"):
        v = prm.get(key)
        if not isinstance(v, str) or ":" in v.split("/")[0]:  # upstream:/lemo:/mg: pages are pinned checkouts
            continue
        p = Path(v) if Path(v).is_absolute() else base / v
        if p.is_file() and key == "page":
            p = p.parent  # a page loads its sibling modules (film.js, timing.js, ...)
        files = [p] if p.is_file() else sorted(
            x for x in p.rglob("*") if x.is_file() and not (_SKIP_DIRS & set(x.relative_to(p).parts))) if p.is_dir() else []
        if p.is_file() and p.with_suffix(".parts.json").is_file():
            files.append(p.with_suffix(".parts.json"))  # sweety_draw drawing order
        for x in files:
            found = True
            h.update(str(x.relative_to(p) if p.is_dir() else x.name).encode())
            h.update(x.read_bytes())
    return h.hexdigest()[:12] if found else None


def _clean(scene: dict) -> dict:
    return {k: v for k, v in scene.items() if not k.startswith("_") and k not in ("validation", "narration_notes")}


def scene_job(scene: dict, tl: dict, settings: RenderSettings, theme_name: str, theme_over: dict,
              prev: dict | None, badge: str | None, captions: list | None, engine: str, fallbacks: list[str],
              out_dir: Path) -> dict:
    payload = {
        "v": VERSION, "code": engine_code_hash(), "scene": _clean(scene), "engine": engine,
        "dur": tl["duration"], "frames": tl["frames"], "words": tl["words"], "settings": settings.key(),
        "theme": [theme_name, theme_over], "badge": badge, "captions": captions,
        "assets": asset_fingerprint(scene),
        "prev": prev["hash"] if (prev and scene.get("transition", "cut") not in ("cut", None)) else None,
    }
    h = hashlib.sha256(json.dumps(payload, sort_keys=True, default=str).encode()).hexdigest()[:12]
    return {"id": scene["id"], "hash": h, "out": str(out_dir / f"{scene['id']}-{h}.mp4"),
            "manifest": str(out_dir / f"{scene['id']}-{h}.json"), "scene": scene, "tl": tl,
            "settings": settings.key(), "fmt": settings.fmt, "quality": settings.quality,
            "theme": theme_name, "theme_over": theme_over, "prev": prev, "badge": badge,
            "captions": captions, "engine": engine, "fallbacks": fallbacks}


def _make_engine(name, job, scene, tl, prev_last=None):
    from .engines import ENGINES, SceneContext

    st = RenderSettings(job["fmt"], job["quality"])
    ctx = SceneContext(scene=scene, width=st.width, height=st.height, ss=st.ss, fps=st.fps,
                       duration=tl["duration"], theme=Theme(job["theme"], job["theme_over"]),
                       fmt=job["fmt"], words=[tuple(w) for w in tl["words"]], prev_last=prev_last,
                       captions=job["captions"] or [], badge=job["badge"])
    return ENGINES[name](ctx), st


def _prev_last_frame(job):
    prev = job.get("prev")
    if not prev or job["scene"].get("transition", "cut") in ("cut", None):
        return None
    try:
        eng, st = _make_engine(prev["engine"], {**job, "captions": prev.get("captions"), "badge": None}, prev["scene"], prev["tl"])
        img = eng.frame(prev["tl"]["duration"] - 1 / st.fps)
        if hasattr(eng, "close"):
            eng.close()
        return img
    except Exception:
        return None


def render_job(job: dict) -> dict:
    """Worker entry (runs in a subprocess)."""
    from .ffmpeg import FrameWriter

    out, man = Path(job["out"]), Path(job["manifest"])
    if out.exists() and man.exists():
        m = json.loads(man.read_text(encoding="utf-8"))
        if m.get("status") == "done":
            return {**m, "cached": True}
    tl = job["tl"]
    attempts = []
    prev_last = _prev_last_frame(job)
    for name in [job["engine"]] + list(job["fallbacks"]):
        for attempt in range(int(job.get("retries", 1)) + 1):
            t0 = time.time()
            fw = None
            eng = None
            try:
                eng, st = _make_engine(name, job, job["scene"], tl, prev_last)
                fw = FrameWriter(out, st.width, st.height, st.fps, crf=st.crf, preset=st.preset)
                for i in range(tl["frames"]):
                    fw.write(eng.frame(i / st.fps))
                fw.close()
                if hasattr(eng, "close"):
                    eng.close()
                rec = {"id": job["id"], "hash": job["hash"], "status": "done", "engine": name,
                       "requested_engine": job["engine"], "fallback_used": name != job["engine"],
                       "frames": tl["frames"], "duration": tl["duration"], "render_sec": round(time.time() - t0, 2),
                       "ms_per_frame": round((time.time() - t0) / max(1, tl["frames"]) * 1000, 1),
                       "attempts": attempts + [{"engine": name, "ok": True}], "out": str(out),
                       "settings": job["settings"]}
                man.write_text(json.dumps(rec, indent=2), encoding="utf-8")
                return {**rec, "cached": False}
            except Exception as e:  # noqa: BLE001
                if fw:
                    fw.abort()
                if eng is not None and hasattr(eng, "close"):
                    try:
                        eng.close()
                    except Exception:
                        pass
                attempts.append({"engine": name, "ok": False, "error": f"{type(e).__name__}: {e}",
                                 "trace": traceback.format_exc()[-1200:]})
                # deterministic engine errors won't fix themselves on retry
                if isinstance(e, (ValueError, KeyError, FileNotFoundError, TypeError, AttributeError)):
                    break
    rec = {"id": job["id"], "hash": job["hash"], "status": "failed", "attempts": attempts, "out": str(out)}
    man.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return {**rec, "cached": False}


def render_all(jobs: list[dict], workers: int = 2, retries: int = 1, log=print) -> list[dict]:
    """Render all jobs in parallel; returns results in timeline order."""
    for j in jobs:
        j["retries"] = retries
    done: dict[str, dict] = {}
    results: list[dict] = []
    pending = list(jobs)
    t_start = time.time()
    total_frames = sum(j["tl"]["frames"] for j in jobs)
    frames_done = 0

    def ready(j):
        # transitions re-render the previous scene's final frame deterministically,
        # so scenes never wait on each other and all workers stay busy
        return True

    with ProcessPoolExecutor(max_workers=max(1, workers)) as ex:
        futs = {}
        while pending or futs:
            for j in [j for j in pending if ready(j)][: max(1, workers * 2) - len(futs)]:
                pending.remove(j)
                futs[ex.submit(render_job, j)] = j
            for f in as_completed(list(futs)):
                j = futs.pop(f)
                try:
                    r = f.result()
                except Exception as e:  # noqa: BLE001
                    r = {"id": j["id"], "status": "failed", "attempts": [{"error": str(e)}]}
                done[j["id"]] = r
                results.append(r)
                frames_done += j["tl"]["frames"]
                el = time.time() - t_start
                eta = el / max(1, frames_done) * (total_frames - frames_done)
                tag = "cached" if r.get("cached") else r.get("status")
                eng = r.get("engine", "?")
                fb = " (fallback)" if r.get("fallback_used") else ""
                log(f"[render] {len(done)}/{len(jobs)} {j['id']:<10} {tag:<7} {eng}{fb} "
                    f"{r.get('ms_per_frame', '-')} ms/f  | {frames_done}/{total_frames} frames, ETA {eta:,.0f}s")
                break
    order = {j["id"]: i for i, j in enumerate(jobs)}
    return sorted(results, key=lambda r: order.get(r["id"], 0))
