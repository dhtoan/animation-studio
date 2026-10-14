"""Shorts-to-long growth engine.

1. `propose(project, timeline)` scores long-form scenes for standalone appeal
   (hook/reveal/data purpose, numbers, emotion, explicit `short_candidate`) and
   groups neighbours into 15–60 s windows -> shorts/candidates.json.
2. A short in project.json is a list of *segments*. Each segment re-uses a long
   scene (`from`) but is re-rendered natively at 1080x1920: elements are
   recomposed with `pos_v` / `box_v` (or the vertical auto-layout), narration is
   rewritten for a standalone idea, and captions are burned in.
3. A CTA end-card segment points viewers to the parent video, and
   shorts/shorts-map.json records parent chapter + source timestamps for the
   YouTube "Related video" field (set manually in YouTube Studio).

No cropping of the 16:9 master is ever used.
"""
from __future__ import annotations

import copy
import json
import re
import time
from pathlib import Path

from . import audio as A
from . import ffmpeg as FF
from . import subtitles, timeline
from .config import RenderSettings
from .engines import availability
from .render import render_all, scene_job
from .router import route
from .spec import load_project, save_json
from .tts import synthesize

DEFAULT_CTA = "The full story is in the related video. Tap it to watch how it all unraveled."


def _score(scene: dict) -> tuple[float, list[str]]:
    why = []
    sc = 0.0
    pur = scene.get("purpose", "")
    if pur in ("hook", "reveal", "data", "metaphor", "evidence"):
        sc += 2
        why.append(f"purpose={pur}")
    narr = scene.get("narration", "")
    if re.search(r"\$?\d[\d,.]*\s*(billion|million|percent|%|x)?", narr, re.I):
        sc += 1.5
        why.append("concrete number")
    if "?" in narr:
        sc += 1
        why.append("open question")
    if scene.get("emotion") in ("shock", "surprise", "suspense", "dread", "urgency"):
        sc += 1
        why.append(f"emotion={scene['emotion']}")
    types = {e.get("type") for e in scene.get("elements", [])}
    if types & {"stamp", "counter", "bar_chart", "line_chart"}:
        sc += 1
        why.append("visual payoff")
    if scene.get("short_candidate"):
        sc += 3
        why.append("author-flagged")
    return sc, why


def propose(p: dict, tl: dict, n: int = 5) -> list[dict]:
    rows = {r["id"]: r for r in tl["scenes"]}
    scored = []
    for i, s in enumerate(p["scenes"]):
        sc, why = _score(s)
        scored.append((sc, i, why))
    scored.sort(reverse=True)
    used = set()
    out = []
    for sc, i, why in scored:
        if len(out) >= n or sc < 2:
            break
        if i in used:
            continue
        # grow a window around the seed until 20-50 s of source material
        win = [i]
        dur = rows[p["scenes"][i]["id"]]["duration"]
        lo, hi = i, i
        while dur < 20 and (lo > 0 or hi < len(p["scenes"]) - 1):
            nxt = hi + 1 if hi + 1 < len(p["scenes"]) and (hi + 1) not in used else None
            if nxt is not None and p["scenes"][nxt].get("chapter") == p["scenes"][i].get("chapter"):
                hi = nxt
                win.append(hi)
            elif lo - 1 >= 0 and (lo - 1) not in used and p["scenes"][lo - 1].get("chapter") == p["scenes"][i].get("chapter"):
                lo -= 1
                win.insert(0, lo)
            else:
                break
            dur += rows[p["scenes"][win[-1] if win[-1] == hi else lo]["id"]]["duration"]
        if dur > 55:
            win = win[:2]
        used.update(win)
        ids = [p["scenes"][k]["id"] for k in sorted(win)]
        out.append({"seed": p["scenes"][i]["id"], "score": sc, "why": why, "source_scenes": ids,
                    "chapter": p["scenes"][i].get("chapter"),
                    "source_start": rows[ids[0]]["start"], "source_end": rows[ids[-1]]["end"],
                    "hook_line": p["scenes"][i].get("narration", "").split(".")[0][:120]})
    return out


