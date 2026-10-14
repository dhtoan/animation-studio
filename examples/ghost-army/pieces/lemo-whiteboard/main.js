// lemo-opuscar page contract (core/README.md): window.READY, window.render(t), window.DUR, window.EV.
// window.MIN_TEXT(t) reports the smallest on-screen label (px) for the legibility check.
import { build } from './film.js';
const F = await build();
const ctx = document.getElementById('c').getContext('2d');
window.DUR = F.dur; window.EV = F.ev; window.SUBS = F.subs; window.SCENES = F.scenes;
window.render = t => F.render(ctx, t);
window.MIN_TEXT = t => F.minText(t);
window.READY = true;
