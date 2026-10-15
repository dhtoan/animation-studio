// =====================================================================
//  g27 — Bouzonville, March 1945: a quiet night, silhouettes, lines of text. No injury imagery.
//  g32 — Capt. Fred Fox types the official history (Sept 1945); it goes into a National Archives box.
//  g33 — the story goes quiet: a night city whose lights go out, 1945 -> 1985.
//  g35 — a son finds his father's service after his death (illustrative); an oral-history tape plays.
// =====================================================================
function gaQuietLine(str, y, size, at, col = '#e9ecf8') {   // a centred hand-lettered line that writes on (screen space)
  if (TT < at) return;
  gaDefer(() => handText(str, CX - handW(str, size) / 2, y, size, col, { key: 'ql' + str, frac: ev(at, Math.min(2.2, 0.035 * str.length + 0.4)) }));
}
function gaBouzonville(s) {
  darkWorld('bouz', { dust: 150, fill: '#0a0b16' });
  const S = RNG('st27');
  for (let i = 0; i < 60; i++) star4(S.r(20, 1900), S.r(20, 560), S.r(1.5, 4.5) * (0.7 + 0.3 * ((B + i) % 2)), 'rgba(230,234,255,0.7)');
  paint(ellipsePts(1640, 170, 60, 60, 0, 40), { fill: '#b9c0e0', key: 'moon27', line: false });
  paint(ellipsePts(1662, 158, 56, 56, 0, 40), { fill: '#0a0b16', key: 'moon27c', line: false });
  // the horizon: a low ridge, the simulated division's decoys (red, faint), then the men, still, in silhouette
  paint([[-40, 760], [400, 720], [900, 745], [1400, 715], [1960, 740], [1960, 1120], [-40, 1120]], { fill: '#06070e', key: 'ridge', line: C.periD, w: 2, tex: [{ k: 'hatch', a: 0.9, gap: 8, c: C.periD, al: 0.18 }] });
  [[260, 150], [520, 160], [1420, 150], [1680, 150]].forEach(([x, sz], i) => gaTank(x, 735, sz, { dark: true, key: 'bz' + i, fake: 0.6 * ev(gaAt(s, 0.2, 2.0) + i * 0.2, 0.8) }));
  for (let i = 0; i < 7; i++) gaFigure(640 + i * 105, 1000 + (i % 2) * 14, 330 - (i % 3) * 14, { dark: true, face: i < 3 ? 1 : -1, pose: gaPose('rest'), key: 'bzs' + i });
  gaQuietLine('Operation Bouzonville · 11–13 March 1945', 150, 58, gaAt(s, 0.04, 0.5));
  gaQuietLine('the unit simulated the 80th Infantry Division', 240, 46, gaAt(s, 0.18, 2.4));
  gaQuietLine('its costliest operation: 2 killed, 15 wounded', 360, 54, gaAt(s, 0.38, 5.0));
  gaQuietLine('In all, three soldiers of the 23rd were killed in the war, and dozens were wounded.', 470, 40, gaAt(s, 0.62, 9.0, 1e9, 4.0));
}
function gaBouzCam(s, t) { return push(t, s.start + 0.2, s.end, { z: 1.06, p: [960, 700], to: [960, 700] }); }

