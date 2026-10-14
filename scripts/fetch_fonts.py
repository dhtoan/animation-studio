"""OFL fonts that lemo-opuscar demos request but do not ship (stdlib only).

  python scripts/fetch_fonts.py            restore tools/fonts/ from tools/fonts/manifest.json
                                           (each file's source URL + sha256; OFL checked via METADATA.pb)
  python scripts/fetch_fonts.py --check    report missing / altered files (exit 1 if any)
  python scripts/fetch_fonts.py --rebuild  rediscover what the demos request (needs the lemo checkout,
                                           --lemo PATH or _upstream/lemo-opuscar) and rewrite the manifest

Sources: github.com/google/fonts (raw ofl/<slug>/...) for whole families, and the Google Fonts CSS2 API
(fonts.googleapis.com -> fonts.gstatic.com) for the unicode-range slices halftone-dossier requests as
fonts/fN.woff2. The binaries are git-ignored; only the manifest is tracked. Never writes into the
upstream clone. html_seek serves these files for missing font requests (see engines/html_seek.py).
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LEMO = ROOT / "_upstream" / "lemo-opuscar"
OUT = ROOT / "tools" / "fonts"
RAW = "https://raw.githubusercontent.com/google/fonts/main/ofl/{slug}/{file}"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/130.0 Safari/537.36")  # same UA as halftone-dossier/demo/fetch_fonts.mjs


def get(url: str) -> bytes:
    for i in range(4):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=60) as r:
                return r.read()
        except Exception as e:  # noqa: BLE001
            if i == 3:
                raise
            print("retry", url, e)
            time.sleep(2 + 2 * i)
    raise RuntimeError(url)


# demo -> {requested path relative to the demo dir: (slug, google/fonts file, family, weight/style note)}
DEMOS = {
    "whiteboard": {"fonts/ArchitectsDaughter-Regular.ttf": ("architectsdaughter", "ArchitectsDaughter-Regular.ttf", "Architects Daughter", "400")},
    "blueprint": {
        "fonts/ArchitectsDaughter-Regular.ttf": ("architectsdaughter", "ArchitectsDaughter-Regular.ttf", "Architects Daughter", "400"),
        "fonts/B612-Regular.ttf": ("b612", "B612-Regular.ttf", "B612", "400"),
        "fonts/B612-Bold.ttf": ("b612", "B612-Bold.ttf", "B612", "700"),
        "fonts/B612Mono-Regular.ttf": ("b612mono", "B612Mono-Regular.ttf", "B612 Mono", "400"),
        "fonts/Allura-Regular.ttf": ("allura", "Allura-Regular.ttf", "Allura", "400"),
    },
    "dataviz": {
        "fonts/Newsreader-VF.ttf": ("newsreader", "Newsreader[opsz,wght].ttf", "Newsreader", "200-800 variable"),
        "fonts/Newsreader-Italic-VF.ttf": ("newsreader", "Newsreader-Italic[opsz,wght].ttf", "Newsreader", "200-800 italic variable"),
        "fonts/Caveat-VF.ttf": ("caveat", "Caveat[wght].ttf", "Caveat", "400-700 variable"),
        "fonts/IBMPlexMono-Regular.ttf": ("ibmplexmono", "IBMPlexMono-Regular.ttf", "IBM Plex Mono", "400"),
        "fonts/IBMPlexMono-Medium.ttf": ("ibmplexmono", "IBMPlexMono-Medium.ttf", "IBM Plex Mono", "500"),
    },
    "silent-film": {
        "fonts/OldStandard-Regular.ttf": ("oldstandardtt", "OldStandard-Regular.ttf", "Old Standard TT", "400"),
        "fonts/OldStandard-Italic.ttf": ("oldstandardtt", "OldStandard-Italic.ttf", "Old Standard TT", "400 italic"),
        "fonts/OldStandard-Bold.ttf": ("oldstandardtt", "OldStandard-Bold.ttf", "Old Standard TT", "700"),
        "fonts/PlayfairDisplay[wght].ttf": ("playfairdisplay", "PlayfairDisplay[wght].ttf", "Playfair Display", "400-900 variable"),
        "fonts/PlayfairDisplay-Italic[wght].ttf": ("playfairdisplay", "PlayfairDisplay-Italic[wght].ttf", "Playfair Display", "400-900 italic variable"),
        "fonts/PlayfairDisplaySC-Black.ttf": ("playfairdisplaysc", "PlayfairDisplaySC-Black.ttf", "Playfair Display SC", "900"),
        "fonts/PlayfairDisplaySC-Bold.ttf": ("playfairdisplaysc", "PlayfairDisplaySC-Bold.ttf", "Playfair Display SC", "700"),
    },
    "iso-infographic": {"fonts/Jost.ttf": ("jost", "Jost[wght].ttf", "Jost", "100-900 variable")},
    "dark-keynote": {
        "fonts/Inter.ttf": ("inter", "Inter[opsz,wght].ttf", "Inter", "100-900 variable"),
        "fonts/InterTight-var.woff2": ("intertight", "InterTight[wght].ttf", "Inter Tight", "100-900 variable (TTF served for a .woff2 request)"),
        "fonts/JetBrainsMono-var.ttf": ("jetbrainsmono", "JetBrainsMono[wght].ttf", "JetBrains Mono", "100-800 variable"),
    },
    "swiss-motion": {
        "fonts/Archivo-VF.ttf": ("archivo", "Archivo[wdth,wght].ttf", "Archivo", "wdth 62-125, wght 100-900 variable"),
        "fonts/UnifrakturMaguntia-Regular.ttf": ("unifrakturmaguntia", "UnifrakturMaguntia-Book.ttf", "UnifrakturMaguntia", "400"),
        "fonts/DMSerifDisplay-Regular.ttf": ("dmserifdisplay", "DMSerifDisplay-Regular.ttf", "DM Serif Display", "400"),
    },
    "spy-titles": {
        "fonts/LeagueGothic.ttf": ("leaguegothic", "LeagueGothic[wdth].ttf", "League Gothic", "400 (wdth variable)"),
        "fonts/LeagueSpartan.ttf": ("leaguespartan", "LeagueSpartan[wght].ttf", "League Spartan", "100-900 variable"),
    },
}
HALFTONE_SPECS = ["ZCOOL+KuaiLe", "Noto+Serif+SC:wght@900", "Bagel+Fat+One", "JetBrains+Mono:wght@500;800",
                  "Noto+Sans+SC:wght@500;900"]
SLUG = {"ZCOOL KuaiLe": "zcoolkuaile", "Noto Serif SC": "notoserifsc", "Bagel Fat One": "bagelfatone",
        "JetBrains Mono": "jetbrainsmono", "Noto Sans SC": "notosanssc"}

FACE = re.compile(r"@font-face\s*{(.*?)}", re.S)


def faces(css: str):
    for body in FACE.findall(css):
        fam = re.search(r"font-family:\s*'([^']+)'", body).group(1)
        w = re.search(r"font-weight:\s*([^;]+);", body).group(1).strip()
        st = re.search(r"font-style:\s*([^;]+);", body).group(1).strip()
        url = re.search(r"url\(([^)]+)\)", body).group(1).strip("'\"")
        ur = re.search(r"unicode-range:\s*([^;]+);", body)
        yield fam, w, st, (ur.group(1).replace(" ", "") if ur else ""), url


def cps(ur: str) -> set:
    out = set()
    for part in ur.split(","):
        a = part.strip().upper().removeprefix("U+")
        if not a:
            continue
        if "-" in a:
            x, y = a.split("-")
            out.update(range(int(x, 16), int(y, 16) + 1))
        else:
            out.add(int(a, 16))
    return out


def license_ok(slug: str) -> str:
    """Read METADATA.pb's license field; only OFL is accepted."""
    meta = OUT / slug / "METADATA.pb"
    if not meta.exists():
        meta.parent.mkdir(parents=True, exist_ok=True)
        meta.write_bytes(get(RAW.format(slug=slug, file="METADATA.pb")))
    m = re.search(r'license:\s*"([^"]+)"', meta.read_text(encoding="utf-8"))
    lic = m.group(1) if m else "?"
    if lic != "OFL":
        raise SystemExit(f"{slug}: licence {lic} is not OFL")
    ofl = OUT / slug / "OFL.txt"
    if not ofl.exists():
        ofl.write_bytes(get(RAW.format(slug=slug, file="OFL.txt")))
    name = re.search(r'name:\s*"([^"]+)"', meta.read_text(encoding="utf-8")).group(1)
    return name


