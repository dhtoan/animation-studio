// Ghost Army — g08 (the 23rd's four components) and g12 (the four tools), drawn live with the
// whiteboard engine of lemo-opuscar (MIT), imported from the library at /styles/whiteboard/demo/engine/wb.js.
// Each era is its own board, timeline and camera, so every scene starts clean. Beats come from the
// narration (timing.js), so the drawing scales with the era's duration.
// Facts: the project's Ghost Army dossier only (the narration text below is the production narration).
import * as W from '/styles/whiteboard/demo/engine/wb.js';
import { mulberry, clamp } from '/core/lib.js';
import { timing, cues } from './timing.js';

const { INK } = W;
const N08 = 'The 23rd was built from specialized parts. A camouflage battalion handled visual deception. A special signal company handled radio. A sonic company, the 3132nd, handled sound. And an engineer combat company guarded the perimeter and helped stage the illusions.';
const N12 = 'So far we have an unusual unit of about eleven hundred men, many of them artists. Now, how did they actually fool an enemy army? The Ghost Army worked with four tools: things you could see, things you could hear, radio traffic, and a kind of theater. Used together, they could make a small force look and sound like a large one.';

// ───────── shared era scaffolding
function era(scene, narration) {
  const tl = new W.Timeline(), C = cues(narration, scene), texts = [];
  const K = new W.Pen('black', INK.black, { park: [2150, 1250] });
  const B = new W.Pen('blue', INK.blue, { park: [2250, 1150] });
  const O = new W.Pen('orange', INK.orange, { park: [2050, 1350] });
  for (const p of [K, B, O]) p.free = 0;
  // draw inside [a, b] without ever overlapping the pen's previous window; min/max hold the speed sane
  const D = (pen, shapes, a, b, o = {}) => {
    const a2 = Math.max(a, pen.free + .05), b2 = clamp(b, a2 + (o.min ?? .3), a2 + (o.max ?? 6));
    pen.free = b2; return tl.draw(pen, shapes, a2, { by: b2, minGap: .015, maxGap: .05, ...o });
  };
  // handwriting that is recorded for the 28 px legibility check (cap height h in world units)
  const T = (str, x, y, o = {}) => { const s = W.text(str, x, y, o); texts.push({ str, h: o.h ?? 60, x0: s.x0, x1: s.x0 + s.width, y, strokes: s }); return s; };
  return { tl, C, K, B, O, PENS: [K, B, O], D, T, texts };
}
function ghostMarks(seed, w, h) {
  const out = [], R = mulberry(seed);
  for (let i = 0; i < 24; i++) {
    const x = R() * (w - 300) + 150, y = R() * (h - 300) + 150, k = R(), o = { w: 11, alpha: .05 + R() * .04, color: R() < .25 ? '#8aa0c8' : '#9aa0a8' };
    if (k < .35) out.push(...W.text(['map', 'D+8', 'route', 'q.4', 'ok', 'N', 'B co.', 'rev'][i % 8], x, y, { h: 44 + R() * 30, ...o }));
    else if (k < .6) out.push(W.circle(x, y, 40 + R() * 90, o));
    else if (k < .8) out.push(...W.arrow(x, y, x + (R() - .5) * 400, y + (R() - .5) * 240, o));
    else out.push(W.line(x, y, x + 160 + R() * 380, y + (R() - .5) * 60, o));
  }
  return out;
}
function finish(E, cam, size) {
  E.tl.end();
  const board = new W.Board(E.tl, { ghosts: ghostMarks(size.seed, size.W, size.H), W: size.W, H: size.H });
  board.objs.push({ draw: (ctx, t, c) => { for (const p of E.PENS) W.drawMarker(ctx, p, W.penPose(p, t, cam), c, t); } });
  const off = new OffscreenCanvas(1920, 1080), oc = off.getContext('2d');
  const raw = cam.at.bind(cam);       // never show past the board edge
  cam.at = t => { const c = raw(t), hw = 960 / c.z, hh = 540 / c.z; return { ...c, x: clamp(c.x, hw, size.W - hw), y: clamp(c.y, hh, size.H - hh) }; };
  E.render = (ctx, t) => {           // camera motion blur on fast moves, as in the style's demo
    const dt = 1 / 30, a = cam.at(t), b = cam.at(Math.max(0, t - dt));
    const sp = Math.hypot((a.x - b.x) * a.z, (a.y - b.y) * a.z) + Math.abs(Math.log(a.z / b.z)) * 900;
    const n = sp > 14 ? Math.min(8, Math.ceil(sp * .5 / 4)) : 1;
    if (n === 1) { board.render(ctx, t, cam); return; }
    for (let i = 0; i < n; i++) { board.render(oc, t - dt * .5 * i / (n - 1), cam); ctx.globalAlpha = 1 / (i + 1); ctx.drawImage(off, 0, 0); }
    ctx.globalAlpha = 1;
  };
  E.minText = t => {                 // smallest on-screen cap height (px) among written labels in frame
    const c = cam.at(t); let m = 1e9, which = '';
    for (const x of E.texts) {
      if (Math.min(...x.strokes.map(k => k.t0)) > t) continue;
      const [sx0, sy] = W.toScreen(c, x.x0, x.y), [sx1] = W.toScreen(c, x.x1, x.y);
      if (sx1 < 0 || sx0 > 1920 || sy < 0 || sy - x.h * c.z > 1080) continue;
      if (x.h * c.z < m) { m = x.h * c.z; which = x.str; }
    }
    return { px: m === 1e9 ? null : +m.toFixed(1), text: which };
  };
  E.cam = cam; E.ev = E.tl.ev;
  return E;
}

