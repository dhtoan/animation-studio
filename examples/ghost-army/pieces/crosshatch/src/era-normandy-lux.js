// =====================================================================
//  g21 — Task Force Mason, 14 June 1944: a 16-man detachment sets up dummy artillery (red = fake); enemy fire
//        falls on the dummies, away from the real 980th Field Artillery Battalion behind the hedgerow.
//  g25 — Limpertsberg, Luxembourg City: the building that housed most of the unit, 25 Sept - 22 Dec 1944.
// =====================================================================
function gaHedge(x0, x1, y, h, key, o = {}) {   // a bocage hedgerow: a bank topped with bushy lumps
  const P = [[x0, y]]; const n = Math.max(3, Math.round((x1 - x0) / 70));
  for (let i = 0; i <= n; i++) { const x = lerp(x0, x1, i / n); P.push([x, y - h * (0.7 + 0.3 * Math.abs(Math.sin(i * 1.9 + x0)))]); }
  P.push([x1, y]);
  paint(P, { fill: o.fill ?? '#6f8a4a', key, w: 2.5, tex: [{ k: 'cross', c: '#3e5326', al: 0.42, gap: 5, dens: (px, py) => clamp((py - (y - h)) / h + 0.2) }] });
}
function gaBurst(x, y, t0, key) {   // a shell burst on empty ground: a flash of ink rays, then a smoke puff that drifts and thins
  const u = (TT - t0); if (u < 0 || u > 2.2) return;
  if (u < 0.35) burst(x, y - 30, 20, 90 + 80 * u, { key, n: 14, w: 4, c: C.ink });
  for (let i = 0; i < 4; i++) { const R = RNG('pf', key, i), k = clamp(u / 2.2), r = (30 + 50 * k) * R.r(0.7, 1.2); ctx.fillStyle = `rgba(110,104,96,${0.55 * (1 - k)})`; ctx.beginPath(); ctx.arc(x + R.n(40) + k * 30, y - 40 - k * 90 - i * 18, r, 0, TAU); ctx.fill(); }
  for (let i = 0; i < 6; i++) { const R = RNG('cl', key, i), k = clamp(u / 0.8); if (k >= 1) break; ctx.fillStyle = '#5a4630'; ctx.fillRect(x + R.n(70) * k, y - 20 - R.r(40, 120) * Math.sin(k * Math.PI), 6, 6); }
}
function gaMason(s) {
  const ph = (TT - s.start) * 3;
  paperSheet('sky21', { fill: '#e6e2cc', ruled: false });
  [[260, 120, 200, 40], [1000, 90, 240, 44], [1650, 150, 190, 38]].forEach(([x, y, w, h], i) => gaCloud(x + Math.sin(TT * 0.2 + i) * 26, y, w, h, 'c21' + i));
  // fields and hedgerows (the bocage)
  paint(box(-40, 560, 2000, 560), { raw: true, fill: '#b9b77c', key: 'fld21', line: false, tex: [{ k: 'pencil', c: '#8f8d52', al: 0.4, per: 420, a: -0.2, len: 24 }] });
  gaHedge(-40, 1960, 600, 90, 'hg0', { fill: '#7f9656' });
  [[120, 520, 200], [700, 510, 230], [1500, 520, 210]].forEach(([x, y, h], i) => gaRoundTree(x, y, h, 'rt21' + i));
  // the REAL battalion, behind a hedgerow on the right (ink, not red): guns and crews, partly hidden
  [[1440, 790, 170], [1640, 800, 170], [1830, 790, 160]].forEach(([x, y, sz], i) => gaGun(x, y, sz, { key: 'real' + i }));
  [[1510, 805], [1720, 812]].forEach(([x, y], i) => gaFigure(x, y, 120, { face: -1, pose: gaPose('stand'), key: 'crew' + i }));
  gaHedge(1250, 1960, 840, 120, 'hg1');
  // the dummies in the open field on the left, set up one by one by the detachment
  const guns = [[300, 900, 230], [610, 940, 240], [920, 900, 220]], fakeAt = gaAt(s, 0.3, 2.6);
  guns.forEach(([x, y, sz], i) => { const k = popS(gaAt(s, 0.06 + 0.07 * i, 0.4 + i * 0.7)); if (k <= 0) return; ctx.save(); ctx.translate(x, y); ctx.scale(k, k); ctx.translate(-x, -y); gaGun(x, y, sz, { key: 'dm' + i, fake: ev(fakeAt + i * 0.2, 0.5) }); ctx.restore(); });
  // the detachment: at work, then walking off to the left before the fire comes
  const leave = gaAt(s, 0.38, 3.2), lu = clamp((TT - leave) / Math.max(1.2, s.dur * 0.12));
  if (lu < 1) [[200, 0], [430, 1], [540, 2], [760, 3], [1020, 4]].forEach(([x, k]) => gaFigure(x - lu * 1100, 960 + (k % 2) * 30, 260, { face: lu > 0 ? -1 : (k % 2 ? 1 : -1), pose: lu > 0 ? gaPose('walk', ph * 2 + k) : gaPose(k % 2 ? 'pump' : 'point', ph + k), key: 'tf' + k }));
  // incoming fire: dashed arcs from beyond the frame, bursts among the dummies (no one is near them)
  const f0 = gaAt(s, 0.5, 4.2, 1e9, 4.0), bursts = [[420, 980], [780, 920], [180, 870], [1000, 990], [560, 860]];
  bursts.forEach(([x, y], i) => {
    const tb = f0 + i * Math.max(0.6, s.dur * 0.05), arc = ev(tb - 0.6, 0.6);
    if (arc > 0 && arc < 1) ink([[2000, 60], [1400, -10 + i * 10], [x, y - 40]].map(([a, b], j) => [a, b]), { w: 2, color: 'rgba(58,36,23,0.5)', key: 'tr' + i, frac: arc, amt: 1 });
    gaBurst(x, y, tb, 'bu' + i);
  });
  if (TT >= fakeAt + 0.3) handText('dummy artillery', 260, 720, 52, GA.fake, { key: 'dumL', frac: ev(fakeAt + 0.3, 0.7) });
  if (TT >= gaAt(s, 0.58, 5.0)) gaDefer(() => inkCard('real: 980th Field Artillery Battalion', 1500, 520, 34, { rot: 0.02, s: popS(gaAt(s, 0.58, 5.0)) }));
  gaDefer(() => gaNote(['TASK FORCE MASON', '16 men · 1st Lt. Bernard Mason'], 1180, 40, 30, { t: gaAt(s, 0.1, 0.8) }));
  gaTag(s, '14 June 1944 · France');
  gaCap('the unit’s first battlefield deception in France', gaAt(s, 0.7, 6.0, 1e9, 2.4));
}

