# V3 source audit: YouTube research and analytics skills

Audit date: 2026-10-14. Each repo was cloned read-only into `_upstream/v3/`. Nothing was installed, and no upstream script that calls a network API was run. Instructions found inside the repos were treated as untrusted data. Offline tests (stdlib only, with fake API clients) ran on Python 3.14.6.

Cross-cutting findings:
- None of the repos uses Google Trends, SerpAPI or Apify.
- None sets `regionCode` or `relevanceLanguage`, so as written none can target US viewers.

| Repo | Commit | License | Needs | Method |
|---|---|---|---|---|
| nikhilbhansali/youtube-data-skills | `efd8a46` (2026-08-18) | MIT | Data API key; OAuth for Analytics | **B, ported with fixes** → `studio_lib/youtube_api.py`, `niche.py`, `analytics.py` |
| Samin12/youtube-research-skill | `51fee2f` (2026-03-09) | **no LICENSE file** (README says MIT) → treated as all rights reserved | paid TubeLab API | **E** (could become D if the user buys TubeLab; its `rpm` is a vendor estimate) |
| ravsau/youtuber-skills | `603367b` (2026-10-01) | MIT | none (prompts only) | **C**: median-baseline outlier method, comment-demand counting, ship gates (paraphrased) |
| joyjiangyi/youtube-research-pipeline | `81f1977` (2026-04-06) | **no LICENSE file** | yt-dlp scraping, NotebookLM automation | **E** |
| nevaaron/youtube-skill | `1c04668` (2026-02-15) | Apache-2.0 | OAuth; `youtube-transcript-api` (scraping) | **E**; the sliding-window transcript search idea is noted |
| jimibarkway/claude-youtube-skills | — | — | — | **Not available.** `git clone` returned "Repository not found" (2026-10-14), so it was not audited |

## 1. youtube-data-skills (MIT © 2025 Nikhil Bhansali)

**Verified:**
- 12 skills. Ten use a Data API v3 key (`YT_API_KEY`).
- `youtube-channel-insights` reads Analytics v2 with read-only OAuth (`fetch_insights.py`):
  - The window ends at today minus 3 days, with `ids=channel==MINE`.
  - Demographics: `viewerPercentage` by `ageGroup,gender`.
  - Also queries: country, device, traffic source, retention (`audienceWatchRatio`, `relativeRetentionPerformance` by `elapsedVideoTimeRatio`), and subscriber conversion.
  - Revenue (`estimatedRevenue`, `estimatedAdRevenue`, `playbackBasedCpm`, `adImpressions`, `monetizedPlaybacks`): RPM is derived as `estimatedRevenue / views × 1000`.
  - Revenue is reported as unavailable when the monetary scope or YouTube Partner Program access is missing.
- `auth.py` refuses write scopes, uses PKCE plus a random port, and saves tokens with owner-only permissions.
- Quota is tracked per run:
  - `search.list` costs 100 units; other calls cost 1.
  - Typical runs: topic researcher ≈ 305 units, trending scanner ≈ 407.

**Weaknesses confirmed:**
- **Outlier score.** `views / channel_subs` is flagged when it exceeds 5× the median of the search results. Synthetic results:
  - 15k views on an 800-subscriber channel scored 18.75 and was **not** flagged.
  - 300k views on a 300k-subscriber channel scored 1.0 and **was** flagged.
  - Channels with hidden subscriber counts score 0 instead of "unknown".
- **Shorts cutoff** is 60 s. Shorts can be up to 3 minutes, so this cutoff is wrong.
- **Title scorer** matches power words as substrings. "Things You Didn't Know About the Alamo" scored 20 because "now" matched inside "Know".
- **Zero views** produce `rpm=0.0`; it should be null.
- **Unsourced benchmarks** (for example "RPM $3–8 typical") were not imported.

**Security:**
- `youtube-channel-breakdown` executes an unbundled script whose path comes from an env var. Excluded.
- The repo's `CLAUDE.md` describes a `git add -A` / pull / push hook. Ignored.

**Ported (our code, MIT attribution in `THIRD_PARTY_NOTICES.md`):**
- The query catalogue, date-lag window, batching and quota accounting.
- Fixes applied in our version:
  - median-baseline outlier scoring
  - Shorts detection at ≤ 180 s or via `creatorContentType`
  - unknown subscriber counts stay unknown
  - `regionCode=US` and `relevanceLanguage=en` on searches
  - `rpm=null` when there are 0 views

