"""Code-drawn Ghost Army illustrations (no external images) for the sweety_draw engine.

Each scene function returns (svg_text, parts, info):
  parts: ordered [{"name", "polygon"}] in normalized output coords (drawing order for sweety_draw)
  info:  {"width", "height"}
Content follows the project brief only (inflatable decoys, the lifted "tank" seen by French
cyclists, sound trucks with vehicle-mounted speakers and wire recorders, spoof radio).
"""
from __future__ import annotations

import math
import random

from .svgkit import (BOOT, INK, INK2, JACKET, TROUSER, OD, OD2, PAPER, RUBBER, SHADOW, SKIN, STEEL, TREE, WOOD, WOOD2,
                     HAUL, LIFT, SEATED_KEY, STAND_PUMP, WALK_CARRY, Svg, figure, head, place)

WHEEL = "#b9b29f"
TRACK_IN = "#c9c2b0"
TIRE = "#8e877a"
PANEL = "#9fa287"
PANEL2 = "#8b8f74"
WALL = "#efe7d3"

HAUL_BACK = dict(head=(30, -262), neck=(26, -230), hip=(0, -140),
                 bshoulder=(24, -218), belbow=(-14, -190), bhand=(-46, -172),
                 fshoulder=(30, -214), felbow=(-8, -182), fhand=(-38, -162),
                 bknee=(28, -70), bankle=(38, -14), fknee=(-26, -72), fankle=(-50, -14))


def _treeline(s: Svg, x0, x1, base, top, seed=7):
    rnd = random.Random(seed)
    pts, x = [], x0
    while x < x1:
        pts.append((x, top + rnd.randint(0, 60)))
        x += rnd.randint(40, 75)
    pts.append((x1, top + 30))
    d = f"M{x0},{base} L{x0},{pts[0][1]} "
    for (a, b), (c, e) in zip(pts, pts[1:]):
        d += f"Q{(a + c) / 2:.0f},{min(b, e) - 38:.0f} {c:.0f},{e:.0f} "
    d += f"L{x1},{base} Z"
    s.path(d, fill=TREE, stroke="#4b4a3c", sw=2.6)
    s.hatch(d, angle=70, spacing=13, sw=1.8, stroke="#55543f", box=(x0, top - 50, x1, base + 4))


def _grass(s: Svg, x0, x1, y, step=70, seed=3):
    rnd = random.Random(seed)
    for gx in range(int(x0), int(x1), step):
        gy = y + rnd.randint(0, 50)
        a, b = rnd.randint(4, 8), rnd.randint(14, 20)
        s.path(f"M{gx},{gy} l{a},-{b} M{gx + 8},{gy} l2,-{b + 4} M{gx + 14},{gy} l-4,-{b - 4}", sw=2.2, stroke=INK2)


