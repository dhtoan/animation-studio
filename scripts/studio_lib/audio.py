"""Procedural music bed, sound effects and the final mix (numpy only).

All music and SFX are synthesised here from oscillators and noise, so they are
original to each render and carry no third-party licence. Mix = narration +
music (side-chain ducked under the voice) + SFX, soft-limited. Loudness is
normalised to YouTube's -14 LUFS reference by ffmpeg `loudnorm` at mux time.
"""
from __future__ import annotations

import math
from pathlib import Path

import numpy as np

from .tts import read_wav, write_wav

SR = 48000

# chord progressions (semitones from A2) per mood
MOODS = {
    "tension": {"chords": [[0, 3, 7], [-4, 0, 3], [-2, 2, 5], [-5, -1, 2]], "bpm": 64, "pulse": 0.35, "bright": 0.4},
    "wonder": {"chords": [[0, 4, 7], [5, 9, 12], [-3, 0, 4], [7, 11, 14]], "bpm": 72, "pulse": 0.15, "bright": 0.7},
    "dark": {"chords": [[0, 3, 7], [1, 5, 8], [-2, 1, 5], [0, 3, 6]], "bpm": 56, "pulse": 0.45, "bright": 0.25},
    "resolve": {"chords": [[0, 4, 7], [-3, 0, 4], [5, 9, 12], [7, 11, 14]], "bpm": 68, "pulse": 0.1, "bright": 0.8},
    "drive": {"chords": [[0, 3, 7], [-4, 0, 3], [3, 7, 10], [-2, 2, 5]], "bpm": 92, "pulse": 0.6, "bright": 0.55},
}


def _hz(semi: float, base: float = 110.0) -> float:
    return base * 2 ** (semi / 12)


def music_segment(dur: float, mood: str, seed: int = 0) -> np.ndarray:
    m = MOODS.get(mood, MOODS["tension"])
    n = int(dur * SR)
    t = np.arange(n, dtype="float32") / SR
    out = np.zeros(n, dtype="float32")
    beat = 60.0 / m["bpm"]
    bar = beat * 4
    rng = np.random.default_rng(seed)
    nb = int(math.ceil(dur / bar)) + 1
    for b in range(nb):
        chord = m["chords"][b % len(m["chords"])]
        t0 = b * bar
        i0, i1 = int(t0 * SR), min(n, int((t0 + bar * 1.15) * SR))
        if i0 >= n:
            break
        tt = t[i0:i1] - t0
        env = np.minimum(1, tt / 1.2) * np.exp(-np.maximum(0, tt - bar) * 3)
        for k, semi in enumerate(chord):
            f = _hz(semi)
            det = 1 + (rng.random() - 0.5) * 0.004
            pad = (np.sin(2 * np.pi * f * tt * det) + 0.35 * np.sin(2 * np.pi * 2 * f * tt)
                   + 0.12 * m["bright"] * np.sin(2 * np.pi * 3 * f * tt))
            out[i0:i1] += pad * env * 0.06
        # bass root
        out[i0:i1] += np.sin(2 * np.pi * _hz(chord[0] - 12) * tt) * env * 0.08
    # heartbeat-like pulse for tension
    if m["pulse"] > 0:
        for k in range(int(dur / beat) + 1):
            i0 = int(k * beat * SR)
            L = min(n - i0, int(0.25 * SR))
            if L <= 0:
                break
            tt = np.arange(L) / SR
            out[i0:i0 + L] += np.sin(2 * np.pi * 52 * tt) * np.exp(-tt * 18) * 0.18 * m["pulse"]
    # gentle shimmer
    shimmer = np.sin(2 * np.pi * _hz(m["chords"][0][2] + 24) * t) * (0.5 + 0.5 * np.sin(2 * np.pi * t / 7.3))
    out += shimmer * 0.008 * m["bright"]
    return out