// ---- g32: the typewriter
const FX = { box: [1360, 560, 440, 300] };
function gaTypewriter(x, y, s, carriage, key) {   // front-ish view; y = the desk line
  paint([[x - s * 0.5, y], [x - s * 0.42, y - s * 0.32], [x + s * 0.42, y - s * 0.32], [x + s * 0.5, y]], { fill: '#2a2a2e', key: key + 'b', w: 3, tex: [{ k: 'hatch', a: 0.7, gap: 5, c: '#55555e', al: 0.4 }] });
  for (let r = 0; r < 4; r++) for (let k = 0; k < 11 - (r % 2); k++) { const kx = x - s * 0.4 + r * s * 0.02 + k * s * 0.075, ky = y - s * 0.07 - r * s * 0.06; paint(ellipsePts(kx, ky, s * 0.026, s * 0.022, 0, 10), { fill: '#e9e4d8', key: key + 'k' + r + k, w: 1.6 }); }
  paint(gaCapsule([x - s * 0.55 + carriage, y - s * 0.38], [x + s * 0.55 + carriage, y - s * 0.38], s * 0.05, 6), { fill: '#1e1e22', key: key + 'pl', w: 2.5 });
  paint(ellipsePts(x - s * 0.6 + carriage, y - s * 0.38, s * 0.04, s * 0.06, 0, 12), { fill: '#b9b5a8', key: key + 'kn', w: 2 });
}
function gaFox(s) {
  woodSurface(-200, -200, W + 200, H + 200, 'desk32');
  gaLamp(80, 720, 190, 'lamp32');
  gaMug(330, 960, 100, 'mug32');
  drawPencil(140, 1010, -0.1, 260, 0.8, 'pen32');
  ctx.save(); ctx.translate(1500, 120); ctx.rotate(0.05); paint(box(0, 0, 230, 260), { fill: '#f6efd9', key: 'cal32', w: 3 }); paint(box(0, 0, 230, 60), { fill: '#7a5434', key: 'cal32h', w: 2.5 }); monoText('SEPT', 50, 44, 34, '#f4f6ff', { key: 'c32m' }); monoText('1945', 30, 190, 72, C.ink, { key: 'c32y' }); ctx.restore();
  // the sheet in the machine, typed line by line; the carriage moves with the text
  const lines = ['OFFICIAL HISTORY', '23rd HEADQUARTERS', 'SPECIAL TROOPS', '', 'Capt. Fred Fox', 'September 1945'];
  const t0 = gaAt(s, 0.05, 0.5), per = Math.min(0.09, Math.max(0.04, s.dur * 0.45 / 80)), cw = monoW(34);
  let tt = t0, cur = 0; const counts = lines.map((l) => { const c = Math.floor(clamp((TT - tt) / (per * Math.max(1, l.length))) * l.length); if (TT >= tt) cur = c; tt += per * Math.max(1, l.length) + 0.2; return c; });
  const carriage = -cur * cw * 0.5 + 120;
  ctx.save(); ctx.translate(carriage, 0);
  paint(box(560, 130, 520, 520), { fill: '#fbf7ec', key: 'sheet32', w: 2.5, tex: [{ k: 'pencil', c: '#e8dcc0', al: 0.35, per: 200 }] });
  lines.forEach((l, i) => { if (counts[i] > 0) monoText(l, 610, 210 + i * 62, 34, C.ink, { key: 'fx' + i, count: counts[i] }); });
  ctx.restore();
  gaTypewriter(820, 880, 640, carriage, 'tw');
  // the typist's hands on the keys (illustrative)
  for (const [k, dx] of [[0, -150], [1, 150]]) { const bob = ((B + k) % 3) * 6; paint(ellipsePts(820 + dx, 760 + bob, 70, 40, 0, 20), { fill: GA.skin, key: 'hand' + k, w: 2.5, tex: [{ k: 'hatch', a: 0.7, gap: 4, al: 0.25 }] }); for (let f = 0; f < 4; f++) ink([[790 + dx + f * 20, 780 + bob], [784 + dx + f * 22, 812 + bob]], { w: 9, color: GA.skin, key: 'fg' + k + f }); paint(gaCapsule([820 + dx + k * 60 - 30, 740 + bob], [820 + dx * 2.2, 1130], 50, 6), { fill: '#6b6346', key: 'sl' + k, w: 2.5, tex: [{ k: 'hatch', a: 0.9, gap: 5, al: 0.35 }] }); }
  // the finished pages, then the archive box
  const pages = Math.floor(clamp((TT - t0) / Math.max(1, s.dur * 0.55)) * 8);
  for (let i = 0; i < pages; i++) paint(box(1400 + (i % 2) * 4, 520 - i * 8, 360, 40), { fill: '#fbf7ec', key: 'pg' + i, w: 1.8 });
  const kb = popS(gaAt(s, 0.62, 6.0, 1e9, 3.0));
  if (kb > 0) {
    const [x, y, w, h] = FX.box;
    ctx.save(); ctx.translate(x + w / 2, y + h); ctx.scale(kb, kb); ctx.translate(-(x + w / 2), -(y + h));
    paint(box(x, y, w, h), { fill: '#c9a46a', key: 'abox', w: 3, tex: [{ k: 'pencil', c: '#a8834a', al: 0.4, per: 90 }, { k: 'hatch', a: 0.8, gap: 6, al: 0.2, dens: gaShade(x, y, x + w, y + h) }] });
    paint(box(x + 30, y + 40, w - 60, 170), { fill: '#f6efd9', key: 'alab', w: 2 });
    monoText('NATIONAL ARCHIVES', x + 50, y + 90, 30, C.ink, { key: 'na1' }); monoText('College Park, Md.', x + 50, y + 140, 28, '#5a4a3a', { key: 'na2' }); monoText('Record Group 407', x + 50, y + 186, 28, '#5a4a3a', { key: 'na3' });
    ctx.restore();
  }
  gaTag(s, 'September 1945');
  gaCap('Capt. Fred Fox writes the unit’s official history', gaAt(s, 0.08, 0.8));
}

