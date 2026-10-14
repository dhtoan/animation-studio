// Ghost Army — g06 as an orders / routing sheet, drafted with the blueprint engine of lemo-opuscar (MIT),
// imported from the library: /styles/blueprint/demo/draw.js (line/solid/hatch/text/balloon/nibs),
// /styles/blueprint/demo/sheet.js (border, handShadow). Beats come from the narration (timing.js).
// Facts: only what the g06 narration says. No dates, ports or numbers beyond it; the route is a schematic.
import { setCam, clear, proj, nibs, line, solid, hatch, text, textW, balloon, LW, FONT, rect, circ, NIBS, cam } from '/styles/blueprint/demo/draw.js';
import { SW, SH, border, handShadow } from '/styles/blueprint/demo/sheet.js';
import { clamp, lerp, seg, eio, track } from '/core/lib.js';
import { timing, cues } from './timing.js';

const N06 = 'On January twentieth, nineteen forty-four, the 23rd Headquarters Special Troops was activated at Camp Forrest, Tennessee, under Colonel Harry Reeder, who would command it for the rest of the war. From there, its men would train, ship out, and eventually cross the Atlantic to England and the battlefields of France.';
const RY = 1340;   // route line

function buildG06(scene) {
  const C = cues(N06, scene), at = C.at, d = C.d, texts = [];
  const tJan = at('january'), tUnit = at('23rd'), tAct = at('activated'), tCamp = at('camp'), tCol = at('colonel'), tRest = at('rest'),
    tFrom = at('from'), tTrain = at('train'), tShip = at('ship'), tCross = at('cross'), tEng = at('england'), tFr = at('france');
  // text that is recorded for the legibility check (font size in sheet units)
  const T = (s, x, y, o) => { const u = o.u ?? 1; if (u > 0) texts.push({ s, x, y, size: o.size, w: textW(s, o.size, o.font || FONT.hand, o.ls || 0), align: o.align }); return text(s, x, y, o); };
  // window [a, b] with a minimum hold so a short era still draws at a readable pace
  const W2 = (t, a, b, min = .35) => seg(t, a, Math.max(b, a + min));

  // ───────── order block: two columns, three rows (the activation facts, as narrated)
  const OB = { y0: 450, rh: 175, cols: [[170, 1560], [1640, 3030]], lab: 400 };
  const FIELDS = [
    [0, 0, 'ACTIVATED', '20 JAN. 1944', tJan], [0, 1, 'UNIT', '23RD HQ SPECIAL TROOPS', tUnit], [0, 2, 'LOCATION', 'CAMP FORREST, TENN.', tCamp],
    [1, 0, 'COMMANDER', 'COL. HARRY L. REEDER', tCol], [1, 1, 'TERM', 'FOR THE REST OF THE WAR', tRest], [1, 2, 'SCALE', 'NOT TO SCALE', tFrom - 1.2],
  ];
  function orderBlock(t) {
    for (const [ci, [x0, x1]] of OB.cols.entries()) {
      const u = W2(t, .3 + ci * .5, 1.5 + ci * .5, .6), y1 = OB.y0 + OB.rh * 3;
      line(rect(x0, OB.y0, x1, y1), { w: LW.out * 1.1, closed: true, u });
      for (let r = 1; r < 3; r++) line([[x0, OB.y0 + OB.rh * r], [x1, OB.y0 + OB.rh * r]], { w: LW.det, u: clamp(u * 1.6 - .4), nib: false });
      line([[x0 + OB.lab, OB.y0], [x0 + OB.lab, y1]], { w: LW.det, u: clamp(u * 1.6 - .5), nib: false });
    }
    for (const [ci, ri, lab, val, tw] of FIELDS) {
      const x0 = OB.cols[ci][0], y = OB.y0 + ri * OB.rh;
      T(lab, x0 + 24, y + 108, { size: 50, font: FONT.tech, weight: 700, ls: 2, v: .85, u: W2(t, tw - .5, tw - .05, .3) });
      T(val, x0 + OB.lab + 30, y + 114, { size: 64, font: FONT.hand, ls: 2, u: W2(t, tw - .05, tw + .9, .5) });
    }
  }
  // ───────── FIG. 1 route schematic: Tennessee → training → ship out → Atlantic → England → France
  const X = [420, 880, 1350, 1900, 2430, 2880];
  const STN = [['CAMP FORREST, TENN.', tFrom], ['TRAINING', tTrain], ['SHIP OUT', tShip], ['ATLANTIC CROSSING', tCross], ['ENGLAND', tEng], ['FRANCE', tFr]];
  function station(i, t) {
    const [lab, tw] = STN[i], x = X[i], u = W2(t, tw - .55, tw + .25, .45);
    if (u <= 0) return;
    if (i === 0) { solid(circ(x, RY, 52, 48), { w: LW.out, u }); const st = []; for (let k = 0; k <= 5; k++) { const a = -Math.PI / 2 + k * 4 * Math.PI / 5; st.push([x + Math.cos(a) * 34, RY + Math.sin(a) * 34]); } line(st, { w: LW.det, u: clamp(u * 2 - 1) }); }
    if (i === 1) { for (const r of [95, 64, 34]) line(circ(x, RY - 200, r, 48), { w: LW.det, u }); line([[x, RY - 105], [x, RY - 52]], { w: LW.det, u }); solid(circ(x, RY, 30, 32), { w: LW.det, u }); hatch(circ(x, RY - 200, 34, 24), { sp: 9, u: clamp(u * 2 - 1) }); }
    if (i === 2) {   // a ship, side elevation: hull, deckhouse, bridge, funnel, mast
      const y = RY - 40;
      solid([[x - 210, y], [x + 160, y], [x + 225, y - 80], [x - 230, y - 80]], { w: LW.out, u });
      solid(rect(x - 95, y - 160, x + 60, y - 80), { w: LW.det, u: clamp(u * 1.5 - .3) });
      solid(rect(x - 55, y - 215, x + 15, y - 160), { w: LW.det, u: clamp(u * 1.5 - .4) });
      solid([[x + 80, y - 80], [x + 128, y - 80], [x + 122, y - 200], [x + 86, y - 200]], { w: LW.det, u: clamp(u * 1.5 - .5) });
      line([[x - 150, y - 80], [x - 150, y - 250]], { w: LW.det, u: clamp(u * 1.5 - .5) });
      hatch([[x - 205, y - 12], [x + 168, y - 12], [x + 162, y], [x - 210, y]], { sp: 8, u: clamp(u * 2 - 1) });
    }
    if (i === 3) {   // the ocean: rows of waves under the crossing
      for (let r = 0; r < 3; r++) { const p = []; for (let xx = 1560; xx <= 2250; xx += 12) p.push([xx, RY + 40 + r * 34 + Math.sin(xx / 34 + r * 1.7) * 9]); line(p, { w: LW.thin, u: clamp(u * 1.4 - r * .12), nib: r === 0 }); }
    }
    if (i >= 4) { solid(circ(x, RY, 52, 48), { w: LW.out, u }); line(circ(x, RY, 30, 40), { w: LW.det, u: clamp(u * 2 - 1) }); }
    const lu = W2(t, tw - .1, tw + .7, .4);
    const rows = i === 0 ? ['CAMP FORREST,', 'TENN.'] : [lab];
    rows.forEach((r, k) => T(r, i === 3 ? 1905 : x, RY + 200 + k * 62, { size: 52, font: FONT.hand, ls: 3, align: 'center', u: clamp(lu * rows.length - k) }));
    balloon([x, i === 3 ? RY - 20 : RY - 60], [x, RY - 330], String(i + 1), { u: W2(t, tw + .1, tw + .7, .3), r: 34 });
  }
  function route(t) {
    for (let i = 0; i < X.length - 1; i++) {
      const a = X[i] + 56, b = X[i + 1] - 56, tw = STN[i + 1][1], u = W2(t, tw - .9, tw - .45, .3);
      if (u <= 0) continue;
      const over = i === 2 || i === 3;      // ship out and the crossing: phantom line over the water
      line([[i === 3 ? 1560 : a, RY], [i === 2 ? 1560 : b, RY]], { w: LW.det, u, dash: over ? 'phantom' : null });
      if (u >= 1) { const ax = i === 2 ? 1560 : b; line([[ax - 26, RY - 12], [ax, RY], [ax - 26, RY + 12]], { w: LW.det, nib: false }); }
    }
  }
  const camKeys = track([
    [0, [1600, 818, .655]], [Math.max(1, tRest + .5), [1600, 818, .665]],                  // the whole order block (header + six fields)
    [tFrom - .1, [1100, 1300, .9]], [tShip + .4, [1250, 1300, .9]], [tCross - .1, [2100, 1300, .9]], [tEng + .2, [2150, 1300, .9]],   // ride the route
    [Math.min(d - .5, tFr + .3), [1600, 975, .66]], [d, [1600, 975, .665]]]);
  const camAt = t => { const [x, y, z] = camKeys(t), hw = 960 / z, hh = 540 / z;   // never past the sheet edge
    return { x: clamp(x, hw, SW - hw), y: clamp(y, hh, SH - hh), z }; };

  function render(t) {
    const c = camAt(t); setCam({ ...c, r: 0 }); proj.k = 0; clear(); texts.length = 0;
    border(W2(t, 0, .9, .6));
    T('23RD HEADQUARTERS SPECIAL TROOPS', 170, 300, { size: 104, font: FONT.hand, ls: 8, u: W2(t, .05, Math.max(1.2, tJan - .1), .8) });
    const hw = textW('23RD HEADQUARTERS SPECIAL TROOPS', 104, FONT.hand, 8);
    line([[170, 330], [170 + hw, 330]], { w: LW.out, u: W2(t, 1.0, 1.6) }); line([[170, 340], [170 + hw, 340]], { w: LW.hair, u: W2(t, 1.0, 1.6) });
    T('ACTIVATION AND ROUTE SCHEMATIC', 172, 400, { size: 48, font: FONT.tech, weight: 700, ls: 5, u: W2(t, tAct - .3, tAct + .6, .5) });
    orderBlock(t);
    const uc = W2(t, .5, 1.8, .6);
    line([[220, RY], [3000, RY]], { w: LW.hair, dash: 'center', u: uc, v: .55 });
    for (const x of X) line([[x, RY - 40], [x, RY + 40]], { w: LW.hair, u: clamp(uc * 2 - 1), v: .55, nib: false });
    route(t);
    for (let i = 0; i < X.length; i++) station(i, t);
    const uf = W2(t, tFr, tFr + .7, .4);
    T('FIG. 1  ROUTE SCHEMATIC', 1600, 1712, { size: 60, font: FONT.hand, ls: 5, align: 'center', u: W2(t, tAct + .2, tAct + 1.1) });
    T('NOT TO SCALE', 1600, 1778, { size: 48, font: FONT.tech, weight: 700, ls: 6, align: 'center', u: W2(t, tAct + .8, tAct + 1.4) });
    line([[1180, 1734], [2020, 1734]], { w: LW.det, u: W2(t, tAct + .5, tAct + 1.1) });
    T('SHEET 1 OF 1', 2750, 1778, { size: 48, font: FONT.tech, weight: 700, ls: 3, align: 'center', u: uf });
    if (NIBS.length) { const [nx, ny] = NIBS[NIBS.length - 1]; handShadow(nx, ny, .7); }
    nibs(1);
    return { cam: c, roll: [1e6, 80], sheet: [SW, SH], seed: 11, wetBlur: 1, fade: 0 };
  }
  // smallest on-screen font size (px) among the texts drawn at t that are inside the frame
  function minText(t) {
    render(t); const c = camAt(t); let m = 1e9, which = '';
    for (const x of texts) {
      const x0 = x.align === 'center' ? x.x - x.w / 2 : x.x, sx0 = (x0 - c.x) * c.z + 960, sx1 = (x0 + x.w - c.x) * c.z + 960, sy = (x.y - c.y) * c.z + 540;
      if (sx1 < 0 || sx0 > 1920 || sy < 0 || sy - x.size * c.z > 1080) continue;
      if (x.size * c.z < m) { m = x.size * c.z; which = x.s; }
    }
    return { px: m === 1e9 ? null : +m.toFixed(1), text: which };
  }
  const ev = [...STN.map(([lab, tw]) => ({ t: +tw.toFixed(3), type: 'pen', label: lab })), ...FIELDS.map(f => ({ t: +f[4].toFixed(3), type: 'letter', label: f[2] }))];
  return { render, minText, ev };
}

export function build() {
  const TM = timing(), eras = TM.scenes.filter(s => s.id === 'g06').map(s => ({ s, E: buildG06(s) }));
  const find = t => eras.find(e => t >= e.s.start && t < e.s.end) || eras[eras.length - 1];
  return {
    dur: TM.dur, scenes: TM.scenes,
    render: t => { const e = find(t); return e.E.render(Math.max(0, t - e.s.start)); },
    minText: t => { const e = find(t); return { scene: e.s.id, ...e.E.minText(Math.max(0, t - e.s.start)) }; },
    ev: eras.flatMap(e => e.E.ev.map(x => ({ ...x, t: +(x.t + e.s.start).toFixed(3) }))),
  };
}
