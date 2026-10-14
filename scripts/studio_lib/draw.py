"""Drawing primitives shared by every engine.

Geometry is expressed as `Shape`s (polylines with optional fill) so the same
element can be drawn progressively (whiteboard / hand-drawn), popped in
(motion graphics) or rendered as a silhouette (artistic).  All artwork here is
generated procedurally and is original to this project.
"""
from __future__ import annotations

import math
import random
import zlib
from dataclasses import dataclass, field

from PIL import Image, ImageChops, ImageDraw, ImageFilter

Pt = tuple[float, float]


@dataclass
class Shape:
    pts: list[Pt]
    closed: bool = False
    stroke: tuple | None = (0, 0, 0)
    width: float = 4.0
    fill: tuple | None = None
    fill_alpha: int = 255
    role: str = "line"  # line | detail | fill_only

    def length(self) -> float:
        return poly_len(self.pts + ([self.pts[0]] if self.closed and self.pts else []))


# ---------------------------------------------------------------- geometry
def seed_of(*parts) -> int:
    return zlib.crc32("|".join(map(str, parts)).encode()) & 0xFFFFFFFF


def poly_len(pts: list[Pt]) -> float:
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def resample(pts: list[Pt], step: float) -> list[Pt]:
    if len(pts) < 2:
        return list(pts)
    out = [pts[0]]
    carry = 0.0
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        d = math.dist(a, b)
        if d == 0:
            continue
        pos = step - carry
        while pos < d:
            f = pos / d
            out.append((a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f))
            pos += step
        carry = d - (pos - step)
    out.append(pts[-1])
    return out


def sub_path(pts: list[Pt], frac: float) -> tuple[list[Pt], Pt | None]:
    """Prefix of a polyline covering `frac` of its length; returns (pts, tip)."""
    if frac <= 0 or len(pts) < 2:
        return [], (pts[0] if pts else None)
    if frac >= 1:
        return list(pts), pts[-1]
    total = poly_len(pts)
    want = total * frac
    acc = 0.0
    out = [pts[0]]
    for i in range(len(pts) - 1):
        a, b = pts[i], pts[i + 1]
        d = math.dist(a, b)
        if acc + d >= want:
            f = (want - acc) / d if d else 0
            tip = (a[0] + (b[0] - a[0]) * f, a[1] + (b[1] - a[1]) * f)
            out.append(tip)
            return out, tip
        out.append(b)
        acc += d
    return out, out[-1]


def ellipse_pts(cx, cy, rx, ry, n=48, a0=0.0, a1=math.tau, rot=0.0) -> list[Pt]:
    out = []
    cr, sr = math.cos(rot), math.sin(rot)
    for i in range(n + 1):
        a = a0 + (a1 - a0) * i / n
        x, y = rx * math.cos(a), ry * math.sin(a)
        out.append((cx + x * cr - y * sr, cy + x * sr + y * cr))
    return out


def rect_pts(x, y, w, h, r=0.0) -> list[Pt]:
    if r <= 0:
        return [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)]
    r = min(r, w / 2, h / 2)
    pts: list[Pt] = []
    for cx, cy, a0 in ((x + w - r, y + r, -math.pi / 2), (x + w - r, y + h - r, 0),
                       (x + r, y + h - r, math.pi / 2), (x + r, y + r, math.pi)):
        pts += ellipse_pts(cx, cy, r, r, 8, a0, a0 + math.pi / 2)
    pts.append(pts[0])
    return pts


def roughen(pts: list[Pt], amount: float, seed: int, step: float = 14.0) -> list[Pt]:
    """Low-frequency wobble that reads as a human line, not noise."""
    if amount <= 0 or len(pts) < 2:
        return pts
    rs = resample(pts, step)
    rnd = random.Random(seed)
    ph1, ph2 = rnd.uniform(0, 6.28), rnd.uniform(0, 6.28)
    f1, f2 = rnd.uniform(0.05, 0.11), rnd.uniform(0.15, 0.3)
    out = []
    n = len(rs)
    for i, (x, y) in enumerate(rs):
        # taper wobble to 0 at endpoints so joins stay connected
        k = min(1.0, i / 3, (n - 1 - i) / 3) if n > 6 else 1.0
        dx = (math.sin(i * f1 + ph1) + 0.5 * math.sin(i * f2 + ph2)) * amount * k
        dy = (math.cos(i * f1 * 1.3 + ph2) + 0.5 * math.cos(i * f2 + ph1)) * amount * k
        out.append((x + dx, y + dy))
    return out


