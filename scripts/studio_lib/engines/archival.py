"""Archival-style recreation engine (V3, documentary-art-director).

A stylised period look for *illustrative recreations*: sepia paper, ink line art
with hatching, typewriter captions, gentle projector flicker, dust and scratches.
Every frame carries an "ILLUSTRATIVE RECREATION" label unless the project opts
out for genuine, rights-cleared archival material (`params.label: false` and
`assets[]` with licence). It never imitates real archival footage.
"""
from __future__ import annotations

import math
import random

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter

from .. import design as D
from ..draw import paper_texture, seed_of, vignette
from .base import Style
from .native import HandDrawnEngine


class ArchivalEngine(HandDrawnEngine):
    name = "archival"
    description = "Sepia period-document look for labelled illustrative recreations (maps, people, events)."
    style = Style("archival", reveal="draw", rough=0.002, boil_fps=6, double_line=False, fill_mode="hatch",
                  fill_alpha=160, ink="ink", text_font="serif_bold", body_font="serif", text_color="ink",
                  pen=False, line_scale=0.85)

    def __init__(self, ctx):
        super().__init__(ctx)
        self._dust = None

    def background(self, t):
        if self._bg_cache is None:
            W, H = self.ctx.W, self.ctx.H
            base = paper_texture((W // 2, H // 2), (226, 211, 178), seed=29, grain=16).resize((W, H), Image.BICUBIC)
            v = vignette((W, H), 0.38)
            base = ImageChops.multiply(base, Image.merge("RGB", (v, v, v)))
            self._bg_cache = base.convert("RGBA")
        return self._bg_cache.copy()

    def post_out(self, img, t):
        W, H = img.size
        # sepia tone map
        g = img.convert("L")
        sep = Image.merge("RGB", (g.point(lambda v: min(255, int(v * 1.02 + 8))), g.point(lambda v: int(v * 0.93 + 4)),
                                  g.point(lambda v: int(v * 0.78))))
        img = Image.blend(img, sep, 0.55)
        # projector flicker (deterministic)
        f = 1.0 + 0.025 * math.sin(t * 23.0) + 0.015 * math.sin(t * 7.3 + 1.1)
        img = img.point(lambda v: max(0, min(255, int(v * f))))
        # dust + scratches, re-seeded 12x per second
        rnd = random.Random(seed_of(self.ctx.scene.get("id"), int(t * 12)))
        d = ImageDraw.Draw(img)
        for _ in range(int(6 + 4 * rnd.random())):
            x, y = rnd.random() * W, rnd.random() * H
            r = rnd.uniform(0.5, 2.2) * W / 1920
            d.ellipse((x - r, y - r, x + r, y + r), fill=(60, 45, 30))
        if rnd.random() < 0.35:
            x = rnd.random() * W
            d.line((x, 0, x + rnd.uniform(-4, 4), H), fill=(250, 240, 220), width=1)
        if self.params.get("label", True):
            U = min(W, H)
            fnt = D.font("serif_bold", int(U * 0.024))
            txt = self.params.get("label_text", "ILLUSTRATIVE RECREATION")
            tw = fnt.getlength(txt)
            pad = U * 0.012
            x0, y0 = pad * 2, H - pad * 2 - U * 0.024 - pad
            d.rectangle((x0 - pad, y0 - pad * 0.6, x0 + tw + pad, y0 + U * 0.024 + pad), fill=(40, 30, 20))
            d.text((x0, y0), txt, font=fnt, fill=(235, 222, 195))
        return img
