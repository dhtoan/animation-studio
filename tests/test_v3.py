"""V3: niche scoring, RPM honesty, analytics, audience, history, story, dubbing fit, voice engine, map/archival."""
import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from studio_lib import analytics, audience, history, niche, story, voice, youtube_api  # noqa: E402
from studio_lib.design import Theme, contrast_ratio, ensure_contrast  # noqa: E402
from studio_lib.engines import ENGINES, SceneContext  # noqa: E402


def cand(**factors):
    return {"title": "x", "factors": factors}


class NicheTests(unittest.TestCase):
    def test_missing_factors_excluded_and_lower_confidence(self):
        fx = {f: {"score": 8, "evidence": ["e1"]} for f in niche.DEFAULT_WEIGHTS}
        fx["revenue_evidence"] = {"score": 8, "evidence": ["e1"], "category": "verified"}
        full = niche.score_candidate(cand(**fx))
        no_cat = niche.score_candidate(cand(revenue_evidence={"score": 8, "evidence": ["e1"]}))
        self.assertEqual(no_cat["breakdown"]["revenue_evidence"]["score"], 0)  # unknown category -> 0
        part = niche.score_candidate(cand(demand={"score": 8, "evidence": ["e1"]}))
        self.assertEqual(full["score"], 80.0)
        self.assertEqual(part["score"], 80.0)  # not imputed: score on covered factors only
        self.assertLess(part["confidence"], full["confidence"])
        self.assertIn("audience_fit_us50", part["missing"])

    def test_revenue_category_caps_score(self):
        r = niche.score_candidate(cand(revenue_evidence={"score": 9, "category": "industry-estimate", "evidence": ["e1"]}))
        self.assertEqual(r["breakdown"]["revenue_evidence"]["score"], 4)
        self.assertTrue(any("capped" in p for p in r["problems"]))

    def test_unevidenced_factor_rejected(self):
        r = niche.score_candidate(cand(demand={"score": 9}))
        self.assertIn("demand", r["problems"][0])
        self.assertIsNone(r["score"])

    def test_unknown_evidence_flagged(self):
        r = niche.rank([cand(demand={"score": 5, "evidence": ["nope"]})], evidence=[{"id": "e1"}])
        self.assertTrue(r[0]["result"]["problems"])

    def test_pillar_scope_lowers_confidence(self):
        a = niche.score_candidate(cand(demand={"score": 5, "evidence": ["e1"]}))
        b = niche.score_candidate(cand(demand={"score": 5, "evidence": ["e1"], "evidence_scope": "pillar"}))
        self.assertLess(b["confidence"], a["confidence"])

    def test_revenue_scenarios_require_labelled_assumptions(self):
        with self.assertRaises(ValueError):
            niche.revenue_scenarios([1000], {"low": 2.0}, "")
        rows = niche.revenue_scenarios([100000], {"assumed": 5.0}, "user assumption")
        self.assertEqual(rows[0]["estimated_revenue_usd"], 500.0)
        self.assertIn("ASSUMPTION", rows[0]["note"])

    def test_example_research_ranks(self):
        ev = json.loads((ROOT / "examples" / "niche-research" / "evidence.json").read_text(encoding="utf-8"))["evidence"]
        cands = json.loads((ROOT / "examples" / "niche-research" / "candidates.json").read_text(encoding="utf-8"))["candidates"]
        self.assertGreaterEqual(len(cands), 20)
        ranked = niche.rank(cands, None, ev)
        self.assertTrue(all(not c["result"]["problems"] for c in ranked), [c["result"]["problems"] for c in ranked][:3])
        rm = niche.roadmap(ranked)
        self.assertEqual(rm["near_duplicates"], [])
        self.assertTrue(all(e["publish_long"] for e in rm["calendar_90d"]))

    def test_near_duplicates(self):
        d = niche.near_duplicates(["The rise and fall of Studebaker", "Studebaker: the rise and fall", "Camp Century"])
        self.assertEqual(len(d), 1)


class YouTubeAPITests(unittest.TestCase):
    def test_outlier_median_baseline(self):
        self.assertEqual(youtube_api.outlier_ratio(15000, [1000, 1200, 800, 900, 1100]), 15.0)
        self.assertIsNone(youtube_api.outlier_ratio(15000, [1000, 1200]))  # too few uploads
        self.assertIsNone(youtube_api.outlier_ratio(None, [1] * 6))

    def test_rpm_none_without_views(self):
        self.assertIsNone(youtube_api.rpm(10.0, 0))
        self.assertIsNone(youtube_api.rpm(None, 1000))
        self.assertEqual(youtube_api.rpm(540, 120000), 4.5)

    def test_shorts_and_duration(self):
        self.assertEqual(youtube_api.iso_duration("PT2M59S"), 179)
        self.assertEqual(youtube_api.iso_duration("P1DT2H"), 93600)
        self.assertTrue(youtube_api.is_short(179))
        self.assertFalse(youtube_api.is_short(600))

    def test_window_lag(self):
        import datetime as dt

        self.assertEqual(youtube_api.analytics_window(28, 3, dt.date(2026, 10, 14)), ("2026-09-14", "2026-10-11"))

    def test_quota_budget_and_region(self):
        urls = []
        api = youtube_api.DataAPI(key="TESTKEY", budget=150, opener=lambda u: (urls.append(u), b'{"items": []}')[1])
        api.search("ghost army", "2026-01-01T00:00:00Z")
        self.assertIn("regionCode=US", urls[0])
        self.assertIn("relevanceLanguage=en", urls[0])
        with self.assertRaises(youtube_api.QuotaExceeded):
            api.search("again", "2026-01-01T00:00:00Z")

    def test_analytics_disabled_without_token(self):
        with mock.patch.dict("os.environ", {}, clear=True):
            with self.assertRaises(RuntimeError):
                youtube_api.AnalyticsAPI()


