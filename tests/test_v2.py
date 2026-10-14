"""V2: style registry, art direction, shot planning, continuity, cinematic transitions, router."""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from studio_lib import direction, styles  # noqa: E402
from studio_lib.design import Theme, spring_ease  # noqa: E402
from studio_lib.engines import ENGINES, SceneContext  # noqa: E402
from studio_lib.router import route  # noqa: E402

AVAIL = {k: {"ok": True} for k in ENGINES}


class RegistryTests(unittest.TestCase):
    def test_registry_entries_complete(self):
        ids = set()
        for s in styles.load():
            for k in ("id", "name", "engine", "source", "license", "description", "aspects", "deps", "params"):
                self.assertIn(k, s, s.get("id"))
            self.assertIn(s["engine"], ENGINES, s["id"])
            self.assertNotIn(s["id"], ids)
            ids.add(s["id"])

    def test_status_never_claims_unverified(self):
        v = styles.verification()
        for s in styles.load():
            st = styles.status(s["id"])
            if s["id"] not in v:
                self.assertEqual(st, "declared")
            else:
                self.assertEqual(st, "operational" if v[s["id"]].get("ok") else "failed")

    def test_apply_style_fills_engine_and_keeps_overrides(self):
        sc = {"id": "x", "engine": "auto", "art_style": "huashu.finance-chart", "params": {"theme": "dark"}}
        out = styles.apply_style(copy.deepcopy(sc))
        self.assertEqual(out["engine"], "huashu_clip")
        self.assertEqual(out["params"]["grammar"], "t3_finance_chart")
        self.assertEqual(out["params"]["theme"], "dark")
        with self.assertRaises(KeyError):
            styles.apply_style({"id": "y", "art_style": "nope"})


class DirectionTests(unittest.TestCase):
    def proj(self):
        return {"category": "business", "chapters": [{"id": "a", "mood": "tension"}, {"id": "b", "mood": "dark"}],
                "scenes": [{"id": "s1", "chapter": "a", "purpose": "hook", "engine": "kinetic"},
                           {"id": "s2", "chapter": "a", "purpose": "data", "engine": "motion", "camera": {"move": "static"}},
                           {"id": "s3", "chapter": "b", "purpose": "atmosphere", "engine": "artistic", "transition": "whip"}]}

    def test_plan_fills_only_missing(self):
        p = self.proj()
        log = direction.plan_shots(p)
        s1, s2, s3 = p["scenes"]
        self.assertEqual(s1["shot"]["type"], "insert")
        self.assertEqual(s1["camera"]["move"], "push_in")
        self.assertEqual(s2["camera"], {"move": "static"})  # explicit kept
        self.assertEqual(s3["transition"], "whip")            # explicit kept
        self.assertEqual(s2["transition"], "cut")
        self.assertTrue(any("s1: shot" in x for x in log))

    def test_chapter_break_gets_soft_transition(self):
        p = self.proj()
        del p["scenes"][2]["transition"]
        direction.plan_shots(p)
        self.assertIn(p["scenes"][2]["transition"], ("fade_black", "crossfade"))

    def test_continuity_flags(self):
        p = {"scenes": [{"id": f"s{i}", "engine": "motion", "chapter": "c", "purpose": "data",
                         "elements": [{"type": "stamp"}]} for i in range(5)]}
        c = direction.continuity(p)
        self.assertTrue(any("consecutive" in x for x in c["issues"]))
        self.assertTrue(any("impacts" in x for x in c["notes"]))

    def test_bible_has_lighting_per_chapter(self):
        b = direction.style_bible(self.proj())
        self.assertEqual(set(b["lighting_by_chapter"]), {"a", "b"})


class TransitionTests(unittest.TestCase):
    def test_cinematic_transitions_render(self):
        from PIL import Image

        prev = Image.new("RGB", (320, 180), (200, 30, 30))
        for kind in ("crash_zoom", "flash_cut", "iris", "blinds", "glitch", "light_leak"):
            sc = {"id": "t", "transition": {"type": kind, "dur": 0.6}, "elements": []}
            ctx = SceneContext(scene=sc, width=320, height=180, ss=1, fps=30, duration=2, theme=Theme(), prev_last=prev)
            eng = ENGINES["motion"](ctx)
            early, late = eng.frame(0.1), eng.frame(1.0)
            self.assertEqual(early.size, (320, 180), kind)
            self.assertNotEqual(early.tobytes(), late.tobytes(), kind)


class RouterV2Tests(unittest.TestCase):
    def test_landscape_only_engine_skipped_for_vertical(self):
        r = route({"engine": "html_seek", "narration": "x", "params": {}}, {"category": "business"}, AVAIL, aspect="9:16")
        self.assertNotEqual(r["engine"], "html_seek")
        r2 = route({"engine": "html_seek", "narration": "x", "params": {}}, {"category": "business"}, AVAIL, aspect="16:9")
        self.assertEqual(r2["engine"], "html_seek")

    def test_dense_scene_prefers_motion(self):
        s = {"engine": "auto", "purpose": "metaphor", "narration": "a b c",
             "elements": [{"type": "bar_chart", "bars": [{}] * 6}, {"type": "list", "items": [1, 2, 3]}]}
        self.assertEqual(route(s, {"category": "history"}, AVAIL)["engine"], "motion")


class SpringTests(unittest.TestCase):
    def test_spring_settles(self):
        self.assertAlmostEqual(spring_ease(2.0, "card"), 1.0, places=3)
        self.assertGreater(spring_ease(0.25, "playful"), 1.0)  # underdamped overshoot
        self.assertEqual(spring_ease(0, "title"), 0.0)


class ShowcaseSpecTests(unittest.TestCase):
    def test_showcase_validates(self):
        from studio_lib.spec import normalize, validate

        f = ROOT / "examples" / "v2-style-showcase" / "project.json"
        p = normalize(json.loads(f.read_text(encoding="utf-8")), f.parent)
        for s in p["scenes"]:
            styles.apply_style(s)
        errs, _ = validate(p)
        self.assertEqual(errs, [])


if __name__ == "__main__":
    unittest.main()