function gaLuxCal(x, y, u) {   // a tear-off calendar from 25 Sept to 22 Dec 1944 (u = 0..1)
  const months = [['SEPT', 25, 30], ['OCT', 1, 31], ['NOV', 1, 30], ['DEC', 1, 22]];
  const m = Math.min(3, Math.floor(u * 4)), mu = u * 4 - m, [name, d0, d1] = months[m], day = Math.round(lerp(d0, d1, clamp(mu)));
  paint(box(x, y, 300, 330), { fill: '#f6efd9', key: 'cal', w: 3, tex: [{ k: 'pencil', c: '#e8d6b0', al: 0.5, per: 90 }] });
  paint(box(x, y, 300, 70), { fill: '#3c5a8c', key: 'calh', w: 3 });
  monoText(name + ' 1944', x + 30, y + 50, 34, '#f4f6ff', { key: 'calm' + name });
  monoText(String(day).padStart(2, '0'), x + 70, y + 250, 130, C.ink, { key: 'cald' + day });
  for (let i = 0; i < 5; i++) ink([[x + 30 + i * 60, y - 12], [x + 30 + i * 60, y + 14]], { w: 5, color: '#8a8590', key: 'ring' + i });
}
function gaLimpertsberg(s) {
  const u = clamp((TT - s.start - 0.4) / Math.max(1, s.dur * 0.7));   // the season: Sept -> Dec
  paperSheet('sky25', { fill: u < 0.8 ? '#e4e1d4' : '#dfe3e6', ruled: false });
  [[400, 110, 220, 42], [1300, 140, 200, 40]].forEach(([x, y, w, h], i) => gaCloud(x + Math.sin(TT * 0.2 + i) * 26, y, w, h, 'c25' + i));
  // neighbours, then the building (4 storeys under a mansard roof with dormers)
  [[260, 360, 360, '#c9b28e'], [1340, 330, 380, '#b8a58a'], [1720, 420, 300, '#cdbf9e']].forEach(([x, y, w, c], i) => {
    paint(box(x, y, w, 860 - y), { fill: c, key: 'nb' + i, w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 6, al: 0.2, dens: gaShade(x, y, x + w, 860) }] });
    paint([[x - 10, y], [x + w / 2, y - 90], [x + w + 10, y]], { fill: '#7a5a4a', key: 'nr' + i, w: 3, tex: [{ k: 'hatch', a: 0.3, gap: 6, al: 0.35 }] });
    for (let r = 0; r < 3; r++) for (let c2 = 0; c2 < 3; c2++) paint(box(x + 40 + c2 * (w - 80) / 3, y + 60 + r * 140, 60, 80), { fill: '#4a5670', key: 'nw' + i + r + c2, w: 2 });
  });
  const bx = 650, by = 250, bw = 660;
  paint([[bx - 20, by], [bx + 40, by - 120], [bx + bw - 40, by - 120], [bx + bw + 20, by]], { fill: '#5d6470', key: 'mans', w: 3, tex: [{ k: 'cross', c: '#2f3440', al: 0.4, gap: 6 }] });
  for (let i = 0; i < 4; i++) { const x = bx + 80 + i * 150; paint([[x, by - 10], [x, by - 80], [x + 35, by - 110], [x + 70, by - 80], [x + 70, by - 10]], { fill: '#e8e2d2', key: 'dor' + i, w: 2.5 }); paint(box(x + 15, by - 70, 40, 50), { fill: '#3d4a63', key: 'dw' + i, w: 2 }); }
  paint(box(bx, by, bw, 610), { fill: '#e8e2d2', key: 'facade', w: 3, tex: [{ k: 'pencil', c: '#cfc6b0', al: 0.4, per: 200 }, { k: 'hatch', a: 0.8, gap: 6, al: 0.18, dens: gaShade(bx, by, bx + bw, 860) }] });
  for (let r = 0; r < 4; r++) { ink([[bx, by + 145 + r * 145], [bx + bw, by + 145 + r * 145]], { w: 2.5, color: 'rgba(58,36,23,0.5)', key: 'cor' + r }); for (let c2 = 0; c2 < 5; c2++) { const wx = bx + 50 + c2 * 122, wy = by + 30 + r * 145; if (r === 3 && c2 === 2) continue; paint(box(wx, wy, 66, 96), { fill: '#3d4a63', key: 'w' + r + c2, w: 2.5, tex: [{ k: 'hatch', a: 0.6, gap: 5, al: 0.3, c: '#ffffff' }] }); ink([[wx + 33, wy], [wx + 33, wy + 96]], { w: 2, key: 'wm' + r + c2 }); } }
  paint(box(bx + bw / 2 - 55, 700, 110, 160), { fill: '#6b4a3a', key: 'door25', w: 3, tex: [{ k: 'hatch', a: Math.PI / 2, gap: 8, al: 0.4 }] });
  paint(box(bx + bw / 2 - 90, 860, 180, 16), { fill: '#bdb3a0', key: 'step', w: 2 });
  // the street: cobbles, a lamp post, trees that lose their leaves, an army truck, soldiers coming and going
  paint(box(-40, 860, 2000, 260), { raw: true, fill: '#b7ad98', key: 'cobble', line: false, tex: [{ k: 'stipple', c: '#7d7464', n: 1800, s: 3 }] });
  ink([[-40, 880], [1960, 876]], { w: 3, key: 'kerb' });
  ink([[560, 880], [560, 520]], { w: 8, color: '#2b2b2b', key: 'lamp' }); paint([[530, 520], [590, 520], [575, 470], [545, 470]], { fill: '#2b2b2b', key: 'lampH', w: 2 });
  [[160, 880, 300], [1560, 880, 280]].forEach(([x, y, h], i) => { ink([[x, y], [x, y - h * 0.5]], { w: 10, color: '#5a3d24', key: 'tt' + i }); ink([[x, y - h * 0.4], [x - 60, y - h * 0.8]], { w: 5, color: '#5a3d24', key: 'tb' + i }); ink([[x, y - h * 0.45], [x + 70, y - h * 0.85]], { w: 5, color: '#5a3d24', key: 'tc' + i }); const leaf = 1 - u; if (leaf > 0.05) paint(ellipsePts(x, y - h * 0.75, h * 0.35 * (0.5 + 0.5 * leaf), h * 0.3 * (0.5 + 0.5 * leaf), 0, 24), { fill: mixHex('#7a8f4e', '#c98a3a', u), key: 'tcr' + i, w: 2.5, tex: [{ k: 'cross', c: '#5a4a26', al: 0.35, gap: 5 }] }); });
  if (u > 0.15 && u < 0.8) for (let i = 0; i < 14; i++) { const R = RNG('lf', i), x = R.r(0, 1900) + Math.sin(TT * 2 + i) * 20, y = mod(R.r(0, 400) + TT * 60, 420) + 480; ctx.fillStyle = '#c98a3a'; ctx.fillRect(x, y, 8, 5); }
  if (u > 0.85) for (let i = 0; i < 90; i++) { const R = RNG('sn', i), x = R.r(0, 1920) + Math.sin(TT + i) * 12, y = mod(R.r(0, 1100) + TT * 50, 1100); ctx.fillStyle = 'rgba(255,255,255,0.9)'; ctx.beginPath(); ctx.arc(x, y, R.r(3, 6), 0, TAU); ctx.fill(); }
  gaTruck(1560, 950, 260, { key: 't25' });
  const walk = (TT - s.start) * 2.6;
  gaFigure(mod(1300 - (TT - s.start) * 40, 900) + 600, 900, 200, { face: -1, pose: gaPose('walk', walk), key: 'w25a' });
  gaFigure(mod(400 + (TT - s.start) * 34, 900) + 300, 905, 200, { face: 1, pose: gaPose('walk', walk + 1), key: 'w25b' });
  gaLuxCal(70, 300, u);
  gaDefer(() => gaNote(["Luxembourg's government:", "more than 1/3 of the unit's", '22 missions were in Luxembourg'], 1290, 40, 28, { t: gaAt(s, 0.55, 5.0, 1e9, 3.2) }));
  gaTag(s, 'Limpertsberg · Luxembourg City');
  gaCap('most of the unit was housed here, 25 Sept – 22 Dec 1944', gaAt(s, 0.12, 1.0));
}
