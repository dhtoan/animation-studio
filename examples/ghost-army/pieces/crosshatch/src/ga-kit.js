// =====================================================================
//  GHOST ARMY — piece helpers (prefixed ga*, on top of kit/core.js and styles/crosshatch/kit.js)
// =====================================================================
const GA = {
  olive: '#6f7046', oliveD: '#4a4b2c', oliveL: '#9a9a68', track: '#3b3a33', steel: '#8b8a80',
  khaki: '#8a7d55', khakiD: '#62583a', trous: '#6b6346', skin: '#e2b48e', skinD: '#c08a64', boot: '#3a2a1e', helmet: '#5e6140',
  fake: '#d4382c', fakeA: 'rgba(212,56,44,0.92)', night: '#0c0d1c', night2: '#15173a', sil: '#07080f',
  water: '#1b2150', land: '#10122a', field: '#c9c08e', fieldD: '#a99d68', sky: '#e8e0c8', grey: '#8f8a7e',
};
const gaCapsule = (a, b, r, n = 8) => {
  const ang = Math.atan2(b[1] - a[1], b[0] - a[0]);
  return [...arcPts(b[0], b[1], r, ang - Math.PI / 2, ang + Math.PI / 2, n), ...arcPts(a[0], a[1], r, ang + Math.PI / 2, ang + Math.PI * 1.5, n)];
};
const gaShade = (x0, y0, x1, y1) => (px, py) => clamp(((px - x0) / (x1 - x0 || 1)) * 0.5 + ((py - y0) / (y1 - y0 || 1)) * 0.7 - 0.25);
const gaTP = (x, y, s, sx = 1, sy = 1) => (P) => P.map(([u, v]) => [x + u * s * sx, y + v * s * sy]);
const gaDefer = (f) => { if (DEFER) DEFER.push(f); else f(); };

// ---- captions and cards (screen space, via DEFER)
const gaTag = (s, str, at) => gaDefer(() => inkCard(str, 80 + (handW(str, 56) + 50) / 2, 88, 56, { rot: -0.03, s: popS(at ?? s.start + 0.15) }));
function gaCap(str, at, o = {}) {
  if (TT < at + 0.05) return;
  gaDefer(() => inkCard(str, o.x ?? CX, o.y ?? 990, o.size ?? 46, { rot: o.rot ?? 0.008, frac: ev(at, o.d ?? Math.min(1.6, 0.03 * str.length + 0.3)), color: o.color }));
}
// a typed note card that GROWS with its text: width follows the longest typed line, height the lines begun
function gaNote(lines, x, y, size, o = {}) {
  const t0 = o.t ?? -1e9, per = o.per ?? 0.045, gap = o.gap ?? 0.25;
  const counts = []; let tt = t0;
  for (const l of lines) { counts.push(Math.floor(clamp((TT - tt) / (per * l.length)) * l.length)); tt += per * l.length + gap; }
  const shown = counts.filter((c) => c > 0).length; if (!shown) return;
  const cw = monoW(size), w = Math.max(...counts.map((c) => c)) * cw + size * 1.6, h = shown * size * 1.45 + size * 0.9;
  ctx.save(); ctx.translate(x, y); ctx.rotate(o.rot ?? -0.015);
  paint(rrectPts(8, 10, w, h, 6), { fill: 'rgba(58,36,23,0.3)', line: false, key: 'nsh' + lines[0], tex: [{ k: 'hatch', a: 0.8, gap: 4, al: 0.5 }] });
  paint(rrectPts(0, 0, w, h, 6), { fill: o.fill ?? '#f6efd9', key: 'nt' + lines[0], w: 2.6, tex: [{ k: 'pencil', c: '#e8d6b0', al: 0.5, per: 90 }] });
  lines.forEach((l, i) => { if (counts[i] > 0) monoText(l, size * 0.8, size * 1.35 + i * size * 1.45, size, (o.colors && o.colors[i]) || C.ink, { key: 'nl' + l, count: counts[i] }); });
  ctx.restore();
}
const gaNoteLen = (lines, per = 0.045, gap = 0.25) => lines.reduce((a, l) => a + per * l.length + gap, 0);
function gaLabel(str, x, y, size = 22, color = 'rgba(58,36,23,0.75)') { monoText(str, x, y, size, color, { key: 'lb' + str, weight: 700 }); }

