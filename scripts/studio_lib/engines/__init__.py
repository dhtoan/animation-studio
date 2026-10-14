"""Engine registry."""
from __future__ import annotations

from .base import Engine, SceneContext, Style  # noqa: F401
from .native import ArtisticEngine, HandDrawnEngine, KineticEngine, MotionEngine, WhiteboardEngine
from .image_whiteboard import ImageWhiteboardEngine
from .browser import AnimatePieceEngine, HuashuClipEngine, availability as browser_availability

ENGINES: dict[str, type[Engine]] = {
    "whiteboard": WhiteboardEngine,
    "handdrawn": HandDrawnEngine,
    "motion": MotionEngine,
    "kinetic": KineticEngine,
    "artistic": ArtisticEngine,
    "image_whiteboard": ImageWhiteboardEngine,
    "huashu_clip": HuashuClipEngine,
    "animate_piece": AnimatePieceEngine,
}

NATIVE = {"whiteboard", "handdrawn", "motion", "kinetic", "artistic", "image_whiteboard"}

# If an engine cannot initialise or fails during render, the scene is re-rendered
# with the next engine whose output carries the same information (elements are
# engine-agnostic, so the facts on screen do not change).
FALLBACKS = {
    "huashu_clip": ["motion"],
    "animate_piece": ["handdrawn", "artistic"],
    "image_whiteboard": ["whiteboard"],
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
