"""Fact ledger + rights gate.

research/facts.json:
  {"facts": [{"id", "claim", "status", "sources": [{"url", "title", "published", "accessed"}],
              "risk": "low|high", "framing": "...", "notes": "..."}]}

status:
  verified      >= 1 source with url + published/accessed date
  hypothesis    must be framed as such on screen / in narration ("framing" field)
  fictional     part of a declared fictional story (project.fictional must be true)
  illustrative  a visual dramatisation, not a factual claim
  unverified    BLOCKS export when used by a scene

Rights: project.rights_issues = [{"item", "status": "resolved|unresolved", "note"}];
any unresolved item blocks the final export.
"""
from __future__ import annotations

import json
from pathlib import Path

from .config import HIGH_RISK_CATEGORIES


def load_facts(pdir: Path) -> list[dict]:
    f = pdir / "research" / "facts.json"
    if not f.exists():
        return []
    return json.loads(f.read_text(encoding="utf-8")).get("facts", [])


def gate(p: dict, pdir: Path) -> dict:
    facts = {f["id"]: f for f in load_facts(pdir)}
    blockers, warnings = [], []
    used = set()
    for s in p.get("scenes", []):
        for cid in s.get("claims", []):
            used.add(cid)
            f = facts.get(cid)
            if not f:
                blockers.append(f"scene {s['id']}: claim '{cid}' not in research/facts.json")
                continue
            st = f.get("status")
            if st == "unverified":
                blockers.append(f"scene {s['id']}: claim '{cid}' is unverified")
            elif st == "verified":
                srcs = [x for x in f.get("sources", []) if x.get("url") and (x.get("published") or x.get("accessed"))]
                if not srcs:
                    blockers.append(f"claim '{cid}': marked verified but has no dated source URL")
            elif st == "hypothesis" and not f.get("framing"):
                blockers.append(f"claim '{cid}': hypothesis without on-screen framing")
            elif st == "fictional" and not p.get("fictional"):
                blockers.append(f"claim '{cid}': fictional claim in a non-fictional project")
            if p.get("category") in HIGH_RISK_CATEGORIES and f.get("risk") == "high" and st != "verified" \
                    and not (st == "fictional" and p.get("fictional")):
                blockers.append(f"claim '{cid}': high reputational risk requires 'verified' status")
    if p.get("fictional") and not p.get("disclaimer"):
        blockers.append("fictional project without disclaimer")
    for r in p.get("rights_issues", []):
        if r.get("status") != "resolved":
            blockers.append(f"rights: {r.get('item')} unresolved ({r.get('note', '')})")
    unused = sorted(set(facts) - used)
    if unused:
        warnings.append(f"{len(unused)} ledger facts not referenced by any scene")
    n_by = {}
    for f in facts.values():
        n_by[f.get("status")] = n_by.get(f.get("status"), 0) + 1
    return {"blockers": blockers, "warnings": warnings, "facts": len(facts), "by_status": n_by,
            "summary": f"{len(facts)} facts {n_by}; {len(blockers)} blockers"}


def asset_license_report(p: dict, pdir: Path, extra: list[dict] | None = None) -> str:
    lines = [f"# Asset & license report — {p['title']}", "",
             "| Asset | Used in | Source | License | Notes |", "|---|---|---|---|---|"]
    seen = set()
    for s in p.get("scenes", []):
        for a in s.get("assets", []):
            key = a.get("path")
            if key in seen:
                continue
            seen.add(key)
            lines.append(f"| `{a.get('path')}` | {s['id']} | {a.get('source', '—')} | {a.get('license', '**MISSING**')} | {a.get('notes', '')} |")
    for e in extra or []:
        lines.append(f"| {e['asset']} | {e['used']} | {e['source']} | {e['license']} | {e.get('notes', '')} |")
    lines += ["", "Rights issues: " + (", ".join(f"{r['item']} ({r['status']})" for r in p.get("rights_issues", [])) or "none recorded")]
    return "\n".join(lines) + "\n"
