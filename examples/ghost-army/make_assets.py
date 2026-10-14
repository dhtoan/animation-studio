"""Original line-art assets for the Ghost Army demo (no third-party imagery).

assets/decoy-tank.png — a generic WWII-era medium tank drawn as an inflatable decoy
(seams, inflation valve), clean dark lines on white so the image_whiteboard engine
can trace it stroke by stroke. Generic silhouette; not traced from any photograph.

Usage: python make_assets.py <project_dir>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw

INK = (28, 26, 24)
OLIVE = (126, 134, 92)
OLIVE_D = (98, 106, 70)
RUBBER = (70, 70, 66)


def decoy_tank(out: Path, W: int = 1600, H: int = 1000):
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)
    lw = 9
    # tracks
    d.rounded_rectangle((250, 560, 1350, 760), radius=100, fill=RUBBER, outline=INK, width=lw)
    for i in range(7):
        cx = 360 + i * 147
        d.ellipse((cx - 62, 598, cx + 62, 722), fill=(150, 150, 140), outline=INK, width=lw)
    # hull
    d.polygon([(220, 560), (330, 420), (1270, 420), (1390, 560)], fill=OLIVE, outline=INK)
    d.line([(220, 560), (330, 420), (1270, 420), (1390, 560), (220, 560)], fill=INK, width=lw, joint="curve")
    # turret
    d.rounded_rectangle((560, 250, 1040, 430), radius=70, fill=OLIVE_D, outline=INK, width=lw)
    # barrel
    d.rounded_rectangle((1030, 305, 1520, 355), radius=20, fill=OLIVE_D, outline=INK, width=lw)
    # inflatable seams (dashed)
    for x0 in range(360, 1240, 60):
        d.line([(x0, 470), (x0 + 30, 470)], fill=INK, width=5)
    for x0 in range(600, 1000, 50):
        d.line([(x0, 300), (x0 + 25, 300)], fill=INK, width=5)
    # star marking + valve
    cx, cy, r = 800, 500, 34
    import math
    pts = [(cx + (r if k % 2 == 0 else r * 0.42) * math.cos(-math.pi / 2 + k * math.pi / 5),
            cy + (r if k % 2 == 0 else r * 0.42) * math.sin(-math.pi / 2 + k * math.pi / 5)) for k in range(10)]
    d.polygon(pts, fill="white", outline=INK)
    d.ellipse((1180, 450, 1214, 484), fill="white", outline=INK, width=6)
    d.line([(1197, 450), (1197, 420)], fill=INK, width=6)
    # ground line
    d.line([(120, 770), (1480, 770)], fill=INK, width=6)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out)
    print("wrote", out)


if __name__ == "__main__":
    pdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    decoy_tank(pdir / "assets" / "decoy-tank.png")
