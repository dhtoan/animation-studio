"""Unit tests for timeline, captions, routing, spec validation, migration and cues.

Run: python -m unittest discover -s tests -v   (from the skill root)
"""
import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from studio_lib import subtitles, timeline  # noqa: E402
from studio_lib.design import Theme  # noqa: E402
from studio_lib.engines import SceneContext  # noqa: E402
from studio_lib.migrate import migrate  # noqa: E402
from studio_lib.router import route  # noqa: E402
from studio_lib.spec import normalize, validate  # noqa: E402
from studio_lib.tts import estimate_words  # noqa: E402

AVAIL_ALL = {k: {"ok": True} for k in ("whiteboard", "handdrawn", "motion", "kinetic", "artistic", "image_whiteboard",
                                        "huashu_clip", "animate_piece", "html_seek")}


def fake_narr(scenes, wps=2.5):
    out = {}
    for s in scenes:
        n = len(s.get("narration", "").split())
        if n:
            d = n / wps
            out[s["id"]] = {"duration": d, "words": estimate_words(s["narration"], d)}
    return out


class TimelineTests(unittest.TestCase):
    def setUp(self):
        self.scenes = [{"id": f"s{i}", "narration": "word " * (10 + i), "pad": {"lead": 0.35, "tail": 0.55}}
                       for i in range(5)]

    def test_frames_are_whole_and_contiguous(self):
        tl = timeline.build(self.scenes, fake_narr(self.scenes), 30, 30)
        t = 0.0
        for r in tl["scenes"]:
            self.assertAlmostEqual(r["start"], t, places=3)
            self.assertEqual(r["frames"], round(r["duration"] * 30))
            self.assertAlmostEqual(r["duration"] * 30, r["frames"], places=6)
            t = r["end"]
        self.assertAlmostEqual(tl["total"], sum(r["frames"] for r in tl["scenes"]) / 30, places=3)

    def test_words_shifted_by_lead(self):
        tl = timeline.build(self.scenes, fake_narr(self.scenes), 30)
        self.assertAlmostEqual(tl["scenes"][0]["words"][0][0], 0.35, places=3)

    def test_target_status(self):
        tl = timeline.build(self.scenes, fake_narr(self.scenes), 30, target=1000, tolerance=0.05)
        self.assertEqual(tl["status"], "short")
        tl2 = timeline.build(self.scenes, fake_narr(self.scenes), 30, target=tl["total"], tolerance=0.05)
        self.assertEqual(tl2["status"], "ok")

    def test_fit_pads_only_holds(self):
        narr = fake_narr(self.scenes)
        base = timeline.build(self.scenes, narr, 30, target=40)
        fitted = timeline.build(self.scenes, narr, 30, target=40, tolerance=0.01, fit=True)
        self.assertGreater(fitted["total"], base["total"])
        for a, b in zip(base["scenes"], fitted["scenes"]):
            self.assertEqual(a["narration_duration"], b["narration_duration"])

    def test_min_duration(self):
        sc = [{"id": "x", "narration": "", "min_duration": 4.0}]
        tl = timeline.build(sc, {}, 30)
        self.assertEqual(tl["scenes"][0]["frames"], 120)


class SubtitleTests(unittest.TestCase):
    def test_chunks_valid(self):
        text = ("On a Monday morning in March, Corvane Logistics was worth one point four billion dollars. "
                "Its purple vans were parked on almost every street in forty American cities.")
        words = estimate_words(text, 9.0, 0.3)
        cues = subtitles.chunk(words, 10.0)
        self.assertGreaterEqual(len(cues), 2)
        srt_cues = [{**c, "text": subtitles.wrap2(c["text"])} for c in cues]
        self.assertEqual(subtitles.check(srt_cues, 10.0), [])
        for a, b in zip(cues, cues[1:]):
            self.assertLessEqual(a["end"], b["start"])

    def test_srt_roundtrip(self, tmp=None):
        import tempfile

        cues = [{"start": 0.5, "end": 2.25, "text": "Hello world."}, {"start": 3661.001, "end": 3662.0, "text": "Later."}]
        with tempfile.TemporaryDirectory() as td:
            p = Path(td) / "c.srt"
            subtitles.write_srt(cues, p)
            back = subtitles.parse_srt(p)
        self.assertEqual(len(back), 2)
        self.assertAlmostEqual(back[1]["start"], 3661.001, places=3)
        self.assertEqual(subtitles.srt_ts(3661.001), "01:01:01,001")

    def test_overlap_detected(self):
        bad = [{"start": 0, "end": 3, "text": "a"}, {"start": 2, "end": 4, "text": "b"}]
        self.assertTrue(any("overlaps" in i for i in subtitles.check(bad, 10)))


