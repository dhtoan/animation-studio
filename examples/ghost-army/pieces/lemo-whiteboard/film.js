// Ghost Army — g08 (the 23rd's four components), g12 (the four tools), g30 (Congress quotes the Army),
// g36 (displaced-persons camps), g42 (the medal's four tools), g43 (where the story lives on), drawn live with the
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
  E.clipped = t => {                // labels cut by the frame edge, and whether the camera is holding
    const c = cam.at(t), p = cam.at(Math.max(0, t - 1 / 30)), out = [];
    const held = Math.hypot((c.x - p.x) * c.z, (c.y - p.y) * c.z) + Math.abs(Math.log(c.z / p.z)) * 900 < 2;
    for (const x of E.texts) {
      if (Math.min(...x.strokes.map(k => k.t0)) > t) continue;
      const [ax, ay] = W.toScreen(c, x.x0, x.y - x.h * 1.15), [bx, by] = W.toScreen(c, x.x1, x.y + x.h * .35);
      const inter = bx > 0 && ax < 1920 && by > 0 && ay < 1080, inside = ax >= 0 && bx <= 1920 && ay >= 0 && by <= 1080;
      if (inter && !inside) out.push(x.str);
    }
    return { held, clipped: out };
  };
  E.cam = cam; E.ev = E.tl.ev;
  return E;
}
// camera as a list of shots: each shot is reached in `mv` seconds and then held until the next one moves
function shots(list, mv = .7) {
  const keys = [[0, ...list[0].slice(1), 0, 'l']];
  for (let i = 1; i < list.length; i++) {
    const [t, x, y, z] = list[i], [, px, py, pz] = list[i - 1], prev = keys[keys.length - 1][0];
    const t0 = Math.max(prev + .05, t - mv);
    keys.push([t0, px, py, pz, 0, 'l'], [Math.max(t, t0 + .1), x, y, z, 0, 'io']);
  }
  return keys;
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
  D(O, T('"Ghost Army"', 710, 300, { h: 46, w: 7, align: 'center' }), 1.3, 2.3, { min: .5 });
  D(O, W.curve([[510, 325], [710, 334], [910, 320]], { w: 9, over: 10 }), 0, 2.6, { min: .2, max: .35 });
  D(B, [...T('specialized', 2310, 285, { h: 44, w: 6, align: 'center' }), ...T('parts', 2310, 345, { h: 44, w: 6, align: 'center' })], 1.3, 2.4, { min: .6 });
  D(B, W.arrow(2310, 370, 2150, 600, { w: 7, head: 22, curve: [2290, 520] }), 0, 2.8, { min: .2, max: .35 });
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
  // header up close → row 1 held (header + two boxes) → row 2 held → the whole organisation
  const end = d, keys = shots([[0, TX, 330, 1.3], [1.2, TX, 520, .94], [Math.max(tSig + .6, tSon - .3), TX, 1126, .94],
    [Math.max(tEng + .8, Math.min(end - .4, tPer + 1.1)), TX, 830, .82]]);
  return finish(E, new W.Camera(keys), { W: 3000, H: 1700, seed: 808 });
}

