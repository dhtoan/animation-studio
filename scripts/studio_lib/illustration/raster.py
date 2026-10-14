"""Rasterise SVG to a transparent PNG with Playwright Chromium.

  python scripts/studio_lib/illustration/raster.py ghost-army [out_dir] [--scale 1.0]
      writes <id>.svg, <id>.png (transparent) and <id>.parts.json for g13/g14/g15/g17
      (default out_dir: examples/ghost-army/assets/art)
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

_AVAILABLE: bool | None = None


def available() -> bool:
    """True when Playwright and a launchable Chromium are present (cached per process)."""
    global _AVAILABLE
    if _AVAILABLE is None:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                p.chromium.launch().close()
            _AVAILABLE = True
        except Exception:  # noqa: BLE001 - any failure means "cannot rasterise here"
            _AVAILABLE = False
    return _AVAILABLE


def svg_size(svg: str) -> tuple[float, float]:
    head = svg[: svg.find(">") + 1]
    w = re.search(r'\bwidth="([\d.]+)', head)
    h = re.search(r'\bheight="([\d.]+)', head)
    if w and h:
        return float(w.group(1)), float(h.group(1))
    vb = re.search(r'viewBox="[\d.\-]+[ ,]+[\d.\-]+[ ,]+([\d.]+)[ ,]+([\d.]+)"', head)
    if vb:
        return float(vb.group(1)), float(vb.group(2))
    raise ValueError("SVG needs width/height or a viewBox")


def render_many(items, scale: float = 1.0, transparent: bool = True) -> list[Path]:
    """items: [(svg_text, out_png)]. One browser for the batch."""
    from playwright.sync_api import sync_playwright
    outs = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            for svg, out in items:
                w, h = svg_size(svg)
                page = browser.new_page(viewport={"width": max(1, round(w)), "height": max(1, round(h))},
                                        device_scale_factor=scale)
                bg = "transparent" if transparent else "#ffffff"
                page.set_content(f"<html><body style='margin:0;background:{bg}'>{svg}</body></html>")
                out = Path(out)
                out.parent.mkdir(parents=True, exist_ok=True)
                page.screenshot(path=str(out), omit_background=transparent,
                                clip={"x": 0, "y": 0, "width": w, "height": h})
                page.close()
                outs.append(out)
        finally:
            browser.close()
    return outs


def render_svg(svg: str, out, scale: float = 1.0, transparent: bool = True) -> Path:
    return render_many([(svg, out)], scale, transparent)[0]


def write_ghost_army(out_dir, scale: float = 1.0, ids=None) -> list[Path]:
    from .ghost_army import SCENES
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    items = []
    for sid, fn in SCENES.items():
        if ids and sid not in ids:
            continue
        svg, parts, info = fn()
        (out_dir / f"{sid}.svg").write_text(svg, encoding="utf-8")
        (out_dir / f"{sid}.parts.json").write_text(json.dumps(parts, indent=1), encoding="utf-8")
        items.append((svg, out_dir / f"{sid}.png"))
    return render_many(items, scale=scale)


if __name__ == "__main__":
    here = Path(__file__).resolve()
    sys.path.insert(0, str(here.parents[2]))
    from studio_lib.illustration.raster import write_ghost_army as _write  # noqa: E402
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    scale = float(sys.argv[sys.argv.index("--scale") + 1]) if "--scale" in sys.argv else 1.0
    if not args or args[0] != "ghost-army":
        sys.exit(__doc__)
    out = Path(args[1]) if len(args) > 1 and not args[1].replace(".", "").isdigit() else here.parents[3] / "examples/ghost-army/assets/art"
    for path in _write(out, scale=scale):
        print("wrote", path, path.stat().st_size, "bytes")