def draw_tank(s: Svg):
    """Inflatable M4-type medium tank decoy, side view facing right; tank coords x 376..1440, y 184..642."""
    trk = ("M505,642 L1215,642 Q1338,642 1350,560 Q1356,470 1282,455 L520,468 "
           "Q392,474 386,545 Q384,606 505,642 Z")
    s.path(trk, fill=RUBBER, sw=4.5)
    s.path("M520,620 L1210,620 Q1318,620 1324,556 Q1326,488 1278,478 L528,490 "
           "Q414,494 410,548 Q410,600 520,620 Z", fill=TRACK_IN, sw=3)
    for tx in range(530, 1215, 34):
        s.line(tx, 622, tx - 4, 640, sw=2.2)
    for tx in range(560, 1270, 36):
        s.line(tx, 459 - (tx - 520) * 0.0185, tx + 3, 477 - (tx - 520) * 0.0185, sw=2.2)
    for bx in (600, 840, 1080):
        s.path(f"M{bx - 70},585 L{bx - 30},528 L{bx + 34},528 L{bx + 70},585 Z", fill=OD2, sw=3.5)
        s.circle(bx + 10, 512, 15, fill=WHEEL, sw=3.2)
        s.circle(bx + 10, 512, 5, fill=INK, sw=1)
        for wx in (bx - 56, bx + 56):
            s.circle(wx, 596, 42, fill=WHEEL, sw=4)
            s.circle(wx, 596, 30, fill="none", sw=2.4)
            s.circle(wx, 596, 11, fill=OD2, sw=2.6)
            s.path(f"M{wx - 30},596 A30,30 0 0 0 {wx},626", sw=6, stroke="#857e70")
        s.path(f"M{bx - 30},545 q30,-10 64,0", sw=2.4)
    s.circle(1286, 530, 54, fill=WHEEL, sw=4)
    s.circle(1286, 530, 40, fill="none", sw=2.5)
    for i in range(10):
        a = i * math.pi / 5
        s.line(1286 + 40 * math.cos(a), 530 + 40 * math.sin(a), 1286 + 52 * math.cos(a), 530 + 52 * math.sin(a), sw=3)
    s.circle(1286, 530, 15, fill=OD2, sw=3)
    s.circle(452, 548, 46, fill=WHEEL, sw=4)
    s.circle(452, 548, 30, fill="none", sw=2.5)
    s.circle(452, 548, 12, fill=OD2, sw=3)
    hull = ("M414,338 Q406,330 420,322 L1046,316 Q1062,302 1092,304 L1108,318 "
            "L1300,410 Q1336,428 1330,458 Q1320,486 1286,478 L1010,468 L520,474 "
            "Q408,476 400,456 L396,352 Q398,340 414,338 Z")
    s.path(hull, fill=OD, sw=4.5)
    band = "M404,430 L1286,436 Q1318,444 1318,458 Q1312,478 1286,478 L520,474 Q408,476 400,456 Z"
    s.path(band, fill=OD2, sw=3)
    s.hatch(band, angle=-35, spacing=10, sw=2, box=(396, 426, 1330, 482))
    s.path("M1108,318 L1112,350 L1290,430", sw=3)
    s.path("M1050,316 Q1060,296 1092,298 Q1110,300 1112,318", fill=OD, sw=3.5)
    s.path("M1120,330 q24,-14 52,4 l-6,14 q-20,-10 -40,0 z", fill=OD2, sw=3)
    s.path("M420,372 L1060,366", sw=2.6, extra='stroke-dasharray="16 10"')       # inflation seams
    s.path("M430,404 L1250,404", sw=2.6, extra='stroke-dasharray="16 10"')
    s.path("M700,324 L702,430", sw=2.6, extra='stroke-dasharray="14 10"')
    s.path("M960,320 L962,432", sw=2.6, extra='stroke-dasharray="14 10"')
    for wx, wy in ((560, 340), (840, 338), (1010, 386), (500, 420), (1180, 392)):   # fabric puckers
        s.path(f"M{wx},{wy} q12,8 26,2", sw=2.2)
        s.path(f"M{wx + 4},{wy + 10} q10,6 20,1", sw=2)
    for gx in range(440, 620, 22):
        s.line(gx, 328, gx + 2, 340, sw=2.4)
    s.path("M398,392 l-22,0 l0,26 l22,0", fill=TRACK_IN, sw=3.5)                  # inflation valve
    s.path("M376,398 l-10,0 l0,14 l10,0", fill="#857e70", sw=3)
    for rx, ry in ((470, 452), (1240, 448)):
        s.circle(rx, ry, 8, fill="none", sw=3)
    turret = ("M640,326 Q622,300 652,278 Q690,226 778,214 L928,210 Q1004,214 1036,256 "
              "Q1052,282 1048,326 Z")
    s.path(turret, fill=OD, sw=4.5)
    s.hatch("M640,326 Q622,300 652,278 L1048,300 Q1052,312 1048,326 Z", angle=-30, spacing=10, sw=2,
            box=(620, 270, 1060, 330))
    s.path("M652,278 Q760,300 1046,296", sw=2.6)
    s.path("M742,214 Q744,186 784,184 Q824,186 826,212", fill=OD2, sw=3.5)
    s.line(752, 196, 818, 196, sw=2.2)
    s.path("M870,212 l4,-16 l34,0 l4,16", fill=OD2, sw=3)
    s.path("M1036,252 Q1084,246 1090,270 L1090,300 Q1084,318 1040,316 Z", fill=OD2, sw=4)
    s.line(1052, 256, 1056, 312, sw=2.2)
    s.path("M1088,268 Q1260,272 1420,286 L1422,306 Q1260,296 1088,294 Z", fill=OD, sw=4)   # soft, sagging gun
    s.path("M1420,282 q14,0 14,14 q0,14 -14,14 z", fill=OD2, sw=3.5)
    for gx in (1120, 1150, 1185):
        s.path(f"M{gx},270 q6,12 0,24", sw=2.2)
    s.path("M1100,296 Q1260,300 1418,306", sw=2, stroke=INK2)
    s.hatch("M1088,284 Q1260,272 1420,286 L1422,306 Q1260,296 1088,294 Z", angle=-20, spacing=9, sw=1.8,
            box=(1088, 280, 1425, 310))