class CueTests(unittest.TestCase):
    def ctx(self, words):
        return SceneContext(scene={"id": "c"}, width=320, height=180, ss=1, fps=30, duration=10, theme=Theme(),
                            words=words)

    def test_resolve_forms(self):
        c = self.ctx([(1.0, "The"), (1.4, "company"), (2.0, "collapsed."), (5.0, "collapsed")])
        self.assertEqual(c.resolve_time(2.5), 2.5)
        self.assertEqual(c.resolve_time("50%"), 5.0)
        self.assertEqual(c.resolve_time("end-1.5"), 8.5)
        self.assertEqual(c.resolve_time("cue:collapsed"), 2.0)
        self.assertEqual(c.resolve_time("cue:collapsed#2"), 5.0)
        self.assertEqual(c.resolve_time("cue:missing", 0.7), 0.7)

    def test_hyphen_and_punctuation(self):
        c = self.ctx([(3.0, "Seventy-two"), (4.0, "$1.4B,")])
        self.assertEqual(c.resolve_time("cue:seventy-two"), 3.0)
        self.assertEqual(c.resolve_time("cue:$1.4B"), 4.0)


class RouterTests(unittest.TestCase):
    proj = {"category": "business"}

    def test_explicit_engine_wins_with_fallbacks(self):
        r = route({"engine": "huashu_clip", "narration": "x"}, self.proj, AVAIL_ALL)
        self.assertEqual(r["engine"], "huashu_clip")
        self.assertIn("motion", r["fallbacks"])

    def test_unavailable_falls_back(self):
        av = dict(AVAIL_ALL, huashu_clip={"ok": False})
        r = route({"engine": "huashu_clip", "narration": "x"}, self.proj, av)
        self.assertEqual(r["engine"], "motion")
        self.assertIn("huashu_clip", r["skipped_unavailable"])

    def test_auto_data_prefers_motion(self):
        s = {"engine": "auto", "purpose": "data", "narration": "Revenue rose.",
             "elements": [{"type": "bar_chart"}, {"type": "counter"}]}
        self.assertEqual(route(s, self.proj, AVAIL_ALL)["engine"], "motion")

    def test_auto_process_in_science_prefers_whiteboard(self):
        s = {"engine": "auto", "purpose": "process", "narration": "First this, then that.",
             "elements": [{"type": "icon"}, {"type": "arrow"}, {"type": "icon"}]}
        self.assertEqual(route(s, {"category": "science"}, AVAIL_ALL)["engine"], "whiteboard")

    def test_auto_image_prefers_image_whiteboard(self):
        s = {"engine": "auto", "purpose": "illustration", "narration": "Look.", "params": {"src": "a.png"}}
        self.assertEqual(route(s, self.proj, AVAIL_ALL)["engine"], "image_whiteboard")

    def test_every_route_has_a_fallback(self):
        for pur in ("hook", "explain", "data", "story", "metaphor", "cta"):
            r = route({"engine": "auto", "purpose": pur, "narration": "a b c"}, self.proj, AVAIL_ALL)
            self.assertTrue(r["fallbacks"], pur)


class SpecTests(unittest.TestCase):
    def test_demo_and_fixture_validate(self):
        for f in (ROOT / "examples" / "billion-dollar-collapse" / "project.json", ROOT / "tests" / "fixtures" / "mini" / "project.json"):
            p = normalize(json.loads(f.read_text(encoding="utf-8")), f.parent)
            errs, warns = validate(p)
            self.assertEqual(errs, [], f.name)

    def test_errors_detected(self):
        p = normalize({"slug": "x", "title": "x", "category": "nope", "target_duration": 60, "fictional": True,
                       "scenes": [{"id": "a", "narration": "hi", "engine": "bogus", "elements": [{"type": "zz"}]},
                                  {"id": "a", "narration": ""}]}, Path("."))
        errs, _ = validate(p)
        joined = "\n".join(errs)
        for needle in ("category", "disclaimer", "unknown engine", "unknown type", "duplicate id", "needs narration"):
            self.assertIn(needle, joined)


class SchemaTests(unittest.TestCase):
    def test_schema_catches_types(self):
        from studio_lib.jsonschema_lite import validate as sv

        schema = json.loads((ROOT / "schemas" / "project.schema.json").read_text(encoding="utf-8"))
        bad = {"slug": "Bad Slug", "title": "", "category": "x", "target_duration": -1, "scenes": [{"id": 3}]}
        errs = " | ".join(sv(bad, schema))
        for needle in ("$.slug", "$.title", "$.category", "$.target_duration", "$.scenes[0].id"):
            self.assertIn(needle, errs)

    def test_template_matches_schema(self):
        from studio_lib.jsonschema_lite import validate_file

        self.assertEqual(validate_file(ROOT / "templates" / "project.template.json", ROOT / "schemas" / "project.schema.json"), [])


class MigrationTests(unittest.TestCase):
    def test_v1_to_v2_is_additive(self):
        v1 = {"slug": "x", "scenes": [{"id": "a", "narration": "n", "intent": "data", "custom": 1}]}
        v2, log = migrate(copy.deepcopy(v1))
        self.assertEqual(v2["schema_version"], 2)
        self.assertEqual(v2["scenes"][0]["purpose"], "data")
        self.assertEqual(v2["scenes"][0]["custom"], 1)
        self.assertIn("validation", v2["scenes"][0])
        self.assertTrue(log)
        again, log2 = migrate(v2)
        self.assertEqual(log2, [])


if __name__ == "__main__":
    unittest.main()
