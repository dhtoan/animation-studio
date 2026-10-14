"""Generates the demo's original illustration assets (no third-party art).

assets/hub-illustration.png — a delivery hub drawn with the studio's own
hand-drawn engine on white, used as input for the `image_whiteboard` engine
(which then re-draws it stroke by stroke with the vendored upstream planners).

Usage: python make_assets.py <project_dir>
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from PIL import Image  # noqa: E402

from studio_lib.design import Theme  # noqa: E402
from studio_lib.engines import SceneContext, Style  # noqa: E402
from studio_lib.engines.native import HandDrawnEngine  # noqa: E402


class _WhiteHanddrawn(HandDrawnEngine):
    style = Style(**{**HandDrawnEngine.style.__dict__, "pen": False})

    def background(self, t):
        return Image.new("RGBA", (self.ctx.W, self.ctx.H), (255, 255, 255, 255))


def hub(out: Path):
    els = [
        {"type": "icon", "name": "warehouse", "pos": [0.5, 0.42], "size": 0.26, "label": "Regional hub", "label_scale": 1.6},
        {"type": "icon", "name": "truck", "pos": [0.17, 0.78], "size": 0.1},
        {"type": "icon", "name": "truck", "pos": [0.83, 0.78], "size": 0.1},
        {"type": "icon", "name": "box", "pos": [0.33, 0.83], "size": 0.06},
        {"type": "icon", "name": "box", "pos": [0.67, 0.83], "size": 0.06},
        {"type": "icon", "name": "coin", "pos": [0.14, 0.2], "size": 0.07},
        {"type": "icon", "name": "coin", "pos": [0.86, 0.2], "size": 0.07},
        {"type": "arrow", "from": [0.22, 0.24], "to": [0.36, 0.33], "curve": 0.2},
        {"type": "arrow", "from": [0.64, 0.33], "to": [0.79, 0.24], "curve": 0.2},
    ]
    sc = {"id": "asset-hub", "elements": els, "camera": {"move": "static"}}
    ctx = SceneContext(scene=sc, width=1600, height=1000, ss=2, fps=30, duration=10, theme=Theme("documentary"))
    eng = _WhiteHanddrawn(ctx)
    img = eng.frame(9.9)
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    print("wrote", out)


if __name__ == "__main__":
    pdir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).parent
    hub(pdir / "assets" / "hub-illustration.png")
