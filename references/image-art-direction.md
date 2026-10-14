# Image art direction (for illustrations that feed `image_whiteboard`, `image`, or thumbnails)

This page is condensed and paraphrased from threerocks/sweety-image-art-direction (MIT). The upstream skill is not embedded, and none of its text is copied. Use these rules when writing prompts for an image generator **that the user has authorised**, or when briefing an illustrator.

## Default look: restrained and professional
- One key light, a believable environment, and at most three main colours (map them to the project palette roles).
- Real materials and textures. No plastic gloss and no random glow.
- Block in the big shapes and values first; detail comes last. Avoid busy, fragmented compositions.

## References
- Give each reference image exactly one job:
  - identity (a character)
  - wardrobe
  - composition
  - style or medium
- Say which job each one has.
- List what must stay unchanged between edits (the preservation list). Change one thing per edit pass.

## Text
- Never let the image model typeset final text. Leave clean space, and add text with the studio's text elements so it stays crisp, translatable and checkable.

## For `image_whiteboard` inputs
- Clean line art: dark lines on white, closed outlines, flat or light fills.
- No photos, gradients or dark backgrounds; they produce noisy ink maps.
- Line weight should be at least 3 px at 1600 px wide.
- Keep the subject inside the central 85 %.

## For historical recreations
- Label recreations as illustrative on screen.
- Avoid photorealistic likenesses of real people unless the provenance and rights of the source photos are documented.
- Prefer stylised drawings.

## QA checklist before using an image
1. Rights recorded in `assets[]` (source, licence, generator terms).
2. No real logos or trademarks unless they are the documented subject.
3. No text baked into the image.
4. Reads at phone size.
5. Palette consistent with the theme.
6. No uncanny hands or faces in prominent positions.
