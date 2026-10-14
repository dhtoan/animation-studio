// =====================================================================
//  g01 / g03 — the Rhine at night. g01: German officers watch the far bank. g03: the same view; the decoys are
//  outed in red, the camera pushes in on them, a sound truck plays recorded engines.
// =====================================================================
const RH = {
  moon: [1600, 165, 92],
  tanks: [[680, 190], [1080, 190], [1480, 190], [1760, 180]], guns: [[880, 130]], spk: [1290, 150], bank: 640,
};
const gaPoseMix = (a, b, u) => { const o = {}; for (const k of ['hn', 'hf', 'fn', 'ff']) o[k] = [lerp(a[k][0], b[k][0], u), lerp(a[k][1], b[k][1], u)]; o.bob = lerp(a.bob ?? 0, b.bob ?? 0, u); o.lean = lerp(a.lean ?? 0, b.lean ?? 0, u); return o; };
const rhReveal = (s) => gaAt(s, 0.12, 1.0, 2.6);
function gaRhine(s, reveal) {
  darkWorld(reveal ? 'rhineR' : 'rhine', { dust: 200 });
  const S = RNG('stars');
  for (let i = 0; i < 70; i++) star4(S.r(20, 1900), S.r(20, 470), S.r(2, 6) * (0.7 + 0.3 * ((B + i) % 2)), 'rgba(244,246,255,0.85)');
  const [mx, my, mr] = RH.moon;
  paint(ellipsePts(mx, my, mr, mr, 0, 64), { fill: C.peri, key: 'moon', line: C.white, w: 3, tex: [{ k: 'cross', c: C.periD, al: 0.45, gap: 6, dens: (px, py) => clamp((px - mx + py - my) / mr + 0.4) }] });
  for (let i = 0; i < 4; i++) { const cx = mod(250 + i * 560 + TT * 12, 2400) - 240; gaCloud(cx, 120 + (i % 2) * 110, 210, 40, 'cl' + i, { fill: '#1d2150', line: 'rgba(200,208,240,0.45)', hc: C.periD }); }
  // the far (west) bank: a village and a tree line, then the "two divisions"
  const tree = [[-40, 600]]; for (let i = 0; i <= 26; i++) tree.push([i * 76, 548 - 24 * Math.abs(Math.sin(i * 1.7)) - (i % 3) * 9]); tree.push([1960, 600]);
  paint([...tree, [1960, 640], [-40, 640]], { fill: GA.land, key: 'trees', line: C.periD, w: 2, tex: [{ k: 'hatch', a: 1.2, gap: 6, c: C.periD, al: 0.3 }] });
  [[300, 70, 60], [380, 60, 48], [520, 80, 70], [1180, 66, 54], [1260, 50, 44]].forEach(([x, w, h], i) => paint([[x - w / 2, 600], [x - w / 2, 600 - h], [x, 600 - h - w * 0.45], [x + w / 2, 600 - h], [x + w / 2, 600]], { fill: '#0b0d22', key: 'hs' + i, line: C.periD, w: 2, tex: [{ k: 'hatch', a: 0.7, gap: 6, c: C.periD, al: 0.25 }] }));
  paint([[446, 600], [446, 480], [460, 420], [474, 480], [474, 600]], { fill: '#0b0d22', key: 'spire', line: C.periD, w: 2 });
  for (let i = 0; i < 10; i++) { const x = 40 + i * 205; ink([[x, 640], [x + 2, 556]], { w: 3, color: C.periD, key: 'tp' + i }); ink([[x - 14, 566], [x + 16, 566]], { w: 2, color: C.periD, key: 'tpa' + i }); }
  ink(Array.from({ length: 21 }, (_, i) => [i * 100 - 20, 568 + Math.sin(i * 1.1) * 4]), { w: 1.4, color: 'rgba(124,134,196,0.6)', key: 'wire' });
  paint(box(-40, 600, 2000, 50), { raw: true, fill: '#151838', key: 'bankW', line: false, tex: [{ k: 'hatch', a: 0.05, gap: 7, c: C.periD, al: 0.3 }] });
  const rv = rhReveal(s), on = reveal && TT >= rv, k = (i) => (on ? clamp((TT - rv) / 0.6 - i * 0.15) : 0);
  RH.tanks.forEach(([x, sz], i) => gaTank(x, RH.bank, sz, { dark: true, key: 'wt' + i, fake: k(i) }));
  RH.guns.forEach(([x, sz], i) => gaGun(x, RH.bank, sz, { dark: true, key: 'wg' + i, fake: k(i + 1) }));
  if (!reveal) gaTruck(mod(1500 - (TT - s.start) * 40, 2300) - 150, RH.bank + 6, RH.spk[1], { dark: true, key: 'drv' });
  else {
    const [sx, ss] = RH.spk, sp = clamp((TT - gaAt(s, 0.36, 3.0)) / 0.4);
    gaTruck(sx, RH.bank + 6, ss, { dark: true, key: 'spk', fake: k(2) });
    // the loudspeaker on the cab roof and its sound (red: the engines are a recording)
    paint(ellipsePts(sx + ss * 0.3, RH.bank - ss * 0.52, ss * 0.06, ss * 0.09, 0, 12), { fill: GA.sil, key: 'horn', line: C.peri, w: 2 });
    if (sp > 0) for (let j = 0; j < 4; j++) { const r = 20 + mod(TT * 70 + j * 30, 120); ink(arcPts(sx + ss * 0.36, RH.bank - ss * 0.52, r, -0.9, 0.9, 14), { w: 3, color: GA.fakeA, alpha: clamp(1 - r / 140) * sp, key: 'arc' + j, amt: 1 }); }
  }
  // the river: hatched water, the moon's broken reflection, mist
  paint(box(-40, 648, 2000, 240), { raw: true, fill: GA.water, key: 'river', line: false, tex: [{ k: 'hatch', a: 0.02, gap: 9, c: '#3b4590', al: 0.6, dash: [40, 160], skip: [10, 60] }] });
  for (let i = 0; i < 12; i++) { const R = RNG('refl', i), y = 668 + i * 17, w = 150 - i * 7 + R.r(0, 40), x = mx - w / 2 + Math.sin(TT * 2.2 + i) * 18; ink([[x, y], [x + w, y + R.n(2)]], { w: 3, color: 'rgba(200,208,240,0.55)', key: 'rf' + i, amt: 1.2 }); }
  [[880, 760], [940, 772], [1000, 784], [1060, 796]].forEach(([x, y], i) => { paint(box(x, y - 70, 18, 90), { fill: GA.sil, key: 'pile' + i, line: C.periD, w: 2 }); ink([[x - 10, y + 20 + Math.sin(TT * 2 + i) * 2], [x + 28, y + 20]], { w: 2, color: 'rgba(200,208,240,0.5)', key: 'pr' + i }); });
  paint([[560, 840], [800, 840], [770, 872], [590, 872]], { fill: GA.sil, key: 'boat', line: C.periD, w: 2.5, tex: [{ k: 'hatch', a: 0.7, gap: 6, c: C.periD, al: 0.3 }] }); ink([[800, 846], [880, 760]], { w: 2, color: C.periD, key: 'rope' });
  for (let i = 0; i < 3; i++) { const x = mod(i * 700 + TT * 22, 2600) - 400; ink([[x, 700 + i * 50], [x + 520, 704 + i * 50]], { w: 14, color: 'rgba(150,160,220,0.10)', key: 'mist' + i, amt: 4 }); }
  // the near (east) bank: a knoll on the left, sandbags and wire on the right, reeds
  paint([[-40, 1120], [-40, 820], [260, 800], [560, 812], [780, 880], [1960, 900], [1960, 1120]], { fill: '#0a0b18', key: 'bankE', line: C.periD, w: 2.5, tex: [{ k: 'hatch', a: 0.9, gap: 7, c: C.periD, al: 0.22 }] });
  gaSandbags(1230, 935, 7, 70, 'sb', { fill: '#141733', line: C.periD, hc: C.periD });
  gaFence(860, 1960, 960, 90, 'fe', { c: C.periD, wc: 'rgba(150,164,230,0.7)', w: 4 });
  for (let i = 0; i < 22; i++) { const R = RNG('reed', i), x = R.r(700, 1900), h = R.r(40, 110); ink([[x, 905], [x + Math.sin(TT * 1.4 + i) * 8 + R.n(10), 905 - h]], { w: 2.4, color: C.periD, key: 'rd' + i, amt: 1 }); }
  // the watchers (g01 and the start of g03): one with binoculars, one pointing across
  const gu = EZ.io(clamp((TT - gaAt(s, 0.12, 0.8, 2.0)) / 0.7));
  gaFigure(250, 810, 440, { dark: true, coat: true, head: 'cap', face: 1, pose: gaPoseMix(gaPose('stand'), gaPose('binoc'), gu), binoc: gu > 0.7, key: 'o1' });
  const pu = EZ.io(clamp((TT - gaAt(s, 0.35, 2.5, 5.0)) / 0.6)) * (1 - EZ.io(clamp((TT - gaAt(s, 0.7, 6, 9)) / 0.6)));
  gaFigure(470, 815, 410, { dark: true, coat: true, head: 'cap', face: 1, pose: gaPoseMix(gaPose('stand'), gaPose('point'), pu), key: 'o2' });
  if (!reveal) {
    gaTag(s, 'March 1945 · the Rhine');
    gaCap('German commanders watch the west bank of the Rhine', gaAt(s, 0.08, 0.6, 1.5));
  } else {
    gaTag(s, TT < rv ? 'March 1945 · the Rhine' : 'Viersen, March 1945', s.start + 0.15);
    gaCap('But those divisions were not there.', rv + 0.3, { size: 54 });
    const nt = gaAt(s, 0.45, 4.0);
    gaDefer(() => gaNote(['tanks: rubber', 'engines: recorded'], 1400, 110, 34, { t: nt, colors: [GA.fake, GA.fake] }));
  }
}
function gaRhineCam(s, t, reveal) {
  if (!reveal) return push(t, s.start + 0.3, s.end, { z: 1.12, p: [1000, 620], to: [960, 560] });
  const rv = rhReveal(s);
  return push(t, rv + 0.2, rv + 1.8, { z: 2.05, p: [1230, 600], to: [960, 500] });
}