// ---- g33: the night city
const CITY = (() => { const R = RNG('city'), B0 = []; let x = -20; while (x < 1960) { const w = R.r(120, 230), h = R.r(260, 620); B0.push([x, 900 - h, w, h]); x += w + R.r(6, 30); } return B0; })();
const CITY_MID = CITY.reduce((a, b) => (Math.abs(b[0] + b[2] / 2 - 960) < Math.abs(a[0] + a[2] / 2 - 960) ? b : a));
function gaCity(s) {
  darkWorld('city33', { dust: 120 });
  const S = RNG('st33'); for (let i = 0; i < 50; i++) star4(S.r(20, 1900), S.r(20, 380), S.r(1.5, 4) * (0.7 + 0.3 * ((B + i) % 2)), 'rgba(230,234,255,0.75)');
  paint(ellipsePts(1700, 150, 70, 70, 0, 40), { fill: C.peri, key: 'moon33', line: C.white, w: 2, tex: [{ k: 'cross', c: C.periD, al: 0.4, gap: 6 }] });
  const t0 = gaAt(s, 0.12, 1.2), t1 = gaAt(s, 0.72, 8.0, 1e9, 3.0), prog = clamp((TT - t0) / (t1 - t0)), relit = TT >= gaAt(s, 0.8, 9.0, 1e9, 2.4);
  let wi = 0;
  CITY.forEach(([x, y, w, h], i) => {
    paint(box(x, y, w, h + 30), { fill: '#0d0f22', key: 'bd' + i, line: C.periD, w: 2, tex: [{ k: 'hatch', a: 1.1, gap: 8, c: C.periD, al: 0.2 }] });
    for (let r = 0; r * 70 + 50 < h - 40; r++) for (let c = 0; c * 46 + 30 < w - 20; c++) {
      const id = wi++, order = RNG('win', id).f(), lit = order > prog || (relit && id === 37);
      ctx.fillStyle = lit ? (id === 37 && relit ? '#ffe7a0' : '#f0c55a') : '#1a1d38'; ctx.fillRect(x + 22 + c * 46, y + 40 + r * 70, 24, 36);
    }
  });
  paint(box(-40, 930, 2000, 200), { raw: true, fill: '#07080f', key: 'street33', line: false, tex: [{ k: 'hatch', a: 0.05, gap: 9, c: C.periD, al: 0.2 }] });
  ink([[300, 935], [300, 700]], { w: 7, color: C.periD, key: 'sl33' }); paint(ellipsePts(300, 694, 22, 12, 0, 14), { fill: prog < 0.5 ? '#f0c55a' : '#1a1d38', key: 'sl33b', w: 2, line: C.periD });
  // CLASSIFIED: an ink stamp (navy, not red: the classification was real)
  const ks = popS(gaAt(s, 0.1, 0.8));
  if (ks > 0) gaDefer(() => { ctx.save(); ctx.translate(960, 300); ctx.rotate(-0.08); ctx.scale(ks, ks); ink(rrectPts(-330, -70, 660, 140, 14), { closed: true, w: 6, color: 'rgba(200,208,240,0.9)', key: 'cls' }); monoText('CLASSIFIED', -270, 30, 92, 'rgba(200,208,240,0.9)', { key: 'clst' }); ctx.restore(); });
  // August 1945: a newspaper blows along the street
  const tn = gaAt(s, 0.28, 3.0), nx = lerp(-200, 1100, clamp((TT - tn) / Math.max(2, s.dur * 0.4)));
  if (TT >= tn) { ctx.save(); ctx.translate(nx, 990 + Math.sin(TT * 4) * 10); ctx.rotate(Math.sin(TT * 2) * 0.15); paint(box(-110, -70, 220, 140), { fill: '#d9d4c4', key: 'np', w: 2.5 }); paint(box(-90, -55, 180, 26), { fill: '#3a3a3a', key: 'nph', w: 0, line: false }); for (let i = 0; i < 4; i++) ink([[-90, -10 + i * 18], [80, -10 + i * 18]], { w: 4, color: '#777', key: 'npl' + i }); ctx.restore(); gaDefer(() => inkCard('Aug 1945: a few newspaper articles', 520, 820, 34, { rot: -0.02, s: popS(tn + 0.3) })); }
  if (relit) gaDefer(() => inkCard('April 1985: Smithsonian magazine', 1400, 820, 36, { rot: 0.02, s: popS(gaAt(s, 0.8, 9.0, 1e9, 2.4)) }));
  const year = relit ? 1985 : 1945 + Math.floor(prog * 39);
  gaTag(s, 'the records: classified · ' + year);
  gaCap('Then the story went quiet.', gaAt(s, 0.04, 0.4), { size: 50 });
}

