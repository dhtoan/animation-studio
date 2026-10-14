"""Captions from word timings: SRT export, burn-in chunks, and timing checks."""
from __future__ import annotations

import re
from pathlib import Path

MAX_LINE = 42
MAX_LINES = 2
MAX_DUR = 6.0
MIN_DUR = 0.9
MAX_CPS = 21.0


def chunk(words: list[tuple[float, str]], end_time: float, max_chars: int = MAX_LINE * MAX_LINES,
          max_dur: float = MAX_DUR) -> list[dict]:
    """Group timed words into caption cues, breaking at punctuation when possible."""
    cues, cur = [], []
    for i, (t, w) in enumerate(words):
        cur.append((t, w))
        text = " ".join(x for _, x in cur)
        nxt = words[i + 1][0] if i + 1 < len(words) else end_time
        brk = (re.search(r"[.!?]$", w) is not None or len(text) >= max_chars - 10
               or (re.search(r"[,;:—]$", w) and len(text) > max_chars * 0.5)
               or (nxt - cur[0][0]) > max_dur)
        if brk or i + 1 == len(words):
            last_end = min(nxt, t + max(0.35, len(w) * 0.07) + 0.25)
            cues.append({"start": cur[0][0], "end": max(last_end, cur[0][0] + MIN_DUR), "text": text,
                         "words": list(cur)})
            cur = []
    # no overlaps
    for a, b in zip(cues, cues[1:]):
        if a["end"] > b["start"] - 0.02:
            a["end"] = max(a["start"] + 0.3, b["start"] - 0.02)
    return cues


def wrap2(text: str, width: int = MAX_LINE) -> str:
    words = text.split()
    lines, cur = [], ""
    for w in words:
        if len(cur) + len(w) + 1 > width and cur:
            lines.append(cur)
            cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    if len(lines) > 2:  # rebalance into two lines
        mid = len(words) // 2
        lines = [" ".join(words[:mid]), " ".join(words[mid:])]
    return "\n".join(lines)


def srt_ts(t: float) -> str:
    t = max(0.0, t)
    ms = int(round(t * 1000))
    h, ms = divmod(ms, 3600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def write_srt(cues: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    out = []
    for i, c in enumerate(cues, 1):
        out.append(f"{i}\n{srt_ts(c['start'])} --> {srt_ts(c['end'])}\n{wrap2(c['text'])}\n")
    path.write_text("\n".join(out), encoding="utf-8")


def parse_srt(path: Path) -> list[dict]:
    blocks = re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip())
    out = []
    for b in blocks:
        lines = b.strip().splitlines()
        if len(lines) < 3:
            continue
        m = re.match(r"(\d+):(\d+):(\d+),(\d+) --> (\d+):(\d+):(\d+),(\d+)", lines[1])
        if not m:
            continue
        g = list(map(int, m.groups()))
        out.append({"start": g[0] * 3600 + g[1] * 60 + g[2] + g[3] / 1000,
                    "end": g[4] * 3600 + g[5] * 60 + g[6] + g[7] / 1000, "text": "\n".join(lines[2:])})
    return out


def check(cues: list[dict], duration: float) -> list[str]:
    issues = []
    prev_end = -1.0
    for i, c in enumerate(cues, 1):
        d = c["end"] - c["start"]
        if c["start"] < prev_end - 1e-3:
            issues.append(f"cue {i}: overlaps previous")
        if d <= 0:
            issues.append(f"cue {i}: non-positive duration")
        if c["end"] > duration + 0.05:
            issues.append(f"cue {i}: ends after media ({c['end']:.2f}s > {duration:.2f}s)")
        lines = c["text"].split("\n")
        if len(lines) > MAX_LINES or any(len(l) > MAX_LINE + 6 for l in lines):
            issues.append(f"cue {i}: too long for 2x{MAX_LINE} chars")
        cps = len(c["text"].replace("\n", " ")) / max(d, 0.01)
        if cps > MAX_CPS + 4:
            issues.append(f"cue {i}: reading speed {cps:.0f} cps")
        prev_end = c["end"]
    return issues
