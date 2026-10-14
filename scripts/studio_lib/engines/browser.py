"""Browser-canvas adapters for upstream engines that render with `renderFrame(t)`.

huashu_clip   -> alchaincyf/huashu-art-motion  scripts/engine/clip.html  (MIT)
animate_piece -> cth9191/animate               tools/build.mjs + index.html (MIT)

The upstream checkouts stay external (never vendored, never modified). Paths:
  STUDIO_HUASHU_DIR / STUDIO_ANIMATE_DIR env vars, else `studio.config.json`
  {"external": {"huashu": "...", "animate": "..."}}, else _upstream/<repo> (repo root) or ../_upstream/<repo>.
Chromium: STUDIO_CHROMIUM, else Playwright's own browser, else any ms-playwright chromium-*.
"""
from __future__ import annotations

import base64
import functools
import http.server
import io
import json
import os
import shutil
import socketserver
import subprocess
import threading
from pathlib import Path

from PIL import Image

from ..config import SKILL_ROOT
from .base import Engine, Style


# ------------------------------------------------------------------ discovery
def _config() -> dict:
    p = SKILL_ROOT / "studio.config.json"
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


def external_dir(name: str, rel_check: str) -> Path | None:
    env = {"huashu": "STUDIO_HUASHU_DIR", "animate": "STUDIO_ANIMATE_DIR"}[name]
    cands = []
    if os.environ.get(env):
        cands.append(Path(os.environ[env]))
    ext = _config().get("external", {})
    if ext.get(name):
        cands.append((SKILL_ROOT / ext[name]).resolve() if not Path(ext[name]).is_absolute() else Path(ext[name]))
    default = {"huashu": "huashu-art-motion", "animate": "animate/plugins/animate/skills/animate"}[name]
    cands.append(SKILL_ROOT / "_upstream" / default)
    cands.append(SKILL_ROOT.parent / "_upstream" / default)
    for c in cands:
        if (c / rel_check).exists():
            return c.resolve()
    return None


def chromium_path() -> str | None:
    if os.environ.get("STUDIO_CHROMIUM") and Path(os.environ["STUDIO_CHROMIUM"]).exists():
        return os.environ["STUDIO_CHROMIUM"]
    roots = [Path(os.environ.get("PLAYWRIGHT_BROWSERS_PATH", "")),
             Path(os.environ.get("LOCALAPPDATA", "")) / "ms-playwright",
             Path.home() / ".cache" / "ms-playwright", Path.home() / "Library" / "Caches" / "ms-playwright"]
    for r in roots:
        if not r or not r.exists():
            continue
        for d in sorted(r.glob("chromium-*"), reverse=True):
            for exe in ("chrome-win64/chrome.exe", "chrome-linux/chrome", "chrome-linux64/chrome",
                        "chrome-mac/Chromium.app/Contents/MacOS/Chromium"):
                if (d / exe).exists():
                    return str(d / exe)
    return None


def playwright_ok() -> bool:
    try:
        import playwright  # noqa: F401
        return True
    except Exception:
        return False


def availability() -> dict:
    hu = external_dir("huashu", "scripts/engine/clip.html")
    an = external_dir("animate", "tools/build.mjs")
    node = shutil.which("node")
    pw, ch = playwright_ok(), chromium_path()
    return {
        "huashu_clip": {"ok": bool(hu and pw), "dir": str(hu) if hu else None, "playwright": pw, "chromium": ch},
        "animate_piece": {"ok": bool(an and pw and node), "dir": str(an) if an else None, "node": node,
                          "playwright": pw, "chromium": ch},
    }


# ------------------------------------------------------------------ browser session
class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


class _Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    request_queue_size = 128


class BrowserSession:
    def __init__(self, root: Path, width: int, height: int):
        from playwright.sync_api import sync_playwright

        self.srv = _Server(("127.0.0.1", 0), functools.partial(_Quiet, directory=str(root)))
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.pw = sync_playwright().start()
        kw = {}
        ch = chromium_path()
        try:
            self.browser = self.pw.chromium.launch(args=["--disable-web-security"])
        except Exception:
            if not ch:
                raise
            self.browser = self.pw.chromium.launch(executable_path=ch, args=["--disable-web-security"])
        self.page = self.browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        self.errors: list[str] = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))

    def close(self):
        try:
            self.browser.close()
            self.pw.stop()
        finally:
            self.srv.shutdown()


