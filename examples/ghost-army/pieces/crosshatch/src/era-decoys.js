// =====================================================================
//  g13 — an inflatable decoy tank fills in a field (pump, red hose, the gun rises).
//  g14 — the same tank lifted and carried by four soldiers; French cyclists stare (oral history, labelled).
// =====================================================================
const DC = { tank13: [960, 860, 880], tank14: [1180, 760, 600] };
const dcInflate = (s) => [gaAt(s, 0.1, 1.2), gaAt(s, 0.6, 5.5, 1e9, 3.0)];
function gaInflate(s) {
  const [i0, i1] = dcInflate(s), ph = (TT - s.start) * 3.4;
  paperSheet('sky13', { fill: GA.sky, ruled: false });
  [[300, 150, 190, 40], [1100, 110, 230, 46], [1700, 190, 170, 36]].forEach(([x, y, w, h], i) => gaCloud(x + Math.sin(TT * 0.2 + i) * 30, y, w, h, 'c13' + i));
  gaBirds(4, 230, 'b13');
  paint([[-40, 640], ...Array.from({ length: 22 }, (_, i) => [i * 95, 596 - 22 * Math.abs(Math.sin(i * 2.3))]), [1960, 640], [1960, 700], [-40, 700]], { fill: '#8f9a62', key: 'hedge', w: 2.5, tex: [{ k: 'cross', c: '#4f5a2e', al: 0.35, gap: 5 }] });
  [[120, 640, 230], [1530, 650, 260], [1870, 640, 200]].forEach(([x, y, h], i) => gaRoundTree(x, y, h, 'rt13' + i));
  paint(box(-40, 660, 2000, 460), { raw: true, fill: GA.field, key: 'field', line: false, tex: [{ k: 'pencil', c: GA.fieldD, al: 0.4, a: -0.2, len: 22, per: 500 }, { k: 'hatch', a: 0.05, gap: 14, al: 0.12, dash: [30, 120] }] });
  // the back of the field: tents, a gun under a camouflage net, a decoy truck already standing, a heap being unrolled
  gaTent(330, 700, 200, 120, 'tent1'); gaTent(520, 705, 160, 100, 'tent2');
  gaGun(760, 708, 150, { key: 'g13' });
  const net = [[650, 712], [690, 610], [800, 585], [880, 640], [890, 712]];
  paint(net, { fill: 'rgba(95,105,60,0.75)', key: 'net', w: 2, tex: [{ k: 'cross', c: '#2f3a1c', al: 0.6, gap: 9 }] });
  gaTruck(1340, 712, 170, { key: 't13' });
  gaTank(1700, 716, 200, { inflate: 0.08, key: 'heap2' });
  gaFigure(1610, 718, 130, { face: 1, pose: gaPose('walk', ph * 0.6), key: 'bk1' }); gaFigure(1800, 718, 130, { face: -1, pose: gaPose('walk', ph * 0.6 + 1), key: 'bk2' });
  gaCrate(1080, 730, 70, 50, 'cr1'); gaCrate(1150, 730, 50, 40, 'cr2');
  // the decoy (the constant): heap -> filled, in pump strokes; the gun rises last
  const [tx, ty, ts] = DC.tank13, inf = clamp((TT - i0) / (i1 - i0)), stepIn = Math.floor(inf * 12) / 12 * 0.35 + inf * 0.65;
  ctx.save(); trace(ellipsePts(tx + 40, ty + 10, ts * 0.55, 36, 0, 30), true); ctx.fillStyle = 'rgba(58,36,23,0.18)'; ctx.fill(); ctx.restore();
  const tk = gaTank(tx, ty, ts, { inflate: stepIn, gun: ev(i1 - 0.8, 1.0), valve: true, key: 'decoy' });
  // the pump cart, the red hose (what makes it fake), the pumping soldier, a second steadying the hull
  const px = 380, py = 930;
  paint(rrectPts(px - 80, py - 130, 160, 130, 10), { fill: '#7c6f58', key: 'pump', w: 3, tex: [{ k: 'cross', al: 0.4, gap: 5 }] });
  ink([[px, py - 130], [px, py - 190 + 20 * Math.sin(ph)]], { w: 8, color: '#3b3a33', key: 'pr' }); ink([[px - 40, py - 190 + 20 * Math.sin(ph)], [px + 40, py - 190 + 20 * Math.sin(ph)]], { w: 8, color: '#3b3a33', key: 'ph' });
  [[-45], [45]].forEach(([d], i) => paint(ellipsePts(px + d, py, 32, 32, 0, 16), { fill: GA.track, key: 'pw' + i, w: 2.5 }));
  ink([[px + 80, py - 70], [px + 260, py + 20], [(px + tk.valve[0]) / 2 + 120, py], tk.valve], { w: 7, color: GA.fake, key: 'hose', amt: 3 });
  const pumping = TT >= i0 - 0.3 && inf < 1;
  gaFigure(px - 140, py + 70, 360, { face: 1, pose: pumping ? gaPose('pump', ph * 1.8) : gaPose('stand'), key: 'pumper' });
  if (pumping) for (let i = 0; i < 3; i++) { const u = mod(TT * 2.2 + i / 3, 1), [vx, vy] = tk.valve; ctx.fillStyle = `rgba(212,56,44,${0.6 * (1 - u)})`; ctx.beginPath(); ctx.arc(vx - 20 - u * 60, vy - 30 - u * 40, 6 + u * 10, 0, TAU); ctx.fill(); }
  gaFigure(tx + ts * 0.6, 980, 350, { face: -1, pose: inf < 1 ? gaPose('point') : gaPose('stand'), key: 'helper' });
  gaTag(s, 'Inflatable rubber decoys');
  gaDefer(() => gaNote(['tanks · artillery', 'trucks · aircraft'], 1300, 60, 34, { t: gaAt(s, 0.64, 6.0, 1e9, 2.6) }));
  gaCap('some were made by U.S. Rubber and Goodyear', gaAt(s, 0.74, 7.5, 1e9, 2.2));
}
function gaInflateCam(s, t) { const [i0, i1] = dcInflate(s); return push(t, i0 + 0.5, i1 - 0.5, { z: 1.12, p: [960, 760], to: [960, 640] }, s.end - 1.6, s.end - 0.75); }

