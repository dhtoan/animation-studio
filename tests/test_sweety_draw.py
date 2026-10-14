"""sweety_draw engine + vendored sweety-handdraw-video core + illustration kit (fast, 320x180)."""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from studio_lib.design import Theme  # noqa: E402
from studio_lib.engines.base import SceneContext  # noqa: E402
from studio_lib.engines import sweety_draw as SD  # noqa: E402

TINY_SVG = ('<svg xmlns="http://www.w3.org/2000/svg" width="200" height="100" viewBox="0 0 200 100">'
            '<rect x="20" y="20" width="60" height="60" fill="#c9a47c" stroke="#26221e" stroke-width="4"/>'
            '<circle cx="150" cy="50" r="30" fill="#a8ab73" stroke="#26221e" stroke-width="4"/></svg>')


def two_shapes(path: Path, transparent=False):
    """Left square + right circle, dark outlines with warm fills (paintable)."""
    im = Image.new("RGBA" if transparent else "RGB", (400, 200), (0, 0, 0, 0) if transparent else "white")
    d = ImageDraw.Draw(im)
    d.rectangle((30, 40, 170, 170), outline=(30, 28, 25), width=5, fill=(201, 164, 124))
    d.ellipse((230, 40, 370, 170), outline=(30, 28, 25), width=5, fill=(168, 171, 115))
    im.save(path)


class SweetyDrawTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = Path(tempfile.mkdtemp())
        two_shapes(cls.td / "shapes.png")
        two_shapes(cls.td / "shapes_alpha.png", transparent=True)

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.td, ignore_errors=True)

    def engine(self, work="w", duration=3.0, size=(320, 180), **params):
        params.setdefault("src", "shapes.png")
        params.setdefault("pen", "none")
        sc = {"id": "sd", "params": params, "_project_dir": str(self.td), "_work_dir": str(self.td / work),
              "camera": {"move": "static"}}
        ctx = SceneContext(scene=sc, width=size[0], height=size[1], ss=2, fps=30, duration=duration, theme=Theme())
        return SD.SweetyDrawEngine(ctx)

    def test_frames_are_rgb_deterministic(self):
        a = self.engine(pen="pen")
        b = self.engine(pen="pen")
        for t in (2.0, 0.4, 1.1, 2.9):  # out of order on purpose
            fa, fb = a.frame(t), b.frame(t)
            self.assertEqual(fa.size, (320, 180))
            self.assertEqual(fa.mode, "RGB")
            self.assertEqual(fa.tobytes(), fb.tobytes(), t)
        self.assertEqual(a.frame(1.1).tobytes(), a.frame(1.1).tobytes())
        self.assertNotEqual(a.frame(0.5).tobytes(), a.frame(2.5).tobytes())

    def test_ink_coverage_is_monotonic(self):
        e = self.engine()
        blank = np.asarray(e.frame(0.0), dtype=np.int16)
        counts = []
        for t in np.linspace(0.0, 3.0, 13):
            f = np.asarray(e.frame(float(t)), dtype=np.int16)
            counts.append(int((np.abs(f - blank).sum(axis=2) > 6).sum()))
        self.assertEqual(counts, sorted(counts), counts)
        self.assertGreater(counts[-1], 2000)

    def test_part_order_is_respected(self):
        e = self.engine(work="order", parts=[{"name": "right", "bbox": [0.5, 0, 1, 1]},
                                             {"name": "left", "bbox": [0, 0, 0.5, 1]}])
        art = e.assets[-1]
        parts = art["meta"]["parts"]
        self.assertEqual([p["id"] for p in parts][:2], ["right", "left"])
        self.assertLessEqual(parts[0]["outline_end"], parts[1]["outline_start"] + 1e-6)
        self.assertLessEqual(max(p["outline_end"] for p in parts), min(p["fill_start"] for p in parts) + 1e-6)
        alpha = SD._vendor().reveal.reveal_alpha(art["rgba"][:, :, 3], art["maps"], parts[0]["outline_end"] * 0.9)
        w = alpha.shape[1]
        self.assertGreater(int((alpha[:, w // 2:] > 0).sum()), 50)     # right part already inked
        self.assertEqual(int((alpha[:, : w // 2 - 4] > 0).sum()), 0)    # left part untouched

    def test_strokes_follow_the_nib(self):
        e = self.engine(work="nib")
        art = e.assets[-1]
        R = SD._vendor().reveal
        R.validate_strokes(art["meta"])
        ink = (art["rgba"][:, :, 3] > 0) & (art["maps"]["ink_weight"] > 0.01)
        dist, _ = R.match_reveal_to_tip(art["meta"], art["maps"]["ink"], ink, {"ink"})
        self.assertTrue(np.isfinite(dist).all())
        self.assertLess(float(dist.max()), 9.0)

    def test_plan_cache_reused_from_disk(self):
        SD.clear_memory_cache()
        before = SD.BUILD_COUNT
        e1 = self.engine(work="cache", title="Hi")
        built = SD.BUILD_COUNT - before
        self.assertEqual(built, 2)                      # art + title
        self.assertTrue((e1.cache_dir / "done.json").exists())
        SD.clear_memory_cache()
        e2 = self.engine(work="cache", title="Hi")
        self.assertEqual(SD.BUILD_COUNT - before, 2)    # loaded, not rebuilt
        self.assertEqual(e1.frame(1.5).tobytes(), e2.frame(1.5).tobytes())
        self.engine(work="cache", title="Hi", parts=[{"name": "all", "bbox": [0, 0, 1, 1]}])
        self.assertEqual(SD.BUILD_COUNT - before, 3)    # parts change -> new art plan, title reused

    def test_transparent_background_keeps_scene_paper(self):
        e = self.engine(work="alpha", src="shapes_alpha.png")
        art = e.assets[-1]
        self.assertEqual(int(art["rgba"][0, 0, 3]), 0)
        empty = (art["x"] + art["rgba"].shape[1] // 2, art["y"] + 2)   # between the shapes, top row
        start, end = e.frame(0.0), e.frame(2.99)
        self.assertEqual(start.getpixel(empty), end.getpixel(empty))

    def test_pen_stays_on_canvas_between_groups(self):
        e = self.engine(work="pen", title="Ab", pen="pen")
        first, last = e.events[0], e.events[-1]
        for t in np.linspace(first["start"], last["end"], 40):
            tip = e.pen_tip(float(t))
            self.assertIsNotNone(tip, t)
            self.assertTrue(0 <= tip[0] < 320 and 0 <= tip[1] < 180, (t, tip))
        self.assertIsNone(e.pen_tip(last["end"] + 2.0))

    def test_draw_window_fractions_and_seconds(self):
        e = self.engine(work="win", draw_window=[0.2, 0.6])
        self.assertAlmostEqual(e.events[0]["start"], 0.6, places=5)
        self.assertAlmostEqual(e.events[-1]["end"], 1.8, places=5)
        e = self.engine(work="win", draw_window=[0.5, 2.5])
        self.assertAlmostEqual(e.events[-1]["end"], 2.5, places=5)

    def test_vendored_attribution(self):
        v = ROOT / "adapters" / "vendor" / "sweety_handdraw"
        self.assertIn("MIT License", (v / "LICENSE").read_text(encoding="utf-8"))
        src = (v / "SOURCE.md").read_text(encoding="utf-8")
        self.assertIn("5206ec0d17f9b353e400b64b9c51ad69e721e02a", src)
        for f in ("stroke_assets.py", "paint_motion.py", "reveal.py", "stroke_paths.py"):
            self.assertIn("threerocks/sweety-handdraw-video", (v / f).read_text(encoding="utf-8")[:600], f)

    def test_ghost_army_scenes_emit_svg_and_parts(self):
        from studio_lib.illustration.ghost_army import SCENES
        for sid, fn in SCENES.items():
            svg, parts, info = fn()
            self.assertTrue(svg.startswith("<svg"), sid)
            self.assertGreaterEqual(len(parts), 4, sid)
            for p in parts:
                self.assertTrue(all(0 <= c <= 1 for pt in p["polygon"] for c in pt), (sid, p))

    def test_svg_raster_and_engine_svg_source(self):
        from studio_lib.illustration import raster
        if not raster.available():
            self.skipTest("Playwright Chromium not available")
        out = raster.render_svg(TINY_SVG, self.td / "tiny.png")
        im = Image.open(out)
        self.assertEqual(im.mode, "RGBA")
        self.assertEqual(im.getpixel((2, 2))[3], 0)            # transparent background
        self.assertEqual(im.getpixel((50, 50))[3], 255)        # painted square
        (self.td / "tiny.svg").write_text(TINY_SVG, encoding="utf-8")
        e = self.engine(work="svg", src="tiny.svg")
        self.assertEqual(int(e.assets[-1]["rgba"][0, 0, 3]), 0)
        self.assertNotEqual(e.frame(0.0).tobytes(), e.frame(2.9).tobytes())


if __name__ == "__main__":
    unittest.main()