// ═════════ g12 · four tools
function buildG12(scene) {
  const E = era(scene, N12), { D, T, K, B, O, C } = E, TX = 1500, GY = 1130;
  const at = C.at, d = C.d;
  const tFar = at('far'), tArt = at('artists'), tHow = at('how'), tFour = at('four'), tSee = at('see'), tHear = at('hear'),
    tRad = at('radio'), tThe = at('theater'), tUsed = at('used'), tSmall = at('small'), tLarge = at('large');
  // recap block (top): the unit's size as a field of dots, and who the men were
  D(K, T('about 1,100 men', 250, 250, { h: 80, w: 10 }), Math.min(tFar, .15), at('men') + .2, { min: .8, max: 2.0 });
  D(K, T('82 officers + 1,023 enlisted', 255, 335, { h: 44, w: 6 }), 0, at('many') + .2, { min: .6, max: 1.4 });
  const dots = []; for (let r = 0; r < 6; r++) for (let c = 0; c < 25; c++) dots.push(W.line(262 + c * 30, 400 + r * 28, 266 + c * 30, 401 + r * 28, { w: 12, jitter: 0 }));
  D(K, dots, 0, tArt + .4, { min: .5, max: 1.2, minGap: .003, maxGap: .01 });
  D(B, T('many of them artists', 1150, 250, { h: 66, w: 8 }), at('many') - .1, tArt + .4, { min: .8, max: 2.0 });
  D(B, T('art schools, ad agencies', 1155, 335, { h: 44, w: 6 }), 0, tHow - .1, { min: .5, max: 1.3 });
  const pal = [W.curve([[1250, 400], [1330, 375], [1440, 385], [1490, 420], [1460, 460], [1400, 450], [1380, 480], [1300, 482], [1240, 450], [1250, 400]], { w: 7, smooth: 2 }),
    ...[[1300, 420], [1350, 405], [1405, 412], [1440, 432]].map(([x, y]) => W.circle(x, y, 11, { w: 6 })),
    W.line(1520, 480, 1660, 380, { w: 8, bow: 0 }), W.curve([[1660, 380], [1690, 350], [1716, 360], [1692, 392], [1660, 380]], { w: 7 })];
  D(B, pal, 0, tHow + .1, { min: .4, max: 1.0 });
  D(O, T('how?', 2330, 470, { h: 150, w: 16, align: 'center' }), tHow, at('fool') + .3, { min: .6, max: 1.4 });
  D(O, W.curve([[2130, 515], [2330, 532], [2550, 508]], { w: 12, over: 14 }), 0, at('army') + .3, { min: .2, max: .4 });
  D(O, W.arrow(2240, 560, 1000, 660, { w: 9, head: 26, curve: [1700, 690] }), tFour - .5, tFour, { min: .25, max: .5 });
  D(K, T('four tools', 300, 700, { h: 84, w: 10 }), tFour - .6, tFour + .5, { min: .6, max: 1.4 });
  D(O, W.curve([[295, 730], [610, 742], [930, 726]], { w: 11, over: 14 }), tFour + .55, tFour + .9, { min: .2, max: .35 });
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
  // recap held → recap + question → tools 1-2 held → tools 3-4 held → tools and conclusion
  const end = d, keys = shots([[0, 1195, 568, .95], [tHow - .2, 1440, 675, .8], [tFour + .2, 772, 965, 1.3],
    [Math.max(tFour + .9, tRad - .4), 2248, 965, 1.3], [Math.max(tRad + .5, Math.min(end - .3, tUsed + .9)), TX, 1235, .775]]);
  return finish(E, new W.Camera(keys), { W: 3000, H: 2100, seed: 1212 });
}
// ═════════ g30 · Congress quotes a postwar Army assessment (C34: exact opening words only)
const N30 = 'Congress later quoted a postwar Army assessment praising how much influence such a small group had on a major operation.';
function buildG30(scene) {
  const E = era(scene, N30), { D, T, K, B, O, C } = E, at = C.at, d = C.d;
  const tQuo = at('quoted'), tPost = at('postwar'), tPra = at('praising'), tSmall = at('small'), tMaj = at('major');
  // the sketched document: page, folded corner, header, lines of (unreadable) text
  const page = [W.poly([[300, 180], [1460, 180], [1600, 320], [1600, 1420], [300, 1420], [300, 180]], { w: 10 }),
    W.poly([[1460, 180], [1460, 320], [1600, 320]], { w: 7 })];
  D(K, page, .1, Math.min(.9, tQuo - .3), { min: .5, max: .9 });
  D(K, T('Public Law 117-85', 380, 320, { h: 64, w: 9 }), 0, tQuo + .2, { min: .7, max: 1.5 });
  D(K, T('findings', 382, 410, { h: 50, w: 7 }), 0, tPost, { min: .35, max: .7 });
  const scrib = [];
  for (const y of [500, 560, 620, 1180, 1240, 1300]) { const p = []; for (let x = 380; x <= 1520; x += 20) p.push([x, y + Math.sin(x / 23 + y) * 7]); scrib.push(W.curve(p, { w: 5, alpha: .45, jitter: .6 })); }
  D(B, scrib, .5, tPra - .2, { min: .6, max: 1.6, minGap: .01, maxGap: .03 });
  // the margin note: who quoted whom
  D(B, [...T('Congress quoted', 1750, 420, { h: 54, w: 7 }), ...T('a postwar Army', 1750, 500, { h: 46, w: 6 }), ...T('assessment', 1750, 570, { h: 46, w: 6 })], tQuo - .2, tPra - .1, { min: 1.0, max: 2.2 });
  D(B, W.arrow(1740, 600, 1560, 760, { w: 7, head: 22, curve: [1640, 640] }), 0, tPra, { min: .2, max: .4 });
  // the quoted opening words, with an orange highlighter behind them
  const Q = ['"Rarely, if ever, has there', 'been a group of such a', 'few men ..."'], qy = [800, 900, 1000], span = tSmall - tPra + .6;
  Q.forEach((s, i) => {
    const hl = W.line(395, qy[i] - 22, 395 + Math.min(1120, s.length * 41), qy[i] - 24, { w: 62, alpha: .28, jitter: .3, bow: .002 });
    D(O, hl, tPra + i * span / 3 - .1, tPra + (i + .6) * span / 3, { min: .25, max: .7 });
    D(K, T(s, 400, qy[i], { h: 58, w: 8 }), tPra + i * span / 3, tPra + (i + 1) * span / 3, { min: .5, max: 1.6 });
  });
  D(O, T('paraphrase:', 1750, 820, { h: 44, w: 6 }), tSmall, tSmall + .5, { min: .3, max: .7 });
  D(B, [...T('outsized influence', 1750, 900, { h: 46, w: 6 }), ...T('on a major campaign', 1750, 970, { h: 46, w: 6 })], tSmall + .4, tMaj + .6, { min: .8, max: 1.8 });
  // the page's header up close, then the whole sheet with its margin notes (held)
  const keys = shots([[0, 760, 470, 1.25], [Math.max(1.0, tQuo - .3), 1355, 800, .87], [Math.max(tQuo + .4, tPra - .2), 1355, 810, .88]]);
  return finish(E, new W.Camera(keys), { W: 2700, H: 1650, seed: 3030 });
}