# ----------------------------------------------------------------- g13
def g13():
    """Inflatable tank decoy being pumped up and staked down."""
    s = Svg(1600, 620, oy=140)
    _treeline(s, 0, 1600, 612, 500)
    s.path("M0,613 Q400,606 800,612 T1600,610", sw=3)
    s.ellipse(880, 646, 560, 26, fill=SHADOW, stroke="none")
    s.path("M0,660 Q300,652 600,664 T1600,658", sw=2.4, stroke=INK2)
    _grass(s, 30, 1600, 690)
    draw_tank(s)
    s.path("M470,452 Q430,520 330,630", sw=2.6)                       # tethers + stakes
    s.path("M1240,448 Q1330,470 1418,626", sw=2.6)
    for sx, sy in ((330, 630), (1418, 626)):
        s.path(f"M{sx - 5},{sy - 14} l10,0 l-5,26 z", fill=WOOD, sw=2.6)
    s.path("M366,405 C320,410 330,520 300,560 S260,640 320,640", sw=7)     # hose to the pump
    s.path("M366,405 C320,410 330,520 300,560 S260,640 320,640", sw=3, stroke="#857e70")
    s.path("M318,640 l44,0 l-6,-12 l-32,0 z", fill="#857e70", sw=3)
    s.path("M326,628 L326,520 Q340,512 354,520 L354,628 Z", fill=TRACK_IN, sw=3.5)
    s.line(340, 520, 340, 478, sw=4)
    s.line(312, 476, 368, 476, sw=6)
    figure(s, place(STAND_PUMP, 236, 640), facing=1)
    s.path("M1300,430 Q1380,452 1446,468 Q1474,478 1490,500", sw=3)
    figure(s, place(HAUL_BACK, 1530, 640), facing=-1)
    bx, by = 30, 492                                                     # distant soldier with bundle
    s.path(f"M{bx - 10},{by + 8} Q{bx},{by - 22} {bx + 46},{by - 18} Q{bx + 74},{by - 12} {bx + 72},{by + 10} "
           f"Q{bx + 66},{by + 30} {bx + 30},{by + 30} Q{bx - 12},{by + 30} {bx - 10},{by + 8} Z", fill=OD, sw=3)
    s.path(f"M{bx - 2},{by + 2} q30,-16 64,-4 M{bx},{by + 16} q30,-12 64,-2", sw=2)
    figure(s, place(WALK_CARRY, 80, 618, k=0.55), facing=1, k=0.55)
    parts = [("tracks_wheels", (376, 452, 1360, 650)), ("hull", (360, 296, 1345, 486)),
             ("turret_gun", (610, 176, 1440, 330)), ("pump_soldier", (140, 330, 410, 652)),
             ("rope_soldier", (1300, 330, 1600, 652)), ("distant_soldier", (0, 420, 130, 630))]
    return s.svg(), [{"name": n, "polygon": s.norm_box(*b)} for n, b in parts], {"width": s.w, "height": s.h}


# ----------------------------------------------------------------- g14
def _bicycle(s: Svg, front, rear, r, color=INK):
    fx, fy = front
    rx, ry = rear
    for cx, cy in (front, rear):
        s.circle(cx, cy, r, fill="none", sw=4)
        s.circle(cx, cy, r - 6, fill="none", sw=1.6)
        for i in range(12):
            a = i * math.pi / 6
            s.line(cx, cy, cx + (r - 6) * math.cos(a), cy + (r - 6) * math.sin(a), sw=1.2, stroke=INK2)
        s.circle(cx, cy, 4, fill=INK, sw=1)
    bb = (rx - (rx - fx) * 0.42, ry - r * 0.05)                 # bottom bracket
    seat = (rx - (rx - fx) * 0.18, ry - r * 1.45)
    head_t = (fx + (rx - fx) * 0.1, fy - r * 1.4)
    s.path(f"M{rx},{ry} L{bb[0]:.0f},{bb[1]:.0f} L{seat[0]:.0f},{seat[1]:.0f} Z", sw=4, stroke=color)
    s.path(f"M{bb[0]:.0f},{bb[1]:.0f} L{head_t[0]:.0f},{head_t[1]:.0f} L{seat[0]:.0f},{seat[1]:.0f}", sw=4, stroke=color)
    s.path(f"M{head_t[0]:.0f},{head_t[1]:.0f} L{fx},{fy}", sw=4, stroke=color)
    s.path(f"M{head_t[0]:.0f},{head_t[1]:.0f} l{-6 if rx > fx else 6},-22 l{-18 if rx > fx else 18},2", sw=4)  # bars
    s.path(f"M{seat[0] - 16:.0f},{seat[1] - 8:.0f} l30,0 l-4,6 l-22,0 z", fill="#6a5848", sw=2.6)          # saddle
    s.circle(bb[0], bb[1], 9, fill="none", sw=2.6)
    s.line(bb[0] - 14, bb[1] + 12, bb[0] + 14, bb[1] - 12, sw=3)                                         # crank
    return {"seat": seat, "bars": (head_t[0] + (-24 if rx > fx else 24), head_t[1] - 20), "bb": bb}


