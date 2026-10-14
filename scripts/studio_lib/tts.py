"""Narration providers.

Every provider returns, per text: a mono WAV and word timings [(t_sec, word)].

  sapi      Windows System.Speech (local, offline, free). Word timings from
            SpeakProgress events. Voices: "Microsoft David Desktop", "Microsoft Zira Desktop".
  edge      `edge-tts` neural voices. Sends text to Microsoft's online service:
            requires `voice.allow_network: true` in project.json (opt-in).
  file      Your own recordings: audio/voice/<scene_id>.wav (timings estimated).
  estimate  Silent placeholder of estimated length (150 wpm). Drafts only;
            QA marks the output as NOT deliverable.

Optional providers we do not ship (no credentials, paid, or platform-bound):
ElevenLabs, VoxCPM2 (MLX), Volcengine. Add one by implementing `synth_many`.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

import numpy as np

SAPI_PS1 = r'''
param([string]$JobFile)
Add-Type -AssemblyName System.Speech
$code = @"
using System; using System.Speech.Synthesis; using System.Text; using System.Globalization;
public static class AunoSapi {
  public static string Run(string text, string wav, string voice, int rate) {
    var s = new SpeechSynthesizer();
    if (!String.IsNullOrEmpty(voice)) s.SelectVoice(voice);
    s.Rate = rate;
    var sb = new StringBuilder(); sb.Append("["); bool first = true;
    s.SpeakProgress += (o, e) => {
      if (!first) sb.Append(","); first = false;
      sb.Append("{\"t\":" + e.AudioPosition.TotalMilliseconds.ToString(CultureInfo.InvariantCulture)
        + ",\"pos\":" + e.CharacterPosition + ",\"len\":" + e.CharacterCount + "}");
    };
    s.SetOutputToWaveFile(wav, new System.Speech.AudioFormat.SpeechAudioFormatInfo(24000,
      System.Speech.AudioFormat.AudioBitsPerSample.Sixteen, System.Speech.AudioFormat.AudioChannel.Mono));
    s.Speak(text); s.SetOutputToNull(); s.Dispose();
    sb.Append("]"); return sb.ToString();
  }
}
"@
Add-Type -TypeDefinition $code -ReferencedAssemblies System.Speech
$jobs = Get-Content -Raw -Encoding UTF8 $JobFile | ConvertFrom-Json
foreach ($j in $jobs) {
  $text = [System.IO.File]::ReadAllText($j.text, [System.Text.Encoding]::UTF8)
  $json = [AunoSapi]::Run($text, $j.wav, $j.voice, [int]$j.rate)
  [System.IO.File]::WriteAllText($j.words, $json, (New-Object System.Text.UTF8Encoding($false)))
}
'''


ALIGN_VERSION = "pause-anchored-v1"


def wav_duration(path: Path) -> float:
    with wave.open(str(path)) as w:
        return w.getnframes() / w.getframerate()


def read_wav(path: Path) -> tuple[np.ndarray, int]:
    with wave.open(str(path)) as w:
        sr, ch, sw, n = w.getframerate(), w.getnchannels(), w.getsampwidth(), w.getnframes()
        raw = w.readframes(n)
    if sw != 2:
        raise ValueError(f"{path}: only 16-bit PCM supported")
    a = np.frombuffer(raw, dtype="<i2").astype("float32") / 32768.0
    if ch > 1:
        a = a.reshape(-1, ch).mean(axis=1)
    return a, sr


def write_wav(path: Path, data: np.ndarray, sr: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    d = np.clip(data, -1, 1)
    ch = 1 if d.ndim == 1 else d.shape[1]
    with wave.open(str(path), "wb") as w:
        w.setnchannels(ch)
        w.setsampwidth(2)
        w.setframerate(sr)
        w.writeframes((d * 32767).astype("<i2").tobytes())


def _tokens(text: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(0)) for m in re.finditer(r"\S+", text)]


def estimate_words(text: str, duration: float, lead: float = 0.0) -> list[tuple[float, str]]:
    """Distribute words over a duration by character weight (used when no timings exist)."""
    toks = _tokens(text)
    if not toks:
        return []
    weights = [len(w) + 2 + (4 if re.search(r"[.,;:!?]$", w) else 0) for _, w in toks]
    total = sum(weights)
    out, acc = [], 0.0
    for (_, w), wt in zip(toks, weights):
        out.append((lead + duration * acc / total, w))
        acc += wt
    return out


def speech_segments(a: np.ndarray, sr: int, thr: float = 0.012, min_gap: float = 0.16) -> list[tuple[float, float]]:
    """Voiced segments [(start, end)] from a 10 ms RMS envelope."""
    hop = int(sr * 0.01)
    n = len(a) // hop
    if n == 0:
        return []
    env = np.sqrt(np.mean(a[: n * hop].reshape(n, hop) ** 2, axis=1))
    voiced = env > thr
    segs, start, silent = [], None, 0
    for i, v in enumerate(voiced):
        if v:
            if start is None:
                start = i
            silent = 0
        elif start is not None:
            silent += 1
            if silent * 0.01 >= min_gap:
                segs.append((start * 0.01, (i - silent + 1) * 0.01))
                start, silent = None, 0
    if start is not None:
        segs.append((start * 0.01, (n - silent) * 0.01))
    return segs


def align_words(words: list[tuple[float, str]], wav: Path) -> tuple[list[tuple[float, str]], dict]:
    """Map word times onto the actual audio.

    SAPI's SpeakProgress positions are monotonic but not in the WAV's time base
    (measured 1.33–1.47x too long here). We fit them linearly to the voiced span,
    then snap words that follow punctuation to the real pauses in the waveform
    and interpolate piecewise-linearly between those anchors.
    """
    if not words:
        return words, {"method": "none"}
    a, sr = read_wav(wav)
    segs = speech_segments(a, sr)
    if not segs:
        return words, {"method": "no-speech"}
    onset, end = segs[0][0], segs[-1][1]
    t = np.array([w[0] for w in words], dtype="float64")
    last_len = 0.12 + 0.065 * len(re.sub(r"\W", "", words[-1][1]))
    span_raw = max(1e-6, t[-1] - t[0])
    k = max(1e-6, (end - last_len - onset)) / span_raw
    lin = onset + (t - t[0]) * k
    # anchors: speech starts after pauses, matched to words following punctuation
    starts = [s for s, _ in segs[1:]]
    anchors = [(0, onset)]
    for i in range(1, len(words)):
        if re.search(r"[.,;:!?—]$", words[i - 1][1]) and starts:
            j = int(np.argmin([abs(s - lin[i]) for s in starts]))
            if abs(starts[j] - lin[i]) < 0.7 and starts[j] > anchors[-1][1] + 0.05:
                anchors.append((i, starts[j]))
    anchors.append((len(words) - 1, max(anchors[-1][1] + 0.05, end - last_len)) if anchors[-1][0] != len(words) - 1
                   else anchors[-1])
    out = lin.copy()
    for (i0, a0), (i1, a1) in zip(anchors, anchors[1:]):
        if i1 == i0:
            continue
        r0, r1 = t[i0], t[i1]
        for i in range(i0, i1 + 1):
            out[i] = a0 + (a1 - a0) * ((t[i] - r0) / max(1e-6, r1 - r0))
    return [(round(float(x), 3), w) for x, (_, w) in zip(out, words)], \
        {"method": "pause-anchored", "anchors": len(anchors), "scale": round(1 / k, 3), "speech": [onset, end]}


class Provider:
    name = "base"
    deliverable = True

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def key(self, text: str) -> str:
        h = hashlib.sha256(json.dumps([self.name, self.cfg.get("voice"), self.cfg.get("rate", 0), text,
                                       ALIGN_VERSION]).encode())
        return h.hexdigest()[:16]

    def synth_many(self, items: list[tuple[str, Path, Path]]) -> None:
        """items: (text, wav_out, words_json_out)."""
        raise NotImplementedError

    @staticmethod
    def available() -> tuple[bool, str]:
        return True, ""


class SapiProvider(Provider):
    name = "sapi"

    @staticmethod
    def available():
        if sys.platform != "win32":
            return False, "Windows only"
        if not shutil.which("powershell"):
            return False, "powershell not found"
        return True, ""

    def synth_many(self, items):
        if not items:
            return
        with tempfile.TemporaryDirectory() as td:
            td = Path(td)
            ps1 = td / "sapi.ps1"
            ps1.write_text(SAPI_PS1, encoding="utf-8")
            jobs = []
            for i, (text, wav, words) in enumerate(items):
                tf = td / f"t{i}.txt"
                tf.write_text(text, encoding="utf-8")
                jobs.append({"text": str(tf), "wav": str(wav), "words": str(words) + ".raw",
                             "voice": self.cfg.get("voice", "Microsoft David Desktop"),
                             "rate": int(self.cfg.get("rate", 0))})
                wav.parent.mkdir(parents=True, exist_ok=True)
            jf = td / "jobs.json"
            jf.write_text(json.dumps(jobs), encoding="utf-8")
            cp = subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1),
                                 "-JobFile", str(jf)], capture_output=True, text=True, encoding="utf-8",
                                errors="replace")
            if cp.returncode != 0:
                raise RuntimeError(f"SAPI failed: {cp.stderr[-1500:]}")
        for text, wav, words in items:
            raw = json.loads(Path(str(words) + ".raw").read_text(encoding="utf-8-sig"))
            Path(str(words) + ".raw").unlink()
            out = []
            for ev in raw:
                w = text[ev["pos"]: ev["pos"] + ev["len"]]
                if w.strip():
                    out.append((ev["t"] / 1000.0, w))
            # attach trailing punctuation from source text so captions read naturally
            toks = _tokens(text)
            merged = []
            ti = 0
            for t, w in out:
                while ti < len(toks) and not toks[ti][1].lower().startswith(w.lower()[:1]):
                    ti += 1
                if ti < len(toks):
                    merged.append((t, toks[ti][1]))
                    ti += 1
                else:
                    merged.append((t, w))
            aligned, info = align_words(merged, wav)
            words.write_text(json.dumps({"provider": self.name, "words": aligned, "alignment": info}), encoding="utf-8")


class EdgeProvider(Provider):
    name = "edge"

    @staticmethod
    def available():
        try:
            import edge_tts  # noqa: F401
        except Exception:
            return False, "pip install edge-tts"
        return True, "network: sends narration text to Microsoft's online TTS service"

    def synth_many(self, items):
        if not self.cfg.get("allow_network"):
            raise RuntimeError("edge TTS sends text to an online service; set voice.allow_network=true to opt in")
        import asyncio

        import edge_tts
        from . import ffmpeg as FF

        async def one(text, wav, words):
            comm = edge_tts.Communicate(text, self.cfg.get("voice", "en-US-AndrewNeural"),
                                        rate=self.cfg.get("edge_rate", "+0%"), boundary="WordBoundary")
            mp3 = wav.with_suffix(".mp3")
            out = []
            with open(mp3, "wb") as f:
                async for ch in comm.stream():
                    if ch["type"] == "audio":
                        f.write(ch["data"])
                    elif ch["type"] == "WordBoundary":
                        out.append((ch["offset"] / 1e7, ch["text"]))
            FF.run(["-y", "-i", str(mp3), "-ac", "1", "-ar", "24000", str(wav)])
            mp3.unlink()
            words.write_text(json.dumps({"provider": self.name, "words": out}), encoding="utf-8")

        async def main():
            for it in items:
                await one(*it)

        asyncio.run(main())


class FileProvider(Provider):
    name = "file"

    def synth_many(self, items):
        raise RuntimeError("file provider: place recordings at audio/voice/<scene_id>.wav (handled by pipeline)")


class EstimateProvider(Provider):
    name = "estimate"
    deliverable = False

    def synth_many(self, items):
        for text, wav, words in items:
            n = len(text.split())
            dur = max(1.0, n / 2.5 + 0.3)
            write_wav(wav, np.zeros(int(24000 * dur), dtype="float32"), 24000)
            words.write_text(json.dumps({"provider": self.name, "words": estimate_words(text, dur - 0.3)}),
                             encoding="utf-8")


PROVIDERS = {"sapi": SapiProvider, "edge": EdgeProvider, "file": FileProvider, "estimate": EstimateProvider}


def provider_report() -> dict:
    return {k: dict(zip(("ok", "note"), v.available())) for k, v in PROVIDERS.items()}


def synthesize(texts: dict[str, str], cfg: dict, cache_dir: Path, voice_dir: Path | None = None,
               log=print) -> dict[str, dict]:
    """texts: {key_id: text}. Returns {key_id: {wav, words, duration, provider, deliverable, cached}}."""
    pname = cfg.get("provider", "sapi")
    prov = PROVIDERS[pname](cfg)
    ok, note = prov.available()
    if not ok:
        raise RuntimeError(f"TTS provider '{pname}' unavailable: {note}")
    out, todo = {}, []
    for kid, text in texts.items():
        if pname == "file":
            src = (voice_dir or cache_dir) / f"{kid}.wav"
            if not src.exists():
                raise FileNotFoundError(f"file provider: missing recording {src}")
            d = wav_duration(src)
            aligned, _ = align_words(estimate_words(text, d), src)
            out[kid] = {"wav": str(src), "words": aligned, "duration": d, "provider": "file",
                        "deliverable": True, "cached": True, "timing": "pause-aligned estimate"}
            continue
        k = prov.key(text)
        wav = cache_dir / f"{k}.wav"
        words = cache_dir / f"{k}.words.json"
        out[kid] = {"wav": str(wav), "words_file": str(words), "key": k}
        if not (wav.exists() and words.exists()):
            todo.append((text, wav, words))
    if todo:
        log(f"[tts] synthesizing {len(todo)} narration clips with '{pname}' ...")
        # de-duplicate identical texts
        seen = {}
        for it in todo:
            seen.setdefault(str(it[1]), it)
        prov.synth_many(list(seen.values()))
    for kid, rec in out.items():
        if "words_file" in rec:
            w = json.loads(Path(rec["words_file"]).read_text(encoding="utf-8"))
            rec["words"] = [tuple(x) for x in w["words"]]
            rec["duration"] = wav_duration(Path(rec["wav"]))
            rec["provider"] = pname
            rec["deliverable"] = prov.deliverable
            rec["timing"] = {"sapi": "events aligned to audio pauses", "edge": "service word boundaries"}.get(pname, "estimated")
            rec["cached"] = not any(str(t[1]) == rec["wav"] for t in todo)
    return out