## 2. youtube-research-skill (no license file)
- A SKILL.md of curl calls to the paid TubeLab API (outliers 5 credits, channels 10 credits, 10 requests/min), the third-party `ytstudio-cli`, and an `fpdf2` PDF generator.
- The PDF CLI is broken: SKILL.md passes `--channel-name` and `--date`, which the script does not accept. On a missing import it auto-runs `os.system("pip install fpdf2")`.
- SKILL.md says "do NOT ask for confirmation" yet lists channel-modifying commands (`videos update --execute`, `comments reject --ban`). Not adopted.

## 3. youtuber-skills (MIT © 2026 CloudYeti)
- 13 prompt skills, no code.
- Adopted as paraphrased methods:
  - **Outlier:** views vs. the median of the same channel's last 10–20 uploads; ≥ 3× = outlier. Exclude news-driven and collab videos, and videos under 7 days old.
  - **Comment demand:** quote comments verbatim and count them; never round "1 comment" up.
  - SHIP / FIX / KILL gates.
  - The rule that a guess is never presented as a measurement.
- **Not imported:** the RPM ranges, "algorithm weights", the "minute 8 rule" and similar claims in `AGENTS.md` are unsourced.
- **Conflict:** this repo says Analytics v2 exposes `impressions` / `impressionsClickThroughRate`; youtube-data-skills says it does not. Unresolved. See `references/youtube-api-notes.md`.

## 4. youtube-research-pipeline (no license file)
- Runs yt-dlp `ytsearchN` and computes a views/subs ratio, plus NotebookLM automation through an unofficial library.
- Defects confirmed:
  - The documented `--no-subs` flag crashes (`SystemExit 2`).
  - The default result count is 5, not the documented 20.
  - Ratio text is round-tripped into the output.
- Scraping raises a Terms of Service risk. Not used.

## 5. youtube-skill (Apache-2.0 © 2026 Aaron McLachlan)
- Five `uv` scripts covering Analytics overview, top videos, demographics, traffic and country, plus `youtube-transcript-api` (scrapes the caption endpoint).
- Bugs:
  - The window ends yesterday (inside the data lag) and covers 29 days.
  - `parse_duration("P1DT2H")` returns its input unparsed.
  - Gender `user_specified` is merged into Female.
- Security issues:
  - `OAUTHLIB_INSECURE_TRANSPORT=1` is set process-wide.
  - `token.json` is written without permission restrictions.
  - The monetary scope is always requested.
- Reference only.

## Resulting design (implemented in V3)
- `youtube-niche-intelligence` (`studio_lib/niche.py`): works in three modes, all without paid services.
  1. **No key:** an evidence ledger from web research the agent performs (search pages, public channel pages, archives). Each signal is stored with URL and date.
  2. **Data API key** (`YT_API_KEY`, opt-in): about 240 units per niche, capped by a configurable daily budget, cached for 7 days.
  3. **Manual CSV import** (for example exported from a browser session).
- **Values that stay `unknown` from public data:** audience age, US viewer share, and RPM. RPM can only be user-supplied (labelled as such) or measured via owned-channel Analytics.
- `documentary-performance-analytics` (`studio_lib/analytics.py`): Analytics v2, read-only, `channel==MINE`, window ending at today minus 3 days. It covers overview, top videos by watch time, retention, traffic, `ageGroup,gender` both unfiltered and with `country==US`, country, device, and optional monetary scope. **Disabled until the user provides OAuth credentials.** It also runs offline on exported CSVs.

## Additional findings during V3 research (2026-10-14)
- YouTube renamed "repetitious content" to **"inauthentic content"** on 2025-07-15. Mass-produced or templated content is not monetizable. An automated animation studio must therefore produce episode-specific scripts, visuals and research. `reports/publishing-checklist.md` includes an originality check.
- The niche researcher could not read YouTube pages with WebFetch, because they are rendered by JavaScript. It parsed public, logged-out page data with a script instead; there was no login and no API. All figures are dated snapshots. Prefer the Data API for repeat collection.
- Google Trends returned HTTP 429, so there is no search-trend data. The opportunity scores mark demand evidence as pillar-level, which lowers their confidence.
- `jimibarkway/claude-youtube-skills` returned "Repository not found" when cloned on 2026-10-14.