def g14():
    """Four soldiers carry an inflatable 'tank' overhead while two French cyclists watch."""
    s = Svg(1600, 700, oy=40)
    G = 700
    _treeline(s, 980, 1600, G - 60, G - 200, seed=11)
    s.path(f"M0,{G} Q400,{G - 6} 800,{G} T1600,{G - 2}", sw=3)
    s.path(f"M960,{G - 58} L1600,{G - 62}", sw=2.4, stroke=INK2)                       # road edge
    s.ellipse(520, G + 4, 400, 14, fill=SHADOW, stroke="none")
    _grass(s, 20, 1000, G + 10, step=80, seed=5)
    k = 0.78
    s.group(f"translate({100 - 376 * k:.1f},{420 - 642 * k:.1f}) scale({k})")
    draw_tank(s)
    s.end()
    lifters = [(220, 0), (400, 1), (580, 2), (760, 3)]
    for x, i in lifters:
        J = place(LIFT, x, G, k=0.92)
        if i % 2:                       # vary heads/arms a little so they are not clones
            J["head"] = (J["head"][0] + 4, J["head"][1] + 3)
            J["fhand"] = (J["fhand"][0] - 6, J["fhand"][1])
        figure(s, J, facing=1, k=0.92)
    # bicycle 2 (further, smaller) with a seated rider
    b2 = _bicycle(s, (1390, 640), (1540, 640), 46)
    J2 = {"head": (1452, 450), "neck": (1466, 478), "hip": (b2["seat"][0] + 2, b2["seat"][1] - 8),
          "bshoulder": (1462, 490), "belbow": (1424, 522), "bhand": b2["bars"],
          "fshoulder": (1468, 494), "felbow": (1430, 530), "fhand": (b2["bars"][0] + 6, b2["bars"][1] + 4),
          "bknee": (1478, 590), "bankle": (b2["bb"][0] - 6, b2["bb"][1] + 12),
          "fknee": (1492, 612), "fankle": (1480, G - 14)}
    figure(s, J2, facing=-1, k=0.82, jacket="#c4a88a", trouser="#a89a86", cap="cap", canteen=False, belt=False,
           boots="#5e5046")
    # bicycle 1 with a rider standing astride, watching
    b1 = _bicycle(s, (1120, 636), (1300, 636), 56)
    J1 = place(dict(head=(-16, -262), neck=(-10, -232), hip=(0, -140),
                    bshoulder=(-8, -220), belbow=(-50, -190), bhand=(-86, -162),
                    fshoulder=(-4, -216), felbow=(-46, -184), fhand=(-80, -150),
                    bknee=(-12, -70), bankle=(-24, -14), fknee=(14, -70), fankle=(26, -14)), 1182, G, k=0.92)
    J1["bhand"], J1["fhand"] = b1["bars"], (b1["bars"][0] + 8, b1["bars"][1] + 6)
    figure(s, J1, facing=-1, k=0.92, jacket="#b9a98a", trouser="#9f927e", cap="beret", canteen=False, belt=False,
           boots="#5e5046")
    parts = [("tank", (100, 40, 960, 430)), ("lifter_1", (150, 380, 300, 720)), ("lifter_2", (300, 380, 480, 720)),
             ("lifter_3", (480, 380, 660, 720)), ("lifter_4", (660, 380, 860, 720)),
             ("cyclist_front", (1040, 400, 1330, 720)), ("cyclist_back", (1330, 400, 1600, 720))]
    return s.svg(), [{"name": n, "polygon": s.norm_box(*b)} for n, b in parts], {"width": s.w, "height": s.h}