// ═════════ g08 · the 23rd, built from four specialized parts
function buildG08(scene) {
  const E = era(scene, N08), { D, T, K, B, O, C } = E, TX = 1500;
  const at = C.at, d = C.d;
  const tCam = at('camouflage'), tSig = at('signal'), tSon = at('sonic'), tEng = at('engineer'), tPer = at('perimeter'), tIll = at('illusions');
  // header: the unit, then the nickname and the "parts" note in the margins
  D(K, T('23rd Headquarters', TX, 290, { h: 72, w: 9, align: 'center' }), .3, Math.min(1.7, tCam - 1.2), { min: .9 });
  D(K, T('Special Troops', TX, 395, { h: 72, w: 9, align: 'center' }), 0, Math.min(2.5, tCam - .6), { min: .6 });
  D(K, W.roundRect(TX - 620, 180, 1240, 270, 44, { w: 10 }), 0, tCam - .2, { min: .35, max: .6 });
  D(O, T('"Ghost Army"', 640, 300, { h: 46, w: 7, align: 'center' }), .9, 2.0, { min: .5 });
  D(O, W.curve([[440, 325], [640, 334], [840, 320]], { w: 9, over: 10 }), 0, 2.4, { min: .2, max: .35 });
  D(B, [...T('specialized', 2370, 285, { h: 44, w: 6, align: 'center' }), ...T('parts', 2370, 345, { h: 44, w: 6, align: 'center' })], .8, 2.1, { min: .6 });
  D(B, W.arrow(2370, 370, 2150, 600, { w: 7, head: 22, curve: [2330, 520] }), 0, 2.6, { min: .2, max: .35 });
  // spine and branches
  const COLS = [TX - 980, TX + 120], ROWS = [640, 1010], BW = 860, BH = 280;
  D(K, [W.line(TX, 450, TX, 1150, { w: 9 }), W.line(TX, 780, TX - 120, 780, { w: 9 }), W.line(TX, 780, TX + 120, 780, { w: 9 }),
    W.line(TX, 1150, TX - 120, 1150, { w: 9 }), W.line(TX, 1150, TX + 120, 1150, { w: 9 })], 0, tCam - .05, { min: .35, max: .7 });
  // the four boxes, in narration order: camouflage, signal, sonic, engineers
  const icon = {
    eye: (x, y) => [W.curve([[x - 75, y], [x, y - 52], [x + 75, y]], { w: 8 }), W.curve([[x - 75, y], [x, y + 52], [x + 75, y]], { w: 8 }), W.circle(x, y, 24, { w: 7 }), W.line(x - 2, y, x + 2, y + 1, { w: 14 })],
    mast: (x, y) => [W.line(x - 40, y + 80, x, y - 70, { w: 8, bow: 0 }), W.line(x + 40, y + 80, x, y - 70, { w: 8, bow: 0 }), W.line(x - 25, y + 25, x + 22, y - 15, { w: 6, bow: 0 }),
      W.arc(x, y - 70, 45, -Math.PI * .85, -Math.PI * .6, { w: 7 }), W.arc(x, y - 70, 45, -Math.PI * .4, -Math.PI * .15, { w: 7 })],
    horn: (x, y) => [W.poly([[x - 70, y - 12], [x - 70, y + 12], [x + 30, y + 50], [x + 30, y - 50], [x - 70, y - 12]], { w: 8 }),
      W.arc(x + 45, y, 55, -Math.PI * .3, Math.PI * .3, { w: 7 }), W.arc(x + 45, y, 90, -Math.PI * .25, Math.PI * .25, { w: 7 })],
    fence: (x, y) => [...[-70, 0, 70].map(dx => W.line(x + dx, y - 70, x + dx, y + 70, { w: 8, bow: 0 })),
      W.curve([[x - 95, y - 30], [x, y - 20], [x + 95, y - 32]], { w: 6 }), W.curve([[x - 95, y + 25], [x, y + 35], [x + 95, y + 22]], { w: 6 })],
  };
  const UNITS = [
    { c: 0, r: 0, a: '603rd', b: 'Camouflage', role: 'visual deception', ic: 'eye', t: tCam, n: tSig },
    { c: 1, r: 0, a: 'Signal Co.', b: 'Special', role: 'radio', ic: 'mast', t: tSig, n: tSon },
    { c: 0, r: 1, a: '3132nd', b: 'sonic company', role: 'sound', ic: 'horn', t: tSon, n: tEng },
    { c: 1, r: 1, a: '406th', b: 'Engineers', role: 'perimeter + staging', ic: 'fence', t: tEng, n: tPer },
  ];
  for (const u of UNITS) {
    const x0 = COLS[u.c], y0 = ROWS[u.r], span = u.n - u.t;
    D(K, W.rect(x0, y0, BW, BH, { w: 9, over: 7 }), u.t - .25, u.t + span * .2, { min: .3, max: .55 });
    D(K, [...T(u.a, x0 + 40, y0 + 85, { h: 58, w: 8 }), ...T(u.b, x0 + 40, y0 + 165, { h: 50, w: 7 })], 0, u.t + span * .5, { min: .6, max: 2.2 });
    D(B, T(u.role, x0 + 40, y0 + 245, { h: 44, w: 6 }), u.t + span * .52, u.t + span * .85, { min: .45, max: 1.6 });
    D(B, icon[u.ic](x0 + BW - 130, y0 + 140), 0, u.t + span * .98, { min: .3, max: 1.0 });
  }
  // the engineers guard the perimeter: an orange dashed loop around the whole organisation
  const loop = [], R0 = 90, LX0 = TX - 1030, LX1 = TX + 1030, LY0 = 595, LY1 = 1335;   // rounded perimeter around the four boxes
  const corner = (cx, cy, a0) => { for (let i = 0; i <= 6; i++) { const a = a0 + i / 6 * Math.PI / 2; loop.push([cx + Math.cos(a) * R0, cy + Math.sin(a) * R0]); } };
  corner(LX1 - R0, LY0 + R0, -Math.PI / 2); corner(LX1 - R0, LY1 - R0, 0); corner(LX0 + R0, LY1 - R0, Math.PI / 2); corner(LX0 + R0, LY0 + R0, Math.PI); loop.push(loop[0]);
  D(O, W.dashed(loop, { w: 8, dash: 38, gap: 24 }), tPer - .1, Math.max(tIll, tPer + .9), { min: .7, max: 2.0 });
  D(O, T('stage the illusions', TX + 360, 1460, { h: 46, w: 7, align: 'center' }), tIll - .4, tIll + .9, { min: .6, max: 1.6 });
  // camera: header → each box as it is named → the whole organisation
  const end = d, keys = [[0, TX, 330, 1.3], [Math.max(.6, tCam - .9), TX, 470, 1.0, 0, 'io'],
    [tCam + .1, COLS[0] + BW / 2 + 120, 700, 1.05, 0, 'io'], [tSig, COLS[0] + BW / 2 + 160, 700, 1.05, 0, 'l'],
    [tSig + .6, COLS[1] + BW / 2 - 120, 700, 1.05, 0, 'io'], [tSon, COLS[1] + BW / 2 - 160, 705, 1.05, 0, 'l'],
    [tSon + .6, COLS[0] + BW / 2 + 120, 1130, 1.05, 0, 'io'], [tEng, COLS[0] + BW / 2 + 160, 1130, 1.05, 0, 'l'],
    [tEng + .6, COLS[1] + BW / 2 - 120, 1130, 1.05, 0, 'io'], [Math.max(tEng + .9, tPer - .3), COLS[1] + BW / 2 - 160, 1120, 1.04, 0, 'l'],
    [Math.min(end - .4, tPer + 1.1), TX, 830, .82, 0, 'io'], [end, TX, 830, .81, 0, 'l']];
  return finish(E, new W.Camera(keys), { W: 3000, H: 1700, seed: 808 });
}

