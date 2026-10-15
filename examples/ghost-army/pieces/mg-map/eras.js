// Map eras after g02 (second half of the film): g20 Normandy, g23 Brittany/Brest, g24 Luxembourg/Bettembourg,
// g26 Battle of the Bulge, g28 Viersen (the reveal), g31 Italy. Same night-HUD look and helpers as g02 (film.js
// passes its kit). Every era stands alone: its own camera, its own beats keyed to its narration words.
// Facts: the scene narration and claims only. Positions, routes and lines are approximate / schematic.
const W = 1920, H = 1080, TAU = Math.PI * 2;
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, u) => a + (b - a) * u;
const P = (t, a, d) => clamp((t - a) / Math.max(1e-6, d));
const outC = (u) => 1 - Math.pow(1 - u, 3);
const ioC = (u) => (u < 0.5 ? 4 * u * u * u : 1 - Math.pow(-2 * u + 2, 3) / 2);
const outB = (u, s = 1.6) => 1 + (s + 1) * Math.pow(u - 1, 3) + s * Math.pow(u - 1, 2);
const smoother = (u) => u * u * u * (u * (u * 6 - 15) + 10);

export const NARRATIONS = {
  g20: "We've seen the tools. Now let's follow the unit across Europe, starting on the beaches of Normandy. The Ghost Army's war began there. Four of its members landed on D-Day itself, and two became casualties while building false beach landing sites. Seymour Nussenbaum, who had studied art at the Pratt Institute, landed on Omaha Beach about two weeks later.",
  g23: 'In August, the unit moved to Brittany, supporting the Allied advance and the siege of the port city of Brest. According to one detailed nonprofit account, it was at Brest that the unit first combined visual, sonic and radio deception in a single operation.',
  g24: "By the end of the summer of nineteen forty-four, the unit had worked in Normandy and in Brittany. Next came Luxembourg. In September came one of the boldest bluffs. Patton's Third Army had a thinly held stretch of line in Luxembourg. In Operation Bettembourg, about five hundred men impersonated the roughly eight thousand men of the Sixth Armored Division.",
  g26: "During the Battle of the Bulge, the 23rd broadcast fake radio traffic suggesting that parts of Patton's Third Army were moving toward the besieged town of Bastogne.",
  g28: "Then came Viersen, the last and largest deception, from March eighteenth to twenty-fourth, nineteen forty-five. The Ghost Army impersonated two infantry divisions, the Thirtieth and the Seventy-Ninth, to draw German attention away from the Ninth Army's real crossing point on the Rhine.",
  g31: 'Meanwhile, in Italy, the 3133rd Signal Service Company carried out its own deceptions. In April nineteen forty-five, in Operation Craftsman, it supported an offensive against the German Gothic Line north of Florence, working alongside British deception units. About two hundred soldiers served in the 3133rd. They spent nineteen days in combat and lost almost seventy percent of their thirty-five dummy tanks to German fire.',
};

const PL = {   // approximate positions (lon, lat)
  omaha: [-0.85, 49.37], normandy: [-0.75, 49.15], brest: [-4.49, 48.39], brittany: [-2.9, 48.2],
  bettembourg: [6.10, 49.52], luxCity: [6.13, 49.61], bastogne: [5.72, 50.0], viersen: [6.395, 51.256], florence: [11.255, 43.77],
};
// approximate Gothic Line (schematic), west coast -> Adriatic, north of Florence
const GOTHIC = [[10.05, 44.05], [10.35, 44.13], [10.7, 44.12], [11.0, 44.08], [11.27, 44.12], [11.55, 44.1], [11.9, 44.02], [12.3, 43.95], [12.75, 43.9]];
// schematic Third Army line through Luxembourg (east side), and the thin stretch near Bettembourg
const LINE3 = [[6.42, 50.12], [6.38, 49.95], [6.45, 49.8], [6.48, 49.65], [6.40, 49.52], [6.25, 49.47], [6.05, 49.45]];