const dcLift = (s) => gaAt(s, 0.12, 1.0, 2.0);
function dcCarry(s) {   // [x offset, lift height] of the carried tank at TT
  const t1 = dcLift(s), up = 195 * EZ.io(clamp((TT - t1) / 1.2)), walk = Math.max(0, TT - t1 - 1.2);
  return [-walk * 22, up + (walk > 0 ? Math.sin(walk * 5.9) * 5 : 0), walk];
}
function gaLift(s) {
  paperSheet('sky14', { fill: '#ece4cc', ruled: false });
  [[400, 130, 200, 40], [1300, 170, 240, 46]].forEach(([x, y, w, h], i) => gaCloud(x + Math.sin(TT * 0.2 + i) * 30, y, w, h, 'c14' + i));
  gaBirds(3, 200, 'b14', { v: 30 });
  paint([[-40, 560], [400, 520], [900, 560], [1400, 510], [1960, 550], [1960, 700], [-40, 700]], { fill: '#a7b07a', key: 'hills', w: 2.5, tex: [{ k: 'pencil', c: '#7f8a52', al: 0.4, per: 300 }] });
  // a farmhouse and a haystack on the hill, poplars along the road
  paint(box(1500, 430, 280, 160), { fill: '#e8dcc0', key: 'farm', w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 5, al: 0.2, dens: gaShade(1500, 430, 1780, 590) }] });
  paint([[1480, 440], [1640, 340], [1800, 440]], { fill: '#a4553a', key: 'roof', w: 3, tex: [{ k: 'hatch', a: 0.3, gap: 6, al: 0.4 }] });
  [[1540, 480], [1700, 480]].forEach(([x, y], i) => paint(box(x, y, 50, 60), { fill: '#3d4a63', key: 'fw' + i, w: 2 })); paint(box(1615, 510, 50, 80), { fill: '#6b4a3a', key: 'fd', w: 2 });
  paint(arcPts(1880, 600, 90, Math.PI, TAU, 14), { fill: '#d9b85a', key: 'hay', w: 2.5, tex: [{ k: 'hatch', a: 1.2, gap: 4, c: '#9a7a2a', al: 0.5 }] });
  for (let i = 0; i < 6; i++) gaPoplar(100 + i * 260, 600, 300, 'pop' + i);
  paint(box(-40, 680, 2000, 440), { raw: true, fill: '#d8c79a', key: 'road', line: false, tex: [{ k: 'pencil', c: '#b9a46e', al: 0.45, per: 350, a: 0.05, len: 30 }] });
  ink([[-40, 690], [1960, 684]], { w: 3, key: 'roadE' });
  for (let i = 0; i < 2; i++) ink([[-40, 820 + i * 120], [1960, 800 + i * 120]], { w: 3, color: 'rgba(120,95,60,0.45)', key: 'rut' + i, amt: 3 });
  // the second cyclist, small, passing along the far side of the road
  gaCyclist(mod(-200 + (TT - s.start) * 70, 2300) - 100, 720, 140, { key: 'cy2', k: TT * 7, coat: '#5a6b7a', hat: '#5b3a2a' });
  // four soldiers lift the tank and carry it: two behind it, the tank, two in front
  const [tx, ty, ts] = DC.tank14, [wx, up, walk] = dcCarry(s), lifting = TT >= dcLift(s);
  const pose = (k) => (lifting ? gaPose('lift', walk > 0 ? walk * 5.9 + k : 0) : gaPose('stand'));
  [[-0.13, 0], [0.4, 2]].forEach(([u, k]) => gaFigure(tx + wx + u * ts, 880, 285, { face: -1, pose: pose(k), jacket: GA.khakiD, trous: '#4e4834', key: 'sb' + k }));
  gaTank(tx + wx, ty - up, ts, { key: 'decoy14' });
  [[-0.38, 1], [0.15, 3]].forEach(([u, k]) => gaFigure(tx + wx + u * ts, 905, 300, { face: -1, pose: pose(k), key: 'sf' + k }));
  // the witness: a cyclist rides in, slows, turns to stare
  const tb = gaAt(s, 0.16, 1.4, 3.0), cx = lerp(-260, 400, EZ.o3(ev(tb, 3.0)));
  gaCyclist(cx, 1010, 300, { key: 'cyc', k: (TT - tb) * 6 * (1 - EZ.o3(ev(tb, 3.0))) + TT * 0.4, look: ev(tb + 2.4, 0.4) });
  if (TT > tb + 2.8) { const k = popS(tb + 2.8); ctx.save(); ctx.translate(cx + 60, 650); ctx.scale(k, k); handText('?!', 0, 0, 80, C.ink, { key: 'qq' }); ctx.restore(); }
  gaDefer(() => gaNote(['ORAL HISTORY', 'ILLUSTRATIVE RECREATION'], 70, 50, 30, { t: s.start + 0.1, per: 0.03 }));
  gaCap('French cyclists saw soldiers lift a "40-ton Sherman"', gaAt(s, 0.3, 3.0));
}
