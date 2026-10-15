"""html_seek: injected scene timing, era offsets, cache keys, font degradation, parallel capture.

The browser tests are skipped when Chromium (Playwright) or the lemo-opuscar checkout is unavailable.
"""
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from studio_lib.config import RenderSettings  # noqa: E402
from studio_lib.design import Theme  # noqa: E402
from studio_lib.engines import html_seek as HS  # noqa: E402
from studio_lib.engines.base import SceneContext  # noqa: E402
from studio_lib.engines.browser import external_dir  # noqa: E402
from studio_lib.render import scene_job  # noqa: E402

PROJECT = ROOT / "examples" / "ghost-army"
PAGE = "pieces/lemo-whiteboard/index.html"
TIMING = {"fps": 30, "scenes": [{"id": "g08", "start": 0, "end": 15}, {"id": "g12", "start": 15, "end": 37}]}


def _ctx(params, words=()):
    scene = {"id": "x", "params": params, "_project_dir": str(PROJECT)}
    return SceneContext(scene=scene, width=640, height=360, ss=1, fps=30, duration=1.0, theme=Theme(), words=list(words))


class TimingTests(unittest.TestCase):
    def test_timing_changes_the_cache_key(self):
        tl = {"duration": 15.0, "frames": 450, "words": []}
        st = RenderSettings("long", "draft")

        def key(timing):
            scene = {"id": "g08", "engine": "html_seek", "params": {"page": PAGE, "era": "g08", "timing": timing}}
            return scene_job(scene, tl, st, "default", {}, None, None, None, "html_seek", [], Path("."))["hash"]

        other = json.loads(json.dumps(TIMING))
        other["scenes"][0]["end"] = 16
        self.assertNotEqual(key(TIMING), key(other))
        self.assertEqual(key(TIMING), key(json.loads(json.dumps(TIMING))))

    def test_timing_script_and_words(self):
        self.assertIsNone(HS.timing_script(None))
        js = HS.timing_script(TIMING, "g12", [(0.5, "So"), (1.25, "far")])
        self.assertTrue(js.startswith("window.STUDIO_TIMING = "))
        tm = json.loads(js[len("window.STUDIO_TIMING = "):-1])
        g12 = [s for s in tm["scenes"] if s["id"] == "g12"][0]
        self.assertEqual(g12["words"], [[0.5, "So"], [1.25, "far"]])
        self.assertNotIn("words", tm["scenes"][0])

    def test_offset_selects_the_era(self):
        self.assertEqual(HS.HtmlSeekEngine(_ctx({"page": PAGE, "era": "g12", "timing": TIMING})).offset, 15.0)
        self.assertEqual(HS.HtmlSeekEngine(_ctx({"page": PAGE, "era": "g08", "timing": TIMING})).offset, 0.0)
        self.assertEqual(HS.HtmlSeekEngine(_ctx({"page": PAGE, "era": "g12", "timing": TIMING, "offset": 3})).offset, 3.0)
        self.assertEqual(HS.HtmlSeekEngine(_ctx({"page": PAGE})).offset, 0.0)


class FontDegradationTests(unittest.TestCase):
    def test_absent_font_is_logged_not_fatal(self):
        td = Path(tempfile.mkdtemp())
        man = td / "manifest.json"
        man.write_text(json.dumps({"paths": {"styles/x/demo/fonts/A.ttf": "a/A.ttf"}, "by_basename": {"B.ttf": "b/B.ttf"}}), encoding="utf-8")
        HS._font_manifest.cache_clear()
        self.assertIsNone(HS.resolve_font("styles/x/demo/fonts/A.ttf", str(man)))   # listed, not fetched
        self.assertTrue(HS.font_listed("styles/x/demo/fonts/A.ttf", str(man)))
        (td / "b").mkdir()
        (td / "b" / "B.ttf").write_bytes(b"\0")
        self.assertEqual(HS.resolve_font("any/where/B.ttf", str(man)), str((td / "b" / "B.ttf").resolve()))
        h = object.__new__(type("H", (HS._Handler,), {"font_manifest": str(man), "font_fallback": None,
                                                     "substitutions": [], "font_mapped": []}))
        out = h._missing_font(str(td / "A.ttf"), "styles/x/demo/fonts/A.ttf")
        self.assertEqual(out, str(td / "A.ttf"))          # no fallback font: a 404, never an exception
        self.assertIn("not fetched", h.substitutions[0])
        missing = HS._font_manifest(str(td / "nope.json"))
        self.assertEqual(missing, ({}, {}, ""))


def _browser_ok() -> bool:
    if not external_dir("lemo", "core/lib.js"):
        return False
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as p:
            try:
                p.chromium.launch().close()
            except Exception:
                from studio_lib.engines.browser import chromium_path

                exe = chromium_path()
                if not exe:
                    return False
                p.chromium.launch(executable_path=exe).close()
        return True
    except Exception:
        return False


@unittest.skipUnless(_browser_ok(), "Chromium (Playwright) or the lemo-opuscar checkout is unavailable")
class BrowserTests(unittest.TestCase):
    def test_offset_renders_the_right_era_and_pool_matches(self):
        import numpy as np

        e1 = HS.HtmlSeekEngine(_ctx({"page": PAGE, "era": "g12", "timing": TIMING, "workers": 1}))
        try:
            e1.grab(0.0)
            self.assertEqual(e1._page.evaluate("window.STUDIO_TIMING.scenes[1].start"), 15)
            self.assertEqual(e1._page.evaluate("window.MIN_TEXT(15.5).scene"), "g12")
            self.assertEqual(e1._page.evaluate("window.MIN_TEXT(14.5).scene"), "g08")
            seq = [np.asarray(e1.grab(5 + i / 30), dtype=float) for i in range(3)]
        finally:
            e1.close()
        e3 = HS.HtmlSeekEngine(_ctx({"page": PAGE, "era": "g12", "timing": TIMING, "workers": 2}))
        try:
            par = [np.asarray(e3.grab(5 + i / 30), dtype=float) for i in range(3)]
        finally:
            e3.close()
        self.assertFalse(e3.errors)
        for a, b in zip(seq, par):   # same frames from the page pool (JPEG q95 on both paths)
            self.assertLess(float(np.abs(a - b).mean()), 2.0)

    def test_second_half_eras_build_and_stay_legible(self):
        tm = {"fps": 30, "scenes": [{"id": "g30", "start": 0, "end": 9.37}, {"id": "g36", "start": 9.37, "end": 23.4},
                                    {"id": "g42", "start": 23.4, "end": 42.97}, {"id": "g43", "start": 42.97, "end": 75.14}]}
        e = HS.HtmlSeekEngine(_ctx({"page": PAGE, "era": "g42", "timing": tm, "workers": 1}))
        try:
            e.grab(1.0)
            self.assertEqual(e.offset, 23.4)
            for s in tm["scenes"]:   # each era answers for its own span, labels >= 28 px at 1080p
                mid = (s["start"] + s["end"]) / 2
                r = e._page.evaluate("t => window.MIN_TEXT(t)", mid)
                self.assertEqual(r["scene"], s["id"])
                end = e._page.evaluate("t => window.MIN_TEXT(t)", s["end"] - .05)
                self.assertGreaterEqual(end["px"], 28)
                self.assertFalse(e._page.evaluate("t => window.CLIPPED(t).clipped", s["end"] - .05))
        finally:
            e.close()
        self.assertFalse([x for x in e.errors if not x.startswith("blocked")])


if __name__ == "__main__":
    unittest.main()
