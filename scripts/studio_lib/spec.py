"""Project spec loading, defaults and validation.

The authoritative JSON Schema lives in `schemas/project.schema.json`; this
module enforces the same rules plus semantic checks a schema cannot express
(unique ids, cue resolvability, engine availability, chapter references).
"""
from __future__ import annotations

import copy
import json
import re
from pathlib import Path

from .config import CATEGORIES, PROJECT_SUBDIRS

SCHEMA_VERSION = 2

SCENE_DEFAULTS = {
    "engine": "auto",
    "elements": [],
    "params": {},
    "illustrative": True,
    "claims": [],
    "assets": [],
    "audio": {},
    "pad": {"lead": 0.35, "tail": 0.55},
}


class SpecError(Exception):
    def __init__(self, errors: list[str]):
        super().__init__("\n".join(errors))
        self.errors = errors


def project_dir(root: Path, slug: str) -> Path:
    return root / slug


def load_project(pdir: Path) -> dict:
    pfile = pdir / "project.json"
    if not pfile.exists():
        raise FileNotFoundError(f"{pfile} not found")
    data = json.loads(pfile.read_text(encoding="utf-8"))
    from .migrate import migrate

    data, _ = migrate(data)
    return normalize(data, pdir)


def normalize(p: dict, pdir: Path) -> dict:
    p = copy.deepcopy(p)
    p.setdefault("language", "en-US")
    p.setdefault("audience", "US")
    p.setdefault("theme", "documentary")
    p.setdefault("fps", 30)
    p.setdefault("tolerance", 0.05)
    p.setdefault("voice", {"provider": "sapi"})
    p.setdefault("music", {"enabled": True, "volume": 0.16})
    p.setdefault("chapters", [])
    p.setdefault("shorts", [])
    p.setdefault("art_direction", {})
    p["_dir"] = str(pdir)
    for s in p.get("scenes", []):
        for k, v in SCENE_DEFAULTS.items():
            s.setdefault(k, copy.deepcopy(v))
        s["_project_dir"] = str(pdir)
    return p


def ensure_dirs(pdir: Path) -> None:
    for d in PROJECT_SUBDIRS:
        (pdir / d).mkdir(parents=True, exist_ok=True)


_CUE = re.compile(r"^cue:([^#]+)(?:#(\d+))?$")


def validate(p: dict, *, engines_available: dict | None = None) -> tuple[list[str], list[str]]:
    """Returns (errors, warnings)."""
    from .engines import ENGINES
    from .engines.elements import ELEMENT_TYPES

    errs: list[str] = []
    warns: list[str] = []
    from .config import SKILL_ROOT
    from .jsonschema_lite import validate as schema_validate

    schema = json.loads((SKILL_ROOT / "schemas" / "project.schema.json").read_text(encoding="utf-8"))
    errs += [f"schema: {e}" for e in schema_validate(_strip_private(p), schema)]
    for k in ("slug", "title", "category", "scenes"):
        if k not in p:
            errs.append(f"project: missing '{k}'")
    if p.get("category") and p["category"] not in CATEGORIES:
        errs.append(f"project: category must be one of {sorted(CATEGORIES)}")
    if not isinstance(p.get("target_duration", 0), (int, float)) or p.get("target_duration", 0) <= 0:
        errs.append("project: target_duration (seconds) required and > 0")
    if p.get("fictional") and not p.get("disclaimer"):
        errs.append("project: fictional projects need a 'disclaimer' (shown on screen + in description)")
    chapters = {c["id"] for c in p.get("chapters", [])}
    ids = set()
    for i, s in enumerate(p.get("scenes", [])):
        sid = s.get("id") or f"#{i}"
        if not s.get("id"):
            errs.append(f"scene {sid}: missing id")
        if sid in ids:
            errs.append(f"scene {sid}: duplicate id")
        ids.add(sid)
        if not str(s.get("narration", "")).strip() and not s.get("min_duration"):
            errs.append(f"scene {sid}: needs narration or min_duration")
        eng = s.get("engine", "auto")
        if eng != "auto" and eng not in ENGINES:
            errs.append(f"scene {sid}: unknown engine '{eng}'")
        if engines_available and eng in engines_available and not engines_available[eng].get("ok"):
            warns.append(f"scene {sid}: engine '{eng}' unavailable here; fallback will be used")
        if chapters and s.get("chapter") not in chapters:
            errs.append(f"scene {sid}: chapter '{s.get('chapter')}' not declared")
        if eng in ("image_whiteboard",) and not s.get("params", {}).get("src"):
            errs.append(f"scene {sid}: image_whiteboard needs params.src")
        if eng == "huashu_clip":
            prm = s.get("params", {})
            shots = prm.get("shots")
            if shots is not None and (not shots or any(not sh.get("grammar") for sh in shots)):
                errs.append(f"scene {sid}: every huashu_clip shot needs a grammar")
            elif shots is None and not prm.get("grammar"):
                errs.append(f"scene {sid}: huashu_clip needs params.grammar (or params.shots)")
        norm = lambda w: re.sub(r"[^a-z0-9$%.]", "", w.lower())  # noqa: E731  (same rule as SceneContext.resolve_time)
        narr_words = [norm(w) for w in str(s.get("narration", "")).split()]
        for j, el in enumerate(s.get("elements", [])):
            if el.get("type") not in ELEMENT_TYPES:
                errs.append(f"scene {sid} element {j}: unknown type {el.get('type')!r}")
            for key in ("at", "until"):
                v = el.get(key)
                if isinstance(v, str):
                    m = _CUE.match(v)
                    if m and not any(w.startswith(norm(m.group(1))) for w in narr_words):
                        warns.append(f"scene {sid} element {j}: cue word '{m.group(1)}' not in narration")
            if el.get("type") == "image":
                src = Path(p.get("_dir", ".")) / el.get("src", "")
                if not src.exists():
                    errs.append(f"scene {sid} element {j}: missing image asset {el.get('src')}")
        for a in s.get("assets", []):
            if not a.get("license"):
                errs.append(f"scene {sid}: asset {a.get('path')} has no license record")
    for sh in p.get("shorts", []):
        if not sh.get("id"):
            errs.append("short: missing id")
        for seg in sh.get("segments", []):
            if seg.get("from") and seg["from"] not in ids:
                errs.append(f"short {sh.get('id')}: segment source '{seg['from']}' not a scene")
    return errs, warns


def save_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    clean = _strip_private(data)
    path.write_text(json.dumps(clean, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _strip_private(d):
    if isinstance(d, dict):
        return {k: _strip_private(v) for k, v in d.items() if not str(k).startswith("_")}
    if isinstance(d, list):
        return [_strip_private(x) for x in d]
    return d
