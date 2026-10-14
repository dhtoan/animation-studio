# youtube-niche-intelligence

Goal: rank documentary ideas for a channel serving U.S. viewers aged 50+. Every signal is cited, and nothing is invented.

## Evidence ledger (`research/niche/evidence.json`)
```json
{"evidence": [{"id": "e12", "pillar": "1", "type": "competitor|video|demand|audience|advertiser|rpm",
               "claim": "…", "value": "…", "url": "…", "published": "…", "accessed": "2026-10-14",
               "window": "7d|30d|90d|12m|evergreen", "category": "verified|public-creator-reported|industry-estimate|ad-demand-proxy|unknown"}]}
```

Ways to collect evidence:
1. **No key.** The agent reads public pages: YouTube search and channel pages, Pew, official YouTube help, museum and archive sites. It records what is displayed, with the date seen.
2. **Data API** (`YT_API_KEY`, opt-in). `studio.py niche collect "<query>"` runs about 240 quota units per query against the default 8,000/day budget:
   - `regionCode=US`, `relevanceLanguage=en`
   - a 12-month view-count search and a 90-day relevance search
   - median-baseline outliers (views ÷ median of the channel's last 15 uploads, excluding videos under 7 days old)
3. **CSV import** of exports you have the right to use.

Recent signals (7d/30d/90d) are kept separate from evergreen ones (12m and multi-year).

## Candidates and scoring (`research/niche/candidates.json`, `studio_lib/niche.py`)
Default weights can be overridden per project (`niche_weights`):

| factor | weight | what counts as evidence |
|---|---|---|
| audience_fit_us50 | 25 % | Pew/YouTube data on 50+ viewing; topic-era relevance (1940–1990); comment demographics are not measurable, so do not claim them |
| revenue_evidence | 20 % | the **category** of evidence only (capped: verified 10, ad-demand-proxy 5, creator-reported 6, industry-estimate 4, unknown 0) |
| demand | 15 % | views/day of top results, long-lived high-view videos, recurring anniversaries |
| competition_gap | 15 % | outliers from small channels, low top-3 concentration, few recent long-form entries |
| evergreen | 10 % | multi-year view accumulation, anniversary cycles |
| storytelling | 10 % | a documented arc with conflict, decision and consequence; quality of primary sources |
| feasibility | 5 % | public-domain sources and visuals; no graphic material needed |

Scoring rules:
- Each factor is scored 0–10 and must cite evidence ids, or be marked `"assessed_by": "agent"` with a rationale.
- Missing factors are **excluded**, not imputed, and lower the confidence (high ≥ 0.75, medium ≥ 0.5).
- The score ranks ideas for planning. **It is not a forecast** of views or revenue.

## RPM rules
- RPM = creator earnings per 1,000 views (after revenue share). CPM = advertiser price per 1,000 ad impressions. They are different.
- Never infer a competitor's RPM from views. A niche gets no RPM number unless the channel's own Analytics measured it (`verified`).
- `niche.revenue_scenarios()` only does arithmetic on **user-labelled assumptions** and stamps every row "ASSUMPTION — not a forecast".

## Outputs
- `research/niche/opportunities.json` and `research/niche/niche-report.md`: a ranked shortlist of 20 ideas with the top 5 recommended. Each idea lists audience fit, evidence links, competitors, demand signals, revenue-evidence category, competition, angle, sources, runtime, visual style and Shorts ideas.
- `research/niche/roadmap.json`: a 30-episode roadmap grouped into series, a 90-day calendar (2-week production lead, 1 long video per week, 5 Shorts around each), and a near-duplicate check.

## Content safety
- Military and war topics must be educational and contextualised. No glorification of atrocities and no sensationalised victims.
- Keep graphic material out of the thumbnail and the first 7 seconds (see `youtube-api-notes.md`).
