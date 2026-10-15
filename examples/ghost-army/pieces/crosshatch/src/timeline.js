// =====================================================================
//  THE GHOST ARMY — crosshatch scenes. 16:9 1920x1080 at GA_TIMING.fps (30: on 2s = 15 drawings/s).
//  Everything time-related is DERIVED from window.GA_TIMING (src/timing.js): the eras, their beats (fractions of
//  each era with minimum/maximum holds), the morph bridges, captions, the score and DURATION.
//  RED means FAKE and nothing else (decoys, fake patches, false markings, fake tracks, recorded sound, the plan).
//  Facts on screen come only from the project dossier. Oral history and portraits are labelled illustrative.
//  Kit and renderer: cth9191/animate (MIT). This piece: the studio's own code.
// =====================================================================
const GA_T = window.GA_TIMING || { fps: 30, scenes: [] };
const FPS = GA_T.fps || 30, W = 1920, H = 1080;
const BPM = 112.5, BEAT = 60 / BPM, E8 = BEAT / 2, E16 = BEAT / 4;
const gaSnap = (t) => Math.round(t * FPS) / FPS;   // every boundary sits on a frame, so a cut lands on its first frame
const GA_SCENES = GA_T.scenes.map((s) => ({ ...s, start: gaSnap(s.start), end: gaSnap(s.end) }))
  .sort((a, b) => a.start - b.start)
  .map((s, i) => ({ ...s, i, dur: Math.max(0.5, s.end - s.start), next: null }));
GA_SCENES.forEach((s, i) => { s.next = GA_SCENES[i + 1] || null; });
const DURATION = GA_SCENES.length ? GA_SCENES[GA_SCENES.length - 1].end : 10;
const NFRAMES = Math.round(DURATION * FPS);
const LOOP_T = NFRAMES / FPS;
const SAFE = { top: 60, bottom: 110, right: 60 };
const HAND = '"Ink Free", "Segoe Print", "Bradley Hand", "Chalkboard SE", "Comic Sans MS", "Comic Neue", cursive';
const CX = W / 2;
// a beat inside era s: at fraction f of its length, but never earlier than lo or later than hi seconds after its
// start, and never in the last `tail` seconds (so a long era holds longer, a short one still shows every beat)
function gaAt(s, f, lo = 0.3, hi = 1e9, tail = 0.8) { return s.start + Math.max(Math.min(lo, s.dur * 0.5), Math.min(f * s.dur, hi, s.dur - tail)); }
const gaEnd = (s, sec) => s.end - Math.min(sec, s.dur * 0.4);   // a beat `sec` before the era ends
// the draw function and look of each scene id
const GA_DRAW = {
  g01: (s) => gaRhine(s, false), g03: (s) => gaRhine(s, true), g04: (s) => gaTitle(s), g05: (s) => gaPlan(s),
  g10: (s) => gaRecruit(s), g11: (s) => gaNames(s), g13: (s) => gaInflate(s), g14: (s) => gaLift(s),
  g18: (s) => gaEffects(s), g19: (s) => gaEngineers(s),
  g21: (s) => gaMason(s), g25: (s) => gaLimpertsberg(s), g27: (s) => gaBouzonville(s), g32: (s) => gaFox(s),
  g33: (s) => gaCity(s), g35: (s) => gaFamily(s), g41: (s) => gaVeterans(s), g45: (s) => gaEndCard(s),
};
const GA_BG = { g01: '#0c0d1c', g03: '#0c0d1c', g04: '#d6a466', g05: '#cdbb94', g10: '#e6dcc3', g11: '#c99a62', g13: '#e8e0c8', g14: '#ece4cc', g18: '#d6a466', g19: '#e9cfa0',
  g21: '#e6e2cc', g25: '#e4e1d4', g27: '#0a0b16', g32: '#d6a466', g33: '#0c0d1c', g35: '#d8c8a8', g41: '#e6e0d2', g45: '#d6a466' };
// eras: each runs to the next scene's start (a gap in the timing holds the previous era)
const ERA_LIST = GA_SCENES.map((s) => [s.start, s.next ? s.next.start : s.end, () => (GA_DRAW[s.id] || gaUnknown)(s)]);
function gaUnknown(s) { paperSheet('unk' + s.id); handText(s.id, 120, 200, 80, C.ink, { key: 'unk' }); }
const SHOTS = GA_SCENES.map((s) => [s.id, s.i, s.start, ERA_LIST[s.i][1], s.id]);
const GA_BRIDGED = GA_SCENES.filter((s) => s.bridge_next && s.next);
const TIMELINE = {
  width: W, height: H, fps: FPS, bpm: BPM, duration: DURATION, frames: NFRAMES, loop: LOOP_T, safe: SAFE, aspect: '16:9',
  format: 'morph-chain',
  shots: SHOTS.map(([key, era, t0, t1, title], i) => ({ id: i + 1, key, era, t0, t1, title })),
  cuts: GA_SCENES.filter((s) => s.next && !s.bridge_next).map((s) => s.next.start),
  morphs: GA_BRIDGED.map((s) => s.next.start),
  cues: {},
  acts: GA_SCENES.map((s) => ({ name: s.id, role: s.id === 'g03' ? 'gift' : 'build', t0: s.start, t1: s.end })),
  narration: [],
  board: GA_SCENES.map((s) => ({ t: gaAt(s, 0.62), title: s.id, sound: '', next: s.bridge_next ? 'morph' : 'cut' })),
  scenes: GA_SCENES.map(({ id, start, end, bridge_next }) => ({ id, start, end, bridge_next })),
};
window.TIMELINE = TIMELINE;
// the scene id drawn at absolute time t (same frame rule as kit/morph.js renderFrame): for the studio's tests
window.gaEraIdAt = (t) => { const F = ((Math.round(t * FPS) % NFRAMES) + NFRAMES) % NFRAMES; const e = Math.max(0, eraAt(F / FPS)); return GA_SCENES[e] ? GA_SCENES[e].id : null; };
