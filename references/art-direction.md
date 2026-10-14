# Art direction

## One design system across engines
- **Theme** (`project.theme`): `documentary`, `tech` or `history`.
  - All themes share the same colour roles: ink, paper, board, night, night2, accent, positive, negative, cool, muted, light.
  - Use `theme_overrides` to change any role.
- **Colour meaning is fixed per project.**
  - accent (amber) = attention
  - negative (red) = loss or failure
  - positive (green) = growth or cash in
  - cool (blue) = systems or neutral entities
- **Type roles** (defined in `studio_lib/design.py`):
  - `sans` / `sans_bold` for data
  - `display` for kinetic type
  - `hand` / `hand_bold` for whiteboard and hand-drawn scenes
  - `serif` for artistic scenes
  - Sizes scale with the frame's short side: hero 10.5 %, h1 7.5 %, h2 5.4 %, h3 4.2 %, body 3.4 %, label 2.7 %.
  - To override system fonts, drop OFL fonts (e.g. Inter, Caveat, Oswald) into `assets/fonts/`.
- **Characters**: describe each recurring character once in `art_direction.characters` and reference it from `scene.characters`. Use the same `color` role every time.

## Choosing engines (router defaults)

| purpose | first choice | then |
|---|---|---|
| hook / title / quote / cta | kinetic | artistic, motion |
| explain / process / tutorial | whiteboard | handdrawn, motion |
| data / comparison / evidence | motion | huashu_clip, whiteboard |
| story / character / recreation | handdrawn | artistic, whiteboard |
| metaphor / atmosphere / reveal | artistic | handdrawn, kinetic |
| illustration (has `params.src`) | image_whiteboard | whiteboard |

- **Category bias**: business leans to motion, history to handdrawn, science and DIY to whiteboard.
- **Variety rule**:
  - Avoid more than three consecutive scenes on the same engine.
  - Alternate dark engines (motion, kinetic, artistic) with light ones (whiteboard, hand-drawn) at chapter boundaries, not on every scene.

## Artistic scenes
Configure through `params`:
- `sky`: `[top, bottom]` colours
- `sun`: `{pos, size, sink}`
- `mood_shift`
- `layers`, listed back to front: mountains, hills, city, towers, skyline_tall
- `fog`, `grain`, `flicker`, `lights_out_at`

Use artistic scenes for chapter openers and emotional turns, not for information.

## Transitions
- Default to `cut`.
- Use `crossfade` or `fade_black` for time jumps and mood changes.
- Use `whip` or `push` for energy.
- Use `erase` between whiteboard scenes.
- One "special" transition per chapter is enough.
