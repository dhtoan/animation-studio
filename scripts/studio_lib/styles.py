"""Unified style registry (V2).

`styles/registry.json` declares every style the studio knows about, from native
engines and audited upstream projects. A style becomes **operational** only when
`studio.py styles --verify` renders its 3-second sample on this machine, the MP4
probes correctly, and the frames change over time. Results are written to
`styles/verification.json` with sample paths and timings. The registry never
claims more than was verified.
"""
from __future__ import annotations

import json
import time
from pathlib import Path

from .config import SKILL_ROOT

REG = SKILL_ROOT / "styles" / "registry.json"
VER = SKILL_ROOT / "styles" / "verification.json"


def load() -> list[dict]:
    return json.loads(REG.read_text(encoding="utf-8"))["styles"]


def verification() -> dict:
    return json.loads(VER.read_text(encoding="utf-8")) if VER.exists() else {}


def get(style_id: str) -> dict:
    for s in load():
        if s["id"] == style_id:
            return s
    raise KeyError(f"unknown style {style_id!r}; see styles/registry.json")


def status(style_id: str) -> str:
    v = verification().get(style_id)
    if not v:
        return "declared"
    return "operational" if v.get("ok") else "failed"


def apply_style(scene: dict) -> dict:
    """If scene.art_style names a registry style, fill engine + default params (scene values win)."""
    sid = scene.get("art_style")
    if not sid:
        return scene
    st = get(sid)
    if scene.get("engine", "auto") == "auto":
        scene["engine"] = st["engine"]
    merged = dict(st.get("params", {}))
    merged.update(scene.get("params") or {})
    scene["params"] = merged
    return scene


SAMPLE_ELEMENTS = [
    {"type": "text", "text": "Style sample", "style": "h1", "pos": [0.5, 0.16], "at": 0.1, "dur": 0.8},
    {"type": "icon", "name": "warehouse", "pos": [0.3, 0.55], "size": 0.1, "at": 0.4},
    {"type": "bar_chart", "box": [0.5, 0.35, 0.4, 0.5], "bars": [{"label": "A", "value": 3}, {"label": "B", "value": 7, "color": "accent"}], "at": 0.6, "dur": 1.6},
]


def verify(ids: list[str] | None = None, out_dir: Path | None = None, seconds: float = 3.0, log=print) -> dict:
    from PIL import ImageChops

    from . import ffmpeg as FF
    from .design import Theme
    from .engines import ENGINES, SceneContext
    from .tts import estimate_words

    out_dir = out_dir or (SKILL_ROOT / "styles" / "samples")
    out_dir.mkdir(parents=True, exist_ok=True)
    results = verification()
    for st in load():
        if ids and st["id"] not in ids:
            continue
        rec = {"checked_at": time.strftime("%Y-%m-%dT%H:%M:%S"), "engine": st["engine"]}
        eng = fw = None
        t0 = time.time()
        try:
            w, h = (640, 360) if "16:9" in st["aspects"] else (360, 640)
            scene = {"id": "sample-" + st["id"].replace(".", "-"), "engine": st["engine"],
                     "params": {**st.get("params", {}), **st.get("sample_params", {})},
                     "elements": SAMPLE_ELEMENTS if st["engine"] in ("whiteboard", "handdrawn", "motion", "artistic") else [],
                     "_project_dir": str(SKILL_ROOT / "examples" / "billion-dollar-collapse"),
                     "_work_dir": str(out_dir / "_work"), "camera": {"move": "drift"}}
            if st["engine"] == "image_whiteboard":
                scene["params"].setdefault("src", "assets/hub-illustration.png")
                scene["params"]["draw_time"] = seconds * 0.8
            words = estimate_words("A short sample sentence to drive word timed typography.", seconds - 0.3, 0.1)
            ctx = SceneContext(scene=scene, width=w, height=h, ss=1, fps=30, duration=seconds, theme=Theme(), words=words)
            eng = ENGINES[st["engine"]](ctx)
            out = out_dir / f"{st['id']}.mp4"
            fw = None
            fw = FF.FrameWriter(out, w, h, 30, crf=28, preset="veryfast")
            first = last = mid = None
            n = int(seconds * 30)
            for i in range(n):
                im = eng.frame(i / 30)
                if i == 0:
                    first = im
                if i == n // 2:
                    mid = im
                last = im
                fw.write(im)
            fw.close()
            if hasattr(eng, "close"):
                eng.close()
            mid.save(out.with_suffix(".png"))
            from PIL import ImageStat

            spread = max(ImageStat.Stat(mid.convert("L")).stddev[0], ImageStat.Stat(last.convert("L")).stddev[0])
            subs = sorted(set(getattr(eng, "substitutions", []) or []))
            if subs:
                rec["degraded"] = f"font fallback used for {len(subs)} missing upstream font file(s): {', '.join(subs[:6])}"
            pr = FF.probe(out)
            diff = ImageChops.difference(first, last).getbbox() is not None
            blank = spread < 6.0  # near-uniform frame (e.g. black WebGL canvas) is not a working style
            ok = pr.width == w and pr.height == h and abs(pr.duration - seconds) < 0.1 and diff and not blank
            rec.update({"ok": ok, "sample": str(out.relative_to(SKILL_ROOT)), "still": str(out.with_suffix(".png").relative_to(SKILL_ROOT)),
                        "size": [w, h], "frames_change": diff, "content_spread": round(spread, 1), "ms_per_frame": round((time.time() - t0) / n * 1000, 1)})
        except Exception as e:  # noqa: BLE001
            rec.update({"ok": False, "error": f"{type(e).__name__}: {str(e)[:300]}"})
            try:  # never leak a browser session into the next style's test
                if fw:
                    fw.abort()
                if eng is not None and hasattr(eng, "close"):
                    eng.close()
            except Exception:
                pass
        results[st["id"]] = rec
        log(f"[styles] {st['id']:<28} {'OPERATIONAL' if rec.get('ok') else 'FAILED':<12} {rec.get('ms_per_frame', '')} {rec.get('error', '')}")
    VER.parent.mkdir(parents=True, exist_ok=True)
    VER.write_text(json.dumps(results, indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown()
    return results


def write_markdown() -> Path:
    v = verification()
    rows = ["# Style registry", "",
            "Generated from `styles/registry.json` + `styles/verification.json` (`studio.py styles --verify`).",
            "**operational** = sample rendered and validated on the verifying machine; **declared** = not yet verified here; "
            "**failed** = verification attempted and failed (see error).", "",
            "| Style ID | Engine | Source / licence | Aspects | Status | ms/frame | Best for | Dependencies |",
            "|---|---|---|---|---|---|---|---|"]
    for s in load():
        r = v.get(s["id"], {})
        stt = "operational" if r.get("ok") else ("failed" if r else "declared")
        rows.append(f"| `{s['id']}` | {s['engine']} | {s['source']} · {s['license']} | {', '.join(s['aspects'])} | **{stt}** | "
                    f"{r.get('ms_per_frame', '—')} | {', '.join(s.get('best_for', []))} | {', '.join(s['deps']) or '—'} |")
    rows += ["", "Descriptions:", ""] + [f"- `{s['id']}`: {s['description']}" for s in load()]
    errs = [(k, x["error"]) for k, x in v.items() if x.get("error")]
    if errs:
        rows += ["", "Verification errors:", ""] + [f"- `{k}`: {e}" for k, e in errs]
    f = SKILL_ROOT / "references" / "style-registry.md"
    f.write_text("\n".join(rows) + "\n", encoding="utf-8")
    return f
