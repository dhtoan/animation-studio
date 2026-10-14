"""Vendored drawing core of threerocks/sweety-handdraw-video (MIT). See SOURCE.md and LICENSE.

VERSION participates in the on-disk plan cache key of the sweety_draw engine: bump it whenever
any file in this package changes behaviour.
"""
UPSTREAM = "threerocks/sweety-handdraw-video"
UPSTREAM_COMMIT = "5206ec0d17f9b353e400b64b9c51ad69e721e02a"
VERSION = "sweety-5206ec0+studio.1"

from . import paint_motion, reveal, stroke_assets, stroke_paths  # noqa: E402,F401