// ---- g35: the family scene and the oral-history tape
function gaReelDeck(x, y, s, key, playing) {
  paint(box(x, y, s, s * 0.62), { fill: '#6e5a44', key: key + 'b', w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 6, al: 0.3 }] });
  paint(box(x + s * 0.05, y + s * 0.05, s * 0.9, s * 0.38), { fill: '#d8d2c2', key: key + 'f', w: 2.5 });
  for (const k of [0, 1]) { const cx = x + s * (0.27 + 0.46 * k), cy = y + s * 0.24, r = s * 0.16, a = playing ? TT * 3 : 0; paint(ellipsePts(cx, cy, r, r, 0, 28), { fill: '#3a3530', key: key + 'r' + k, w: 2.5 }); for (let j = 0; j < 3; j++) { const q = a + j * TAU / 3; ink([[cx, cy], [cx + Math.cos(q) * r * 0.85, cy + Math.sin(q) * r * 0.85]], { w: 4, color: '#bcb6a8', key: key + 'sp' + k + j }); } }
  ink([[x + s * 0.27, y + s * 0.4], [x + s * 0.5, y + s * 0.47], [x + s * 0.73, y + s * 0.4]], { w: 3, color: '#3a3530', key: key + 'tape' });
  for (let i = 0; i < 4; i++) paint(box(x + s * (0.12 + i * 0.2), y + s * 0.5, s * 0.12, s * 0.07), { fill: '#e9e4d8', key: key + 'btn' + i, w: 2 });
}
function gaFamily(s) {
  paint(box(-300, -200, W + 600, 1000), { raw: true, fill: '#d8c8a8', key: 'wp35', line: false, tex: [{ k: 'hatch', a: Math.PI / 2, gap: 40, c: '#b9a682', al: 0.5, w: 3 }, { k: 'pencil', c: '#c8b690', al: 0.35, per: 400 }] });
  paint(box(80, 120, 380, 300), { fill: '#1d2150', key: 'win35', w: 4, tex: [{ k: 'hatch', a: 0, gap: 12, c: '#0c0d1c', al: 0.5 }] }); ink([[270, 120], [270, 420]], { w: 5, key: 'wb35' }); ink([[80, 270], [460, 270]], { w: 5, key: 'wc35' });
  woodSurface(-300, 800, W + 300, H + 200, 'floor35');
  gaLamp(1040, 640, 160, 'lamp35');
  // the table and the box of the father's things (illustrative)
  paint(box(180, 620, 760, 40), { fill: '#8a5a34', key: 'tbl', w: 3 }); ink([[220, 660], [220, 880]], { w: 12, color: '#6a4424', key: 'tl1' }); ink([[900, 660], [900, 880]], { w: 12, color: '#6a4424', key: 'tl2' });
  paint([[300, 620], [300, 480], [600, 480], [600, 620]], { fill: '#c9a46a', key: 'cbox', w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 6, al: 0.25 }] });
  paint([[300, 480], [260, 420], [560, 420], [600, 480]], { fill: '#b8925a', key: 'flap', w: 3 });
  monoText('DAD', 400, 570, 40, C.ink, { key: 'dad' });
  [[640, 600, -0.1], [700, 610, 0.08]].forEach(([x, y, r], i) => { ctx.save(); ctx.translate(x, y); ctx.rotate(r); paint(box(0, -40, 150, 90), { fill: '#f2ead8', key: 'env' + i, w: 2 }); ink([[0, -40], [75, 10], [150, -40]], { w: 2, key: 'envf' + i }); ctx.restore(); });
  ctx.save(); ctx.translate(780, 520); ctx.rotate(0.06); paint(box(0, 0, 120, 150), { fill: '#7a5434', key: 'frm', w: 3 }); paint(box(15, 15, 90, 120), { fill: '#d9d2c0', key: 'frmi', w: 2 }); paint(ellipsePts(60, 60, 22, 26, 0, 14), { fill: '#a39a86', key: 'frmh', w: 1.5, line: false }); paint([[25, 135], [35, 95], [85, 95], [95, 135]], { fill: '#a39a86', key: 'frmb', w: 1.5, line: false }); ctx.restore();
  gaFigure(130, 900, 470, { face: 1, head: 'hair', hair: '#7a6a5a', jacket: '#5b6b7a', trous: '#3e4250', pose: gaPose('read'), key: 'son' });
  paint(box(225, 520, 80, 60), { fill: '#f2ead8', key: 'letter', w: 2 });
  gaLabel('illustrative', 600, 960, 22);
  gaNote(['AP: Capt. Oscar Seale’s son', 'learned of his service only', 'after his father’s death in 2001'], 520, 175, 28, { t: gaAt(s, 0.1, 0.8) });
  // the sideboard and the oral-history tape
  paint(box(1240, 560, 600, 320), { fill: '#7a5434', key: 'sb35', w: 3, tex: [{ k: 'hatch', a: 0, gap: 8, al: 0.3 }] });
  const tp = gaAt(s, 0.5, 9.0, 1e9, 6.0);
  gaReelDeck(1300, 340, 420, 'deck', TT >= tp);
  if (TT >= tp) for (let k = 0; k < 4; k++) { const r = 30 + mod((TT - tp) * 80 + k * 40, 160); ink(arcPts(1730, 430, r, -0.8, 0.8, 14), { w: 3, color: C.ink, alpha: clamp(1 - r / 190), key: 'sw' + k, amt: 1 }); }
  gaNote(['LIBRARY OF CONGRESS', 'Veterans History Project', 'interview: Elmer Mellebrand', 'decoys · sound deception'], 1230, 175, 28, { t: tp + 0.4 });
  gaCap('Many veterans stayed quiet for decades', gaAt(s, 0.04, 0.5), { y: 1000 });
}
function gaFamilyCam(s, t) {
  const A = camOf({ z: 1.3, p: [740, 560], to: [960, 540] }), Bc = camOf({ z: 1.3, p: [1180, 560], to: [960, 540] }), tp = gaAt(s, 0.5, 9.0, 1e9, 6.0);
  return camMix(A, Bc, EZ.io(clamp((t - tp + 1.2) / 1.4)));
}