# ----------------------------------------------------------------- g15
def _wheel_tire(s, cx, cy, r):
    s.circle(cx, cy, r, fill=TIRE, sw=4.5)
    for i in range(16):
        a = i * math.pi / 8
        s.line(cx + (r - 9) * math.cos(a), cy + (r - 9) * math.sin(a), cx + r * math.cos(a), cy + r * math.sin(a), sw=2.4)
    s.circle(cx, cy, r * 0.62, fill=STEEL, sw=3.5)
    s.circle(cx, cy, r * 0.30, fill=OD2, sw=3)
    for i in range(6):
        a = i * math.pi / 3
        s.circle(cx + r * 0.45 * math.cos(a), cy + r * 0.45 * math.sin(a), 4, fill=INK, sw=1)


def g15():
    """Half-track sound truck: horn loudspeakers on a turntable, wire recorder, crew, sound waves."""
    s = Svg(1600, 680, oy=30)
    G = 690
    _treeline(s, 0, 600, G - 40, G - 120, seed=9)
    s.path(f"M0,{G - 40} Q400,{G - 46} 800,{G - 40} T1600,{G - 42}", sw=3)
    s.ellipse(860, G - 2, 600, 22, fill=SHADOW, stroke="none")
    s.path(f"M0,{G + 14} Q400,{G + 6} 800,{G + 16} T1600,{G + 10}", sw=2.4, stroke=INK2)
    s.path(f"M470,{G} L840,{G} Q905,{G} 905,628 Q905,580 850,578 L480,586 Q420,590 420,640 Q420,{G} 470,{G} Z",
           fill=RUBBER, sw=4.5)
    s.path(f"M478,{G - 16} L836,{G - 16} Q884,{G - 16} 884,630 Q884,600 848,598 L486,604 Q440,608 440,642 "
           f"Q440,{G - 16} 478,{G - 16} Z", fill=TRACK_IN, sw=3)
    for tx in range(486, 840, 26):
        s.line(tx, G - 15, tx - 3, G - 1, sw=2.2)
    s.path(f"M520,{G - 78} L800,{G - 78} L780,{G - 56} L540,{G - 56} Z", fill=OD2, sw=3)
    for wx in (548, 616, 704, 772):
        s.circle(wx, G - 42, 30, fill=STEEL, sw=3.5)
        s.circle(wx, G - 42, 10, fill=OD2, sw=2.5)
    s.circle(856, 630, 34, fill=STEEL, sw=3.5)
    for i in range(8):
        a = i * math.pi / 4
        s.line(856 + 22 * math.cos(a), 630 + 22 * math.sin(a), 856 + 32 * math.cos(a), 630 + 32 * math.sin(a), sw=2.6)
    s.circle(856, 630, 9, fill=OD2, sw=2.5)
    s.circle(466, 640, 30, fill=STEEL, sw=3.5)
    s.circle(466, 640, 9, fill=OD2, sw=2.5)
    s.path("M412,402 L1092,402 L1100,560 L1080,592 L430,592 L412,560 Z", fill=OD, sw=4.5)
    s.path("M412,420 L1094,420", sw=2.6)
    for bx in range(430, 1090, 34):
        s.circle(bx, 411, 2.6, fill=INK, sw=1)
    s.path("M470,470 L1040,470 L1040,540 L470,540 Z", fill="none", sw=3)
    for mx in range(484, 1030, 74):
        s.path(f"M{mx},478 l58,0 l0,54 l-58,0 Z", fill=STEEL, sw=2.6)
        s.circle(mx + 29, 505, 13, fill="none", sw=2.2)
    s.hatch("M430,560 L1100,560 L1080,592 L430,592 Z", angle=-35, spacing=10, sw=2, box=(410, 556, 1104, 596))
    s.path("M1100,412 L1260,412 L1268,560 L1100,560 Z", fill=OD, sw=4.5)
    s.path("M1112,440 L1250,440 L1254,540 L1114,540 Z", fill="none", sw=2.4)
    s.line(1140, 484, 1172, 484, sw=5)
    s.path("M1252,412 L1236,300 L1262,296 L1280,412 Z", fill=OD2, sw=4)
    s.line(1240, 330, 1262, 328, sw=3)
    s.line(1244, 356, 1268, 354, sw=3)
    s.path("M1268,430 L1470,438 L1486,560 L1268,560 Z", fill=OD, sw=4.5)
    for lx in range(1300, 1460, 26):
        s.line(lx, 450, lx + 2, 548, sw=2.2)
    s.path("M1470,438 L1500,452 L1508,566 L1486,560 Z", fill=OD2, sw=3.5)
    for ly in range(462, 560, 14):
        s.line(1490, ly, 1504, ly + 3, sw=2.2)
    s.path("M1240,600 Q1258,500 1370,500 Q1470,500 1500,588 L1520,600 L1240,600 Z", fill=OD2, sw=4)
    _wheel_tire(s, 1370, G - 82, 82)
    s.path("M1470,512 q10,-26 32,-14 l-6,24 z", fill=STEEL, sw=3)
    s.path("M1510,590 L1560,590 Q1580,612 1560,634 L1510,634 Z", fill=STEEL, sw=4)
    s.line(1512, 612, 1556, 612, sw=2.2)
    # crew: driver (helmet) and operator (headphones)
    s.path("M1160,412 Q1166,386 1190,390 Q1218,390 1222,412 Z", fill=JACKET, sw=3.5)
    head(s, 1192, 366, 22, facing=1, cap="helmet")
    s.path("M1222,402 Q1246,396 1262,386", sw=6)
    s.path("M948,402 Q954,372 990,374 Q1026,374 1030,402 Z", fill=JACKET, sw=3.5)
    head(s, 990, 350, 22, facing=-1, cap="hair")
    s.path("M970,334 Q990,318 1010,334", sw=6)
    s.ellipse(986, 352, 9, 12, fill="#5b5248", sw=3)
    # loudspeaker array on a turntable
    s.path("M680,402 L700,368 L800,368 L820,402 Z", fill=OD2, sw=4)
    s.path("M738,368 L738,290 L762,290 L762,368 Z", fill=STEEL, sw=3.5)
    s.path("M560,100 L760,100 L760,300 L560,300 Z", fill=OD, sw=4.5)
    s.path("M574,114 L746,114 L746,286 L574,286 Z", fill="none", sw=2.4)
    s.hatch("M560,262 L760,262 L760,300 L560,300 Z", angle=-35, spacing=9, sw=2, box=(556, 258, 764, 304))
    s.path("M574,114 L746,286 M746,114 L574,286", sw=2.4)
    for bx, by in ((574, 114), (746, 114), (574, 286), (746, 286), (660, 200)):
        s.circle(bx, by, 6, fill=STEEL, sw=2.4)
    for cy in (140, 200, 260):
        s.path(f"M760,{cy - 18} C860,{cy - 20} 920,{cy - 34} 978,{cy - 52} L978,{cy + 52} C920,{cy + 34} 860,{cy + 20} 760,{cy + 18} Z",
               fill=STEEL, sw=4)
        s.ellipse(978, cy, 14, 52, fill="#d8d1bf", sw=3.5)
        s.ellipse(978, cy, 6, 30, fill="none", sw=2.2)
        s.path(f"M790,{cy + 18} C870,{cy + 22} 920,{cy + 34} 966,{cy + 48}", sw=2, stroke=INK2)
    s.path("M760,120 L800,120 M760,280 L800,282", sw=3)
    s.path("M600,300 C600,360 560,360 548,350", sw=3)
    s.path("M470,350 L600,350 L600,402 L470,402 Z", fill=STEEL, sw=4)                 # wire recorder case
    for rx in (505, 565):
        s.circle(rx, 376, 16, fill="#d8d1bf", sw=3)
        s.circle(rx, 376, 4, fill=INK, sw=1)
    s.path("M505,360 L565,360", sw=1.8)
    s.path("M420,402 Q414,250 440,96", sw=3)
    s.circle(440, 96, 4, fill=INK, sw=1)
    for i, r in enumerate((80, 150, 225, 305)):
        a0, a1 = -0.55, 0.22
        x0, y0 = 1000 + r * math.cos(a0), 200 + r * math.sin(a0)
        x1, y1 = 1000 + r * math.cos(a1), 200 + r * math.sin(a1)
        dash = 'stroke-dasharray="22 14"' if i % 2 else ""
        s.path(f"M{x0:.0f},{y0:.0f} A{r},{r} 0 0 1 {x1:.0f},{y1:.0f}", sw=4 - i * 0.4, extra=dash)
    parts = [("track_unit", (405, 574, 910, 700)), ("front_wheel_fender", (1236, 494, 1585, 700)),
             ("body_cab_hood", (405, 286, 1515, 600)), ("speaker_array", (550, 80, 1000, 410)),
             ("recorder_antenna", (400, 80, 610, 410)), ("sound_waves", (1000, 0, 1600, 500))]
    return s.svg(), [{"name": n, "polygon": s.norm_box(*b)} for n, b in parts], {"width": s.w, "height": s.h}


