"""End-to-end orchestration for one project.

Topic -> Research -> Script -> Storyboard -> Art direction -> Shot plan -> Engine
selection -> Assets -> Narration -> Timeline -> Scene render -> Audio mix ->
Subtitles -> Assembly -> Shorts -> QA -> SEO -> Reports

Every stage writes its artefact to the project folder and is skipped when its
inputs are unchanged, so `build` is safe to re-run after an interruption.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from . import audio as A
from . import ffmpeg as FF
from . import research, subtitles, timeline
from .config import RenderSettings
from .engines import availability
from .render import render_all, scene_job
from .router import EngineUnavailable, route
from .spec import ensure_dirs, load_project, save_json, validate
from .tts import synthesize


class Log:
    def __init__(self, path: Path):
        self.path = path
        path.parent.mkdir(parents=True, exist_ok=True)
        self.f = open(path, "a", encoding="utf-8")

    def __call__(self, msg: str):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        self.f.write(line + "\n")
        self.f.flush()


def narration_texts(scenes: list[dict]) -> dict[str, str]:
    return {s["id"]: s["narration"].strip() for s in scenes if str(s.get("narration", "")).strip()}


def _music_plan(p: dict, tl: dict) -> list[tuple[float, float, str]]:
    moods = {c["id"]: c.get("mood", "tension") for c in p.get("chapters", [])}
    plan: list[list] = []
    for r in tl["scenes"]:
        mood = moods.get(r["chapter"], p.get("music", {}).get("mood", "tension"))
        if plan and plan[-1][2] == mood:
            plan[-1][1] = r["end"]
        else:
            plan.append([r["start"], r["end"], mood])
    return [tuple(x) for x in plan]


def _sfx_events(scenes: list[dict], tl: dict, auto: bool = True) -> list[tuple[float, str]]:
    ev = []
    from .engines.base import SceneContext
    from .design import Theme

    for s, r in zip(scenes, tl["scenes"]):
        ctx = SceneContext(scene=s, width=16, height=9, ss=1, fps=30, duration=r["duration"], theme=Theme(),
                           words=r["words"])
        for x in s.get("audio", {}).get("sfx", []) or []:
            ev.append((r["start"] + ctx.resolve_time(x.get("at")), x.get("name", "pop")))
        if auto:
            tr = s.get("transition", "cut")
            tr = tr.get("type") if isinstance(tr, dict) else tr
            if tr in ("whip", "push", "zoom_through", "wipe", "slide_up", "blinds", "iris"):
                ev.append((max(0.0, r["start"] - 0.15), "whoosh"))
            elif tr == "crash_zoom":
                ev.append((r["start"] + 0.38, "impact"))
            elif tr in ("flash_cut", "glitch"):
                ev.append((r["start"], "pop" if tr == "flash_cut" else "tick"))
            for el in s.get("elements", []):
                if el.get("type") == "stamp":
                    ev.append((r["start"] + ctx.resolve_time(el.get("at")) + 0.3, "stamp"))
    return ev


def plan(pdir: Path, log=print, avail=None) -> dict:
    """Validate + route every scene. No rendering."""
    from . import direction, styles

    p = load_project(pdir)
    avail = avail or availability()
    style_errs = []
    for s in p["scenes"]:
        try:
            styles.apply_style(s)
        except KeyError as e:
            style_errs.append(f"scene {s['id']}: {e}")
    shot_log = direction.plan_shots(p)
    errs, warns = validate(p, engines_available=avail)
    errs += style_errs
    cont = direction.continuity(p)
    warns += [f"continuity: {x}" for x in cont["issues"]]
    routes = {}
    for s in p["scenes"]:
        try:
            routes[s["id"]] = route(s, p, avail)
        except EngineUnavailable as e:  # premium profile: report the dependency, never degrade silently
            errs.append(str(e))
    return {"project": p, "errors": errs, "warnings": warns, "routes": routes, "availability": avail,
            "direction": {"bible": direction.style_bible(p), "continuity": cont, "shot_plan": shot_log}}


def tts_config(p: dict, lang: str = "en-US") -> dict:
    """Unified voice engine -> provider config (V3). Legacy `voice.provider` projects keep working."""
    v = p.get("voice", {"provider": "sapi"})
    if "mode" not in v:
        return v
    from .voice import resolve

    r = resolve(v, lang)
    return {"provider": {"edge-tts": "edge"}.get(r["mode"], r["mode"]), "mode": r["mode"], "voice": r["voice"],
            "edge_rate": r["rate"], "edge_pitch": r["pitch"], "rate": v.get("rate", 0), "allow_network": True,
            "model": r.get("model"), "reason": r["reason"]}


def narrate(p: dict, pdir: Path, log=print) -> dict:
    cfg = tts_config(p)
    if cfg.get("provider") == "elevenlabs":
        from .voice import elevenlabs_ready

        raise RuntimeError("ElevenLabs narration: run `studio.py voice jobs` / `voice ingest` (MCP). "
                           + elevenlabs_ready(p.get("voice", {}))[1])
    texts = narration_texts(p["scenes"])
    out = synthesize(texts, cfg, pdir / "audio" / "narration", voice_dir=pdir / "audio" / "voice", log=log)
    try:
        from .voice import log_usage

        made = [(k, texts[k]) for k, v in out.items() if not v.get("cached")]
        log_usage(pdir, {"mode": cfg.get("mode", cfg.get("provider")), "voice": cfg.get("voice"), "lang": "en-US"},
                  made, cached=len(texts) - len(made))
    except Exception:
        pass
    return out


def storyboard_export(p: dict, tl: dict, routes: dict, results: dict | None, pdir: Path) -> None:
    rows = []
    for s, r in zip(p["scenes"], tl["scenes"]):
        res = (results or {}).get(s["id"], {})
        on_screen = [e.get("text") for e in s.get("elements", []) if e.get("type") in ("text", "stamp") and e.get("text")]
        rows.append({
            "scene_id": s["id"], "chapter": s.get("chapter"), "start": r["start"], "end": r["end"],
            "duration": r["duration"], "narration": s.get("narration", ""), "purpose": s.get("purpose"),
            "attention": s.get("attention", ""), "emotion": s.get("emotion"),
            "visual": s.get("visual", ""), "art_style": s.get("art_style"),
            "engine": res.get("engine") or routes[s["id"]]["engine"],
            "engine_requested": s.get("engine", "auto"), "fallbacks": routes[s["id"]]["fallbacks"],
            "route_reason": routes[s["id"]]["reason"], "shot": s.get("shot"), "camera": s.get("camera"),
            "image_prompt": s.get("image_prompt", ""), "motion_prompt": s.get("motion_prompt", ""),
            "characters": s.get("characters", []),
            "animation_actions": [f"{e.get('type')}@{e.get('at', 0)}" for e in s.get("elements", [])],
            "elements": s.get("elements", []), "transition": s.get("transition", "cut"),
            "required_assets": s.get("assets", []) + ([{"path": s["params"]["src"]}] if s.get("params", {}).get("src") else []),
            "audio_cues": s.get("audio", {}).get("sfx", []), "on_screen_text": s.get("on_screen_text") or on_screen,
            "illustrative": s.get("illustrative", True), "claims": s.get("claims", []),
            "render_status": res.get("status", "pending"), "render_file": res.get("out"),
            "validation": {"status": "rendered" if res.get("status") == "done" else "planned"},
        })
    sb = {"schema": "studio.storyboard/v2", "project": p["slug"], "title": p["title"], "fps": tl["fps"],
          "total_duration": tl["total"], "target_duration": tl["target"], "timing_status": tl["status"],
          "scenes": rows}
    save_json(pdir / "storyboard" / "storyboard.json", sb)
    md = [f"# Storyboard — {p['title']}", "",
          f"Total {timeline.fmt_ts(tl['total'])} (target {timeline.fmt_ts(tl['target'] or 0)}, "
          f"status **{tl['status']}**) · {len(rows)} scenes · {tl['fps']} fps", ""]
    md += ["| # | Time | Chapter | Engine | Shot / camera | Visual | Status |", "|---|---|---|---|---|---|---|"]
    for i, r in enumerate(rows, 1):
        cam = (r["camera"] or {}).get("move", "")
        shot = (r["shot"] or {}).get("type", "") if isinstance(r["shot"], dict) else ""
        md.append(f"| {r['scene_id']} | {timeline.fmt_ts(r['start'])}–{timeline.fmt_ts(r['end'])} | {r['chapter']} | "
                  f"{r['engine']} | {shot} / {cam} | {r['visual'][:80]} | {r['render_status']} |")
    md.append("")
    for r in rows:
        md += [f"## {r['scene_id']} · {timeline.fmt_ts(r['start'])}–{timeline.fmt_ts(r['end'])} · {r['engine']}",
               "", f"**Narration:** {r['narration']}", "", f"**Visual:** {r['visual']}", "",
               f"**Purpose / attention:** {r['purpose']} — {r['attention']}", "",
               f"**Actions:** {', '.join(r['animation_actions']) or '—'}  ",
               f"**On-screen text:** {', '.join(t for t in r['on_screen_text'] if t) or '—'}  ",
               f"**Transition:** {r['transition']} · **Camera:** {r['camera']}  ",
               f"**Illustrative:** {r['illustrative']} · **Claims:** {', '.join(r['claims']) or '—'}", ""]
    (pdir / "storyboard" / "storyboard.md").write_text("\n".join(md), encoding="utf-8")


def build_long(pdir: Path, quality: str = "preview", workers: int = 3, retries: int = 1, only: list[str] | None = None,
               fit: bool = False, log=None) -> dict:
    ensure_dirs(pdir)
    log = log or Log(pdir / "reports" / "build.log")
    t0 = time.time()
    pl = plan(pdir, log)
    p = pl["project"]
    if pl["errors"]:
        for e in pl["errors"]:
            log(f"[spec] ERROR {e}")
        raise SystemExit("spec errors; fix project.json (see above)")
    for w in pl["warnings"]:
        log(f"[spec] warn {w}")
    save_json(pdir / "reports" / "direction.json", pl["direction"])
    for n in pl["direction"]["continuity"]["notes"]:
        log(f"[direction] note {n}")
    gate = research.gate(p, pdir)
    for b in gate["blockers"]:
        log(f"[research] BLOCKER {b}")
    log(f"[research] {gate['summary']}")
    stages = {}
    _t = time.time()
    # narration
    narr = narrate(p, pdir, log)
    stages["narration"] = round(time.time() - _t, 2)
    (pdir / "scripts" / "narration.txt").write_text(
        "\n\n".join(f"[{s['id']}] {s['narration'].strip()}" for s in p["scenes"] if s.get("narration")), encoding="utf-8")
    tl = timeline.build(p["scenes"], narr, p.get("fps", 30), p.get("target_duration"), p.get("tolerance", 0.05), fit=fit)
    save_json(pdir / "storyboard" / "timeline.json", tl)
    log(f"[timeline] total {tl['total']:.1f}s target {tl['target']} -> {tl['status']} "
        f"(dev {100 * (tl['deviation'] or 0):+.1f}%) {tl['fit'] or ''}")
    # render
    st = RenderSettings("long", quality)
    out_dir = pdir / "scenes" / f"long-{quality}"
    out_dir.mkdir(parents=True, exist_ok=True)
    badge = p.get("badge") if p.get("badge") is not None else ("FICTIONAL STORY · ILLUSTRATIVE" if p.get("fictional") else None)
    jobs, prev = [], None
    for s, r in zip(p["scenes"], tl["scenes"]):
        s["_work_dir"] = str(pdir / "scenes")
        rt = pl["routes"][s["id"]]
        sb = badge if s.get("illustrative", True) else None
        j = scene_job(s, r, st, p.get("theme", "documentary"), p.get("theme_overrides", {}), prev, sb, None,
                      rt["engine"], rt["fallbacks"], out_dir)
        jobs.append(j)
        prev = {"id": j["id"], "hash": j["hash"], "engine": rt["engine"], "scene": s, "tl": r, "captions": None,
                "out": j["out"]}
    sel = [j for j in jobs if not only or j["id"] in only]
    log(f"[render] {len(sel)} scenes · {st.width}x{st.height} · {quality} · {workers} workers")
    _t = time.time()
    res = render_all(sel, workers=workers, retries=retries, log=log)
    stages["render"] = round(time.time() - _t, 2)
    results = {r["id"]: r for r in res}
    failed = [r for r in res if r.get("status") != "done"]
    storyboard_export(p, tl, pl["routes"], results, pdir)
    report = {"project": p["slug"], "quality": quality, "timeline": {k: tl[k] for k in ("total", "target", "status", "deviation")},
              "scenes": res, "research_gate": gate, "routes": pl["routes"]}
    if failed or only:
        report["assembled"] = False
        save_json(pdir / "reports" / f"render-{quality}.json", report)
        if failed:
            for r in failed:
                log(f"[render] FAILED {r['id']}: {r['attempts'][-1].get('error') if r.get('attempts') else ''}")
        return report
    _t = time.time()
    # audio
    voice = [(r["start"] + r["lead"], narr[r["id"]]["wav"]) for r in tl["scenes"] if r["id"] in narr]
    mix_info = A.mix(tl["total"], voice, _music_plan(p, tl), _sfx_events(p["scenes"], tl),
                     pdir / "audio" / "mix.wav", p.get("music", {}).get("volume", 0.16), p.get("music", {}).get("enabled", True))
    log(f"[audio] mix.wav {tl['total']:.1f}s {mix_info}")
    # subtitles
    cues = []
    for r in tl["scenes"]:
        if r["words"]:
            for c in subtitles.chunk(r["words"], r["duration"]):
                cues.append({**c, "start": c["start"] + r["start"], "end": min(c["end"], r["duration"]) + r["start"]})
    subtitles.write_srt(cues, pdir / "subtitles" / "captions.srt")
    log(f"[subs] {len(cues)} cues")
    # assembly
    lst = pdir / "renders" / f"concat-{quality}.txt"
    lst.write_text("".join(f"file '{Path(results[j['id']]['out']).as_posix()}'\n" for j in jobs), encoding="utf-8")
    silent = pdir / "renders" / f"long-video-{quality}.silent.mp4"
    FF.run(["-y", "-f", "concat", "-safe", "0", "-i", str(lst), "-c", "copy", str(silent)])
    stages["audio_subs_concat"] = round(time.time() - _t, 2)
    _t = time.time()
    final = pdir / "renders" / ("long-video.mp4" if quality == "final" else f"long-video-{quality}.mp4")
    FF.run(["-y", "-i", str(silent), "-i", str(pdir / "audio" / "mix.wav"), "-map", "0:v", "-map", "1:a",
            "-c:v", "copy", "-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-ar", "48000", "-c:a", "aac", "-b:a", "192k",
            "-shortest", "-movflags", "+faststart", str(final)])
    silent.unlink(missing_ok=True)
    log(f"[assemble] {final.name} ({time.time() - t0:.0f}s total build)")
    report.update({"assembled": True, "output": str(final), "captions": str(pdir / "subtitles" / "captions.srt"),
                   "audio": mix_info, "narration_provider": next(iter(narr.values()))["provider"] if narr else None,
                   "narration_deliverable": all(v.get("deliverable") for v in narr.values()),
                   "build_sec": round(time.time() - t0, 1)})
    stages["mux_loudnorm"] = round(time.time() - _t, 2)
    save_json(pdir / "reports" / f"render-{quality}.json", report)
    write_production_report(pdir, p, quality, tl, res, stages, narr, report)
    return report


def write_production_report(pdir, p, quality, tl, res, stages, narr, report):
    """Machine-readable production report: stages, cost, cache efficiency, dependencies."""
    from .engines import availability
    from . import ffmpeg as FF

    cpu_render = sum(r.get("render_sec", 0) for r in res if not r.get("cached"))
    rep = {
        "project": p["slug"], "quality": quality, "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "stages_sec": stages, "wall_total_sec": report.get("build_sec"),
        "render": {"scenes": len(res), "rendered": sum(1 for r in res if not r.get("cached")),
                   "cache_hits": sum(1 for r in res if r.get("cached")), "worker_render_sec": round(cpu_render, 1),
                   "frames": sum(r.get("frames", 0) for r in res),
                   "engines": {e: sum(1 for r in res if r.get("engine") == e) for e in {r.get("engine") for r in res}},
                   "fallbacks_used": [r["id"] for r in res if r.get("fallback_used")]},
        "narration": {"provider": report.get("narration_provider"),
                      "characters": sum(len(s.get("narration", "")) for s in p["scenes"]),
                      "clips": len(narr), "deliverable": report.get("narration_deliverable")},
        "paid_services_used": [], "cost_usd_measured": 0.0,
        "dependencies": {"ffmpeg": FF.find_ffmpeg(), "engines": {k: v.get("ok") for k, v in availability().items()}},
        "timeline": {"total": tl["total"], "target": tl["target"], "status": tl["status"]},
        "output": report.get("output"),
    }
    save_json(pdir / "reports" / "production-report.json", rep)
    return rep
