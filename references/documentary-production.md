# Documentary production (V3)

This page covers the 50+ audience profile, historical research, story architecture, art direction, the Shorts funnel, series planning and analytics.

## audience-50plus-intelligence (`studio_lib/audience.py`)
The profile is a *testable* set of defaults, not an assumption about every older viewer:
- Narration at 125–150 wpm.
- No text smaller than body size.
- WCAG AA contrast (≥ 4.5:1).
- Captions at ≤ 17 characters per second.
- Scenes of at least 6 s.
- A calm transition budget.
- Music ducked well under narration, loudness at −14 LUFS.
- Dates and names on screen.

`studio.py audience <slug>` audits a project and lists A/B variants for pacing, density and style mix. Validate any preference with real retention data for the 55–64 and 65+ groups; never assume it.

## historical-documentary-research (`studio_lib/history.py`)
- **Source tiers:**
  - Tier 1: National Archives, Library of Congress, Smithsonian, National WWII Museum, Army Center of Military History, govinfo/congress, presidential libraries, NPS.
  - Tier 2: universities and academic publishers.
  - Tier 3: established newspapers and wire services.
  - Tier 4: everything else.
- **Claim classes and how the ledger treats them:**

  | class | ledger status | requirement |
  |---|---|---|
  | established | `verified` | a dated URL |
  | contested | `contested` | must be framed, e.g. "estimates range from … according to …" |
  | allegation | `allegation` | attributed, never stated as fact |
  | reconstruction | `illustrative` | labelled on screen as a recreation |
  | fictional | `fictional` | — |

- `studio.py history import <slug> --dossier dossier.json` builds `research/facts.json`. `studio.py history report <slug>` writes `reports/fact-check-report.md` *before rendering*.
- **Media rights:** U.S. federal government works are generally public domain. Museum and agency photos can carry restrictions. Record every item in `assets[]`. Never fabricate archival documents, quotes or dates.

## documentary-story-architect (`studio_lib/story.py`)
Structure and share of runtime:

| section | share | purpose |
|---|---|---|
| opening | 6 % | hook |
| setup | 14 % | context |
| development | 38 % | chronological discoveries |
| complications | 20 % | decisions, consequences, conflicting evidence |
| resolution | 12 % | what happened, and **what remains uncertain** |
| significance | 7 % | why it matters |
| next episode | 3 % | bridge to another documentary |

- Formats: 12–15, 15–20 (default about 18–20), 20–30 and 30–45 minutes.
- `studio.py story plan --minutes 20` prints word, scene and second budgets per section.
- `studio.py story check <slug>` verifies the hook, the stated uncertainty and the bridge.

## documentary-art-director
- The router and registry pick verified engines per scene. Documentary defaults:
  - timelines and maps → `motion` / `whiteboard`
  - people and decisions → `handdrawn`
  - recreations → `archival` (sepia paper, typewriter type, "ILLUSTRATIVE RECREATION" label)
  - data → `huashu.finance-chart` / `motion`
- Keep transitions calm. Synthetic recreations are always labelled.

## documentary-shorts-funnel
Five Shorts per documentary by default, 25–50 s each:
1. surprising fact
2. unanswered question
3. unexpected decision
4. overlooked person
5. dramatic consequence

Each Short has a `funnel_type` and a `publish_order`, and goes into `shorts-map.json`. The default sequence is: 2 days before the long video, then +1, +3, +5 and +7 days after it. Link each Short with the Studio "Related video" field. A description link alone is not a clickable funnel in the Shorts player.

## Series strategy
`niche.roadmap()` produces:
- a 30-episode list grouped into series (Forgotten Battles of WWII, Cold War Files, America's Lost Industrial Giants, and others)
- a 90-day calendar
- a near-duplicate check (Jaccard on title tokens)

After publishing, re-rank related episodes using measured returning-viewer and retention data, not guesses.

## documentary-performance-analytics (`studio_lib/analytics.py`)
- **Data sources:** the Analytics API v2 (read-only, `YT_ANALYTICS_TOKEN`), or YouTube Studio CSV exports in `analytics/exports/`.
- **Goal tracking:** the target is *90 % of views from U.S. viewers aged 55+*. It is a target, not a guarantee, and is measured as US view share × 55+ share among US viewers.
- **Limits it respects:**
  - The 45–54 bucket is reported separately.
  - Privacy-withheld data counts as missing, not zero.
  - Impressions/CTR and returning viewers are marked unavailable via the API.
  - RPM is shown only when revenue metrics exist.
