"""documentary-performance-analytics: the learning loop.

Sources (in order of preference):
  1. YouTube Analytics API v2 for the authenticated channel (youtube_api.AnalyticsAPI;
     needs YT_ANALYTICS_TOKEN). Read-only.
  2. CSV exports from YouTube Studio (Advanced mode → Export → CSV), dropped in
     analytics/exports/. Works with no credentials at all.

Facts this module respects (official docs checked 2026-10-14, see
references/youtube-api-notes.md):
  * ageGroup buckets are age13-17 … age45-54, age55-64, age65- — there is no
    "50+" bucket. The goal is tracked as US 55+ (55-64 + 65-), and 45-54 is
    reported separately because it straddles 50.
  * Demographic data is withheld below unpublished privacy thresholds → missing,
    not zero.
  * Impressions/CTR and returning/unique viewers are NOT available in the
    Analytics API (CTR only via the bulk Reporting API) → "unavailable" here
    unless present in a Studio CSV export.
  * RPM = estimatedRevenue / views × 1000, only with the monetary scope + YPP.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

GOAL = {"metric": "share of views from US viewers aged 55+", "target": 0.90,
        "note": "Target, not a guarantee. Proxy = US view share × 55+ share among US viewers."}
AGE_55P = ("age55-64", "age65-")


def _num(x):
    try:
        return float(str(x).replace(",", "").replace("%", ""))
    except (TypeError, ValueError):
        return None


def read_csv(path: Path) -> list[dict]:
    with open(path, encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def demographics_from_rows(rows: list[dict]) -> dict:
    """rows: [{ageGroup, gender, viewerPercentage}] (API or CSV with those headers)."""
    by_age = {}
    for r in rows:
        age = r.get("ageGroup") or r.get("Viewer age")
        pct = _num(r.get("viewerPercentage") or r.get("Views (%)"))
        if age and pct is not None:
            by_age[age] = by_age.get(age, 0.0) + pct
    total = sum(by_age.values())
    if not total:
        return {"available": False, "reason": "no demographic rows (privacy threshold or no data)"}
    share55 = sum(by_age.get(a, 0) for a in AGE_55P) / total
    return {"available": True, "by_age_pct": {k: round(v / total * 100, 2) for k, v in sorted(by_age.items())},
            "share_55_plus": round(share55, 4), "share_45_54_note": round(by_age.get("age45-54", 0) / total, 4)}


def progress(us_view_share: float | None, demo_us: dict) -> dict:
    if us_view_share is None or not demo_us.get("available"):
        return {"status": "insufficient data", "goal": GOAL}
    est = us_view_share * demo_us["share_55_plus"]
    return {"status": "measured", "us_view_share": us_view_share, "us_55plus_share_of_us": demo_us["share_55_plus"],
            "estimated_us55plus_share_of_all_views": round(est, 4), "goal": GOAL,
            "gap_to_target": round(GOAL["target"] - est, 4)}


def recommendations(metrics: dict) -> list[str]:
    rec = []
    p = metrics.get("progress", {})
    if p.get("status") == "measured":
        if p["us_view_share"] < 0.6:
            rec.append("US share is below 60%: check traffic sources by country; favour US-specific topics and "
                       "US-centric references in titles/thumbnails.")
        if p["us_55plus_share_of_us"] < 0.5:
            rec.append("Under half of US viewers are 55+: compare retention of the 'pace' A/B variants "
                       "(audience.AB_VARIANTS) for 55–64 and 65+ before changing topics.")
    ret = metrics.get("retention", {})
    if ret.get("avg_view_percentage") is not None and ret["avg_view_percentage"] < 35:
        rec.append("Average percentage viewed < 35%: inspect the first 60 s of the retention curve; tighten the "
                   "cold open and deliver the viewer promise earlier.")
    if metrics.get("revenue", {}).get("available") is False:
        rec.append("Revenue metrics unavailable (needs YPP + monetary scope). Do not estimate RPM from views.")
    return rec or ["Not enough measured data for recommendations yet."]


def summarize_exports(export_dir: Path) -> dict:
    """Reads Studio CSV exports named by convention: demographics_us.csv, geography.csv, overview.csv."""
    out = {"source": "studio_csv", "files": sorted(p.name for p in export_dir.glob("*.csv"))}
    geo = export_dir / "geography.csv"
    us_share = None
    if geo.exists():
        rows = read_csv(geo)
        views = {(r.get("country") or r.get("Geography")): _num(r.get("views") or r.get("Views")) for r in rows}
        tot = sum(v for v in views.values() if v)
        if tot:
            us_share = round((views.get("US") or views.get("United States") or 0) / tot, 4)
    dem = export_dir / "demographics_us.csv"
    demo = demographics_from_rows(read_csv(dem)) if dem.exists() else {"available": False, "reason": "no export"}
    out["demographics_us"] = demo
    out["progress"] = progress(us_share, demo)
    ov = export_dir / "overview.csv"
    if ov.exists():
        rows = read_csv(ov)
        views = sum(_num(r.get("views") or r.get("Views")) or 0 for r in rows)
        rev = [x for x in (_num(r.get("estimatedRevenue") or r.get("Estimated revenue (USD)")) for r in rows) if x is not None]
        avp = [x for x in (_num(r.get("averageViewPercentage") or r.get("Average percentage viewed (%)")) for r in rows) if x is not None]
        out["retention"] = {"avg_view_percentage": round(sum(avp) / len(avp), 2) if avp else None}
        out["revenue"] = ({"available": True, "estimated_revenue": round(sum(rev), 2),
                           "rpm": round(sum(rev) / views * 1000, 2) if views else None} if rev else {"available": False})
    out["unavailable_metrics"] = ["impressions / CTR (not in Analytics API; only bulk Reporting API or Studio export)",
                                  "returning / unique viewers (Studio UI only)"]
    out["recommendations"] = recommendations(out)
    return out
