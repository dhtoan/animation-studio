"""Scene elements. Each element is engine-agnostic: the engine's Style decides
whether it is drawn stroke by stroke (whiteboard, hand-drawn) or animated in
(motion graphics, kinetic, artistic).

Element spec keys shared by all types:
  type   element type (see ELEMENT_TYPES)
  at     start time (seconds | "40%" | "cue:word" | "end-2")
  dur    reveal duration in seconds
  until  optional exit time (fades out over 0.4 s)
  pos    [x, y] in 0..1 of the 16:9 frame; `pos_v` overrides for 9:16
  box    [x, y, w, h] in 0..1; `box_v` overrides for 9:16
  anim   override reveal: draw | pop | fade | slide
"""
from __future__ import annotations

import math
import random

from PIL import Image, ImageChops, ImageDraw

from .. import design as D
from ..draw import (Shape, character_shapes, ellipse_pts, icon_shapes, rect_pts, resample, seed_of, sub_path,
                    text_image, wipe, wrap_text)


# ------------------------------------------------------------ layout helpers
def _vpos(x: float, y: float) -> tuple[float, float]:
    """Heuristic 16:9 -> 9:16 recomposition: side-by-side becomes stacked."""
    return 0.5 + (x - 0.5) * 0.5, 0.5 + (y - 0.5) * 0.55 + (x - 0.5) * 0.42


class Element:
    default_dur = 1.2
    visible_before = False

    def __init__(self, eng, spec: dict, idx: int):
        self.eng = eng
        self.ctx = eng.ctx
        self.spec = spec
        self.idx = idx
        self.start = self.ctx.resolve_time(spec.get("at"), 0.0)
        self.dur = max(0.05, float(spec.get("dur", self.default_dur)) / max(0.1, eng.style.draw_speed))
        self.until = self.ctx.resolve_time(spec["until"]) if spec.get("until") is not None else None
        self.reveal = spec.get("anim") or eng.style.reveal
        self.key = (self.ctx.scene.get("id"), idx, spec.get("type"))
        self._full = None

    # -- layout
    def pos(self, key="pos", default=(0.5, 0.5)) -> tuple[float, float]:
        if self.ctx.vertical and self.spec.get(key + "_v"):
            p = self.spec[key + "_v"]
        else:
            p = self.spec.get(key, default)
            if self.ctx.vertical:
                p = _vpos(*p)
        return p[0] * self.ctx.W, p[1] * self.ctx.H

    def box(self, default=(0.1, 0.2, 0.8, 0.6)) -> tuple[float, float, float, float]:
        if self.ctx.vertical and self.spec.get("box_v"):
            x, y, w, h = self.spec["box_v"]
        else:
            x, y, w, h = self.spec.get("box", default)
            if self.ctx.vertical:
                cx, cy = _vpos(x + w / 2, y + h / 2)
                w2 = min(0.9, w * 1920 / 1080)
                h2 = h * 1080 / 1920 * 1.25
                x, y, w, h = cx - w2 / 2, cy - h2 / 2, w2, h2
                x = max(0.05, min(x, 0.95 - w))
        return x * self.ctx.W, y * self.ctx.H, w * self.ctx.W, h * self.ctx.H

    def size_px(self, default=0.08) -> float:
        return float(self.spec.get("size", default)) * self.ctx.U

    def color(self, key="color", default="ink"):
        return self.eng.theme.c(self.spec.get(key), default)

    # -- timing
    def progress(self, t: float) -> float:
        return D.clamp((t - self.start) / self.dur)

    def is_dynamic(self, t: float) -> bool:
        return False

    def exit_alpha(self, t: float) -> float:
        if self.until is None:
            return 1.0
        return 1.0 - D.clamp((t - self.until) / 0.4)

    # -- rendering
    def shapes(self) -> list[Shape]:
        return []

    def texts(self) -> list[tuple[Image.Image, float, float, int]]:
        """[(rgba_img, x_center, y_top, line_count)] in canvas px."""
        return []

    def render_full(self, t: float):
        return self.render_draw(1.0, t)

    def render_draw(self, p: float, t: float):
        shapes = self.shapes()
        texts = self.texts()
        # split progress: shapes first, then text (if both present)
        if shapes and texts:
            ps, pt = D.clamp(p / 0.7), D.clamp((p - 0.55) / 0.45)
        else:
            ps = pt = p
        layer, (x0, y0), tip = self.eng.render_shapes(shapes, ps, self.key, t) if shapes else (None, (0, 0), None)
        if not texts:
            return layer, (x0, y0), tip
        if tip is not None:
            tip = (tip[0] + x0, tip[1] + y0)  # to canvas coords while composing
        # compose texts onto a common canvas
        boxes = [(cx - im.width / 2, ty, cx + im.width / 2, ty + im.height) for im, cx, ty, _ in texts]
        if layer is not None:
            boxes.append((x0, y0, x0 + layer.width, y0 + layer.height))
        bx0 = int(min(b[0] for b in boxes))
        by0 = int(min(b[1] for b in boxes))
        bx1 = int(max(b[2] for b in boxes)) + 1
        by1 = int(max(b[3] for b in boxes)) + 1
        out = Image.new("RGBA", (max(1, bx1 - bx0), max(1, by1 - by0)), (0, 0, 0, 0))
        if layer is not None:
            out.alpha_composite(layer, (int(x0 - bx0), int(y0 - by0)))
        n = len(texts)
        for i, (im, cx, ty, lines) in enumerate(texts):
            f = D.clamp(pt * n - i)
            if f <= 0:
                continue
            if self.reveal == "draw":
                part, (tx, tyy) = wipe(im, f, lines)
                if f < 1:
                    tip = (cx - im.width / 2 + tx, ty + tyy)
            else:
                part = im
            out.alpha_composite(part, (int(cx - im.width / 2 - bx0), int(ty - by0)))
        if tip is not None:
            tip = (tip[0] - bx0, tip[1] - by0)
        return out, (bx0, by0), tip

    def render(self, p: float, t: float):
        if self.reveal == "draw":
            return self.render_draw(p, t)
        # pop / fade / slide: render full once, then transform
        if self._full is None or self.is_dynamic(t):
            full = self.render_full(t)
            if not self.is_dynamic(t):
                self._full = full
        else:
            full = self._full
        layer, (x, y), _ = full
        if layer is None or p >= 1:
            return layer, (x, y), None
        if self.reveal == "pop":
            s = max(0.02, D.ease_out_back(p))
            a = D.clamp(p * 3)
        elif self.reveal == "slide":
            s, a = 1.0, D.clamp(p * 2)
        else:
            s, a = 0.96 + 0.04 * D.ease_out_cubic(p), D.ease_out_cubic(p)
        w, h = layer.size
        lw, lh = max(1, int(w * s)), max(1, int(h * s))
        im = layer.resize((lw, lh), Image.BILINEAR) if (lw, lh) != (w, h) else layer.copy()
        if a < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        nx, ny = x + (w - lw) / 2, y + (h - lh) / 2
        if self.reveal == "slide":
            ny += (1 - D.ease_out_cubic(p)) * self.ctx.U * 0.06
        if self.reveal == "fade":
            ny += (1 - D.ease_out_cubic(p)) * self.ctx.U * 0.015
        return im, (nx, ny), None


