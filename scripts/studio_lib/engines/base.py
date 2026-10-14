"""Engine base: scene context, element caching, camera, transitions, overlays.

Every engine renders a scene as a pure function of time: `frame(t) -> RGB`.
Determinism (same spec -> same pixels) is what makes scene caching and
incremental rebuilds safe.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field

from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .. import design as D
from ..draw import Shape, roughen, seed_of, stroke_poly, fill_poly, hatch_layer, shapes_bbox, sub_path


# ------------------------------------------------------------------ context
@dataclass
class SceneContext:
    scene: dict
    width: int            # output width (px)
    height: int           # output height (px)
    ss: int               # supersampling factor
    fps: int
    duration: float
    theme: D.Theme
    fmt: str = "long"     # long | short
    words: list = field(default_factory=list)  # [(t_sec, word)] in scene time
    prev_last: Image.Image | None = None       # previous scene's final frame (for transitions)
    captions: list = field(default_factory=list)  # [(t0, t1, text, [(t, word)])] burned captions (shorts)
    badge: str | None = None                   # e.g. "DRAMATIZATION · FICTIONAL COMPANY"

    @property
    def W(self) -> int:
        return self.width * self.ss

    @property
    def H(self) -> int:
        return self.height * self.ss

    @property
    def U(self) -> float:
        """Layout unit = canvas short side (1080 * ss at full quality)."""
        return min(self.W, self.H)

    @property
    def vertical(self) -> bool:
        return self.height > self.width

    def px(self, pos) -> tuple[float, float]:
        return pos[0] * self.W, pos[1] * self.H

    def resolve_time(self, at, default: float = 0.0) -> float:
        """Seconds | "40%" | "cue:word" | "cue:word#2" | "end-1.5"."""
        if at is None:
            return default
        if isinstance(at, (int, float)):
            return float(at)
        s = str(at).strip()
        if s.endswith("%"):
            return float(s[:-1]) / 100.0 * self.duration
        if s.startswith("end"):
            return self.duration + float(s[3:] or 0)
        if s.startswith("cue:"):
            word, _, nth = s[4:].partition("#")
            n = int(nth or 1)
            target = re.sub(r"[^a-z0-9$%.]", "", word.lower())
            hits = [t for t, w in self.words if re.sub(r"[^a-z0-9$%.]", "", w.lower()).startswith(target)]
            if len(hits) >= n:
                return hits[n - 1]
            return default  # unresolved cue: fall back (reported by validator)
        return float(s)


# ------------------------------------------------------------------ style
@dataclass
class Style:
    name: str
    reveal: str = "draw"          # draw | pop | fade | slide
    rough: float = 0.0            # wobble amplitude in U-fraction
    boil_fps: float = 0.0         # line boil rate (0 = static lines)
    double_line: bool = False
    fill_mode: str = "flat"       # flat | hatch | wash | none
    fill_alpha: int = 255
    fill_after: float = 0.72      # draw-reveal fraction at which fills start
    line_scale: float = 1.0
    ink: str = "ink"
    text_font: str = "sans_bold"
    body_font: str = "sans"
    text_color: str = "ink"
    pen: bool = False             # draw a pen/hand cursor at the drawing tip
    draw_speed: float = 1.0


# ------------------------------------------------------------------ engine
class Engine:
    name = "base"
    style = Style("base")
    description = ""

    max_ss: int | None = None  # engines with soft/atmospheric looks skip supersampling

    def __init__(self, ctx: SceneContext):
        if self.max_ss and ctx.ss > self.max_ss:
            ctx.ss = self.max_ss
        self.ctx = ctx
        self.theme = ctx.theme
        from .elements import build_elements  # late import (circular)

        self.params = ctx.scene.get("params", {}) or {}
        self.elements = build_elements(self, ctx.scene.get("elements", []))
        self._cache: dict = {}
        self._bg_cache: Image.Image | None = None
        self.seed = seed_of(ctx.scene.get("id", "scene"))
        self.camera = ctx.scene.get("camera") or {}

    # ---------------- hooks for subclasses
    def background(self, t: float) -> Image.Image:
        if self._bg_cache is None:
            self._bg_cache = Image.new("RGBA", (self.ctx.W, self.ctx.H), self.theme.c("board") + (255,))
        return self._bg_cache.copy()

    def post(self, img: Image.Image, t: float) -> Image.Image:
        """Hook on the supersampled RGBA canvas (before camera)."""
        return img

    def post_out(self, img: Image.Image, t: float) -> Image.Image:
        """Hook on the final output-resolution RGB frame (after camera)."""
        return img

    # ---------------- shape rendering (shared)
    def line_w(self, base: float = 0.0045) -> float:
        return max(1.0, self.ctx.U * base * self.style.line_scale)

    def boil_index(self, t: float) -> int:
        return int(t * self.style.boil_fps) % 3 if self.style.boil_fps else 0

    def render_shapes(self, shapes: list[Shape], frac: float, key, t: float = 0.0,
                      fill_frac: float | None = None):
        """Rasterise shapes revealed to `frac` (by length). Returns (layer, (x0,y0), tip)."""
        st = self.style
        if not shapes:
            return None, (0, 0), None
        bi = self.boil_index(t)
        x0, y0, x1, y1 = shapes_bbox(shapes)
        pad = int(self.ctx.U * (st.rough * 3 + 0.01))
        x0, y0 = int(x0) - pad, int(y0) - pad
        w, h = int(x1 - x0) + pad, int(y1 - y0) + pad
        w, h = max(2, w), max(2, h)
        layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        amp = st.rough * self.ctx.U
        loc = lambda pts: [(x - x0, y - y0) for x, y in pts]  # noqa: E731
        # fills first (beneath lines)
        ff = fill_frac if fill_frac is not None else (
            1.0 if frac >= 1 else max(0.0, (frac - st.fill_after) / max(1e-6, 1 - st.fill_after)))
        if ff > 0 and st.fill_mode != "none":
            for i, s in enumerate(shapes):
                if s.fill is None or len(s.pts) < 3:
                    continue
                pts = loc(roughen(s.pts, amp * 0.6, seed_of(key, i, "f", bi)) if amp else s.pts)
                a = int(min(st.fill_alpha, s.fill_alpha) * ff)
                if st.fill_mode == "hatch":
                    hl = hatch_layer((w, h), pts, s.fill, spacing=self.ctx.U * 0.012,
                                     width=max(1, self.line_w(0.0018)), alpha=a, seed=seed_of(key, i))
                    layer.alpha_composite(hl)
                    fill_poly(d, pts, s.fill, int(a * 0.35))
                elif st.fill_mode == "wash":
                    wash = Image.new("RGBA", (w, h), (0, 0, 0, 0))
                    ImageDraw.Draw(wash).polygon([(round(x), round(y)) for x, y in pts],
                                                 fill=tuple(s.fill[:3]) + (int(a * 0.75),))
                    wash = wash.filter(ImageFilter.GaussianBlur(self.ctx.U * 0.002))
                    layer.alpha_composite(wash)
                else:
                    fill_poly(d, pts, s.fill, a)
        # lines, progressively by cumulative length
        lens = [max(1e-6, s.length()) for s in shapes if s.stroke is not None]
        total = sum(lens)
        budget = total * max(0.0, min(1.0, frac))
        tip = None
        for i, s in enumerate(shapes):
            if s.stroke is None or budget <= 0:
                continue
            pts = s.pts + ([s.pts[0]] if s.closed else [])
            L = max(1e-6, s.length())
            f = min(1.0, budget / L)
            budget -= L
            if amp:
                pts = roughen(pts, amp, seed_of(key, i, bi))
            part, tp = sub_path(pts, f)
            if len(part) >= 2:
                col = s.stroke if (st.ink == "keep" or s.role == "keep_color") else self.theme.c(st.ink)
                stroke_poly(d, loc(part), col, s.width * st.line_scale)
                if st.double_line and f >= 1:
                    p2 = loc(roughen(pts, amp * 1.4 + 1, seed_of(key, i, bi, "dbl")))
                    stroke_poly(d, p2, col, max(1, s.width * 0.45), alpha=120)
            if f < 1 and tp:
                tip = (tp[0] - x0, tp[1] - y0)  # local layer coords
        return layer, (x0, y0), tip

    # ---------------- per-element caching
    def element_layer(self, el, t: float):
        p = el.progress(t)
        if p <= 0 and not el.visible_before:
            return None
        static = p >= 1 and not el.is_dynamic(t)
        bi = self.boil_index(t) if self.style.boil_fps else 0
        key = (el.idx, "done", bi) if static else None
        if key and key in self._cache:
            return self._cache[key]
        res = el.render(p, t)
        if key:
            self._cache[key] = res
        return res

    # ---------------- camera
    def camera_rect(self, t: float) -> tuple[float, float, float, float]:
        """Returns (cx, cy, zoom) as crop centre (fraction) + zoom >= 1."""
        cam = self.camera
        move = cam.get("move", "drift")
        amt = float(cam.get("amount", 0.06))
        dur = max(0.1, self.ctx.duration)
        u = D.ease_in_out(t / dur)
        cx, cy = cam.get("focus", [0.5, 0.5])
        base = 1.0 + float(cam.get("base_zoom", 0.03))
        if move == "push_in":
            z = base + amt * u
        elif move == "pull_out":
            z = base + amt * (1 - u)
        elif move == "pan_left":
            z = base + amt
            cx = cx + (amt / 2) * (1 - 2 * u) * 0.9
        elif move == "pan_right":
            z = base + amt
            cx = cx - (amt / 2) * (1 - 2 * u) * 0.9
        elif move == "pan_up":
            z = base + amt
            cy = cy + (amt / 2) * (1 - 2 * u) * 0.9
        elif move == "static":
            z = 1.0
        else:  # drift: slow breathing so no frame is ever frozen
            z = base + 0.012 * math.sin(t * 0.45 + 0.7) + amt * 0.25 * u
            cx = cx + 0.004 * math.sin(t * 0.31)
            cy = cy + 0.003 * math.cos(t * 0.27)
        # optional punch-in at a time
        for k in cam.get("keys", []) or []:
            kt = self.ctx.resolve_time(k.get("at"))
            kz = float(k.get("zoom", 1.0))
            kd = float(k.get("dur", 0.8))
            e = D.ease_in_out((t - kt) / kd)
            z = z * (1 + (kz - 1) * e)
            if "focus" in k:
                cx = D.lerp(cx, k["focus"][0], e)
                cy = D.lerp(cy, k["focus"][1], e)
        z = max(1.0, z)
        half_w, half_h = 0.5 / z, 0.5 / z
        cx = min(max(cx, half_w), 1 - half_w)
        cy = min(max(cy, half_h), 1 - half_h)
        return cx, cy, z

    def apply_camera(self, img: Image.Image, t: float) -> Image.Image:
        cx, cy, z = self.camera_rect(t)
        W, H = img.size
        cw, ch = W / z, H / z
        box = (cx * W - cw / 2, cy * H - ch / 2, cx * W + cw / 2, cy * H + ch / 2)
        out = (self.ctx.width, self.ctx.height)
        if z == 1.0 and self.ctx.ss == 1:
            return img
        if z == 1.0 and self.ctx.ss in (2, 3, 4):
            return img.reduce(self.ctx.ss)
        return img.resize(out, Image.BILINEAR, box=box, reducing_gap=2.0 if self.ctx.ss > 1 else None)

    # ---------------- pen cursor (original procedural artwork)
    def draw_pen(self, img: Image.Image, tip, t: float):
        if tip is None:
            return
        U = self.ctx.U
        x, y = tip
        d = ImageDraw.Draw(img)
        L = U * 0.2
        wdt = U * 0.026
        # pen body runs from the tip towards the upper right, with a slight wiggle
        ang = math.radians(-55 + 3 * math.sin(t * 9))
        dirx, diry = math.cos(ang), math.sin(ang)
        nx, ny = -diry, dirx
        def Q(a, b):
            return (x + dirx * a + nx * b, y + diry * a + ny * b)
        shadow = [Q(U * 0.03, -wdt / 2 + U * 0.012), Q(L, -wdt / 2 + U * 0.012), Q(L, wdt / 2 + U * 0.012),
                  Q(U * 0.03, wdt / 2 + U * 0.012)]
        d.polygon(shadow, fill=(0, 0, 0, 40))
        tipcone = [Q(0, 0), Q(U * 0.03, -wdt / 2), Q(U * 0.03, wdt / 2)]
        d.polygon(tipcone, fill=self.theme.c("ink") + (255,))
        body = [Q(U * 0.03, -wdt / 2), Q(L, -wdt / 2), Q(L, wdt / 2), Q(U * 0.03, wdt / 2)]
        d.polygon(body, fill=self.theme.c("accent") + (255,))
        band = [Q(L * 0.62, -wdt / 2), Q(L * 0.7, -wdt / 2), Q(L * 0.7, wdt / 2), Q(L * 0.62, wdt / 2)]
        d.polygon(band, fill=self.theme.c("ink") + (255,))
        # stylised hand: rounded knuckle mass gripping the pen
        hc = Q(L * 0.42, U * 0.035)
        r = U * 0.05
        d.ellipse((hc[0] - r, hc[1] - r * 0.8, hc[0] + r, hc[1] + r * 0.8), fill=(236, 196, 160, 255),
                  outline=self.theme.c("ink") + (255,), width=max(1, int(U * 0.003)))
        f = Q(L * 0.25, U * 0.012)
        d.ellipse((f[0] - r * 0.42, f[1] - r * 0.32, f[0] + r * 0.42, f[1] + r * 0.32), fill=(236, 196, 160, 255),
                  outline=self.theme.c("ink") + (255,), width=max(1, int(U * 0.003)))
        sleeve = [Q(L * 0.55, U * 0.02), Q(L * 1.25, U * 0.02 + U * 0.03), Q(L * 1.25, U * 0.12), Q(L * 0.6, U * 0.09)]
        d.polygon(sleeve, fill=self.theme.c("cool") + (255,))

    # ---------------- frame
    def compose(self, t: float) -> Image.Image:
        img = self.background(t)
        tip = None
        for el in self.elements:
            if t < el.start and not el.visible_before:
                continue
            res = self.element_layer(el, t)
            if not res:
                continue
            layer, (x, y), etip = res[0], res[1], res[2]
            if layer is None:
                continue
            a = el.exit_alpha(t)
            if a <= 0:
                continue
            if a < 1:
                layer = layer.copy()
                layer.putalpha(layer.getchannel("A").point(lambda v, a=a: int(v * a)))
            img.alpha_composite(layer, (int(x), int(y)))
            if etip is not None and 0 < el.progress(t) < 1:
                tip = (etip[0] + x, etip[1] + y)
        if self.style.pen and tip is not None:
            self.draw_pen(img, tip, t)
        return self.post(img, t)

    def frame(self, t: float) -> Image.Image:
        img = self.compose(t)
        out = self.apply_camera(img, t).convert("RGB")
        out = self.post_out(out, t)
        out = self.apply_transition(out, t)
        if self.ctx.badge:
            self.draw_badge(out)
        if self.ctx.captions:
            self.draw_captions(out, t)
        return out

    # ---------------- transitions (blend with previous scene's last frame)
    def apply_transition(self, img: Image.Image, t: float) -> Image.Image:
        tr = self.ctx.scene.get("transition", "cut")
        if isinstance(tr, dict):
            kind, dur = tr.get("type", "cut"), float(tr.get("dur", 0.6))
        else:
            kind, dur = tr, 0.6
        if kind == "cut" or t >= dur:
            return img
        prev = self.ctx.prev_last
        u = D.ease_in_out(t / dur)
        if prev is None:  # first scene: fade from black
            if kind in ("fade", "crossfade", "fade_black"):
                return Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, u)
            return img
        if prev.size != img.size:
            prev = prev.resize(img.size)
        W, H = img.size
        if kind == "crossfade":
            return Image.blend(prev, img, u)
        if kind == "fade_black":
            if u < 0.5:
                return Image.blend(prev, Image.new("RGB", img.size, (0, 0, 0)), u * 2)
            return Image.blend(Image.new("RGB", img.size, (0, 0, 0)), img, (u - 0.5) * 2)
        if kind in ("wipe", "wipe_left", "erase"):
            out = prev.copy()
            x = int(W * u)
            out.paste(img.crop((0, 0, x, H)), (0, 0))
            if kind == "erase" and 0 < x < W:  # whiteboard eraser swipe
                d = ImageDraw.Draw(out)
                bw = max(8, W // 40)
                d.rectangle((x - bw, 0, x + bw // 3, H), fill=self.theme.c("board"))
            return out
        if kind in ("push", "whip"):
            out = Image.new("RGB", img.size)
            off = int(W * u)
            out.paste(prev, (-off, 0))
            out.paste(img, (W - off, 0))
            if kind == "whip" and 0.1 < u < 0.9:
                out = out.filter(ImageFilter.BoxBlur(max(1, int(W * 0.012 * math.sin(u * math.pi)))))
            return out
        if kind == "zoom_through":
            z = 1 + 0.6 * u
            pw, ph = W / z, H / z
            p = prev.resize((W, H), Image.BILINEAR, box=((W - pw) / 2, (H - ph) / 2, (W + pw) / 2, (H + ph) / 2))
            return Image.blend(p, img, u)
        if kind == "slide_up":
            out = prev.copy()
            off = int(H * (1 - u))
            out.paste(img, (0, off))
            return out
        return self._cinematic_transition(kind, prev, img, t, dur)

    # ---------------- V2 cinematic transitions
    # Parameters ported from video-shotcraft recipe cards (Apache-2.0, re-implemented in Pillow):
    # crash-zoom-punch, flash-cut, circle-match-iris, blinds-slice, glitch-displace, light-leak-burn.
    def _cinematic_transition(self, kind, prev, img, t, dur):
        W, H = img.size
        fps = self.ctx.fps
        f = t * fps  # frames since cut
        if kind == "crash_zoom":
            # 6-frame 3.5% pull-back, 6-frame ease-in push to 2.6x on the outgoing shot,
            # then the new shot lands with a decaying 14 px shake (e^(-f/1.8)).
            if f < 6:
                z = 1 - 0.035 * D.ease_in_out(f / 6)
                return self._zoom(prev, z)
            if f < 12:
                z = 0.965 + (2.6 - 0.965) * D.ease_in_cubic((f - 6) / 6)
                out = self._zoom(prev, z)
                return out.filter(ImageFilter.GaussianBlur(max(0.1, (z - 1) * W * 0.004)))
            k = f - 12
            amp = 14 * (W / 1920) * math.exp(-k / 1.8)
            dx = int(amp * math.sin(k * 2.7))
            dy = int(amp * 0.6 * math.cos(k * 3.1))
            out = Image.new("RGB", img.size)
            out.paste(self._zoom(img, 1.0 + 0.04 * math.exp(-k / 3)), (dx, dy))
            return out
        if kind == "flash_cut":
            white = Image.new("RGB", img.size, (255, 255, 255))
            if f < 3:
                return Image.blend(prev, white, f / 3)
            return Image.blend(white, img, D.clamp((f - 3) / 8))
        if kind == "iris":
            u = D.ease_in_out(t / dur)
            mask = Image.new("L", img.size, 0)
            r = math.hypot(W, H) / 2 * u
            ImageDraw.Draw(mask).ellipse((W / 2 - r, H / 2 - r, W / 2 + r, H / 2 + r), fill=255)
            return Image.composite(img, prev, mask)
        if kind == "blinds":
            u = D.ease_in_out(t / dur)
            n = 8
            mask = Image.new("L", img.size, 0)
            d = ImageDraw.Draw(mask)
            sh = H / n
            for i in range(n):
                local = D.clamp(u * 1.6 - i * 0.6 / n)
                d.rectangle((0, i * sh, W, i * sh + sh * local), fill=255)
            return Image.composite(img, prev, mask)
        if kind == "glitch":
            import random as _r

            u = t / dur
            base = prev if u < 0.5 else img
            rnd = _r.Random(int(f) * 7919 + 13)
            out = base.copy()
            for _ in range(10):
                y0 = rnd.randrange(0, H)
                hgt = rnd.randrange(max(2, H // 60), max(3, H // 12))
                off = int(rnd.uniform(-0.08, 0.08) * W * math.sin(math.pi * u))
                band = base.crop((0, y0, W, min(H, y0 + hgt)))
                out.paste(band, (off, y0))
            r, g, b = out.split()
            sh = int(W * 0.008 * math.sin(math.pi * u))
            r = r.transform(r.size, Image.AFFINE, (1, 0, sh, 0, 1, 0))
            b = b.transform(b.size, Image.AFFINE, (1, 0, -sh, 0, 1, 0))
            return Image.merge("RGB", (r, g, b))
        if kind == "light_leak":
            u = t / dur
            mixd = Image.blend(prev, img, D.ease_in_out(u))
            leak = Image.radial_gradient("L").resize((W, H)).point(lambda v: 255 - v)
            k = math.sin(math.pi * u) * 0.85
            warm = Image.merge("RGB", (leak, leak.point(lambda v: int(v * 0.62)), leak.point(lambda v: int(v * 0.25))))
            return ImageChops.screen(mixd, warm.point(lambda v: int(v * k)))
        return Image.blend(prev, img, D.ease_in_out(t / dur))

    @staticmethod
    def _zoom(im, z):
        W, H = im.size
        if z >= 1:
            cw, ch = W / z, H / z
            return im.resize((W, H), Image.BILINEAR, box=((W - cw) / 2, (H - ch) / 2, (W + cw) / 2, (H + ch) / 2))
        small = im.resize((max(1, int(W * z)), max(1, int(H * z))), Image.BILINEAR)
        out = Image.new("RGB", (W, H), (0, 0, 0))
        out.paste(small, ((W - small.width) // 2, (H - small.height) // 2))
        return out

    # ---------------- burned overlays
    def draw_badge(self, img: Image.Image):
        text = self.ctx.badge
        U = min(img.size)
        f = D.font("sans_bold", int(U * 0.022))
        d = ImageDraw.Draw(img, "RGBA")
        tw = f.getlength(text)
        pad = U * 0.012
        x = img.width - tw - pad * 3
        y = pad * 2
        d.rounded_rectangle((x - pad, y - pad * 0.6, x + tw + pad, y + U * 0.022 + pad * 0.9),
                            radius=pad, fill=(0, 0, 0, 120))
        d.text((x, y), text, font=f, fill=(255, 255, 255, 230))

    def draw_captions(self, img: Image.Image, t: float):
        cur = None
        for c in self.ctx.captions:
            if c[0] <= t < c[1]:
                cur = c
                break
        if not cur:
            return
        U = min(img.size)
        f = D.font("sans_bold", int(U * (0.062 if self.ctx.vertical else 0.042)))
        words = cur[2].split()
        spoken = sum(1 for wt, _ in cur[3] if wt <= t)
        d = ImageDraw.Draw(img, "RGBA")
        maxw = img.width * 0.84
        lines, line = [], []
        for i, w in enumerate(words):
            trial = " ".join([x for _, x in line] + [w])
            if line and f.getlength(trial) > maxw:
                lines.append(line)
                line = []
            line.append((i, w))
        if line:
            lines.append(line)
        lh = f.getmetrics()[0] + f.getmetrics()[1]
        y0 = img.height * (0.66 if self.ctx.vertical else 0.84) - lh * len(lines) / 2
        sw = max(2, int(U * 0.006))
        for li, ln in enumerate(lines):
            txt = " ".join(w for _, w in ln)
            x = (img.width - f.getlength(txt)) / 2
            y = y0 + li * lh
            for i, w in ln:
                col = self.theme.c("accent") if i == spoken - 1 else (255, 255, 255)
                d.text((x, y), w, font=f, fill=col + (255,), stroke_width=sw, stroke_fill=(0, 0, 0, 255))
                x += f.getlength(w + " ")