def _segments(p: dict, short: dict) -> list[dict]:
    byid = {s["id"]: s for s in p["scenes"]}
    segs = []
    for k, seg in enumerate(short.get("segments", []), 1):
        base = copy.deepcopy(byid[seg["from"]]) if seg.get("from") else {
            "engine": "kinetic", "elements": [], "params": {}, "camera": {"move": "drift"}, "transition": "cut",
            "pad": {"lead": 0.2, "tail": 0.4}, "illustrative": True, "_project_dir": p["_dir"]}
        for key in ("narration", "engine", "camera", "transition", "min_duration", "audio", "purpose", "pad"):
            if key in seg:
                base[key] = copy.deepcopy(seg[key])
        if "params" in seg:  # merge, so a segment can override cues without losing the scene's data
            base["params"] = {**(base.get("params") or {}), **copy.deepcopy(seg["params"])}
        if "elements" in seg:
            base["elements"] = copy.deepcopy(seg["elements"])
        base["pad"] = seg.get("pad", {"lead": 0.15, "tail": 0.35})
        from . import design_system as _ds
        from . import styles as _styles

        _ds.apply_look(base)
        _styles.apply_style(base)  # art_style -> engine + default params, same as the long video
        base["id"] = f"{short['id']}-{k:02d}"
        base["_source"] = seg.get("from")
        base["_captions"] = seg.get("captions", base.get("engine") != "kinetic")
        segs.append(base)
    cta = short.get("cta", DEFAULT_CTA)
    if cta:
        segs.append({"id": f"{short['id']}-cta", "engine": "kinetic", "narration": cta,
                     "params": {"emphasis": ["full", "story", "related", "video."], "max_words": 3},
                     "elements": [{"type": "text", "text": short.get("cta_label", "FULL STORY: TAP THE RELATED VIDEO"),
                                   "style": "h3", "pos_v": [0.5, 0.82], "color": "accent", "at": 0.2,
                                   "font": "sans_bold"}],
                     "camera": {"move": "static"}, "transition": "crossfade", "pad": {"lead": 0.15, "tail": 0.6},
                     "illustrative": False, "_project_dir": p["_dir"], "_captions": False})
    return segs


