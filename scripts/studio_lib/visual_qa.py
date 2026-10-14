"""Visual quality-regression checks, scene by scene.

The format-level checks in qa.py (resolution, fps, black frames) cannot tell a
slideshow from a documentary. These checks look at the pixels and the render
manifests of every scene and flag the failure modes that made earlier renders read
as "PowerPoint":

  blank_composition   most of the frame is empty background for most of the scene
  static_scene        the picture barely changes over the scene
  edge_clipping       content runs into the frame edge (cropped text/graphics)
  off_balance         the content mass sits far from the frame centre for the whole scene
  aspect              frame size differs from the delivery format
  primitive_engine    a premium project used a native (Pillow) drawing engine
  silent_fallback     the requested engine failed and another engine drew the scene
  degraded_dependency an engine reported a degradation (missing font, missing asset, ...)
  typography          more font families than the design system allows, or fallback fonts
  overflow            an HTML engine reported text overflowing its box or the viewport
  continuity          an abrupt palette/brightness jump between consecutive scenes

Every check returns plain dicts so tests can drive them with synthetic frames.
Issues are blockers for premium projects; warnings are reported for review.
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

# thresholds (tuned on the v1-v3 demo renders; see tests/test_visual_qa.py)
GRID = (16, 9)  # tiles across x down
TILE_STD_MIN = 6.0  # a tile with less luminance spread than this is "empty"
BLANK_OCCUPANCY = 0.18  # fewer occupied tiles than this = blank composition
STATIC_DIFF = 1.2  # mean abs luminance change between samples (0-255) below this = static
EDGE_BAND = 0.012  # fraction of width/height treated as the frame edge
BALANCE_MAX = 0.28  # centroid offset (fraction of half-size) tolerated
MAX_FONT_FAMILIES = 3
CONTINUITY_JUMP = 0.55  # histogram distance (0-1) treated as an abrupt jump


def _lum(img) -> np.ndarray:
    a = np.asarray(img.convert("RGB"), dtype="float32")
    return 0.2126 * a[..., 0] + 0.7152 * a[..., 1] + 0.0722 * a[..., 2]


def frame_stats(img, exclude_bottom: float = 0.0) -> dict:
    """Occupancy (share of tiles with visible detail), content centroid and edge contact."""
    L = _lum(img)
    if exclude_bottom:
        L = L[: int(L.shape[0] * (1 - exclude_bottom))]
    h, w = L.shape
    gx, gy = GRID
    occ = np.zeros((gy, gx), dtype=bool)
    for j in range(gy):
        for i in range(gx):
            t = L[j * h // gy:(j + 1) * h // gy, i * w // gx:(i + 1) * w // gx]
            occ[j, i] = t.std() > TILE_STD_MIN
    # detail map: gradient magnitude, used for centroid and edge contact
    g = np.abs(np.diff(L, axis=1))[:-1, :] + np.abs(np.diff(L, axis=0))[:, :-1]
    mask = g > 24
    ys, xs = np.nonzero(mask)
    if xs.size:
        cx = (xs.mean() / w - 0.5) * 2
        cy = (ys.mean() / h - 0.5) * 2
    else:
        cx = cy = 0.0
    bw, bh = max(2, int(w * EDGE_BAND)), max(2, int(h * EDGE_BAND))
    # detail touching the edge on an otherwise calm band = something is cut off
    edges = {"left": mask[:, :bw], "right": mask[:, -bw:], "top": mask[:bh, :], "bottom": mask[-bh:, :]}
    edge_contact = {k: float(v.mean()) for k, v in edges.items()}
    hist = np.histogram(L, bins=16, range=(0, 255))[0].astype("float64")
    return {"occupancy": float(occ.mean()), "centroid": [float(cx), float(cy)], "detail": float(mask.mean()),
            "edge_contact": edge_contact, "hist": (hist / max(1.0, hist.sum())).tolist(),
            "mean_lum": float(L.mean())}


def _hist_dist(a, b) -> float:
    a, b = np.asarray(a), np.asarray(b)
    return float(0.5 * np.abs(a - b).sum())


def scene_checks(frames: list, expect_size: tuple[int, int] | None = None, exclude_bottom: float = 0.0,
                 build_frac: float = 0.25) -> dict:
    """frames: [(t, PIL.Image)] sampled across one scene, in time order."""
    out = {"issues": [], "warnings": [], "samples": len(frames)}
    if not frames:
        out["issues"].append("no frames sampled")
        return out
    if expect_size:
        sizes = {im.size for _, im in frames}
        if sizes != {tuple(expect_size)}:
            out["issues"].append(f"aspect: frame size {sorted(sizes)} != {tuple(expect_size)}")
    stats = [frame_stats(im, exclude_bottom) for _, im in frames]
    out["stats"] = [{k: v for k, v in s.items() if k != "hist"} for s in stats]
    # ignore the build-up at the start of a scene (things draw in)
    k0 = min(len(stats) - 1, int(len(stats) * build_frac))
    settled = stats[k0:]
    occ = [s["occupancy"] for s in settled]
    out["occupancy"] = round(float(np.median(occ)), 3)
    if np.median(occ) < BLANK_OCCUPANCY:
        out["issues"].append(f"blank_composition: median occupancy {np.median(occ):.2f} < {BLANK_OCCUPANCY} "
                             "(most of the frame is empty background)")
    lums = [_lum(im) for _, im in frames]
    if exclude_bottom:
        lums = [L[: int(L.shape[0] * (1 - exclude_bottom))] for L in lums]
    diffs = [float(np.mean(np.abs(a - b))) for a, b in zip(lums, lums[1:]) if a.shape == b.shape]
    out["motion"] = round(float(np.mean(diffs)), 2) if diffs else None
    if diffs and np.mean(diffs) < STATIC_DIFF:
        out["issues"].append(f"static_scene: mean change {np.mean(diffs):.2f} < {STATIC_DIFF} between samples")
    # edge clipping: detail on the same edge in most settled frames
    for side in ("left", "right", "top", "bottom"):
        hits = sum(s["edge_contact"][side] > 0.06 for s in settled)
        if hits >= max(2, int(0.7 * len(settled))):
            out["warnings"].append(f"edge_clipping: detail runs into the {side} edge in {hits}/{len(settled)} samples")
    cxs = [abs(s["centroid"][0]) for s in settled]
    cys = [abs(s["centroid"][1]) for s in settled]
    if min(cxs) > BALANCE_MAX or min(cys) > BALANCE_MAX * 1.4:
        out["warnings"].append(f"off_balance: content centroid stays off-centre "
                               f"(x {min(cxs):.2f}, y {min(cys):.2f} of half-frame)")
    out["first_hist"], out["last_hist"] = stats[0]["hist"], stats[-1]["hist"]
    out["first_lum"], out["last_lum"] = stats[0]["mean_lum"], stats[-1]["mean_lum"]
    return out


def manifest_checks(manifest: dict, premium: bool, scene: dict | None = None) -> dict:
    """Policy checks from a scene's render manifest (engine, fallbacks, degradations, layout)."""
    from .engines import TIER

    scene = scene or {}
    out = {"issues": [], "warnings": []}
    eng = manifest.get("engine")
    if manifest.get("status") not in (None, "done"):
        out["issues"].append(f"render failed: {[a.get('error') for a in manifest.get('attempts', [])][-1:]}")
    if manifest.get("fallback_used"):
        msg = (f"silent_fallback: requested {manifest.get('requested_engine')} failed, drawn by {eng}; "
               f"errors: {[a.get('error') for a in manifest.get('attempts', []) if not a.get('ok')]}")
        (out["issues"] if premium else out["warnings"]).append(msg)
    if premium and eng and TIER.get(eng) == "native":
        if scene.get("allow_native") and scene.get("native_reason"):
            out["warnings"].append(f"primitive_engine allowed by scene: {eng} ({scene['native_reason']})")
        else:
            out["issues"].append(f"primitive_engine: premium project rendered with native engine {eng!r}")
    for d in manifest.get("degradations", []) or []:
        (out["issues"] if premium else out["warnings"]).append(f"degraded_dependency: {d}")
    lay = manifest.get("layout") or {}
    for o in lay.get("overflow", []) or []:
        out["issues"].append(f"overflow: {o}")
    fonts = lay.get("fonts") or []
    if fonts:
        out["fonts"] = fonts
    return out