# ------------------------------------------------------------ text-ish
def _text_font(eng, spec, role_default="h2"):
    role = spec.get("style", role_default)
    size = D.TYPE_SCALE.get(role, 0.05) * eng.ctx.U * float(spec.get("scale", 1.0))
    if spec.get("font"):
        fam = spec["font"]
    elif role in ("hero", "h1", "h2"):
        fam = eng.style.text_font
    else:
        fam = eng.style.body_font
    return D.font(fam, size), role


def _readable(eng, col):
    """Accessibility: keep on-screen text at WCAG AA contrast against the engine background."""
    bg = D.ENGINE_BG.get(eng.name)
    if bg is None or eng.ctx.scene.get("params", {}).get("allow_low_contrast"):
        return col
    bgc = bg if isinstance(bg, tuple) else eng.theme.c(bg)
    return D.ensure_contrast(col, bgc, 4.5)


class TextEl(Element):
    default_dur = 1.0

    def texts(self):
        fnt, role = _text_font(self.eng, self.spec)
        col = _readable(self.eng, self.eng.theme.c(self.spec.get("color"), self.eng.style.text_color))
        maxw = float(self.spec.get("max_width", 0.8 if not self.ctx.vertical else 0.86)) * self.ctx.W
        align = self.spec.get("align", "center")
        txt = self.spec.get("text", "")
        if self.spec.get("upper"):
            txt = txt.upper()
        stroke = int(self.ctx.U * 0.004) if self.spec.get("outline") else 0
        im = text_image(txt, fnt, col, maxw, align, stroke=stroke, stroke_color=(0, 0, 0))
        x, y = self.pos()
        lines = len(wrap_text(txt, fnt, maxw))
        if align == "left":
            x += im.width / 2
        elif align == "right":
            x -= im.width / 2
        return [(im, x, y - im.height / 2, lines)]

    def shapes(self):
        if not self.spec.get("underline"):
            return []
        im, x, y, _ = self.texts()[0]
        uy = y + im.height * 0.98
        col = self.eng.theme.c(self.spec.get("underline_color", "accent"))
        return [Shape([(x - im.width * 0.45, uy), (x + im.width * 0.45, uy + self.ctx.U * 0.004)], False, col,
                      self.eng.line_w(0.006), role="keep_color")]

    def render_draw(self, p, t):
        # text first, underline after
        if not self.spec.get("underline"):
            return super().render_draw(p, t)
        texts = self.texts()
        im, cx, ty, lines = texts[0]
        pt, ps = D.clamp(p / 0.75), D.clamp((p - 0.75) / 0.25)
        part, (tx, tyy) = wipe(im, pt, lines) if self.reveal == "draw" else (im, (0, 0))
        layer, (x0, y0), tip = self.eng.render_shapes(self.shapes(), ps, self.key, t)
        if tip is not None:
            tip = (tip[0] + x0, tip[1] + y0)
        bx0 = int(min(cx - im.width / 2, x0))
        by0 = int(min(ty, y0))
        bx1 = int(max(cx + im.width / 2, x0 + layer.width)) + 1
        by1 = int(max(ty + im.height, y0 + layer.height)) + 1
        out = Image.new("RGBA", (bx1 - bx0, by1 - by0), (0, 0, 0, 0))
        out.alpha_composite(part, (int(cx - im.width / 2 - bx0), int(ty - by0)))
        if ps > 0:
            out.alpha_composite(layer, (int(x0 - bx0), int(y0 - by0)))
        if pt < 1:
            tip = (cx - im.width / 2 + tx, ty + tyy)
        if tip is not None:
            tip = (tip[0] - bx0, tip[1] - by0)
        return out, (bx0, by0), tip


