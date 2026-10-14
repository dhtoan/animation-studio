#!/usr/bin/env python3
"""Animation Studio — command line.

  studio.py capabilities                       engines, TTS, ffmpeg, fonts available here
  studio.py init <slug> --title T --category business --duration 600
  studio.py validate <slug>                    schema + semantic checks + research gate
  studio.py dry-run <slug>                     validate, route, estimate timing & render cost (no rendering)
  studio.py migrate <slug>                     upgrade project.json schema (keeps a .bak)
  studio.py preview <slug> --scene s01 [--t 2.5] [--fmt short]   still frames to previews/
  studio.py build <slug> [--quality draft|preview|final] [--workers N] [--only s01,s02] [--fit]
  studio.py shorts <slug> [--quality ...] [--only short-01]
  studio.py seo <slug>                         YouTube + Shorts metadata, chapters, thumbnail
  studio.py qa <slug> [--quality ...]          automated QA -> reports/quality-report.json + contact sheets
  studio.py review <slug> --approve --notes "..."   record the human visual review
  studio.py all <slug> [--quality final]      build + shorts + seo + qa + package
  studio.py status <slug>

Projects live in ./projects (override with --projects-dir or STUDIO_PROJECTS_DIR).
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
os.environ.setdefault("PYTHONUTF8", "1")
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")  # type: ignore[attr-defined]
except Exception:
    pass

from studio_lib import VERSION  # noqa: E402
from studio_lib.config import CATEGORIES, projects_root  # noqa: E402


def _pdir(a) -> Path:
    root = projects_root(a.projects_dir)
    p = Path(a.slug)
    if (p / "project.json").exists():
        return p.resolve()
    return root / a.slug


def cmd_capabilities(a):
    from studio_lib import design, ffmpeg, tts
    from studio_lib.engines import availability

    out = {"version": VERSION, "engines": availability(), "tts": tts.provider_report(), "fonts": design.font_report()}
    try:
        out["ffmpeg"] = ffmpeg.find_ffmpeg()
    except Exception as e:
        out["ffmpeg"] = f"MISSING: {e}"
    print(json.dumps(out, indent=2))


def cmd_init(a):
    from studio_lib.spec import ensure_dirs, save_json

    pdir = _pdir(a)
    if (pdir / "project.json").exists():
        sys.exit(f"{pdir}/project.json exists; refusing to overwrite")
    ensure_dirs(pdir)
    tpl = json.loads((Path(__file__).resolve().parents[1] / "templates" / "project.template.json").read_text(encoding="utf-8"))
    tpl.update({"slug": a.slug, "title": a.title or a.slug.replace("-", " ").title(), "category": a.category,
                "target_duration": a.duration})
    save_json(pdir / "project.json", tpl)
    (pdir / "research" / "facts.json").write_text(json.dumps({"facts": []}, indent=2), encoding="utf-8")
    (pdir / "research" / "brief.md").write_text((Path(__file__).resolve().parents[1] / "templates" / "research-brief.md").read_text(encoding="utf-8"), encoding="utf-8")
    print(f"created {pdir}")


def cmd_validate(a):
    from studio_lib import research
    from studio_lib.pipeline import plan

    pdir = _pdir(a)
    pl = plan(pdir)
    g = research.gate(pl["project"], pdir)
    for e in pl["errors"]:
        print("ERROR  ", e)
    for w in pl["warnings"]:
        print("warn   ", w)
    for b in g["blockers"]:
        print("BLOCKER", b)
    print(f"{len(pl['errors'])} errors, {len(pl['warnings'])} warnings, {len(g['blockers'])} research/rights blockers")
    sys.exit(1 if pl["errors"] else 0)


def cmd_dry_run(a):
    from studio_lib import research, timeline, tts
    from studio_lib.config import RenderSettings
    from studio_lib.pipeline import narration_texts, plan
    from studio_lib import ffmpeg

    pdir = _pdir(a)
    pl = plan(pdir)
    p = pl["project"]
    ok = True
    try:
        print("ffmpeg:", ffmpeg.find_ffmpeg())
    except Exception as e:
        print("ffmpeg: MISSING", e)
        ok = False
    prov = p.get("voice", {}).get("provider", "sapi")
    pok, note = tts.PROVIDERS[prov].available()
    print(f"tts: {prov} -> {'ok' if pok else 'UNAVAILABLE'} {note}")
    ok &= pok
    est = {k: {"duration": len(v.split()) / 2.6, "words": tts.estimate_words(v, len(v.split()) / 2.6)}
           for k, v in narration_texts(p["scenes"]).items()}
    tl = timeline.build(p["scenes"], est, p.get("fps", 30), p.get("target_duration"), p.get("tolerance", 0.05))
    st = RenderSettings("long", a.quality)
    cost = sum(r["frames"] * (pl["routes"][r["id"]]["est_ms_per_frame"] or 150) for r in tl["scenes"]) / 1000
    print(f"estimated runtime {timeline.fmt_ts(tl['total'])} vs target {timeline.fmt_ts(tl['target'] or 0)} -> {tl['status']}"
          f" (estimate at 156 wpm; real TTS timing decides)")
    print(f"render estimate @{a.quality}: {cost * st.width * st.height / (1920 * 1080) / 60:.1f} CPU-min "
          f"({sum(r['frames'] for r in tl['scenes'])} frames)")
    for s in p["scenes"]:
        r = pl["routes"][s["id"]]
        print(f"  {s['id']:<8} {r['engine']:<16} fb={','.join(r['fallbacks']) or '-':<26} {r['reason'][:60]}")
    for e in pl["errors"]:
        print("ERROR", e)
    for w in pl["warnings"]:
        print("warn ", w)
    g = research.gate(p, pdir)
    for b in g["blockers"]:
        print("BLOCKER", b)
    ok &= not pl["errors"]
    print("DRY-RUN", "OK" if ok else "FAILED")
    sys.exit(0 if ok else 1)


def cmd_migrate(a):
    from studio_lib.migrate import migrate

    pdir = _pdir(a)
    f = pdir / "project.json"
    data = json.loads(f.read_text(encoding="utf-8"))
    new, log = migrate(data)
    if not log:
        print("already current")
        return
    bak = pdir / f"project.v{data.get('schema_version', 1)}.bak.json"
    if not bak.exists():
        bak.write_text(f.read_text(encoding="utf-8"), encoding="utf-8")
    f.write_text(json.dumps(new, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("\n".join(log), f"\nbackup: {bak.name}")


def cmd_preview(a):
    from studio_lib.preview import stills

    for p in stills(_pdir(a), a.scene, [float(x) for x in a.t.split(",")] if a.t else None, a.fmt, a.quality):
        print(p)


def cmd_build(a):
    from studio_lib.pipeline import build_long

    r = build_long(_pdir(a), a.quality, a.workers, a.retries, a.only.split(",") if a.only else None, fit=a.fit)
    print(json.dumps({k: r.get(k) for k in ("assembled", "output", "timeline", "build_sec")}, indent=2, default=str))


def cmd_shorts(a):
    from studio_lib.shorts import build_shorts

    r = build_shorts(_pdir(a), a.quality, a.workers, a.only.split(",") if a.only else None)
    print(json.dumps([{k: x.get(k) for k in ("id", "output", "duration", "status")} for x in r], indent=2))


def cmd_seo(a):
    from studio_lib.seo import write_seo

    for f in write_seo(_pdir(a), a.quality):
        print(f)


def cmd_qa(a):
    from studio_lib.qa import run_qa

    r = run_qa(_pdir(a), a.quality)
    print(json.dumps(r["summary"], indent=2))
    sys.exit(0 if r["summary"]["status"] in ("pass", "pass_with_warnings") else 1)


def cmd_review(a):
    from studio_lib.qa import record_review

    print(record_review(_pdir(a), a.approve, a.notes or ""))


def cmd_all(a):
    cmd_build(a)
    cmd_shorts(a)
    cmd_seo(a)
    from studio_lib.qa import run_qa

    r = run_qa(_pdir(a), a.quality)
    print(json.dumps(r["summary"], indent=2))


def cmd_styles(a):
    from studio_lib import styles

    if a.verify:
        styles.verify(a.only.split(",") if a.only else None)
    else:
        for s in styles.load():
            print(f"{s['id']:<28} {styles.status(s['id']):<12} {s['engine']:<16} {s['description'][:70]}")
    print("registry doc:", styles.write_markdown())


def cmd_direction(a):
    from studio_lib.pipeline import plan

    pl = plan(_pdir(a))
    d = pl["direction"]
    from studio_lib import direction

    print(json.dumps({"bible": d["bible"], "continuity": d["continuity"], "shot_plan_filled": d["shot_plan"],
                      "style_proposal": direction.propose_styles(pl["project"])}, indent=2, ensure_ascii=False))


def cmd_status(a):
    from studio_lib.qa import status

    print(json.dumps(status(_pdir(a)), indent=2))


def main(argv=None):
    ap = argparse.ArgumentParser(prog="studio.py", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--projects-dir")
    sub = ap.add_subparsers(dest="cmd", required=True)

    def add(name, fn, slug=True, **kw):
        sp = sub.add_parser(name, **kw)
        if slug:
            sp.add_argument("slug")
        sp.set_defaults(fn=fn)
        return sp

    add("capabilities", cmd_capabilities, slug=False)
    sp = add("init", cmd_init)
    sp.add_argument("--title")
    sp.add_argument("--category", default="business", choices=sorted(CATEGORIES))
    sp.add_argument("--duration", type=float, default=600)
    add("validate", cmd_validate)
    sp = add("dry-run", cmd_dry_run)
    sp.add_argument("--quality", default="final", choices=["draft", "preview", "final"])
    add("migrate", cmd_migrate)
    sp = add("preview", cmd_preview)
    sp.add_argument("--scene", required=True)
    sp.add_argument("--t")
    sp.add_argument("--fmt", default="long", choices=["long", "short"])
    sp.add_argument("--quality", default="preview", choices=["draft", "preview", "final"])
    for name, fn in (("build", cmd_build), ("all", cmd_all)):
        sp = add(name, fn)
        sp.add_argument("--quality", default="preview", choices=["draft", "preview", "final"])
        sp.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
        sp.add_argument("--retries", type=int, default=1)
        sp.add_argument("--only")
        sp.add_argument("--fit", action="store_true", help="pad visual holds to reach target duration")
    sp = add("shorts", cmd_shorts)
    sp.add_argument("--quality", default="preview", choices=["draft", "preview", "final"])
    sp.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    sp.add_argument("--only")
    for name, fn in (("seo", cmd_seo), ("qa", cmd_qa)):
        sp = add(name, fn)
        sp.add_argument("--quality", default="preview", choices=["draft", "preview", "final"])
    sp = add("review", cmd_review)
    sp.add_argument("--approve", action="store_true")
    sp.add_argument("--notes")
    add("status", cmd_status)
    sp = add("styles", cmd_styles, slug=False)
    sp.add_argument("--verify", action="store_true", help="render a 3 s sample per style and record results")
    sp.add_argument("--only")
    add("direction", cmd_direction)
    a = ap.parse_args(argv)
    if getattr(a, "cmd", "") == "all":
        a.only = None
    a.fn(a)


if __name__ == "__main__":
    main()