def build_shorts(pdir: Path, quality: str = "preview", workers: int = 3, only: list[str] | None = None,
                 log=print) -> list[dict]:
    p = load_project(pdir)
    tl_long_f = pdir / "storyboard" / "timeline.json"
    tl_long = json.loads(tl_long_f.read_text(encoding="utf-8")) if tl_long_f.exists() else None
    if tl_long:
        save_json(pdir / "shorts" / "candidates.json", {"candidates": propose(p, tl_long)})
    avail = availability()
    st = RenderSettings("short", quality)
    results = []
    chapters = {c["id"]: c for c in p.get("chapters", [])}
    badge = "FICTIONAL STORY" if p.get("fictional") else None
    for short in p.get("shorts", []):
        if only and short["id"] not in only:
            continue
        t0 = time.time()
        segs = _segments(p, short)
        from .pipeline import tts_config

        narr = synthesize({s["id"]: s["narration"] for s in segs if s.get("narration")}, tts_config(p),
                          pdir / "audio" / "narration", log=log)
        tl = timeline.build(segs, narr, p.get("fps", 30))
        out_dir = pdir / "scenes" / f"short-{quality}"
        out_dir.mkdir(parents=True, exist_ok=True)
        jobs, prev = [], None
        for s, r in zip(segs, tl["scenes"]):
            s["_work_dir"] = str(pdir / "scenes")
            caps = None
            if s.get("_captions") and r["words"]:
                caps = [[c["start"], c["end"], c["text"], [list(w) for w in c["words"]]]
                        for c in subtitles.chunk(r["words"], r["duration"], max_chars=34, max_dur=2.6)]
            rt = route(s, p, avail, aspect="9:16")
            j = scene_job(s, r, st, p.get("theme", "documentary"), p.get("theme_overrides", {}), prev,
                          badge if s.get("illustrative", True) else None, caps, rt["engine"], rt["fallbacks"], out_dir)
            jobs.append(j)
            prev = {"id": j["id"], "hash": j["hash"], "engine": rt["engine"], "scene": s, "tl": r,
                    "captions": caps, "out": j["out"]}
        res = render_all(jobs, workers=workers, log=log)
        failed = [r for r in res if r.get("status") != "done"]
        rec = {"id": short["id"], "title": short.get("title"), "duration": tl["total"], "segments": len(segs)}
        if failed:
            rec.update({"status": "failed", "errors": [f["attempts"][-1] for f in failed if f.get("attempts")]})
            results.append(rec)
            continue
        # audio
        mood = chapters.get(short.get("chapter"), {}).get("mood", "tension")
        voice = [(r["start"] + r["lead"], narr[r["id"]]["wav"]) for r in tl["scenes"] if r["id"] in narr]
        sfx = [(0.0, "impact")] + [(r["start"], "whoosh") for r in tl["scenes"][1:]
                                     if (s := next(x for x in segs if x["id"] == r["id"])).get("transition") not in ("cut", None)]
        mix_wav = pdir / "audio" / f"{short['id']}-mix.wav"
        A.mix(tl["total"], voice, [(0, tl["total"], mood)], sfx, mix_wav, p.get("music", {}).get("volume", 0.16) * 1.15)
        # subtitles sidecar
        cues = []
        for r in tl["scenes"]:
            for c in subtitles.chunk(r["words"], r["duration"], max_chars=34, max_dur=2.6):
                cues.append({**c, "start": c["start"] + r["start"], "end": min(c["end"], r["duration"]) + r["start"]})
        subtitles.write_srt(cues, pdir / "shorts" / f"{short['id']}.srt")
        lst = pdir / "shorts" / f"{short['id']}-concat.txt"
        res_by = {r["id"]: r for r in res}
        lst.write_text("".join(f"file '{Path(res_by[j['id']]['out']).as_posix()}'\n" for j in jobs), encoding="utf-8")
        silent = pdir / "shorts" / f"{short['id']}.silent.mp4"
        FF.run(["-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])
        name = f"{short['id']}.mp4" if quality == "final" else f"{short['id']}-{quality}.mp4"
        final = pdir / "shorts" / name
        FF.run(["-y", "-i", str(silent), "-i", str(mix_wav), "-map", "0:v", "-map", "1:a", "-c:v", "copy",
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k", "-shortest",
                "-movflags", "+faststart", str(final)])
        silent.unlink(missing_ok=True)
        lst.unlink(missing_ok=True)
        lo, hi = short.get("duration_range", [15, 60])
        rec.update({"status": "done", "output": str(final), "in_range": lo <= tl["total"] <= hi,
                    "duration_range": [lo, hi], "build_sec": round(time.time() - t0, 1),
                    "engines": [r.get("engine") for r in res]})
        log(f"[shorts] {short['id']} {tl['total']:.1f}s -> {final.name} (range {lo}-{hi}s: "
            f"{'ok' if rec['in_range'] else 'OUT OF RANGE'})")
        results.append(rec)
    write_map(p, pdir, tl_long, results)
    save_json(pdir / "reports" / f"shorts-{quality}.json", {"shorts": results})
    return results


def write_map(p: dict, pdir: Path, tl_long: dict | None, results: list[dict]) -> Path:
    rows = {r["id"]: r for r in (tl_long or {}).get("scenes", [])}
    chapters = {c["id"]: c for c in p.get("chapters", [])}
    out = []
    for sh in p.get("shorts", []):
        src = [seg["from"] for seg in sh.get("segments", []) if seg.get("from")]
        ts = [(rows[s]["start"], rows[s]["end"]) for s in src if s in rows]
        res = next((r for r in results if r["id"] == sh["id"]), {})
        out.append({
            "short_id": sh["id"], "title": sh.get("title"), "file": res.get("output"),
            "duration": res.get("duration"), "parent": {"title": p["title"], "slug": p["slug"],
                                                        "youtube_id": p.get("youtube_id", "<set after upload>")},
            "parent_chapter": {"id": sh.get("chapter"), "title": chapters.get(sh.get("chapter"), {}).get("title")},
            "source_scenes": src,
            "source_timestamps": [{"start": timeline.fmt_ts(a), "end": timeline.fmt_ts(b), "start_sec": a, "end_sec": b}
                                  for a, b in ts],
            "deep_link": (f"https://youtu.be/{p['youtube_id']}?t={int(ts[0][0])}" if p.get("youtube_id") and ts
                          else "<https://youtu.be/VIDEO_ID?t=SECONDS after upload>"),
            "related_video_setup": "YouTube Studio > Content > Shorts > (this Short) > Details > Related video > select the parent video.",
        })
    f = pdir / "shorts" / "shorts-map.json"
    save_json(f, {"parent": p["title"], "shorts": out})
    return f