class CounterEl(Element):
    """Number that counts up/down. Keys: from, to, prefix, suffix, decimals, style, label."""
    default_dur = 1.8

    def is_dynamic(self, t):
        return self.progress(t) < 1

    def value_text(self, p):
        a, b = float(self.spec.get("from", 0)), float(self.spec.get("to", 100))
        v = a + (b - a) * D.ease_out_cubic(p)
        dec = int(self.spec.get("decimals", 0))
        s = f"{v:,.{dec}f}"
        return f"{self.spec.get('prefix', '')}{s}{self.spec.get('suffix', '')}"

    def render(self, p, t):
        fnt, _ = _text_font(self.eng, {**self.spec, "style": self.spec.get("style", "hero")})
        col = _readable(self.eng, self.eng.theme.c(self.spec.get("color"), self.eng.style.text_color))
        im = text_image(self.value_text(max(p, 0.0)), fnt, col)
        x, y = self.pos()
        lab = self.spec.get("label")
        if lab:
            lf = D.font(self.eng.style.body_font, D.TYPE_SCALE["body"] * self.ctx.U)
            li = text_image(lab, lf, self.eng.theme.c(self.spec.get("label_color"), "muted"),
                            self.ctx.W * 0.7)
            out = Image.new("RGBA", (max(im.width, li.width), im.height + li.height), (0, 0, 0, 0))
            out.alpha_composite(im, ((out.width - im.width) // 2, 0))
            out.alpha_composite(li, ((out.width - li.width) // 2, im.height))
            im = out
        a = D.clamp(p * 4)
        if a < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        return im, (x - im.width / 2, y - im.height / 2), None


# ------------------------------------------------------------ icons & shapes
class IconEl(Element):
    default_dur = 1.1

    def shapes(self):
        x, y = self.pos()
        ink = self.eng.theme.c(self.spec["color"]) if self.spec.get("color") else None
        return icon_shapes(self.spec.get("name", "building"), x, y, self.size_px(0.08), self.eng.theme,
                           ink=ink, width=self.eng.line_w(), fills=self.spec.get("fill", True))

    def texts(self):
        lab = self.spec.get("label")
        if not lab:
            return []
        f = D.font(self.eng.style.body_font, D.TYPE_SCALE["label"] * self.ctx.U * float(self.spec.get("label_scale", 1)))
        im = text_image(lab, f, self.eng.theme.c(self.spec.get("label_color"), self.eng.style.text_color),
                        self.size_px(0.08) * 3.2)
        x, y = self.pos()
        return [(im, x, y + self.size_px(0.08) * 1.12, len(wrap_text(lab, f, self.size_px(0.08) * 3.2)))]


class ArrowEl(Element):
    default_dur = 0.8

    def shapes(self):
        sx, sy = self.pos("from", (0.3, 0.5))
        ex, ey = self.pos("to", (0.7, 0.5))
        bend = float(self.spec.get("curve", 0.15))
        mx, my = (sx + ex) / 2, (sy + ey) / 2
        dx, dy = ex - sx, ey - sy
        L = math.hypot(dx, dy) or 1
        cx, cy = mx - dy / L * bend * L, my + dx / L * bend * L
        pts = []
        for i in range(25):
            u = i / 24
            pts.append(((1 - u) ** 2 * sx + 2 * (1 - u) * u * cx + u * u * ex,
                        (1 - u) ** 2 * sy + 2 * (1 - u) * u * cy + u * u * ey))
        col = self.eng.theme.c(self.spec.get("color"), "ink")
        w = self.eng.line_w(0.005)
        hx, hy = pts[-1]
        px, py = pts[-3]
        a = math.atan2(hy - py, hx - px)
        hl = self.ctx.U * 0.03
        head = [(hx - hl * math.cos(a - 0.45), hy - hl * math.sin(a - 0.45)), (hx, hy),
                (hx - hl * math.cos(a + 0.45), hy - hl * math.sin(a + 0.45))]
        role = "keep_color" if self.spec.get("color") else "line"
        out = [Shape(pts, False, col, w, role=role), Shape(head, False, col, w, role=role)]
        if self.spec.get("dashed"):
            out[0].role = "keep_color"
        return out

    def texts(self):
        lab = self.spec.get("label")
        if not lab:
            return []
        sx, sy = self.pos("from", (0.3, 0.5))
        ex, ey = self.pos("to", (0.7, 0.5))
        f = D.font(self.eng.style.body_font, D.TYPE_SCALE["label"] * self.ctx.U)
        im = text_image(lab, f, self.eng.theme.c(self.spec.get("label_color"), "muted"), self.ctx.U * 0.5)
        return [(im, (sx + ex) / 2, (sy + ey) / 2 - im.height - self.ctx.U * 0.03, 1)]


class ShapeEl(Element):
    """Generic shape: kind = rect | circle | line | underline | bracket | x_mark | check_mark."""
    default_dur = 0.7

    def shapes(self):
        kind = self.spec.get("kind", "rect")
        col = self.eng.theme.c(self.spec.get("color"), "ink")
        fill = self.eng.theme.c(self.spec["fill"]) if self.spec.get("fill") else None
        w = self.eng.line_w(float(self.spec.get("weight", 0.005)))
        role = "keep_color" if self.spec.get("color") else "line"
        if kind in ("rect", "circle"):
            x, y, bw, bh = self.box((0.3, 0.3, 0.4, 0.4))
            pts = rect_pts(x, y, bw, bh, float(self.spec.get("radius", 0.02)) * self.ctx.U) if kind == "rect" \
                else ellipse_pts(x + bw / 2, y + bh / 2, bw / 2, bh / 2, 56)
            return [Shape(pts, True, col, w, fill, role=role)]
        if kind == "x_mark":
            x, y = self.pos()
            s = self.size_px(0.06)
            return [Shape([(x - s, y - s), (x + s, y + s)], False, col, w * 1.6, role="keep_color"),
                    Shape([(x + s, y - s), (x - s, y + s)], False, col, w * 1.6, role="keep_color")]
        if kind == "check_mark":
            x, y = self.pos()
            s = self.size_px(0.06)
            return [Shape([(x - s, y), (x - s * 0.3, y + s * 0.7), (x + s, y - s * 0.8)], False, col, w * 1.6,
                          role="keep_color")]
        a = self.pos("from", (0.3, 0.5))
        b = self.pos("to", (0.7, 0.5))
        return [Shape([a, b], False, col, w, role=role)]


class StampEl(Element):
    """Rubber-stamp slam (e.g. BANKRUPT). Keys: text, color, angle."""
    default_dur = 0.35

    def render(self, p, t):
        col = self.eng.theme.c(self.spec.get("color"), "negative")
        f = D.font("display", self.ctx.U * float(self.spec.get("scale", 0.09)))
        txt = self.spec.get("text", "BANKRUPT").upper()
        tw = int(f.getlength(txt))
        asc, desc = f.getmetrics()
        pad = int(self.ctx.U * 0.025)
        im = Image.new("RGBA", (tw + pad * 4, asc + desc + pad * 3), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        bw = max(3, int(self.ctx.U * 0.008))
        d.rounded_rectangle((bw, bw, im.width - bw, im.height - bw), radius=pad, outline=col + (235,), width=bw)
        d.text((pad * 2, pad), txt, font=f, fill=col + (235,))
        # worn ink texture
        rnd = random.Random(seed_of(self.key))
        for _ in range(int(im.width * im.height / 900)):
            x, y = rnd.randrange(im.width), rnd.randrange(im.height)
            d.point((x, y), fill=(0, 0, 0, 0))
        im = im.rotate(float(self.spec.get("angle", -12)), expand=True, resample=Image.BICUBIC)
        s = 1 + 1.4 * (1 - D.ease_in_cubic(p))
        a = D.clamp(p * 2.5)
        w, h = int(im.width * s), int(im.height * s)
        im = im.resize((max(1, w), max(1, h)), Image.BILINEAR)
        if a < 1:
            im.putalpha(im.getchannel("A").point(lambda v: int(v * a)))
        x, y = self.pos()
        return im, (x - w / 2, y - h / 2), None


class CardEl(Element):
    """Panel with title/body (quote card, fact card). Keys: box, title, body, tone, tag."""
    default_dur = 0.8

    def render_full(self, t):
        x, y, w, h = self.box((0.55, 0.25, 0.38, 0.4))
        th = self.eng.theme
        tone = self.spec.get("tone", "light")
        im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        r = int(self.ctx.U * 0.02)
        bg = th.c(tone)
        d.rounded_rectangle((0, 0, im.width - 1, im.height - 1), radius=r, fill=bg + (245,),
                            outline=th.c(self.spec.get("border"), "ink") + (255,), width=max(2, int(self.ctx.U * 0.003)))
        dark = sum(bg) < 360
        fg = (245, 245, 245) if dark else th.c("ink")
        pad = self.ctx.U * 0.03
        yy = pad
        if self.spec.get("tag"):
            tf = D.font("sans_bold", D.TYPE_SCALE["small"] * self.ctx.U)
            tag = self.spec["tag"].upper()
            tw = tf.getlength(tag)
            d.rounded_rectangle((pad, yy, pad + tw + pad * 0.8, yy + tf.size * 1.5), radius=r // 2,
                                fill=th.c(self.spec.get("tag_color"), "accent") + (255,))
            d.text((pad + pad * 0.4, yy + tf.size * 0.2), tag, font=tf, fill=(20, 20, 20, 255))
            yy += tf.size * 2.1
        if self.spec.get("title"):
            f = D.font(self.eng.style.text_font, D.TYPE_SCALE["h3"] * self.ctx.U)
            for ln in wrap_text(self.spec["title"], f, w - 2 * pad):
                d.text((pad, yy), ln, font=f, fill=fg + (255,))
                yy += f.size * 1.2
            yy += pad * 0.3
        if self.spec.get("body"):
            f = D.font(self.eng.style.body_font, D.TYPE_SCALE["body"] * self.ctx.U * float(self.spec.get("body_scale", 1)))
            for ln in wrap_text(self.spec["body"], f, w - 2 * pad):
                d.text((pad, yy), ln, font=f, fill=fg + (230,))
                yy += f.size * 1.3
        return im, (x, y), None

    def render(self, p, t):
        if self.reveal == "draw":
            # outline draws, then content fades in
            x, y, w, h = self.box((0.55, 0.25, 0.38, 0.4))
            sh = [Shape(rect_pts(x, y, w, h, self.ctx.U * 0.02), True, self.eng.theme.c("ink"), self.eng.line_w())]
            layer, (x0, y0), tip = self.eng.render_shapes(sh, D.clamp(p / 0.6), self.key, t, fill_frac=0)
            if p > 0.6:
                full, (fx, fy), _ = self.render_full(t)
                a = D.clamp((p - 0.6) / 0.4)
                full = full.copy()
                full.putalpha(full.getchannel("A").point(lambda v: int(v * a)))
                layer = layer.copy()
                layer.alpha_composite(full, (int(fx - x0), int(fy - y0)))
            return layer, (x0, y0), tip
        return super().render(p, t)


class ImageEl(Element):
    """Raster asset. Keys: src (project-relative), pos, width (fraction of W)."""
    default_dur = 0.8

    def render_full(self, t):
        from pathlib import Path

        src = Path(self.ctx.scene.get("_project_dir", ".")) / self.spec["src"]
        im = Image.open(src).convert("RGBA")
        w = float(self.spec.get("width", 0.4)) * (self.ctx.W if not self.ctx.vertical else self.ctx.W * 1.6)
        w = min(w, self.ctx.W * 0.92)
        h = im.height * w / im.width
        im = im.resize((int(w), int(h)), Image.LANCZOS)
        x, y = self.pos()
        return im, (x - w / 2, y - h / 2), None

    def render(self, p, t):
        if self.reveal == "draw":
            self.reveal = "fade"
        return super().render(p, t)


# ------------------------------------------------------------ data viz
def _fmt(v: float, spec: dict) -> str:
    dec = int(spec.get("decimals", 0))
    return f"{spec.get('prefix', '')}{v:,.{dec}f}{spec.get('suffix', '')}"


class BarChartEl(Element):
    """Keys: box, bars [{label, value, color}], max, prefix/suffix/decimals, stagger."""
    default_dur = 2.4

    def is_dynamic(self, t):
        return self.progress(t) < 1

    def render(self, p, t):
        x, y, w, h = self.box((0.12, 0.25, 0.76, 0.6))
        th = self.eng.theme
        bars = self.spec.get("bars", [])
        n = max(1, len(bars))
        vmax = float(self.spec.get("max", max([abs(b.get("value", 0)) for b in bars] + [1])))
        pad = self.ctx.U * 0.03
        lab_f = D.font(self.eng.style.body_font, D.TYPE_SCALE["label"] * self.ctx.U)
        val_f = D.font(self.eng.style.text_font, D.TYPE_SCALE["h3"] * self.ctx.U)
        lab_h = lab_f.size * 1.8
        im = Image.new("RGBA", (int(w + 2 * pad), int(h + 2 * pad)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        ink = th.c(self.eng.style.text_color)
        base_y = pad + h - lab_h
        axis_p = D.clamp(p / 0.15)
        lw = max(2, int(self.eng.line_w()))
        d.line((pad, base_y, pad + w * axis_p, base_y), fill=ink + (255,), width=lw)
        slot = w / n
        bw = slot * 0.58
        stag = float(self.spec.get("stagger", 0.8))
        top_room = val_f.size * 1.6
        draw_mode = self.reveal == "draw"
        tip = None
        for i, b in enumerate(bars):
            seg0 = 0.15 + (0.85 * stag) * i / n
            seg1 = seg0 + 0.85 * (1 - stag) + 0.85 * stag / n
            q = D.clamp((p - seg0) / max(1e-6, seg1 - seg0))
            if q <= 0:
                continue
            e = D.ease_out_cubic(q) if draw_mode else D.ease_out_back(q, 1.2)
            val = float(b.get("value", 0))
            bh = (h - lab_h - top_room) * abs(val) / vmax
            cx = pad + slot * (i + 0.5)
            col = th.c(b.get("color"), "cool")
            x0, x1 = cx - bw / 2, cx + bw / 2
            y1 = base_y
            y0 = base_y - bh * min(1.0, e)
            if draw_mode:
                # outline traced up, then fill
                outline_q = D.clamp(q / 0.7)
                yt = base_y - bh * outline_q
                d.line((x0, y1, x0, yt), fill=ink + (255,), width=lw)
                if outline_q >= 1:
                    d.line((x0, yt, x1, yt), fill=ink + (255,), width=lw)
                    d.line((x1, yt, x1, y1), fill=ink + (255,), width=lw)
                    fa = int(200 * D.clamp((q - 0.7) / 0.3))
                    d.rectangle((x0 + lw, yt + lw, x1 - lw, y1 - 1), fill=col + (fa,))
                if q < 1:
                    tip = (x0, yt)
                y0 = yt
            else:
                if bh * e > 1:
                    d.rounded_rectangle((x0, y0, x1, y1), radius=int(min(bw * 0.12, bh * e / 2)), fill=col + (255,))
            # labels
            lab = str(b.get("label", ""))
            tw = lab_f.getlength(lab)
            d.text((cx - tw / 2, base_y + lab_f.size * 0.4), lab, font=lab_f,
                   fill=th.c(self.spec.get("label_color"), "muted") + (int(255 * D.clamp(q * 3)),))
            vt = _fmt(val * min(1.0, D.ease_out_cubic(q)), {**self.spec, **b})
            vw = val_f.getlength(vt)
            d.text((cx - vw / 2, y0 - val_f.size * 1.35), vt, font=val_f, fill=ink + (int(255 * D.clamp(q * 2)),))
        title = self.spec.get("title")
        if title:
            tf = D.font(self.eng.style.text_font, D.TYPE_SCALE["h3"] * self.ctx.U)
            d.text((pad, pad - tf.size * 0.2), title, font=tf, fill=ink + (int(255 * D.clamp(p * 4)),))
        return im, (x - pad, y - pad), tip


class LineChartEl(Element):
    """Keys: box, values, labels, color, area(bool), mark {index, text}, prefix/suffix."""
    default_dur = 2.6

    def is_dynamic(self, t):
        return self.progress(t) < 1

    def render(self, p, t):
        x, y, w, h = self.box((0.1, 0.2, 0.8, 0.62))
        th = self.eng.theme
        vals = [float(v) for v in self.spec.get("values", [1, 2, 3])]
        n = len(vals)
        vmin = float(self.spec.get("min", min(vals + [0])))
        vmax = float(self.spec.get("max", max(vals) * 1.1 or 1))
        pad = self.ctx.U * 0.03
        im = Image.new("RGBA", (int(w + 2 * pad), int(h + 2 * pad)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        ink = th.c(self.eng.style.text_color)
        muted = th.c("muted")
        lw = max(2, int(self.eng.line_w()))
        lab_f = D.font(self.eng.style.body_font, D.TYPE_SCALE["label"] * self.ctx.U)
        lab_h = lab_f.size * 1.8 if self.spec.get("labels") else 0
        gx0, gy0, gx1, gy1 = pad, pad + self.ctx.U * 0.05, pad + w, pad + h - lab_h
        ax = D.clamp(p / 0.12)
        d.line((gx0, gy1, gx0 + (gx1 - gx0) * ax, gy1), fill=ink + (255,), width=lw)
        for k in range(1, 4):  # faint gridlines
            gy = gy1 - (gy1 - gy0) * k / 4
            d.line((gx0, gy, gx0 + (gx1 - gx0) * ax, gy), fill=muted + (60,), width=1)
        pts = [(gx0 + (gx1 - gx0) * i / max(1, n - 1), gy1 - (gy1 - gy0) * (v - vmin) / max(1e-9, vmax - vmin))
               for i, v in enumerate(vals)]
        q = D.clamp((p - 0.12) / 0.88)
        upto = q * (n - 1)
        k = int(upto)
        part = pts[: k + 1]
        if k < n - 1:
            f = upto - k
            a, b = pts[k], pts[k + 1]
            part.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
        col = th.c(self.spec.get("color"), "positive")
        if self.spec.get("colors_after") is not None:
            pass
        if len(part) >= 2:
            if self.spec.get("area", True):
                d.polygon(part + [(part[-1][0], gy1), (part[0][0], gy1)], fill=col + (50,))
            # segment colouring: red after `drop_index`
            di = self.spec.get("drop_index")
            for i in range(len(part) - 1):
                c = th.c("negative") if (di is not None and i >= di) else col
                d.line((part[i], part[i + 1]), fill=c + (255,), width=int(lw * 1.6))
            hx, hy = part[-1]
            r = lw * 2.2
            d.ellipse((hx - r, hy - r, hx + r, hy + r), fill=ink + (255,))
        labels = self.spec.get("labels") or []
        for i, lab in enumerate(labels):
            if i / max(1, n - 1) <= q + 1e-6:
                lx = gx0 + (gx1 - gx0) * i / max(1, len(labels) - 1)
                tw = lab_f.getlength(str(lab))
                d.text((lx - tw / 2, gy1 + lab_f.size * 0.4), str(lab), font=lab_f, fill=muted + (255,))
        mark = self.spec.get("mark")
        if mark and q >= mark.get("index", n - 1) / max(1, n - 1):
            mx, my = pts[int(mark.get("index", n - 1))]
            mf = D.font(self.eng.style.text_font, D.TYPE_SCALE["h3"] * self.ctx.U)
            txt = mark.get("text", _fmt(vals[int(mark.get("index", n - 1))], self.spec))
            tw = mf.getlength(txt)
            tx = min(max(mx - tw / 2, gx0), gx1 - tw)
            d.text((tx, my - mf.size * 1.6), txt, font=mf, fill=th.c(mark.get("color"), "negative") + (255,))
        tip = (part[-1][0], part[-1][1]) if (len(part) >= 2 and q < 1) else None
        return im, (x - pad, y - pad), tip


class DonutEl(Element):
    """Keys: pos, size, segments [{value, color, label}], center (text)."""
    default_dur = 1.8

    def is_dynamic(self, t):
        return self.progress(t) < 1

    def render(self, p, t):
        th = self.eng.theme
        cx, cy = self.pos()
        R = self.size_px(0.18)
        segs = self.spec.get("segments", [])
        tot = sum(float(s.get("value", 0)) for s in segs) or 1
        pad = int(R * 0.15)
        im = Image.new("RGBA", (int(2 * R + 2 * pad), int(2 * R + 2 * pad)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        a0 = -90.0
        q = D.ease_in_out(p)
        sweep_total = 360 * q
        for s in segs:
            sw = 360 * float(s.get("value", 0)) / tot
            vis = max(0.0, min(sw, sweep_total - (a0 + 90)))
            if vis > 0:
                d.pieslice((pad, pad, pad + 2 * R, pad + 2 * R), a0, a0 + vis, fill=th.c(s.get("color"), "cool") + (255,))
            a0 += sw
        r2 = R * 0.6
        bg = th.c(self.spec.get("hole"), "board")
        d.ellipse((pad + R - r2, pad + R - r2, pad + R + r2, pad + R + r2), fill=bg + (255,))
        ctext = self.spec.get("center")
        if ctext:
            f = D.font(self.eng.style.text_font, R * 0.32)
            tw = f.getlength(ctext)
            d.text((pad + R - tw / 2, pad + R - f.size * 0.62), ctext, font=f,
                   fill=th.c(self.eng.style.text_color) + (int(255 * D.clamp(p * 2)),))
        return im, (cx - R - pad, cy - R - pad), None


class NetworkEl(Element):
    """Keys: nodes [{id, label, pos, icon}], edges [[a, b]], break_at, broken [[a, b]]."""
    default_dur = 2.5

    def is_dynamic(self, t):
        bt = self.spec.get("break_at")
        return self.progress(t) < 1 or (bt is not None and t < self.ctx.resolve_time(bt) + 0.8)

    def _node_px(self, n):
        x, y = n.get("pos", [0.5, 0.5])
        if self.ctx.vertical:
            if n.get("pos_v"):
                x, y = n["pos_v"]
            else:
                x, y = _vpos(x, y)
        return x * self.ctx.W, y * self.ctx.H

    def render(self, p, t):
        th = self.eng.theme
        nodes = self.spec.get("nodes", [])
        byid = {n["id"]: n for n in nodes}
        edges = self.spec.get("edges", [])
        broken = {tuple(e) for e in self.spec.get("broken", [])} | {tuple(e[::-1]) for e in self.spec.get("broken", [])}
        bt = self.spec.get("break_at")
        btime = self.ctx.resolve_time(bt) if bt is not None else None
        W, H = self.ctx.W, self.ctx.H
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        lw = max(2, int(self.eng.line_w(0.004)))
        ink = th.c(self.eng.style.text_color)
        nn = max(1, len(nodes))
        ne = max(1, len(edges))
        # edges in second half
        for i, (a, b) in enumerate(edges):
            q = D.clamp((p - 0.35 - 0.5 * i / ne) / 0.25)
            if q <= 0 or a not in byid or b not in byid:
                continue
            (ax, ay), (bx, by) = self._node_px(byid[a]), self._node_px(byid[b])
            ex, ey = ax + (bx - ax) * q, ay + (by - ay) * q
            col = th.c("muted")
            if btime is not None and (a, b) in broken and t >= btime:
                k = D.clamp((t - btime) / 0.6)
                col = D.mix_rgb(col, th.c("negative"), k)
                mx, my = (ax + bx) / 2, (ay + by) / 2
                gap = 0.12 * k
                d.line((ax, ay, ax + (bx - ax) * (0.5 - gap), ay + (by - ay) * (0.5 - gap)), fill=col + (255,), width=lw)
                d.line((ax + (bx - ax) * (0.5 + gap), ay + (by - ay) * (0.5 + gap), bx, by), fill=col + (255,), width=lw)
                s = self.ctx.U * 0.018 * k
                d.line((mx - s, my - s, mx + s, my + s), fill=th.c("negative") + (255,), width=lw * 2)
                d.line((mx + s, my - s, mx - s, my + s), fill=th.c("negative") + (255,), width=lw * 2)
            else:
                d.line((ax, ay, ex, ey), fill=col + (255,), width=lw)
        # nodes
        f = D.font(self.eng.style.body_font, D.TYPE_SCALE["label"] * self.ctx.U)
        for i, n in enumerate(nodes):
            q = D.clamp((p - 0.35 * i / nn) / 0.25)
            if q <= 0:
                continue
            x, y = self._node_px(n)
            r = float(n.get("size", 0.045)) * self.ctx.U * (D.ease_out_back(q) if self.reveal != "draw" else 1)
            col = th.c(n.get("color"), "cool")
            if btime is not None and n.get("fails") and t >= btime:
                col = D.mix_rgb(col, th.c("negative"), D.clamp((t - btime) / 0.6))
            if self.reveal == "draw":
                ext = 360 * q
                d.arc((x - r, y - r, x + r, y + r), -90, -90 + ext, fill=ink + (255,), width=lw)
                if q >= 1:
                    d.ellipse((x - r + lw, y - r + lw, x + r - lw, y + r - lw), fill=col + (170,))
            else:
                d.ellipse((x - r, y - r, x + r, y + r), fill=col + (255,), outline=ink + (255,), width=max(1, lw // 2))
            if n.get("icon") and q >= 1:
                for s in icon_shapes(n["icon"], x, y, r * 0.55, th, ink=(255, 255, 255), width=max(1, lw * 0.7),
                                     fills=False):
                    pts = s.pts + ([s.pts[0]] if s.closed else [])
                    d.line([(round(a), round(b)) for a, b in pts], fill=(255, 255, 255, 255), width=max(1, int(lw * 0.7)))
            lab = n.get("label")
            if lab and q >= 0.6:
                tw = f.getlength(lab)
                d.text((x - tw / 2, y + r + f.size * 0.3), lab, font=f, fill=ink + (int(255 * D.clamp((q - 0.6) / 0.4)),))
        bb = im.getbbox()
        if not bb:
            return None, (0, 0), None
        return im.crop(bb), (bb[0], bb[1]), None


class TimelineEl(Element):
    """Keys: box, events [{label, sub, color}]."""
    default_dur = 2.5

    def is_dynamic(self, t):
        return self.progress(t) < 1

    def render(self, p, t):
        th = self.eng.theme
        x, y, w, h = self.box((0.08, 0.4, 0.84, 0.3))
        evs = self.spec.get("events", [])
        n = max(1, len(evs))
        pad = self.ctx.U * 0.04
        im = Image.new("RGBA", (int(w + 2 * pad), int(h + 2 * pad)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        ink = th.c(self.eng.style.text_color)
        lw = max(2, int(self.eng.line_w()))
        vertical = self.ctx.vertical and not self.spec.get("horizontal")
        lf = D.font(self.eng.style.text_font, D.TYPE_SCALE["h3"] * self.ctx.U)
        sf = D.font(self.eng.style.body_font, D.TYPE_SCALE["label"] * self.ctx.U)
        lp = D.clamp(p / 0.85)
        if not vertical:
            ly = pad + h * 0.45
            d.line((pad, ly, pad + w * lp, ly), fill=ink + (255,), width=lw)
        else:
            lx = pad + w * 0.18
            d.line((lx, pad, lx, pad + h * lp), fill=ink + (255,), width=lw)
        tip = None
        for i, e in enumerate(evs):
            fr = (i + 0.5) / n
            q = D.clamp((lp - fr) / 0.12 + 0.5) if lp >= fr - 0.06 else 0
            if q <= 0:
                continue
            col = th.c(e.get("color"), "accent")
            r = self.ctx.U * 0.014 * (D.ease_out_back(q) if self.reveal != "draw" else 1)
            if not vertical:
                cx, cy = pad + w * fr, ly
            else:
                cx, cy = lx, pad + h * fr
            d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=col + (255,), outline=ink + (255,), width=max(1, lw // 2))
            a = int(255 * q)
            lab, sub = str(e.get("label", "")), str(e.get("sub", ""))
            if not vertical:
                up = i % 2 == 0
                lw_ = lf.getlength(lab)
                ty = cy - r - lf.size * 1.5 if up else cy + r + lf.size * 0.4
                d.text((cx - lw_ / 2, ty), lab, font=lf, fill=ink + (a,))
                for j, ln in enumerate(wrap_text(sub, sf, w / n * 0.95)):
                    sw = sf.getlength(ln)
                    sy = (ty - sf.size * 1.3 * (len(wrap_text(sub, sf, w / n * 0.95)) - j)) if up else ty + lf.size * 1.3 + j * sf.size * 1.25
                    d.text((cx - sw / 2, sy), ln, font=sf, fill=th.c("muted") + (a,))
            else:
                d.text((cx + r * 2.2, cy - lf.size * 0.75), lab, font=lf, fill=ink + (a,))
                d.text((cx + r * 2.2, cy + lf.size * 0.45), sub, font=sf, fill=th.c("muted") + (a,))
        return im, (x - pad, y - pad), tip


class ProcessEl(Element):
    """Keys: box, steps [str | {label, icon, color}], fail_at (index of the broken step)."""
    default_dur = 2.6

    def is_dynamic(self, t):
        return self.progress(t) < 1

    def render(self, p, t):
        th = self.eng.theme
        x, y, w, h = self.box((0.06, 0.35, 0.88, 0.32))
        steps = [s if isinstance(s, dict) else {"label": s} for s in self.spec.get("steps", [])]
        n = max(1, len(steps))
        vertical = self.ctx.vertical
        pad = self.ctx.U * 0.02
        im = Image.new("RGBA", (int(w + 2 * pad), int(h + 2 * pad)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        ink = th.c(self.eng.style.text_color)
        lw = max(2, int(self.eng.line_w()))
        f = D.font(self.eng.style.text_font, D.TYPE_SCALE["label"] * self.ctx.U * 1.1)
        gap = 0.32
        for i, s in enumerate(steps):
            q = D.clamp((p - i / n * 0.9) / (0.9 / n))
            if q <= 0:
                continue
            if not vertical:
                bw = w / (n + (n - 1) * gap)
                bx, by, bww, bhh = pad + i * bw * (1 + gap), pad + h * 0.15, bw, h * 0.7
            else:
                bh = h / (n + (n - 1) * gap)
                bx, by, bww, bhh = pad + w * 0.1, pad + i * bh * (1 + gap), w * 0.8, bh
            col = th.c(s.get("color"), "light")
            failing = self.spec.get("fail_at") == i
            if failing:
                col = th.c("negative")
            a = int(255 * D.clamp(q * 2))
            s_ = D.ease_out_back(q) if self.reveal != "draw" else 1.0
            cx, cy = bx + bww / 2, by + bhh / 2
            hw, hh = bww / 2 * s_, bhh / 2 * s_
            d.rounded_rectangle((cx - hw, cy - hh, cx + hw, cy + hh), radius=int(self.ctx.U * 0.015),
                                fill=col + (int(a * 0.9),), outline=ink + (a,), width=lw)
            lines = wrap_text(s.get("label", ""), f, bww * 0.86)
            ty = cy - len(lines) * f.size * 0.62
            fg = (255, 255, 255) if failing or sum(col) < 360 else ink
            for ln in lines:
                tw = f.getlength(ln)
                d.text((cx - tw / 2, ty), ln, font=f, fill=fg + (a,))
                ty += f.size * 1.22
            if i < n - 1 and q >= 1:
                if not vertical:
                    ax0, ay0, ax1 = bx + bww + bw * gap * 0.15, cy, bx + bww + bw * gap * 0.85
                    d.line((ax0, ay0, ax1, ay0), fill=ink + (255,), width=lw)
                    d.polygon([(ax1, ay0), (ax1 - lw * 4, ay0 - lw * 3), (ax1 - lw * 4, ay0 + lw * 3)], fill=ink + (255,))
                else:
                    ay0, ax0, ay1 = by + bhh + bh * gap * 0.15, cx, by + bhh + bh * gap * 0.85
                    d.line((ax0, ay0, ax0, ay1), fill=ink + (255,), width=lw)
                    d.polygon([(ax0, ay1), (ax0 - lw * 3, ay1 - lw * 4), (ax0 + lw * 3, ay1 - lw * 4)], fill=ink + (255,))
        return im, (x - pad, y - pad), None


class ListEl(Element):
    """Bullet list revealed item by item. Keys: items [str], marker (dot|check|cross|num), box."""
    default_dur = 2.0

    def is_dynamic(self, t):
        return self.progress(t) < 1

    def render(self, p, t):
        th = self.eng.theme
        x, y, w, h = self.box((0.15, 0.25, 0.7, 0.55))
        items = self.spec.get("items", [])
        n = max(1, len(items))
        f = D.font(self.eng.style.body_font, D.TYPE_SCALE["body"] * self.ctx.U * float(self.spec.get("scale", 1.1)))
        ink = th.c(self.eng.style.text_color)
        im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        yy = 0.0
        mk = self.spec.get("marker", "dot")
        lw = max(2, int(self.eng.line_w()))
        for i, it in enumerate(items):
            q = D.clamp((p - i / n) / (1 / n) * 1.2)
            if q <= 0:
                break
            a = int(255 * q)
            off = (1 - D.ease_out_cubic(q)) * self.ctx.U * 0.03
            ms = f.size * 0.42
            mx, my = ms * 1.2 - off, yy + f.size * 0.62
            if mk == "check":
                d.line([(mx - ms, my), (mx - ms * 0.3, my + ms * 0.7), (mx + ms, my - ms * 0.8)],
                       fill=th.c("positive") + (a,), width=lw)
            elif mk == "cross":
                d.line((mx - ms, my - ms, mx + ms, my + ms), fill=th.c("negative") + (a,), width=lw)
                d.line((mx + ms, my - ms, mx - ms, my + ms), fill=th.c("negative") + (a,), width=lw)
            elif mk == "num":
                d.text((mx - ms, yy), f"{i + 1}.", font=f, fill=th.c("accent") + (a,))
            else:
                d.ellipse((mx - ms * 0.4, my - ms * 0.4, mx + ms * 0.4, my + ms * 0.4), fill=th.c("accent") + (a,))
            for j, ln in enumerate(wrap_text(it, f, w - ms * 4)):
                d.text((ms * 3.2 - off, yy), ln, font=f, fill=ink + (a,))
                yy += f.size * 1.25
            yy += f.size * 0.45
        return im, (x, y), None


# ------------------------------------------------------------ figures
class CharacterEl(Element):
    """Original simple figure. Keys: pos (feet), height (fraction of H), pose, poses [{at, pose}],
    talk (bool), color, facing."""
    default_dur = 1.4

    def is_dynamic(self, t):
        return True  # idle sway + blink + talk

    def pose_at(self, t):
        pose = self.spec.get("pose", "stand")
        for k in self.spec.get("poses", []) or []:
            if t >= self.ctx.resolve_time(k.get("at")):
                pose = k.get("pose", pose)
        return pose

    def render(self, p, t):
        x, y = self.pos("pos", (0.25, 0.85))
        h = float(self.spec.get("height", 0.5)) * self.ctx.H * (0.62 if self.ctx.vertical else 1.0)
        shapes = character_shapes(x, y, h, self.eng.theme, self.pose_at(t), t=t,
                                  talk=bool(self.spec.get("talk")) and p >= 1,
                                  color_role=self.spec.get("color", "cool"), width=self.eng.line_w(),
                                  blink_seed=self.idx, facing=int(self.spec.get("facing", 1)),
                                  ink=self.eng.theme.c(self.eng.style.text_color))
        if self.reveal == "draw":
            return self.eng.render_shapes(shapes, p, self.key, t)
        layer, xy, _ = self.eng.render_shapes(shapes, 1.0, self.key, t, fill_frac=1.0)
        if p < 1:
            a = D.ease_out_cubic(p)
            layer.putalpha(layer.getchannel("A").point(lambda v: int(v * a)))
            xy = (xy[0], xy[1] + (1 - a) * self.ctx.U * 0.05)
        return layer, xy, None


class CrowdEl(Element):
    """Rows of people icons appearing (customers, employees). Keys: box, count, color, highlight."""
    default_dur = 1.6

    def is_dynamic(self, t):
        return self.progress(t) < 1

    def render(self, p, t):
        th = self.eng.theme
        x, y, w, h = self.box((0.1, 0.3, 0.8, 0.5))
        n = int(self.spec.get("count", 24))
        cols = int(self.spec.get("cols", max(4, round(math.sqrt(n * w / max(h, 1))))))
        rows = math.ceil(n / cols)
        cw, ch = w / cols, h / rows
        im = Image.new("RGBA", (int(w), int(h)), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        col = th.c(self.spec.get("color"), "cool")
        hl = self.spec.get("highlight", 0)
        hcol = th.c(self.spec.get("highlight_color"), "negative")
        for i in range(n):
            q = D.clamp(p * n * 1.3 - i * 1.0)
            if q <= 0:
                continue
            r, c = divmod(i, cols)
            cx, cy = c * cw + cw / 2, r * ch + ch / 2
            s = min(cw, ch) * 0.36 * (D.ease_out_back(q) if self.reveal != "draw" else 1)
            cc = hcol if i < hl else col
            d.ellipse((cx - s * 0.45, cy - s * 1.0, cx + s * 0.45, cy - s * 0.1), fill=cc + (255,))
            d.rounded_rectangle((cx - s * 0.7, cy + s * 0.0, cx + s * 0.7, cy + s * 1.1), radius=int(s * 0.4), fill=cc + (255,))
        return im, (x, y), None


class ParticlesEl(Element):
    """Falling/rising particles: kind = coins | bills | dust | embers | rain | paper. Keys: count, speed."""
    default_dur = 0.5
    visible_before = False

    def is_dynamic(self, t):
        return True

    def render(self, p, t):
        th = self.eng.theme
        W, H = self.ctx.W, self.ctx.H
        kind = self.spec.get("kind", "dust")
        n = int(self.spec.get("count", 40))
        rnd = random.Random(seed_of(self.key))
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        tt = t - self.start
        speed = float(self.spec.get("speed", 1.0))
        a_mul = D.clamp(tt / 0.6)
        U = self.ctx.U
        for i in range(n):
            x0, y0 = rnd.random() * W, rnd.random() * H
            sp = rnd.uniform(0.4, 1.0) * speed
            ph = rnd.random() * 6.28
            if kind in ("coins", "bills", "paper", "rain", "snow"):
                yy = (y0 + tt * sp * H * (0.9 if kind == "rain" else 0.22)) % (H * 1.1) - H * 0.05
                xx = x0 + math.sin(tt * 1.3 + ph) * U * 0.02
            else:  # dust / embers rise
                yy = (y0 - tt * sp * H * 0.06) % H
                xx = x0 + math.sin(tt * 0.7 + ph) * U * 0.03
            if kind == "coins":
                r = U * rnd.uniform(0.012, 0.022)
                squash = abs(math.cos(tt * 3 * sp + ph))
                d.ellipse((xx - r, yy - r * max(0.15, squash), xx + r, yy + r * max(0.15, squash)),
                          fill=th.c("accent") + (int(230 * a_mul),), outline=th.c("ink") + (int(120 * a_mul),))
            elif kind in ("bills", "paper"):
                r = U * rnd.uniform(0.02, 0.035)
                ang = tt * 2 * sp + ph
                pts = [(xx + r * math.cos(ang + k), yy + r * 0.55 * math.sin(ang + k)) for k in (0.5, 2.6, 3.6, 5.7)]
                fill = (120, 170, 120) if kind == "bills" else (240, 238, 230)
                d.polygon(pts, fill=fill + (int(220 * a_mul),))
            elif kind == "rain":
                d.line((xx, yy, xx - U * 0.004, yy + U * 0.03), fill=(200, 210, 230, int(120 * a_mul)), width=max(1, int(U * 0.0015)))
            elif kind == "embers":
                r = U * rnd.uniform(0.002, 0.005)
                fl = 0.6 + 0.4 * math.sin(tt * 6 + ph)
                d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(255, 160, 60, int(255 * fl * a_mul)))
            else:
                r = U * rnd.uniform(0.0015, 0.004)
                d.ellipse((xx - r, yy - r, xx + r, yy + r), fill=(255, 255, 255, int(90 * a_mul)))
        return im, (0, 0), None


class MapEl(Element):
    default_dur = 1.6
    _geo_cache: dict = {}

    def is_dynamic(self, t):
        last = max([self.ctx.resolve_time(r.get("at"), 0) + float(r.get("dur", 2.0)) for r in self.spec.get("routes", [])]
                   + [self.ctx.resolve_time(m.get("at"), 0) + 0.6 for m in self.spec.get("markers", [])]
                   + [self.start + self.dur])
        return t < last + 0.05

    def _features(self):
        import json
        from pathlib import Path

        src = Path(self.ctx.scene.get("_project_dir", ".")) / self.spec["geojson"]
        key = str(src)
        if key not in self._geo_cache:
            self._geo_cache[key] = json.loads(src.read_text(encoding="utf-8"))["features"]
        return self._geo_cache[key]

    def render(self, p, t):
        th = self.eng.theme
        x, y, w, h = self.box((0.05, 0.08, 0.9, 0.84))
        lon0, lat0, lon1, lat1 = self.spec.get("bounds", [-12, 35, 20, 60])
        kx = math.cos(math.radians((lat0 + lat1) / 2))
        sx = w / ((lon1 - lon0) * kx)
        sy = h / (lat1 - lat0)
        s = min(sx, sy)
        ox = x + (w - (lon1 - lon0) * kx * s) / 2
        oy = y + (h - (lat1 - lat0) * s) / 2

        def P(lon, lat):
            return ox + (lon - lon0) * kx * s, oy + (lat1 - lat) * s

        W, H = self.ctx.W, self.ctx.H
        im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        lw = max(1, int(self.eng.line_w(0.0018)))
        land = th.c(self.spec.get("land", "light"))
        sea = th.c(self.spec.get("sea", "#6f8796"))
        d.rectangle((x, y, x + w, y + h), fill=sea + (int(255 * D.clamp(p * 2)),))
        border = th.c(self.spec.get("border", "muted"))
        hl = {h_["name"].lower(): th.c(h_.get("color", "accent")) for h_ in self.spec.get("highlight", [])}
        a_land = int(255 * D.clamp(p * 2))
        for f in self._features():
            props = f.get("properties", {})
            name = str(props.get("NAME") or props.get("ADMIN") or props.get("name") or "").lower()
            geom = f.get("geometry") or {}
            polys = geom.get("coordinates", [])
            if geom.get("type") == "Polygon":
                polys = [polys]
            elif geom.get("type") != "MultiPolygon":
                continue
            for poly in polys:
                ring = poly[0]
                if not any(lon0 - 5 <= lon <= lon1 + 5 and lat0 - 5 <= lat <= lat1 + 5 for lon, lat in ring[:: max(1, len(ring) // 20)]):
                    continue
                pts = [P(lon, lat) for lon, lat in ring]
                col = hl.get(name, land)
                hp = D.clamp((p - 0.4) / 0.6) if name in hl else 1.0
                fill = D.mix_rgb(land, col, hp) if name in hl else land
                d.polygon(pts, fill=fill + (a_land,), outline=border + (a_land,))
                if lw > 1:
                    d.line(pts + [pts[0]], fill=border + (a_land,), width=lw)
        ink = th.c(self.eng.style.text_color)
        f_lab = D.font(self.eng.style.body_font, D.TYPE_SCALE["label"] * self.ctx.U * 1.15)
        for lab in self.spec.get("labels", []):
            la = D.clamp((t - self.ctx.resolve_time(lab.get("at"), self.start + 0.6)) / 0.5)
            if la > 0:
                px, py = P(lab["lon"], lab["lat"])
                txt = lab["text"]
                d.text((px - f_lab.getlength(txt) / 2, py), txt, font=f_lab, fill=th.c(lab.get("color"), "muted") + (int(200 * la),))
        tip = None
        for r in self.spec.get("routes", []):
            r0 = self.ctx.resolve_time(r.get("at"), self.start + 0.8)
            q = D.clamp((t - r0) / float(r.get("dur", 2.0)))
            if q <= 0:
                continue
            pts = [P(lon, lat) for lon, lat in r["path"]]
            part, tp = sub_path(resample(pts, 4.0), D.ease_in_out(q))
            col = th.c(r.get("color"), "negative")
            if len(part) >= 2:
                if r.get("dashed"):
                    for i in range(0, len(part) - 1, 4):
                        d.line(part[i:i + 3], fill=col + (255,), width=lw * 3)
                else:
                    d.line(part, fill=col + (255,), width=lw * 3, joint="curve")
                if q < 1 and tp:
                    rr = lw * 4
                    d.ellipse((tp[0] - rr, tp[1] - rr, tp[0] + rr, tp[1] + rr), fill=col + (255,))
                elif q >= 1 and len(part) >= 3:
                    (ax, ay), (bx, by) = part[-3], part[-1]
                    ang = math.atan2(by - ay, bx - ax)
                    hl_ = self.ctx.U * 0.025
                    d.polygon([(bx, by), (bx - hl_ * math.cos(ang - 0.5), by - hl_ * math.sin(ang - 0.5)),
                               (bx - hl_ * math.cos(ang + 0.5), by - hl_ * math.sin(ang + 0.5))], fill=col + (255,))
        f_mk = D.font(self.eng.style.text_font, D.TYPE_SCALE["h3"] * self.ctx.U * 0.85)
        for m in self.spec.get("markers", []):
            q = D.clamp((t - self.ctx.resolve_time(m.get("at"), self.start + 0.5)) / 0.5)
            if q <= 0:
                continue
            px, py = P(m["lon"], m["lat"])
            r = self.ctx.U * 0.011 * D.ease_out_back(q)
            col = th.c(m.get("color"), "negative")
            d.ellipse((px - r, py - r, px + r, py + r), fill=col + (255,), outline=ink + (255,), width=max(1, lw))
            if m.get("label"):
                lbl = m["label"]
                d.text((px + r * 1.6, py - f_mk.size * 0.6), lbl, font=f_mk, fill=ink + (int(255 * q),),
                       stroke_width=max(1, lw), stroke_fill=land + (int(220 * q),))
        # clip everything to the map panel, then frame it
        clip = Image.new("L", (W, H), 0)
        ImageDraw.Draw(clip).rectangle((x, y, x + w, y + h), fill=255)
        im.putalpha(ImageChops.multiply(im.getchannel("A"), clip))
        ImageDraw.Draw(im).rectangle((x, y, x + w, y + h), outline=th.c("ink") + (int(200 * D.clamp(p * 2)),),
                                     width=max(2, lw * 2))
        bb = im.getbbox()
        if not bb:
            return None, (0, 0), None
        return im.crop(bb), (bb[0], bb[1]), None


ELEMENT_TYPES = {"map": MapEl,
    
    "text": TextEl, "counter": CounterEl, "icon": IconEl, "arrow": ArrowEl, "shape": ShapeEl,
    "stamp": StampEl, "card": CardEl, "image": ImageEl, "bar_chart": BarChartEl, "line_chart": LineChartEl,
    "donut": DonutEl, "network": NetworkEl, "timeline": TimelineEl, "process": ProcessEl, "list": ListEl,
    "character": CharacterEl, "crowd": CrowdEl, "particles": ParticlesEl,
}


def build_elements(eng, specs: list[dict]) -> list[Element]:
    out = []
    for i, s in enumerate(specs or []):
        cls = ELEMENT_TYPES.get(s.get("type"))
        if cls is None:
            raise ValueError(f"unknown element type {s.get('type')!r} in scene {eng.ctx.scene.get('id')}")
        out.append(cls(eng, s, i))
    return out
