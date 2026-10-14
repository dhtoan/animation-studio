// =====================================================================
//  GHOST ARMY — cameras and shape-morph bridges, all derived from GA_TIMING (read by kit/morph.js)
//  A bridge exists only where timing.js says bridge_next (the two scenes are adjacent on the final timeline).
//  Morphs are short: d = 0.5s each side, m = 0.12s -> 0.24s on blank paper.
// =====================================================================
const ERA_BG = GA_SCENES.map((s) => GA_BG[s.id] || '#efe5cf');
const GA_CAMS = {
  g01: (s, t) => gaRhineCam(s, t, false), g03: (s, t) => gaRhineCam(s, t, true), g05: gaPlanCam, g11: gaNamesCam,
  g13: gaInflateCam, g18: gaEffectsCam, g04: (s, t) => push(t, s.start + 0.3, s.end, { z: 1.05, p: [960, 540], to: [960, 540] }),
};
function pieceCam(era, t) { const s = GA_SCENES[era], f = s && GA_CAMS[s.id]; return f ? f(s, t) : null; }
const gaCircle = (x, y, r) => ellipsePts(x, y, r, r, 0, 64);
// the object each era closes onto (OUT) and opens from (IN): { P: points, c: '#hex' } in that era's world coords
const GA_OUT = {
  g01: () => ({ P: gaCircle(...RH.moon), c: '#c8d0f0' }), g03: () => ({ P: gaCircle(...RH.moon), c: '#c8d0f0' }),
  g04: () => ({ P: gaCircle(1390, 650, 140), c: '#26315f' }), g05: () => ({ P: box(250, 730, 520, 230), c: '#f6efd9' }),
  g10: () => ({ P: box(...RC.book), c: '#6f7046' }), g11: () => ({ P: box(RC.card0[0] + 1260, RC.card0[1] + 24, RC.card0[2], RC.card0[3]), c: '#f6efd9' }),
  g13: () => ({ P: gaTankOutline(...DC.tank13), c: '#6f7046' }),
  g14: (s) => { const [wx, up] = dcCarry(s); return { P: gaTankOutline(DC.tank14[0] + wx, DC.tank14[1] - up, DC.tank14[2]), c: '#6f7046' }; },
  g18: () => ({ P: box(...TH.bumper), c: '#4a4b2c' }), g19: (s) => ({ P: box(...thBlade(s)), c: '#8d7a3a' }),
};
const GA_IN = {
  g01: () => ({ P: gaCircle(...RH.moon), c: '#c8d0f0' }), g03: () => ({ P: gaCircle(...RH.moon), c: '#c8d0f0' }),
  g04: () => ({ P: gaCircle(1390, 650, 140), c: '#26315f' }), g05: () => ({ P: box(100, 70, 1100, 640), c: '#a9c4cf' }),
  g10: () => ({ P: box(170, 330, 320, 380), c: '#f6f0de' }), g11: () => ({ P: box(...RC.card0), c: '#f6efd9' }),
  g13: () => ({ P: ellipsePts(DC.tank13[0], DC.tank13[1] - 34, 520, 50, 0, 64), c: '#6f7046' }),
  g14: () => ({ P: gaTankOutline(...DC.tank14), c: '#6f7046' }),
  g18: () => ({ P: gaPatchPts(...TH.patch), c: '#d9b23c' }), g19: (s) => ({ P: box(...thBlade(s)), c: '#8d7a3a' }),
};
const BRIDGES = GA_BRIDGED.filter((s) => GA_OUT[s.id] && GA_IN[s.next.id]).map((s) => {
  const d = Math.max(0.2, Math.min(0.5, s.dur * 0.1, s.next.dur * 0.1));
  return { tc: s.next.start, d, m: Math.min(0.12, d * 0.4), A: () => GA_OUT[s.id](s), B: () => GA_IN[s.next.id](s.next) };
});
