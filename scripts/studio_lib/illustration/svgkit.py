"""Tiny SVG authoring kit for code-drawn line art (no external images).

Drawing rules that suit the sweety_draw engine (sweety-handdraw-video planner):
- outlines are dark (max RGB channel < 125) and 2-6 px wide -> traced as pen strokes;
- fills are muted, max channel >= 125, and never "cool ink" (blue-ish with red < 218),
  otherwise they would be traced as ink instead of painted;
- the background is transparent (bg="none"), so the art sits on the scene's own paper.
"""
from __future__ import annotations

import math

INK = "#26221e"
INK2 = "#3a332c"

# palette (all paintable: max channel >= 125, not cool)
OD = "#a8ab73"        # olive drab (rubber decoy / vehicles)
OD2 = "#8f9460"       # olive shade
JACKET = "#a7a873"
TROUSER = "#9d9a68"
SKIN = "#ecc9a5"
BOOT = "#6a5848"
HELMET = "#8f9462"
STEEL = "#bdb6a4"
RUBBER = "#9b9384"
SHADOW = "#e4ddcc"
TREE = "#dde0c6"
WOOD = "#c9a47c"
WOOD2 = "#b58e66"
PAPER = "#f6f0dc"


class Svg:
    def __init__(self, w, h, bg="none", oy=0, ox=0):
        self.w, self.h, self.bg, self.oy, self.ox = w, h, bg, oy, ox
        self.defs: list[str] = []
        self.body: list[str] = []
        self._id = 0

    def uid(self, p="c"):
        self._id += 1
        return f"{p}{self._id}"

    def add(self, s):
        self.body.append(s)

    def group(self, transform):
        self.add(f'<g transform="{transform}">')

    def end(self):
        self.add("</g>")

    def path(self, d, fill="none", stroke=INK, sw=4, extra=""):
        self.add(f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" '
                 f'stroke-linecap="round" stroke-linejoin="round" {extra}/>')

    def circle(self, cx, cy, r, fill="none", stroke=INK, sw=4, extra=""):
        self.add(f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def ellipse(self, cx, cy, rx, ry, fill="none", stroke=INK, sw=4, extra=""):
        self.add(f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{rx:.1f}" ry="{ry:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}" {extra}/>')

    def line(self, x1, y1, x2, y2, stroke=INK, sw=3, extra=""):
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" '
                 f'stroke-width="{sw}" stroke-linecap="round" {extra}/>')

    def hatch(self, clip_d, angle=45, spacing=9, sw=2, stroke=INK2, box=None, extra=""):
        """Parallel hatch lines clipped to clip_d (box = x0, y0, x1, y1 to bound the line set)."""
        cid = self.uid("h")
        self.defs.append(f'<clipPath id="{cid}"><path d="{clip_d}"/></clipPath>')
        x0, y0, x1, y1 = box or (0, 0, self.w, self.h)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        R = math.hypot(x1 - x0, y1 - y0) / 2 + 4
        a = math.radians(angle)
        dx, dy = math.cos(a), math.sin(a)
        nx, ny = -dy, dx
        out = []
        k = -R
        while k <= R:
            px, py = cx + nx * k, cy + ny * k
            out.append(f'M{px - dx * R:.1f},{py - dy * R:.1f} L{px + dx * R:.1f},{py + dy * R:.1f}')
            k += spacing
        self.add(f'<g clip-path="url(#{cid})"><path d="{" ".join(out)}" stroke="{stroke}" stroke-width="{sw}" '
                 f'fill="none" stroke-linecap="round" {extra}/></g>')

    def tube(self, pts, width, fill, ink=INK, lw=4):
        """Outlined limb: dark wide stroke with a fill-coloured stroke on top."""
        d = smooth(pts)
        self.add(f'<path d="{d}" fill="none" stroke="{ink}" stroke-width="{width + 2 * lw:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')
        self.add(f'<path d="{d}" fill="none" stroke="{fill}" stroke-width="{width:.1f}" stroke-linecap="round" stroke-linejoin="round"/>')

    def svg(self) -> str:
        bg = "" if self.bg in (None, "none") else f'<rect width="100%" height="100%" fill="{self.bg}"/>'
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" viewBox="0 0 {self.w} {self.h}">'
                f'<defs>{"".join(self.defs)}</defs>{bg}'
                f'<g transform="translate({-self.ox},{-self.oy})">' + "".join(self.body) + "</g></svg>")

    def norm_box(self, x0, y0, x1, y1):
        """Pixel box in drawing coords -> normalized polygon in output coords (clamped)."""
        f = lambda x, y: [round(min(1, max(0, (x - self.ox) / self.w)), 4), round(min(1, max(0, (y - self.oy) / self.h)), 4)]
        return [f(x0, y0), f(x1, y0), f(x1, y1), f(x0, y1)]

    def norm_poly(self, pts):
        return [[round(min(1, max(0, (x - self.ox) / self.w)), 4), round(min(1, max(0, (y - self.oy) / self.h)), 4)]
                for x, y in pts]