export function makeEras(K) {
  const { g, proj, path, LAND, BORDERS, CTRY, C, F, label, rr, vis, crPath, sampleCR, along, glyph, observer, GRAIN, rng, RHINE, ROADS, DIV, OBS, TOWNS } = K;
  const GRAT = d3.geoGraticule().extent([[-12, 36], [20, 58]]).step([1, 1])();
  const FINE = d3.geoGraticule().extent([[-6, 43], [13, 53]]).step([0.1, 0.1])();

  // ---------- shared pieces ----------
  function cam(t, keys) {
    let k = 0; while (k < keys.length - 2 && t > keys[k + 1][0]) k++;
    const a = keys[k], b = keys[k + 1], u = (k === 0 ? smoother : ioC)(P(t, a[0], b[0] - a[0]));
    const ip = d3.geoInterpolate([a[1], a[2]], [b[1], b[2]])(u);
    const c = { lon: ip[0], lat: ip[1], s: Math.exp(lerp(Math.log(a[3]), Math.log(b[3]), u)), x: lerp(a[4] ?? 960, b[4] ?? 960, u), y: lerp(a[5] ?? 540, b[5] ?? 540, u) };
    proj.rotate([-c.lon, -c.lat]).scale(c.s).translate([c.x, c.y]);
    return c;
  }
  function base(t, c, countries = []) {
    g.setTransform(1, 0, 0, 1, 0, 0); g.globalAlpha = 1; g.globalCompositeOperation = 'source-over'; g.setLineDash([]); g.lineDashOffset = 0;
    g.lineCap = 'butt'; g.lineJoin = 'miter'; g.letterSpacing = '0px'; g.filter = 'none';
    const bg = g.createRadialGradient(960, 520, 120, 960, 540, 1250); bg.addColorStop(0, C.sea1); bg.addColorStop(1, C.sea0);
    g.fillStyle = bg; g.fillRect(0, 0, W, H);
    g.fillStyle = C.land; g.beginPath(); path(LAND); g.fill();
    g.strokeStyle = C.coast; g.lineWidth = 1.3; g.beginPath(); path(LAND); g.stroke();
    const bA = 1 - clamp((c.s - 22000) / 30000);
    if (bA > 0) { g.globalAlpha = bA; g.setLineDash([5, 5]); g.strokeStyle = C.border; g.lineWidth = 1.2; g.beginPath(); path(BORDERS); g.stroke(); g.setLineDash([]); g.globalAlpha = 1; }
    g.strokeStyle = C.grat; g.lineWidth = 1; g.beginPath(); path(GRAT); g.stroke();
    const fA = clamp((c.s - 45000) / 40000);
    if (fA > 0) { g.globalAlpha = fA; g.strokeStyle = 'rgba(120,160,180,0.08)'; g.beginPath(); path(FINE); g.stroke(); g.globalAlpha = 1; }
    for (const [n, lo, la, a] of countries) if (a > 0 && vis([lo, la], c)) { const [x, y] = proj([lo, la]); g.globalAlpha = a * 0.9; label(n, x, y, F.sans(600, 28), 28, C.faint, 'center', 8, null); g.globalAlpha = 1; }
  }
  function country(name, a, fill = 'rgba(125,185,242,0.06)') {
    if (a <= 0) return; const f = CTRY.features.find((x) => x.properties && x.properties.name === name); if (!f) return;
    g.globalAlpha = a; g.fillStyle = fill; g.beginPath(); path(f); g.fill(); g.strokeStyle = 'rgba(166,203,224,0.55)'; g.lineWidth = 2; g.setLineDash([8, 6]); g.beginPath(); path(f); g.stroke(); g.setLineDash([]); g.globalAlpha = 1;
  }
  function river(c, pts0, a = 1) {
    if (a <= 0) return;
    const pts = pts0.filter((ll) => vis(ll, c)).map((ll) => proj(ll)), rw = Math.min(17, Math.max(2, c.s / 6500));
    g.globalAlpha = a; g.lineCap = 'round'; g.lineJoin = 'round';
    g.strokeStyle = 'rgba(95,147,173,0.25)'; g.lineWidth = rw * 2.2; crPath(pts); g.stroke();
    g.strokeStyle = C.river; g.lineWidth = rw; crPath(pts); g.stroke();
    g.strokeStyle = C.riverHi; g.lineWidth = Math.max(1, rw * 0.2); crPath(pts); g.stroke(); g.globalAlpha = 1;
  }
  function furniture(t, title, sub, chip, c, { note = 'approximate positions', scale = true, backdrop = false } = {}) {
    const hA = P(t, 0.15, 0.5);
    if (backdrop) { const bd = g.createLinearGradient(0, 0, 0, 230); bd.addColorStop(0, 'rgba(6,12,17,0.85)'); bd.addColorStop(1, 'rgba(6,12,17,0)'); g.fillStyle = bd; g.fillRect(0, 0, W, 230); }
    g.globalAlpha = hA;
    label(title, 96, 92, F.head(54), 54, C.ink, 'left', 4, null);
    if (sub) label(sub, 96, 140, F.sans(500, 28), 28, C.dim, 'left', 0, null);
    if (chip) { g.font = F.mono(28); g.letterSpacing = '3px'; const w = g.measureText(chip).width + 48; g.letterSpacing = '0px';
      g.fillStyle = 'rgba(242,177,52,0.14)'; rr(1824 - w, 66, w, 52, 26); g.fill(); g.strokeStyle = 'rgba(242,177,52,0.6)'; g.lineWidth = 1.5; rr(1824 - w, 66, w, 52, 26); g.stroke();
      label(chip, 1824 - w / 2, 93, F.mono(28), 28, C.amber, 'center', 3, null); }
    if (note) label(note, 96, sub ? 182 : 140, F.mono(18), 18, C.faint, 'left', 1, null, false);
    g.globalAlpha = 1;
    const km = c.s / 6371;
    if (scale) for (const d of [10, 50, 100, 200]) { const L = d * km; if (L > 80 && L < 420) { const x0 = W - 96 - L, y0 = H - 78;
      g.fillStyle = C.dim; g.fillRect(x0, y0, L, 3); g.fillRect(x0, y0 - 9, 2, 12); g.fillRect(x0 + L - 2, y0 - 9, 2, 12); g.fillRect(x0 + L / 2 - 1, y0 - 6, 2, 9);
      label(`${d} km`, x0 + L, y0 - 26, F.mono(22), 22, C.dim, 'center', 0, null, false); break; } }
    const f = Math.round(t * 30), r1 = rng(f + 7)(), r2 = rng(f + 99)();
    g.save(); g.globalAlpha = 0.045; g.globalCompositeOperation = 'overlay'; g.translate(-r1 * 256, -r2 * 256); g.fillStyle = GRAIN; g.fillRect(0, 0, W + 256, H + 256); g.restore();
    const v = g.createRadialGradient(960, 540, 500, 960, 540, 1180); v.addColorStop(0, 'rgba(0,0,0,0)'); v.addColorStop(1, 'rgba(0,0,0,0.6)');
    g.fillStyle = v; g.fillRect(0, 0, W, H);
  }
  // place marker: primary = big League Gothic name with pulse; secondary = small dot + 28 px name
  function marker(c, ll, t, t0, name, { primary = false, side = 1, col = C.amber, sub = null, dy = 0, fade = 1 } = {}) {
    const a = P(t, t0, 0.45) * fade; if (a <= 0 || !vis(ll, c)) return null;
    const [x, y] = proj(ll);
    g.globalAlpha = a;
    if (primary) for (let i = 0; i < 2; i++) { const u = ((t - t0) * 0.6 + i * 0.5) % 1; g.strokeStyle = col; g.globalAlpha = a * (1 - u) * 0.55; g.lineWidth = 2; g.beginPath(); g.arc(x, y, 14 + u * 46, 0, TAU); g.stroke(); }
    g.globalAlpha = a; const k = outB(P(t, t0, 0.45));
    g.fillStyle = 'rgba(6,12,17,0.9)'; g.beginPath(); g.arc(x, y, (primary ? 14 : 10) * k, 0, TAU); g.fill();
    g.fillStyle = primary ? col : C.dim; g.beginPath(); g.arc(x, y, (primary ? 9 : 6) * k, 0, TAU); g.fill();
    if (name) {
      const al = side > 0 ? 'left' : 'right', lx = x + side * (primary ? 26 : 18);
      if (primary) label(name, lx, y + 3 + dy, F.head(52), 52, C.ink, al, 3); else label(name, lx, y + dy, F.sans(600, 28), 28, C.dim, al);
      if (sub) label(sub, lx, y + (primary ? 44 : 34) + dy, F.sans(500, 28), 28, C.dim, al);
    }
    g.globalAlpha = 1; return [x, y];
  }
  function card(x, y, w, t, t0, lines, { accent = C.amber, fade = 1 } = {}) {   // lines: [text, font, size, col, gap]
    const p = outC(P(t, t0, 0.55)) ; if (p <= 0 || fade <= 0) return;
    const h = lines.reduce((s, l) => s + l[4], 0) + 26;
    g.save(); g.globalAlpha = fade; g.beginPath(); g.rect(x - 4, y - 4, (w + 8) * p, h + 8); g.clip();
    g.fillStyle = 'rgba(8,15,21,0.9)'; rr(x, y, w, h, 6); g.fill();
    g.strokeStyle = 'rgba(242,177,52,0.35)'; g.lineWidth = 1.5; rr(x + 0.5, y + 0.5, w - 1, h - 1, 6); g.stroke();
    g.fillStyle = accent; g.fillRect(x, y, 6, h);
    let yy = y + 13;
    lines.forEach(([s, font, size, col, gap], i) => { const a = P(t, t0 + 0.2 + i * 0.12, 0.3); g.globalAlpha = a * fade;
      label(s, x + 32 + (1 - outC(a)) * 16, yy + gap / 2, font, size, col, 'left', i === 0 && size >= 40 ? 2 : 0, null); yy += gap; });
    g.restore();
  }
  // animated dashed route along a smooth curve; returns head point
  function route(c, lls, t, t0, d, { col = C.amber, w = 4, dash = [14, 10], arrow = true, fade = 1 } = {}) {
    const p = ioC(P(t, t0, d)); if (p <= 0 || fade <= 0) return null;
    const pts = lls.filter((ll) => vis(ll, c)).map((ll) => proj(ll)); if (pts.length < 2) return null;
    const S = sampleCR(pts, 16), L = S.L * p;
    g.save(); g.globalAlpha = fade; g.strokeStyle = col; g.lineWidth = w; g.lineCap = 'round'; g.setLineDash(dash); g.lineDashOffset = -t * 30;
    g.beginPath(); g.moveTo(S.pts[0][0], S.pts[0][1]); for (let i = 1; i < S.pts.length && S.cum[i] <= L; i++) g.lineTo(S.pts[i][0], S.pts[i][1]);
    const hd = along(S, L); g.lineTo(hd.x, hd.y); g.stroke(); g.setLineDash([]);
    if (arrow) { g.fillStyle = col; g.translate(hd.x, hd.y); g.rotate(hd.ang); g.beginPath(); g.moveTo(10, 0); g.lineTo(-10, -9); g.lineTo(-10, 9); g.closePath(); g.fill(); }
    g.restore(); return hd;
  }
  // unit symbol: kind 'inf' (X) or 'arm' (oval); dashed + SIMULATED when simulated
  function unit(x, y, t, t0, name, { kind = 'inf', simulated = false, below = true, col = null, size = 1, alpha = 1, tag = true } = {}) {
    const a = P(t, t0, 0.45); if (a <= 0 || alpha <= 0) return;
    const k = outB(a, 1.4) * size, w = 120, h = 78, cc = col || (simulated ? C.amber : C.blue);
    g.save(); g.globalAlpha = alpha; g.translate(x, y); g.scale(k, k);
    g.fillStyle = 'rgba(6,12,17,0.75)'; g.fillRect(-w / 2 - 6, -h / 2 - 34, w + 12, h + 40);
    g.fillStyle = simulated ? 'rgba(242,177,52,0.14)' : C.blueFill; g.fillRect(-w / 2, -h / 2, w, h);
    g.strokeStyle = cc; g.lineWidth = 4.5; if (simulated) { g.setLineDash([12, 8]); g.lineDashOffset = -t * 18; }
    g.strokeRect(-w / 2, -h / 2, w, h); g.setLineDash([]); g.lineWidth = 3.5;
    if (kind === 'inf') { g.beginPath(); g.moveTo(-w / 2, -h / 2); g.lineTo(w / 2, h / 2); g.moveTo(w / 2, -h / 2); g.lineTo(-w / 2, h / 2); g.stroke(); }
    else { g.beginPath(); g.ellipse(0, 0, w * 0.33, h * 0.26, 0, 0, TAU); g.stroke(); }
    g.lineWidth = 4; for (const [dx, s] of [[-10, 1], [10, -1]]) { g.beginPath(); g.moveTo(dx - 6 * s, -h / 2 - 28); g.lineTo(dx + 6 * s, -h / 2 - 8); g.moveTo(dx + 6 * s, -h / 2 - 28); g.lineTo(dx - 6 * s, -h / 2 - 8); g.stroke(); }
    g.restore();
    const la = P(t, t0 + 0.25, 0.4) * alpha; g.globalAlpha = la;
    const ly = below ? y + h / 2 * k + 34 : y - h / 2 * k - 60;
    label(name, x, ly, F.sans(650, 30), 30, C.ink, 'center');
    if (simulated && tag) label('SIMULATED', x, ly + (below ? 36 : -36), F.mono(24), 28, C.amber, 'center', 4);
    g.globalAlpha = 1;
  }
  function radioArcs(x, y, t, t0, dir, col, { n = 3, reach = 160, spread = 0.5, fade = 1 } = {}) {
    if (t < t0 || fade <= 0) return; const a0 = P(t, t0, 0.4) * fade;
    for (let k = 0; k < n; k++) { const v = ((t - t0) * 0.7 + k / n) % 1; g.strokeStyle = col; g.globalAlpha = a0 * (1 - v) * 0.85; g.lineWidth = 3 - v * 1.5;
      g.beginPath(); g.arc(x, y, 20 + v * reach, dir - spread, dir + spread); g.stroke(); }
    g.globalAlpha = 1;
  }
  function mast(x, y, s, col, a) { g.save(); g.globalAlpha = a; g.translate(x, y); g.scale(s, s); g.strokeStyle = col; g.lineWidth = 3; g.lineCap = 'round';
    g.beginPath(); g.moveTo(-12, 18); g.lineTo(0, -22); g.lineTo(12, 18); g.moveTo(-7, 2); g.lineTo(7, 2); g.stroke(); g.fillStyle = col; g.beginPath(); g.arc(0, -26, 5, 0, TAU); g.fill(); g.restore(); }
  function person(x, y, s, col) { g.fillStyle = col; g.beginPath(); g.arc(x, y - 22 * s, 9 * s, 0, TAU); g.fill(); rr(x - 11 * s, y - 10 * s, 22 * s, 30 * s, 8 * s); g.fill(); }
  const OVERVIEW = [['normandy', 'Normandy'], ['brest', 'Brest'], ['bettembourg', 'Luxembourg'], ['viersen', 'Viersen']];

  // ---------- g20: Normandy, Omaha Beach ----------
  function g20(t, cue) {
    const tN = cue.at('Normandy'), tB = cue.at('began'), tF = cue.at('Four'), tCas = cue.at('casualties'), tS = cue.at('Seymour'), tO = cue.at('Omaha'), tL = cue.at('later');
    const c = cam(t, [[0, 2.5, 49.4, 3300], [Math.max(1.5, cue.at('Europe')), 2.8, 49.5, 3600], [tB, -0.95, 49.33, 36000, 860, 470], [cue.d, -0.95, 49.33, 40000, 860, 470]]);
    base(t, c, [['FRANCE', 2.4, 47.2, 1 - P(t, tN, 1)], ['UNITED KINGDOM', -1.8, 52.4, 1 - P(t, tN, 1)], ['GERMANY', 9.6, 50.9, 1 - P(t, tN, 1)], ['BELGIUM', 4.7, 50.6, 1 - P(t, tN, 1)]]);
    // the journey ahead: dim stops across Europe (first beat), then the camera goes to the beaches
    const ov = P(t, cue.at('follow'), 0.6) * (1 - P(t, tN + 0.4, 0.8));
    if (ov > 0) { route(c, OVERVIEW.map(([k]) => PL[k]), t, cue.at('across'), 1.6, { col: 'rgba(242,177,52,0.7)', w: 3, fade: ov });
      OVERVIEW.forEach(([k, n], i) => marker(c, PL[k], t, cue.at('across') + i * 0.25, n, { side: k === 'brest' ? -1 : 1, fade: ov })); }
    const ch = P(t, tN + 0.8, 1) * 0.9; if (ch > 0) { g.globalAlpha = ch; const [x, y] = proj([-0.25, 49.72]); label('ENGLISH CHANNEL', x, y, F.sans(600, 28), 28, C.riverHi, 'center', 10, null); g.globalAlpha = 1; }
    const om = marker(c, PL.omaha, t, tB - 0.3, 'OMAHA BEACH', { primary: true, side: -1, dy: -46 });
    // D-Day card: four members landed; two became casualties (shown as two muted figures, no injury imagery)
    if (om) {
      const cx = 1060, cy = 560, a = P(t, tF, 0.5);
      card(cx, cy, 700, t, tF - 0.2, [['D-DAY', F.head(52), 52, C.ink, 62], ['Four members of the 23rd landed.', F.sans(500, 30), 30, C.ink, 46],
        ['Two became casualties building', F.sans(500, 30), 30, C.dim, 42], ['false beach landing sites.', F.sans(500, 30), 30, C.dim, 46]], { fade: 1 - P(t, tS - 0.5, 0.5) });
      if (a > 0 && t < tS) for (let i = 0; i < 4; i++) { const pa = P(t, tF + 0.3 + i * 0.12, 0.3), cas = i >= 2 ? P(t, tCas, 0.6) : 0;
        g.globalAlpha = pa * (1 - P(t, tS - 0.5, 0.5)); person(cx + 520 + i * 40, cy + 80, 1.2, cas > 0 ? `rgba(236,231,218,${0.9 - 0.6 * cas})` : C.ink);
        g.globalAlpha = 1; }
      card(cx, cy, 700, t, tS - 0.2, [['SEYMOUR NUSSENBAUM', F.head(52), 52, C.ink, 62], ['studied art at the Pratt Institute;', F.sans(500, 30), 30, C.ink, 46],
        ['landed on Omaha Beach', F.sans(500, 30), 30, C.ink, 42], ['about two weeks after D-Day', F.sans(600, 30), 30, C.amber, 46]]);
      const tl = P(t, tO, 0.6); if (tl > 0) { g.strokeStyle = C.amber; g.lineWidth = 2; g.globalAlpha = tl; g.setLineDash([6, 8]); g.beginPath(); g.moveTo(om[0] + 18, om[1]); g.lineTo(lerp(om[0] + 18, cx - 6, outC(tl)), lerp(om[1], cy + 120, outC(tl))); g.stroke(); g.setLineDash([]); g.globalAlpha = 1; }
    }
    void tL;
    furniture(t, 'NORMANDY', 'where the Ghost Army’s war began', null, c);
  }

  // ---------- g23: Normandy -> Brittany -> the siege of Brest ----------
  function g23(t, cue) {
    const tBr = cue.at('Brittany'), tSi = cue.at('siege'), tBe = cue.at('Brest'), tAcc = cue.at('According'), tC = cue.at('combined'), tV = cue.at('visual'), tSo = cue.at('sonic'), tR = cue.at('radio');
    const c = cam(t, [[0, -1.2, 48.9, 7000], [tBr + 0.4, -2.3, 48.55, 7600], [tBe + 0.3, -4.2, 48.4, 26000, 820, 520], [cue.d, -4.25, 48.4, 28000, 820, 520]]);
    base(t, c, [['FRANCE', 0.2, 47.6, 1 - P(t, tSi, 0.8)]]);
    marker(c, PL.normandy, t, 0.3, 'Normandy', { side: 1 });
    const hd = route(c, [PL.normandy, [-1.5, 48.75], [-2.2, 48.35], [-3.0, 48.25], [-3.8, 48.3], [-4.35, 48.39]], t, cue.at('moved') - 0.2, tBe - cue.at('moved') + 0.2);
    const bt = P(t, tBr, 0.6) * (1 - P(t, tBe, 0.8)); if (bt > 0) { g.globalAlpha = bt; const [x, y] = proj(PL.brittany); label('BRITTANY', x, y + 70, F.sans(600, 30), 30, C.faint, 'center', 10, null); g.globalAlpha = 1; }
    const bm = marker(c, PL.brest, t, tBe - 0.4, 'BREST', { primary: true, side: 1, sub: 'port city under siege', dy: -40 });
    if (bm) { const sa = P(t, tSi, 0.8);   // the siege: Allied ring closing on the port
      if (sa > 0) { g.strokeStyle = C.blue; g.lineWidth = 4; g.globalAlpha = sa; g.setLineDash([16, 10]); g.lineDashOffset = -t * 20; g.beginPath(); g.arc(bm[0], bm[1], 150 - 30 * outC(sa), Math.PI * 0.55, Math.PI * 1.45); g.stroke(); g.setLineDash([]);
        for (let k = 0; k < 7; k++) { const an = Math.PI * (0.6 + k * 0.13), r = 150 - 30 * outC(sa); g.beginPath(); g.moveTo(bm[0] + Math.cos(an) * (r + 16), bm[1] + Math.sin(an) * (r + 16)); g.lineTo(bm[0] + Math.cos(an) * (r + 2), bm[1] + Math.sin(an) * (r + 2)); g.stroke(); }
        g.globalAlpha = 1; } }
    void hd;
    // three methods converge on Brest
    if (bm && t > tC - 0.3) {
      const items = [['VISUAL', tV, 'eye'], ['SONIC', tSo, 'spk'], ['RADIO', tR, 'radio']];
      items.forEach(([n, t0, ic], i) => { const a = P(t, t0 - 0.15, 0.45); if (a <= 0) return;
        const sx = 1180 + i * 210, sy = 700, u = outC(P(t, t0, 0.8)), x = lerp(sx, sx, u), y = sy;
        g.globalAlpha = a; g.fillStyle = 'rgba(8,15,21,0.92)'; rr(x - 90, y - 60, 180, 120, 10); g.fill(); g.strokeStyle = C.amber; g.lineWidth = 2; rr(x - 90, y - 60, 180, 120, 10); g.stroke();
        g.strokeStyle = C.amber; g.fillStyle = C.amber; g.lineWidth = 3;
        if (ic === 'eye') { g.beginPath(); g.ellipse(x, y - 14, 30, 16, 0, 0, TAU); g.stroke(); g.beginPath(); g.arc(x, y - 14, 7, 0, TAU); g.fill(); }
        else if (ic === 'spk') { g.beginPath(); g.moveTo(x - 24, y - 22); g.lineTo(x - 6, y - 22); g.lineTo(x + 8, y - 34); g.lineTo(x + 8, y + 6); g.lineTo(x - 6, y - 6); g.lineTo(x - 24, y - 6); g.closePath(); g.fill(); for (let k = 0; k < 2; k++) { g.beginPath(); g.arc(x + 10, y - 14, 14 + k * 9, -0.7, 0.7); g.stroke(); } }
        else mast(x, y - 10, 0.9, C.amber, a);
        label(n, x, y + 34, F.mono(28), 28, C.ink, 'center', 3, null);
        g.globalAlpha = a * 0.8; g.strokeStyle = 'rgba(242,177,52,0.6)'; g.lineWidth = 2; g.setLineDash([4, 8]); g.beginPath(); g.moveTo(x, y - 60); g.lineTo(lerp(x, bm[0], 0.95), lerp(y - 60, bm[1], 0.95)); g.stroke(); g.setLineDash([]); g.globalAlpha = 1; });
      card(1090, 820, 720, t, cue.at('single') - 0.2, [['in a single operation, for the first time', F.sans(600, 30), 30, C.ink, 44], ['according to one nonprofit account', F.sans(500, 28), 28, C.dim, 40]]);
    }
    const ac = P(t, tAcc, 0.4) * (1 - P(t, tC - 0.4, 0.4)); if (ac > 0) card(1090, 760, 720, t, tAcc, [['ONE DETAILED NONPROFIT ACCOUNT', F.head(44), 44, C.ink, 54], ['says this happened at Brest:', F.sans(500, 30), 30, C.dim, 44]], { fade: ac });
    furniture(t, 'BRITTANY AND BREST', 'supporting the Allied advance', 'AUGUST 1944', c);
  }

  // ---------- g24: Luxembourg, Operation Bettembourg ----------
  function g24(t, cue) {
    const tLx = cue.at('Luxembourg'), tSe = cue.at('September'), tPa = cue.at('Patton'), tTh = cue.at('thinly'), tOp = cue.at('Bettembourg'), tFi = cue.at('five'), tEi = cue.at('eight'), tAr = cue.at('Armored');
    const c = cam(t, [[0, 1.6, 48.9, 3900], [tLx - 0.2, 2.2, 49.1, 4300], [tSe + 0.4, 6.25, 49.62, 70000, 760, 540], [cue.d, 6.25, 49.62, 74000, 760, 540]]);
    base(t, c, [['FRANCE', 2.4, 47.4, 1 - P(t, tLx, 1)], ['GERMANY', 9.4, 50.6, 1 - P(t, tLx, 1)], ['LUXEMBOURG', 5.95, 49.86, P(t, tSe + 0.4, 0.6)], ['FRANCE', 6.05, 49.33, P(t, tSe + 0.4, 0.6)], ['GERMANY', 6.95, 49.85, P(t, tSe + 0.4, 0.6)]]);
    // recap: where the unit had already worked
    const rc = 1 - P(t, tLx + 0.3, 0.8);
    marker(c, PL.normandy, t, 0.5, 'Normandy', { side: -1, fade: rc });
    marker(c, PL.brest, t, 0.8, 'Brittany', { side: 1, dy: 34, fade: rc });
    route(c, [PL.normandy, [1.5, 49.3], [4.0, 49.5], PL.luxCity], t, tLx - 0.4, 1.2, { fade: rc });
    // Third Army line (schematic) with the thinly held stretch
    const la = P(t, tPa, 0.8);
    if (la > 0) {
      const pts = LINE3.filter((ll) => vis(ll, c)).map((ll) => proj(ll)), S = sampleCR(pts, 16), th = P(t, tTh, 0.6);
      g.save(); g.globalAlpha = la; g.lineCap = 'round';
      for (let i = 1; i < S.pts.length; i++) { const u = S.cum[i] / S.L; if (u > la) break; const thin = u > 0.62 && u < 0.92;
        g.strokeStyle = C.blue; g.lineWidth = thin ? lerp(7, 2, th) : 7; g.globalAlpha = la * (thin ? lerp(1, 0.55, th) : 1);
        g.beginPath(); g.moveTo(S.pts[i - 1][0], S.pts[i - 1][1]); g.lineTo(S.pts[i][0], S.pts[i][1]); g.stroke(); }
      g.restore();
      const lp = along(S, S.L * 0.2); g.globalAlpha = la; label('Third Army line', lp.x + 26, lp.y, F.sans(600, 30), 30, C.blue, 'left'); g.globalAlpha = 1;
      if (th > 0) { const q = along(S, S.L * 0.78); g.globalAlpha = th; label('thinly held', q.x + 24, q.y + 30, F.sans(600, 28), 28, C.blue, 'left'); g.globalAlpha = 1; }
    }
    marker(c, PL.luxCity, t, tSe, 'Luxembourg City', { side: -1 });
    const bm = marker(c, PL.bettembourg, t, tOp - 0.3, 'BETTEMBOURG', { primary: true, side: -1, dy: 40 });
    { const u = proj([6.27, 49.59]); if (bm) unit(u[0], u[1], t, tEi - 0.3, '6th Armored Division', { kind: 'arm', simulated: true, below: false, size: 0.9 }); }
    // 500 vs 8,000
    const cc = P(t, tFi - 0.2, 0.4);
    if (cc > 0) {
      const x0 = 1190, y0 = 560, x = x0 + 32, Wb = 560;
      card(x0, y0, 630, t, tFi - 0.3, [['OPERATION BETTEMBOURG', F.head(44), 44, C.ink, 60], ['', F.sans(500, 28), 28, C.ink, 200]]);
      g.globalAlpha = P(t, tFi, 0.4); label('about 500 men', x, y0 + 100, F.sans(600, 30), 30, C.amber, 'left', 0, null);
      g.fillStyle = C.amber; g.fillRect(x, y0 + 122, Wb * 500 / 8000 * outC(P(t, tFi, 0.6)), 24);
      const eb = P(t, tEi, 0.8); g.globalAlpha = eb; label('impersonated about 8,000', x, y0 + 184, F.sans(600, 30), 30, C.ink, 'left', 0, null);
      g.strokeStyle = C.ink; g.setLineDash([10, 7]); g.lineWidth = 2.5; g.strokeRect(x, y0 + 206, Wb * outC(eb), 24); g.setLineDash([]);
      g.globalAlpha = 1;
    }
    void tAr;
    furniture(t, 'LUXEMBOURG', 'one of the boldest bluffs', 'SEPTEMBER 1944', c, { note: 'approximate positions · schematic front line' });
  }

  // ---------- g26: Battle of the Bulge, fake radio toward Bastogne ----------
  function g26(t, cue) {
    const tBu = cue.at('Bulge'), tFa = cue.at('fake'), tSu = cue.at('suggesting'), tPa = cue.at('Patton'), tMo = cue.at('moving'), tBs = cue.at('besieged'), tBa = cue.at('Bastogne');
    const c = cam(t, [[0, 5.6, 49.9, 14000], [tFa, 5.75, 49.78, 60000, 960, 540], [cue.d, 5.75, 49.78, 64000, 960, 540]]);
    base(t, c, [['BELGIUM', 5.2, 50.07, 1], ['LUXEMBOURG', 6.12, 49.72, 1]]);
    const bm = marker(c, PL.bastogne, t, tBu - 0.4, 'BASTOGNE', { primary: true, side: 1, sub: null, dy: -48 });
    if (bm) { const sa = P(t, tBs - 0.2, 0.6);   // besieged: red ring of German pressure
      if (sa > 0) { g.globalAlpha = sa; g.strokeStyle = C.red; g.lineWidth = 3; for (let k = 0; k < 18; k++) { const an = k / 18 * TAU + t * 0.05; g.beginPath(); g.moveTo(bm[0] + Math.cos(an) * 92, bm[1] + Math.sin(an) * 92); g.lineTo(bm[0] + Math.cos(an) * 112, bm[1] + Math.sin(an) * 112); g.stroke(); }
        g.beginPath(); g.arc(bm[0], bm[1], 92, 0, TAU); g.stroke(); label('besieged', bm[0] + 120, bm[1] + 70, F.sans(600, 28), 28, C.red, 'left'); g.globalAlpha = 1; } }
    // the suggested Third Army moves (dashed: radio-only suggestion), with radio arcs riding along
    const fade = P(t, tPa - 0.3, 0.4);
    const arrows = [[[6.05, 49.40], [6.0, 49.58], [5.88, 49.78], [5.77, 49.925]], [[5.50, 49.42], [5.58, 49.6], [5.66, 49.8], [5.70, 49.925]]];
    arrows.forEach((a, i) => { const hd = route(c, a, t, tMo - 0.6 + i * 0.25, 1.6, { col: C.blue, w: 5, dash: [16, 12], fade });
      if (hd) radioArcs(hd.x, hd.y, t, tMo, hd.ang, C.blue, { reach: 90, fade }); });
    const ta = P(t, tPa, 0.5) * fade; if (ta > 0) { const [x, y] = proj([5.25, 49.62]); g.globalAlpha = ta; label('Third Army moves?', x, y, F.sans(600, 30), 30, C.blue, 'center'); label('suggested only by radio', x, y + 38, F.sans(500, 28), 28, C.dim, 'center'); g.globalAlpha = 1; }
    // the broadcast: radio masts, west of the sector (schematic)
    const ma = P(t, tFa - 0.3, 0.5);
    if (ma > 0) { const [x, y] = proj([5.3, 49.97]); mast(x, y, 1.4, C.amber, ma); radioArcs(x, y - 30, t, tFa, 0, C.amber, { reach: 200, spread: 0.7 });
      g.globalAlpha = ma; label('FAKE RADIO TRAFFIC', x, y + 52, F.mono(28), 28, C.amber, 'center', 3); g.globalAlpha = 1; }
    void tSu; void tBa;
    furniture(t, 'BATTLE OF THE BULGE', 'broadcast by the 23rd', null, c, { note: 'approximate positions · schematic arrows' });
  }

  // ---------- g28: Viersen, the reveal (same sector geometry as g02) ----------
  function g28(t, cue) {
    const tV = cue.at('Viersen'), tLa = cue.at('largest'), tM = cue.at('March'), tIm = cue.at('impersonated'), t30 = cue.at('Thirtieth'), t79 = cue.at('Seventy'), tDr = cue.at('draw'), tNi = cue.at('Ninth'), tRe = cue.at('real'), tCr = cue.at('crossing');
    const c = cam(t, [[0, 6.62, 51.31, 98000, 960, 520], [tDr - 0.6, 6.63, 51.31, 100000, 960, 520], [tNi - 0.1, 6.62, 51.45, 70000, 960, 560], [cue.d, 6.62, 51.45, 68000, 960, 560]]);
    base(t, c, []);
    river(c, RHINE, 1);
    const roads = ROADS.map((r) => r.filter((ll) => vis(ll, c)).map((ll) => proj(ll)));
    g.lineCap = 'round'; g.lineJoin = 'round'; for (const pts of roads) { g.strokeStyle = 'rgba(196,206,212,0.16)'; g.lineWidth = 7; crPath(pts); g.stroke(); }
    // Viersen + the river label, as in g02
    marker(c, PL.viersen, t, tV - 0.4, 'VIERSEN', { primary: true, side: -1 });
    { const a = proj([6.735, 51.29]), b = proj([6.725, 51.31]); g.save(); g.globalAlpha = P(t, 0.4, 0.6); g.translate(a[0] + 40, a[1]); g.rotate(Math.atan2(b[1] - a[1], b[0] - a[0])); label('RHINE', 0, 0, F.sans(650, 30), 30, C.riverHi, 'center', 12); g.restore(); }
    // what the Germans saw (as in g02: solid units, parked columns), then the reveal on "impersonated"
    const rv = P(t, tIm, 0.8), seen = P(t, tV + 0.4, 0.6), zs = c.s / 98000;
    roads.forEach((pts) => { if (pts.length < 2) return; const S = sampleCR(pts, 12);
      for (let i = 0; i < 8; i++) { const p = along(S, S.L - 70 * zs - i * 46 * zs), kind = 'TKG'[i % 3];
        if (rv < 1) glyph(kind, p.x, p.y, p.ang, 1.7 * zs, seen * (1 - rv));
        if (rv > 0) { g.save(); g.globalAlpha = rv * 0.9; g.translate(p.x, p.y); g.rotate(p.ang); g.scale(1.7 * zs, 1.7 * zs); g.strokeStyle = C.amber; g.lineWidth = 1.2; g.setLineDash([3, 3]); rr(-13, -7, 26, 14, 3); g.stroke(); g.setLineDash([]); g.restore(); } } });
    const dP = DIV.map((d) => proj(d.ll)), sc = clamp(zs, 0.75, 1);
    [[0, false, t30], [1, true, t79]].forEach(([i, below, tl]) => {
      const nm = i ? '79th Infantry Division' : '30th Infantry Division';
      if (rv < 1) unit(dP[i][0], dP[i][1], t, tV + 0.3 + i * 0.2, nm, { below, size: sc, alpha: 1 - rv });
      if (rv > 0) unit(dP[i][0], dP[i][1], t, 0, nm, { simulated: true, tag: P(t, tl - 0.2, 0.3) > 0, below, size: sc, alpha: rv }); });
    // German attention drawn to the decoys
    const oP = OBS.map((ll) => proj(ll));
    oP.forEach(([x, y], i) => { observer(x, y, t, tDr - 0.4 + i * 0.1, 0);
      const q = outC(P(t, tDr, 0.7)); if (q > 0) { g.strokeStyle = 'rgba(226,88,63,0.85)'; g.lineWidth = 3; g.setLineDash([3, 9]); g.beginPath(); g.moveTo(x - 30, y); g.lineTo(lerp(x - 30, dP[i][0] + 70, q), lerp(y, dP[i][1], q)); g.stroke(); g.setLineDash([]); } });
    { const a = P(t, tDr + 0.3, 0.4); if (a > 0) { g.globalAlpha = a; label('German attention', oP[1][0] + 40, oP[1][1] + 52, F.sans(600, 28), 28, C.red, 'left'); g.globalAlpha = 1; } }
    // the real crossing, to the north (approximate)
    const rA = P(t, tRe - 0.2, 0.5);
    if (rA > 0) { const A = proj([6.38, 51.585]), B = proj([6.86, 51.585]); const hd = (() => { g.save(); g.globalAlpha = rA; g.strokeStyle = C.blue; g.fillStyle = C.blue; g.lineWidth = 12; g.lineCap = 'round';
        const u = outC(P(t, tRe, 0.8)), ex = lerp(A[0], B[0], u), ey = lerp(A[1], B[1], u); g.beginPath(); g.moveTo(A[0], A[1]); g.lineTo(ex, ey); g.stroke();
        g.translate(ex, ey); g.rotate(Math.atan2(B[1] - A[1], B[0] - A[0])); g.beginPath(); g.moveTo(22, 0); g.lineTo(-12, -18); g.lineTo(-12, 18); g.closePath(); g.fill(); g.restore(); return [ex, ey]; })();
      g.globalAlpha = P(t, tCr, 0.4); label('NINTH ARMY · REAL CROSSING', A[0] - 20, A[1] - 84, F.mono(28), 28, C.blue, 'left', 2); label('to the north (approximate)', A[0] - 20, A[1] - 46, F.sans(500, 28), 28, C.dim, 'left', 0); g.globalAlpha = 1; void hd; }
    const ll = P(t, tLa, 0.5); if (ll > 0) { g.globalAlpha = ll * (1 - P(t, tIm - 0.4, 0.4)); label('the last and largest deception', 96, 182, F.sans(600, 30), 30, C.amber, 'left', 0, null); g.globalAlpha = 1; }
    furniture(t, 'THE RHINE, NEAR VIERSEN', null, P(t, tM, 0.1) > 0 ? 'MARCH 18–24, 1945' : null, c, { note: P(t, tIm - 0.4, 0.4) > 0 ? 'approximate positions · schematic roads' : null, backdrop: true });
  }

  // ---------- g31: Italy, the 3133rd, Operation Craftsman ----------
  function g31(t, cue) {
    const tIt = cue.at('Italy'), t33 = cue.at('3133rd'), tAp = cue.at('April'), tCr = cue.at('Craftsman'), tGo = cue.at('Gothic'), tFl = cue.at('Florence'), tBr = cue.at('British'),
      tTw = cue.at('two'), tNi = cue.at('nineteen', 1), tSe = cue.at('seventy'), tTf = cue.at('thirty'), tDu = cue.at('dummy'), tFi = cue.at('fire');
    const c = cam(t, [[0, 6.5, 47.5, 2600], [tIt + 0.6, 11.3, 43.6, 4800], [tGo, 11.25, 43.95, 30000, 640, 600], [cue.d, 11.25, 43.95, 31500, 640, 600]]);
    base(t, c, [['ITALY', 12.6, 42.6, P(t, tIt, 0.6) * (1 - P(t, tGo, 0.6))], ['FRANCE', 3.5, 46.5, 1 - P(t, tIt, 0.6)], ['GERMANY', 10.0, 50.0, 1 - P(t, tIt, 0.6)]]);
    marker(c, PL.viersen, t, 0.3, 'Viersen', { side: 1, fade: 1 - P(t, tIt, 0.6) });
    const fm = marker(c, PL.florence, t, tFl - 0.4, 'FLORENCE', { primary: true, side: -1, dy: 30 });
    marker(c, [10.4, 43.72], t, tGo + 0.3, 'Pisa', { side: -1 });
    marker(c, [11.34, 44.49], t, tGo + 0.3, 'Bologna', { side: 1 });
    // the German Gothic Line (schematic), north of Florence
    const gl = P(t, tGo - 0.3, 1.0);
    if (gl > 0) { const pts = GOTHIC.filter((ll) => vis(ll, c)).map((ll) => proj(ll)), S = sampleCR(pts, 16);
      g.save(); g.strokeStyle = C.red; g.lineWidth = 5; g.lineCap = 'round'; g.beginPath(); g.moveTo(S.pts[0][0], S.pts[0][1]);
      for (let i = 1; i < S.pts.length && S.cum[i] <= S.L * gl; i++) g.lineTo(S.pts[i][0], S.pts[i][1]); g.stroke();
      for (let s = 30; s < S.L * gl; s += 44) { const p = along(S, s); g.save(); g.translate(p.x, p.y); g.rotate(p.ang); g.beginPath(); g.moveTo(-8, 0); g.lineTo(0, -13); g.lineTo(8, 0); g.fillStyle = C.red; g.fill(); g.restore(); }
      g.restore(); const lp = along(S, S.L * 0.18); g.globalAlpha = P(t, tGo, 0.5); label('GOTHIC LINE', lp.x - 10, lp.y - 46, F.mono(28), 28, C.red, 'left', 3); g.globalAlpha = 1; }
    // the offensive and the deception, from the south (schematic)
    if (fm) { route(c, [[11.0, 43.45], [11.15, 43.62], [11.25, 43.85], [11.3, 44.0]], t, cue.at('offensive') - 0.3, 1.2, { col: C.blue, w: 6, dash: [1, 0] });
      const ba = P(t, tBr, 0.5); if (ba > 0) { const [x, y] = proj([11.75, 43.62]); g.globalAlpha = ba; for (let i = 0; i < 4; i++) { g.strokeStyle = C.amber; g.lineWidth = 2; g.setLineDash([6, 6]); rr(x - 46 + i * 24, y - 10, 22, 14, 3); g.stroke(); } g.setLineDash([]);
        label('with British deception units', x - 50, y + 36, F.sans(600, 28), 28, C.amber, 'left'); g.globalAlpha = 1; } }
    // the 3133rd panel
    const px = 1240, py = 200, pA = P(t, t33 - 0.2, 0.5);
    card(px, py, 600, t, t33 - 0.2, [['3133rd', F.head(56), 56, C.ink, 64], ['Signal Service Company', F.sans(600, 30), 30, C.ink, 44]]);
    card(px, py + 150, 600, t, tCr - 0.3, [['OPERATION CRAFTSMAN', F.head(44), 44, C.amber, 54], ['April 1945', F.sans(500, 30), 30, C.dim, 42]]);
    void pA; void tAp;
    const sa = P(t, tTw - 0.2, 0.4);
    if (sa > 0) {
      card(px, py + 290, 600, t, tTw - 0.2, [['about 200 soldiers', F.sans(650, 34), 34, C.ink, 50], ['19 days in combat', F.sans(650, 34), 34, P(t, tNi, 0.3) > 0 ? C.ink : 'rgba(0,0,0,0)', 50]]);
      const da = P(t, tTf - 0.3, 0.5);   // 35 dummy tanks; almost 70% lost (shown as dimmed, no destruction imagery)
      if (da > 0) { const gx = px + 36, gy = py + 456;
        g.globalAlpha = da; label('35 dummy tanks', gx - 4, gy - 4, F.sans(600, 30), 30, C.amber, 'left', 0, null);
        for (let i = 0; i < 35; i++) { const col = i % 8, row = Math.floor(i / 8), x = gx + col * 66, y = gy + 36 + row * 44, ap = P(t, tTf + i * 0.02, 0.2);
          const lost = i < 24 ? P(t, tFi - 0.6 + (23 - i) * 0.02, 0.4) : 0;   // 24 of 35 = "almost 70 percent" (only the words are shown)
          g.globalAlpha = ap * lerp(1, 0.2, lost); g.strokeStyle = C.amber; g.lineWidth = 2; g.setLineDash([4, 3]); rr(x, y, 48, 24, 6); g.stroke(); g.beginPath(); g.arc(x + 22, y + 10, 7, 0, TAU); g.stroke(); g.setLineDash([]); }
        g.globalAlpha = P(t, tSe, 0.5); label('almost 70% lost to German fire', gx - 4, gy + 270, F.sans(600, 30), 30, C.ink, 'left', 0, null); g.globalAlpha = 1; }
    }
    void tDu;
    furniture(t, 'ITALY', 'north of Florence', 'APRIL 1945', c, { note: 'approximate positions · schematic lines' });
  }

  return { g20, g23, g24, g26, g28, g31 };
}