def typography_checks(scene_fonts: dict[str, list[str]], allowed: list[str] | None = None,
                      max_families: int = MAX_FONT_FAMILIES) -> dict:
    """scene_fonts: scene id -> font families actually used (as reported by the engine)."""
    out = {"issues": [], "warnings": []}
    fams = sorted({f for v in scene_fonts.values() for f in v})
    out["families"] = fams
    if allowed:
        alien = {sid: [f for f in v if f not in allowed] for sid, v in scene_fonts.items()}
        alien = {k: v for k, v in alien.items() if v}
        if alien:
            out["issues"].append(f"typography: fonts outside the design system: {alien}")
    if len(fams) > max_families:
        out["warnings"].append(f"typography: {len(fams)} font families in one video ({', '.join(fams)}) > {max_families}")
    return out


def continuity_checks(scene_results: list[tuple[str, dict, dict]]) -> list[str]:
    """scene_results: [(scene_id, scene_spec, scene_checks_result)] in timeline order."""
    out = []
    for (ida, sa, ra), (idb, sb, rb) in zip(scene_results, scene_results[1:]):
        if "last_hist" not in ra or "first_hist" not in rb:
            continue
        d = _hist_dist(ra["last_hist"], rb["first_hist"])
        dl = abs(ra["last_lum"] - rb["first_lum"])
        intended = sb.get("transition") not in (None, "cut") or sb.get("chapter") != sa.get("chapter") \
            or sb.get("continuity_break")
        if d > CONTINUITY_JUMP and dl > 60 and not intended:
            out.append(f"continuity: abrupt jump {ida}->{idb} (histogram {d:.2f}, brightness {dl:.0f}) "
                       "on a hard cut inside a chapter")
    return out