def smooth(pts):
    """Polyline -> quadratic-smoothed path through midpoints."""
    if len(pts) == 2:
        (a, b), (c, d) = pts
        return f"M{a:.1f},{b:.1f} L{c:.1f},{d:.1f}"
    d = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts) - 1):
        mx = (pts[i][0] + pts[i + 1][0]) / 2
        my = (pts[i][1] + pts[i + 1][1]) / 2
        if i == len(pts) - 2:
            mx, my = pts[i + 1]
        d += f" Q{pts[i][0]:.1f},{pts[i][1]:.1f} {mx:.1f},{my:.1f}"
    return d


def lerp(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy) or 1.0
    return dx / n, dy / n


# ----------------------------------------------------------------- figures
def helmet(s: Svg, cx, cy, r, facing=1, fill=HELMET):
    """M1 helmet side view over a head centred (cx, cy), radius r, with liner rim and chin strap."""
    f = facing
    brim_y = cy - r * 0.22
    d = (f"M{cx - f * r * 1.30:.1f},{brim_y + r * 0.14:.1f} "
         f"C{cx - f * r * 1.22:.1f},{cy - r * 1.62:.1f} {cx + f * r * 1.12:.1f},{cy - r * 1.66:.1f} {cx + f * r * 1.22:.1f},{brim_y:.1f} "
         f"L{cx + f * r * 1.40:.1f},{brim_y + r * 0.12:.1f} "
         f"L{cx - f * r * 1.46:.1f},{brim_y + r * 0.26:.1f} Z")
    s.path(d, fill=fill, sw=3.6)
    s.path(f"M{cx - f * r * 1.30:.1f},{brim_y + r * 0.08:.1f} Q{cx:.1f},{brim_y - r * 0.14:.1f} {cx + f * r * 1.25:.1f},{brim_y - r * 0.04:.1f}",
           sw=2.2)
    # chin strap: two straps from the rim at the ear, meeting under the jaw
    ex, ey = cx - f * r * 0.15, brim_y + r * 0.22
    jx, jy = cx + f * r * 0.42, cy + r * 0.92
    s.path(f"M{ex:.1f},{ey:.1f} Q{ex + f * r * 0.05:.1f},{cy + r * 0.55:.1f} {jx:.1f},{jy:.1f}", sw=2.0)
    s.path(f"M{ex - f * r * 0.22:.1f},{ey + r * 0.02:.1f} Q{ex - f * r * 0.12:.1f},{cy + r * 0.62:.1f} {jx - f * r * 0.12:.1f},{jy + r * 0.04:.1f}", sw=2.0)