// ═════════ g36 · displaced-persons camps (C55; the number framed as the unit history's)
const N36 = 'There was one more chapter. After Germany surrendered, the 23rd helped run camps for displaced persons. The unit\'s history cites up to about one hundred thousand people in thirteen camps.';
function buildG36(scene) {
  const E = era(scene, N36), { D, T, K, B, O, C } = E, at = C.at, d = C.d, TX = 1350;
  const tOne = at('one'), tSur = at('surrendered'), tHelp = at('helped'), tDisp = at('displaced'), tHist = at('history'), tHun = at('hundred'), tThir = at('thirteen');
  D(K, T('one more chapter', TX, 300, { h: 90, w: 11, align: 'center' }), .1, tOne + .9, { min: .8, max: 1.4 });
  D(O, W.curve([[TX - 420, 335], [TX, 348], [TX + 420, 330]], { w: 11, over: 12 }), 0, tOne + 1.2, { min: .2, max: .35 });
  D(K, T('after Germany surrendered,', TX, 430, { h: 66, w: 9, align: 'center' }), tSur - .9, tSur + .4, { min: .8, max: 1.6 });
  D(B, T('the 23rd helped run camps for displaced persons', TX, 530, { h: 54, w: 7, align: 'center' }), tHelp - .3, tDisp + .6, { min: 1.0, max: 2.4 });
  // thirteen tents as simple symbols, two rows
  const tent = (x, y) => [W.poly([[x - 70, y], [x, y - 95], [x + 70, y], [x - 70, y]], { w: 7 }), W.line(x, y - 95, x, y, { w: 5, bow: 0 }), W.line(x - 92, y + 3, x + 92, y + 3, { w: 5 })];
  const TP = []; for (let i = 0; i < 7; i++) TP.push([360 + i * 330, 740]); for (let i = 0; i < 6; i++) TP.push([525 + i * 330, 900]);
  D(K, TP.flatMap(([x, y]) => tent(x, y)), tDisp - .2, tHist + .3, { min: 1.2, max: 3.0, minGap: .01, maxGap: .04 });
  // people as simple symbols (head + shoulders), a calm band under the tents
  const person = (x, y) => [W.circle(x, y - 34, 11, { w: 5 }), W.arc(x, y + 6, 24, Math.PI * 1.05, Math.PI * 1.95, { w: 5 })];
  const PP = []; for (let i = 0; i < 26; i++) PP.push([330 + i * 82 + (i % 2) * 20, 1030 + (i % 3) * 18]);
  D(B, PP.flatMap(([x, y]) => person(x, y)), tHist - .2, tHun + .6, { min: .9, max: 2.4, minGap: .005, maxGap: .02 });
  D(B, T("the unit's history cites:", TX, 1170, { h: 50, w: 7, align: 'center' }), tHist - .3, tHist + .7, { min: .5, max: 1.2 });
  D(K, T('up to about 100,000 people', TX, 1285, { h: 76, w: 10, align: 'center' }), tHun - .5, at('people') + .4, { min: .8, max: 1.6 });
  const s13 = W.text('in 13 camps', TX, 1395, { h: 76, w: 10, align: 'center' });   // to place the circle on "13"
  D(K, T('in 13 camps', TX, 1395, { h: 76, w: 10, align: 'center' }), tThir - .3, tThir + .6, { min: .5, max: 1.0 });
  D(O, W.circle(s13.x0 + s13.width * .36, 1367, 78, { w: 8, ry: 62, a0: -2.4 }), tThir + .45, tThir + .9, { min: .25, max: .4 });
  const keys = shots([[0, TX, 470, 1.18], [Math.max(.8, tHelp - .4), TX, 560, 1.0], [Math.max(tHelp + .3, tDisp + .1), TX, 760, .86],
    [Math.max(tDisp + .8, tHist - .2), TX, 1100, 1.0], [Math.max(tHist + .5, Math.min(d - .5, tThir + .7)), TX, 850, .8]]);
  return finish(E, new W.Camera(keys), { W: 2700, H: 1650, seed: 3636 });
}