def sfx(name: str) -> np.ndarray:
    rng = np.random.default_rng(abs(hash(name)) % 1000)
    if name == "whoosh":
        L = int(0.55 * SR)
        tt = np.arange(L) / SR
        noise = rng.normal(0, 1, L).astype("float32")
        env = np.sin(np.pi * np.clip(tt / 0.55, 0, 1)) ** 2
        # sweep by mixing progressively smoothed noise
        lo = np.convolve(noise, np.ones(40) / 40, mode="same")
        hi = noise - lo
        mix = lo * (1 - tt / 0.55) + hi * (tt / 0.55) * 0.5
        return (mix * env * 0.35).astype("float32")
    if name in ("thud", "stamp"):
        L = int(0.5 * SR)
        tt = np.arange(L) / SR
        body = np.sin(2 * np.pi * (70 - 30 * tt) * tt) * np.exp(-tt * 9)
        click = rng.normal(0, 1, L) * np.exp(-tt * 80) * 0.4
        return ((body + click) * 0.7).astype("float32")
    if name == "pop":
        L = int(0.15 * SR)
        tt = np.arange(L) / SR
        return (np.sin(2 * np.pi * (600 - 1800 * tt) * tt) * np.exp(-tt * 40) * 0.3).astype("float32")
    if name == "tick":
        L = int(0.05 * SR)
        tt = np.arange(L) / SR
        return (np.sin(2 * np.pi * 2200 * tt) * np.exp(-tt * 120) * 0.15).astype("float32")
    if name == "riser":
        L = int(2.0 * SR)
        tt = np.arange(L) / SR
        f = 200 + 600 * (tt / 2.0) ** 2
        return (np.sin(2 * np.pi * np.cumsum(f) / SR) * (tt / 2.0) ** 2 * 0.15
                + rng.normal(0, 1, L) * (tt / 2.0) ** 3 * 0.06).astype("float32")
    if name == "impact":
        L = int(1.6 * SR)
        tt = np.arange(L) / SR
        return ((np.sin(2 * np.pi * 45 * tt) * np.exp(-tt * 2.5) + rng.normal(0, 1, L) * np.exp(-tt * 12) * 0.3)
                * 0.6).astype("float32")
    if name == "cash":
        L = int(0.4 * SR)
        tt = np.arange(L) / SR
        return (sum(np.sin(2 * np.pi * f * tt) for f in (1568, 2093, 2637)) * np.exp(-tt * 9) * 0.08).astype("float32")
    return np.zeros(1, dtype="float32")


def _resample(a: np.ndarray, sr: int) -> np.ndarray:
    if sr == SR:
        return a
    n = int(len(a) * SR / sr)
    return np.interp(np.linspace(0, len(a) - 1, n), np.arange(len(a)), a).astype("float32")


def mix(total: float, voice: list[tuple[float, str]], music_plan: list[tuple[float, float, str]],
        sfx_events: list[tuple[float, str]], out_wav: Path, music_volume: float = 0.16,
        music_enabled: bool = True) -> dict:
    """voice: [(start_sec, wav_path)], music_plan: [(start, end, mood)], sfx_events: [(t, name)]."""
    n = int(math.ceil(total * SR)) + 1
    v = np.zeros(n, dtype="float32")
    for st, path in voice:
        a, sr = read_wav(Path(path))
        a = _resample(a, sr)
        i0 = int(st * SR)
        L = min(len(a), n - i0)
        if L > 0:
            v[i0:i0 + L] += a[:L]
    # voice gain to ~ -18 dBFS RMS where speaking
    speaking = np.abs(v) > 0.003
    if speaking.any():
        rms = np.sqrt(np.mean(v[speaking] ** 2))
        v *= min(4.0, 0.125 / max(rms, 1e-4))
    m = np.zeros(n, dtype="float32")
    if music_enabled:
        for i, (a, b, mood) in enumerate(music_plan):
            seg = music_segment(b - a + 1.5, mood, seed=i)
            i0 = int(a * SR)
            L = min(len(seg), n - i0)
            fade = np.ones(L, dtype="float32")
            f = min(L, int(1.5 * SR))
            fade[:f] = np.linspace(0, 1, f)
            fade[-f:] = np.minimum(fade[-f:], np.linspace(1, 0, f))
            m[i0:i0 + L] += seg[:L] * fade
        # side-chain ducking from smoothed voice envelope
        env = np.abs(v)
        k = int(0.25 * SR)
        cs = np.concatenate([[0.0], np.cumsum(env, dtype="float64")])  # O(N) centred moving average
        lo = np.clip(np.arange(n) - k // 2, 0, n)
        hi = np.clip(np.arange(n) + k // 2, 0, n)
        env = ((cs[hi] - cs[lo]) / np.maximum(1, hi - lo)).astype("float32")
        env = env / (env.max() + 1e-6)
        duck = 1 - 0.55 * np.clip(env * 4, 0, 1)
        m *= duck * music_volume / 0.16 * 0.9
    s = np.zeros(n, dtype="float32")
    for t, name in sfx_events:
        a = sfx(name)
        i0 = int(t * SR)
        L = min(len(a), n - i0)
        if L > 0 and i0 >= 0:
            s[i0:i0 + L] += a[:L] * 0.6
    mixd = v + m + s
    # soft limiter: transparent below 0.7, ceiling at -1 dBFS (0.891)
    ceil = 0.891
    over = np.abs(mixd) > 0.7
    if over.any():
        x = mixd[over]
        mixd[over] = np.sign(x) * (0.7 + (ceil - 0.7) * np.tanh((np.abs(x) - 0.7) / (ceil - 0.7)))
    stereo = np.stack([mixd, mixd], axis=1)
    write_wav(out_wav, stereo, SR)
    return {"samples": n, "voice_peak": float(np.max(np.abs(v))), "music_rms": float(np.sqrt(np.mean(m ** 2))),
            "sfx_events": len(sfx_events)}
