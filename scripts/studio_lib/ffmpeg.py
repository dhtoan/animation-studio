"""FFmpeg discovery, probing and raw-frame encoding.

ffprobe is optional: probing parses `ffmpeg -i` output so a single bundled
ffmpeg binary (e.g. from the `imageio-ffmpeg` wheel) is enough.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

_CACHED: str | None = None


class FFmpegMissing(RuntimeError):
    pass


def find_ffmpeg() -> str:
    """Return a usable ffmpeg path. Order: $STUDIO_FFMPEG, PATH, imageio-ffmpeg."""
    global _CACHED
    if _CACHED:
        return _CACHED
    cands = []
    if os.environ.get("STUDIO_FFMPEG"):
        cands.append(os.environ["STUDIO_FFMPEG"])
    w = shutil.which("ffmpeg")
    if w:
        cands.append(w)
    try:
        import imageio_ffmpeg  # type: ignore

        cands.append(imageio_ffmpeg.get_ffmpeg_exe())
    except Exception:
        pass
    for c in cands:
        if c and Path(c).exists():
            _CACHED = c
            return c
    raise FFmpegMissing(
        "ffmpeg not found. Install ffmpeg on PATH, set STUDIO_FFMPEG, or `pip install imageio-ffmpeg`."
    )


def run(args: list[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    cmd = [find_ffmpeg(), "-hide_banner", "-nostdin"] + args
    cp = subprocess.run(cmd, capture_output=capture, text=True, encoding="utf-8", errors="replace")
    if check and cp.returncode != 0:
        tail = (cp.stderr or "")[-2000:]
        raise RuntimeError(f"ffmpeg failed ({cp.returncode}): {' '.join(args[:12])} ...\n{tail}")
    return cp


@dataclass
class Probe:
    path: str
    duration: float
    width: int | None
    height: int | None
    fps: float | None
    vcodec: str | None
    pix_fmt: str | None
    has_audio: bool
    audio_rate: int | None
    audio_channels: str | None

    def as_dict(self) -> dict:
        return dict(self.__dict__)


_DUR = re.compile(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)")
_VID = re.compile(r"Stream #\S+.*?Video:\s*(\w+)[^,]*,\s*(\w+)[^\n]*?,\s*(\d{2,5})x(\d{2,5})")
_FPS = re.compile(r"(\d+(?:\.\d+)?)\s*fps")
_AUD = re.compile(r"Stream #\S+.*?Audio:\s*\w+[^,]*,\s*(\d+)\s*Hz,\s*([\w.]+)")


def probe(path: str | Path) -> Probe:
    path = str(path)
    if not Path(path).exists():
        raise FileNotFoundError(path)
    cp = run(["-i", path], check=False)
    err = cp.stderr or ""
    m = _DUR.search(err)
    dur = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3)) if m else 0.0
    v = _VID.search(err)
    fps = None
    if v:
        line = err[v.start(): err.find("\n", v.start())]
        f = _FPS.search(line)
        fps = float(f.group(1)) if f else None
    a = _AUD.search(err)
    return Probe(
        path=path,
        duration=dur,
        width=int(v.group(3)) if v else None,
        height=int(v.group(4)) if v else None,
        fps=fps,
        vcodec=v.group(1) if v else None,
        pix_fmt=v.group(2) if v else None,
        has_audio=bool(a),
        audio_rate=int(a.group(1)) if a else None,
        audio_channels=a.group(2) if a else None,
    )


def count_frames(path: str | Path) -> int:
    cp = run(["-i", str(path), "-map", "0:v:0", "-f", "null", "-"], check=True)
    frames = re.findall(r"frame=\s*(\d+)", cp.stderr or "")
    return int(frames[-1]) if frames else 0


class FrameWriter:
    """Pipe raw RGB frames into ffmpeg -> H.264 MP4 (no audio)."""

    def __init__(self, out: str | Path, width: int, height: int, fps: int, crf: int = 20,
                 preset: str = "veryfast", gop: int | None = None):
        self.out = str(out)
        self.size = (width, height)
        args = [find_ffmpeg(), "-hide_banner", "-loglevel", "error", "-y",
                "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{width}x{height}", "-r", str(fps),
                "-i", "-", "-an", "-c:v", "libx264", "-preset", preset, "-crf", str(crf),
                "-pix_fmt", "yuv420p", "-r", str(fps), "-g", str(gop or fps * 2),
                "-movflags", "+faststart", self.out]
        self.proc = subprocess.Popen(args, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        self.frames = 0

    def write(self, img) -> None:
        if img.size != self.size:
            raise ValueError(f"frame size {img.size} != {self.size}")
        if img.mode != "RGB":
            img = img.convert("RGB")
        self.proc.stdin.write(img.tobytes())
        self.frames += 1

    def close(self) -> None:
        self.proc.stdin.close()
        err = self.proc.stderr.read().decode("utf-8", "replace")
        rc = self.proc.wait()
        if rc != 0:
            raise RuntimeError(f"ffmpeg encode failed ({rc}): {err[-1500:]}")

    def abort(self) -> None:
        try:
            self.proc.stdin.close()
        except Exception:
            pass
        self.proc.kill()
        self.proc.wait()
        try:
            Path(self.out).unlink(missing_ok=True)
        except Exception:
            pass


def extract_frame(video: str | Path, t: float, out_png: str | Path) -> Path:
    run(["-y", "-ss", f"{max(0.0, t):.3f}", "-i", str(video), "-frames:v", "1", str(out_png)])
    return Path(out_png)
