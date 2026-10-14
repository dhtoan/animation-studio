"""V3 CLI commands (imported by studio.py)."""
from __future__ import annotations

import json
import sys
from pathlib import Path


PDIR = None  # set by studio.py


def _p(a):
    return PDIR(a)


def cmd_niche(a):
    from studio_lib import niche

    root = Path(a.dir).resolve()
    ev = niche.load_json(root / "evidence.json", {"evidence": []})["evidence"]
    if a.action == "collect":
        from studio_lib.youtube_api import DataAPI

        api = DataAPI(budget=a.budget)
        res = niche.collect_api(a.query, api)
        out = root / "api" / (a.query.replace(" ", "_")[:60] + ".json")
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(res, indent=2), encoding="utf-8")
        print(out, "quota used", api.used)
        return
    cands = niche.load_json(root / "candidates.json", {"candidates": []})["candidates"]
    weights = niche.load_json(root / "weights.json", {}) or None
    ranked = niche.rank(cands, weights, ev)
    w = dict(niche.DEFAULT_WEIGHTS)
    w.update(weights or {})
    (root / "opportunities.json").write_text(json.dumps({"ranked": ranked}, indent=2, ensure_ascii=False), encoding="utf-8")
    (root / "niche-report.md").write_text(niche.report_md(ranked, ev, w), encoding="utf-8")
    rm = niche.roadmap(ranked)
    (root / "roadmap.json").write_text(json.dumps(rm, indent=2, ensure_ascii=False), encoding="utf-8")
    for c in ranked[:a.top]:
        r = c["result"]
        print(f"{c['rank']:>2}. {r['score']!s:>5} ({r['confidence_label']:<6}) {c['title']}")
    print("wrote", root / "niche-report.md", "and roadmap.json;", len(rm["near_duplicates"]), "near-duplicates")


def cmd_audience(a):
    from studio_lib import audience
    from studio_lib.spec import load_project

    pdir = _p(a)
    p = load_project(pdir)
    tlf = pdir / "storyboard" / "timeline.json"
    tl = json.loads(tlf.read_text(encoding="utf-8")) if tlf.exists() else None
    r = audience.audit(p, tl)
    (pdir / "reports" / "audience-50plus.json").write_text(json.dumps(r, indent=2), encoding="utf-8")
    print(json.dumps({k: r[k] for k in ("status", "issues", "notes")}, indent=2))


def cmd_history(a):
    from studio_lib import history
    from studio_lib.spec import load_project

    pdir = _p(a)
    if a.action == "import":
        d = json.loads(Path(a.dossier).read_text(encoding="utf-8"))
        led = history.ledger_from_dossier(d, d.get("accessed", "2026-10-14"))
        (pdir / "research").mkdir(parents=True, exist_ok=True)
        (pdir / "research" / "facts.json").write_text(json.dumps(led, indent=2, ensure_ascii=False), encoding="utf-8")
        (pdir / "research" / "dossier.json").write_text(json.dumps(d, indent=2, ensure_ascii=False), encoding="utf-8")
        print(f"{len(led['facts'])} claims imported")
        return
    p = load_project(pdir)
    facts = json.loads((pdir / "research" / "facts.json").read_text(encoding="utf-8"))["facts"]
    f = pdir / "reports" / "fact-check-report.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(history.fact_check_report(p, facts), encoding="utf-8")
    for w in history.scan_narration_numbers(p, facts):
        print("warn", w)
    print(f)


def cmd_story(a):
    from studio_lib import story

    if a.action == "plan":
        print(json.dumps(story.plan(a.minutes, a.voice), indent=2))
        return
    from studio_lib.spec import load_project

    pdir = _p(a)
    p = load_project(pdir)
    tlf = pdir / "storyboard" / "timeline.json"
    tl = json.loads(tlf.read_text(encoding="utf-8")) if tlf.exists() else None
    print(json.dumps(story.check(p, tl), indent=2))


def cmd_dub(a):
    from studio_lib import dubbing

    pdir = _p(a)
    langs = a.lang.split(",")
    for lang in langs:
        r = dubbing.dub(pdir, lang)
        print(json.dumps({k: r[k] for k in ("lang", "status", "track_duration_wav", "master_duration", "issues")},
                         indent=2, ensure_ascii=False))
    print(dubbing.upload_package(pdir, langs))


