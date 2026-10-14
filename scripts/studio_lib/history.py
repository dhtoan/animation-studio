"""historical-documentary-research: source tiers, claim classes, fact-check report.

Claim classes (dossier) → ledger status used by research.gate:
  established        → verified        (needs ≥1 dated source URL; tier-1/2 preferred)
  contested          → contested       (needs `framing`, e.g. "estimates range from … according to …")
  allegation         → allegation      (needs attribution in `framing`; never stated as fact)
  reconstruction     → illustrative    (labelled on screen as recreation)
  fictional          → fictional       (only in fictional projects)
"""
from __future__ import annotations

import re
from pathlib import Path
from urllib.parse import urlparse

TIERS = {
    1: ["archives.gov", "loc.gov", "si.edu", "smithsonianmag.com", "nationalww2museum.org", "history.army.mil",
        "army.mil", "navy.mil", "af.mil", "govinfo.gov", "congress.gov", "cia.gov", "nsa.gov", "state.gov",
        "presidentiallibraries.us", "fdrlibrary.org", "trumanlibrary.gov", "eisenhowerlibrary.gov", "jfklibrary.org",
        "nps.gov", "usmint.gov", "defense.gov", "nara.gov"],
    2: [".edu", "jstor.org", "britannica.com", "oup.com", "cambridge.org", "imperialwarmuseums.org.uk",
        "gouvernement.lu", "speaker.gov", "senate.gov", "house.gov"],
    3: ["apnews.com", "reuters.com", "nytimes.com", "washingtonpost.com", "cbsnews.com", "npr.org", "bbc.co.uk",
        "bbc.com", "pbs.org", "wsj.com", "theatlantic.com"],
}

CLASS_TO_STATUS = {"established": "verified", "contested": "contested", "allegation": "allegation",
                   "reconstruction": "illustrative", "fictional": "fictional"}


def tier(url: str) -> int:
    host = urlparse(url).netloc.lower()
    for t, doms in TIERS.items():
        if any(host.endswith(d) or (d.startswith(".") and host.endswith(d)) for d in doms):
            return t
    return 4


def ledger_from_dossier(dossier: dict, accessed: str) -> dict:
    src = {s["id"]: s for s in dossier.get("sources", [])}
    facts = []
    for c in dossier.get("claims", []):
        sources = [{"url": src[i]["url"], "title": src[i].get("title"), "publisher": src[i].get("publisher"),
                    "published": src[i].get("published"), "accessed": src[i].get("accessed") or accessed,
                    "tier": tier(src[i]["url"])} for i in c.get("source_ids", []) if i in src]
        status = CLASS_TO_STATUS.get(c.get("status"), "unverified")
        f = {"id": c["id"], "claim": c["claim"], "status": status, "class": c.get("status"), "sources": sources,
             "risk": "high" if c.get("status") in ("allegation",) else "low", "notes": c.get("notes", "")}
        if status in ("contested", "allegation"):
            f["framing"] = c.get("framing") or ("Attributed on screen to its sources; presented as "
                                                + ("a contested estimate" if status == "contested" else "an allegation"))
        facts.append(f)
    return {"facts": facts}


def fact_check_report(p: dict, facts: list[dict]) -> str:
    byid = {f["id"]: f for f in facts}
    used = {c for s in p.get("scenes", []) for c in s.get("claims", [])}
    L = [f"# Fact-check report — {p['title']}", "",
         "| Claim | Class | Best source tier | Sources | Used in | Framing / notes |", "|---|---|---|---|---|---|"]
    for cid in sorted(used):
        f = byid.get(cid)
        if not f:
            L.append(f"| `{cid}` | **MISSING** | — | — | — | not in ledger |")
            continue
        scenes = ", ".join(s["id"] for s in p["scenes"] if cid in s.get("claims", []))
        best = min((s.get("tier", 4) for s in f.get("sources", [])), default=None)
        srcs = "; ".join(f"[{(s.get('publisher') or urlparse(s['url']).netloc)}]({s['url']})" for s in f.get("sources", [])[:3])
        L.append(f"| `{cid}` {f['claim'][:90]} | {f.get('class', f['status'])} | {best or '—'} | {srcs or '—'} | {scenes} | "
                 f"{(f.get('framing') or f.get('notes') or '')[:120]} |")
    weak = [cid for cid in used if cid in byid and byid[cid]["status"] == "verified"
            and min((s.get("tier", 4) for s in byid[cid]["sources"]), default=4) >= 4]
    L += ["", f"Claims used: {len(used)} · verified only by tier-4 sources: {len(weak)} {weak[:10]}"]
    return "\n".join(L) + "\n"


def scan_narration_numbers(p: dict, facts: list[dict]) -> list[str]:
    """Flag scenes that state years/numbers but cite no claim."""
    out = []
    for s in p.get("scenes", []):
        if re.search(r"\b(1[6-9]\d\d|20\d\d)\b|\b\d[\d,]{2,}\b", s.get("narration", "")) and not s.get("claims"):
            out.append(f"{s['id']}: states a date/number without a claim id")
    return out
