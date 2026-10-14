"""YouTube metadata package: titles, description with chapters, tags, pinned
comment, thumbnail brief + rendered thumbnail, Shorts metadata.

Chapters follow YouTube's published rules: first timestamp 0:00, at least three
chapters, each at least 10 seconds long.
"""
from __future__ import annotations

import json
from pathlib import Path

from . import timeline
from .spec import load_project


def chapters(p: dict, tl: dict) -> list[tuple[float, str]]:
    titles = {c["id"]: c["title"] for c in p.get("chapters", [])}
    out: list[tuple[float, str]] = []
    for r in tl["scenes"]:
        ch = r.get("chapter")
        if ch and (not out or out[-1][1] != titles.get(ch, ch)):
            out.append((r["start"], titles.get(ch, ch)))
    if out:
        out[0] = (0.0, out[0][1])
    # merge chapters shorter than 10 s into the previous one
    merged: list[tuple[float, str]] = []
    for i, (t, name) in enumerate(out):
        nxt = out[i + 1][0] if i + 1 < len(out) else tl["total"]
        if merged and nxt - t < 10:
            continue
        merged.append((t, name))
    return merged


def check_chapters(ch: list[tuple[float, str]], total: float) -> list[str]:
    issues = []
    if len(ch) < 3:
        issues.append("YouTube needs >= 3 chapters")
    if ch and ch[0][0] != 0:
        issues.append("first chapter must start at 0:00")
    for i, (t, _) in enumerate(ch):
        nxt = ch[i + 1][0] if i + 1 < len(ch) else total
        if nxt - t < 10:
            issues.append(f"chapter at {timeline.fmt_ts(t)} shorter than 10 s")
    return issues


def write_seo(pdir: Path, quality: str = "preview") -> list[Path]:
    p = load_project(pdir)
    tl = json.loads((pdir / "storyboard" / "timeline.json").read_text(encoding="utf-8"))
    seo = p.get("seo", {})
    ch = chapters(p, tl)
    ch_issues = check_chapters(ch, tl["total"])
    titles = seo.get("title_options") or [p["title"]]
    desc_lines = [seo.get("description", "").strip(), ""]
    if p.get("fictional"):
        desc_lines += [f"Note: {p['disclaimer']}", ""]
    if seo.get("sources_note"):
        desc_lines += [seo["sources_note"], ""]
    desc_lines += ["Chapters:"] + [f"{timeline.fmt_ts(t)} {name}" for t, name in ch] + [""]
    if seo.get("hashtags"):
        desc_lines.append(" ".join(seo["hashtags"][:3]))  # YouTube shows the first three above the title
    description = "\n".join(desc_lines).strip() + "\n"
    tags = seo.get("tags", [])
    tag_chars = sum(len(t) + 1 for t in tags)
    md = [f"# YouTube metadata — {p['title']}", "",
          "## Title options (pick one; <= 70 chars recommended)", ""]
    md += [f"{i}. {t} ({len(t)} chars)" for i, t in enumerate(titles, 1)]
    md += ["", "## Description", "", "```", description, "```", "",
           f"## Tags ({tag_chars}/500 chars)", "", ", ".join(tags), "",
           "## Chapters", ""] + [f"- {timeline.fmt_ts(t)} {n}" for t, n in ch]
    md += ["", "Chapter check: " + ("OK" if not ch_issues else "; ".join(ch_issues)), "",
           "## Pinned comment", "", seo.get("pinned_comment", ""), "",
           "## Thumbnail brief", "", seo.get("thumbnail_brief", ""), "",
           "## Upload settings", "",
           f"- Language: {p.get('language')}; audience: {p.get('audience')}; captions file: subtitles/captions.srt",
           "- Category: Education (27) or as appropriate; altered/synthetic content disclosure: "
           + ("**Yes** — realistic-looking synthetic scenes present" if seo.get("synthetic_disclosure") else
              "not required for clearly stylised animation (review YouTube's current policy before upload)"),
           "- Made for kids: No (unless reviewed otherwise)", ""]
    out = [pdir / "seo" / "youtube-metadata.md"]
    out[0].write_text("\n".join(md), encoding="utf-8")
    (pdir / "seo" / "youtube-metadata.json").write_text(json.dumps(
        {"titles": titles, "description": description, "tags": tags, "chapters": [[t, n] for t, n in ch],
         "chapter_issues": ch_issues, "pinned_comment": seo.get("pinned_comment", "")}, indent=2), encoding="utf-8")
    out.append(pdir / "seo" / "youtube-metadata.json")
    # Shorts metadata
    smap_f = pdir / "shorts" / "shorts-map.json"
    smap = json.loads(smap_f.read_text(encoding="utf-8")) if smap_f.exists() else {"shorts": []}
    sm = [f"# Shorts metadata — parent: {p['title']}", "",
          "Publishing: upload each Short, then in YouTube Studio open the Short → Details → **Related video** and "
          "select the parent video. That link is the supported way to send Shorts viewers to the long video; "
          "description links alone are not clickable in the Shorts player.", ""]
    for sh in p.get("shorts", []):
        mp = next((x for x in smap["shorts"] if x["short_id"] == sh["id"]), {})
        sm += [f"## {sh['id']} — {sh.get('title', '')}", "",
               f"- File: `{Path(mp['file']).name if mp.get('file') else 'not rendered'}` · duration "
               f"{mp.get('duration', 0) or 0:.1f}s",
               f"- Parent chapter: {mp.get('parent_chapter', {}).get('title')} · source "
               + ", ".join(f"{x['start']}–{x['end']}" for x in mp.get("source_timestamps", [])),
               f"- Title: {sh.get('title', '')}",
               f"- Description: {sh.get('description', '')}",
               f"- Hashtags: {' '.join(sh.get('hashtags', []))}",
               f"- Pinned comment: {sh.get('pinned_comment', '')}",
               f"- Related video: {p['title']} (set in YouTube Studio)",
               f"- Suggested publish order: {sh.get('publish_order', '—')}", ""]
    out.append(pdir / "seo" / "shorts-metadata.md")
    out[-1].write_text("\n".join(sm), encoding="utf-8")
    out.append(publishing_checklist(p, pdir))
    thumb = render_thumbnail(p, pdir)
    if thumb:
        out.append(thumb)
    return out