def cmd_analytics(a):
    from studio_lib import analytics

    d = Path(a.exports)
    r = analytics.summarize_exports(d)
    out = d.parent / "analytics-report.json"
    out.write_text(json.dumps(r, indent=2), encoding="utf-8")
    print(json.dumps(r, indent=2))


def cmd_voice(a):
    from studio_lib import voice

    if a.action == "list":
        for v in voice.list_edge_voices(a.lang):
            print(f"{v['name']:<36} {v['locale']:<8} {v['gender']}")
        return
    if a.action == "status":
        ok, why = voice.edge_ready()
        print(json.dumps({"edge-tts": {"ok": ok, "note": why}, "elevenlabs": voice.provider_status().get("elevenlabs",
                          {"verified": False, "note": "ElevenLabs MCP not connected/verified"})}, indent=2))
        return
    if a.action == "sample":
        from studio_lib.config import SKILL_ROOT

        txt = a.text or {"en-US": "This is the Animation Studio documentary narrator, testing a free Edge text to speech voice.",
                         "es": "Esta es una prueba de la voz de narración en español para nuestros documentales."}.get(a.lang, "Test.")
        r = voice.sample(a.lang, txt, SKILL_ROOT / "voice" / "samples")
        print(json.dumps(r, indent=2, ensure_ascii=False))
        return
    if a.action == "verify-elevenlabs":
        print(json.dumps(voice.verify_elevenlabs(Path(a.sample), a.plan, a.quota, a.used, a.voice_id, a.model_id,
                                                 a.tools.split(",") if a.tools else None), indent=2))
        return
    pdir = _p(a)
    from studio_lib.spec import load_project

    p = load_project(pdir)
    if a.action == "jobs":
        cfg = voice.resolve(p.get("voice", {}), a.lang)
        if cfg["mode"] != "elevenlabs":
            sys.exit(f"provider for {a.lang} resolves to {cfg['mode']} ({cfg['reason']}); jobs are only for ElevenLabs")
        texts = {s["id"]: s["narration"] for s in p["scenes"] if s.get("narration")} if a.lang == "en-US" else \
            json.loads((pdir / "localization" / a.lang / "script.json").read_text(encoding="utf-8"))["scenes"]
        print(voice.elevenlabs_jobs(pdir, texts, cfg, a.lang))
    elif a.action == "ingest":
        print(json.dumps(voice.elevenlabs_ingest(pdir, a.lang), indent=2))


def add_parsers(add):
    sp = add("niche", cmd_niche, slug=False)
    sp.add_argument("action", choices=["score", "collect"])
    sp.add_argument("--dir", default="research/niche")
    sp.add_argument("--query")
    sp.add_argument("--budget", type=int, default=8000)
    sp.add_argument("--top", type=int, default=20)
    add("audience", cmd_audience)
    sp = add("history", cmd_history)
    sp.add_argument("action", choices=["import", "report"])
    sp.add_argument("--dossier")
    sp = add("story", cmd_story, slug=False)
    sp.add_argument("action", choices=["plan", "check"])
    sp.add_argument("slug", nargs="?")
    sp.add_argument("--minutes", type=float, default=20)
    sp.add_argument("--voice", default="edge-tts")
    sp = add("dub", cmd_dub)
    sp.add_argument("--lang", required=True, help="comma-separated, e.g. es,de")
    sp = add("analytics", cmd_analytics, slug=False)
    sp.add_argument("--exports", required=True, help="folder with YouTube Studio CSV exports")
    sp = add("voice", cmd_voice, slug=False)
    sp.add_argument("action", choices=["list", "status", "sample", "verify-elevenlabs", "jobs", "ingest"])
    sp.add_argument("--text")
    sp.add_argument("slug", nargs="?")
    sp.add_argument("--lang", default="en-US")
    sp.add_argument("--sample")
    sp.add_argument("--plan")
    sp.add_argument("--quota", type=int)
    sp.add_argument("--used", type=int)
    sp.add_argument("--voice-id")
    sp.add_argument("--model-id")
    sp.add_argument("--tools")