def head(s: Svg, cx, cy, r, facing=1, cap="helmet", skin=SKIN, hair="#6b5440"):
    f = facing
    d = (f"M{cx - f * r * 0.85:.1f},{cy + r * 0.35:.1f} "
         f"C{cx - f * r * 1.1:.1f},{cy - r * 0.9:.1f} {cx + f * r * 0.6:.1f},{cy - r * 1.25:.1f} {cx + f * r * 0.95:.1f},{cy - r * 0.2:.1f} "
         f"L{cx + f * r * 1.18:.1f},{cy + r * 0.2:.1f} L{cx + f * r * 0.98:.1f},{cy + r * 0.3:.1f} "
         f"Q{cx + f * r * 1.02:.1f},{cy + r * 0.62:.1f} {cx + f * r * 0.86:.1f},{cy + r * 0.8:.1f} "
         f"Q{cx + f * r * 0.5:.1f},{cy + r * 1.1:.1f} {cx + f * r * 0.05:.1f},{cy + r * 0.98:.1f} "
         f"Q{cx - f * r * 0.55:.1f},{cy + r * 0.92:.1f} {cx - f * r * 0.85:.1f},{cy + r * 0.35:.1f} Z")
    s.path(d, fill=skin, sw=3.2)
    s.path(f"M{cx - f * r * 0.12:.1f},{cy + r * 0.02:.1f} q{-f * r * 0.24:.1f},{r * 0.05:.1f} {-f * r * 0.12:.1f},{r * 0.4:.1f}", sw=2.2)
    s.circle(cx + f * r * 0.6, cy - r * 0.06, max(1.6, r * 0.075), fill=INK, sw=1.2)
    s.path(f"M{cx + f * r * 0.42:.1f},{cy - r * 0.3:.1f} l{f * r * 0.3:.1f},{-r * 0.04:.1f}", sw=1.8)  # brow
    if cap == "helmet":
        helmet(s, cx, cy, r, f)
    elif cap == "hair":
        s.path(f"M{cx - f * r * 0.92:.1f},{cy + r * 0.2:.1f} C{cx - f * r * 1.05:.1f},{cy - r * 1.0:.1f} "
               f"{cx + f * r * 0.55:.1f},{cy - r * 1.3:.1f} {cx + f * r * 0.92:.1f},{cy - r * 0.38:.1f} "
               f"Q{cx + f * r * 0.3:.1f},{cy - r * 0.55:.1f} {cx - f * r * 0.1:.1f},{cy - r * 0.35:.1f} "
               f"Q{cx - f * r * 0.45:.1f},{cy - r * 0.1:.1f} {cx - f * r * 0.92:.1f},{cy + r * 0.2:.1f} Z",
               fill=hair, sw=2.8)
    elif cap == "beret":
        s.path(f"M{cx - f * r * 1.05:.1f},{cy - r * 0.25:.1f} Q{cx - f * r * 0.9:.1f},{cy - r * 1.35:.1f} {cx + f * r * 0.35:.1f},{cy - r * 1.22:.1f} "
               f"Q{cx + f * r * 1.15:.1f},{cy - r * 1.05:.1f} {cx + f * r * 0.85:.1f},{cy - r * 0.5:.1f} "
               f"Q{cx:.1f},{cy - r * 0.62:.1f} {cx - f * r * 1.05:.1f},{cy - r * 0.25:.1f} Z", fill="#7d6a58", sw=3)
        s.line(cx + f * r * 0.05, cy - r * 1.26, cx + f * r * 0.1, cy - r * 1.46, sw=2.4)
    elif cap == "cap":
        s.path(f"M{cx - f * r * 0.95:.1f},{cy - r * 0.3:.1f} Q{cx - f * r * 0.7:.1f},{cy - r * 1.25:.1f} {cx + f * r * 0.5:.1f},{cy - r * 1.1:.1f} "
               f"L{cx + f * r * 0.9:.1f},{cy - r * 0.55:.1f} L{cx + f * r * 1.45:.1f},{cy - r * 0.45:.1f} "
               f"L{cx + f * r * 0.85:.1f},{cy - r * 0.35:.1f} Q{cx:.1f},{cy - r * 0.5:.1f} {cx - f * r * 0.95:.1f},{cy - r * 0.3:.1f} Z",
               fill="#b9a98a", sw=3)