def rebuild():
    OUT.mkdir(parents=True, exist_ok=True)
    families: dict[str, dict] = {}
    paths: dict[str, str] = {}
    demos: dict[str, dict] = {}

    def fam(slug):
        if slug not in families:
            name = license_ok(slug)
            families[slug] = {"name": name, "license": "OFL-1.1", "license_file": f"{slug}/OFL.txt",
                              "metadata": f"{slug}/METADATA.pb",
                              "source": f"https://github.com/google/fonts/tree/main/ofl/{slug}", "files": []}
        return families[slug]

    for demo, reqs in DEMOS.items():
        demos[demo] = {}
        for req, (slug, gfile, family, note) in reqs.items():
            f = fam(slug)
            dst = OUT / slug / gfile
            if not dst.exists():
                print("get", slug, gfile)
                dst.write_bytes(get(RAW.format(slug=slug, file=urllib.request.quote(gfile))))
            local = f"{slug}/{gfile}"
            if gfile not in f["files"]:
                f["files"].append(gfile)
            rel = f"styles/{demo}/demo/{req}"
            paths[rel] = local
            demos[demo][req] = {"local": local, "family": family, "weight": note,
                                "exact_name": Path(req).name == gfile}

    # halftone-dossier: Google Fonts unicode-range slices, matched by (family, weight, style, unicode-range)
    local_css = (LEMO / "styles/halftone-dossier/demo/fonts.css").read_text(encoding="utf-8")
    want = {}
    for fm, w, st, ur, url in faces(local_css):
        want[(fm, w, st, ur)] = url  # url = fonts/fN.woff2
    have = {}
    for spec in HALFTONE_SPECS:
        css = get(f"https://fonts.googleapis.com/css2?family={spec}&display=block").decode("utf-8")
        for fm, w, st, ur, url in faces(css):
            have[(fm, w, st, ur)] = url
    demos["halftone-dossier"] = {}
    unmatched = []
    near_note = {}
    for key, req in sorted(want.items(), key=lambda kv: int(re.search(r"f(\d+)", kv[1]).group(1))):
        fm, w, st, ur = key
        slug = SLUG[fm]
        f = fam(slug)
        near = None
        if key not in have:  # Google re-cut this range since the demo was made: take the same face's slice with the largest overlap
            cand = [(len(cps(ur) & cps(k[3])) / max(1, len(cps(ur))), u) for k, u in have.items() if k[:3] == key[:3]]
            if cand:
                near = max(cand)
        if key in have or (near and near[0] > 0.9):
            url = have[key] if key in have else near[1]
            name = f"{fm.replace(' ', '')}-{Path(url).name}"  # variable slices are shared by weights
            dst = OUT / slug / "gf-slices" / name
            if not dst.exists():
                dst.parent.mkdir(parents=True, exist_ok=True)
                dst.write_bytes(get(url))
            local = f"{slug}/gf-slices/{name}"
            src = url
            if key not in have:
                near_note[req] = round(near[0], 4)
        else:
            unmatched.append(req)
            local, src = None, None
        paths[f"styles/halftone-dossier/demo/{req}"] = local
        demos["halftone-dossier"][req] = {"local": local, "family": fm, "weight": w, "gstatic": src,
                                          "match": ("exact unicode-range slice" if req not in near_note else
                                                    f"nearest slice of the same face, covers {near_note[req]:.1%} of the requested range")
                                                   if local else "unmatched"}
    if unmatched:
        print("unmatched halftone slices:", len(unmatched))
    for slug in {SLUG[k] for k in SLUG}:
        if (OUT / slug / "gf-slices").exists():
            n = len(list((OUT / slug / "gf-slices").glob("*.woff2")))
            fam(slug)["files"].append(f"gf-slices/*.woff2 ({n} Google Fonts unicode-range slices)")

    # unique basenames (fN.woff2 is ambiguous across the library, so it is only resolvable by full path)
    counts = {}
    for rel in paths:
        counts.setdefault(Path(rel).name, set()).add(paths[rel])
    by_basename = {b: next(iter(v)) for b, v in sorted(counts.items())
                   if len(v) == 1 and next(iter(v)) and not re.fullmatch(r"f\d+\.woff2", b)}
    manifest = {
        "about": "OFL fonts requested by lemo-opuscar demos but not tracked in its git. Paths are relative to this file's folder. "
                 "'paths' keys are request paths relative to the lemo library root; 'by_basename' holds the unambiguous names.",
        "generated": time.strftime("%Y-%m-%d"),
        "families": families,
        "demos": demos,
        "paths": paths,
        "by_basename": by_basename,
        "unavailable": [{"request": r, "reason": "no matching Google Fonts slice today"} for r in sorted(set(unmatched))],
        "files": file_table(families, demos),
    }
    (OUT / "manifest.json").write_text(json.dumps(manifest, indent=1, ensure_ascii=False), encoding="utf-8")
    print("families", len(families), "paths", len(paths), "basenames", len(by_basename), "unmatched", len(unmatched))


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def file_table(families: dict, demos: dict) -> dict:
    """local path -> {url, sha256, bytes, family}: what restore() needs to reproduce tools/fonts."""
    out = {}
    gst = {r["local"]: r["gstatic"] for r in demos.get("halftone-dossier", {}).values() if r.get("local")}
    for slug in families:
        for p in sorted((OUT / slug).rglob("*")):
            if not p.is_file():
                continue
            local = p.relative_to(OUT).as_posix()
            url = gst.get(local) or RAW.format(slug=slug, file=urllib.request.quote(p.name))
            out[local] = {"url": url, "sha256": sha256(p), "bytes": p.stat().st_size, "family": slug}
    return out


