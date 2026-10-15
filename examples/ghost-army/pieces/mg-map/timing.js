// Scene timing for this piece (same contract as pieces/lemo-blueprint/timing.js).
// html_seek injects window.STUDIO_TIMING = {fps, scenes: [{id, start, end, words?: [[t_local, word], ...]}]}
// before any page script runs (params.timing; params.era picks the scene and adds its words).
// Without it the production default below applies. The page clock is the piece clock: scene X spans
// [start_X, end_X) and the pipeline renders it with offset = start_X for end_X - start_X seconds.
// Production defaults: the map eras laid end to end in film order (scene durations from the narration timeline).
export const DEFAULT = { fps: 30, scenes: (() => { let t = 0; return [['g02', 14.4667], ['g20', 24.4333], ['g23', 18.9333], ['g24', 24.7667], ['g26', 12.2], ['g28', 20.6667], ['g31', 33.8]]
  .map(([id, d]) => { const s = { id, start: +t.toFixed(4), end: +(t + d).toFixed(4) }; t += d; return s; }); })() };

export function timing() {
  const T = (typeof window !== 'undefined' && window.STUDIO_TIMING) || DEFAULT;
  const scenes = (T.scenes || []).map((s) => ({ ...s, start: +s.start, end: +s.end })).filter((s) => s.end > s.start)
    .sort((a, b) => a.start - b.start);
  return { fps: +T.fps || 30, scenes, dur: scenes.length ? Math.max(...scenes.map((s) => s.end)) : 0 };
}

// Narration beats. at(word, k) = scene-local time of the k-th occurrence of `word` (prefix match), from the
// injected word timings when present, otherwise from the word's character position in the narration spread
// over the spoken span [lead, duration - tail], so beats scale with the scene's length.
export function cues(narration, scene, { lead = 0.5, tail = 0.8 } = {}) {
  const d = scene.end - scene.start, norm = (s) => s.toLowerCase().replace(/[^a-z0-9]/g, '');
  const words = Array.isArray(scene.words) && scene.words.length ? scene.words : null;
  const toks = [...narration.matchAll(/[A-Za-z0-9’']+/g)].map((m) => ({ w: norm(m[0]), i: m.index }));
  const span = Math.max(0.5, d - lead - tail), L = narration.length;
  const at = (w, k = 0) => {
    const n = norm(w);
    if (words) { let c = 0; for (const [t, x] of words) if (norm(String(x)).startsWith(n) && c++ === k) return +t; }
    let c = 0; for (const tk of toks) if (tk.w.startsWith(n) && c++ === k) return lead + (tk.i / L) * span;
    throw new Error(`cue "${w}" #${k} not in narration`);
  };
  const end = words ? +words[words.length - 1][0] + 0.35 : lead + span;
  return { at, end, d, fromWords: !!words };
}
