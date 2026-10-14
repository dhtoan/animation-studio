// lemo-opuscar page contract (core/README.md): window.READY, window.render(t), window.DUR, window.EV.
// The blueprint compositor (paper.js, WebGL2) turns the engine's ink/fx/overlay canvases into the sheet.
// window.MIN_TEXT(t) reports the smallest on-screen font size (px) for the legibility check.
import { W, H, inkC, fxC, ovC } from '/styles/blueprint/demo/draw.js';
import { makePaper } from '/styles/blueprint/demo/paper.js';
import { build } from './film.js';
const comp = makePaper(document.getElementById('c'), W, H);
await Promise.all(['400 40px Architects', '400 40px B612', '700 40px B612'].map(s => document.fonts.load(s)));
const F = build();
window.render = t => { const o = F.render(t); comp(inkC, fxC, ovC, o); };
window.DUR = F.dur; window.EV = F.ev; window.SCENES = F.scenes;
window.MIN_TEXT = t => F.minText(t);
window.READY = true;