def load_manifest() -> dict:
    p = OUT / "manifest.json"
    if not p.exists():
        raise SystemExit(f"{p} is missing: run with --rebuild")
    m = json.loads(p.read_text(encoding="utf-8"))
    if not m.get("files"):
        raise SystemExit("manifest has no 'files' table: run with --rebuild")
    return m


def check(m: dict) -> list[str]:
    bad = []
    for local, f in m["files"].items():
        p = OUT / local
        if not p.exists():
            bad.append(f"missing  {local}")
        elif p.stat().st_size != f["bytes"] or sha256(p) != f["sha256"]:
            bad.append(f"altered  {local}")
    return bad


def restore(m: dict) -> int:
    todo = [local for local in m["files"] if check({"files": {local: m["files"][local]}})]
    fams = sorted({m["files"][x]["family"] for x in todo})
    for slug in fams:   # licence first: METADATA.pb must say OFL before any font of the family is fetched
        meta = OUT / slug / "METADATA.pb"
        if not meta.exists() or check({"files": {f"{slug}/METADATA.pb": m["files"].get(f"{slug}/METADATA.pb", {"bytes": -1, "sha256": ""})}}):
            meta.parent.mkdir(parents=True, exist_ok=True)
            meta.write_bytes(get(m["files"][f"{slug}/METADATA.pb"]["url"]))
        lic = re.search(r'license:\s*"([^"]+)"', meta.read_text(encoding="utf-8"))
        if not lic or lic.group(1) != "OFL":
            raise SystemExit(f"{slug}: METADATA.pb licence is {lic.group(1) if lic else '?'}, not OFL: refusing")
    n = 0
    for local in todo:
        f, p = m["files"][local], OUT / local
        if local.endswith("METADATA.pb") and not check({"files": {local: f}}):
            continue
        data = get(f["url"])
        if hashlib.sha256(data).hexdigest() != f["sha256"]:
            print(f"warning: {local}: upstream bytes changed (sha256 differs); kept the new file")
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_bytes(data)
        n += 1
    return n


def main():
    global LEMO
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report missing or altered files (exit 1 if any)")
    ap.add_argument("--rebuild", action="store_true", help="rediscover the demos' font requests and rewrite the manifest")
    ap.add_argument("--lemo", help="lemo-opuscar checkout (for --rebuild)")
    a = ap.parse_args()
    if a.rebuild:
        if a.lemo:
            LEMO = Path(a.lemo)
        rebuild()
        return 0
    m = load_manifest()
    if a.check:
        bad = check(m)
        for b in bad:
            print(b)
        print(f"{len(m['files']) - len(bad)}/{len(m['files'])} font files present" + ("" if not bad else "; run: python scripts/fetch_fonts.py"))
        return 1 if bad else 0
    n = restore(m)
    bad = check(m)
    print(f"fetched {n}; {len(m['files']) - len(bad)}/{len(m['files'])} present")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
