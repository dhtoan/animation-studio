"""Output formats, quality presets and project paths."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]

FORMATS = {
    "long": {"width": 1920, "height": 1080, "aspect": "16:9"},
    "short": {"width": 1080, "height": 1920, "aspect": "9:16"},
}

# fps is identical across qualities so timing/caching semantics never drift.
QUALITY = {
    # scale: output resolution multiplier; ss: supersampling factor for anti-aliasing
    "draft": {"scale": 0.5, "ss": 1, "crf": 28, "preset": "ultrafast"},
    "preview": {"scale": 0.5, "ss": 2, "crf": 23, "preset": "veryfast"},
    "final": {"scale": 1.0, "ss": 2, "crf": 18, "preset": "medium"},
}
FPS = 30

PROJECT_SUBDIRS = [
    "research", "scripts", "storyboard", "assets", "scenes", "audio", "subtitles",
    "previews", "renders", "shorts", "thumbnails", "seo", "reports",
]

DURATION_PRESETS = {
    "explainer": (8 * 60, 12 * 60),
    "documentary": (12 * 60, 20 * 60),
    "deep-dive": (20 * 60, 30 * 60),
}

CATEGORIES = {
    "business": "Business, Money, Scandals, and Mysteries",
    "technology": "Technology, AI, and Startups",
    "history": "History and Educational Explainers",
    "science": "Science and Engineering",
    "diy": "DIY and How-to Education",
    "startups": "Startup Stories",
}

# Categories that trigger extra accuracy / reputational-risk gates.
HIGH_RISK_CATEGORIES = {"business"}


@dataclass(frozen=True)
class RenderSettings:
    fmt: str
    quality: str

    @property
    def width(self) -> int:
        return int(round(FORMATS[self.fmt]["width"] * QUALITY[self.quality]["scale"] / 2) * 2)

    @property
    def height(self) -> int:
        return int(round(FORMATS[self.fmt]["height"] * QUALITY[self.quality]["scale"] / 2) * 2)

    @property
    def ss(self) -> int:
        return QUALITY[self.quality]["ss"]

    @property
    def fps(self) -> int:
        return FPS

    @property
    def crf(self) -> int:
        return QUALITY[self.quality]["crf"]

    @property
    def preset(self) -> str:
        return QUALITY[self.quality]["preset"]

    def key(self) -> dict:
        return {"fmt": self.fmt, "quality": self.quality, "w": self.width, "h": self.height,
                "ss": self.ss, "fps": self.fps, "crf": self.crf}


def projects_root(override: str | None = None) -> Path:
    if override:
        return Path(override).resolve()
    if os.environ.get("STUDIO_PROJECTS_DIR"):
        return Path(os.environ["STUDIO_PROJECTS_DIR"]).resolve()
    return (Path.cwd() / "projects").resolve()
