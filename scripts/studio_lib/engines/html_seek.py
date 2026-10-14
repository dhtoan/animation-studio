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
  timing    {fps, scenes: [{id, start, end}]}: injected as window.STUDIO_TIMING before any page
            script runs (add_init_script; nothing is written into the source dir). It is part of
            the scene params, so it is part of the scene cache key.
  era       a scene id in `timing` (true = this scene's id): offset defaults to its start, and the
            scene's word timings (era-local seconds) are injected as scenes[i].words
  workers   pages rendering in parallel for sequential frames (default 3 for lemo pages, else 1)
  capture   jpeg (q95, as lemo's own video.mjs; default) | png (lossless)

Frames are captured with a viewport screenshot, which also works for WebGL
pages that do not preserve their drawing buffer. Every network request outside
127.0.0.1 is blocked.

Fonts: upstream demos reference OFL font files they do not ship. A missing font
request is resolved through tools/fonts/manifest.json (request path, then
basename; recorded in `font_mapped`), and only then replaced by the generic
fallback font (recorded in `substitutions`, reported as a degradation).
"""
from __future__ import annotations

import base64
import functools
import http.server
import io
import json
import os
import socketserver
import threading
import urllib.parse
from pathlib import Path

from PIL import Image

from .base import Engine, Style
from .browser import chromium_path, external_dir

CONTRACTS = {
    # await: some lemo pages (silent-film) define render as async; lemo's still.mjs awaits it too
    "lemo": {"ready": "window.READY === true", "seek": "async (t)=>{ await window.render(t); }"},
    "dashi": {"ready": "typeof window.seek === 'function' && window.ready !== false",
              "seek": "async (t)=>{ await Promise.resolve(window.seek(t)); }"},
    "mg": {"ready": "window.__ready === true",
           "seek": "async (t)=>{ for (const a of document.getAnimations()) { try { a.pause(); a.currentTime = t*1000; } "
                   "catch(e){} } if (typeof window.renderAt==='function') await window.renderAt(t); }"},
    "frame": {"ready": "typeof window.renderFrame === 'function'",
              "seek": "async (t)=>{ await Promise.resolve(window.renderFrame(t)); }"},
}


FONT_EXT = (".ttf", ".otf", ".woff", ".woff2")
# real GPU when there is one (headless Chromium otherwise rasterises on SwiftShader, ~5x slower here);
# hinting / colour profile as lemo's core/render/browser.mjs, for pixel parity with its renders
LAUNCH_ARGS = ["--ignore-gpu-blocklist", "--enable-webgl", "--enable-gpu", "--font-render-hinting=none",
               "--force-color-profile=srgb"]


@functools.lru_cache(maxsize=4)
def _font_manifest(path: str) -> tuple[dict, dict, str]:
    """tools/fonts/manifest.json (built by the font fetcher): the OFL fonts upstream demos
    request but do not ship. Returns (by request path, by unambiguous basename, base dir)."""
    import json

    try:
        m = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}, {}, ""
    return dict(m.get("paths") or {}), dict(m.get("by_basename") or {}), str(Path(path).parent)


def font_manifest_path() -> str:
    from ..config import SKILL_ROOT

    return os.environ.get("STUDIO_FONTS_MANIFEST") or str(SKILL_ROOT / "tools" / "fonts" / "manifest.json")


def resolve_font(rel: str, manifest: str | None = None) -> str | None:
    """Local file for a missing font request, by request path (relative to the served root),
    then by basename. None when the manifest has no entry or the file is absent."""
    paths, names, base = _font_manifest(manifest or font_manifest_path())
    rel = rel.replace("\\", "/").lstrip("/")
    local = paths.get(rel) or names.get(rel.rsplit("/", 1)[-1])
    if not local:
        return None
    full = os.path.realpath(os.path.join(base, local))
    if not full.startswith(os.path.realpath(base) + os.sep) or not os.path.isfile(full):
        return None
    return full


def font_listed(rel: str, manifest: str | None = None) -> bool:
    """True when the manifest maps this request but the file is not on disk (fonts not fetched)."""
    paths, names, _ = _font_manifest(manifest or font_manifest_path())
    rel = rel.replace("\\", "/").lstrip("/")
    return bool(paths.get(rel) or names.get(rel.rsplit("/", 1)[-1]))


def timing_script(timing: dict | None, era: str | None = None, words=None, speed: float = 1.0) -> str | None:
    """JS that defines window.STUDIO_TIMING before the page's scripts run (None without timing)."""
    if not timing:
        return None
    tm = json.loads(json.dumps(timing))
    if era and words:
        for s in tm.get("scenes", []):
            if s.get("id") == era:
                s["words"] = [[round(float(t) * speed, 3), w] for t, w in words]
    return "window.STUDIO_TIMING = " + json.dumps(tm, sort_keys=True) + ";"


def era_offset(timing: dict | None, era: str | None) -> float | None:
    for s in (timing or {}).get("scenes", []):
        if s.get("id") == era:
            return float(s["start"])
    return None


class _AsyncPool:
    """N pages of one browser rendering frames concurrently (async Playwright on its own thread),
    like lemo's video.mjs workers. Each page owns a contiguous run of frame times."""

    def __init__(self, n, url, viewport, ready, seek, init_script, port, errors, capture):
        import asyncio

        self.loop = asyncio.new_event_loop()
        self.th = threading.Thread(target=self.loop.run_forever, daemon=True)
        self.th.start()
        self.seek, self.errors = seek, errors
        self.shot = {"format": "png", "optimizeForSpeed": True} if capture == "png" else \
            {"format": "jpeg", "quality": 95, "optimizeForSpeed": True}
        self._run(self._open(n, url, viewport, ready, init_script, port))

    def _run(self, coro, timeout=900):
        import asyncio

        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    async def _open(self, n, url, viewport, ready, init_script, port):
        import asyncio

        from playwright.async_api import async_playwright

        self.pw = await async_playwright().start()
        try:
            self.browser = await self.pw.chromium.launch(args=LAUNCH_ARGS)
        except Exception:
            self.browser = await self.pw.chromium.launch(executable_path=chromium_path(), args=LAUNCH_ARGS)

        async def page():
            pg = await self.browser.new_page(viewport=viewport, device_scale_factor=1)
            pg.on("pageerror", lambda e: self.errors.append(str(e)))

            async def guard(route):
                u = route.request.url
                if u.startswith(f"http://127.0.0.1:{port}/") or u.startswith(("data:", "blob:")):
                    await route.continue_()
                else:
                    self.errors.append(f"blocked external request {u}")
                    await route.abort()

            await pg.route("**/*", guard)
            if init_script:
                await pg.add_init_script(init_script)
            await pg.goto(url)
            await pg.wait_for_function(ready, timeout=180000)
            await pg.evaluate("document.fonts ? document.fonts.ready.then(()=>1) : 1")
            return pg, await pg.context.new_cdp_session(pg)

        self.pages = await asyncio.gather(*[page() for _ in range(n)])

    async def _render(self, times):
        import asyncio

        k = -(-len(times) // len(self.pages))

        async def work(i):
            pg, cdp = self.pages[i]
            out = []
            for tt in times[i * k:(i + 1) * k]:
                await pg.evaluate(self.seek, float(tt))
                out.append(base64.b64decode((await cdp.send("Page.captureScreenshot", self.shot))["data"]))
            return out

        return [b for part in await asyncio.gather(*[work(i) for i in range(len(self.pages))]) for b in part]

    def render(self, times) -> list[bytes]:
        return self._run(self._render(list(times)))

    def submit(self, times):
        import asyncio

        return asyncio.run_coroutine_threadsafe(self._render(list(times)), self.loop)

    def close(self):
        async def _close():
            await self.browser.close()
            await self.pw.stop()
        try:
            self._run(_close(), timeout=60)
        finally:
            self.loop.call_soon_threadsafe(self.loop.stop)
            self.th.join(10)


class _Handler(http.server.SimpleHTTPRequestHandler):
    film_dir: str | None = None
    font_fallback: str | None = None
    substitutions: list | None = None
    font_mapped: list | None = None
    font_manifest: str | None = None

    def log_message(self, *a):
        pass

    def _missing_font(self, full: str, rel: str) -> str:
        """Missing font: try tools/fonts/manifest.json first (real OFL file), then the generic
        fallback, which is logged as a visual degradation."""
        if self.font_manifest:
            hit = resolve_font(rel, self.font_manifest)
            if hit:
                if self.font_mapped is not None:
                    self.font_mapped.append(rel)
                return hit
        note = os.path.basename(full)
        if self.font_manifest and font_listed(rel, self.font_manifest):
            note += " (in tools/fonts/manifest.json but not fetched: python scripts/fetch_fonts.py)"
        if self.substitutions is not None:   # always a logged degradation, never a crash
            self.substitutions.append(note)
        if self.font_fallback:
            # upstream demos reference font binaries they do not distribute; serve a local
            # fallback so document.fonts.load() resolves.
            return self.font_fallback
        return full

    def translate_path(self, path):
        p = urllib.parse.unquote(path.split("?", 1)[0])
        if self.film_dir and p.startswith("/@film/"):
            rel = p[len("/@film/"):]
            full = os.path.realpath(os.path.join(self.film_dir, rel))
            if not full.startswith(os.path.realpath(self.film_dir)):
                return "/nonexistent"
            if not os.path.exists(full) and full.lower().endswith(FONT_EXT):
                return self._missing_font(full, rel.rsplit("/", 1)[-1])  # film pages: basename only
            return full
        full = super().translate_path(path)
        if not os.path.realpath(full).startswith(os.path.realpath(self.directory)):
            return "/nonexistent"
        if not os.path.exists(full) and full.lower().endswith(FONT_EXT):
            return self._missing_font(full, p.lstrip("/"))
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
        self.timing, self.era = prm.get("timing"), prm.get("era")
        if self.era is True:   # `era: true` before piece_timing.assign rewrote it: the era is this scene
            self.era = ctx.scene.get("_source") or ctx.scene.get("id")
        eo = era_offset(self.timing, self.era)
        self.offset = float(prm["offset"]) if "offset" in prm else (eo if eo is not None else 0.0)
        self.speed = float(prm.get("speed", 1.0))
        self.capture = prm.get("capture", "jpeg")
        self.workers = max(1, int(prm.get("workers", os.environ.get("STUDIO_HTML_SEEK_WORKERS",
                                                                     3 if self.contract == "lemo" else 1))))
        self._pw = self._browser = self._page = self._srv = self._pool = self._cdp = None
        self._frames: dict = {}   # prefetched frames (bytes) by page time
        self._last = self._next = None
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
        self.font_mapped = []  # missing upstream fonts served from tools/fonts (not a degradation)
        fb = font_path("sans_bold") if self.params.get("font_fallback", True) else None
        handler = type("H", (_Handler,), {"film_dir": str(self.film) if self.film else None,
                                          "font_fallback": fb, "substitutions": self.substitutions,
                                          "font_mapped": self.font_mapped,
                                          "font_manifest": font_manifest_path()})
        self._srv = _Server(("127.0.0.1", 0), functools.partial(handler, directory=str(self.root)))
        port = self._srv.server_address[1]
        threading.Thread(target=self._srv.serve_forever, daemon=True).start()
        q = self.params.get("query", "")
        url = f"http://127.0.0.1:{port}{self.url}" + (("?" + q) if q else "")
        init = timing_script(self.timing, self.era, self.ctx.words, self.speed)
        self.vw, self.vh, self.mb, self.shutter = self.ctx.width, self.ctx.height, 1, 0.5
        if self.workers > 1 and self.contract != "mg":   # mg pages read window.DEMO per page: sequential
            self._pool = _AsyncPool(self.workers, url, {"width": self.vw, "height": self.vh},
                                    CONTRACTS[self.contract]["ready"], CONTRACTS[self.contract]["seek"],
                                    init, port, self.errors, self.capture)
            self._page = self._pool
            return
        self._pw = sync_playwright().start()
        try:
            self._browser = self._pw.chromium.launch(args=LAUNCH_ARGS)
        except Exception:
            self._browser = self._pw.chromium.launch(executable_path=chromium_path(), args=LAUNCH_ARGS)
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
        if init:
            pg.add_init_script(init)
        pg.goto(url)
        pg.wait_for_function(CONTRACTS[self.contract]["ready"], timeout=180000)
        pg.evaluate("document.fonts ? document.fonts.ready.then(()=>1) : 1")
        # mg harness parity (harness/render.mjs): stage size and motion blur come from window.DEMO.
        # motion_blur / shutter params override; motion_blur=1 disables the sub-samples.
        if self.contract == "mg":
            demo = pg.evaluate("window.DEMO || {}") or {}
            w, h = int(demo.get("width") or self.vw), int(demo.get("height") or self.vh)
            if (w, h) != (self.vw, self.vh):
                pg.set_viewport_size({"width": w, "height": h})
                self.vw, self.vh = w, h
            mbc = demo.get("motionBlur") or {}
            self.mb = max(1, int(self.params.get("motion_blur", mbc.get("samples", 1))))
            self.shutter = float(self.params.get("shutter", mbc.get("shutter", 0.5)))
        self._cdp = pg.context.new_cdp_session(pg)
        self._page = pg

    def _check(self):
        if self.errors and any(not e.startswith("blocked") for e in self.errors):
            raise RuntimeError(f"page error: {[e for e in self.errors if not e.startswith('blocked')][-1][:300]}")

    def _shot(self, tt: float) -> Image.Image:
        # CDP capture (what page.screenshot wraps, without its per-call waits); JPEG q95 like lemo's
        # video.mjs, PNG with capture=png. The viewport is the stage, so no clip is needed.
        self._page.evaluate(CONTRACTS[self.contract]["seek"], float(tt))
        req = {"format": "png", "optimizeForSpeed": True} if self.capture == "png" else             {"format": "jpeg", "quality": 95, "optimizeForSpeed": True}
        data = base64.b64decode(self._cdp.send("Page.captureScreenshot", req)["data"])
        self._check()
        return Image.open(io.BytesIO(data)).convert("RGB")

    def _pooled(self, tt: float) -> Image.Image:
        """Sequential frames are rendered ahead in batches across the pool's pages, and the next batch
        renders while this one is consumed; a random-access frame (a still) is rendered alone."""
        k4 = lambda x: round(x, 4)  # noqa: E731
        key, step, batch = k4(tt), self.speed / self.ctx.fps, self.workers * 6
        if key not in self._frames:
            nxt, self._next = self._next, None
            if nxt and key in nxt[0]:
                self._frames = dict(zip(nxt[0], nxt[1].result(900)))
            else:
                if nxt:
                    nxt[1].result(900)
                seq = self._last is not None and abs(tt - self._last - step) < 1e-6
                ts = [tt + i * step for i in range(batch if seq else 1)]
                self._frames = dict(zip(map(k4, ts), self._pool.render(ts)))
            if len(self._frames) > 1:
                last = max(self._frames)
                ts = [last + (i + 1) * step for i in range(batch)]
                self._next = (list(map(k4, ts)), self._pool.submit(ts))
        self._last = tt
        data = self._frames.pop(key)
        self._check()
        return Image.open(io.BytesIO(data)).convert("RGB")

    def grab(self, t: float) -> Image.Image:
        self._open()
        tt = self.offset + t * self.speed
        if self._pool:
            return self._pooled(tt)
        if self.mb <= 1:
            return self._shot(tt)
        # box-filter shutter like the harness (tmix of MB sub-frames centred on the frame time)
        import numpy as np

        acc = None
        for s in range(self.mb):
            dt = self.shutter * ((s + 0.5) / self.mb - 0.5) / self.ctx.fps * self.speed
            a = np.asarray(self._shot(max(0.0, tt + dt)), dtype=np.float32)
            acc = a if acc is None else acc + a
        return Image.fromarray(np.clip(acc / self.mb + 0.5, 0, 255).astype(np.uint8))

    def compose(self, t):
        img = self.grab(t)
        if img.size != (self.ctx.W, self.ctx.H):
            img = img.resize((self.ctx.W, self.ctx.H), Image.LANCZOS)
        return img.convert("RGBA")

    def close(self):
        try:
            if self._pool:
                if self._next:
                    try:
                        self._next[1].result(900)
                    except Exception:
                        pass
                    self._next = None
                self._pool.close()
            if self._browser:
                self._browser.close()
            if self._pw:
                self._pw.stop()
        finally:
            if self._srv:
                self._srv.shutdown()
                self._srv.server_close()
            self._page = self._browser = self._pw = self._srv = self._pool = self._cdp = None
