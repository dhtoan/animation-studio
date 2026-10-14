"""Generic seekable-HTML adapter (V2).

Drives any deterministic HTML page that exposes a time-seek function, from an
external checkout or from the project itself. Contracts:

  lemo     lemomo-ai/lemo-opuscar   window.render(t), window.READY, window.DUR
           served from the library root; project pages are mounted at /@film/
  dashi    chuspeeism/dashi-animationstyle   window.seek(t), window.ready
  frame    generic: window.renderFrame(t) (huashu / animate style pages)

params:
  page      "lemo:styles/<slug>/demo/index.html" | "dashi:styles/<style>/<file>.html"
            | project-relative path to an .html file
  contract  lemo | dashi | frame   (default inferred from the page prefix)
  offset    seconds into the page's own timeline at scene t=0
  speed     playback rate (1.0)

Frames are captured with a viewport screenshot, which also works for WebGL
pages that do not preserve their drawing buffer. Every network request outside
127.0.0.1 is blocked.
"""
from __future__ import annotations

import functools
import http.server
import io
import os
import socketserver
import threading
import urllib.parse
from pathlib import Path

from PIL import Image

from .base import Engine, Style
from .browser import chromium_path, external_dir

CONTRACTS = {
    "lemo": {"ready": "window.READY === true", "seek": "async (t)=>{ window.render(t); }"},
    "dashi": {"ready": "typeof window.seek === 'function' && window.ready !== false",
              "seek": "async (t)=>{ await Promise.resolve(window.seek(t)); }"},
    "mg": {"ready": "window.__ready === true",
           "seek": "async (t)=>{ for (const a of document.getAnimations()) { try { a.pause(); a.currentTime = t*1000; } "
                   "catch(e){} } if (typeof window.renderAt==='function') await window.renderAt(t); }"},
    "frame": {"ready": "typeof window.renderFrame === 'function'",
              "seek": "async (t)=>{ await Promise.resolve(window.renderFrame(t)); }"},
}


FONT_EXT = (".ttf", ".otf", ".woff", ".woff2")


class _Handler(http.server.SimpleHTTPRequestHandler):
    film_dir: str | None = None
    font_fallback: str | None = None
    substitutions: list | None = None

    def log_message(self, *a):
        pass

    def translate_path(self, path):
        p = urllib.parse.unquote(path.split("?", 1)[0])
        if self.film_dir and p.startswith("/@film/"):
            rel = p[len("/@film/"):]
            full = os.path.realpath(os.path.join(self.film_dir, rel))
            if not full.startswith(os.path.realpath(self.film_dir)):
                return "/nonexistent"
            return full
        full = super().translate_path(path)
        if not os.path.realpath(full).startswith(os.path.realpath(self.directory)):
            return "/nonexistent"
        if (self.font_fallback and not os.path.exists(full) and full.lower().endswith(FONT_EXT)):
            # upstream demos reference font binaries they do not distribute; serve a local
            # fallback so document.fonts.load() resolves. Logged as a visual degradation.
            if self.substitutions is not None:
                self.substitutions.append(os.path.basename(full))
            return self.font_fallback
        return full


class _Server(socketserver.ThreadingTCPServer):
    daemon_threads = True
    request_queue_size = 128


def resolve_page(page: str, project_dir: Path) -> tuple[str, Path, str, Path | None]:
    """Returns (contract, server_root, url_path, film_dir)."""
    if page.startswith("lemo:"):
        root = external_dir("lemo", "core/lib.js")
        if not root:
            raise RuntimeError("lemo-opuscar checkout not found (set STUDIO_LEMO_DIR)")
        return "lemo", root, "/" + page[5:].lstrip("/"), None
    if page.startswith("mg:"):
        root = external_dir("mg", "harness/render.mjs")
        if not root:
            raise RuntimeError("mg-styles-15 checkout not found (set STUDIO_MG_DIR)")
        return "mg", root, "/" + page[3:].lstrip("/"), None
    if page.startswith("dashi:"):
        root = external_dir("dashi", "pipeline/render.mjs")
        if not root:
            raise RuntimeError("dashi-animationstyle checkout not found (set STUDIO_DASHI_DIR)")
        return "dashi", root, page[6:].lstrip("/"), None
    f = (project_dir / page).resolve()
    if not f.exists():
        raise FileNotFoundError(f"html_seek page not found: {f}")
    lemo = external_dir("lemo", "core/lib.js")
    if lemo:  # project pages may import /core/lib.js from the lemo library
        return "lemo", lemo, "/@film/" + f.name, f.parent
    return "frame", f.parent, "/" + f.name, None


