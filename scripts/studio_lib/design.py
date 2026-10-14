"""Design system: palettes, typography, easing.

One project theme feeds every engine so a video that mixes whiteboard,
motion graphics and artistic scenes still reads as one piece: the same accent
colours, the same type scale and the same transition vocabulary.
"""
from __future__ import annotations

import math
import os
import sys
from functools import lru_cache
from pathlib import Path

from PIL import ImageFont

from .config import SKILL_ROOT

# ---------------------------------------------------------------- palettes
THEMES = {
    # Business documentary: ink navy, money green, alarm red, signal amber.
    "documentary": {
        "ink": "#1b1f2a",
        "paper": "#f6f1e7",
        "board": "#fbfbf8",
        "night": "#0f1626",
        "night2": "#1c2a44",
        "accent": "#e8a33d",   # amber: attention
        "positive": "#2f9e6e", # growth
        "negative": "#d64541", # collapse
        "cool": "#3a7bd5",     # systems / tech
        "muted": "#8a93a6",
        "light": "#e9edf5",
    },
    "tech": {
        "ink": "#14161c", "paper": "#f3f4f7", "board": "#fafbfc", "night": "#0b1020",
        "night2": "#16213d", "accent": "#7c5cff", "positive": "#22c493", "negative": "#ff5d5d",
        "cool": "#2bb3ff", "muted": "#8b93a7", "light": "#e7ebf5",
    },
    "history": {
        "ink": "#2a2118", "paper": "#efe4cf", "board": "#f7f1e4", "night": "#1d1712",
        "night2": "#3a2c20", "accent": "#c4862d", "positive": "#5f8a4a", "negative": "#a63d2f",
        "cool": "#4f6d8a", "muted": "#9a8b74", "light": "#f2e9d8",
    },
}

ROLE_ALIASES = {"red": "negative", "green": "positive", "blue": "cool", "gold": "accent",
                "amber": "accent", "gray": "muted", "grey": "muted", "black": "ink", "white": "light"}


def hex_rgb(h: str) -> tuple[int, int, int]:
    h = h.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)


class Theme:
    def __init__(self, name: str = "documentary", overrides: dict | None = None):
        base = dict(THEMES.get(name, THEMES["documentary"]))
        base.update(overrides or {})
        self.name = name
        self.colors = base

    def c(self, role_or_hex: str | None, default: str = "ink") -> tuple[int, int, int]:
        v = role_or_hex or default
        if isinstance(v, (list, tuple)):
            return tuple(v)[:3]  # type: ignore
        if v.startswith("#"):
            return hex_rgb(v)
        v = ROLE_ALIASES.get(v, v)
        return hex_rgb(self.colors.get(v, self.colors[default]))


# ---------------------------------------------------------------- fonts
# role -> candidate files. First existing wins. Drop OFL fonts into
# <skill>/assets/fonts/ (e.g. Inter, Caveat, Oswald) to override system fonts.
_FONT_CANDIDATES = {
    "sans": ["Inter-Regular.ttf", "segoeui.ttf", "Roboto-Regular.ttf", "arial.ttf",
             "DejaVuSans.ttf", "Helvetica.ttc", "LiberationSans-Regular.ttf"],
    "sans_bold": ["Inter-Bold.ttf", "segoeuib.ttf", "arialbd.ttf", "DejaVuSans-Bold.ttf",
                  "Helvetica.ttc", "LiberationSans-Bold.ttf"],
    "display": ["Oswald-Bold.ttf", "bahnschrift.ttf", "impact.ttf", "arialbd.ttf",
                "DejaVuSans-Bold.ttf"],
    "hand": ["Caveat-Bold.ttf", "PatrickHand-Regular.ttf", "segoepr.ttf", "Inkfree.ttf",
             "comic.ttf", "DejaVuSans.ttf"],
    "hand_bold": ["Caveat-Bold.ttf", "segoeprb.ttf", "Inkfree.ttf", "comicbd.ttf",
                  "DejaVuSans-Bold.ttf"],
    "serif": ["georgia.ttf", "Georgia.ttf", "DejaVuSerif.ttf", "times.ttf"],
    "serif_bold": ["georgiab.ttf", "DejaVuSerif-Bold.ttf", "timesbd.ttf"],
}


def _font_dirs() -> list[Path]:
    dirs = [SKILL_ROOT / "assets" / "fonts"]
    if os.environ.get("STUDIO_FONT_DIR"):
        dirs.insert(0, Path(os.environ["STUDIO_FONT_DIR"]))
    if sys.platform == "win32":
        dirs += [Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
                 Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft/Windows/Fonts"]
    elif sys.platform == "darwin":
        dirs += [Path("/System/Library/Fonts"), Path("/Library/Fonts"), Path.home() / "Library/Fonts"]
    else:
        dirs += [Path("/usr/share/fonts"), Path.home() / ".fonts"]
    return dirs


@lru_cache(maxsize=None)
def font_path(role: str) -> str | None:
    for name in _FONT_CANDIDATES.get(role, _FONT_CANDIDATES["sans"]):
        for d in _font_dirs():
            p = d / name
            if p.exists():
                return str(p)
            if d.exists() and not str(d).startswith("/usr"):
                continue
            hits = list(d.rglob(name)) if d.exists() else []
            if hits:
                return str(hits[0])
    return None


@lru_cache(maxsize=512)
def font(role: str, size: int) -> ImageFont.FreeTypeFont:
    p = font_path(role)
    size = max(6, int(size))
    if p:
        return ImageFont.truetype(p, size)
    return ImageFont.load_default(size)


def font_report() -> dict:
    return {r: font_path(r) for r in _FONT_CANDIDATES}


# Type scale relative to the canvas short side (1080 for both formats).
TYPE_SCALE = {"hero": 0.105, "h1": 0.075, "h2": 0.054, "h3": 0.042, "body": 0.034,
              "label": 0.027, "caption": 0.03, "small": 0.022}


# ---------------------------------------------------------------- easing
def clamp(x: float, a: float = 0.0, b: float = 1.0) -> float:
    return a if x < a else b if x > b else x


def ease_out_cubic(t: float) -> float:
    t = clamp(t)
    return 1 - (1 - t) ** 3


def ease_in_out(t: float) -> float:
    t = clamp(t)
    return 3 * t * t - 2 * t * t * t


def ease_out_back(t: float, s: float = 1.6) -> float:
    t = clamp(t) - 1
    return t * t * ((s + 1) * t + s) + 1


def ease_in_cubic(t: float) -> float:
    t = clamp(t)
    return t ** 3


def spring(t: float, freq: float = 3.2, damp: float = 5.0) -> float:
    t = max(0.0, t)
    return 1 - math.exp(-damp * t) * math.cos(freq * math.tau * t * 0.5)


def lerp(a, b, t):
    return a + (b - a) * t


def mix_rgb(a, b, t):
    return tuple(int(round(lerp(a[i], b[i], clamp(t)))) for i in range(3))