def sample_scene_frames(video: Path, start: float, duration: float, n: int = 6, tmp: Path | None = None) -> list:
    from PIL import Image

    from . import ffmpeg as FF

    tmp = tmp or video.parent / "_vqa"
    tmp.mkdir(parents=True, exist_ok=True)
    out = []
    for k in range(n):
        t = start + duration * (0.06 + 0.88 * k / max(1, n - 1))
        f = tmp / f"{video.stem}-{t:09.3f}.png"
        FF.extract_frame(video, t, f)
        out.append((round(t - start, 2), Image.open(f).convert("RGB")))
    return out


def run_visual_qa(pdir: Path, quality: str = "preview", n: int = 6) -> dict:
    """Scene-by-scene checks over the rendered long video + render manifests."""
    from .config import FORMATS, QUALITY
    from .engines import is_premium
    from .spec import load_project, save_json

    p = load_project(pdir)
    premium = is_premium(p)
    tl = json.loads((pdir / "storyboard" / "timeline.json").read_text(encoding="utf-8"))
    name = "long-video.mp4" if quality == "final" else f"long-video-{quality}.mp4"
    video = pdir / "renders" / name
    rr = pdir / "reports" / f"render-{quality}.json"
    manifests = {s["id"]: s for s in json.loads(rr.read_text(encoding="utf-8")).get("scenes", [])} if rr.exists() else {}
    W = int(round(FORMATS["long"]["width"] * QUALITY[quality]["scale"] / 2) * 2)
    H = int(round(FORMATS["long"]["height"] * QUALITY[quality]["scale"] / 2) * 2)
    specs = {s["id"]: s for s in p["scenes"]}
    scenes, chain, fonts = [], [], {}
    for r in tl["scenes"]:
        sid = r["id"]
        res = {"id": sid, "issues": [], "warnings": []}
        if video.exists():
            fr = sample_scene_frames(video, r["start"], r["duration"], n, pdir / "previews" / "_vqa")
            sc = scene_checks(fr, (W, H), exclude_bottom=0.12 if p.get("burn_captions") else 0.0)
            res.update({k: v for k, v in sc.items() if k not in ("first_hist", "last_hist", "stats")})
            chain.append((sid, specs.get(sid, {}), sc))
        if sid in manifests:
            mc = manifest_checks(manifests[sid], premium, specs.get(sid))
            res["issues"] += mc["issues"]
            res["warnings"] += mc["warnings"]
            res["engine"] = manifests[sid].get("engine")
            if mc.get("fonts"):
                fonts[sid] = mc["fonts"]
        if not premium:  # legacy projects: pixel findings are advisory
            res["warnings"] = res["issues"] + res["warnings"]
            res["issues"] = []
        scenes.append(res)
    typo = typography_checks(fonts, (p.get("design_system") or {}).get("fonts"))
    cont = continuity_checks(chain)
    issues = [f"{s['id']}: {i}" for s in scenes for i in s["issues"]] + (typo["issues"] if premium else [])
    warnings = [f"{s['id']}: {w}" for s in scenes for w in s["warnings"]] + typo["warnings"] + cont \
        + ([] if premium else typo["issues"])
    rep = {"project": p["slug"], "quality": quality, "premium": premium, "video": str(video),
           "scenes": scenes, "typography": typo, "continuity": cont,
           "summary": {"status": "fail" if issues else ("pass_with_warnings" if warnings else "pass"),
                       "issues": issues, "warnings": warnings}}
    save_json(pdir / "reports" / f"visual-qa-{quality}.json", rep)
    return rep
