"""Automated quality assurance + deliverable status.

Checks per output video: resolution/aspect, duration vs timeline, frame rate and
frame count, audio stream, black frames (blackdetect), frozen frames
(freezedetect), unexpected silence in the narration track, subtitle timing,
missing assets, licence records, research/rights blockers, and whether the
narration is a deliverable voice. Representative frames + transition frames are
exported to contact sheets for the human visual review, which is recorded
separately (`studio.py review`) — automation never marks it as done.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path

import numpy as np

from . import ffmpeg as FF
from . import research, subtitles
from .config import FORMATS, QUALITY
from .preview import contact_sheet
from .spec import load_project, save_json
from .tts import read_wav


def _detect(video: Path, vf: str, pattern: str) -> list[str]:
    cp = FF.run(["-i", str(video), "-vf", vf, "-an", "-f", "null", "-"], check=False)
    return re.findall(pattern, cp.stderr or "")


def video_checks(video: Path, expect_fmt: str, quality: str, expect_dur: float | None, fps: int = 30) -> dict:
    res = {"file": str(video), "exists": video.exists(), "issues": [], "warnings": []}
    if not video.exists():
        res["issues"].append("missing")
        return res
    pr = FF.probe(video)
    res["probe"] = pr.as_dict()
    W = int(round(FORMATS[expect_fmt]["width"] * QUALITY[quality]["scale"] / 2) * 2)
    H = int(round(FORMATS[expect_fmt]["height"] * QUALITY[quality]["scale"] / 2) * 2)
    if (pr.width, pr.height) != (W, H):
        res["issues"].append(f"resolution {pr.width}x{pr.height} != {W}x{H}")
    if pr.width and pr.height and abs(pr.width / pr.height - FORMATS[expect_fmt]["width"] / FORMATS[expect_fmt]["height"]) > 0.01:
        res["issues"].append("aspect ratio mismatch")
    if not pr.fps or abs(pr.fps - fps) > 0.01:
        res["issues"].append(f"fps {pr.fps} != {fps}")
    if not pr.has_audio:
        res["issues"].append("no audio stream")
    nf = FF.count_frames(video)
    res["frames"] = nf
    if expect_dur:
        if abs(pr.duration - expect_dur) > 0.15:
            res["issues"].append(f"duration {pr.duration:.2f}s != timeline {expect_dur:.2f}s")
        if abs(nf - round(expect_dur * fps)) > 2:
            res["issues"].append(f"frame count {nf} != {round(expect_dur * fps)} (constant frame rate check)")
    blacks = _detect(video, "blackdetect=d=0.5:pix_th=0.06", r"black_start:([\d.]+) black_end:([\d.]+)")
    res["black_segments"] = [[float(a), float(b)] for a, b in blacks]
    bad_black = [b for b in res["black_segments"] if b[0] > 0.6]  # an intentional fade-in at 0 is fine
    if bad_black:
        res["issues"].append(f"{len(bad_black)} black segment(s) >= 0.5s after the open")
    freezes = _detect(video, "freezedetect=n=0.0008:d=4", r"freeze_start: ([\d.]+)")
    res["frozen_starts"] = [float(x) for x in freezes]
    if freezes:
        res["warnings"].append(f"{len(freezes)} frozen stretch(es) >= 4s at {', '.join(f'{float(x):.1f}s' for x in freezes[:6])}")
    return res


def richness(video: Path, step: float = 2.5, exclude_bottom: float = 0.18) -> dict:
    """Visual-change metric (ported idea: dashi-animationstyle 丰富度检查, MIT): mean absolute
    difference between frames sampled every `step` s, subtitle band excluded. ~10+ reads as 'alive'."""
    import tempfile

    from PIL import Image

    pr = FF.probe(video)
    diffs = []
    prev = None
    with tempfile.TemporaryDirectory() as td:
        t = 0.5
        k = 0
        while t < pr.duration - 0.1:
            f = Path(td) / f"r{k}.png"
            FF.extract_frame(video, t, f)
            im = Image.open(f).convert("L").resize((320, 180))
            arr = np.asarray(im, dtype="float32")[: int(180 * (1 - exclude_bottom))]
            if prev is not None:
                diffs.append(float(np.mean(np.abs(arr - prev))))
            prev = arr
            t += step
            k += 1
    if not diffs:
        return {"mean": None, "samples": 0}
    return {"mean": round(float(np.mean(diffs)), 2), "min": round(float(np.min(diffs)), 2), "samples": len(diffs),
            "low_change_pairs": int(sum(d < 2.0 for d in diffs))}


def narration_gaps(pdir: Path, tl: dict, max_gap: float = 4.0) -> list[str]:
    """Silence between consecutive narration clips (music bed can hide it in the mix)."""
    out = []
    prev_end = None
    for r in tl["scenes"]:
        if not r.get("words"):
            continue
        st = r["start"] + r["lead"]
        if prev_end is not None and st - prev_end > max_gap:
            out.append(f"{st - prev_end:.1f}s without narration before {r['id']}")
        prev_end = st + r["narration_duration"]
    return out


def audio_level(wav: Path) -> dict:
    a, sr = read_wav(wav)
    if a.size == 0:
        return {"rms_db": None}
    rms = float(np.sqrt(np.mean(a ** 2)) + 1e-12)
    peak = float(np.max(np.abs(a)) + 1e-12)
    return {"rms_db": round(20 * np.log10(rms), 1), "peak_db": round(20 * np.log10(peak), 1)}


def run_qa(pdir: Path, quality: str = "preview") -> dict:
    t0 = time.time()
    p = load_project(pdir)
    rep: dict = {"project": p["slug"], "quality": quality, "checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                 "deliverables": {}, "checks": {}}
    tl_f = pdir / "storyboard" / "timeline.json"
    tl = json.loads(tl_f.read_text(encoding="utf-8")) if tl_f.exists() else None
    name = "long-video.mp4" if quality == "final" else f"long-video-{quality}.mp4"
    long_v = pdir / "renders" / name
    rep["checks"]["long_video"] = video_checks(long_v, "long", quality, tl["total"] if tl else None, p.get("fps", 30))
    if long_v.exists():
        rep["checks"]["long_video"]["richness"] = richness(long_v, step=5.0)
    if tl:
        rep["checks"]["timing"] = {"total": tl["total"], "target": tl["target"], "status": tl["status"],
                                   "deviation_pct": round(100 * (tl["deviation"] or 0), 2)}
        rep["checks"]["narration_gaps"] = narration_gaps(pdir, tl)
    srt = pdir / "subtitles" / "captions.srt"
    if srt.exists():
        cues = subtitles.parse_srt(srt)
        rep["checks"]["subtitles"] = {"cues": len(cues), "issues": subtitles.check(cues, tl["total"] if tl else 1e9)}
    mix = pdir / "audio" / "mix.wav"
    if mix.exists():
        rep["checks"]["audio_mix"] = audio_level(mix)
    # narration deliverability
    rr = pdir / "reports" / f"render-{quality}.json"
    if rr.exists():
        r = json.loads(rr.read_text(encoding="utf-8"))
        rep["checks"]["narration"] = {"provider": r.get("narration_provider"), "deliverable": r.get("narration_deliverable")}
        rep["checks"]["render"] = {"scenes": len(r.get("scenes", [])),
                                   "failed": [s["id"] for s in r.get("scenes", []) if s.get("status") != "done"],
                                   "fallbacks": [s["id"] for s in r.get("scenes", []) if s.get("fallback_used")],
                                   "engines": sorted({s.get("engine") for s in r.get("scenes", []) if s.get("engine")})}
    # shorts
    shorts = []
    for sh in p.get("shorts", []):
        f = pdir / "shorts" / (f"{sh['id']}.mp4" if quality == "final" else f"{sh['id']}-{quality}.mp4")
        c = video_checks(f, "short", quality, None, p.get("fps", 30))
        if f.exists():
            d = c["probe"]["duration"]
            lo, hi = sh.get("duration_range", [15, 60])
            if not lo <= d <= hi:
                c["issues"].append(f"duration {d:.1f}s outside {lo}-{hi}s")
        shorts.append({"id": sh["id"], **c})
    rep["checks"]["shorts"] = shorts
    # research, rights, assets, licences
    g = research.gate(p, pdir)
    rep["checks"]["research"] = g
    missing = []
    for s in p["scenes"]:
        for a in s.get("assets", []):
            if not (pdir / a["path"]).exists():
                missing.append(a["path"])
        if s.get("params", {}).get("src") and not (pdir / s["params"]["src"]).exists():
            missing.append(s["params"]["src"])
    rep["checks"]["missing_assets"] = missing
    lic = pdir / "reports" / "asset-license-report.md"
    lic.write_text(research.asset_license_report(p, pdir, extra=_generated_assets()), encoding="utf-8")
    # contact sheets for visual review
    sheets = []
    if long_v.exists() and tl:
        ims = []
        from PIL import Image

        tmp = pdir / "previews" / "_qa"
        tmp.mkdir(parents=True, exist_ok=True)
        for r in tl["scenes"]:
            for label, t in ((f"{r['id']} mid", r["start"] + r["duration"] * 0.55),
                             (f"{r['id']} in", r["start"] + 0.25)):
                if label.endswith(" in") and r["start"] == 0:
                    continue
                f = tmp / f"{r['id']}-{label.split()[-1]}.png"
                FF.extract_frame(long_v, t, f)
                ims.append((f"{label} {t:6.1f}s", Image.open(f).convert("RGB")))
        sheets.append(str(contact_sheet(ims, pdir / "previews" / f"contact-sheet-long-{quality}.png", cols=4, thumb_w=400)))
    for sh in shorts:
        if sh.get("exists"):
            from PIL import Image

            d = sh["probe"]["duration"]
            ims = []
            for k, frac in enumerate((0.03, 0.2, 0.4, 0.6, 0.8, 0.97)):
                f = pdir / "previews" / "_qa" / f"{sh['id']}-{k}.png"
                FF.extract_frame(Path(sh["file"]), d * frac, f)
                ims.append((f"{sh['id']} {d * frac:.1f}s", Image.open(f).convert("RGB")))
            sheets.append(str(contact_sheet(ims, pdir / "previews" / f"contact-sheet-{sh['id']}-{quality}.png", cols=6, thumb_w=220)))
    rep["contact_sheets"] = sheets
    rev_f = pdir / "reports" / "visual-review.json"
    rep["visual_review"] = json.loads(rev_f.read_text(encoding="utf-8")) if rev_f.exists() else {"status": "pending"}
    # deliverables
    D = {
        "long-video.mp4" if quality == "final" else name: long_v.exists() and not rep["checks"]["long_video"]["issues"],
        "storyboard.json": (pdir / "storyboard" / "storyboard.json").exists(),
        "storyboard.md": (pdir / "storyboard" / "storyboard.md").exists(),
        "narration.txt": (pdir / "scripts" / "narration.txt").exists(),
        "captions.srt": srt.exists() and not rep["checks"].get("subtitles", {}).get("issues"),
        "youtube-metadata.md": (pdir / "seo" / "youtube-metadata.md").exists(),
        "shorts-metadata.md": (pdir / "seo" / "shorts-metadata.md").exists(),
        "asset-license-report.md": lic.exists(),
    }
    for sh in shorts:
        D[Path(sh["file"]).name] = sh.get("exists", False) and not sh["issues"]
    rep["deliverables"] = D
    blockers = list(rep["checks"]["long_video"]["issues"]) + g["blockers"] + [f"missing asset {m}" for m in missing]
    for sh in shorts:
        blockers += [f"{sh['id']}: {i}" for i in sh["issues"]]
    blockers += [f"subtitles: {i}" for i in rep["checks"].get("subtitles", {}).get("issues", [])]
    if rep["checks"].get("narration", {}).get("deliverable") is False:
        blockers.append("narration is a placeholder (estimate provider) — not deliverable")
    warnings = list(rep["checks"]["long_video"].get("warnings", [])) + rep["checks"].get("narration_gaps", [])
    rich = rep["checks"]["long_video"].get("richness") or {}
    if rich.get("mean") is not None and rich["mean"] < 6:
        warnings.append(f"low visual change (richness {rich['mean']} < 6): risk of a slideshow feel")
    for sh in shorts:
        warnings += [f"{sh['id']}: {w}" for w in sh.get("warnings", [])]
    if rep["checks"].get("timing", {}).get("status") not in ("ok", None):
        warnings.append(f"runtime {rep['checks']['timing']['status']} vs target")
    if rep["visual_review"].get("status") != "approved":
        warnings.append("human visual review pending (studio.py review --approve)")
    status = "fail" if blockers else ("pass_with_warnings" if warnings else "pass")
    rep["summary"] = {"status": status, "blockers": blockers, "warnings": warnings,
                      "deliverables_ok": sum(bool(v) for v in D.values()), "deliverables_total": len(D),
                      "qa_sec": round(time.time() - t0, 1)}
    save_json(pdir / "reports" / "quality-report.json", rep)
    return rep


def _generated_assets() -> list[dict]:
    return [
        {"asset": "All animation frames", "used": "all scenes", "source": "rendered procedurally by this studio",
         "license": "original work of the project owner"},
        {"asset": "Music bed + SFX", "used": "mix", "source": "synthesised in studio_lib/audio.py", "license": "original"},
        {"asset": "Narration (SAPI voice)", "used": "voice-over", "source": "Windows System.Speech",
         "license": "generated locally; check Microsoft voice terms for commercial use",
         "notes": "replace with a licensed human or neural voice for publication"},
        {"asset": "Fonts", "used": "on-screen text", "source": "system fonts resolved by design.font_path",
         "license": "per font vendor (OFL recommended: drop OFL fonts into assets/fonts)"},
    ]


def record_review(pdir: Path, approve: bool, notes: str) -> dict:
    rec = {"status": "approved" if approve else "changes_requested", "notes": notes,
           "at": time.strftime("%Y-%m-%dT%H:%M:%S")}
    (pdir / "reports").mkdir(parents=True, exist_ok=True)
    (pdir / "reports" / "visual-review.json").write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return rec


def status(pdir: Path) -> dict:
    out = {}
    for sub in ("renders", "shorts", "seo", "subtitles", "storyboard", "reports"):
        d = pdir / sub
        out[sub] = sorted(x.name for x in d.glob("*") if x.is_file()) if d.exists() else []
    q = pdir / "reports" / "quality-report.json"
    if q.exists():
        out["qa"] = json.loads(q.read_text(encoding="utf-8"))["summary"]
    return out