def render_thumbnail(p: dict, pdir: Path) -> Path | None:
    spec = p.get("thumbnail")
    if not spec:
        return None
    from .design import Theme
    from .engines import ENGINES, SceneContext

    sc = {"id": "thumbnail", "elements": spec.get("elements", []), "params": spec.get("params", {}),
          "camera": {"move": "static"}, "_project_dir": str(pdir)}
    ctx = SceneContext(scene=sc, width=1280, height=720, ss=2, fps=30, duration=10, theme=Theme(p.get("theme", "documentary")))
    img = ENGINES[spec.get("engine", "motion")](ctx).frame(9.9)
    out = pdir / "thumbnails" / "thumbnail.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out)
    return out


def publishing_checklist(p: dict, pdir: Path) -> Path:
    """Manual pre-publish checklist (nothing here is automated: the studio never uploads)."""
    dubs = sorted(x.stem.replace("dub-", "") for x in (pdir / "reports").glob("dub-*.json"))
    L = [f"# Publishing checklist — {p['title']}", "",
         "Tick each item in YouTube Studio. The studio prepares files; it never uploads or publishes.", "",
         "## Before upload",
         "- [ ] `reports/quality-report.json` status is `pass` (visual review approved)",
         "- [ ] `reports/fact-check-report.md` reviewed; contested claims are framed on screen and in narration",
         "- [ ] Originality: script, visuals and voice choices are specific to this episode (YouTube's *inauthentic content* "
         "policy, renamed from 'repetitious content' on 2025-07-15, demonetizes mass-produced/templated content)",
         "- [ ] Advertiser-friendly: no graphic injury/death; nothing graphic in the thumbnail or first 7 seconds",
         "- [ ] Altered/synthetic content disclosure decided (Studio → Attributes → AI use) — required for realistic "
         "synthetic depictions of real people/events; stylised animation labelled 'illustrative' usually is not",
         "", "## Upload (master video, once)",
         "- [ ] Upload `renders/long-video.mp4` · title/description/tags from `seo/youtube-metadata.md`",
         "- [ ] Chapters present in description (first at 0:00, ≥ 3, each ≥ 10 s)",
         "- [ ] Captions: upload `subtitles/captions.srt` (Subtitles → Upload file → With timing)",
         "- [ ] Thumbnail `thumbnails/thumbnail.png`; pinned comment from metadata",
         "- [ ] Language of video = English (United States)", ""]
    if dubs:
        L += ["## Additional languages (same video URL)"] + [
            f"- [ ] `{d}`: audio track `renders/audio-{d}.m4a` (Languages → Add language → Dub), captions "
            f"`subtitles/captions-{d}.srt`, localized title/description (`seo/localizations.json`); "
            f"check `reports/dub-{d}.json` status and native review" for d in dubs] + [
            "- [ ] Feature access: multi-language audio requires Advanced features and may be limited to some creators", ""]
    L += ["## Shorts", "- [ ] Upload each Short in `shorts/`; set **Related video** → this video (Content → Short → Related video)",
          "- [ ] Follow the publish order in `seo/shorts-metadata.md`", "",
          "## After publishing",
          "- [ ] Add `youtube_id` to project.json and re-run `studio.py shorts` (deep links in shorts-map.json)",
          "- [ ] After 7 and 28 days: export Studio CSVs to `analytics/exports/` and run `studio.py analytics`", ""]
    f = pdir / "reports" / "publishing-checklist.md"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(chr(10).join(L), encoding="utf-8")
    return f
