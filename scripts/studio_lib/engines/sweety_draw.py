"""sweety_draw: authentic hand-drawn reveal built on the vendored sweety-handdraw-video planner.

Drawing core: adapters/vendor/sweety_handdraw (threerocks/sweety-handdraw-video, MIT; see SOURCE.md).
The pen draws every outline stroke in semantic-part order, lifting between strokes, and then
paints each part with brush passes that it follows. Before all of that, an optional
handwritten title is drawn glyph by glyph.

params
  src          project-relative or absolute PNG/JPG/SVG (SVG is rasterised with Playwright Chromium,
               transparent background; PNG may be opaque-white or transparent)
  parts        drawing order: list of {name|id, polygon:[[x,y]..] | bbox:[x0,y0,x1,y1]} in
               normalized image coords, or a path to such a JSON list, or "auto".
               Default: <src stem>.parts.json beside src if present, else auto (largest blobs first).
  box          [x, y, w, h] canvas fractions for the art (contain fit). box_v for 9:16.
  draw_window  [start, end]: seconds, or fractions when both <= 1, or "40%"/"end-1.5"/"cue:word".
  title        optional handwritten title, drawn before the art. title_font (path), title_size
               (fraction of height, default 0.08), title_pos [x, y] fractions, title_color.
  pen          "pen" (code-drawn marker, default) | "none"
  art_weight / title_weight   share of the draw window (default 5 / 0.7)

The plan, which takes 35-60 s for a full-HD illustration, is cached on disk at
<scene _work_dir or temp>/_sweety/<hash>/ (one entry for the art, one for the title). The art hash
covers the src bytes, parts and art box size, the title hash covers text/size/colour/font; both
include the vendored code version, so parallel workers and re-renders
reuse it. frame(t) is a pure function of t once the plan exists.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
import shutil
import sys
import tempfile
import uuid
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .. import design as D
from ..config import SKILL_ROOT
from .base import Engine, Style

ENGINE_REV = "sweety_draw.1"
BUILD_COUNT = 0                    # real (uncached) plan builds in this process; used by tests
_MEMORY: dict[str, dict] = {}       # in-process plan cache keyed by content hash


def _vendor():
    p = str(SKILL_ROOT)
    if p not in sys.path:
        sys.path.insert(0, p)
    from adapters.vendor import sweety_handdraw  # noqa: E402
    return sweety_handdraw


def clear_memory_cache():
    _MEMORY.clear()


def _sha_file(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _norm_parts(parts) -> list[dict]:
    out = []
    for i, p in enumerate(parts or []):
        name = str(p.get("name") or p.get("id") or f"part{i}")
        if "polygon" in p:
            poly = [[float(x), float(y)] for x, y in p["polygon"]]
        elif "bbox" in p:
            x0, y0, x1, y1 = (float(v) for v in p["bbox"])
            poly = [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]
        else:
            raise ValueError(f"sweety_draw: part {name} needs polygon or bbox")
        poly = [[min(1.0, max(0.0, x)), min(1.0, max(0.0, y))] for x, y in poly]
        out.append({"id": name, "polygon": poly})
    return out


def auto_parts(img: Image.Image, max_parts: int = 6) -> list[dict]:
    """Largest connected blobs of the artwork first (bounding boxes), then the rest."""
    from scipy import ndimage
    a = np.asarray(img.convert("RGBA"), dtype=np.int16)
    visible = (a[:, :, 3] > 30) & (a[:, :, :3].min(axis=2) < 245)
    dark = visible & (a[:, :, :3].max(axis=2) < 125)
    blobs, n = ndimage.label(ndimage.binary_dilation(visible, iterations=4))
    if n <= 1:
        return []
    sizes = ndimage.sum(np.ones_like(blobs), blobs, index=range(1, n + 1))
    h, w = visible.shape
    owned = np.zeros_like(visible)
    parts = []
    for rank, idx in enumerate(np.argsort(sizes)[::-1][:max_parts]):
        sl = ndimage.find_objects((blobs == idx + 1).astype(np.int8))[0]
        box = np.zeros_like(visible)
        box[sl] = True
        if ((box & ~owned) & dark).sum() < 40:
            continue
        owned |= box
        y0, y1, x0, x1 = sl[0].start / h, (sl[0].stop - 1) / max(1, h - 1), sl[1].start / w, (sl[1].stop - 1) / max(1, w - 1)
        parts.append({"id": f"blob{rank}", "polygon": [[x0, y0], [x1, y0], [x1, y1], [x0, y1]]})
    return parts


# ------------------------------------------------------------------ code-drawn pen sprite
def pen_sprite(scale: float = 1.0):
    """Felt-tip marker at 45 deg, nib top-left. Returns (RGBA image, nib xy)."""
    ss = 4
    k = scale * ss
    L = 420 * k
    size = int(L * 0.75 + 60 * k)
    im = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    nib = np.array([12 * k, 12 * k])
    u = np.array([math.cos(math.radians(45)), math.sin(math.pi / 4)])
    n = np.array([-u[1], u[0]])

    def quad(a, b, hw0, hw1=None, off=(0, 0)):
        hw1 = hw0 if hw1 is None else hw1
        o = np.array(off) * k
        p0, p1 = nib + u * a * k + o, nib + u * b * k + o
        return [tuple(p0 + n * hw0 * k), tuple(p1 + n * hw1 * k), tuple(p1 - n * hw1 * k), tuple(p0 - n * hw0 * k)]

    ink = (38, 34, 30, 255)
    d.polygon(quad(40, 420, 14, off=(18, 26)), fill=(0, 0, 0, 30))                  # soft shadow
    d.polygon([tuple(nib), *quad(16, 16, 4)[1:3]], fill=(29, 27, 25, 255))           # nib
    d.polygon(quad(14, 44, 6, 11), fill=(156, 150, 138, 255), outline=ink, width=int(2.5 * k))
    d.polygon(quad(44, 114, 14), fill=(59, 56, 51, 255), outline=ink, width=int(2.5 * k))
    for a in range(52, 112, 9):
        d.line([tuple(nib + u * a * k + n * 13 * k), tuple(nib + u * a * k - n * 13 * k)], fill=(87, 83, 75, 255),
               width=int(2 * k))
    d.polygon(quad(112, 412, 16), fill=(239, 233, 218, 255), outline=ink, width=int(3 * k))
    d.polygon(quad(118, 406, 3, off=(0, 0)), fill=(255, 255, 255, 200))
    d.polygon(quad(150, 166, 16), fill=(180, 75, 54, 255), outline=ink, width=int(2.5 * k))
    d.polygon(quad(380, 420, 19), fill=(59, 56, 51, 255), outline=ink, width=int(2.5 * k))
    out = im.resize((max(1, size // ss), max(1, size // ss)), Image.LANCZOS)
    return out, nib / ss


# ------------------------------------------------------------------ engine
class SweetyDrawEngine(Engine):
    name = "sweety_draw"
    description = ("Authentic sweety-handdraw-video drawing: semantic-part outline strokes with pen lifts, "
                   "then brush painting, from a code-drawn PNG/SVG illustration.")
    style = Style("sweety_draw", reveal="draw", pen=False, text_font="hand_bold", body_font="hand")
    max_ss = 1  # sweety layers are already anti-aliased rasters planned at output resolution

    def __init__(self, ctx):
        super().__init__(ctx)
        self.SW = _vendor()
        prm = self.params
        if not prm.get("src"):
            raise ValueError("sweety_draw needs params.src")
        src = Path(str(prm["src"]))
        if not src.is_absolute():
            src = Path(ctx.scene.get("_project_dir", ".")) / src
        if not src.exists():
            raise FileNotFoundError(f"sweety_draw: missing asset {src}")
        self.src = src
        W, H = ctx.W, ctx.H
        title = (prm.get("title") or "").strip()
        default_box = [0.05, 0.17, 0.90, 0.72] if title else [0.05, 0.08, 0.90, 0.84]
        if ctx.vertical:
            default_box = [0.04, 0.22, 0.92, 0.58]
        box = prm.get("box_v") if (ctx.vertical and prm.get("box_v")) else prm.get("box", default_box)
        bx, by, bw, bh = (int(round(box[0] * W)), int(round(box[1] * H)),
                          max(8, int(round(box[2] * W))), max(8, int(round(box[3] * H))))
        base = Path(ctx.scene.get("_work_dir") or Path(tempfile.gettempdir()) / "studio_sweety")
        self.cache_root = base / "_sweety"
        parts_spec = self._parts_spec()
        art_key = {"kind": "art", "v": self.SW.VERSION, "rev": ENGINE_REV, "src": _sha_file(src),
                   "ext": src.suffix.lower(), "parts": parts_spec, "box": [bw, bh]}
        plan = {"art": self._cached(art_key, lambda tmp: self._build_art(parts_spec, bw, bh, tmp))}
        self.key = plan["art"]["key"]
        self.cache_dir = self.cache_root / self.key
        if title:
            tfont = self._title_font()
            tsize = max(10, int(round(float(prm.get("title_size", 0.08)) * H)))
            tcolor = prm.get("title_color") or "#%02x%02x%02x" % self.theme.c("ink")
            title_key = {"kind": "title", "v": self.SW.VERSION, "rev": ENGINE_REV, "text": title, "size": tsize,
                         "color": tcolor, "font": _sha_file(tfont)}
            plan["title"] = self._cached(title_key, lambda tmp: self.SW.stroke_assets.build_text(title, tsize, tcolor, str(tfont)))
        # layout
        self.assets = []
        if title:
            tp = prm.get("title_pos", [0.06, 0.045])
            self.assets.append(dict(plan["title"], x=int(tp[0] * W), y=int(tp[1] * H), weight=float(prm.get("title_weight", 0.7))))
        art = plan["art"]
        ah, aw = art["rgba"].shape[:2]
        self.assets.append(dict(art, x=bx + (bw - aw) // 2, y=by + (bh - ah) // 2, weight=float(prm.get("art_weight", 5.0))))
        # timing
        t0, t1 = self._window()
        gap = 0.08
        budget = max(0.2, t1 - t0 - gap * (len(self.assets) - 1))
        total = sum(a["weight"] for a in self.assets)
        cur = t0
        self.events = []
        for i, a in enumerate(self.assets):
            d = budget * a["weight"] / total
            self.events.append({"index": i, "start": cur, "end": cur + d})
            cur += d + gap
        self._pen = None
        if str(prm.get("pen", "pen")) != "none":
            self._pen = pen_sprite(H / 1080)
        self._board = None
        self._baked = None

    # ---------------- params
    def _title_font(self) -> Path:
        prm = self.params
        if prm.get("title_font"):
            p = Path(prm["title_font"])
            if not p.is_absolute():
                p = Path(self.ctx.scene.get("_project_dir", ".")) / p
            if p.exists():
                return p
        for cand in (SKILL_ROOT / "tools" / "fonts" / "caveat" / "Caveat[wght].ttf",):
            if cand.exists():
                return cand
        fp = D.font_path("hand_bold") or D.font_path("hand") or D.font_path("sans")
        if not fp:
            raise FileNotFoundError("sweety_draw: no font for the handwritten title")
        return Path(fp)

    def _parts_spec(self):
        p = self.params.get("parts")
        if p is None:
            side = self.src.with_name(self.src.stem + ".parts.json")
            p = str(side) if side.exists() else "auto"
        if isinstance(p, str) and p != "auto":
            path = Path(p)
            if not path.is_absolute():
                path = Path(self.ctx.scene.get("_project_dir", ".")) / path
            p = json.loads(path.read_text(encoding="utf-8"))
        return "auto" if p == "auto" else _norm_parts(p)

    def _window(self):
        dur = self.ctx.duration
        win = self.params.get("draw_window")
        if not win:
            return min(0.35, dur * 0.1), max(min(0.35, dur * 0.1) + 0.2, dur - max(0.8, dur * 0.12))
        vals = list(win)[:2]
        if all(isinstance(v, (int, float)) for v in vals) and all(0 <= v <= 1 for v in vals) and vals[1] > vals[0]:
            a, b = vals[0] * dur, vals[1] * dur
        else:
            a, b = (self.ctx.resolve_time(v) for v in vals)
        a = min(max(0.0, a), dur)
        b = min(max(a + 0.2, b), max(dur, a + 0.2))
        return a, b

    # ---------------- plan (build or load)
    def _cached(self, key_src: dict, builder) -> dict:
        """Load the asset plan for key_src from memory/disk, or build it once and persist atomically."""
        global BUILD_COUNT
        key = hashlib.sha256(json.dumps(key_src, sort_keys=True).encode()).hexdigest()[:20]
        if key in _MEMORY:
            return _MEMORY[key]
        final = self.cache_root / key
        asset = self._load(final)
        if asset is None:
            tmp = self.cache_root / f"{key}.tmp-{os.getpid()}-{uuid.uuid4().hex[:6]}"
            tmp.mkdir(parents=True, exist_ok=True)
            try:
                rgba, maps, meta = builder(tmp)
                self.SW.reveal.validate_strokes(meta)
                Image.fromarray(rgba).save(tmp / "asset.png")
                np.savez_compressed(tmp / "asset.npz", **maps)
                (tmp / "asset.json").write_text(json.dumps(meta), encoding="utf-8")
                (tmp / "done.json").write_text(json.dumps({"key": key, **key_src}), encoding="utf-8")
                BUILD_COUNT += 1
                try:
                    os.replace(tmp, final)
                except OSError:          # another worker finished first: keep theirs
                    pass
            finally:
                if tmp.exists():
                    shutil.rmtree(tmp, ignore_errors=True)
            asset = self._load(final)
            if asset is None:
                raise RuntimeError(f"sweety_draw: could not persist plan at {final}")
        asset["key"] = key
        _MEMORY[key] = asset
        return asset

    def _build_art(self, parts_spec, bw, bh, tmp: Path):
        img = self._source_image(bw, bh, tmp)
        parts = auto_parts(img) if parts_spec == "auto" else parts_spec
        return self.SW.stroke_assets.build_illustration(img, bw, bh, parts)

    def _source_image(self, bw, bh, tmp: Path) -> Image.Image:
        if self.src.suffix.lower() == ".svg":
            from ..illustration import raster
            svg = self.src.read_text(encoding="utf-8")
            sw, sh = raster.svg_size(svg)
            scale = min(bw / sw, bh / sh)
            out = raster.render_svg(svg, tmp / "src.png", scale=scale, transparent=True)
            return Image.open(out).convert("RGBA")
        return Image.open(self.src).convert("RGBA")

    @staticmethod
    def _load(d: Path):
        if not (d / "done.json").exists():
            return None
        with np.load(d / "asset.npz") as z:
            maps = {k: z[k] for k in z.files}
        with Image.open(d / "asset.png") as im:
            rgba = np.array(im.convert("RGBA"))
        return {"rgba": rgba, "maps": maps,
                "meta": json.loads((d / "asset.json").read_text(encoding="utf-8")), "dir": str(d)}

    # ---------------- render
    def background(self, t):
        if self._board is None:
            from ..draw import paper_texture
            self._board = paper_texture((self.ctx.W // 4, self.ctx.H // 4), self.theme.c("board"), seed=3, grain=3)                 .resize((self.ctx.W, self.ctx.H), Image.BILINEAR).convert("RGBA")
        done = sum(1 for ev in self.events if t >= ev["end"])
        if self._baked is None or self._baked[0] != done:
            # finished groups are baked once (events never overlap and only complete in order)
            img = self._board.copy()
            for ev in self.events[:done]:
                a = self.assets[ev["index"]]
                _paste(img, Image.fromarray(a["rgba"], "RGBA"), a["x"], a["y"])
            self._baked = (done, img)
        img = self._baked[1].copy()
        for ev in self.events[done:]:
            if t < ev["start"]:
                continue
            _paste(img, self._asset_layer(ev, t), self.assets[ev["index"]]["x"], self.assets[ev["index"]]["y"])
        return img

    def _asset_layer(self, ev, t) -> Image.Image:
        a = self.assets[ev["index"]]
        p = (t - ev["start"]) / max(1e-6, ev["end"] - ev["start"])
        if p >= 1:
            return Image.fromarray(a["rgba"], "RGBA")
        rgba = a["rgba"].copy()
        rgba[:, :, 3] = self.SW.reveal.reveal_alpha(a["rgba"][:, :, 3], a["maps"], max(0.0, p))
        return Image.fromarray(rgba, "RGBA")

    def _tip(self, ev, progress):
        a = self.assets[ev["index"]]
        local = self.SW.reveal.point_on_asset(a["meta"]["segments"], float(np.clip(progress, 0, 1)))
        return np.array([a["x"], a["y"]], dtype=float) + local

    def pen_tip(self, t):
        evs = [e for e in self.events if self.assets[e["index"]]["meta"]["segments"]]
        return self.SW.reveal.pen_position(evs, self._tip, t, (self.ctx.W, self.ctx.H))

    def compose(self, t):
        img = super().compose(t)          # background (paper + drawing) + elements + post
        if self._pen is not None:
            tip = self.pen_tip(t)
            if tip is not None:
                sprite, nib = self._pen
                _paste(img, sprite, int(round(tip[0] - nib[0])), int(round(tip[1] - nib[1])))
        return img


def _paste(img: Image.Image, layer: Image.Image, x: int, y: int):
    """alpha_composite that tolerates layers partly outside the canvas."""
    l, tp = max(0, -x), max(0, -y)
    r, b = min(layer.width, img.width - x), min(layer.height, img.height - y)
    if r <= l or b <= tp:
        return
    img.alpha_composite(layer.crop((l, tp, r, b)), (x + l, y + tp))