def bbox(pts: list[Pt]) -> tuple[float, float, float, float]:
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def shapes_bbox(shapes: list[Shape]) -> tuple[float, float, float, float]:
    boxes = [bbox(s.pts) for s in shapes if s.pts]
    if not boxes:
        return 0, 0, 1, 1
    pad = max((s.width for s in shapes), default=4) * 2
    return (min(b[0] for b in boxes) - pad, min(b[1] for b in boxes) - pad,
            max(b[2] for b in boxes) + pad, max(b[3] for b in boxes) + pad)


# ---------------------------------------------------------------- rasterize
def stroke_poly(d: ImageDraw.ImageDraw, pts: list[Pt], color, width: float, alpha: int = 255):
    if len(pts) < 2:
        return
    w = max(1, int(round(width)))
    col = tuple(color[:3]) + (alpha,)
    d.line([(round(x), round(y)) for x, y in pts], fill=col, width=w, joint="curve")
    r = w / 2
    for (x, y) in (pts[0], pts[-1]):
        d.ellipse((x - r, y - r, x + r, y + r), fill=col)


def fill_poly(d: ImageDraw.ImageDraw, pts: list[Pt], color, alpha: int = 255):
    if len(pts) >= 3:
        d.polygon([(round(x), round(y)) for x, y in pts], fill=tuple(color[:3]) + (alpha,))


def hatch_layer(size, poly: list[Pt], color, spacing: float, width: float, angle: float = 0.8,
                alpha: int = 200, seed: int = 0) -> Image.Image:
    """Diagonal pencil hatching clipped to a polygon."""
    w, h = size
    layer = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    rnd = random.Random(seed)
    diag = w + h
    ca, sa = math.cos(angle), math.sin(angle)
    k = -diag
    while k < diag:
        x0, y0 = k * sa, -k * ca
        p0 = (x0 - ca * diag + w / 2, y0 - sa * diag + h / 2)
        p1 = (x0 + ca * diag + w / 2, y0 + sa * diag + h / 2)
        jitter = rnd.uniform(-spacing * 0.15, spacing * 0.15)
        d.line([(p0[0] + jitter, p0[1]), (p1[0] + jitter, p1[1])],
               fill=tuple(color[:3]) + (alpha,), width=max(1, int(width)))
        k += spacing
    mask = Image.new("L", size, 0)
    ImageDraw.Draw(mask).polygon([(round(x), round(y)) for x, y in poly], fill=255)
    layer.putalpha(ImageChops.multiply(layer.getchannel("A"), mask))
    return layer


# ---------------------------------------------------------------- text
def wrap_text(text: str, fnt, max_w: float) -> list[str]:
    lines: list[str] = []
    for para in text.split("\n"):
        words = para.split()
        cur = ""
        for w in words:
            trial = (cur + " " + w).strip()
            if fnt.getlength(trial) <= max_w or not cur:
                cur = trial
            else:
                lines.append(cur)
                cur = w
        lines.append(cur)
    return lines


