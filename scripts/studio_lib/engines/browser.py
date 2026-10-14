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
import urllib.parse
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
    env = {"huashu": "STUDIO_HUASHU_DIR", "animate": "STUDIO_ANIMATE_DIR", "lemo": "STUDIO_LEMO_DIR",
           "dashi": "STUDIO_DASHI_DIR", "mg": "STUDIO_MG_DIR"}[name]
    cands = []
    if os.environ.get(env):
        cands.append(Path(os.environ[env]))
    ext = _config().get("external", {})
    if ext.get(name):
        cands.append((SKILL_ROOT / ext[name]).resolve() if not Path(ext[name]).is_absolute() else Path(ext[name]))
    default = {"huashu": "huashu-art-motion", "animate": "animate/plugins/animate/skills/animate",
               "lemo": "lemo-opuscar", "dashi": "dashi-animationstyle", "mg": "mg-styles-15-src"}[name]
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
    lemo = external_dir("lemo", "core/lib.js")
    dashi = external_dir("dashi", "pipeline/render.mjs")
    return {
        "html_seek": {"ok": bool(pw), "lemo_dir": str(lemo) if lemo else None,
                      "dashi_dir": str(dashi) if dashi else None, "playwright": pw, "chromium": ch,
                      "note": "project pages always; lemo:/dashi: pages need the matching checkout"},
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


class _Files(_Quiet):
    """Also serves explicitly allowed absolute files at /__file__/<quoted path> (huashu render.py convention)."""
    allowed: frozenset = frozenset()

    def translate_path(self, path):
        if path.startswith("/__file__/"):
            f = urllib.parse.unquote(path[len("/__file__/"):].split("?")[0])
            return f if f in self.allowed else "/nonexistent"
        return super().translate_path(path)


# same flags as huashu scripts/engine/render.py, so canvas output matches the native renderer
_LAUNCH_ARGS = ["--disable-web-security", "--enable-gpu-rasterization", "--ignore-gpu-blocklist"]


class BrowserSession:
    def __init__(self, root: Path, width: int, height: int, allowed_files=None):
        from playwright.sync_api import sync_playwright

        handler = type("_H", (_Files,), {"allowed": frozenset(allowed_files or ())})
        self.srv = _Server(("127.0.0.1", 0), functools.partial(handler, directory=str(root)))
        self.port = self.srv.server_address[1]
        threading.Thread(target=self.srv.serve_forever, daemon=True).start()
        self.pw = sync_playwright().start()
        ch = chromium_path()
        try:
            try:
                self.browser = self.pw.chromium.launch(args=_LAUNCH_ARGS)
            except Exception:
                if not ch:
                    raise
                self.browser = self.pw.chromium.launch(executable_path=ch, args=_LAUNCH_ARGS)
        except Exception:
            self.pw.stop()  # leave no running event loop behind (next sync_playwright() would fail)
            self.srv.shutdown()
            raise
        self.page = self.browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        self.errors: list[str] = []
        self.console_errors: list[str] = []
        self.page.on("pageerror", lambda e: self.errors.append(str(e)))
        self.page.on("console", lambda m: self.console_errors.append(m.text) if m.type == "error" else None)

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
    """params: grammar, theme, data, cues[{at,kind,text,sub,data}], safe
    or shots: [{start, grammar, theme, data, cues, safe}] - one scene cut into several huashu shots
    (upstream guidance: one composition per 2-8 s shot). shot.start is scene time (seconds, "40%",
    "cue:word"); the first shot starts at 0. Inside a shot, numeric/"%" cue times are shot-relative and
    "cue:word" anchors are converted from scene time. Shots share the scene theme unless they set one."""
    name = "huashu_clip"
    description = "huashu-art-motion parameterised clip grammars (3b1b, Vox, finance chart, kinetic, whiteboard...)."

    def __init__(self, ctx):
        super().__init__(ctx)
        # Fidelity: the clip grammars run their own camera (holds are deliberate: "no built-in uniform
        # slow push or breathing"), so no drift is added unless the scene asks for a camera explicitly.
        # The drift crop + bilinear upscale softened every frame (PSNR ~24 dB vs the native renderer).
        self.camera = ctx.scene.get("camera") or {"move": "static"}
        root = external_dir("huashu", "scripts/engine/clip.html")
        if not root:
            raise RuntimeError("huashu-art-motion checkout not found (set STUDIO_HUASHU_DIR)")
        self.root = root / "scripts" / "engine"
        p = self.params
        shots = p.get("shots") or [{k: p[k] for k in ("grammar", "theme", "data", "cues", "safe") if k in p}]
        starts = [0.0] + [min(ctx.duration, max(0.0, ctx.resolve_time(sh.get("start")))) for sh in shots[1:]]
        if any(b <= a for a, b in zip(starts, starts[1:])):
            raise ValueError(f"huashu shots must start in increasing order, got {starts}")
        self.bounds = list(zip(starts, starts[1:] + [ctx.duration]))
        self.allowed: set[str] = set()
        self.specs = []
        for sh, (a, b) in zip(shots, self.bounds):
            dur = b - a

            def rt(at, a=a, dur=dur):
                if isinstance(at, str) and at.strip().startswith("cue:"):
                    return max(0.0, ctx.resolve_time(at) - a)
                if isinstance(at, str) and at.strip().endswith("%"):
                    return float(at.strip()[:-1]) / 100.0 * dur
                if isinstance(at, str) and at.strip().startswith("end"):
                    return dur + float(at.strip()[3:] or 0)
                return float(at or 0)

            spec = {"grammar": sh["grammar"], "duration": round(dur, 3), "fps": ctx.fps,
                    "width": ctx.width, "height": ctx.height,
                    "data": json.loads(json.dumps(sh.get("data", {}))),
                    "cues": [{**json.loads(json.dumps(c)), "at": round(rt(c.get("at")), 3)} for c in sh.get("cues", [])]}
            # no theme -> each grammar's own default look (native behaviour); was forced to "paper"
            theme = sh.get("theme", p.get("theme"))
            if theme is not None:
                spec["theme"] = theme
            if sh.get("safe") or p.get("safe"):
                spec["safe"] = sh.get("safe") or p.get("safe")
            # local asset paths (cue.image, cue.frames, data.image, data.character) -> /__file__/ URLs,
            # resolved against the project dir exactly like huashu render.py (spec_assets.localize, MIT)
            self._localize(spec, Path(ctx.scene.get("_project_dir", ".")))
            self.specs.append(spec)
        self.spec = self.specs[0]
        self.shot = None

    def _localize(self, spec, base: Path):
        import importlib.util

        f = self.root / "spec_assets.py"
        if not f.exists():
            return
        sp = importlib.util.spec_from_file_location("_huashu_spec_assets", f)
        mod = importlib.util.module_from_spec(sp)
        sp.loader.exec_module(mod)
        mod.localize(spec, base.resolve(), self.allowed)  # FileNotFoundError -> engine fails (no blank frames)

    def _open(self, k: int = 0):
        if self.session and self.shot == k:
            return
        try:
            if not self.session:
                self.session = BrowserSession(self.root, self.ctx.width, self.ctx.height, self.allowed)
                self.session.page.add_init_script(
                    "window.__STUDIO_SHOTS = " + json.dumps(self.specs, ensure_ascii=False) + ";"
                    "window.CLIP_SPEC = window.__STUDIO_SHOTS[+(new URLSearchParams(location.search).get('shot') || 0)];")
            pg = self.session.page
            self.shot = k
            pg.goto(f"http://127.0.0.1:{self.session.port}/clip.html?render=1&shot={k}")
            pg.wait_for_function("window.__ready === true || !!window.__bootFailed", timeout=120000)
            bf = pg.evaluate("window.__bootFailed || null")
            if bf:
                raise RuntimeError(f"huashu clip boot failed: {bf}")
        except Exception:
            self.close()  # do not leak a running Playwright loop into the next engine in this process
            raise

    def grab(self, t):
        k = max(i for i, (a, _) in enumerate(self.bounds) if t >= a - 1e-9) if t > 0 else 0
        self._open(k)
        b64 = self.session.page.evaluate(
            "async (t)=>{ await window.prepare(t); window.renderFrame(t); "
            "return window.__canvas.toDataURL('image/png').split(',')[1]; }", float(t - self.bounds[k][0]))
        return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")


class AnimatePieceEngine(_BrowserEngine):
    """params: piece (dir; "upstream:examples/history-of-ai" or project-relative), offset (s), format,
    timing (dict written to the work copy's src/timing.js as window.<timing_var>, default GA_TIMING)"""
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
        # the piece paints its own camera (push/bump) and boils on 2s, so it never freezes: no added drift.
        # A drift re-samples every frame (1.5-4% zoom, bilinear) and cost ~18 dB PSNR vs the native export.
        self.camera = ctx.scene.get("camera") or {"move": "static"}
        # params.timing (dict, e.g. {"fps": 30, "scenes": [{id, start, end, bridge_next}]}) is written as
        # src/timing.js (`window.<timing_var> = ...;`) into the WORK copy; the source dir is never touched.
        timing = self.params.get("timing")
        timing_var = self.params.get("timing_var", "GA_TIMING")
        # one work dir per build key (source path + newest source file + timing): every shipped style demo is a
        # folder called "demo" (a name-only key served one build for all of them), and parallel scene workers
        # with the same key share a finished build instead of rebuilding over each other
        self.build_key = self.build_key_for(src, timing, timing_var)
        base = Path(ctx.scene.get("_work_dir", ".")) / "_animate"
        work = base / f"{src.parent.name}-{src.name}-{self.build_key}"
        if not (work / "index.html").exists():
            tmp = base / f".tmp-{self.build_key}-{os.getpid()}-{threading.get_ident()}"
            if tmp.exists():
                shutil.rmtree(tmp)
            shutil.copytree(src, tmp, ignore=shutil.ignore_patterns("renders", "frames", "index.html"))
            if timing is not None:
                (tmp / "src").mkdir(exist_ok=True)
                (tmp / "src" / "timing.js").write_text(
                    f"window.{timing_var} = {json.dumps(timing, ensure_ascii=False)};\n", encoding="utf-8")
            cp = subprocess.run(["node", str(root / "tools" / "build.mjs"), str(tmp)], capture_output=True, text=True,
                                encoding="utf-8", errors="replace")
            if cp.returncode != 0:
                shutil.rmtree(tmp, ignore_errors=True)
                raise RuntimeError(f"animate build failed: {cp.stderr[-800:]}")
            try:
                os.rename(tmp, work)          # atomic publish; another worker may have won the race
            except OSError:
                shutil.rmtree(tmp, ignore_errors=True)
                if not (work / "index.html").exists():
                    raise
        self.work = work
        self.offset = float(self.params.get("offset", 0.0))
        # ?format= only means something to heads that read it (templates/piece); the shipped demos and
        # history-of-ai are fixed 1080x1920. Ask for a relayout only from a head that supports it.
        html = (work / "index.html").read_text(encoding="utf-8", errors="replace")
        relayout = "get('format')" in html or 'get("format")' in html
        fmt = self.params.get("format") or (("9:16" if ctx.vertical else "16:9") if relayout else None)
        self.query = "?export=1" + (f"&format={fmt}" if fmt else "")
        self.piece_fps = None

    @staticmethod
    def build_key_for(src: Path, timing=None, timing_var: str = "GA_TIMING") -> str:
        """Hash of what the built page depends on: the source path, its newest file (an edit inside src/ does not
        bump the folder's mtime on NTFS) and the injected timing."""
        import hashlib
        src = Path(src)
        newest = max([p.stat().st_mtime_ns for p in src.rglob("*")
                      if p.is_file() and not ({"renders", "frames"} & set(p.relative_to(src).parts))
                      and p.name != "index.html"] or [0])
        payload = json.dumps({"src": str(src.resolve()), "newest": newest, "timing": timing, "var": timing_var},
                             sort_keys=True, default=str)
        return hashlib.sha1(payload.encode("utf-8")).hexdigest()[:12]

    def _open(self):
        if self.session:
            return
        self.session = BrowserSession(self.work, self.ctx.width, self.ctx.height)
        try:
            self.session.page.goto(f"http://127.0.0.1:{self.session.port}/index.html{self.query}")
            self.session.page.wait_for_function("typeof window.renderFrame === 'function' && !!window.TIMELINE",
                                                timeout=60000)
            # renderFrame(t) snaps t to the piece's own frame grid (Math.round(t * TIMELINE.fps)); a 24 fps piece
            # in a 30 fps timeline repeats every 4th drawing. Author pieces at the timeline fps to avoid judder.
            self.piece_fps = self.session.page.evaluate("window.TIMELINE.fps")
        except Exception:
            self.close()
            raise

    def compose(self, t):
        img = self.grab(t)
        W, H = self.ctx.W, self.ctx.H
        if img.size != (W, H):
            iw, ih = img.size
            if abs(iw / ih - W / H) < 0.01:
                img = img.resize((W, H), Image.LANCZOS)
            else:  # never stretch a fixed-format piece: fit it, padded with its own edge colour
                k = min(W / iw, H / ih)
                fit = img.resize((max(1, round(iw * k)), max(1, round(ih * k))), Image.LANCZOS)
                out = Image.new("RGB", (W, H), img.getpixel((0, 0)))
                out.paste(fit, ((W - fit.width) // 2, (H - fit.height) // 2))
                img = out
        return img.convert("RGBA")

    def grab(self, t):
        self._open()
        b64 = self.session.page.evaluate(
            "(t)=>{ window.renderFrame(t); const c=document.getElementById('c');"
            " return c.toDataURL('image/png').split(',')[1]; }", float(t + self.offset))
        return Image.open(io.BytesIO(base64.b64decode(b64))).convert("RGB")
