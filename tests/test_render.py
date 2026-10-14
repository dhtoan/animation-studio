"""Integration tests: real frames, real MP4s (16:9 and 9:16), audio mix, caching.

Requires ffmpeg (PATH, STUDIO_FFMPEG or imageio-ffmpeg). Uses the 'estimate'
TTS provider so it runs on any OS without a voice.
"""
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from studio_lib import audio as A  # noqa: E402
from studio_lib import ffmpeg as FF  # noqa: E402
from studio_lib.design import Theme  # noqa: E402
from studio_lib.engines import ENGINES, NATIVE, SceneContext  # noqa: E402
from studio_lib.tts import read_wav  # noqa: E402

SCENE = {"id": "t", "elements": [
    {"type": "text", "text": "Test", "style": "h1", "pos": [0.5, 0.2]},
    {"type": "icon", "name": "bank", "pos": [0.3, 0.6], "at": 0.1},
    {"type": "bar_chart", "box": [0.5, 0.4, 0.4, 0.5], "bars": [{"label": "a", "value": 1}, {"label": "b", "value": 2}], "at": 0.2},
    {"type": "character", "pos": [0.12, 0.95], "height": 0.4}],
    "params": {"layers": ["city"], "src": "img.png"}, "transition": "crossfade"}


class EngineFrameTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.td = Path(tempfile.mkdtemp())
        from PIL import Image, ImageDraw

        im = Image.new("RGB", (400, 300), "white")
        d = ImageDraw.Draw(im)
        d.ellipse((100, 50, 300, 250), outline="black", width=6)
        d.line((50, 280, 350, 280), fill="black", width=5)
        im.save(cls.td / "img.png")

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.td, ignore_errors=True)

    def test_every_native_engine_both_formats(self):
        for name in sorted(NATIVE):
            for (w, h) in ((320, 180), (180, 320)):
                sc = dict(SCENE, _project_dir=str(self.td))
                ctx = SceneContext(scene=sc, width=w, height=h, ss=1, fps=30, duration=3, theme=Theme(),
                                   words=[(0.2, "test"), (0.6, "words")])
                eng = ENGINES[name](ctx)
                a, b = eng.frame(0.5), eng.frame(2.5)
                self.assertEqual(a.size, (w, h), name)
                self.assertEqual(a.mode, "RGB")
                # frames must change over time (no static slideshow)
                self.assertNotEqual(a.tobytes(), b.tobytes(), f"{name} {w}x{h} static")

    def test_determinism(self):
        sc = dict(SCENE, _project_dir=str(self.td))
        frames = []
        for _ in range(2):
            ctx = SceneContext(scene=sc, width=320, height=180, ss=1, fps=30, duration=3, theme=Theme())
            frames.append(ENGINES["handdrawn"](ctx).frame(1.3).tobytes())
        self.assertEqual(frames[0], frames[1])


class EncodeTests(unittest.TestCase):
    def test_mp4_16x9_and_9x16(self):
        with tempfile.TemporaryDirectory() as td:
            for fmt, (w, h) in {"long": (320, 180), "short": (180, 320)}.items():
                out = Path(td) / f"{fmt}.mp4"
                ctx = SceneContext(scene=dict(SCENE, params={}), width=w, height=h, ss=1, fps=30, duration=1,
                                   theme=Theme())
                eng = ENGINES["motion"](ctx)
                fw = FF.FrameWriter(out, w, h, 30, crf=30, preset="ultrafast")
                for i in range(30):
                    fw.write(eng.frame(i / 30))
                fw.close()
                pr = FF.probe(out)
                self.assertEqual((pr.width, pr.height), (w, h))
                self.assertAlmostEqual(pr.fps, 30.0)
                self.assertEqual(FF.count_frames(out), 30)
                self.assertAlmostEqual(pr.duration, 1.0, delta=0.05)


class AudioTests(unittest.TestCase):
    def test_mix_length_and_ducking(self):
        import numpy as np
        from studio_lib.tts import write_wav

        with tempfile.TemporaryDirectory() as td:
            v = Path(td) / "v.wav"
            t = np.arange(24000 * 2) / 24000
            write_wav(v, (0.3 * np.sin(2 * np.pi * 220 * t)).astype("float32"), 24000)
            out = Path(td) / "mix.wav"
            info = A.mix(6.0, [(1.0, str(v))], [(0, 6, "tension")], [(0.5, "whoosh")], out)
            a, sr = read_wav(out)
            self.assertEqual(sr, 48000)
            self.assertAlmostEqual(len(a) / sr, 6.0, delta=0.01)
            self.assertLessEqual(float(np.max(np.abs(a))), 1.0)
            self.assertGreater(info["voice_peak"], 0)


class PipelineTests(unittest.TestCase):
    """Builds the mini fixture end to end with the placeholder voice, then checks caching."""

    def test_build_cache_and_qa(self):
        from studio_lib.pipeline import build_long
        from studio_lib.qa import run_qa
        from studio_lib.shorts import build_shorts

        with tempfile.TemporaryDirectory() as td:
            pdir = Path(td) / "mini"
            shutil.copytree(ROOT / "tests" / "fixtures" / "mini", pdir)
            pj = json.loads((pdir / "project.json").read_text(encoding="utf-8"))
            pj["voice"] = {"provider": "estimate"}
            (pdir / "project.json").write_text(json.dumps(pj), encoding="utf-8")
            quiet = lambda *a, **k: None  # noqa: E731
            r1 = build_long(pdir, "draft", workers=2, log=quiet)
            self.assertTrue(r1["assembled"])
            self.assertFalse(r1["narration_deliverable"])
            r2 = build_long(pdir, "draft", workers=2, log=quiet)
            self.assertTrue(all(s.get("cached") for s in r2["scenes"]), "second build must hit the scene cache")
            sh = build_shorts(pdir, "draft", workers=2, log=quiet)
            self.assertEqual(sh[0]["status"], "done")
            pr = FF.probe(sh[0]["output"])
            self.assertEqual((pr.width, pr.height), (540, 960))
            q = run_qa(pdir, "draft")
            self.assertEqual(q["checks"]["long_video"]["issues"], [])
            self.assertIn("narration is a placeholder (estimate provider) — not deliverable", q["summary"]["blockers"])


if __name__ == "__main__":
    unittest.main()
