"""pieces/mg-map (g02): package hygiene, `era: true` resolution, and one browser smoke test.

The browser test is skipped when Chromium (Playwright) is unavailable.
"""
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from studio_lib.design import Theme  # noqa: E402
from studio_lib.engines import html_seek as HS  # noqa: E402
from studio_lib.engines.base import SceneContext  # noqa: E402

PROJECT = ROOT / "examples" / "ghost-army"
PIECE = PROJECT / "pieces" / "mg-map"
PAGE = "pieces/mg-map/index.html"
# g02 as the second era of a piece clock, so the offset must come from the timing (5 s), not be 0
TIMING = {"fps": 30, "scenes": [{"id": "g01", "start": 0, "end": 5}, {"id": "g02", "start": 5, "end": 19.4667}]}
LATER = ["g20", "g23", "g24", "g26", "g28", "g31"]
WORDS = [(0.625, "Not"), (3.458, "trucks,"), (6.167, "two"), (10.347, "engines"), (12.347, "radio")]


def _ctx(params, w=1920, h=1080):
    scene = {"id": "g02", "params": params, "_project_dir": str(PROJECT)}
    return SceneContext(scene=scene, width=w, height=h, ss=1, fps=30, duration=1.0, theme=Theme(), words=list(WORDS))


class PackageTests(unittest.TestCase):
    def test_files_licences_and_size(self):
        for f in ["index.html", "main.js", "film.js", "timing.js", "README.md", "data/land-50m.json", "data/countries-110m.json",
                  "lib/d3-geo.min.js", "lib/d3-array.min.js", "lib/topojson-client.min.js", "lib/LICENSE.d3-geo",
                  "lib/LICENSE.topojson-client", "fonts/OFL-Inter.txt"]:
            self.assertTrue((PIECE / f).is_file(), f)
        size = sum(p.stat().st_size for p in PIECE.rglob("*") if p.is_file())
        self.assertLess(size, 3 * 1024 * 1024)
        readme = (PIECE / "README.md").read_text(encoding="utf-8")
        for s in ("MIT", "Natural Earth", "ISC", "OFL"):
            self.assertIn(s, readme)
        html = (PIECE / "index.html").read_text(encoding="utf-8") + (PIECE / "main.js").read_text(encoding="utf-8")
        self.assertNotIn("http", html.replace("https://", ""))   # no network fetches; relative paths only
        film = (PIECE / "film.js").read_text(encoding="utf-8")
        self.assertIn("getContext('2d')", film)                   # canvas 2D only, no GPU-only path
        self.assertFalse("getContext('webgl" in film or 'getContext("webgl' in film)

    def test_setup_scene_has_no_reveal_wording(self):   # g02 sets up g03's reveal
        js = (PIECE / "film.js").read_text(encoding="utf-8")
        for bad in ("SIMULATED", "contested", "decoy"):
            self.assertFalse(bad in js, bad)

    def test_later_eras_are_registered(self):
        eras = (PIECE / "eras.js").read_text(encoding="utf-8")
        timing = (PIECE / "timing.js").read_text(encoding="utf-8")
        for sid in LATER:
            self.assertIn(f"function {sid}(", eras)
            self.assertIn(f"'{sid}'", timing)                        # production default clock lists every era
        self.assertIn("SIMULATED", eras)                              # the g28 reveal is labelled; g02 is not

    def test_era_true_means_this_scene(self):
        e = HS.HtmlSeekEngine(_ctx({"page": PAGE, "era": True, "timing": TIMING}))
        self.assertEqual(e.era, "g02")
        self.assertEqual(e.offset, 5.0)
        js = HS.timing_script(e.timing, e.era, WORDS)
        self.assertIn('"words"', js)


def _browser_ok() -> bool:
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


@unittest.skipUnless(_browser_ok(), "Chromium (Playwright) is unavailable")
class BrowserTests(unittest.TestCase):
    def test_page_loads_era_offset_and_frame0(self):
        import numpy as np

        e = HS.HtmlSeekEngine(_ctx({"page": PAGE, "era": True, "timing": TIMING, "workers": 1, "capture": "png"}))
        try:
            im = np.asarray(e.grab(0.0), dtype=float)
            pg = e._page
            self.assertEqual(pg.evaluate("window.SCENES[0].id"), "g02")
            self.assertTrue(pg.evaluate("window.SCENES[0].words"))            # injected word timings are used
            self.assertAlmostEqual(pg.evaluate("window.DUR"), 19.4667, places=3)
            self.assertEqual(pg.evaluate("window.MIN_TEXT(15).scene"), "g02")
            self.assertGreaterEqual(pg.evaluate("window.MIN_TEXT(5 + 12.9).px"), 28)
        finally:
            e.close()
        self.assertEqual(im.shape, (1080, 1920, 3))
        self.assertGreater(im.std(), 8.0)                                     # frame 0 is a map, not a blank fill
        self.assertGreater(im.mean(), 8.0)


@unittest.skipUnless(_browser_ok(), "Chromium (Playwright) is unavailable")
class LaterEraTests(unittest.TestCase):
    def test_every_later_era_renders_readably_from_its_offset(self):
        import numpy as np

        durs = {"g20": 24.43, "g23": 18.93, "g24": 24.77, "g26": 12.2, "g28": 20.67, "g31": 33.8}
        t, scenes = 0.0, []
        for sid in ["g02"] + LATER:
            d = 14.4667 if sid == "g02" else durs[sid]
            scenes.append({"id": sid, "start": round(t, 4), "end": round(t + d, 4)})
            t += d
        timing = {"fps": 30, "scenes": scenes}
        scene = {"id": "g28", "params": {"page": PAGE, "era": True, "timing": timing, "workers": 1, "capture": "png"},
                 "_project_dir": str(PROJECT)}
        e = HS.HtmlSeekEngine(SceneContext(scene=scene, width=1920, height=1080, ss=1, fps=30, duration=1.0, theme=Theme()))
        try:
            self.assertAlmostEqual(e.offset, scenes[5]["start"], places=3)
            im = np.asarray(e.grab(19.0), dtype=float)               # g28 near its end: the reveal is on screen
            self.assertGreater(im.std(), 8.0)
            pg = e._page
            self.assertEqual([s["id"] for s in pg.evaluate("window.SCENES")], ["g02"] + LATER)
            for s in scenes[1:]:
                for frac in (0.5, 0.95):
                    r = pg.evaluate(f"window.MIN_TEXT({s['start'] + frac * (s['end'] - s['start'])})")
                    self.assertEqual(r["scene"], s["id"])
                    self.assertGreaterEqual(r["px"], 28, (s["id"], frac, r))
        finally:
            e.close()


if __name__ == "__main__":
    unittest.main()