// ═════════ g12 · four tools
function buildG12(scene) {
  const E = era(scene, N12), { D, T, K, B, O, C } = E, TX = 1500, GY = 1130;
  const at = C.at, d = C.d;
  const tFar = at('far'), tArt = at('artists'), tHow = at('how'), tFour = at('four'), tSee = at('see'), tHear = at('hear'),
    tRad = at('radio'), tThe = at('theater'), tUsed = at('used'), tSmall = at('small'), tLarge = at('large');
  // recap block (top): the unit's size as a field of dots, and who the men were
  D(K, T('about 1,100 men', 250, 250, { h: 80, w: 10 }), tFar, at('men') + .2, { min: .8, max: 2.0 });
  D(K, T('82 officers + 1,023 enlisted', 255, 335, { h: 44, w: 6 }), 0, at('many') + .2, { min: .6, max: 1.4 });
  const dots = []; for (let r = 0; r < 6; r++) for (let c = 0; c < 25; c++) dots.push(W.line(262 + c * 30, 400 + r * 28, 266 + c * 30, 401 + r * 28, { w: 12, jitter: 0 }));
  D(K, dots, 0, tArt + .4, { min: .5, max: 1.2, minGap: .003, maxGap: .01 });
  D(B, T('many of them artists', 1150, 250, { h: 66, w: 8 }), at('many') - .1, tArt + .4, { min: .8, max: 2.0 });
  D(B, T('art schools, ad agencies', 1155, 335, { h: 44, w: 6 }), 0, tHow - .1, { min: .5, max: 1.3 });
  const pal = [W.curve([[1250, 400], [1330, 375], [1440, 385], [1490, 420], [1460, 460], [1400, 450], [1380, 480], [1300, 482], [1240, 450], [1250, 400]], { w: 7, smooth: 2 }),
    ...[[1300, 420], [1350, 405], [1405, 412], [1440, 432]].map(([x, y]) => W.circle(x, y, 11, { w: 6 })),
    W.line(1520, 480, 1660, 380, { w: 8, bow: 0 }), W.curve([[1660, 380], [1690, 350], [1716, 360], [1692, 392], [1660, 380]], { w: 7 })];
  D(B, pal, 0, tHow + .1, { min: .4, max: 1.0 });
  D(O, T('how?', 2400, 470, { h: 150, w: 16, align: 'center' }), tHow, at('fool') + .3, { min: .6, max: 1.4 });
  D(O, W.curve([[2200, 515], [2400, 532], [2620, 508]], { w: 12, over: 14 }), 0, at('army') + .3, { min: .2, max: .4 });
  D(O, W.arrow(2300, 560, 1900, 690, { w: 9, head: 26, curve: [2200, 660] }), tFour - .5, tFour, { min: .25, max: .5 });
  D(K, T('four tools', TX, 720, { h: 92, w: 11, align: 'center' }), tFour - .6, tFour + .5, { min: .6, max: 1.4 });
  D(O, W.curve([[TX - 310, 752], [TX, 764], [TX + 310, 748]], { w: 11, over: 14 }), tFour + .55, tFour + .9, { min: .2, max: .35 });
  const XS = [TX - 930, TX - 310, TX + 310, TX + 930];
  // 1 · things you could see — an inflatable Sherman-like decoy
  const sherman = (x, g) => [
    W.poly([[x - 250, g - 52], [x - 225, g - 82], [x + 215, g - 92], [x + 258, g - 58], [x + 205, g], [x - 205, g], [x - 250, g - 52]], { w: 9, jitter: .7 }),  // track run
    ...[-175, -120, -30, 25, 115, 170].map(dx => W.circle(x + dx, g - 30, 25, { w: 6 })),                                                       // bogie wheels
    ...[-148, -3, 143].map(dx => W.arc(x + dx, g - 30, 46, Math.PI * 1.15, Math.PI * 1.85, { w: 6 })),                                        // three bogie units
    W.poly([[x - 245, g - 84], [x - 235, g - 150], [x + 80, g - 152], [x + 252, g - 92]], { w: 9 }),                                           // hull + sloped glacis
    W.curve([[x - 135, g - 150], [x - 122, g - 208], [x - 60, g - 238], [x + 40, g - 236], [x + 92, g - 205], [x + 100, g - 150]], { w: 9 }),   // cast turret
    W.arc(x - 52, g - 236, 24, Math.PI, TAU0, { w: 6 }),                                                                                       // cupola
    W.line(x + 95, g - 205, x + 300, g - 211, { w: 8, bow: 0 }), W.line(x + 95, g - 186, x + 300, g - 191, { w: 8, bow: 0 }),               // gun
  ];
  D(K, sherman(XS[0], GY), tFour + .1, tSee + .5, { min: 1.0, max: 3.5 });
  D(O, [W.circle(XS[0] - 205, GY - 118, 13, { w: 6 }), ...W.arrow(XS[0] - 300, GY - 230, XS[0] - 214, GY - 132, { w: 6, head: 18, curve: [XS[0] - 290, GY - 160] })], tSee - .1, tSee + .5, { min: .3, max: .7 });
  D(O, T('inflatable', XS[0] - 140, GY - 300, { h: 44, w: 6, align: 'center' }), 0, tSee + 1.0, { min: .4, max: .9 });
  // 2 · things you could hear — a half-track carrying a loudspeaker horn
  const horn = (x, y, a, L = 130) => {
    const c = Math.cos(a), s = Math.sin(a), nx = -s, ny = c, P = (u, w) => [x + c * u + nx * w, y + s * u + ny * w];
    return [W.poly([P(0, -12), P(0, 12), P(L, 58), P(L, -58), P(0, -12)], { w: 8 }), W.line(...P(L, -58), ...P(L + 14, 0), { w: 6, bow: 0 }), W.line(...P(L + 14, 0), ...P(L, 58), { w: 6, bow: 0 })];
  };
  const HA = -Math.PI * .75;
  const halftrack = (x, g) => [
    W.roundRect(x - 245, g - 70, 285, 70, 35, { w: 9 }), ...[-200, -105, -10].map(dx => W.circle(x + dx, g - 35, 21, { w: 6 })),           // rear tracks
    W.circle(x + 185, g - 38, 38, { w: 8 }),                                                                                                 // front wheel
    W.poly([[x - 245, g - 70], [x - 245, g - 150], [x + 60, g - 150], [x + 60, g - 70]], { w: 9 }),                                         // armoured bed
    W.poly([[x + 60, g - 70], [x + 60, g - 175], [x + 120, g - 175], [x + 150, g - 125], [x + 245, g - 115], [x + 245, g - 70]], { w: 9 }),  // cab + hood
    W.line(x - 100, g - 150, x - 100, g - 240, { w: 9, bow: 0 }), ...horn(x - 100, g - 240, HA),                                           // mast + horn
  ];
  D(K, halftrack(XS[1], GY), tSee + .5, tHear + .4, { min: .9, max: 3.0 });
  const hc = [XS[1] - 100 + Math.cos(HA) * 150, GY - 240 + Math.sin(HA) * 150];
  [0, 1, 2].forEach(k => D(B, W.arc(hc[0], hc[1], 40 + k * 38, HA - .55, HA + .55, { w: 7 }), tHear + k * .12, tHear + .12 + k * .12, { min: .12, max: .3 }));
  // 3 · radio traffic — a lattice mast and Morse dots and dashes
  const mx = XS[2] - 90;
  const mast = [W.line(mx - 80, GY, mx, GY - 320, { w: 9, bow: 0 }), W.line(mx + 80, GY, mx, GY - 320, { w: 9, bow: 0 }), W.line(mx - 130, GY, mx + 130, GY, { w: 9 }),
    ...[0, 1, 2, 3, 4].map(k => { const y = GY - 30 - k * 60, hw = 72 - k * 14; return W.line(mx - hw, y, mx + hw - 14, y - 50, { w: 6, bow: 0 }); })];
  D(K, mast, tHear + .45, tRad + .2, { min: .7, max: 2.4 });
  D(B, [0, 1].flatMap(k => [W.arc(mx, GY - 320, 60 + k * 55, -Math.PI * .85, -Math.PI * .6, { w: 7 }), W.arc(mx, GY - 320, 60 + k * 55, -Math.PI * .4, -Math.PI * .15, { w: 7 })]), tRad - .1, tRad + .3, { min: .25, max: .6 });
  const morse = []; let qx = mx + 120; const qy = GY - 200;
  for (const ch of '.-..-') { if (ch === '.') { morse.push(W.line(qx, qy, qx + 4, qy + 1, { w: 16 })); qx += 42; } else { morse.push(W.line(qx, qy, qx + 62, qy, { w: 12, bow: 0 })); qx += 92; } }
  D(B, morse, tRad + .3, tRad + .8, { min: .4, max: 1.0 });
  // 4 · a kind of theater — a shoulder patch and a phony HQ sign
  const px = XS[3] - 130, patch = [
    W.curve([[px - 95, GY - 250], [px - 95, GY - 120], [px, GY - 40], [px + 95, GY - 120], [px + 95, GY - 250], [px - 95, GY - 250]], { w: 9, smooth: 1 }),
    W.curve([[px - 100, GY - 268], [px, GY - 310], [px + 100, GY - 268]], { w: 8 }), W.line(px - 100, GY - 268, px - 95, GY - 250, { w: 7, bow: 0 }), W.line(px + 100, GY - 268, px + 95, GY - 250, { w: 7, bow: 0 })];
  const sx = XS[3] + 150, sign = [W.line(sx, GY, sx, GY - 170, { w: 10, bow: 0 }), ...W.rect(sx - 120, GY - 300, 240, 130, { w: 9, over: 5 }), ...T('HQ', sx, GY - 205, { h: 70, w: 10, align: 'center' })];
  D(K, [...patch, ...sign], tRad + .5, tThe + .4, { min: .8, max: 2.6 });
  const star = []; for (let k = 0; k <= 5; k++) { const a = -Math.PI / 2 + k * 4 * Math.PI / 5; star.push([px + Math.cos(a) * 42, GY - 150 + Math.sin(a) * 42]); }
  D(O, W.poly(star, { w: 7 }), tThe + .1, tThe + .45, { min: .25, max: .5 });
  // labels under each tool (narration wording), then what each tool was
  const LAB = [['things you see', 'rubber decoys', tSee], ['things you hear', 'recorded sound', tHear], ['radio traffic', 'phony networks', tRad], ['theater', '"special effects"', tThe]];
  LAB.forEach(([a, b, t0], i) => {
    D(B, T(a, XS[i], GY + 110, { h: 52, w: 7, align: 'center' }), t0 + .05, t0 + .8, { min: .45, max: 1.1 });
    D(B, T(b, XS[i], GY + 180, { h: 44, w: 6, align: 'center' }), 0, t0 + 1.5, { min: .45, max: 1.2 });
  });
  // used together: a small force made to look and sound large
  const glyph = (x, y, s = 1, o = {}) => [W.roundRect(x - 34 * s, y - 14 * s, 68 * s, 28 * s, 12 * s, { w: 6, ...o }), W.line(x + 4 * s, y - 20 * s, x + 46 * s, y - 22 * s, { w: 6, bow: 0, ...o })];
  const smallF = [[460, 1520], [580, 1520], [520, 1585]].flatMap(([x, y]) => glyph(x, y, 1.3));
  const bigF = []; for (let r = 0; r < 3; r++) for (let c = 0; c < 7; c++) bigF.push(...glyph(1640 + c * 155 + (r % 2) * 60, 1490 + r * 62, 1.15, { alpha: .85 }));
  D(K, smallF, tUsed - .2, tSmall + .2, { min: .4, max: 1.0 });
  D(K, T('small force', 520, 1720, { h: 52, w: 7, align: 'center' }), tSmall, tSmall + .7, { min: .4, max: 1.0 });
  D(O, W.arrow(780, 1560, 1500, 1560, { w: 11, head: 36, over: 0 }), at('look') - .2, at('sound', 0) + .1, { min: .3, max: .8 });
  D(B, bigF, at('look'), tLarge + .3, { min: .8, max: 2.2 });
  D(B, T('looks + sounds large', 2140, 1720, { h: 52, w: 7, align: 'center' }), tLarge - .2, tLarge + .8, { min: .5, max: 1.2 });
  // camera: recap → question → four tools tracked one by one → the tools and the conclusion
  const end = d, keys = [[0, 800, 380, 1.45], [Math.max(.5, tArt - .3), 1250, 400, 1.3, 0, 'io'], [tHow - .2, 1900, 460, 1.18, 0, 'io'],
    [tFour - .7, TX, 760, 1.0, 0, 'io'], [tFour + .3, XS[0] + 120, 1000, 1.08, 0, 'io'], [tSee + .5, XS[0] + 160, 1010, 1.08, 0, 'l'],
    [tSee + 1.0, XS[1] + 40, 1000, 1.08, 0, 'io'], [tHear + .5, XS[1] + 80, 1010, 1.08, 0, 'l'],
    [tHear + 1.0, XS[2] + 40, 1000, 1.08, 0, 'io'], [tRad + .6, XS[2] + 80, 1010, 1.08, 0, 'l'],
    [tRad + 1.1, XS[3] - 40, 1000, 1.08, 0, 'io'], [Math.max(tRad + 1.2, tUsed - .6), XS[3] - 20, 1010, 1.07, 0, 'l'],
    [Math.min(end - .3, tUsed + .9), TX, 1235, .78, 0, 'io'], [end, TX, 1235, .775, 0, 'l']];
  return finish(E, new W.Camera(keys), { W: 3000, H: 2100, seed: 1212 });
}
const TAU0 = Math.PI * 2;

// ───────── the film: eras on one clock
export async function build() {
  await W.loadFont('tech', '/styles/whiteboard/demo/fonts/EMSTech.json');
  const TM = timing(), BUILD = { g08: buildG08, g12: buildG12 };
  const eras = TM.scenes.filter(s => BUILD[s.id]).map(s => ({ s, E: BUILD[s.id](s) }));
  const find = t => eras.find(e => t >= e.s.start && t < e.s.end) || eras[eras.length - 1];
  const render = (ctx, t) => { const e = find(t); ctx.setTransform(1, 0, 0, 1, 0, 0); e.E.render(ctx, Math.max(0, t - e.s.start)); };
  const ev = eras.flatMap(e => e.E.ev.map(x => ({ ...x, t: +(x.t + e.s.start).toFixed(3), scene: e.s.id })));
  const minText = t => { const e = find(t); return { scene: e.s.id, ...e.E.minText(Math.max(0, t - e.s.start)) }; };
  return { dur: TM.dur, render, ev, subs: [], minText, scenes: TM.scenes };
}