class _BrowserEngine(Engine):
    style = Style("browser", reveal="fade")
    session: BrowserSession | None = None
    max_ss = 1  # the page renders at output resolution

    def __init__(self, ctx):
        super().__init__(ctx)
        # upstream pages run their own camera; only a gentle drift is added (keeps holds alive)
        self.camera = ctx.scene.get("camera") or {"move": "drift", "base_zoom": 0.015, "amount": 0.03}

    def grab(self, t: float) -> Image.Image:
        raise NotImplementedError

    def compose(self, t):
        img = self.grab(t)
        if img.size != (self.ctx.W, self.ctx.H):
            img = img.resize((self.ctx.W, self.ctx.H), Image.LANCZOS)
        return img.convert("RGBA")


    def close(self):
        if self.session:
            self.session.close()
            self.session = None


class HuashuClipEngine(_BrowserEngine):
    """params: grammar, theme, data, cues[{at,kind,text,sub,data}], safe"""
    name = "huashu_clip"
    description = "huashu-art-motion parameterised clip grammars (3b1b, Vox, finance chart, kinetic, whiteboard...)."

    def __init__(self, ctx):
        super().__init__(ctx)
        root = external_dir("huashu", "scripts/engine/clip.html")
        if not root:
            raise RuntimeError("huashu-art-motion checkout not found (set STUDIO_HUASHU_DIR)")
        self.root = root / "scripts" / "engine"
        p = self.params
        spec = {"grammar": p["grammar"], "duration": round(ctx.duration, 3), "fps": ctx.fps,
                "width": ctx.width, "height": ctx.height, "theme": p.get("theme", "paper"),
                "data": p.get("data", {}),
                "cues": [{**c, "at": ctx.resolve_time(c.get("at"))} for c in p.get("cues", [])]}
        if p.get("safe"):
            spec["safe"] = p["safe"]
        self.spec = spec

    def _open(self):
        if self.session:
            return
        self.session = BrowserSession(self.root, self.ctx.width, self.ctx.height)
        pg = self.session.page
        pg.add_init_script("window.CLIP_SPEC = " + json.dumps(self.spec, ensure_ascii=False) + ";")
        pg.goto(f"http://127.0.0.1:{self.session.port}/clip.html?render=1")
        pg.wait_for_function("window.__ready === true || !!window.__bootFailed", timeout=120000)
        bf = pg.evaluate("window.__bootFailed || null")
        if bf:
            raise RuntimeError(f"huashu clip boot failed: {bf}")

    def grab(self, t):
        self._open()
        b64 = self.session.page.evaluate(
            "async (t)=>{ await window.prepare(t); window.renderFrame(t); "
            "return window.__canvas.toDataURL('image/png').split(',')[1]; }", float(t))
        return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")


class AnimatePieceEngine(_BrowserEngine):
    """params: piece (dir; "upstream:examples/history-of-ai" or project-relative), offset (s), format"""
    name = "animate_piece"
    description = "cth9191/animate pieces (cut-paper, riso, crosshatch, isometric, math, pixel, sketchbook)."

    def __init__(self, ctx):
        super().__init__(ctx)
        root = external_dir("animate", "tools/build.mjs")
        if not root:
            raise RuntimeError("animate checkout not found (set STUDIO_ANIMATE_DIR)")
        piece = self.params["piece"]
        src = root / piece.split(":", 1)[1] if piece.startswith("upstream:") else \
            Path(ctx.scene.get("_project_dir", ".")) / piece
        work = Path(ctx.scene.get("_work_dir", ".")) / "_animate" / src.name
        if not (work / "index.html").exists() or (src / "src").stat().st_mtime > (work / "index.html").stat().st_mtime:
            if work.exists():
                shutil.rmtree(work)
            shutil.copytree(src, work, ignore=shutil.ignore_patterns("renders", "frames", "index.html"))
            cp = subprocess.run(["node", str(root / "tools" / "build.mjs"), str(work)], capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
            if cp.returncode != 0:
                raise RuntimeError(f"animate build failed: {cp.stderr[-800:]}")
        self.work = work
        self.offset = float(self.params.get("offset", 0.0))
        fmt = self.params.get("format") or ("9:16" if ctx.vertical else "16:9")
        self.query = f"?export=1&format={fmt}"

    def _open(self):
        if self.session:
            return
        self.session = BrowserSession(self.work, self.ctx.width, self.ctx.height)
        self.session.page.goto(f"http://127.0.0.1:{self.session.port}/index.html{self.query}")
        self.session.page.wait_for_function("typeof window.renderFrame === 'function'", timeout=60000)

    def grab(self, t):
        self._open()
        b64 = self.session.page.evaluate(
            "(t)=>{ window.renderFrame(t); const c=document.getElementById('c');"
            " return c.toDataURL('image/png').split(',')[1]; }", float(t + self.offset))
        return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
