"""Image -> whiteboard drawing, built on vendored upstream planners.

order = "strokes": ink skeleton traced into pen strokes with
        sweety-handdraw-video `stroke_paths.py` (MIT). The pen follows real strokes.
order = "grid":    ink cells ordered with whiteboard-animation-vi /
        SRT Whiteboard `grid_stream.py` (MIT). The classic cell-sweep reveal.

After the line pass, colour is revealed region by region (top -> bottom),
then the illustration holds with camera drift.

params: src (project-relative PNG/JPG), order, fit (contain|cover), ink_threshold,
        line_share (fraction of the draw time spent on lines), draw_time (seconds)
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

from .. import design as D
from ..config import SKILL_ROOT
from .base import Engine, Style

_VENDOR = SKILL_ROOT / "adapters" / "vendor"


def _vendor_import():
    p = str(SKILL_ROOT)
    if p not in sys.path:
        sys.path.insert(0, p)
    from adapters.vendor.srt_whiteboard_grid import grid_stream  # noqa: E402
    from adapters.vendor.sweety_stroke_paths import stroke_paths  # noqa: E402

    return grid_stream, stroke_paths


class ImageWhiteboardEngine(Engine):
    name = "image_whiteboard"
    description = "Draws a supplied illustration on a whiteboard (upstream stroke/grid planners) then colours it."
    style = Style("image_whiteboard", reveal="draw", pen=True, text_font="hand_bold", body_font="hand")
    _plan_cache: dict = {}

    def __init__(self, ctx):
        super().__init__(ctx)
        prm = self.params
        src = Path(ctx.scene.get("_project_dir", ".")) / prm["src"]
        if not src.exists():
            raise FileNotFoundError(f"image_whiteboard: missing asset {src}")
        W, H = ctx.W, ctx.H
        # work at a reduced plan resolution; reveal maps are upscaled
        self.pw = W // ctx.ss
        self.ph = H // ctx.ss
        img = Image.open(src).convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        bg.alpha_composite(img)
        img = bg.convert("RGB")
        box = prm.get("box", [0.08, 0.06, 0.84, 0.88])
        if ctx.vertical and prm.get("box_v"):
            box = prm["box_v"]
        elif ctx.vertical:
            box = [0.05, 0.18, 0.9, 0.55]
        bx, by, bw, bh = int(box[0] * self.pw), int(box[1] * self.ph), int(box[2] * self.pw), int(box[3] * self.ph)
        s = min(bw / img.width, bh / img.height)
        nw, nh = max(1, int(img.width * s)), max(1, int(img.height * s))
        canvas = Image.new("RGB", (self.pw, self.ph), (255, 255, 255))
        canvas.paste(img.resize((nw, nh), Image.LANCZOS), (bx + (bw - nw) // 2, by + (bh - nh) // 2))
        self.src_img = canvas
        key = (str(src), src.stat().st_mtime, self.pw, self.ph, tuple(box), prm.get("order", "strokes"),
               prm.get("ink_threshold", 110))
        if key not in self._plan_cache:
            self._plan_cache[key] = self._plan(canvas)
        self.ink_time, self.color_time, self.path = self._plan_cache[key]
        self.line_share = float(prm.get("line_share", 0.62))
        self.draw_time = float(prm.get("draw_time", min(ctx.duration * 0.8, max(4.0, ctx.duration - 2.0))))
        self.start = ctx.resolve_time(prm.get("at", 0.3))
        self.src_arr = np.asarray(canvas, dtype="uint8")
        self._board = None

    # -------------------------------------------------- planning
    def _plan(self, canvas: Image.Image):
        grid_stream, stroke_paths = _vendor_import()
        arr = np.asarray(canvas.convert("L"), dtype="uint8")
        thr = int(self.params.get("ink_threshold", 110))
        ink = arr < thr
        h, w = ink.shape
        ink_time = np.full((h, w), np.inf, dtype="float32")
        path: list[tuple[float, float, float]] = []  # (u, x, y) for pen
        order = self.params.get("order", "strokes")
        if order == "grid":
            edge = 10
            hh, ww = (h // edge) * edge, (w // edge) * edge
            thr_map = np.where(ink[:hh, :ww], 0, 255).astype("uint8")
            active = grid_stream._active_mask(thr_map, edge, 128)
            cells = grid_stream.flatten_streams(grid_stream.cluster_ink_streams(active))
            n = max(1, len(cells))
            for i, (r, c) in enumerate(cells):
                u = i / n
                blk = ink[r * edge:(r + 1) * edge, c * edge:(c + 1) * edge]
                sub = ink_time[r * edge:(r + 1) * edge, c * edge:(c + 1) * edge]
                sub[blk] = u
                path.append((u, c * edge + edge / 2, r * edge + edge / 2))
        else:
            # downsample for thinning speed, then dilate reveal back to full ink
            f = 2
            small = ink[::f, ::f]
            skel = stroke_paths.thin_ink(small)
            strokes = stroke_paths.trace_strokes(skel)
            strokes = [s for s in strokes if len(s) >= 3]
            # order: top band then left -> right (as upstream), keep long strokes
            strokes.sort(key=lambda s: (int(min(p[1] for p in s) // 12), min(p[0] for p in s)))
            lens = [max(1.0, float(stroke_paths.calculate_lengths(np.asarray(s, dtype="float32"))[-1]))
                    if len(s) > 1 else 1.0 for s in strokes]
            total = sum(lens) or 1.0
            acc = 0.0
            seed_t = np.full(small.shape, np.inf, dtype="float32")
            for s, L in zip(strokes, lens):
                pts = np.asarray(s, dtype="float32")
                seg = np.r_[0.0, np.cumsum(np.hypot(*np.diff(pts, axis=0).T))]
                for (x, y), d in zip(pts, seg):
                    u = (acc + d) / total
                    xi, yi = int(x), int(y)
                    if 0 <= yi < seed_t.shape[0] and 0 <= xi < seed_t.shape[1]:
                        seed_t[yi, xi] = min(seed_t[yi, xi], u)
                for k in range(0, len(pts), 3):
                    path.append(((acc + seg[k]) / total, float(pts[k][0]) * f, float(pts[k][1]) * f))
                acc += L
            # propagate skeleton times to neighbouring ink (cheap 8-neighbour min-propagation)
            t_small = seed_t.copy()
            for _ in range(8):
                p = np.pad(t_small, 1, constant_values=np.inf)
                nb = np.minimum.reduce([p[1:-1, 1:-1], p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:],
                                        p[:-2, :-2], p[:-2, 2:], p[2:, :-2], p[2:, 2:]])
                t_small = np.where(small, nb, np.inf)
            full = np.repeat(np.repeat(t_small, f, axis=0), f, axis=1)[:h, :w]
            ink_time[: full.shape[0], : full.shape[1]] = np.where(ink[: full.shape[0], : full.shape[1]], full, np.inf)
            leftover = ink & ~np.isfinite(ink_time)
            ink_time[leftover] = 1.0
        path.sort()
        # colour reveal: band sweep top->bottom with a gentle diagonal
        ys, xs = np.mgrid[0:h, 0:w].astype("float32")
        color_time = np.clip((ys / h) * 0.85 + (xs / w) * 0.15, 0, 1)
        return ink_time, color_time.astype("float32"), path

    # -------------------------------------------------- render
    def background(self, t):
        if self._board is None:
            from ..draw import paper_texture
            self._board = paper_texture((self.ctx.W // 4, self.ctx.H // 4), self.theme.c("board"), seed=3, grain=3) \
                .resize((self.ctx.W, self.ctx.H), Image.BILINEAR).convert("RGBA")
        return self._board.copy()

    def compose(self, t):
        img = self.background(t)
        u = (t - self.start) / max(0.1, self.draw_time)
        lu = D.clamp(u / self.line_share)
        cu = D.clamp((u - self.line_share) / (1 - self.line_share))
        board = np.full((self.ph, self.pw, 3), 255, dtype="uint8")
        line_mask = self.ink_time <= lu
        board[line_mask] = (np.asarray(self.theme.c("ink")) * 0.85 + self.src_arr[line_mask] * 0.15).astype("uint8")
        if cu > 0:
            cm = self.color_time <= cu
            board[cm] = self.src_arr[cm]
        layer = Image.fromarray(board, "RGB").resize((self.ctx.W, self.ctx.H), Image.BILINEAR)
        # multiply onto the board texture so white stays paper
        from PIL import ImageChops
        img = ImageChops.multiply(img.convert("RGB"), layer).convert("RGBA")
        tip = None
        if 0 < lu < 1 and self.path:
            i = min(len(self.path) - 1, int(np.searchsorted([p[0] for p in self.path], lu)))
            _, x, y = self.path[i]
            tip = (x * self.ctx.ss, y * self.ctx.ss)
        elif 0 < cu < 1:
            x = self.pw * (0.2 + 0.6 * ((cu * 7) % 1))
            y = self.ph * min(0.95, cu * 0.9 + 0.05)
            tip = (x * self.ctx.ss, y * self.ctx.ss)
        for el in self.elements:  # optional overlays (labels, arrows)
            if t < el.start:
                continue
            res = self.element_layer(el, t)
            if res and res[0] is not None:
                img.alpha_composite(res[0], (int(res[1][0]), int(res[1][1])))
                if res[2] is not None and 0 < el.progress(t) < 1:
                    tip = (res[2][0] + res[1][0], res[2][1] + res[1][1])
        if tip is not None:
            self.draw_pen(img, tip, t)
        return img
