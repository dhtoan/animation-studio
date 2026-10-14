"""Engine registry."""
from __future__ import annotations

from .base import Engine, SceneContext, Style  # noqa: F401
from .native import ArtisticEngine, HandDrawnEngine, KineticEngine, MotionEngine, WhiteboardEngine
from .image_whiteboard import ImageWhiteboardEngine
from .browser import AnimatePieceEngine, HuashuClipEngine, availability as browser_availability
from .html_seek import HtmlSeekEngine
from .archival import ArchivalEngine
from .sweety_draw import SweetyDrawEngine

ENGINES: dict[str, type[Engine]] = {
    "whiteboard": WhiteboardEngine,
    "handdrawn": HandDrawnEngine,
    "motion": MotionEngine,
    "kinetic": KineticEngine,
    "artistic": ArtisticEngine,
    "image_whiteboard": ImageWhiteboardEngine,
    "huashu_clip": HuashuClipEngine,
    "animate_piece": AnimatePieceEngine,
    "html_seek": HtmlSeekEngine,
    "archival": ArchivalEngine,
    "sweety_draw": SweetyDrawEngine,
}

NATIVE = {"whiteboard", "handdrawn", "motion", "kinetic", "artistic", "image_whiteboard", "archival", "sweety_draw"}

# Visual tier. "authentic" engines run the upstream repositories' own rendering code
# (pages, kits, stroke physics; sweety_draw runs sweety-handdraw-video's vendored stroke + paint code,
# adapters/vendor/sweety_handdraw); "native" engines are this studio's Pillow drawings
# (simple figures, icon clip-art, flat maps). Projects with
# quality_profile = "documentary-premium" may only use authentic engines unless a scene
# opts in with allow_native + native_reason; they never fall back to a native engine.
AUTHENTIC = {"huashu_clip", "animate_piece", "html_seek", "sweety_draw"}
TIER = {n: ("authentic" if n in AUTHENTIC else "native") for n in ENGINES}
PREMIUM_PROFILES = {"documentary-premium"}


def is_premium(project: dict) -> bool:
    return project.get("quality_profile") in PREMIUM_PROFILES

# If an engine cannot initialise or fails during render, the scene is re-rendered
# with the next engine whose output carries the same information (elements are
# engine-agnostic, so the facts on screen do not change).
FALLBACKS = {
    "huashu_clip": ["motion"],
    "animate_piece": ["handdrawn", "artistic"],
    "html_seek": ["motion", "whiteboard"],
    "archival": ["handdrawn", "whiteboard"],
    "image_whiteboard": ["whiteboard"],
    "sweety_draw": ["image_whiteboard"],
    "kinetic": ["motion"],
    "artistic": ["motion"],
    "handdrawn": ["whiteboard"],
    "whiteboard": ["handdrawn"],
    "motion": ["whiteboard"],
}


def availability() -> dict:
    out = {n: {"ok": True, "kind": "native"} for n in NATIVE}
    for k, v in browser_availability().items():
        out[k] = {**v, "kind": "external-adapter"}
    return out
