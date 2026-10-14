# YouTube SEO package (`studio.py seo`)

## Outputs
Written to `seo/`:
- `youtube-metadata.md` / `.json`:
  - title options with character counts
  - description
  - tags, checked against the 500-character budget
  - chapters
  - pinned comment
  - thumbnail brief
  - upload-settings checklist
- `shorts-metadata.md`, for each Short:
  - title, description, hashtags
  - pinned comment
  - parent chapter and timestamps
  - related-video instructions
  - publish order

Also: `thumbnails/thumbnail.png` (1280×720), rendered from `project.thumbnail`.

## Rules
- **Titles**
  - Be specific; the curiosity must be grounded in the actual content.
  - ≤ 70 characters is recommended.
  - Put the concrete noun or number first.
- **Description**
  - The first two lines summarise the video's value.
  - Then: disclaimers (fictional/illustrative), a sources note, chapters, and up to 3 hashtags (YouTube shows the first three).
- **Chapters**
  - Generated from the scene chapters.
  - Validated against YouTube's rules: the first starts at 0:00, there are at least 3 chapters, and each lasts ≥ 10 s.
- **Tags**: secondary. Use them for misspellings and synonyms.
- **Synthetic-content disclosure**
  - Realistic-looking altered or synthetic media must be disclosed in YouTube Studio.
  - Clearly stylised animation usually does not require it, but check the current policy before uploading (`seo.synthetic_disclosure`).
- **Thumbnail**
  - At most 3 words, high contrast, readable at phone size.
  - No fake news branding and no misleading imagery.
