// g02: the Rhine sector near Viersen at night, as German observers on the east bank saw it (March 1945).
// Setup for g03's reveal: here the two American infantry divisions look REAL (solid symbols, moving columns).
// Canvas 2D only (no WebGL). Map drawing follows mg-styles-15's 22-hud approach (topojson-client ->
// GeoJSON -> d3.geoPath on a canvas), with an animated orthographic projection as the camera.
// Every frame is a pure function of t. Positions of roads, columns and the Rhine course are approximate.
import { timing, cues } from './timing.js';
import { makeEras, NARRATIONS } from './eras.js';

const W = 1920, H = 1080, TAU = Math.PI * 2;
const NARRATION = 'Not far from the front, they could see it: the trucks, the tanks and the artillery of two American infantry divisions moving into position. They could hear engines at night. They could pick up the radio traffic.';
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, u) => a + (b - a) * u;
const P = (t, a, d) => clamp((t - a) / Math.max(1e-6, d));
const outC = (u) => 1 - Math.pow(1 - u, 3);
const ioC = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
const outB = (u, s = 1.6) => 1 + (s + 1) * Math.pow(u - 1, 3) + s * Math.pow(u - 1, 2);
const smoother = (u) => u * u * u * (u * (u * 6 - 15) + 10);
function rng(seed) { let a = seed >>> 0; return () => { a |= 0; a = a + 0x6D2B79F5 | 0; let t = Math.imul(a ^ a >>> 15, 1 | a); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

const C = {
  sea0: '#081118', sea1: '#0f1d27', grat: 'rgba(120,160,180,0.09)',
  land: '#1a2730', coast: 'rgba(150,182,196,0.5)', border: 'rgba(150,182,196,0.2)',
  river: '#5f93ad', riverHi: '#a6cbe0', road: 'rgba(196,206,212,0.20)', roadHi: 'rgba(196,206,212,0.08)',
  ink: '#ece7da', dim: 'rgba(236,231,218,0.72)', faint: 'rgba(236,231,218,0.42)',
  blue: '#7db9f2', blueD: '#2c5a85', blueFill: 'rgba(125,185,242,0.30)', red: '#e2583f', amber: '#f2b134',
};
const F = { head: (s) => `400 ${s}px 'League Gothic'`, sans: (w, s) => `${w} ${s}px Inter`, mono: (s) => `500 ${s}px 'IBM Plex Mono'` };

// approximate courses (lon, lat), downstream: upper Rhine coarse, lower Rhine (Bonn -> Emmerich) denser
const RHINE = [[7.59, 47.56], [7.58, 48.03], [7.80, 48.58], [8.05, 48.80], [8.30, 49.00], [8.38, 49.20], [8.47, 49.49], [8.37, 49.83], [8.27, 50.00],
  [7.90, 49.97], [7.80, 50.15], [7.60, 50.36], [7.33, 50.52], [7.21, 50.62], [7.10, 50.74], [7.05, 50.80], [7.00, 50.86], [6.97, 50.90],
  [6.965, 50.94], [6.99, 50.98], [6.98, 51.02], [6.93, 51.06], [6.90, 51.08], [6.88, 51.09], [6.86, 51.11], [6.87, 51.14], [6.86, 51.165],
  [6.82, 51.18], [6.78, 51.19], [6.76, 51.21], [6.765, 51.23], [6.75, 51.25], [6.73, 51.27], [6.72, 51.29], [6.73, 51.305], [6.71, 51.325],
  [6.68, 51.34], [6.66, 51.355], [6.665, 51.375], [6.69, 51.395], [6.72, 51.415], [6.73, 51.44], [6.73, 51.46], [6.71, 51.49], [6.69, 51.52],
  [6.67, 51.55], [6.65, 51.58], [6.63, 51.62], [6.61, 51.655], [6.55, 51.68], [6.48, 51.70], [6.44, 51.72], [6.40, 51.76], [6.33, 51.80],
  [6.25, 51.83], [6.12, 51.86], [5.86, 51.85], [5.40, 51.82], [5.00, 51.83], [4.70, 51.82], [4.40, 51.88], [4.05, 51.98]];
const VIERSEN = [6.395, 51.256];
const DIV = [{ name: '30th Infantry Division', ll: [6.50, 51.405] }, { name: '79th Infantry Division', ll: [6.575, 51.185] }];
const OBS = [[6.93, 51.43], [6.99, 51.24]];   // German observers, east bank
const TOWNS = [['Düsseldorf', 6.773, 51.227], ['Duisburg', 6.762, 51.434]];
// schematic approach roads (approximate), each ends at a division's assembly area
const ROADS = [
  [[5.55, 51.47], [5.75, 51.45], [5.95, 51.44], [6.10, 51.43], [6.22, 51.42], [6.33, 51.415], [6.42, 51.41], [6.47, 51.407]],
  [[5.55, 51.13], [5.75, 51.15], [5.95, 51.16], [6.12, 51.17], [6.28, 51.18], [6.40, 51.185], [6.50, 51.186], [6.545, 51.186]],
  [[5.85, 50.93], [6.00, 50.97], [6.13, 51.02], [6.25, 51.07], [6.36, 51.11], [6.45, 51.145], [6.52, 51.165]],
];
// columns: [road, cue word, glyph kinds front to back]
const COLS = [[0, 'trucks', 'TTTTKKKKKK'], [1, 'tanks', 'KKKKKKTTTT'], [2, 'artillery', 'GGGGGGTTT']];

export function build({ topo50, topo110 }) {
  const cv = document.getElementById('c'), g = cv.getContext('2d');
  const LAND = topojson.feature(topo50, topo50.objects.land);
  const BORDERS = topojson.mesh(topo110, topo110.objects.countries, (a, b) => a !== b);
  const GRAT = d3.geoGraticule().extent([[2, 48], [11, 54]]).step([0.5, 0.5])();
  const FINE = d3.geoGraticule().extent([[5, 50.5], [8, 52]]).step([0.1, 0.1])();
  const proj = d3.geoOrthographic().clipAngle(90).precision(0.3);
  const path = d3.geoPath(proj, g);
  const grain = document.createElement('canvas'); grain.width = grain.height = 256;
  { const x = grain.getContext('2d'), im = x.createImageData(256, 256), r = rng(1945); for (let i = 0; i < im.data.length; i += 4) { const v = 110 + r() * 145; im.data[i] = im.data[i + 1] = im.data[i + 2] = v; im.data[i + 3] = 255; } x.putImageData(im, 0, 0); }
  const GRAIN = g.createPattern(grain, 'repeat');
  const texts = [];   // legibility record per frame: {s, size}

  const TM = timing();
  const ERA = { g02: null };   // g02 draws with renderLocal below; the later map eras come from eras.js (built lazily)
  let LATER = null;
  const eras = TM.scenes.filter((s) => s.id === 'g02' || NARRATIONS[s.id]).map((s) => ({ s, cue: cues(s.id === 'g02' ? NARRATION : NARRATIONS[s.id], s) }));
  if (!eras.length) eras.push({ s: { id: 'g02', start: 0, end: TM.dur || 14.4667 }, cue: null });
  for (const e of eras) if (!e.cue) e.cue = cues(NARRATION, e.s);
  void ERA;

  function label(s, x, y, font, size, col, align = 'left', ls = 0, halo = 'rgba(6,12,17,0.88)', record = true) {
    g.font = font; g.textAlign = align; g.textBaseline = 'middle'; g.letterSpacing = ls + 'px';
    if (halo) { g.lineJoin = 'round'; g.strokeStyle = halo; g.lineWidth = Math.max(4, size * 0.22); g.strokeText(s, x, y); }
    g.fillStyle = col; g.fillText(s, x, y); g.letterSpacing = '0px';
    if (record && g.globalAlpha > 0.05) texts.push({ s, size });
  }
  const rr = (x, y, w, h, r) => { g.beginPath(); g.roundRect(x, y, w, h, r); };
  const vis = (ll, c) => d3.geoDistance(ll, [c.lon, c.lat]) < Math.PI / 2 - 0.02;

  // smooth screen-space Catmull-Rom through projected points
  function crPath(pts) {
    g.beginPath(); if (pts.length < 2) return;
    g.moveTo(pts[0][0], pts[0][1]);
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      g.bezierCurveTo(p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6, p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6, p2[0], p2[1]);
    }
  }
  // dense sample of a Catmull-Rom curve (for placing glyphs along roads)
  function sampleCR(pts, n = 14) {
    const out = [];
    for (let i = 0; i < pts.length - 1; i++) {
      const p0 = pts[Math.max(0, i - 1)], p1 = pts[i], p2 = pts[i + 1], p3 = pts[Math.min(pts.length - 1, i + 2)];
      for (let k = 0; k < n; k++) {
        const u = k / n, u2 = u * u, u3 = u2 * u;
        out.push([0, 1].map((j) => 0.5 * (2 * p1[j] + (-p0[j] + p2[j]) * u + (2 * p0[j] - 5 * p1[j] + 4 * p2[j] - p3[j]) * u2 + (-p0[j] + 3 * p1[j] - 3 * p2[j] + p3[j]) * u3)));
      }
    }
    out.push(pts[pts.length - 1]);
    const cum = [0]; for (let i = 1; i < out.length; i++) cum.push(cum[i - 1] + Math.hypot(out[i][0] - out[i - 1][0], out[i][1] - out[i - 1][1]));
    return { pts: out, cum, L: cum[cum.length - 1] };
  }
  function along(S, s) {   // point + heading at arc length s
    s = clamp(s, 0, S.L); let i = 1; while (i < S.cum.length - 1 && S.cum[i] < s) i++;
    const a = S.pts[i - 1], b = S.pts[i], u = (s - S.cum[i - 1]) / Math.max(1e-6, S.cum[i] - S.cum[i - 1]);
    return { x: lerp(a[0], b[0], u), y: lerp(a[1], b[1], u), ang: Math.atan2(b[1] - a[1], b[0] - a[0]) };
  }

  // vehicle glyphs, solid, drawn heading +x (blackout-light dot in front)
  function glyph(kind, x, y, ang, s, a) {
    g.save(); g.globalAlpha = a; g.translate(x, y); g.rotate(ang); g.scale(s, s);
    g.fillStyle = 'rgba(242,177,52,0.85)'; g.beginPath(); g.arc(17, 0, 1.6, 0, TAU); g.fill();
    g.fillStyle = C.blue; g.strokeStyle = C.blueD; g.lineWidth = 1.2;
    if (kind === 'K') {          // tank: hull, turret, gun
      rr(-13, -7, 26, 14, 3); g.fill(); g.stroke();
      g.fillStyle = C.blueD; g.beginPath(); g.arc(-1, 0, 4.6, 0, TAU); g.fill(); g.fillRect(2, -1.2, 13, 2.4);
    } else if (kind === 'T') {   // truck: cargo box + cab
      g.fillRect(-12, -5.5, 15, 11); g.strokeRect(-12, -5.5, 15, 11); rr(4, -4.5, 8, 9, 2); g.fill(); g.stroke();
    } else {                     // towed gun: tractor + gun on two wheels
      rr(2, -4.5, 10, 9, 2); g.fill(); g.stroke();
      g.fillStyle = C.blueD; g.fillRect(-16, -1.2, 18, 2.4); g.fillStyle = C.blue; g.beginPath(); g.arc(-4, -5, 2.6, 0, TAU); g.arc(-4, 5, 2.6, 0, TAU); g.fill();
    }
    g.restore();
  }
  // NATO-style friendly infantry division symbol: solid frame + X, XX above
  function divSymbol(x, y, t, t0, name, labelBelow) {
    const a = P(t, t0, 0.45); if (a <= 0) return;
    const k = outB(a, 1.4), w = 120, h = 78;
    g.save(); g.translate(x, y); g.scale(k, k);
    g.fillStyle = 'rgba(6,12,17,0.75)'; g.fillRect(-w / 2 - 6, -h / 2 - 34, w + 12, h + 40);
    g.fillStyle = C.blueFill; g.fillRect(-w / 2, -h / 2, w, h);
    g.strokeStyle = C.blue; g.lineWidth = 4.5; g.strokeRect(-w / 2, -h / 2, w, h);
    g.lineWidth = 3.5; g.beginPath(); g.moveTo(-w / 2, -h / 2); g.lineTo(w / 2, h / 2); g.moveTo(w / 2, -h / 2); g.lineTo(-w / 2, h / 2); g.stroke();
    g.lineWidth = 4; for (const [dx, s] of [[-10, 1], [10, -1]]) { g.beginPath(); g.moveTo(dx - 6 * s, -h / 2 - 28); g.lineTo(dx + 6 * s, -h / 2 - 8); g.moveTo(dx + 6 * s, -h / 2 - 28); g.lineTo(dx - 6 * s, -h / 2 - 8); g.stroke(); }
    g.restore();
    const la = P(t, t0 + 0.25, 0.4); g.globalAlpha = la;
    label(name, x, y + (labelBelow ? h / 2 + 34 : -h / 2 - 60), F.sans(650, 30), 30, C.ink, 'center');
    g.globalAlpha = 1;
  }
  function observer(x, y, t, t0, ping) {
    const a = P(t, t0, 0.4); if (a <= 0) return;
    if (ping > 0) for (let i = 0; i < 3; i++) { const u = ((t - t0) * 0.9 + i / 3) % 1; g.strokeStyle = C.red; g.globalAlpha = a * ping * (1 - u) * 0.8; g.lineWidth = 2.5; g.beginPath(); g.arc(x, y, 30 + u * 70, 0, TAU); g.stroke(); }
    g.globalAlpha = a; const k = outB(a);
    g.save(); g.translate(x, y); g.scale(k, k);
    g.fillStyle = 'rgba(6,12,17,0.94)'; g.beginPath(); g.arc(0, 0, 28, 0, TAU); g.fill();
    g.strokeStyle = C.red; g.lineWidth = 3; g.beginPath(); g.arc(0, 0, 28, 0, TAU); g.stroke();
    g.fillStyle = C.red; for (const dx of [-8, 8]) { rr(dx - 6.5, -9, 13, 20, 5); g.fill(); } g.fillRect(-4, -3, 8, 6);
    g.restore(); g.globalAlpha = 1;
  }

  // camera: open on the lower Rhine, push into the sector by "it:", then a slow drift
  function camAt(t, cue) {
    const tPush = Math.max(1.8, cue.at('trucks') - 0.5);
    const K = [[0, 6.30, 51.38, 16000, 960, 540], [tPush, 6.62, 51.31, 98000, 960, 520], [Math.max(tPush + 0.1, cue.d), 6.63, 51.305, 106000, 960, 520]];
    let k = 0; while (k < K.length - 2 && t > K[k + 1][0]) k++;
    const a = K[k], b = K[k + 1], u = (k === 0 ? smoother : ioC)(P(t, a[0], b[0] - a[0]));
    const ip = d3.geoInterpolate([a[1], a[2]], [b[1], b[2]])(u);
    return { lon: ip[0], lat: ip[1], s: Math.exp(lerp(Math.log(a[3]), Math.log(b[3]), u)), x: lerp(a[4], b[4], u), y: lerp(a[5], b[5], u) };
  }

  function renderLocal(t, era) {
    const cue = era.cue, c = camAt(t, cue);
    texts.length = 0;
    g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.setLineDash([]); g.lineDashOffset = 0;
    g.lineCap = 'butt'; g.lineJoin = 'miter'; g.letterSpacing = '0px'; g.filter = 'none';
    proj.rotate([-c.lon, -c.lat]).scale(c.s).translate([c.x, c.y]);
    // base: night sea, land, coast, borders (fade with zoom), graticules
    const bg = g.createRadialGradient(960, 520, 120, 960, 540, 1250); bg.addColorStop(0, C.sea1); bg.addColorStop(1, C.sea0);
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
    g.fillStyle = C.land; g.beginPath(); path(LAND); g.fill();
    g.strokeStyle = C.coast; g.lineWidth = 1.3; g.beginPath(); path(LAND); g.stroke();
    const bA = 1 - clamp((c.s - 22000) / 30000);
    if (bA > 0) { g.globalAlpha = bA; g.setLineDash([5, 5]); g.strokeStyle = C.border; g.lineWidth = 1.2; g.beginPath(); path(BORDERS); g.stroke(); g.setLineDash([]); g.globalAlpha = 1; }
    g.strokeStyle = C.grat; g.lineWidth = 1; g.beginPath(); path(GRAT); g.stroke();
    const fA = clamp((c.s - 45000) / 40000);
    if (fA > 0) {
      g.globalAlpha = fA; g.strokeStyle = 'rgba(120,160,180,0.08)'; g.beginPath(); path(FINE); g.stroke();
      const tl = proj.invert([0, 0]), br = proj.invert([W, H]);
      const dm = (v, h) => { const m = Math.round(v * 60); return `${Math.floor(m / 60)}°${String(m % 60).padStart(2, '0')}′${h}`; };
      for (let la = Math.ceil(br[1] * 10) / 10; la <= tl[1]; la += 0.1) { const y = proj([tl[0] + 0.02, la])[1]; if (y > 200 && y < H - 70) label(dm(la, 'N'), 26, y, F.mono(16), 16, C.faint, 'left', 0, null, false); }
      for (let lo = Math.ceil(tl[0] * 10) / 10; lo <= br[0]; lo += 0.1) { const x = proj([lo, br[1] + 0.01])[0]; if (x > 90 && x < W - 380) label(dm(lo, 'E'), x, H - 24, F.mono(16), 16, C.faint, 'center', 0, null, false); }
      g.globalAlpha = 1;
    }
    // country names on the wide shot only
    const cn = 1 - P(t, 0.9, 0.9);
    if (cn > 0) { g.globalAlpha = cn * 0.9; for (const [n, lo, la] of [['NETHERLANDS', 5.55, 51.95], ['GERMANY', 7.45, 51.0], ['BELGIUM', 5.35, 50.82]]) if (vis([lo, la], c)) { const [x, y] = proj([lo, la]); label(n, x, y, F.sans(600, 28), 28, C.faint, 'center', 8, null); } g.globalAlpha = 1; }

    // roads (schematic, approximate)
    const roadPts = ROADS.map((r) => r.filter((ll) => vis(ll, c)).map((ll) => proj(ll)));
    const rA = P(t, 0.6, 1.2);
    if (rA > 0) { g.globalAlpha = rA; g.lineCap = 'round'; g.lineJoin = 'round';
      for (const pts of roadPts) { g.strokeStyle = C.road; g.lineWidth = 7; crPath(pts); g.stroke(); g.strokeStyle = C.roadHi; g.lineWidth = 15; crPath(pts); g.stroke(); }
      g.globalAlpha = 1; }
    // the Rhine
    { const pts = RHINE.filter((ll) => vis(ll, c)).map((ll) => proj(ll)), rw = Math.min(17, Math.max(2, c.s / 6500));
      g.lineCap = 'round'; g.lineJoin = 'round';
      g.strokeStyle = 'rgba(95,147,173,0.25)'; g.lineWidth = rw * 2.2; crPath(pts); g.stroke();
      g.strokeStyle = C.river; g.lineWidth = rw; crPath(pts); g.stroke();
      g.strokeStyle = C.riverHi; g.lineWidth = Math.max(1, rw * 0.2); crPath(pts); g.stroke(); }
    // towns (east-bank context) + river label
    const zA = P(t, 1.6, 0.8);
    if (zA > 0) {
      g.globalAlpha = zA;
      for (const [n, lo, la] of TOWNS) { const [x, y] = proj([lo, la]); g.fillStyle = C.dim; g.beginPath(); g.arc(x, y, 5, 0, TAU); g.fill(); label(n, x + 16, y, F.sans(500, 28), 28, C.dim, 'left'); }
      const a = proj([6.735, 51.29]), b = proj([6.725, 51.31]);
      g.save(); g.translate(a[0] + 46, a[1]); g.rotate(Math.atan2(b[1] - a[1], b[0] - a[0])); label('RHINE', 0, 0, F.sans(650, 30), 30, C.riverHi, 'center', 12); g.restore();
      g.globalAlpha = 1;
    }
    // Viersen
    { const [x, y] = proj(VIERSEN), a = P(t, 1.2, 0.6);
      if (a > 0) { g.globalAlpha = a; g.fillStyle = 'rgba(6,12,17,0.9)'; g.beginPath(); g.arc(x, y, 13, 0, TAU); g.fill(); g.fillStyle = C.ink; g.beginPath(); g.arc(x, y, 8, 0, TAU); g.fill();
        label('VIERSEN', x - 24, y + 3, F.head(56), 56, C.ink, 'right', 3); g.globalAlpha = 1; } }

    // German observers on the east bank: sight cones toward the west bank from "see"
    const tSee = cue.at('see'), tRadio = cue.at('radio'), oPts = OBS.map((ll) => proj(ll));
    const sA = P(t, tSee, 0.8) * 0.9;
    if (sA > 0) oPts.forEach(([ox, oy], i) => {
      const [tx, ty] = proj(DIV[i].ll), ang = Math.atan2(ty - oy, tx - ox), R = Math.hypot(tx - ox, ty - oy) + 120, sw = 0.16 + 0.04 * Math.sin(t * 0.7 + i);
      const gr = g.createRadialGradient(ox, oy, 20, ox, oy, R); gr.addColorStop(0, 'rgba(226,88,63,0.20)'); gr.addColorStop(1, 'rgba(226,88,63,0)');
      g.globalAlpha = sA; g.fillStyle = gr; g.beginPath(); g.moveTo(ox, oy); g.arc(ox, oy, R, ang - sw, ang + sw); g.closePath(); g.fill(); g.globalAlpha = 1;
    });
    oPts.forEach(([x, y], i) => observer(x, y, t, tSee - 0.3 + i * 0.15, P(t, tRadio + 0.5, 0.4)));
    { const a = P(t, tSee + 0.2, 0.5); if (a > 0) { g.globalAlpha = a; label('German observers · east bank', oPts[0][0] + 44, oPts[0][1] - 52, F.sans(600, 28), 28, C.red, 'left'); g.globalAlpha = 1; } }

    // columns move along the roads into position, arriving by "position"
    const tArr = cue.at('position') + 0.1, shots = [];
    COLS.forEach(([ri, word, kinds], ci) => {
      if (roadPts[ri].length < 2) return;
      const S = sampleCR(roadPts[ri], 12), t0 = cue.at(word) - 0.25, gap = 46;
      const u = P(t, t0, Math.max(0.8, tArr - t0 + ci * 0.15)), head = lerp(-10, S.L - 70, 1 - Math.pow(1 - u, 2.2));
      if (u <= 0) return;
      [...kinds].forEach((k, i) => {
        const s = head - i * gap; if (s < 0) return;
        const p = along(S, s), jig = (u < 1 ? 0.8 * Math.sin(t * 13 + i * 2.1 + ci) : 0);
        glyph(k, p.x, p.y + jig, p.ang, 1.7, clamp(s / 40));
        if (i % 2 === 0) shots.push([p.x, p.y]);
      });
    });

    // division symbols land on "two" / "infantry"
    const dPts = DIV.map((d) => proj(d.ll));
    divSymbol(dPts[0][0], dPts[0][1], t, cue.at('two') - 0.1, DIV[0].name, false);
    divSymbol(dPts[1][0], dPts[1][1], t, cue.at('infantry') - 0.1, DIV[1].name, true);

    // engines at night: sound arcs from the columns, facing the east bank
    const tEng = cue.at('engines') - 0.15;
    if (t > tEng) {
      const eA = P(t, tEng, 0.4) * (1 - 0.6 * P(t, tRadio, 1.0));
      g.lineCap = 'round';
      shots.forEach(([x, y], i) => { if (i % 2) return; for (let k = 0; k < 3; k++) {
        const v = ((t - tEng) * 0.55 + k / 3 + i * 0.13) % 1; g.strokeStyle = 'rgba(166,203,224,1)'; g.globalAlpha = eA * (1 - v) * 0.8; g.lineWidth = 3.5 - 1.5 * v;
        g.beginPath(); g.arc(x, y, 18 + v * 230, -0.55, 0.55); g.stroke(); } });
      g.globalAlpha = 1;
      const la = P(t, tEng + 0.2, 0.4) * (1 - P(t, tRadio - 0.3, 0.4));
      if (la > 0) { g.globalAlpha = la; const m = proj([6.66, 51.30]); label('engines, at night', m[0] - 10, m[1] + 6, F.sans(600, 28), 28, C.riverHi, 'right'); g.globalAlpha = 1; }
    }
    // radio traffic between the two division HQs, picked up on the east bank
    if (t > tRadio - 0.2) {
      const rA2 = P(t, tRadio - 0.2, 0.4), A = dPts[0], B = dPts[1], cx = Math.min(A[0], B[0]) - 170, cy = (A[1] + B[1]) / 2;
      const q = (u) => [(1 - u) * (1 - u) * A[0] + 2 * (1 - u) * u * cx + u * u * B[0], (1 - u) * (1 - u) * (A[1] + 40) + 2 * (1 - u) * u * cy + u * u * (B[1] - 40)];
      g.globalAlpha = rA2; g.strokeStyle = C.blue; g.lineWidth = 2.5; g.setLineDash([6, 10]); g.lineDashOffset = -t * 60;
      g.beginPath(); for (let i = 0; i <= 40; i++) { const [x, y] = q(i / 40); i ? g.lineTo(x, y) : g.moveTo(x, y); } g.stroke(); g.setLineDash([]); g.lineDashOffset = 0;
      for (let k = 0; k < 4; k++) { const u = ((t - tRadio) * 0.45 + k / 4) % 1, [x, y] = q(u); g.fillStyle = C.blue; rr(x - (k % 2 ? 9 : 3), y - 3, k % 2 ? 18 : 6, 6, 3); g.fill(); }
      // radio waves from both HQs, and an intercept trace to each observer
      for (const [x, y] of [A, B]) for (let k = 0; k < 2; k++) { const v = ((t - tRadio) * 0.8 + k / 2) % 1; g.strokeStyle = C.blue; g.globalAlpha = rA2 * (1 - v) * 0.7; g.lineWidth = 2; g.beginPath(); g.arc(x, y, 50 + v * 90, -Math.PI * 0.9, -Math.PI * 0.1); g.stroke(); }
      g.globalAlpha = rA2;
      const ip = P(t, tRadio + 0.3, 0.6);
      oPts.forEach(([ox, oy], i) => { const [sx, sy] = dPts[i]; const ex = lerp(sx + 60, ox - 30, outC(ip)), ey = lerp(sy, oy, outC(ip));
        g.strokeStyle = 'rgba(226,88,63,0.85)'; g.lineWidth = 2; g.setLineDash([2, 8]); g.beginPath(); g.moveTo(sx + 60, sy); g.lineTo(ex, ey); g.stroke(); g.setLineDash([]); });
      const lb = P(t, tRadio + 0.5, 0.4); if (lb > 0) { g.globalAlpha = lb; label('radio traffic, intercepted', oPts[1][0] + 44, oPts[1][1] + 56, F.sans(600, 28), 28, C.red, 'left'); }
      g.globalAlpha = 1;
    }

    // frame furniture: header, date chip, approx note, scale bar, vignette + grain
    const hA = P(t, 0.15, 0.5); g.globalAlpha = hA;
    label('THE RHINE, NEAR VIERSEN', 96, 92, F.head(54), 54, C.ink, 'left', 4, null);
    label('west bank, seen from the east bank', 96, 140, F.sans(500, 28), 28, C.dim, 'left', 0, null);
    { const s = 'MARCH 1945'; g.font = F.mono(28); g.letterSpacing = '3px'; const w = g.measureText(s).width + 48; g.letterSpacing = '0px';
      g.fillStyle = 'rgba(242,177,52,0.14)'; rr(1824 - w, 66, w, 52, 26); g.fill(); g.strokeStyle = 'rgba(242,177,52,0.6)'; g.lineWidth = 1.5; rr(1824 - w, 66, w, 52, 26); g.stroke();
      label(s, 1824 - w / 2, 93, F.mono(28), 28, C.amber, 'center', 3, null); }
    label('approximate positions · schematic roads', 96, 182, F.mono(18), 18, C.faint, 'left', 1, null, false);
    g.globalAlpha = 1;
    const km = c.s / 6371, L = 10 * km;
    if (L > 60 && L < 420) { const x0 = W - 96 - L, y0 = H - 78; g.globalAlpha = fA > 0 ? 1 : 0.8;
      g.fillStyle = C.dim; g.fillRect(x0, y0, L, 3); g.fillRect(x0, y0 - 9, 2, 12); g.fillRect(x0 + L - 2, y0 - 9, 2, 12); g.fillRect(x0 + L / 2 - 1, y0 - 6, 2, 9);
      label('10 km', x0 + L, y0 - 26, F.mono(22), 22, C.dim, 'center', 0, null, false); g.globalAlpha = 1; }
    const f = Math.round(t * 30), r1 = rng(f + 7)(), r2 = rng(f + 99)();
    g.save(); g.globalAlpha = 0.045; g.globalCompositeOperation = 'overlay'; g.translate(-r1 * 256, -r2 * 256); g.fillStyle = GRAIN; g.fillRect(0, 0, W + 256, H + 256); g.restore();
    const v = g.createRadialGradient(960, 540, 500, 960, 540, 1180); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.6)');
    g.fillStyle = v; g.fillRect(0, 0, W, H);
  }

  const find = (t) => eras.find((e) => t >= e.s.start && t < e.s.end) || eras[eras.length - 1];
  const kit = () => (LATER = LATER || makeEras({ g, proj, path, LAND, BORDERS, CTRY: topojson.feature(topo110, topo110.objects.countries), C, F, label, rr, vis, crPath, sampleCR, along, glyph, observer, GRAIN, rng, RHINE, ROADS, DIV, OBS, TOWNS }));
  const draw = (e, t) => { const lt = clamp(t - e.s.start, 0, e.s.end - e.s.start); texts.length = 0; if (e.s.id === 'g02') renderLocal(lt, e); else kit()[e.s.id](lt, e.cue); };
  return {
    dur: Math.max(TM.dur, ...eras.map((e) => e.s.end)),
    scenes: eras.map((e) => ({ id: e.s.id, start: e.s.start, end: e.s.end, words: !!e.cue.fromWords })),
    render: (t) => draw(find(t), t),
    minText: (t) => { const e = find(t); draw(e, t);
      let m = 1e9, which = ''; for (const x of texts) if (x.size < m) { m = x.size; which = x.s; } return { scene: e.s.id, px: m === 1e9 ? null : m, text: which }; },
  };
}