// ═════════ g42 · the medal's four tools, our own sketch (C53), and the Army Secretary's remark (C51)
const N42 = 'The medal\'s design shows the four tools: a telegraph operator, a soldier applying a fake unit patch, a loudspeaker half-track, and soldiers carrying an inflatable tank. At the ceremony, the Secretary of the Army said many of the unit\'s techniques are still used today.';
function buildG42(scene) {
  const E = era(scene, N42), { D, T, K, B, O, C } = E, at = C.at, d = C.d;
  const tFour = at('four'), tTel = at('telegraph'), tPat = at('patch'), tLou = at('loudspeaker'), tInf = at('inflatable'), tCer = at('ceremony'),
    tSec = at('secretary'), tTech = at('techniques'), tTod = at('today');
  const MX = 1100, MY = 1010, MR = 430;
  D(K, [W.circle(MX, MY, MR, { w: 11, lap: .05 }), W.circle(MX, MY, MR - 34, { w: 6, lap: .05 })], .1, Math.min(1.6, tFour - .2), { min: .9, max: 1.6 });
  D(K, [W.line(MX - MR + 38, MY, MX + MR - 38, MY, { w: 7 }), W.line(MX, MY - MR + 38, MX, MY + MR - 38, { w: 7 })], 0, tFour + .4, { min: .3, max: .6 });
  D(O, T('four tools', MX, 445, { h: 66, w: 9, align: 'center' }), tFour - .3, tFour + .6, { min: .5, max: 1.0 });
  const pp = (x, y, s = 1) => [W.circle(x, y - 46 * s, 16 * s, { w: 6 }), W.arc(x, y + 8 * s, 34 * s, Math.PI * 1.05, Math.PI * 1.95, { w: 6 })];
  // TL · telegraph operator: a person at a key, with dots and dashes
  const tq = [MX - 240, MY - 190];
  const tele = [...pp(tq[0] - 90, tq[1] + 60), W.roundRect(tq[0] - 20, tq[1] + 50, 200, 40, 10, { w: 7 }), W.line(tq[0] + 20, tq[1] + 50, tq[0] + 140, tq[1] + 22, { w: 7, bow: 0 }),
    W.circle(tq[0] + 140, tq[1] + 20, 13, { w: 6 }), W.line(tq[0] - 70, tq[1] + 40, tq[0] + 128, tq[1] + 22, { w: 6, bow: .01 })];
  D(K, tele, tTel - .4, tPat - .9, { min: .8, max: 2.0 });
  D(B, [W.line(tq[0] - 20, tq[1] - 60, tq[0] - 16, tq[1] - 59, { w: 13 }), W.line(tq[0] + 20, tq[1] - 60, tq[0] + 70, tq[1] - 60, { w: 10, bow: 0 }), W.line(tq[0] + 100, tq[1] - 60, tq[0] + 104, tq[1] - 59, { w: 13 })], tTel + .3, tPat - .6, { min: .25, max: .5 });
  // TR · a soldier applying a fake unit patch: a shoulder and sleeve, the patch going on
  const sq = [MX + 210, MY - 200];
  const sleeve = [W.curve([[sq[0] - 150, sq[1] - 50], [sq[0] - 40, sq[1] - 100], [sq[0] + 70, sq[1] - 80], [sq[0] + 140, sq[1] - 15]], { w: 8 }),
    W.line(sq[0] - 150, sq[1] - 50, sq[0] - 125, sq[1] + 130, { w: 8, bow: .02 }), W.line(sq[0] + 140, sq[1] - 15, sq[0] + 115, sq[1] + 130, { w: 8, bow: .02 })];
  const fpatch = [W.curve([[sq[0] - 50, sq[1] - 15], [sq[0] - 50, sq[1] + 50], [sq[0], sq[1] + 92], [sq[0] + 50, sq[1] + 50], [sq[0] + 50, sq[1] - 15], [sq[0] - 50, sq[1] - 15]], { w: 7, smooth: 1 })];
  D(K, sleeve, tPat - .8, tPat - .1, { min: .5, max: 1.0 });
  D(O, [...fpatch, ...W.arrow(sq[0] + 140, sq[1] + 150, sq[0] + 60, sq[1] + 60, { w: 6, head: 18 })], tPat - .1, tPat + .5, { min: .4, max: .8 });
  // BL · a loudspeaker half-track
  const lq = [MX - 200, MY + 250];
  const ht = [W.roundRect(lq[0] - 170, lq[1] - 50, 200, 50, 25, { w: 7 }), W.circle(lq[0] + 130, lq[1] - 27, 27, { w: 6 }),
    W.poly([[lq[0] - 170, lq[1] - 50], [lq[0] - 170, lq[1] - 105], [lq[0] + 40, lq[1] - 105], [lq[0] + 40, lq[1] - 50]], { w: 7 }),
    W.poly([[lq[0] + 40, lq[1] - 50], [lq[0] + 40, lq[1] - 122], [lq[0] + 85, lq[1] - 122], [lq[0] + 105, lq[1] - 88], [lq[0] + 170, lq[1] - 80], [lq[0] + 170, lq[1] - 50]], { w: 7 }),
    W.line(lq[0] - 70, lq[1] - 105, lq[0] - 70, lq[1] - 165, { w: 7, bow: 0 }),
    W.poly([[lq[0] - 70, lq[1] - 175], [lq[0] - 70, lq[1] - 155], [lq[0] - 170, lq[1] - 210], [lq[0] - 150, lq[1] - 250], [lq[0] - 70, lq[1] - 175]], { w: 6 })];
  D(K, ht, tLou - .5, tInf - .7, { min: .8, max: 1.8 });
  D(B, [0, 1].map(k => W.arc(lq[0] - 175, lq[1] - 235, 30 + k * 30, Math.PI * .9, Math.PI * 1.5, { w: 6 })), tLou + .3, tInf - .4, { min: .2, max: .4 });
  // BR · soldiers carrying an inflatable tank
  const iq = [MX + 200, MY + 240];
  const tank = [W.roundRect(iq[0] - 150, iq[1] - 150, 300, 55, 27, { w: 7 }), W.poly([[iq[0] - 140, iq[1] - 150], [iq[0] - 120, iq[1] - 195], [iq[0] + 120, iq[1] - 195], [iq[0] + 150, iq[1] - 150]], { w: 7 }),
    W.arc(iq[0] - 10, iq[1] - 195, 55, Math.PI, TAU0, { w: 7 }), W.line(iq[0] + 40, iq[1] - 222, iq[0] + 180, iq[1] - 230, { w: 6, bow: 0 })];
  const carriers = [-110, 0, 110].flatMap(dx => [...pp(iq[0] + dx, iq[1] + 30, .85), W.line(iq[0] + dx, iq[1] - 30, iq[0] + dx, iq[1] - 92, { w: 5, bow: 0 })]);
  D(K, [...carriers, ...tank], tInf - .5, tCer - .2, { min: .9, max: 2.0 });
  // labels outside the medal, and the disclaimer
  const LB = [['telegraph operator', MX - 320, 530, tTel], ['fake unit patch', MX + 320, 530, tPat], ['loudspeaker half-track', MX - 330, 1530, tLou], ['inflatable tank', MX + 340, 1530, tInf]];
  LB.forEach(([s, x, y, t0]) => D(B, T(s, x, y, { h: 42, w: 6, align: 'center' }), t0 + .1, t0 + .8, { min: .45, max: 1.0 }));
  D(O, T('sketch, not the actual medal design', MX, 1625, { h: 44, w: 6, align: 'center' }), tCer - .4, tCer + .6, { min: .6, max: 1.2 });
  // the Army Secretary's remark at the ceremony (reported speech)
  D(K, [...T('at the ceremony,', 1700, 800, { h: 52, w: 7 }), ...T('the Secretary of the Army:', 1700, 880, { h: 52, w: 7 })], tCer, tSec + 1.0, { min: 1.0, max: 2.0 });
  D(B, [...T("many of the unit's", 1700, 1020, { h: 64, w: 9 }), ...T('techniques are', 1700, 1110, { h: 64, w: 9 }), ...T('still used today', 1700, 1200, { h: 64, w: 9 })], tTech - .7, tTod + .3, { min: 1.2, max: 2.6 });
  D(O, W.curve([[1695, 1230], [1950, 1240], [2220, 1226]], { w: 10, over: 12 }), tTod, tTod + .6, { min: .2, max: .35 });
  // the medal held while its quadrants fill, a slow push toward each; the remark; the whole board
  const keys = shots([[0, MX, 1011, 1.0], [tTel - .3, MX - 40, 1011, 1.0], [tPat - .3, MX + 40, 1011, 1.0], [tLou - .3, MX - 40, 1011, 1.0],
    [tInf - .3, MX + 40, 1011, 1.0], [tCer - .2, 1610, 1010, .82], [Math.max(tCer + .6, Math.min(d - .5, tTod + .5)), 1610, 1010, .8]]);
  return finish(E, new W.Camera(keys), { W: 3000, H: 2000, seed: 4242 });
}

