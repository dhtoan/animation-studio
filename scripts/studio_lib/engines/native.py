"""Native engines (pure Python: Pillow + numpy). Always available."""
from __future__ import annotations

import math
import random
import re

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .. import design as D
from ..draw import paper_texture, seed_of, vignette
from .base import Engine, Style


class WhiteboardEngine(Engine):
    name = "whiteboard"
    description = "Marker on whiteboard; every element is drawn stroke by stroke with a pen cursor."
    style = Style("whiteboard", reveal="draw", rough=0.0012, fill_mode="flat", fill_alpha=150,
                  ink="ink", text_font="hand_bold", body_font="hand", text_color="ink", pen=True,
                  line_scale=1.0)

    def background(self, t):
        if self._bg_cache is None:
            W, H = self.ctx.W, self.ctx.H
            base = paper_texture((W // 4, H // 4), self.theme.c("board"), seed=3, grain=3).resize((W, H), Image.BILINEAR)
            v = vignette((W, H), 0.12)
            base = ImageChops.multiply(base, Image.merge("RGB", (v, v, v)))
            self._bg_cache = base.convert("RGBA")
        return self._bg_cache.copy()


class HandDrawnEngine(Engine):
    name = "handdrawn"
    description = "Pencil and watercolour on paper; boiling lines on 2s, hatched fills, sketch characters."
    style = Style("handdrawn", reveal="draw", rough=0.0028, boil_fps=8, double_line=True, fill_mode="wash",
                  fill_alpha=200, ink="ink", text_font="hand_bold", body_font="hand", text_color="ink",
                  pen=True, line_scale=0.9)

    def __init__(self, ctx):
        if (ctx.scene.get("params") or {}).get("fill") == "hatch":
            self.style = Style(**{**self.style.__dict__, "fill_mode": "hatch"})
        super().__init__(ctx)

    def background(self, t):
        if self._bg_cache is None:
            W, H = self.ctx.W, self.ctx.H
            base = paper_texture((W // 2, H // 2), self.theme.c("paper"), seed=11, grain=14).resize((W, H), Image.BICUBIC)
            v = vignette((W, H), 0.22)
            base = ImageChops.multiply(base, Image.merge("RGB", (v, v, v)))
            self._bg_cache = base.convert("RGBA")
        return self._bg_cache.copy()


class MotionEngine(Engine):
    name = "motion"
    description = "Flat vector motion graphics on a dark field: charts, networks, counters, cards."
    style = Style("motion", reveal="pop", rough=0.0, fill_mode="flat", ink="keep", text_font="sans_bold",
                  body_font="sans", text_color="light", pen=False, line_scale=1.0)

    def background(self, t):
        W, H = self.ctx.W, self.ctx.H
        if self._bg_cache is None:
            top = np.array(self.theme.c(self.params.get("bg_top", "night2")), dtype="float32")
            bot = np.array(self.theme.c(self.params.get("bg_bottom", "night")), dtype="float32")
            self._step = step = int(self.ctx.U * 0.06)
            ys = np.linspace(0, 1, H // 4, dtype="float32")[:, None, None]
            grad = np.repeat((top * (1 - ys) + bot * ys).astype("uint8"), (W + step) // 4 + 1, axis=1)
            bg = Image.fromarray(grad, "RGB").resize((W + step, H), Image.BILINEAR)
            if self.params.get("grid", True):
                d = ImageDraw.Draw(bg, "RGBA")
                for x in range(0, bg.width, step):
                    d.line((x, 0, x, H), fill=(255, 255, 255, 10), width=max(1, self.ctx.ss))
                for y in range(0, H, step):
                    d.line((0, y, bg.width, y), fill=(255, 255, 255, 10), width=max(1, self.ctx.ss))
            self._bg_cache = bg.convert("RGBA")
        off = int((t * self.ctx.U * 0.01) % self._step) if self.params.get("grid", True) else 0
        return self._bg_cache.crop((off, 0, off + W, H))


class KineticEngine(Engine):
    """Kinetic typography driven by narration word timings.

    params: emphasis [words], bg (role), fg (role), max_words (per phrase), align
    If `elements` are given they render on top (e.g. a counter).
    """
    name = "kinetic"
    description = "Word-synced kinetic typography; phrases build word by word on the narration."
    style = Style("kinetic", reveal="pop", ink="keep", text_font="display", body_font="sans_bold",
                  text_color="light", pen=False)

    def __init__(self, ctx):
        super().__init__(ctx)
        words = ctx.words or []
        maxw = int(self.params.get("max_words", 3 if ctx.vertical else 5))
        self.phrases: list[list[tuple[float, str]]] = []
        cur: list = []
        for t, w in words:
            cur.append((t, w))
            if len(cur) >= maxw or re.search(r"[.,;:!?—]$", w):
                self.phrases.append(cur)
                cur = []
        if cur:
            self.phrases.append(cur)
        self.emph = {re.sub(r"[^a-z0-9$%]", "", e.lower()) for e in self.params.get("emphasis", [])}

    def background(self, t):
        if self._bg_cache is None:
            self._bg_cache = Image.new("RGBA", (self.ctx.W, self.ctx.H), self.theme.c(self.params.get("bg", "night")) + (255,))
        return self._bg_cache.copy()

    def post(self, img, t):
        if not self.phrases:
            return img
        idx = 0
        for i, ph in enumerate(self.phrases):
            if t >= ph[0][0] - 0.05:
                idx = i
        U = self.ctx.U
        big = D.font("display", U * float(self.params.get("size", 0.11 if not self.ctx.vertical else 0.135)))
        small_col = self.theme.c(self.params.get("fg", "light"))
        acc = self.theme.c(self.params.get("accent", "accent"))
        d = ImageDraw.Draw(img)
        maxw = self.ctx.W * 0.86
        for k, off in ((idx - 1, -1), (idx, 0)):
            if k < 0:
                continue
            ph = self.phrases[k]
            # layout words in lines
            lines, line, lw = [], [], 0.0
            for (wt, w) in ph:
                ww = big.getlength(w.upper() + " ")
                if line and lw + ww > maxw:
                    lines.append(line)
                    line, lw = [], 0.0
                line.append((wt, w, ww))
                lw += ww
            if line:
                lines.append(line)
            lh = big.size * 1.08
            block_h = lh * len(lines)
            cy = self.ctx.H * 0.5 - block_h / 2
            if off == -1:  # previous phrase drifts up and fades
                nxt = self.phrases[idx][0][0]
                u = D.clamp((t - nxt + 0.05) / 0.35)
                if u >= 1:
                    continue
                cy -= U * 0.12 * D.ease_out_cubic(u)
                alpha_mul = 1 - u
            else:
                alpha_mul = 1.0
            for li, ln in enumerate(lines):
                total = sum(x[2] for x in ln)
                x = (self.ctx.W - total) / 2
                y = cy + li * lh
                for (wt, w, ww) in ln:
                    if t < wt - 0.02:
                        x += ww
                        continue
                    u = D.clamp((t - wt + 0.02) / 0.18)
                    s = D.ease_out_back(u, 2.0)
                    key = re.sub(r"[^a-z0-9$%]", "", w.lower())
                    col = acc if key in self.emph else small_col
                    a = int(255 * alpha_mul * D.clamp(u * 2))
                    txt = w.upper()
                    if s < 0.999:
                        f2 = D.font("display", max(6, big.size * s))
                        dy = (big.size - f2.size) * 0.6
                        d.text((x + (ww - f2.getlength(txt + " ")) / 2, y + dy), txt, font=f2, fill=col + (a,))
                    else:
                        d.text((x, y), txt, font=big, fill=col + (a,))
                    x += ww
        return img


class ArtisticEngine(Engine):
    """Atmospheric, painterly scenes: gradient sky, parallax silhouettes, light, particles, grain.

    params:
      sky: [top, bottom] colour roles/hex      sun: {pos:[x,y], color, size}
      layers: ["mountains", "city", "towers", "hills", "skyline_tall"]  (back -> front)
      fog: bool       grain: float       mood_shift: [role] (sky drifts toward this over the scene)
      flicker: bool   (lights in windows flicker / go out)   lights_out_at: time
    """
    name = "artistic"
    description = "Atmospheric painterly sequences: parallax silhouettes, light, fog, particles, grain."
    max_ss = 1
    style = Style("artistic", reveal="fade", ink="keep", text_font="serif_bold", body_font="serif",
                  text_color="light", pen=False)

    def __init__(self, ctx):
        super().__init__(ctx)
        self._layers = None

    def _sky(self, t):
        W, H = self.ctx.W // 4, self.ctx.H // 4
        sky = self.params.get("sky", ["night2", "accent"])
        top = np.array(self.theme.c(sky[0]), dtype="float32")
        bot = np.array(self.theme.c(sky[1]), dtype="float32")
        shift = self.params.get("mood_shift")
        if shift:
            u = D.ease_in_out(t / max(0.1, self.ctx.duration))
            tgt = np.array(self.theme.c(shift[0] if isinstance(shift, list) else shift), dtype="float32")
            bot = bot * (1 - u) + tgt * u
        ys = np.linspace(0, 1, H, dtype="float32")[:, None, None] ** 1.3
        grad = top * (1 - ys) + bot * ys
        return Image.fromarray(np.repeat(grad.astype("uint8"), W, axis=1), "RGB")

    def _make_layers(self):
        W, H = self.ctx.W, self.ctx.H
        names = self.params.get("layers", ["mountains", "city"])
        out = []
        n = len(names)
        for i, nm in enumerate(names):
            depth = (i + 1) / n
            rnd = random.Random(seed_of(self.ctx.scene.get("id"), nm, i))
            lw = int(W * 1.25)
            layer = Image.new("RGBA", (lw, H), (0, 0, 0, 0))
            d = ImageDraw.Draw(layer)
            dark = D.mix_rgb(self.theme.c(self.params.get("sky", ["night2"])[0]), (8, 10, 16), 0.35 + 0.6 * depth)
            base_y = H * (0.62 + 0.12 * depth)
            windows = []
            if nm in ("mountains", "hills"):
                pts = [(0, H)]
                amp = H * (0.22 if nm == "mountains" else 0.08)
                ph = rnd.random() * 6
                for x in range(0, lw + 40, 40):
                    y = base_y - amp * (0.55 + 0.45 * math.sin(x / lw * 6.3 + ph)) * (0.7 + 0.3 * math.sin(x / lw * 17 + ph * 2))
                    pts.append((x, y))
                pts.append((lw, H))
                d.polygon(pts, fill=dark + (255,))
            else:
                x = 0
                tall = nm in ("towers", "skyline_tall")
                while x < lw:
                    bw = rnd.uniform(0.03, 0.07) * W
                    bh = rnd.uniform(0.12, 0.42 if tall else 0.25) * H * (0.7 + 0.5 * depth)
                    top = base_y - bh
                    d.rectangle((x, top, x + bw, H), fill=dark + (255,))
                    if rnd.random() < 0.3:
                        d.rectangle((x + bw * 0.4, top - bh * 0.12, x + bw * 0.5, top), fill=dark + (255,))
                    # windows
                    for wy in np.arange(top + bw * 0.2, H - bw * 0.2, bw * 0.28):
                        for wx in np.arange(x + bw * 0.15, x + bw - bw * 0.2, bw * 0.25):
                            if rnd.random() < 0.38:
                                windows.append((wx, wy, bw * 0.1, bw * 0.12, rnd.random()))
                    x += bw + rnd.uniform(0, 0.012) * W
            out.append({"img": layer, "depth": depth, "windows": windows, "name": nm})
        return out

    def _bake_windows(self, L, on: bool):
        img = L["img"].copy()
        if on:
            d = ImageDraw.Draw(img)
            wcol = self.theme.c(self.params.get("window_color", "accent"))
            for (wx, wy, ww, wh, r) in L["windows"]:
                d.rectangle((wx, wy, wx + ww, wy + wh), fill=wcol + (int(150 + 80 * r),))
        return img

    def _static_sky(self, t):
        dynamic = bool(self.params.get("mood_shift")) or float((self.params.get("sun") or {}).get("sink", 0)) != 0
        if not dynamic and getattr(self, "_sky_cache", None) is not None:
            return self._sky_cache.copy()
        W, H = self.ctx.W, self.ctx.H
        img = self._sky(t).resize((W, H), Image.BILINEAR).convert("RGBA")
        sun = self.params.get("sun")
        if sun:
            sx, sy = sun.get("pos", [0.7, 0.35])
            r = float(sun.get("size", 0.12)) * self.ctx.U
            sy = sy + float(sun.get("sink", 0.0)) * D.ease_in_out(t / max(0.1, self.ctx.duration))
            glow = Image.new("RGBA", (W // 4, H // 4), (0, 0, 0, 0))
            gd = ImageDraw.Draw(glow)
            col = self.theme.c(sun.get("color", "accent"))
            cx, cy = sx * W / 4, sy * H / 4
            for k in range(6, 0, -1):
                rr = r / 4 * (1 + k * 0.6)
                gd.ellipse((cx - rr, cy - rr, cx + rr, cy + rr), fill=col + (int(28 / k * 3),))
            gd.ellipse((cx - r / 4, cy - r / 4, cx + r / 4, cy + r / 4), fill=col + (235,))
            glow = glow.filter(ImageFilter.GaussianBlur(3)).resize((W, H), Image.BILINEAR)
            img.alpha_composite(glow)
        if not dynamic:
            self._sky_cache = img.copy()
        return img

    def background(self, t):
        W, H = self.ctx.W, self.ctx.H
        img = self._static_sky(t)
        if self._layers is None:
            self._layers = self._make_layers()
            for L in self._layers:
                L["on"] = self._bake_windows(L, True) if L["windows"] else L["img"]
                L["off"] = L["img"]
        lights_out = self.params.get("lights_out_at")
        lo_t = self.ctx.resolve_time(lights_out) if lights_out is not None else None
        for L in self._layers:
            drift = (t * 0.004 + 0.02) * L["depth"] * W
            lay = L["on"]
            x = -int(drift % (lay.width - W)) if lay.width > W else 0
            if lo_t is not None and t >= lo_t:
                u = D.clamp((t - lo_t) / 2.5)
                lay = L["off"] if u >= 1 else Image.blend(L["on"], L["off"], u)
            img.alpha_composite(lay, (x, 0))
        if self.params.get("fog"):
            if not hasattr(self, "_fog"):
                rng = np.random.default_rng(seed_of(self.ctx.scene.get("id"), "fog"))
                n = rng.random((max(2, H // 64), max(2, W // 32))).astype("float32")
                fog = Image.fromarray((n * 255).astype("uint8")).resize((W * 2, H), Image.BICUBIC)
                fog = fog.filter(ImageFilter.GaussianBlur(self.ctx.U * 0.02))
                mask = Image.linear_gradient("L").resize((W * 2, H)).point(lambda v: int(v * 0.6))
                self._fog = Image.merge("RGBA", (Image.new("L", fog.size, 220),) * 3 + (ImageChops.multiply(fog, mask),))
            off = int((t * self.ctx.U * 0.02) % W)
            img.alpha_composite(self._fog.crop((off, 0, off + W, H)))
        return img

    def post_out(self, img, t):
        g = float(self.params.get("grain", 6.0))
        W, H = img.size
        if getattr(self, "_post", None) is None or self._post[0] != (W, H):
            v = vignette((W, H), 0.45)
            vig = Image.merge("RGB", (v, v, v))
            tiles = []
            rng = np.random.default_rng(17)
            for _ in range(4):
                n = rng.normal(128, g, (H // 2, W // 2)).clip(0, 255).astype("uint8")
                tiles.append(Image.fromarray(n, "L").resize((W, H), Image.NEAREST).convert("RGB"))
            self._post = ((W, H), vig, tiles)
        _, vig, tiles = self._post
        img = ImageChops.multiply(img, vig)
        if g > 0:
            img = ImageChops.overlay(img, tiles[int(t * 12) % 4])
        return img
