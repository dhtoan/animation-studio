"""Still-frame previews and contact sheets (no video encode)."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from . import design as D
from .config import RenderSettings
from .engines import ENGINES, SceneContext
from .router import route
from .spec import load_project
from .tts import estimate_words


def _ctx_for(scene, p, fmt, quality, duration=None, words=None):
    st = RenderSettings(fmt, quality)
    narr = scene.get("narration", "")
    dur = duration or max(float(scene.get("min_duration", 0)), len(narr.split()) / 2.6 + 0.9)
    words = words if words is not None else estimate_words(narr, dur - 0.9, 0.35)
    return SceneContext(scene=scene, width=st.width, height=st.height, ss=st.ss, fps=st.fps, duration=dur,
                        theme=D.Theme(p.get("theme", "documentary"), p.get("theme_overrides", {})), fmt=fmt,
                        words=words), st


def stills(pdir: Path, scene_id: str, times: list[float] | None, fmt: str = "long", quality: str = "preview") -> list[Path]:
    p = load_project(pdir)
    sc = next(s for s in p["scenes"] if s["id"] == scene_id)
    sc["_work_dir"] = str(pdir / "scenes")
    # prefer real timing if a timeline exists
    tl_file = pdir / "storyboard" / "timeline.json"
    dur = words = None
    if tl_file.exists():
        import json

        tl = json.loads(tl_file.read_text(encoding="utf-8"))
        row = next((r for r in tl["scenes"] if r["id"] == scene_id), None)
        if row:
            dur, words = row["duration"], [tuple(w) for w in row["words"]]
    ctx, st = _ctx_for(sc, p, fmt, quality, dur, words)
    from . import styles as _styles

    _styles.apply_style(sc)
    eng = ENGINES[route(sc, p, aspect="9:16" if fmt == "short" else "16:9")["engine"]](ctx)
    times = times or [ctx.duration * f for f in (0.15, 0.5, 0.95)]
    out = []
    for t in times:
        f = pdir / "previews" / f"{scene_id}-{fmt}-{t:06.2f}.png"
        f.parent.mkdir(parents=True, exist_ok=True)
        eng.frame(t).save(f)
        out.append(f)
    if hasattr(eng, "close"):
        eng.close()
    return out


def contact_sheet(images: list[tuple[str, Image.Image]], out: Path, cols: int = 4, thumb_w: int = 480) -> Path:
    if not images:
        return out
    ims = []
    for label, im in images:
        r = thumb_w / im.width
        ims.append((label, im.resize((thumb_w, int(im.height * r)))))
    th = max(i.height for _, i in ims)
    rows = (len(ims) + cols - 1) // cols
    lab_h = 26
    sheet = Image.new("RGB", (cols * (thumb_w + 8) + 8, rows * (th + lab_h + 8) + 8), (24, 26, 32))
    d = ImageDraw.Draw(sheet)
    f = D.font("sans_bold", 16)
    for k, (label, im) in enumerate(ims):
        r, c = divmod(k, cols)
        x, y = 8 + c * (thumb_w + 8), 8 + r * (th + lab_h + 8)
        sheet.paste(im, (x, y + lab_h))
        d.text((x + 2, y + 3), label, font=f, fill=(230, 230, 230))
    out.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(out)
    return out