# ----------------------------------------------------------------- g17
def _dial(s, cx, cy, r, ticks=24):
    s.circle(cx, cy, r, fill="#e9e3cf", sw=4)
    s.circle(cx, cy, r - 12, fill="none", sw=2)
    for i in range(ticks):
        a = math.pi * (0.8 + 1.4 * i / (ticks - 1))
        ln = 9 if i % 4 == 0 else 5
        s.line(cx + (r - 3) * math.cos(a), cy + (r - 3) * math.sin(a),
               cx + (r - 3 - ln) * math.cos(a), cy + (r - 3 - ln) * math.sin(a), sw=2)
    s.line(cx, cy, cx + (r - 16) * math.cos(-1.0), cy + (r - 16) * math.sin(-1.0), sw=3)
    s.circle(cx, cy, 8, fill=INK, sw=1)


def _knob(s, cx, cy, r=11):
    s.circle(cx, cy, r, fill="#7a766a", sw=3)
    s.line(cx, cy - r + 3, cx, cy - 2, stroke=INK, sw=2.4)


def g17():
    """Spoof-radio operator keying Morse at a field desk (tent interior)."""
    s = Svg(1600, 690, oy=40)
    wall = "M0,110 Q420,52 800,44 Q1180,52 1600,110 L1600,560 L0,560 Z"
    s.path(wall, fill=WALL, sw=3.5)
    for x in (380, 700, 1010, 1330):
        s.path(f"M{x},{60 + abs(x - 800) // 12} Q{x + 8},300 {x},558", sw=2.2, stroke=INK2)
    s.path("M0,140 Q420,84 800,76 Q1180,84 1600,140", sw=2.2, stroke=INK2)
    s.path("M150,60 L162,60 L170,700 L144,700 Z", fill=WOOD2, sw=3.5)
    s.path("M0,560 L1600,560", sw=2.6)
    s.path("M0,562 L1600,562 L1600,730 L0,730 Z", fill="#e8d9bd", stroke="none", sw=0)
    for x in range(-700, 2400, 260):
        s.path(f"M{800 + (x - 800) * 0.42:.0f},562 L{x},730", sw=2, stroke=INK2)
    s.path("M0,640 L1600,640", sw=1.6, stroke=INK2, extra='stroke-dasharray="90 60"')
    # situation map (unit boxes, river, arrow) pinned to the wall
    s.path("M1210,110 L1540,104 L1546,360 L1214,366 Z", fill=PAPER, sw=3.5)
    for i in range(1, 6):
        s.path(f"M{1210 + i * 55},{110 - i} L{1214 + i * 55},{366 - i}", sw=1.6, stroke=INK2)
    for j in range(1, 5):
        s.path(f"M1211,{110 + j * 51} L1545,{104 + j * 51}", sw=1.6, stroke=INK2)
    s.path("M1236,350 C1290,300 1300,230 1380,200 S1500,150 1530,118", sw=7, stroke="#dfe8e6")
    s.path("M1236,350 C1290,300 1300,230 1380,200 S1500,150 1530,118", sw=2.4)
    for bx, by in ((1270, 170), (1420, 280)):
        s.path(f"M{bx},{by} l60,0 l0,36 l-60,0 Z", fill="#f0d9b5", sw=3)
        s.path(f"M{bx},{by} l60,36 M{bx + 60},{by} l-60,36", sw=2.2)
    s.path("M1340,250 Q1380,236 1410,262", sw=3)
    s.path("M1402,252 l10,10 l-14,4", sw=3)
    for px, py in ((1222, 120), (1530, 116), (1226, 352), (1534, 348)):
        s.circle(px, py, 6, fill="#c0503a", sw=2)
    s.path("M420,160 L560,156 L566,344 L426,348 Z", fill="#d9c09a", sw=3.5)          # clipboard
    s.path("M436,184 L548,181 L552,334 L440,337 Z", fill=PAPER, sw=2.6)
    s.path("M462,150 L524,148 L526,170 L464,172 Z", fill=STEEL, sw=3)
    for k in range(9):
        s.line(452, 206 + k * 14, 536 - (k % 3) * 12, 205 + k * 14, sw=1.8, stroke=INK2)
    s.line(800, 40, 800, 120, sw=2.6)                                                   # lamp
    s.path("M770,120 L830,120 L866,170 L734,170 Z", fill="#9aa284", sw=3.5)
    s.path("M780,170 Q800,196 820,170", fill="#f6e7a8", sw=3)
    s.path("M378,576 L536,576 L530,594 L384,594 Z", fill=WOOD, sw=3.5)                 # chair
    s.path("M394,594 L378,700 M522,594 L538,700 M386,646 L530,646", sw=5)
    s.path("M378,576 L360,402 L382,398 L400,576", fill=WOOD2, sw=3.5)
    s.path("M362,430 L420,428 L422,462 L366,466 Z", fill=WOOD, sw=3)
    s.path("M650,512 L670,700 M1380,512 L1360,700 M660,600 L1372,600", sw=6)           # desk
    s.path("M626,492 L1404,492 L1404,516 L626,516 Z", fill=WOOD2, sw=3.5)
    s.path("M640,452 L1390,452 L1420,492 L610,492 Z", fill=WOOD, sw=4)
    for gx in (700, 960, 1180):
        s.path(f"M{gx},462 q40,8 120,4", sw=1.8, stroke=INK2)
    s.path("M850,346 L1250,346 L1250,470 L850,470 Z", fill=PANEL, sw=4.5)               # transmitter
    s.path("M868,360 L1060,360 L1060,456 L868,456 Z", fill="none", sw=2.4)
    for gy in range(372, 452, 10):
        s.line(1080, gy, 1232, gy, sw=2.2)
    for kx in (896, 944, 992, 1040):
        _knob(s, kx, 412, 13)
    s.path("M840,376 q-14,0 -14,16 l0,30 q0,16 14,16", sw=4)
    s.path("M1260,376 q14,0 14,16 l0,30 q0,16 -14,16", sw=4)
    s.path("M870,226 L1230,226 L1230,346 L870,346 Z", fill=PANEL2, sw=4.5)              # receiver
    s.hatch("M870,326 L1230,326 L1230,346 L870,346 Z", angle=-35, spacing=9, sw=1.8, box=(866, 322, 1234, 350))
    _dial(s, 948, 284, 44)
    s.circle(1060, 276, 28, fill="#e9e3cf", sw=3.5)
    s.path("M1040,284 A22,22 0 0 1 1080,284", sw=1.8)
    s.line(1060, 290, 1072, 262, sw=2.6)
    for kx in (1120, 1160, 1200):
        _knob(s, kx, 268, 10)
        s.path(f"M{kx - 5},312 l10,0 l0,-14 l-10,0 z", fill="#e9e3cf", sw=2.4)
    for bx, by in ((878, 234), (1222, 234), (878, 338), (1222, 338)):
        s.circle(bx, by, 3.5, fill=INK, sw=1)
    s.path("M1210,226 Q1218,150 1260,60", sw=3)
    s.path("M1290,416 L1334,416 L1330,466 L1294,466 Z", fill="#e9e3cf", sw=3.5)         # mug
    s.path("M1334,428 q18,2 14,18 q-4,10 -16,8", sw=3.5)
    s.path("M1300,404 q6,-12 0,-22 M1318,402 q6,-12 0,-22", sw=2, stroke=INK2)
    s.path("M770,470 L840,466 L846,480 L774,484 Z", fill=PAPER, sw=3)                   # pad + pencil
    s.line(782, 474, 830, 472, sw=1.6, stroke=INK2)
    s.line(790, 462, 838, 458, sw=3.4)
    s.path("M660,478 L760,478 L762,490 L658,490 Z", fill="#a08468", sw=3)               # Morse key
    s.path("M676,478 L676,468 L744,464 L746,478", fill=STEEL, sw=3)
    s.path("M672,460 L744,456", sw=5)
    s.ellipse(676, 452, 15, 7, fill="#7a766a", sw=2.6)
    s.path("M762,486 C800,500 840,470 850,452", sw=2.4)
    figure(s, place(SEATED_KEY, 470, 706), facing=1, jacket="#b8ab7c", trouser=TROUSER, cap="hair")
    s.path("M538,334 Q548,292 590,306", sw=7)                                           # headphones
    s.ellipse(546, 346, 13, 17, fill="#5b5248", sw=3)
    s.circle(562, 362, 11, fill=SKIN, sw=3)
    s.path("M546,364 C576,430 700,410 760,424 S836,446 852,430", sw=2.4)
    parts = [("operator", (440, 300, 700, 715)), ("morse_key_pad", (650, 440, 860, 500)),
             ("radio_set", (820, 200, 1280, 476)), ("desk_chair", (350, 380, 1430, 705)),
             ("wall_map_lamp", (0, 0, 1600, 562))]
    return s.svg(), [{"name": n, "polygon": s.norm_box(*b)} for n, b in parts], {"width": s.w, "height": s.h}


SCENES = {"g13": g13, "g14": g14, "g15": g15, "g17": g17}