def boot(s: Svg, ankle, facing=1, size=1.0, fill=BOOT):
    x, y = ankle
    f, k = facing, size
    d = (f"M{x - f * 12 * k:.1f},{y - 18 * k:.1f} L{x + f * 11 * k:.1f},{y - 18 * k:.1f} "
         f"Q{x + f * 14 * k:.1f},{y - 4 * k:.1f} {x + f * 31 * k:.1f},{y + 2 * k:.1f} "
         f"Q{x + f * 39 * k:.1f},{y + 6 * k:.1f} {x + f * 37 * k:.1f},{y + 12 * k:.1f} "
         f"L{x - f * 15 * k:.1f},{y + 12 * k:.1f} Z")
    s.path(d, fill=fill, sw=3.2)
    s.line(x - f * 13 * k, y + 6 * k, x + f * 35 * k, y + 6 * k, sw=1.8)
    s.line(x - f * 12 * k, y - 10 * k, x + f * 11 * k, y - 10 * k, sw=1.8)   # legging top


def _limb(s: Svg, a, b, c, width, fill, fold=True, cuff=None):
    s.tube([a, b, c], width, fill)
    if fold:  # two short fold arcs on the inside of the joint
        ux, uy = _unit(a, b)
        vx, vy = _unit(b, c)
        bx, by = b
        nx, ny = -(ux + vx), -(uy + vy)
        n = math.hypot(nx, ny) or 1
        nx, ny = nx / n, ny / n
        for k in (0.18, 0.36):
            px, py = bx + nx * width * k, by + ny * width * k
            s.path(f"M{px - vx * width * 0.35:.1f},{py - vy * width * 0.35:.1f} Q{px + nx * 3:.1f},{py + ny * 3:.1f} "
                   f"{px + ux * width * 0.35:.1f},{py + uy * width * 0.35:.1f}", sw=1.7)
    if cuff is not None:
        cx, cy = lerp(b, c, cuff)
        px, py = -_unit(b, c)[1], _unit(b, c)[0]
        h = width / 2 + 1
        s.line(cx + px * h, cy + py * h, cx - px * h, cy - py * h, sw=2)


def hand(s: Svg, p, r=10, skin=SKIN):
    s.circle(p[0], p[1], r, fill=skin, sw=3)


def figure(s: Svg, J: dict, facing=1, k=1.0, jacket=JACKET, trouser=TROUSER, cap="helmet", skin=SKIN,
           canteen=True, boots=BOOT, belt=True):
    """Side-view figure from joints: head, neck, hip, b/f shoulder elbow hand, b/f knee ankle
    (b = far side, drawn first; f = near side). Proportions ~7.5 heads for a standing pose."""
    T, A, L = 60 * k, 24 * k, 33 * k
    # far limbs
    _limb(s, J["hip"], J["bknee"], J["bankle"], L, trouser)
    boot(s, J["bankle"], facing, k, boots)
    _limb(s, J["bshoulder"], J["belbow"], J["bhand"], A, jacket, cuff=0.82)
    hand(s, J["bhand"], 9.5 * k, skin)
    # torso
    nx, ny = J["neck"]
    hx, hy = J["hip"]
    ang = math.atan2(hy - ny, hx - nx)
    px, py = -math.sin(ang), math.cos(ang)
    w1, w2 = T * 0.55, T * 0.47
    d = (f"M{nx + px * w1:.1f},{ny + py * w1:.1f} L{nx - px * w1:.1f},{ny - py * w1:.1f} "
         f"Q{(nx + hx) / 2 - px * (w1 + 5 * k):.1f},{(ny + hy) / 2 - py * (w1 + 5 * k):.1f} {hx - px * w2:.1f},{hy - py * w2:.1f} "
         f"L{hx + px * w2:.1f},{hy + py * w2:.1f} "
         f"Q{(nx + hx) / 2 + px * (w1 + 5 * k):.1f},{(ny + hy) / 2 + py * (w1 + 5 * k):.1f} {nx + px * w1:.1f},{ny + py * w1:.1f} Z")
    s.path(d, fill=jacket, sw=3.6)
    # collar
    s.path(f"M{nx - px * w1 * 0.6:.1f},{ny - py * w1 * 0.6:.1f} L{nx + facing * 4 * k:.1f},{ny + 14 * k:.1f} "
           f"L{nx + px * w1 * 0.6:.1f},{ny + py * w1 * 0.6:.1f}", sw=2)
    # chest pocket flap + button line
    mx, my = lerp(J["neck"], J["hip"], 0.3)
    s.path(f"M{mx:.1f},{my:.1f} l{facing * 15 * k:.1f},{1 * k:.1f} l{-facing * 2 * k:.1f},{7 * k:.1f} l{-facing * 12 * k:.1f},{-1 * k:.1f}", sw=1.8)
    # belt + buckle
    bx, by = lerp(J["neck"], J["hip"], 0.84)
    if belt:
        s.path(f"M{bx + px * w2 * 1.04:.1f},{by + py * w2 * 1.04:.1f} L{bx - px * w2 * 1.04:.1f},{by - py * w2 * 1.04:.1f}",
               stroke=INK, sw=6.5 * k)
    if canteen:
        cx, cy = lerp(J["neck"], J["hip"], 0.92)
        s.ellipse(cx - facing * w2 * 0.85, cy + 6 * k, 9 * k, 12 * k, fill=OD2, sw=2.4)
    # back fold of the jacket
    fx, fy = lerp(J["neck"], J["hip"], 0.62)
    s.path(f"M{fx - facing * w1 * 0.5:.1f},{fy:.1f} q{facing * 8 * k:.1f},{6 * k:.1f} {facing * 4 * k:.1f},{16 * k:.1f}", sw=1.7)
    # near leg
    _limb(s, J["hip"], J["fknee"], J["fankle"], L, trouser)
    s.path(smooth([lerp(J["hip"], J["fknee"], .4), lerp(J["fknee"], J["fankle"], .05)]), sw=1.7)
    boot(s, J["fankle"], facing, k, boots)
    head(s, *J["head"], 20 * k, facing, cap=cap, skin=skin)
    _limb(s, J["fshoulder"], J["felbow"], J["fhand"], A, jacket, cuff=0.82)
    hand(s, J["fhand"], 9.5 * k, skin)


