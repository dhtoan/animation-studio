"""Visual-fidelity upgrade: quality-regression checks and the premium (no silent fallback) policy."""
import sys
import unittest
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from studio_lib import visual_qa as V  # noqa: E402
from studio_lib.engines import ENGINES, TIER  # noqa: E402
from studio_lib.router import EngineUnavailable, route  # noqa: E402

AVAIL_ALL = {k: {"ok": True} for k in ENGINES}
PREMIUM = {"category": "history", "quality_profile": "documentary-premium"}


def busy(seed: int, w=480, h=270):
    """A detailed, full composition (noise texture + many shapes), different per seed."""
    rng = np.random.default_rng(seed)
    a = (rng.random((h, w, 3)) * 60 + 90).astype("uint8")
    im = Image.fromarray(a)
    d = ImageDraw.Draw(im)
    for _ in range(60):
        x, y = int(rng.integers(20, w - 60)), int(rng.integers(20, h - 60))
        d.rectangle([x, y, x + int(rng.integers(10, 40)), y + int(rng.integers(10, 40))],
                    outline=tuple(int(c) for c in rng.integers(0, 255, 3)), width=2)
    return im


def blank(w=480, h=270, dot=False):
    im = Image.new("RGB", (w, h), (244, 241, 232))
    if dot:
        ImageDraw.Draw(im).ellipse([w // 2 - 6, h // 2 - 6, w // 2 + 6, h // 2 + 6], fill=(20, 20, 20))
    return im


class SceneCheckTests(unittest.TestCase):
    def test_blank_composition_flagged(self):
        r = V.scene_checks([(t, blank(dot=True)) for t in range(6)])
        self.assertTrue(any(i.startswith("blank_composition") for i in r["issues"]))

    def test_static_scene_flagged(self):
        im = busy(1)
        r = V.scene_checks([(t, im) for t in range(6)])
        self.assertTrue(any(i.startswith("static_scene") for i in r["issues"]))

    def test_rich_moving_scene_passes(self):
        r = V.scene_checks([(t, busy(t)) for t in range(6)], expect_size=(480, 270))
        self.assertEqual(r["issues"], [], r["issues"])

    def test_aspect_mismatch(self):
        r = V.scene_checks([(t, busy(t, 270, 480)) for t in range(4)], expect_size=(480, 270))
        self.assertTrue(any(i.startswith("aspect") for i in r["issues"]))

    def test_edge_clipping_warning(self):
        def cut(k):
            im = blank()
            d = ImageDraw.Draw(im)
            for y in range(20, 250, 6):  # dense "text" bars running off the right edge
                d.line([300 + k, y, 480, y], fill=(10, 10, 10), width=2)
            return im
        r = V.scene_checks([(t, cut(t)) for t in range(6)])
        self.assertTrue(any(w.startswith("edge_clipping: detail runs into the right") for w in r["warnings"]))

    def test_continuity_jump_on_hard_cut(self):
        dark = Image.new("RGB", (480, 270), (12, 14, 20))
        light = Image.new("RGB", (480, 270), (245, 242, 235))
        a = V.scene_checks([(0, dark), (1, dark)])
        b = V.scene_checks([(0, light), (1, light)])
        same = {"chapter": "c1", "transition": "cut"}
        self.assertTrue(V.continuity_checks([("a", same, a), ("b", same, b)]))
        self.assertFalse(V.continuity_checks([("a", same, a), ("b", {**same, "transition": "dissolve"}, b)]))


class PolicyTests(unittest.TestCase):
    def test_premium_never_routes_to_native(self):
        r = route({"id": "s1", "engine": "huashu_clip", "narration": "x"}, PREMIUM, AVAIL_ALL)
        self.assertEqual(r["engine"], "huashu_clip")
        self.assertTrue(all(TIER[f] == "authentic" for f in r["fallbacks"]), r["fallbacks"])
        self.assertTrue(r["strict"])

    def test_premium_missing_engine_raises_with_reason(self):
        av = {**AVAIL_ALL, **{k: {"ok": False} for k in ("huashu_clip", "animate_piece", "html_seek")}}
        with self.assertRaises(EngineUnavailable) as cm:
            route({"id": "s9", "engine": "huashu_clip", "narration": "x"}, PREMIUM, av)
        self.assertIn("s9", str(cm.exception))
        self.assertIn("huashu_clip", str(cm.exception))

    def test_premium_allow_native_opt_in(self):
        r = route({"id": "s2", "engine": "whiteboard", "narration": "x", "allow_native": True,
                   "native_reason": "diagram"}, PREMIUM, AVAIL_ALL)
        self.assertEqual(r["engine"], "whiteboard")

    def test_legacy_projects_keep_fallbacks(self):
        r = route({"id": "s3", "engine": "huashu_clip", "narration": "x"}, {"category": "history"}, AVAIL_ALL)
        self.assertIn("motion", r["fallbacks"])
        self.assertFalse(r["strict"])

    def test_manifest_silent_fallback_is_blocker_in_premium(self):
        m = {"status": "done", "engine": "motion", "requested_engine": "html_seek", "fallback_used": True,
             "attempts": [{"engine": "html_seek", "ok": False, "error": "TimeoutError"}]}
        prem = V.manifest_checks(m, premium=True)
        self.assertTrue(any(i.startswith("silent_fallback") for i in prem["issues"]))
        self.assertTrue(any(i.startswith("primitive_engine") for i in prem["issues"]))
        legacy = V.manifest_checks(m, premium=False)
        self.assertFalse(legacy["issues"])
        self.assertTrue(legacy["warnings"])

    def test_degradations_and_overflow(self):
        m = {"status": "done", "engine": "html_seek", "degradations": ["font Inter.woff2 missing -> fallback"],
             "layout": {"overflow": ["h1 '...' exceeds box by 40px"], "fonts": ["Inter"]}}
        r = V.manifest_checks(m, premium=True)
        self.assertTrue(any(i.startswith("degraded_dependency") for i in r["issues"]))
        self.assertTrue(any(i.startswith("overflow") for i in r["issues"]))
        self.assertEqual(r["fonts"], ["Inter"])

    def test_typography_system(self):
        t = V.typography_checks({"a": ["Inter", "Oswald"], "b": ["Comic Neue"]}, allowed=["Inter", "Oswald"])
        self.assertTrue(t["issues"])
        t2 = V.typography_checks({"a": ["A"], "b": ["B"], "c": ["C"], "d": ["D"]})
        self.assertTrue(t2["warnings"])


class DesignSystemTests(unittest.TestCase):
    def test_look_fills_engine_params_and_palette(self):
        from studio_lib import design_system as DS
        s = DS.apply_look({"id": "x", "look": "kinetic-type", "params": {"cues": []}})
        self.assertEqual(s["engine"], "huashu_clip")
        self.assertEqual(s["params"]["grammar"], "y5_kinetic_type")
        self.assertEqual(s["params"]["theme"]["bg"], DS.palette("paper")["bg"])
        self.assertNotIn("alert", s["params"]["theme"])

    def test_scene_values_win_and_unknown_look_fails(self):
        from studio_lib import design_system as DS
        s = DS.apply_look({"id": "x", "look": "data-editorial", "params": {"grammar": "y5_kinetic_type", "theme": "ink"}})
        self.assertEqual(s["params"], {"grammar": "y5_kinetic_type", "theme": "ink"})
        with self.assertRaises(KeyError):
            DS.apply_look({"id": "x", "look": "nope"})

    def test_every_look_uses_an_authentic_engine(self):
        from studio_lib import design_system as DS
        for name, lk in DS.load()["looks"].items():
            self.assertEqual(TIER[lk["engine"]], "authentic", name)


class AssetFingerprintTests(unittest.TestCase):
    def test_editing_a_page_module_changes_the_cache_key(self):
        import tempfile

        from studio_lib.render import asset_fingerprint
        with tempfile.TemporaryDirectory() as td:
            d = Path(td) / "pieces" / "film"
            (d / "node_modules").mkdir(parents=True)
            (d / "index.html").write_text("<script src=film.js></script>")
            (d / "film.js").write_text("a")
            sc = {"_project_dir": td, "params": {"page": "pieces/film/index.html"}}
            k1 = asset_fingerprint(sc)
            (d / "node_modules" / "x.js").write_text("ignored")
            self.assertEqual(asset_fingerprint(sc), k1)
            (d / "film.js").write_text("b")
            self.assertNotEqual(asset_fingerprint(sc), k1)
            self.assertIsNone(asset_fingerprint({"params": {"page": "lemo:styles/x/index.html"}}))


class PieceTimingTests(unittest.TestCase):
    def test_eras_follow_timeline_and_bridges_only_between_adjacent(self):
        from studio_lib import piece_timing
        P = {"piece": "pieces/crosshatch", "era": True}
        sc = [{"id": "a", "engine": "animate_piece", "params": dict(P)},
              {"id": "b", "engine": "huashu_clip", "params": {}},
              {"id": "c", "engine": "animate_piece", "params": dict(P)},
              {"id": "d", "engine": "animate_piece", "params": dict(P)}]
        tl = [{"id": "a", "frames": 300}, {"id": "b", "frames": 90}, {"id": "c", "frames": 150}, {"id": "d", "frames": 60}]
        out = piece_timing.assign(sc, tl, 30)
        self.assertEqual(len(out), 1)
        eras = sc[0]["params"]["timing"]["scenes"]
        self.assertEqual([(e["id"], e["start"], e["end"]) for e in eras], [("a", 0, 10), ("c", 10, 15), ("d", 15, 17)])
        self.assertEqual([e["bridge_next"] for e in eras], [False, True, False])
        self.assertEqual(sc[2]["params"]["offset"], 10)
        self.assertNotIn("timing", sc[1]["params"])

    def test_short_segments_keep_source_era(self):
        from studio_lib import piece_timing
        sc = [{"id": "short-1-01", "_source": "g13", "engine": "animate_piece", "params": {"piece": "p", "era": True}}]
        piece_timing.assign(sc, [{"id": "short-1-01", "frames": 60}], 30)
        self.assertEqual(sc[0]["params"]["era"], "g13")
        self.assertEqual(sc[0]["params"]["timing"]["scenes"][0]["id"], "g13")


if __name__ == "__main__":
    unittest.main()