class AnalyticsTests(unittest.TestCase):
    def _csv(self, path, rows):
        with open(path, "w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows(rows)

    def test_progress_from_exports(self):
        with tempfile.TemporaryDirectory() as td:
            d = Path(td)
            self._csv(d / "geography.csv", [{"country": "US", "views": 800}, {"country": "CA", "views": 200}])
            self._csv(d / "demographics_us.csv", [{"ageGroup": "age55-64", "gender": "male", "viewerPercentage": 30},
                                                 {"ageGroup": "age65-", "gender": "female", "viewerPercentage": 30},
                                                 {"ageGroup": "age45-54", "gender": "male", "viewerPercentage": 40}])
            r = analytics.summarize_exports(d)
        self.assertEqual(r["progress"]["us_view_share"], 0.8)
        self.assertAlmostEqual(r["progress"]["us_55plus_share_of_us"], 0.6)
        self.assertAlmostEqual(r["progress"]["estimated_us55plus_share_of_all_views"], 0.48)
        self.assertIn("impressions", r["unavailable_metrics"][0])

    def test_missing_demographics_not_zero(self):
        self.assertFalse(analytics.demographics_from_rows([])["available"])
        self.assertEqual(analytics.progress(0.9, {"available": False})["status"], "insufficient data")


class AudienceTests(unittest.TestCase):
    def test_contrast_autocorrection(self):
        amber, paper = (196, 134, 45), (239, 228, 207)
        self.assertLess(contrast_ratio(amber, paper), 4.5)
        fixed = ensure_contrast(amber, paper)
        self.assertGreaterEqual(contrast_ratio(fixed, paper), 4.5)

    def test_audit_flags_small_long_text_and_pace(self):
        p = {"theme": "history", "category": "history", "scenes": [
            {"id": "a", "engine": "motion", "narration": "word " * 300,
             "elements": [{"type": "text", "style": "label", "text": "a long label that is far too small"}]}]}
        tl = {"total": 60, "scenes": [{"id": "a", "duration": 60, "narration_duration": 60}]}
        r = audience.audit(p, tl)
        joined = " ".join(r["issues"])
        self.assertIn("long text", joined)
        self.assertIn("300.0 wpm", joined)
        self.assertIn("no dates on screen", joined)


class HistoryStoryTests(unittest.TestCase):
    def test_ledger_classes_and_tiers(self):
        d = {"sources": [{"id": "S1", "url": "https://www.govinfo.gov/x", "title": "PL", "published": "2022"},
                         {"id": "S2", "url": "https://example.blog/x", "title": "blog"}],
             "claims": [{"id": "C1", "claim": "a", "status": "established", "source_ids": ["S1"]},
                        {"id": "C2", "claim": "b", "status": "contested", "source_ids": ["S2"]},
                        {"id": "C3", "claim": "c", "status": "reconstruction", "source_ids": ["S2"]}]}
        led = history.ledger_from_dossier(d, "2026-10-14")["facts"]
        self.assertEqual([f["status"] for f in led], ["verified", "contested", "illustrative"])
        self.assertEqual(led[0]["sources"][0]["tier"], 1)
        self.assertEqual(led[1]["sources"][0]["tier"], 4)
        self.assertIn("framing", led[1])

    def test_story_plan_and_check(self):
        pl = story.plan(20)
        self.assertAlmostEqual(sum(r["seconds"] for r in pl["sections"]), 1200, delta=5)
        bad = story.check({"scenes": [{"id": "a", "purpose": "explain", "narration": "x"}]})
        self.assertEqual(len(bad["issues"]), 3)

    def test_ghost_army_demo_passes_gates(self):
        from studio_lib import research
        from studio_lib.spec import normalize, validate

        base = ROOT / "examples" / "ghost-army"
        p = normalize(json.loads((base / "project.json").read_text(encoding="utf-8")), base)
        errs, _ = validate(p)
        self.assertEqual(errs, [])
        d = json.loads((base / "research" / "dossier.json").read_text(encoding="utf-8"))
        facts = history.ledger_from_dossier(d, "2026-10-14")["facts"]
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "research").mkdir()
            (Path(td) / "research" / "facts.json").write_text(json.dumps({"facts": facts}), encoding="utf-8")
            g = research.gate(p, Path(td))
        self.assertEqual(g["blockers"], [])
        self.assertEqual(story.check(p)["issues"], [])