// ═════════ g43 · where the story lives on (C48, C60, C58, C59)
const N43 = 'The law directs that the gold medal go to the Smithsonian Institution for display and research. The National World War Two Museum opened an exhibition about the unit in twenty twenty, and filmmaker Rick Beyer\'s twenty thirteen documentary, which aired on PBS, brought the story to a wide audience. In Luxembourg, there is a Ghost Army marker at Bettembourg, and a monument was unveiled in Limpertsberg in twenty twenty-three, where the unit had once been based.';
function buildG43(scene) {
  const E = era(scene, N43), { D, T, K, B, O, C } = E, at = C.at, d = C.d;
  const tSmi = at('smithsonian'), tNat = at('national'), tBey = at('rick'), tPBS = at('pbs'), tLux = at('luxembourg'), tBet = at('bettembourg'), tLim = at('limpertsberg'), tBas = at('based');
  D(K, T('where the story lives on', 1600, 250, { h: 84, w: 10, align: 'center' }), .1, Math.min(1.5, tSmi - .4), { min: .9, max: 1.5 });
  D(O, W.curve([[1120, 282], [1600, 296], [2080, 278]], { w: 11, over: 14 }), 0, Math.min(1.9, tSmi), { min: .2, max: .35 });
  D(B, T('in the U.S.', 360, 420, { h: 52, w: 7 }), .4, Math.min(2.2, tSmi + .3), { min: .4, max: .8 });
  // icons
  const medal = (x, y) => [W.line(x - 40, y - 130, x - 10, y - 60, { w: 7, bow: 0 }), W.line(x + 40, y - 130, x + 10, y - 60, { w: 7, bow: 0 }), W.circle(x, y, 62, { w: 8 }), W.circle(x, y, 38, { w: 5 })];
  const museum = (x, y) => [W.poly([[x - 110, y - 70], [x, y - 140], [x + 110, y - 70], [x - 110, y - 70]], { w: 7 }), ...[-80, -27, 27, 80].map(dx => W.line(x + dx, y - 62, x + dx, y + 60, { w: 7, bow: 0 })), W.line(x - 120, y + 68, x + 120, y + 68, { w: 8 })];
  const tv = (x, y) => [W.roundRect(x - 105, y - 80, 210, 150, 18, { w: 8 }), W.line(x - 40, y - 80, x - 75, y - 140, { w: 6, bow: 0 }), W.line(x + 40, y - 80, x + 75, y - 140, { w: 6, bow: 0 }), W.poly([[x - 25, y - 35], [x + 35, y - 5], [x - 25, y + 25], [x - 25, y - 35]], { w: 6 })];
  const marker = (x, y) => [W.curve([[x - 60, y + 70], [x - 60, y - 60], [x, y - 110], [x + 60, y - 60], [x + 60, y + 70]], { w: 8 }), W.line(x - 95, y + 72, x + 95, y + 72, { w: 8 }), W.line(x - 30, y - 30, x + 30, y - 30, { w: 5, bow: 0 }), W.line(x - 30, y, x + 30, y, { w: 5, bow: 0 })];
  const monument = (x, y0) => { const y = y0 + 80; return [W.poly([[x - 40, y + 70], [x - 25, y - 130], [x, y - 170], [x + 25, y - 130], [x + 40, y + 70]], { w: 8 }), W.line(x - 90, y + 72, x + 90, y + 72, { w: 8 }), W.line(x - 70, y + 100, x + 70, y + 100, { w: 7 })]; };
  const ROW = (icon, ix, iy, lines, t0, t1, tx) => {
    D(K, icon(ix, iy), t0 - .3, t0 + .5, { min: .45, max: .9 });
    lines.forEach(([s, h], k) => D(k ? B : K, T(s, tx, iy - 50 + k * 70 + (k ? 10 : 0), { h, w: Math.max(6, h * .13) }), t0 + .2 + k * (t1 - t0) / lines.length * .9, t0 + .2 + (k + 1) * (t1 - t0) / lines.length * .9, { min: .4, max: 1.6 }));
  };
  ROW(medal, 450, 650, [['Smithsonian Institution', 56], ['the gold medal, by law,', 44], ['for display and research', 44]], tSmi - .2, tNat - .3, 610);
  ROW(museum, 450, 1070, [['National WWII Museum', 56], ['exhibition (2020):', 44], ['"Ghost Army: The Combat Con', 42], ['Artists of World War II"', 42]], tNat, tBey - .3, 610);
  ROW(tv, 450, 1530, [['Rick Beyer', 56], ['documentary "The Ghost Army"', 44], ['(2013), aired on PBS', 44]], tBey, tPBS + 1.2, 610);
  D(O, W.dashed([[1790, 390], [1790, 1700]], { w: 6, dash: 30, gap: 22 }), tLux - .6, tLux - .2, { min: .3, max: .5 });
  D(B, T('in Luxembourg', 1880, 420, { h: 52, w: 7 }), tLux - .2, tLux + .6, { min: .4, max: .8 });
  // "In Luxembourg, there is a Ghost Army marker at Bettembourg": the marker as soon as the shot lands, words on the words
  D(K, marker(1960, 690), tLux - .2, tLux + .6, { min: .45, max: .9 });
  D(B, T('Ghost Army marker', 2120, 720, { h: 52, w: 7 }), at('ghost') - .1, at('marker') + .5, { min: .5, max: 1.4 });
  D(K, T('Bettembourg', 2120, 640, { h: 64, w: 8 }), tBet - .2, tBet + .8, { min: .5, max: 1.2 });
  ROW(monument, 1960, 950, [['Limpertsberg,', 64], ['Luxembourg City', 52], ['monument unveiled', 52], ['Sept. 7, 2023', 52], ['where the unit', 52], ['was once based', 52]], Math.min(tLim - .3, at('monument') - .1), tBas + .2, 2120);
  // each entry held while it is written, then the whole board
  const keys = shots([[0, 1600, 470, 1.1], [tSmi - .4, 1130, 775, 1.1], [tNat - .2, 1130, 930, 1.1], [tBey - .2, 1130, 1300, 1.1],
    [tLux - .5, 2435, 922, 1.15], [Math.max(tLim + .8, Math.min(d - .5, tBas + 1.0)), 1600, 900, .715]]);
  return finish(E, new W.Camera(keys), { W: 3300, H: 1900, seed: 4343 });
}

