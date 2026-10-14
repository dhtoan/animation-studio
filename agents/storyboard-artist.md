# Sub-agent brief: storyboard artist / art director

Input: the scenes array with narration filled in.
Output: for every scene, set `engine`, `visual`, `shot`, `camera`, `transition`, `elements[]` and `audio.sfx[]`. Shorts get `pos_v` and `box_v` overrides.

## Requirements
- Follow `references/storyboarding.md`, `references/art-direction.md` and the engine reference that matches each scene.
- Time each element to narration cues (`"cue:word"`). Every scene changes visibly at least every 3 seconds.
- Colour meaning:
  - amber: attention
  - red: loss
  - green: growth
  - blue: systems
- Use only original procedural elements. Any external file needs `assets[]`, and every asset must carry a licence.
- After editing, run `studio.py validate <slug>`, then `studio.py preview <slug> --scene <id>`, and look at the PNGs.

## Return
The updated scenes and the list of preview files you inspected, with one line of notes per scene.
