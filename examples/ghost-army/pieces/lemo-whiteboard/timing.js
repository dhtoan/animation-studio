// Scene timing for this piece. The studio adapter (html_seek params.timing) injects
// window.STUDIO_TIMING = {fps, scenes: [{id, start, end, words?: [[t_local, word], ...]}]} before any
// page script runs; without it the production defaults below apply. Each scene is an era of the film:
// the pipeline renders scene X with {page, offset: start_X} for end_X - start_X seconds.
export const DEFAULT = { fps: 30, scenes: [{ id: 'g08', start: 0, end: 15 }, { id: 'g12', start: 15, end: 37 }] };

export function timing() {
  const T = (typeof window !== 'undefined' && window.STUDIO_TIMING) || DEFAULT;
  const scenes = (T.scenes || []).map(s => ({ ...s, start: +s.start, end: +s.end })).filter(s => s.end > s.start)
    .sort((a, b) => a.start - b.start);
  return { fps: +T.fps || 30, scenes, dur: scenes.length ? Math.max(...scenes.map(s => s.end)) : 0 };
}

// Narration beats. at(word, k) = local time of the k-th occurrence of `word` (prefix match): taken from
// injected word timings when present, otherwise from the word's character position in the narration,
// spread over the spoken span [lead, duration - tail]. So beats scale with the era's length.
export function cues(narration, scene, { lead = .5, tail = .8 } = {}) {
  const d = scene.end - scene.start, norm = s => s.toLowerCase().replace(/[^a-z0-9]/g, '');
  const words = Array.isArray(scene.words) && scene.words.length ? scene.words : null;
  const toks = [...narration.matchAll(/[A-Za-z0-9’']+/g)].map(m => ({ w: norm(m[0]), i: m.index }));
  const span = Math.max(.5, d - lead - tail), L = narration.length;
  const at = (w, k = 0) => {
    const n = norm(w);
    if (words) { let c = 0; for (const [t, x] of words) if (norm(String(x)).startsWith(n) && c++ === k) return +t; }
    let c = 0; for (const tk of toks) if (tk.w.startsWith(n) && c++ === k) return lead + tk.i / L * span;
    throw new Error(`cue "${w}" #${k} not in narration`);
  };
  const end = words ? +words[words.length - 1][0] + .35 : lead + span;
  return { at, end, d };
}