const TAU0 = Math.PI * 2;

// ───────── the film: eras on one clock
export async function build() {
  await W.loadFont('tech', '/styles/whiteboard/demo/fonts/EMSTech.json');
  const TM = timing(), BUILD = { g08: buildG08, g12: buildG12, g30: buildG30, g36: buildG36, g42: buildG42, g43: buildG43 };
  const eras = TM.scenes.filter(s => BUILD[s.id]).map(s => ({ s, E: BUILD[s.id](s) }));
  const find = t => eras.find(e => t >= e.s.start && t < e.s.end) || eras[eras.length - 1];
  const render = (ctx, t) => { const e = find(t); ctx.setTransform(1, 0, 0, 1, 0, 0); e.E.render(ctx, Math.max(0, t - e.s.start)); };
  const ev = eras.flatMap(e => e.E.ev.map(x => ({ ...x, t: +(x.t + e.s.start).toFixed(3), scene: e.s.id })));
  const minText = t => { const e = find(t); return { scene: e.s.id, ...e.E.minText(Math.max(0, t - e.s.start)) }; };
  const clipped = t => { const e = find(t); return { scene: e.s.id, ...e.E.clipped(Math.max(0, t - e.s.start)) }; };
  return { dur: TM.dur, render, ev, subs: [], minText, clipped, scenes: TM.scenes };
}
