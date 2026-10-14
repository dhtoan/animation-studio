"""youtube-niche-intelligence: evidence ledger + transparent opportunity scoring.

Inputs (all optional, all cited):
  research/niche/evidence.json   signals gathered by the agent from public pages,
                                 official reports, or the Data API (`collect_api`)
  research/niche/candidates.json topic ideas with factor assessments
  studio.config / project niche_weights   weight overrides

A factor score is 0–10 and MUST cite evidence ids or carry `assessed_by:"agent"`
with a rationale. Missing factors are excluded from the weighted sum and lower
the confidence; they are never imputed. RPM is never a number unless it comes
from the user's own YouTube Analytics (category "verified"); otherwise only the
revenue *evidence category* is recorded.

The score ranks ideas for production planning. It is not a forecast.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import re
import statistics
from pathlib import Path

DEFAULT_WEIGHTS = {
    "audience_fit_us50": 0.25,
    "revenue_evidence": 0.20,
    "demand": 0.15,
    "competition_gap": 0.15,
    "evergreen": 0.10,
    "storytelling": 0.10,
    "feasibility": 0.05,
}

REVENUE_EVIDENCE = {
    # category -> max score it can justify (strength of evidence, NOT an RPM estimate)
    "verified": 10,               # user's own Analytics for this topic type
    "public-creator-reported": 6, # a named creator published figures (single channel, dated)
    "industry-estimate": 4,       # third-party estimate, methodology unclear
    "ad-demand-proxy": 5,         # e.g., advertiser categories present, mid-roll friendly long-form
    "unknown": 0,
}

WINDOWS = {"7d": 7, "30d": 30, "90d": 90, "12m": 365}


def load_json(p: Path, default):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def score_candidate(c: dict, weights: dict | None = None, evidence_ids: set | None = None) -> dict:
    w = dict(DEFAULT_WEIGHTS)
    w.update(weights or {})
    total_w = sum(w.values())
    w = {k: v / total_w for k, v in w.items()}
    used, missing, problems = {}, [], []
    for f, wt in w.items():
        fx = (c.get("factors") or {}).get(f)
        if not fx or fx.get("score") is None:
            missing.append(f)
            continue
        s = float(fx["score"])
        if not 0 <= s <= 10:
            problems.append(f"{f}: score {s} out of range")
            continue
        ev = fx.get("evidence", [])
        if not ev and fx.get("assessed_by") != "agent":
            problems.append(f"{f}: no evidence ids and not marked as agent assessment")
            continue
        if evidence_ids is not None and any(e not in evidence_ids for e in ev):
            problems.append(f"{f}: cites unknown evidence {[e for e in ev if e not in evidence_ids]}")
        if f == "revenue_evidence":
            cat = fx.get("category", "unknown")
            cap = REVENUE_EVIDENCE.get(cat, 0)
            if s > cap:
                problems.append(f"revenue_evidence capped from {s} to {cap} (category {cat})")
                s = cap
        # evidence about the broader niche (pillar) counts half as much as topic-specific evidence
        strength = 0.0 if not ev else (0.5 if fx.get("evidence_scope") == "pillar" else 1.0)
        used[f] = (s, wt, strength)
    covered = sum(wt for _, wt, _ in used.values())
    raw = sum(s * wt for s, wt, _ in used.values())
    score = round(raw / covered * 10, 1) if covered else None  # 0–100 on covered factors
    evidenced = sum(wt * has for _, wt, has in used.values())
    confidence = round(covered * (0.5 + 0.5 * (evidenced / covered if covered else 0)), 2)
    label = "high" if confidence >= 0.75 else "medium" if confidence >= 0.5 else "low"
    return {"score": score, "confidence": confidence, "confidence_label": label, "missing": missing,
            "problems": problems, "weights": w,
            "breakdown": {f: {"score": s, "weight": round(wt, 3), "evidenced": bool(has), "evidence_strength": has}
                          for f, (s, wt, has) in used.items()}}


def rank(cands: list[dict], weights: dict | None = None, evidence: list[dict] | None = None) -> list[dict]:
    ids = {e["id"] for e in evidence} if evidence is not None else None
    out = []
    for c in cands:
        r = score_candidate(c, weights, ids)
        out.append({**c, "result": r})
    # rank by score, then confidence; ideas without any score go last
    out.sort(key=lambda x: (x["result"]["score"] is None, -(x["result"]["score"] or 0), -x["result"]["confidence"]))
    for i, x in enumerate(out, 1):
        x["rank"] = i
    return out


def revenue_scenarios(views: list[int], rpm_assumptions: dict[str, float], source: str) -> list[dict]:
    """Illustrative arithmetic only. Every row carries its assumption + source label."""
    if not source:
        raise ValueError("revenue scenarios require a labelled assumption source")
    return [{"views": v, "assumed_rpm_usd": r, "label": k, "estimated_revenue_usd": round(v / 1000 * r, 2),
             "assumption_source": source, "note": "ASSUMPTION — not a forecast"}
            for k, r in rpm_assumptions.items() for v in views]


# ------------------------------------------------------------------ live collection (Data API)
def collect_api(query: str, api, today: dt.date | None = None, per_channel_baseline: int = 15) -> dict:
    """~240 quota units: 2 searches + stats + channel baselines for top channels."""
    today = today or dt.date.today()
    def since(days):
        return (today - dt.timedelta(days=days)).isoformat() + "T00:00:00Z"
    res12 = api.search(query, since(365), order="viewCount", duration="long")
    res90 = api.search(query, since(90), order="relevance", duration=None)
    ids = list({r["id"]: r for r in res12 + res90})
    vids = api.videos(ids)
    chans = api.channels(list({v["channelId"] for v in vids.values()}))
    top_ch = sorted(chans, key=lambda c: -sum(v["views"] or 0 for v in vids.values() if v["channelId"] == c))[:8]
    baselines = {}
    for c in top_ch:
        try:
            up = api.recent_uploads(chans[c]["uploads"], per_channel_baseline)
            bv = api.videos(up)
            baselines[c] = [x["views"] for x in bv.values() if x["views"] is not None and not is_short_safe(x)]
        except Exception:
            baselines[c] = []
    from .youtube_api import outlier_ratio

    rows = []
    for vid, v in vids.items():
        age = max(1, (today - dt.date.fromisoformat(v["published"][:10])).days)
        rows.append({"id": vid, "title": v["title"], "channel": chans.get(v["channelId"], {}).get("title"),
                     "views": v["views"], "age_days": age, "views_per_day": round((v["views"] or 0) / age, 1),
                     "duration_s": v["duration_s"],
                     "engagement": (round(((v["likes"] or 0) + (v["comments"] or 0)) / v["views"], 4)
                                    if v["views"] and v["likes"] is not None else None),
                     "outlier": outlier_ratio(v["views"], baselines.get(v["channelId"], [])) if age >= 7 else None,
                     "subscribers": chans.get(v["channelId"], {}).get("subscribers")})
    longform = [r for r in rows if r["duration_s"] and r["duration_s"] > 180]
    small = [r for r in longform if r["subscribers"] is not None and r["subscribers"] < 100_000 and (r["outlier"] or 0) >= 3]
    return {
        "query": query, "region": "US", "collected": today.isoformat(), "quota_used": api.used,
        "videos": rows,
        "summary": {
            "median_views_12m_top": statistics.median([r["views"] for r in rows if r["views"]]) if rows else None,
            "median_views_per_day": statistics.median([r["views_per_day"] for r in rows]) if rows else None,
            "longform_share": round(len(longform) / len(rows), 2) if rows else None,
            "outlier_rate": round(sum(1 for r in rows if (r["outlier"] or 0) >= 3) / max(1, sum(1 for r in rows if r["outlier"] is not None)), 2),
            "small_channel_outliers": len(small),
            "channel_concentration_top3": _concentration(rows),
            "audience_age": "unknown (not available from public data)",
            "us_viewer_share": "unknown (not available from public data)",
            "rpm": "unknown (only owned-channel Analytics can measure RPM)",
        },
    }


def is_short_safe(v):
    return v.get("duration_s") is not None and v["duration_s"] <= 180


def _concentration(rows):
    by = {}
    for r in rows:
        by[r["channel"]] = by.get(r["channel"], 0) + (r["views"] or 0)
    tot = sum(by.values()) or 1
    return round(sum(sorted(by.values(), reverse=True)[:3]) / tot, 2)


# ------------------------------------------------------------------ series planning
def _tokens(s):
    return {w for w in re.findall(r"[a-z0-9]+", s.lower()) if len(w) > 3}


def near_duplicates(titles: list[str], thr: float = 0.5) -> list[tuple[str, str, float]]:
    out = []
    for i in range(len(titles)):
        for j in range(i + 1, len(titles)):
            a, b = _tokens(titles[i]), _tokens(titles[j])
            if a and b:
                jac = len(a & b) / len(a | b)
                if jac >= thr:
                    out.append((titles[i], titles[j], round(jac, 2)))
    return out


def roadmap(ranked: list[dict], n: int = 30, start: dt.date | None = None, long_per_week: int = 1,
            shorts_per_long: int = 5) -> dict:
    """30-episode roadmap grouped into series + a 90-day production/publishing calendar."""
    eps = [c for c in ranked if c["result"]["score"] is not None][:n]
    series = {}
    for c in eps:
        series.setdefault(c.get("series") or c.get("niche"), []).append(c["title"])
    start = start or dt.date.today()
    cal = []
    day = start
    for k, c in enumerate(eps):
        pub = start + dt.timedelta(days=7 * (k // long_per_week) + 14)  # 2-week production lead
        if (pub - start).days > 90:
            break
        cal.append({"episode": k + 1, "title": c["title"], "research_start": (pub - dt.timedelta(days=14)).isoformat(),
                    "render_by": (pub - dt.timedelta(days=3)).isoformat(), "publish_long": pub.isoformat(),
                    "shorts": [(pub + dt.timedelta(days=d)).isoformat() for d in (-2, 1, 3, 5, 7)][:shorts_per_long]})
    return {"episodes": [{"n": i + 1, "title": c["title"], "niche": c.get("niche"), "series": c.get("series"),
                          "score": c["result"]["score"], "confidence": c["result"]["confidence_label"]}
                         for i, c in enumerate(eps)],
            "series": series, "calendar_90d": cal, "near_duplicates": near_duplicates([c["title"] for c in eps])}


def report_md(ranked: list[dict], evidence: list[dict], weights: dict, top_n: int = 5) -> str:
    ev = {e["id"]: e for e in evidence}
    L = ["# Niche opportunity report", "",
         f"Generated {dt.date.today().isoformat()}. Weights: " + ", ".join(f"{k} {int(v * 100)}%" for k, v in weights.items()),
         "", "> Scores rank ideas for planning. They are **not** performance predictions. Missing evidence lowers "
         "confidence and is never imputed. RPM is not estimated for other channels; only the *category* of revenue "
         "evidence is recorded.", "",
         "| # | Idea | Niche | Score | Confidence | Missing factors | Revenue evidence |", "|---|---|---|---|---|---|---|"]
    for c in ranked:
        r = c["result"]
        rev = ((c.get("factors") or {}).get("revenue_evidence") or {}).get("category", "unknown")
        L.append(f"| {c['rank']} | {c['title']} | {c.get('niche', '')} | {r['score'] if r['score'] is not None else '—'} | "
                 f"{r['confidence_label']} ({r['confidence']}) | {', '.join(r['missing']) or '—'} | {rev} |")
    L += ["", f"## Recommended for production (top {top_n})", ""]
    for c in ranked[:top_n]:
        r = c["result"]
        L += [f"### {c['rank']}. {c['title']}", "",
              f"- **Niche:** {c.get('niche')} · **Series:** {c.get('series', '—')} · **Runtime:** {c.get('runtime', '—')} · "
              f"**Visual style:** {c.get('visual_style', '—')}",
              f"- **Audience fit (US 50+):** {c.get('audience_fit', '—')}",
              f"- **Original angle:** {c.get('angle', '—')}",
              f"- **Competition:** {c.get('competition', '—')}",
              f"- **Historical sources:** {', '.join(c.get('sources', [])) or '—'}",
              f"- **Shorts opportunities:** {', '.join(c.get('shorts', [])) or '—'}",
              f"- **Score breakdown:** " + ", ".join(f"{k} {v['score']}{'' if v['evidenced'] else ' (agent-assessed)'}"
                                                   for k, v in r["breakdown"].items()),
              f"- **Evidence:** " + "; ".join(f"[{e}]({ev[e]['url']})" for f in (c.get('factors') or {}).values()
                                              for e in f.get('evidence', []) if e in ev and ev[e].get('url')), ""]
    if any(c["result"]["problems"] for c in ranked):
        L += ["## Scoring problems", ""] + [f"- {c['title']}: {p}" for c in ranked for p in c["result"]["problems"]]
    return "\n".join(L) + "\n"