def place(J: dict, ox=0.0, oy=0.0, k=1.0, flip=False):
    """Translate / scale / mirror a joint set defined around (0, 0) at the feet."""
    return {n: (ox + (-x if flip else x) * k, oy + y * k) for n, (x, y) in J.items()}


# Reusable poses (feet at y=0, facing +x). Height ~ 285 px at k=1.
STAND_PUMP = dict(head=(30, -262), neck=(22, -232), hip=(-12, -140),
                  bshoulder=(18, -220), belbow=(56, -190), bhand=(76, -160),
                  fshoulder=(24, -216), felbow=(62, -184), fhand=(104, -162),
                  bknee=(-28, -70), bankle=(-58, -14), fknee=(14, -72), fankle=(4, -14))
HAUL = dict(head=(-24, -262), neck=(-26, -230), hip=(4, -140),
            bshoulder=(-30, -218), belbow=(-68, -184), bhand=(-96, -168),
            fshoulder=(-24, -214), felbow=(-60, -176), fhand=(-86, -158),
            bknee=(-26, -70), bankle=(-58, -14), fknee=(26, -70), fankle=(22, -14))
LIFT = dict(head=(16, -258), neck=(6, -228), hip=(-4, -140),
            bshoulder=(10, -220), belbow=(34, -262), bhand=(28, -300),
            fshoulder=(-2, -214), felbow=(-10, -258), fhand=(-4, -298),
            bknee=(-20, -70), bankle=(-42, -14), fknee=(20, -72), fankle=(30, -14))
WALK_CARRY = dict(head=(10, -262), neck=(6, -232), hip=(0, -140),
                  bshoulder=(2, -220), belbow=(-12, -178), bhand=(2, -140),
                  fshoulder=(10, -216), felbow=(34, -238), fhand=(26, -270),
                  bknee=(-22, -70), bankle=(-46, -14), fknee=(28, -72), fankle=(40, -14))
SEATED_KEY = dict(head=(78, -354), neck=(56, -314), hip=(0, -140),
                  bshoulder=(60, -302), belbow=(104, -270), bhand=(86, -334),
                  fshoulder=(50, -296), felbow=(116, -224), fhand=(206, -256),
                  bknee=(160, -126), bankle=(170, -16), fknee=(148, -120), fankle=(142, -14))
