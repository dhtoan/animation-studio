// One page, three seek contracts (all relative paths, so it works mounted at /@film/ or served from its folder):
//   lemo-opuscar  window.READY, window.render(t), window.DUR, window.MIN_TEXT(t)  (html_seek's project-page contract)
//   generic       window.renderFrame(t)
//   mg-styles-15  window.DEMO, window.renderAt(t), window.__ready              (harness/render.mjs)
import { build } from './film.js';
const [topo50, topo110] = await Promise.all(['data/land-50m.json', 'data/countries-110m.json'].map((u) => fetch(u).then((r) => r.json())));
await Promise.all(["400 56px 'League Gothic'", '500 28px Inter', '600 28px Inter', '650 30px Inter', "500 22px 'IBM Plex Mono'"].map((f) => document.fonts.load(f)));
await document.fonts.ready;
const F = build({ topo50, topo110 });
window.render = (t) => F.render(t);
window.renderFrame = window.render;
window.renderAt = async (t) => F.render(t);
window.DUR = F.dur; window.SCENES = F.scenes;
window.MIN_TEXT = (t) => F.minText(t);
window.DEMO = { width: 1920, height: 1080, fps: 30, duration: F.dur, motionBlur: { samples: 1, shutter: 0.5 } };
F.render(0);
window.READY = true; window.__ready = true;
