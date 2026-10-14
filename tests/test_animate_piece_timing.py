"""AnimatePieceEngine + the timing-driven Ghost Army crosshatch piece.

- params.timing changes the build key (and is written only into the work copy, never the source dir);
- a scene rendered with offset = its start shows that scene's era on its first frame (a clean cut), and is
  pixel-identical to the same absolute time rendered with offset 0.
Skips when node / the animate checkout / Chromium are unavailable.
Run: python -m unittest tests.test_animate_piece_timing -v   (from the repo root)
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from studio_lib.design import Theme  # noqa: E402
from studio_lib.engines import SceneContext  # noqa: E402
from studio_lib.engines.browser import AnimatePieceEngine, external_dir  # noqa: E402

PIECE = ROOT / "examples" / "ghost-army" / "pieces" / "crosshatch"
TIMING = {"fps": 30, "scenes": [
    {"id": "g01", "start": 0, "end": 4.2, "bridge_next": False},
    {"id": "g03", "start": 4.2, "end": 9.0, "bridge_next": False},
    {"id": "g04", "start": 9.0, "end": 12.5, "bridge_next": False},
    {"id": "g13", "start": 12.5, "end": 18.0, "bridge_next": True},
    {"id": "g14", "start": 18.0, "end": 22.0, "bridge_next": False},
]}


def _can_build() -> bool:
    return bool(shutil.which("node") and external_dir("animate", "tools/build.mjs") and PIECE.exists())


def _engine(work: str, offset: float = 0.0, timing=TIMING):
    scene = {"id": "t", "params": {"piece": str(PIECE), "offset": offset, "timing": timing}, "_work_dir": work}
    ctx = SceneContext(scene=scene, width=1920, height=1080, ss=1, fps=30, duration=2.0, theme=Theme())
    return AnimatePieceEngine(ctx)


class BuildKeyTest(unittest.TestCase):
    def test_timing_changes_build_key(self):
        a = AnimatePieceEngine.build_key_for(PIECE, TIMING)
        b = AnimatePieceEngine.build_key_for(PIECE, {**TIMING, "scenes": TIMING["scenes"][:-1]})
        self.assertNotEqual(a, b)
        self.assertEqual(a, AnimatePieceEngine.build_key_for(PIECE, dict(TIMING)))
        self.assertNotEqual(a, AnimatePieceEngine.build_key_for(PIECE, None))

    @unittest.skipUnless(_can_build(), "node or the animate checkout is unavailable")
    def test_timing_written_to_work_copy_only(self):
        before = (PIECE / "src" / "timing.js").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as td:
            eng = _engine(td)
            js = (eng.work / "src" / "timing.js").read_text(encoding="utf-8")
            self.assertIn("window.GA_TIMING", js)
            self.assertIn('"end": 22.0', js)
            self.assertIn(eng.build_key, eng.work.name)
            other = _engine(td, timing={**TIMING, "scenes": TIMING["scenes"][:3]})
            self.assertNotEqual(eng.work, other.work)
        self.assertEqual(before, (PIECE / "src" / "timing.js").read_text(encoding="utf-8"))


@unittest.skipUnless(_can_build(), "node or the animate checkout is unavailable")
class OffsetTest(unittest.TestCase):
    def test_offset_maps_to_scene(self):
        import numpy as np
        with tempfile.TemporaryDirectory() as td:
            try:
                a = _engine(td, offset=9.0)
                a._open()
            except Exception as e:  # no Chromium / Playwright
                self.skipTest(f"browser unavailable: {e}")
            try:
                pg = a.session.page
                self.assertEqual(pg.evaluate("gaEraIdAt(9.0)"), "g04")       # first frame of g04: a clean cut
                self.assertEqual(pg.evaluate("gaEraIdAt(9.0 - 1/30)"), "g03")
                self.assertEqual(pg.evaluate("gaEraIdAt(12.5)"), "g13")
                self.assertEqual(pg.evaluate("window.TIMELINE.duration"), 22.0)
                self.assertEqual(pg.evaluate("window.TIMELINE.morphs"), [18.0])   # only g13 -> g14 bridges
                first = np.asarray(a.grab(0.0))
            finally:
                a.close()   # one sync Playwright per thread at a time
            b = _engine(td, offset=0.0)
            try:
                same = np.asarray(b.grab(9.0))
            finally:
                b.close()
            self.assertTrue(np.array_equal(first, same))


if __name__ == "__main__":
    unittest.main()