class VoiceEngineTests(unittest.TestCase):
    def test_auto_never_picks_unverified_elevenlabs(self):
        with mock.patch.object(voice, "provider_status", return_value={}):
            r = voice.resolve({"mode": "auto", "elevenlabs": {"approved": True}}, "en-US")
        self.assertNotEqual(r["mode"], "elevenlabs")

    def test_auto_needs_project_approval(self):
        with mock.patch.object(voice, "provider_status", return_value={"elevenlabs": {"verified": True}}):
            r = voice.resolve({"mode": "auto"}, "en-US")
            self.assertNotEqual(r["mode"], "elevenlabs")
            r2 = voice.resolve({"mode": "auto", "elevenlabs": {"approved": True, "voice_id": "v1"}}, "en-US")
            self.assertEqual(r2["mode"], "elevenlabs")

    def test_explicit_elevenlabs_without_verification_errors(self):
        with mock.patch.object(voice, "provider_status", return_value={}):
            with self.assertRaises(RuntimeError):
                voice.resolve({"mode": "elevenlabs"}, "en-US")

    def test_per_language_override_and_default_voices(self):
        r = voice.resolve({"mode": "edge-tts", "languages": {"es": {"voice": "es-ES-AlvaroNeural", "rate": "+4%"}}}, "es")
        self.assertEqual((r["voice"], r["rate"]), ("es-ES-AlvaroNeural", "+4%"))
        self.assertEqual(voice.resolve({"mode": "edge-tts"}, "ja")["voice"], "ja-JP-KeitaNeural")

    def test_cache_key_changes_with_settings(self):
        a = voice.request_key({"mode": "edge-tts", "voice": "v", "rate": "-5%"}, "hello")
        b = voice.request_key({"mode": "edge-tts", "voice": "v", "rate": "+5%"}, "hello")
        self.assertNotEqual(a, b)

    def test_usage_log_and_quota_guard(self):
        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td)
            voice.log_usage(pdir, {"mode": "elevenlabs", "voice": "v"}, [("k", "x" * 900)], cached=2)
            data = json.loads((pdir / "reports" / "voice-usage.json").read_text(encoding="utf-8"))
            self.assertEqual(data["totals"]["elevenlabs"]["characters"], 900)
            with mock.patch.object(voice, "provider_status",
                                   return_value={"elevenlabs": {"verified": True, "quota_characters": 1000,
                                                                "used_characters_at_verification": 50}}):
                with self.assertRaises(RuntimeError):
                    voice.elevenlabs_jobs(pdir, {"s1": "y" * 200}, {"mode": "elevenlabs", "voice": "v"}, "en-US")


class DubbingTests(unittest.TestCase):
    def test_glossary_and_numbers(self):
        from studio_lib.dubbing import glossary_check

        src = {"s1": "The Ghost Army landed in 1944."}
        issues = glossary_check(src, {"s1": "El ejército llegó en 1945."}, [{"term": "Ghost Army", "es": "Ejército Fantasma"}], "es")
        self.assertTrue(any("glossary" in i for i in issues))
        self.assertTrue(any("1944" in i for i in issues))
        self.assertEqual(glossary_check(src, {}, [], "es", partial=True), [])


class MapArchivalTests(unittest.TestCase):
    def test_map_and_archival_render(self):
        geo = {"type": "FeatureCollection", "features": [
            {"type": "Feature", "properties": {"NAME": "Testland"},
             "geometry": {"type": "Polygon", "coordinates": [[[0, 40], [10, 40], [10, 50], [0, 50], [0, 40]]]}}]}
        with tempfile.TemporaryDirectory() as td:
            (Path(td) / "g.geojson").write_text(json.dumps(geo), encoding="utf-8")
            sc = {"id": "m", "_project_dir": td, "elements": [
                {"type": "map", "geojson": "g.geojson", "bounds": [-5, 35, 15, 55], "highlight": [{"name": "Testland"}],
                 "markers": [{"lon": 5, "lat": 45, "label": "Here", "at": 0.2}],
                 "routes": [{"path": [[0, 40], [10, 50]], "at": 0.3, "dur": 1.0}]}]}
            for eng in ("motion", "archival"):
                ctx = SceneContext(scene=dict(sc), width=320, height=180, ss=1, fps=30, duration=3, theme=Theme("history"))
                e = ENGINES[eng](ctx)
                a, b = e.frame(0.1), e.frame(2.0)
                self.assertNotEqual(a.tobytes(), b.tobytes(), eng)


if __name__ == "__main__":
    unittest.main()