// ---- scenery
function gaCloud(cx, cy, w, h, key, o = {}) {
  const P = []; for (let i = 0; i <= 10; i++) { const a = Math.PI + i / 10 * Math.PI; P.push([cx + Math.cos(a) * w, cy + Math.sin(a) * h * (0.7 + 0.3 * Math.abs(Math.sin(i * 1.7)))]); }
  paint(P, { fill: o.fill ?? '#f4eedc', key, w: 2, line: o.line ?? 'rgba(58,36,23,0.6)', tex: [{ k: 'hatch', a: 0.2, gap: 6, al: 0.25, c: o.hc ?? C.ink, dens: (px, py) => clamp((py - cy + h) / h) }] });
}
function gaPoplar(x, y, h, key, o = {}) {
  const sw = Math.sin(TT * 1.6 + x) * h * 0.02;
  ink([[x, y], [x, y - h * 0.35]], { w: Math.max(3, h * 0.035), color: '#5a3d24', key: key + 't' });
  paint(ellipsePts(x + sw, y - h * 0.62, h * 0.14, h * 0.4, 0, 24), { fill: o.fill ?? '#6f8a4a', key: key + 'c', w: 2.5, tex: [{ k: 'cross', c: '#3e5326', al: 0.4, gap: 5, dens: gaShade(x - h * 0.14, y - h, x + h * 0.14, y - h * 0.2) }] });
}
function gaRoundTree(x, y, h, key) {
  ink([[x, y], [x, y - h * 0.45]], { w: Math.max(3, h * 0.05), color: '#5a3d24', key: key + 't' });
  paint(ellipsePts(x, y - h * 0.65, h * 0.32, h * 0.3, 0, 26), { fill: '#7a8f4e', key: key + 'c', w: 2.5, tex: [{ k: 'cross', c: '#3e5326', al: 0.35, gap: 5, dens: gaShade(x - h * 0.3, y - h, x + h * 0.3, y - h * 0.35) }] });
}
function gaFence(x0, x1, y, h, key, o = {}) {   // posts and two strands of barbed wire
  const n = Math.max(2, Math.round((x1 - x0) / (o.gap ?? 120)));
  for (let i = 0; i <= n; i++) { const x = lerp(x0, x1, i / n); ink([[x, y], [x + 3, y - h]], { w: o.w ?? 5, color: o.c ?? '#5a3d24', key: key + 'p' + i }); }
  for (const k of [0.45, 0.85]) {
    ink([[x0, y - h * k], [x1, y - h * k + 4]], { w: 1.6, color: o.wc ?? '#4a4550', key: key + 'w' + k, amt: 1.2 });
    for (let i = 0; i < n * 4; i++) { const x = lerp(x0, x1, (i + 0.5) / (n * 4)), yy = y - h * k + 2 * (i / (n * 4)); ink([[x - 5, yy - 5], [x + 5, yy + 5]], { w: 1.4, color: o.wc ?? '#4a4550', key: key + 'b' + k + i, amt: 0.4 }); ink([[x - 5, yy + 5], [x + 5, yy - 5]], { w: 1.4, color: o.wc ?? '#4a4550', key: key + 'c' + k + i, amt: 0.4 }); }
  }
}
function gaSandbags(x0, y, n, s, key, o = {}) {
  for (let r = 0; r < 2; r++) for (let i = 0; i < n - r; i++) {
    const cx = x0 + (i + r * 0.5) * s * 1.05, cy = y - r * s * 0.42;
    paint(ellipsePts(cx, cy, s * 0.55, s * 0.24, 0, 18), { fill: o.fill ?? '#b9a77c', key: key + r + i, w: 2, line: o.line, tex: [{ k: 'hatch', a: 0.9, gap: 4, al: 0.35, c: o.hc ?? C.ink, dens: (px, py) => clamp((py - cy) / (s * 0.24) + 0.5) }] });
  }
}
function gaCrate(x, y, w, h, key) {
  paint(box(x, y - h, w, h), { fill: '#b88f5a', key, w: 2.5, tex: [{ k: 'hatch', a: 0, gap: 9, al: 0.35 }] });
  ink([[x, y - h], [x + w, y]], { w: 2, key: key + 'x' }); ink([[x + w, y - h], [x, y]], { w: 2, key: key + 'y' });
}
function gaTent(x, y, w, h, key) {
  paint([[x - w / 2, y], [x - w * 0.1, y - h], [x + w * 0.1, y - h], [x + w / 2, y]], { fill: '#7d7a4e', key, w: 2.5, tex: [{ k: 'cross', c: '#4b4a2c', al: 0.35, gap: 6, dens: gaShade(x - w / 2, y - h, x + w / 2, y) }] });
  paint([[x - w * 0.06, y], [x, y - h * 0.62], [x + w * 0.06, y]], { fill: '#2f2d1c', key: key + 'd', w: 2 });
}
function gaMug(x, y, s, key) {   // a side-view enamel mug
  paint(rrectPts(x - s * 0.4, y - s, s * 0.8, s, 6), { fill: '#e9e2d0', key: key + 'b', w: 2.4, tex: [{ k: 'hatch', a: 0.9, gap: 4, al: 0.3, dens: (px) => clamp((px - x) / (s * 0.4)) }] });
  ink(arcPts(x + s * 0.4, y - s * 0.5, s * 0.22, -1.4, 1.4, 10), { w: 4, key: key + 'h' });
  for (let i = 0; i < 2; i++) { const P = []; for (let k = 0; k <= 6; k++) P.push([x - s * 0.1 + i * s * 0.2 + Math.sin(k * 0.9 + TT * 3 + i) * 6, y - s - 10 - k * 10]); ink(P, { w: 2, color: 'rgba(58,36,23,0.4)', key: key + 's' + i }); }
}
function gaLamp(x, y, s, key, on = true) {   // a desk lamp with a soft cone of light
  if (on) { ctx.save(); const g = ctx.createRadialGradient(x + s * 0.9, y - s * 0.2, 10, x + s * 0.9, y + s * 0.6, s * 2.2); g.addColorStop(0, 'rgba(255,226,150,0.45)'); g.addColorStop(1, 'rgba(255,226,150,0)'); ctx.fillStyle = g; ctx.beginPath(); ctx.moveTo(x + s * 0.55, y - s * 1.0); ctx.lineTo(x + s * 1.35, y - s * 1.0); ctx.lineTo(x + s * 2.4, y + s * 0.2); ctx.lineTo(x - s * 0.4, y + s * 0.2); ctx.closePath(); ctx.fill(); ctx.restore(); }
  paint(ellipsePts(x, y, s * 0.4, s * 0.1, 0, 18), { fill: '#3e5a46', key: key + 'b', w: 2.4 });
  ink([[x, y], [x + s * 0.3, y - s * 0.8], [x + s * 0.7, y - s * 1.05]], { w: 6, color: '#3e5a46', key: key + 'a' });
  paint([[x + s * 0.5, y - s * 1.0], [x + s * 0.75, y - s * 1.3], [x + s * 1.3, y - s * 1.1], [x + s * 1.35, y - s * 0.95]], { fill: '#3e5a46', key: key + 's', w: 2.4, tex: [{ k: 'hatch', a: 0.7, gap: 4, al: 0.35 }] });
}
function gaPin(x, y, c = '#c9a227') { ctx.fillStyle = c; ctx.beginPath(); ctx.arc(x, y, 9, 0, TAU); ctx.fill(); ctx.lineWidth = 2; ctx.strokeStyle = C.ink; ctx.stroke(); ctx.fillStyle = 'rgba(255,255,255,0.6)'; ctx.beginPath(); ctx.arc(x - 3, y - 3, 3, 0, TAU); ctx.fill(); }
function gaWallClock(x, y, r, key) {
  paint(ellipsePts(x, y, r, r, 0, 30), { fill: '#f3ecd8', key, w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 5, al: 0.2, dens: gaShade(x - r, y - r, x + r, y + r) }] });
  for (let i = 0; i < 12; i++) { const a = i / 12 * TAU; ink([[x + Math.cos(a) * r * 0.8, y + Math.sin(a) * r * 0.8], [x + Math.cos(a) * r * 0.92, y + Math.sin(a) * r * 0.92]], { w: 2, key: key + 't' + i, amt: 0.2 }); }
  const m = TT * 0.8, hA = TT * 0.07;
  ink([[x, y], [x + Math.sin(hA) * r * 0.5, y - Math.cos(hA) * r * 0.5]], { w: 4, key: key + 'h', amt: 0.2 });
  ink([[x, y], [x + Math.sin(m) * r * 0.75, y - Math.cos(m) * r * 0.75]], { w: 2.5, key: key + 'm', amt: 0.2 });
}
function gaBirds(n, y0, key, o = {}) {
  for (let i = 0; i < n; i++) { const x = mod(200 + i * 160 + TT * (o.v ?? 40), 2300) - 150, y = y0 + i * 22 + Math.sin(TT * 3 + i) * 8, f = (B + i) % 2 ? 10 : -6; ink([[x - 16, y + f], [x, y], [x + 16, y + f]], { w: 2.4, color: o.c ?? C.ink, key: key + i }); }
}