class HtmlSeekEngine(Engine):
    name = "html_seek"
    description = "Seekable HTML/Canvas/WebGL pages (lemo-opuscar styles, dashi templates, any renderFrame page)."
    style = Style("html_seek", reveal="fade")
    max_ss = 1

    def __init__(self, ctx):
        super().__init__(ctx)
        self.camera = ctx.scene.get("camera") or {"move": "static"}
        prm = self.params
        contract, root, url, film = resolve_page(prm["page"], Path(ctx.scene.get("_project_dir", ".")))
        self.contract = prm.get("contract", contract)
        if contract == "dashi" and prm["page"].startswith("dashi:"):
            root, url = self._stage_dashi(root, url)
        self.root, self.url, self.film = root, url, film
        self.offset = float(prm.get("offset", 0.0))
        self.speed = float(prm.get("speed", 1.0))
        self._pw = self._browser = self._page = self._srv = None
        self.errors: list[str] = []

    def _stage_dashi(self, root: Path, rel: str):
        """dashi's own render.mjs copies 动效部件.js (+ the project's timeline.js) next to the page.
        We do the same in a work dir so the upstream checkout is never modified."""
        import hashlib
        import shutil

        page = root / rel
        timeline = Path(self.params.get("timeline") or (root / "examples" / "token" / "timeline.js"))
        if not timeline.is_absolute():
            timeline = Path(self.ctx.scene.get("_project_dir", ".")) / timeline
        key = hashlib.sha1(f"{page}|{timeline}".encode()).hexdigest()[:10]
        work = Path(self.ctx.scene.get("_work_dir", ".")) / "_dashi" / key
        work.mkdir(parents=True, exist_ok=True)
        shutil.copy2(page, work / "index.html")
        shutil.copy2(root / "pipeline" / "动效部件.js", work / "动效部件.js")
        shutil.copy2(timeline, work / "timeline.js")
        for extra in ("assets",):  # optional asset folder beside the timeline
            src = timeline.parent / extra
            if src.is_dir() and not (work / extra).exists():
                shutil.copytree(src, work / extra)
        return work, "/index.html"

    def _open(self):
        if self._page:
            return
        from playwright.sync_api import sync_playwright

        from ..design import font_path

        self.substitutions = []
        fb = font_path("sans_bold") if self.params.get("font_fallback", True) else None
        handler = type("H", (_Handler,), {"film_dir": str(self.film) if self.film else None,
                                          "font_fallback": fb, "substitutions": self.substitutions})
        self._srv = _Server(("127.0.0.1", 0), functools.partial(handler, directory=str(self.root)))
        port = self._srv.server_address[1]
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch(args=["--ignore-gpu-blocklist", "--enable-webgl"])
        except Exception:
            self._browser = self._pw.chromium.launch(executable_path=chromium_path(),
                                                     args=["--ignore-gpu-blocklist", "--enable-webgl"])
        pg = self._browser.new_page(viewport={"width": self.ctx.width, "height": self.ctx.height},
                                    device_scale_factor=1)
        pg.on("pageerror", lambda e: self.errors.append(str(e)))

        def guard(route):
            u = route.request.url
            if u.startswith(f"http://127.0.0.1:{port}/") or u.startswith("data:") or u.startswith("blob:"):
                route.continue_()
            else:
                self.errors.append(f"blocked external request {u}")
                route.abort()

        pg.route("**/*", guard)
        q = self.params.get("query", "")
        pg.goto(f"http://127.0.0.1:{port}{self.url}" + (("?" + q) if q else ""))
        pg.wait_for_function(CONTRACTS[self.contract]["ready"], timeout=180000)
        pg.evaluate("document.fonts ? document.fonts.ready.then(()=>1) : 1")
        self._page = pg

    def grab(self, t: float) -> Image.Image:
        self._open()
        self._page.evaluate(CONTRACTS[self.contract]["seek"], float(self.offset + t * self.speed))
        png = self._page.screenshot(type="png", clip={"x": 0, "y": 0, "width": self.ctx.width, "height": self.ctx.height})
        if self.errors and any(not e.startswith("blocked") for e in self.errors):
            raise RuntimeError(f"page error: {self.errors[-1][:300]}")
        return Image.open(io.BytesIO(png)).convert("RGB")

    def compose(self, t):
        img = self.grab(t)
        if img.size != (self.ctx.W, self.ctx.H):
            img = img.resize((self.ctx.W, self.ctx.H), Image.LANCZOS)
        return img.convert("RGBA")

    def close(self):
        try:
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        finally:
            if self._srv:
                self._srv.shutdown()
            self._page = self._browser = self._pw = self._srv = None
