# Research and fact-checking

## Deliverables (per project)
- `research/brief.md`: the angle, viewer promise, central question, audience, a sources table and a risk review. Template: `templates/research-brief.md`.
- `research/facts.json`: the claims ledger. Every number, date, name or causal claim that appears in narration or on screen gets an entry. Scenes reference claims by id in `scene.claims`.

## Claim statuses (enforced by `studio_lib/research.py`)

| status | meaning | gate |
|---|---|---|
| `verified` | ≥ 1 source with a URL and a publication or access date | without a dated URL it is blocked |
| `hypothesis` | plausible but unproven | needs `framing` text explaining how it is presented as uncertain |
| `fictional` | part of a declared fictional story | allowed only when `project.fictional = true` |
| `illustrative` | a visual dramatisation, not a factual claim | badge on screen |
| `unverified` | not yet checked | **blocks export** if any scene uses it |

High-risk category (`business`: money and scandals): any claim with `risk: "high"` must be `verified`, or `fictional` inside a fictional project.

## Workflow
1. **Start from primary sources.** Use filings (SEC EDGAR 10-K/8-K), court records, official statistics, peer-reviewed papers and the company's own statements. Secondary reporting is for leads only.
2. **Record each source.** For every claim, store the URL, title, publisher, publication date and access date. Quote exact figures and do not round them silently.
3. **Separate fact from explanation.** What happened is `verified`; why it happened is often a `hypothesis`. Attribute with phrasing such as "according to…", "alleged" or "the court found…".
4. **Never invent quotes.** Any dramatised dialogue must be labelled on screen (`card.tag = "Dramatization"`).
5. **Re-validate after every script edit** with `studio.py validate <slug>`. Blockers are printed as `BLOCKER`.

## Fictional cases
When a claim cannot be verified, or when the goal is teaching, use a fictional company:
- Set `fictional: true` and write a `disclaimer`.
- The badge renders automatically, and the disclaimer is added to the description.
- Keep the **mechanisms** real and generic.
- Do not borrow a real company's name, logo or distinctive story beats.