def text_image(text: str, fnt, color, max_w: float | None = None, align: str = "center",
               line_gap: float = 1.18, stroke: int = 0, stroke_color=None) -> Image.Image:
    lines = wrap_text(text, fnt, max_w) if max_w else text.split("\n")
    asc, desc = fnt.getmetrics()
    lh = int((asc + desc) * line_gap)
    widths = [int(fnt.getlength(l)) + 2 * stroke + 4 for l in lines]
    W = max(widths + [1])
    H = lh * len(lines) + desc + 2 * stroke + 4
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for i, l in enumerate(lines):
        lw = widths[i]
        x = {"left": 0, "right": W - lw}.get(align, (W - lw) // 2) + stroke + 2
        d.text((x, i * lh + stroke + 2), l, font=fnt, fill=tuple(color[:3]) + (255,),
               stroke_width=stroke, stroke_fill=tuple((stroke_color or color)[:3]) + (255,))
    return img


def wipe(img: Image.Image, frac: float, line_count: int = 1) -> tuple[Image.Image, tuple[float, float]]:
    """Reveal text image left->right, line by line. Returns (img, pen tip in img coords)."""
    frac = max(0.0, min(1.0, frac))
    if frac >= 1:
        return img, (img.width, img.height * 0.6)
    W, H = img.size
    n = max(1, line_count)
    lh = H / n
    pos = frac * n
    full = int(pos)
    part = pos - full
    mask = Image.new("L", img.size, 0)
    md = ImageDraw.Draw(mask)
    if full:
        md.rectangle((0, 0, W, int(full * lh)), fill=255)
    x = int(W * part)
    md.rectangle((0, int(full * lh), x, int((full + 1) * lh)), fill=255)
    out = img.copy()
    out.putalpha(ImageChops.multiply(img.getchannel("A"), mask))
    return out, (x, (full + 0.65) * lh)


# ---------------------------------------------------------------- icon library
# Each icon is defined in a unit box [-1, 1]^2 (y down) as a list of
# (kind, data, fill_role) entries; kind: "poly" (closed), "line" (open),
# "circle" (cx, cy, r), "rect" (x, y, w, h, r).


def _star(n=5, r1=1.0, r2=0.45, rot=-math.pi / 2):
    pts = []
    for i in range(n * 2 + 1):
        r = r1 if i % 2 == 0 else r2
        a = rot + i * math.pi / n
        pts.append((r * math.cos(a), r * math.sin(a)))
    return pts


ICONS: dict[str, list] = {
    "building": [("rect", (-0.6, -0.95, 1.2, 1.9, 0), "light"),
                 *[("rect", (-0.42 + c * 0.32, -0.75 + r * 0.32, 0.18, 0.2, 0), "cool")
                   for r in range(4) for c in range(3)],
                 ("rect", (-0.15, 0.6, 0.3, 0.35, 0), "ink")],
    "factory": [("poly", [(-1, 0.9), (-1, -0.1), (-0.5, 0.25), (-0.5, -0.1), (0, 0.25), (0, -0.1),
                          (0.5, 0.25), (0.5, -0.9), (0.85, -0.9), (0.85, 0.9), (-1, 0.9)], "light"),
                ("rect", (-0.8, 0.45, 0.3, 0.25, 0), "accent"), ("rect", (-0.25, 0.45, 0.3, 0.25, 0), "accent")],
    "warehouse": [("poly", [(-1, 0.9), (-1, -0.2), (0, -0.85), (1, -0.2), (1, 0.9), (-1, 0.9)], "light"),
                  ("rect", (-0.5, 0.15, 1.0, 0.75, 0), "muted"),
                  ("line", [(-0.5, 0.4), (0.5, 0.4)], None), ("line", [(-0.5, 0.65), (0.5, 0.65)], None)],
    "truck": [("rect", (-1, -0.45, 1.2, 0.85, 0.05), "light"),
              ("poly", [(0.2, -0.15), (0.65, -0.15), (0.95, 0.15), (0.95, 0.4), (0.2, 0.4), (0.2, -0.15)], "cool"),
              ("circle", (-0.6, 0.55, 0.2), "ink"), ("circle", (0.6, 0.55, 0.2), "ink")],
    "box": [("poly", [(-0.8, -0.35), (0, -0.75), (0.8, -0.35), (0.8, 0.55), (0, 0.95), (-0.8, 0.55), (-0.8, -0.35)], "accent"),
            ("line", [(-0.8, -0.35), (0, 0.05), (0.8, -0.35)], None), ("line", [(0, 0.05), (0, 0.95)], None)],
    "coin": [("circle", (0, 0, 0.9), "accent"), ("circle", (0, 0, 0.68), None),
             ("line", [(0.22, -0.32), (-0.05, -0.36), (-0.22, -0.2), (-0.1, -0.02), (0.12, 0.04),
                       (0.24, 0.2), (0.08, 0.36), (-0.22, 0.32)], None), ("line", [(0, -0.5), (0, 0.5)], None)],
    "dollar": [("line", [(0.42, -0.5), (0.0, -0.62), (-0.42, -0.42), (-0.4, -0.1), (0.0, 0.0),
                         (0.4, 0.12), (0.42, 0.44), (0.0, 0.62), (-0.45, 0.48)], None),
               ("line", [(0, -0.95), (0, 0.95)], None)],
    "bank": [("poly", [(-1, -0.4), (0, -0.95), (1, -0.4), (-1, -0.4)], "light"),
             *[("rect", (-0.8 + i * 0.45, -0.3, 0.2, 0.9, 0), "light") for i in range(4)],
             ("rect", (-1, 0.65, 2, 0.25, 0), "muted")],
    "person": [("circle", (0, -0.62, 0.3), "light"),
               ("poly", [(-0.55, 0.95), (-0.55, 0.15), (-0.3, -0.2), (0.3, -0.2), (0.55, 0.15), (0.55, 0.95), (-0.55, 0.95)], "cool")],
    "crowd": [*[("circle", (x, -0.35 + dy, 0.2), "light") for x, dy in ((-0.6, 0.1), (0, 0), (0.6, 0.1))],
              *[("poly", [(x - 0.32, 0.9), (x - 0.32, 0.25 + dy), (x + 0.32, 0.25 + dy), (x + 0.32, 0.9), (x - 0.32, 0.9)], "muted")
                for x, dy in ((-0.6, 0.1), (0, 0), (0.6, 0.1))]],
    "phone": [("rect", (-0.5, -0.95, 1.0, 1.9, 0.15), "ink"), ("rect", (-0.4, -0.75, 0.8, 1.4, 0.05), "cool"),
              ("circle", (0, 0.82, 0.06), None)],
    "laptop": [("rect", (-0.75, -0.7, 1.5, 1.0, 0.06), "ink"), ("rect", (-0.65, -0.6, 1.3, 0.8, 0), "cool"),
               ("poly", [(-0.95, 0.4), (0.95, 0.4), (1.0, 0.6), (-1.0, 0.6), (-0.95, 0.4)], "muted")],
    "server": [*[("rect", (-0.7, -0.9 + i * 0.62, 1.4, 0.5, 0.06), "muted") for i in range(3)],
               *[("circle", (0.45, -0.65 + i * 0.62, 0.07), "positive") for i in range(3)]],
    "chart_up": [("line", [(-0.9, -0.9), (-0.9, 0.9), (0.95, 0.9)], None),
                 ("line", [(-0.7, 0.5), (-0.3, 0.1), (0.05, 0.3), (0.7, -0.6)], None),
                 ("poly", [(0.45, -0.65), (0.78, -0.7), (0.72, -0.37), (0.45, -0.65)], "positive")],
    "chart_down": [("line", [(-0.9, -0.9), (-0.9, 0.9), (0.95, 0.9)], None),
                   ("line", [(-0.7, -0.6), (-0.3, -0.2), (0.05, -0.35), (0.7, 0.55)], None),
                   ("poly", [(0.45, 0.6), (0.78, 0.68), (0.72, 0.35), (0.45, 0.6)], "negative")],
    "warning": [("poly", [(0, -0.95), (0.98, 0.8), (-0.98, 0.8), (0, -0.95)], "accent"),
                ("line", [(0, -0.35), (0, 0.25)], None), ("circle", (0, 0.5, 0.07), "ink")],
    "lock": [("rect", (-0.65, -0.1, 1.3, 1.0, 0.1), "accent"),
             ("line", [(-0.4, -0.1), (-0.4, -0.45), (-0.2, -0.75), (0.2, -0.75), (0.4, -0.45), (0.4, -0.1)], None),
             ("circle", (0, 0.35, 0.12), "ink")],
    "document": [("poly", [(-0.65, -0.95), (0.35, -0.95), (0.7, -0.6), (0.7, 0.95), (-0.65, 0.95), (-0.65, -0.95)], "light"),
                 *[("line", [(-0.45, -0.45 + i * 0.3), (0.5, -0.45 + i * 0.3)], None) for i in range(4)]],
    "magnifier": [("circle", (-0.2, -0.2, 0.55), "light"), ("line", [(0.2, 0.2), (0.85, 0.85)], None)],
    "clock": [("circle", (0, 0, 0.9), "light"), ("line", [(0, -0.6), (0, 0), (0.45, 0.2)], None)],
    "rocket": [("poly", [(0, -0.98), (0.35, -0.45), (0.35, 0.45), (-0.35, 0.45), (-0.35, -0.45), (0, -0.98)], "light"),
               ("poly", [(-0.35, 0.1), (-0.7, 0.6), (-0.35, 0.45)], "negative"),
               ("poly", [(0.35, 0.1), (0.7, 0.6), (0.35, 0.45)], "negative"),
               ("circle", (0, -0.25, 0.14), "cool"),
               ("poly", [(-0.2, 0.45), (0, 0.95), (0.2, 0.45)], "accent")],
    "house": [("poly", [(-0.9, -0.05), (0, -0.9), (0.9, -0.05)], None),
              ("rect", (-0.7, -0.05, 1.4, 0.95, 0), "light"), ("rect", (-0.15, 0.4, 0.3, 0.5, 0), "accent")],
    "globe": [("circle", (0, 0, 0.92), "cool"), ("line", ellipse_pts(0, 0, 0.4, 0.92, 24), None),
              ("line", [(-0.92, 0), (0.92, 0)], None), ("line", [(-0.8, -0.45), (0.8, -0.45)], None),
              ("line", [(-0.8, 0.45), (0.8, 0.45)], None)],
    "lightbulb": [("poly", ellipse_pts(0, -0.25, 0.6, 0.62, 28, math.radians(140), math.radians(400)) + [(-0.25, 0.55), (0.25, 0.55)], "accent"),
                  ("rect", (-0.25, 0.55, 0.5, 0.3, 0.05), "muted")],
    "check": [("line", [(-0.8, 0.0), (-0.25, 0.6), (0.85, -0.65)], None)],
    "cross": [("line", [(-0.75, -0.75), (0.75, 0.75)], None), ("line", [(0.75, -0.75), (-0.75, 0.75)], None)],
    "arrow_right": [("line", [(-0.9, 0), (0.85, 0)], None), ("line", [(0.4, -0.45), (0.9, 0), (0.4, 0.45)], None)],
    "handshake": [("line", [(-1, -0.1), (-0.5, -0.3), (0, 0), (0.5, -0.3), (1, -0.1)], None),
                  ("poly", [(-0.5, -0.3), (-0.05, 0.35), (0.25, 0.2), (0.5, -0.3)], "accent")],
    "star": [("poly", _star(), "accent")],
    "flame": [("poly", [(0, -0.95), (0.45, -0.25), (0.6, 0.3), (0.3, 0.85), (-0.3, 0.85), (-0.6, 0.3), (-0.35, -0.2), (-0.15, 0.1), (0, -0.95)], "negative"),
              ("poly", [(0, -0.1), (0.25, 0.35), (0.12, 0.75), (-0.12, 0.75), (-0.25, 0.35), (0, -0.1)], "accent")],
    "briefcase": [("rect", (-0.9, -0.45, 1.8, 1.3, 0.1), "muted"), ("rect", (-0.3, -0.75, 0.6, 0.3, 0.05), None),
                  ("line", [(-0.9, 0.05), (0.9, 0.05)], None)],
    "gavel": [("rect", (-0.85, -0.75, 0.9, 0.42, 0.05), "accent"), ("line", [(-0.4, -0.33), (0.55, 0.62)], None),
              ("rect", (0.05, 0.7, 0.9, 0.2, 0.03), "muted")],
    "cloud": [("poly", ellipse_pts(-0.4, 0.15, 0.45, 0.4, 16, math.pi * 0.5, math.pi * 1.5)
               + ellipse_pts(0.05, -0.15, 0.5, 0.5, 16, math.pi, math.pi * 2)
               + ellipse_pts(0.5, 0.15, 0.4, 0.4, 16, math.pi * 1.5, math.pi * 2.5) + [(-0.4, 0.55)], "light")],
}

ICON_NAMES = sorted(ICONS)


def icon_shapes(name: str, cx: float, cy: float, size: float, theme, *, ink=None, width: float = 4.0,
                fills: bool = True) -> list[Shape]:
    """Instantiate a unit icon at (cx, cy) with half-size `size` px."""
    spec = ICONS.get(name)
    if spec is None:
        spec = [("circle", (0, 0, 0.85), "light"), ("line", [(-0.3, -0.3), (0.3, 0.3)], None)]
    ink = ink or theme.c("ink")
    out: list[Shape] = []
    T = lambda p: (cx + p[0] * size, cy + p[1] * size)  # noqa: E731
    for kind, data, fill_role in spec:
        if kind == "circle":
            x, y, r = data
            pts = [T(p) for p in ellipse_pts(x, y, r, r, 40)]
            closed = True
        elif kind == "rect":
            x, y, w, h, r = data
            pts = [T(p) for p in rect_pts(x, y, w, h, r)]
            closed = True
        elif kind == "poly":
            pts = [T(p) for p in data]
            closed = True
        else:
            pts = [T(p) for p in data]
            closed = False
        fill = theme.c(fill_role) if (fills and fill_role) else None
        out.append(Shape(pts=pts, closed=closed, stroke=ink, width=width, fill=fill))
    return out


# ---------------------------------------------------------------- character
POSES = {
    # angles (radians) for upper/lower arm and legs; 0 = straight down
    "stand": {"la": (0.25, 0.1), "ra": (-0.25, -0.1), "ll": 0.12, "rl": -0.12},
    "point": {"la": (0.25, 0.1), "ra": (-1.9, -1.7), "ll": 0.12, "rl": -0.12},
    "shock": {"la": (2.6, 2.9), "ra": (-2.6, -2.9), "ll": 0.3, "rl": -0.3},
    "think": {"la": (0.3, 2.6), "ra": (-0.25, -0.1), "ll": 0.1, "rl": -0.1},
    "celebrate": {"la": (2.4, 2.6), "ra": (-2.4, -2.6), "ll": 0.2, "rl": -0.2},
    "slump": {"la": (0.05, 0.0), "ra": (-0.05, 0.0), "ll": 0.05, "rl": -0.05},
}


def character_shapes(cx: float, cy: float, h: float, theme, pose: str = "stand", *, t: float = 0.0,
                     talk: bool = False, color_role: str = "cool", width: float = 4.0,
                     blink_seed: int = 0, facing: int = 1, ink=None) -> list[Shape]:
    """Original simple 'analyst' figure. (cx, cy) = feet centre, h = height px."""
    ink = ink or theme.c("ink")
    P = POSES.get(pose, POSES["stand"])
    s = h / 2.0
    head_r = 0.17 * s
    neck = (cx, cy - 1.45 * s)
    hip = (cx, cy - 0.78 * s)
    sway = math.sin(t * 1.6 + blink_seed) * 0.03
    head_c = (cx + sway * s, cy - 1.45 * s - head_r * 1.05)
    shapes: list[Shape] = []
    # body (rounded torso)
    torso = rect_pts(cx - 0.2 * s, neck[1], 0.4 * s, hip[1] - neck[1] + 0.05 * s, 0.12 * s)
    shapes.append(Shape(torso, True, ink, width, theme.c(color_role)))
    # legs
    for ang, side in ((P["ll"], -1), (P["rl"], 1)):
        hx = cx + side * 0.09 * s
        foot = (hx + math.sin(ang) * 0.78 * s, hip[1] + math.cos(ang) * 0.78 * s)
        shapes.append(Shape([(hx, hip[1]), foot, (foot[0] + side * 0.1 * s * facing, foot[1])], False, ink, width))
    # arms (two segments) with a small idle swing
    swing = math.sin(t * 2.2 + blink_seed) * 0.06
    for (a1, a2), side in ((P["la"], -1), (P["ra"], 1)):
        sh = (cx + side * 0.2 * s, neck[1] + 0.08 * s)
        e = (sh[0] + math.sin(a1 + swing) * 0.36 * s * (-side) * -1, sh[1] + math.cos(a1 + swing) * 0.36 * s)
        hnd = (e[0] + math.sin(a2 + swing) * 0.33 * s * (-side) * -1, e[1] + math.cos(a2 + swing) * 0.33 * s)
        shapes.append(Shape([sh, e, hnd], False, ink, width))
    # head
    shapes.append(Shape(ellipse_pts(head_c[0], head_c[1], head_r, head_r * 1.08, 36), True, ink, width,
                        theme.c("light")))
    # eyes (blink ~ every 3.7s)
    blink = (t + blink_seed * 0.37) % 3.7 < 0.12
    for side in (-1, 1):
        ex, ey = head_c[0] + side * head_r * 0.38 + facing * head_r * 0.12, head_c[1] - head_r * 0.1
        if blink:
            shapes.append(Shape([(ex - head_r * 0.12, ey), (ex + head_r * 0.12, ey)], False, ink, width * 0.8))
        else:
            shapes.append(Shape(ellipse_pts(ex, ey, head_r * 0.08, head_r * 0.11, 10), True, ink, width * 0.6, ink))
    # mouth
    my = head_c[1] + head_r * 0.45
    if pose == "shock":
        shapes.append(Shape(ellipse_pts(head_c[0], my, head_r * 0.16, head_r * 0.2, 14), True, ink, width * 0.7, ink))
    elif talk:
        open_ = abs(math.sin(t * 11.0)) * head_r * 0.16 + head_r * 0.03
        shapes.append(Shape(ellipse_pts(head_c[0], my, head_r * 0.2, open_, 14), True, ink, width * 0.7, ink))
    elif pose in ("slump",):
        shapes.append(Shape(ellipse_pts(head_c[0], my + head_r * 0.15, head_r * 0.25, head_r * 0.12, 12,
                                        math.pi * 1.1, math.pi * 1.9), False, ink, width * 0.7))
    else:
        shapes.append(Shape(ellipse_pts(head_c[0], my - head_r * 0.08, head_r * 0.28, head_r * 0.14, 12,
                                        math.pi * 0.15, math.pi * 0.85), False, ink, width * 0.7))
    return shapes


# ---------------------------------------------------------------- textures
_PAPER_CACHE: dict = {}


def paper_texture(size, base, seed: int = 7, grain: float = 10.0) -> Image.Image:
    key = (size, base, seed, grain)
    if key in _PAPER_CACHE:
        return _PAPER_CACHE[key]
    import numpy as np

    rng = np.random.default_rng(seed)
    w, h = size
    small = rng.normal(0, 1, (max(2, h // 8), max(2, w // 8))).astype("float32")
    noise = Image.fromarray(((small - small.min()) / (np.ptp(small) + 1e-6) * 255).astype("uint8")).resize(
        (w, h), Image.BICUBIC)
    fine = rng.normal(0, grain * 0.35, (h, w)).astype("float32")
    n = (np.asarray(noise, dtype="float32") / 255.0 - 0.5) * grain + fine
    arr = np.clip(np.array(base, dtype="float32")[None, None, :] + n[..., None], 0, 255).astype("uint8")
    img = Image.fromarray(arr, "RGB")
    _PAPER_CACHE[key] = img
    return img


def vignette(size, strength: float = 0.35) -> Image.Image:
    """L-mode multiplier mask (255 centre -> darker edges)."""
    key = ("vig", size, strength)
    if key in _PAPER_CACHE:
        return _PAPER_CACHE[key]
    w, h = size
    small = Image.radial_gradient("L").resize((w, h), Image.BILINEAR)  # 0 centre .. 255 edge
    m = small.point(lambda v: int(255 - strength * 255 * (v / 255) ** 2))
    _PAPER_CACHE[key] = m
    return m


def soft_glow(img: Image.Image, radius: float) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(radius))
