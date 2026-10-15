// =====================================================================
//  g18 — special effects: fake shoulder patches painted on the bench, false markings stencilled on a truck bumper.
//  g19 — the 406th Engineers: a bulldozer lays fake tank tracks, a sentry walks the perimeter, soldiers pose as MPs.
// =====================================================================
const TH = { bumper: [1170, 640, 620, 110], patch: [560, 600, 240], dozer: { x0: 1250, x1: 560, y: 945, s: 440 } };
function gaEffects(s) {
  woodSurface(-200, -200, W + 200, H + 200, 'bench18');
  const tPaint = gaAt(s, 0.06, 0.5), tSt = gaAt(s, 0.4, 4.5), tS0 = gaAt(s, 0.45, 5.0), tS1 = gaAt(s, 0.62, 6.5), tBett = gaAt(s, 0.68, 7.5, 1e9, 2.5);
  // bench life: paint pots, a rag, a stack of stencil sheets, brushes
  [[730, 230, '#d9b23c'], [850, 300, '#3c5a8c'], [730, 380, '#7c6a8a']].forEach(([x, y, c], i) => { paint(ellipsePts(x, y, 55, 55, 0, 24), { fill: '#b9b5a8', key: 'pot' + i, w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 5, al: 0.3 }] }); paint(ellipsePts(x, y, 44, 44, 0, 20), { fill: c, key: 'pc' + i, w: 2 }); });
  paint([[60, 900], [200, 860], [280, 930], [230, 1010], [90, 1000]], { fill: '#d8cfc0', key: 'rag', w: 2.5, tex: [{ k: 'hatch', a: 0.4, gap: 5, al: 0.3 }] });
  for (let i = 0; i < 3; i++) paint(box(720 + i * 10, 760 - i * 12, 300, 200), { fill: '#c9b58c', key: 'sts' + i, w: 2, tex: [{ k: 'hatch', a: 0.8, gap: 6, al: 0.2 }] });
  [[1080, 860, -0.4], [980, 960, 0.2]].forEach(([x, y, r], i) => { ctx.save(); ctx.translate(x, y); ctx.rotate(r); paint(rrectPts(0, -7, 240, 14, 6), { fill: '#a46a3a', key: 'b18' + i, w: 2 }); paint([[0, -10], [-50, 0], [0, 10]], { fill: ['#d9b23c', '#3c5a8c'][i], key: 'bt' + i, w: 2 }); ctx.restore(); });
  // the patches: two done, one being painted (brush follows), all three outed in red later
  const [px, py, ps] = TH.patch, red = ev(tBett + 0.4, 0.5);
  gaPatch(180, 330, 180, { key: 'p1', fake: red });
  gaPatch(340, 820, 200, { key: 'p2', paint: ev(tPaint - 0.5, 1.5), fake: red });
  gaPatch(px, py, ps, { key: 'p3', paint: ev(tPaint, Math.max(1.5, s.dur * 0.2)), fake: red });
  const bt = ev(tPaint, Math.max(1.5, s.dur * 0.2)), bxh = px - 60 + Math.sin(TT * 9) * 30 * (bt < 1 ? 1 : 0), byh = py - 60 + bt * 120;
  ctx.save(); ctx.translate(bxh, byh); ctx.rotate(-0.7); paint(rrectPts(0, -8, 300, 16, 6), { fill: '#a46a3a', key: 'br18', w: 2.4 }); paint([[0, -12], [-60, -2], [-66, 4], [0, 12]], { fill: '#3c5a8c', key: 'bt18', w: 2 }); ctx.restore();
  // the truck, front view, fully in frame
  const [bx, by, bw, bh] = TH.bumper;
  [[bx + 60, by + 220], [bx + bw - 60, by + 220]].forEach(([x, y], i) => paint(ellipsePts(x, y, 100, 110, 0, 28), { fill: GA.track, key: 'tyre' + i, w: 3, tex: [{ k: 'hatch', a: 0, gap: 8, al: 0.4 }] }));
  paint([[bx - 10, by], [bx + 20, by - 120], [bx + 150, by - 140], [bx + 150, by]], { fill: GA.oliveD, key: 'fendL', w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 5, al: 0.3 }] });
  paint([[bx + bw + 10, by], [bx + bw - 20, by - 120], [bx + bw - 150, by - 140], [bx + bw - 150, by]], { fill: GA.oliveD, key: 'fendR', w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 5, al: 0.3 }] });
  paint(box(bx + 60, by - 500, bw - 120, 500), { fill: GA.olive, key: 'cab', w: 3, tex: [{ k: 'cross', c: GA.oliveD, al: 0.45, gap: 6, dens: gaShade(bx, by - 500, bx + bw, by) }] });
  [[bx + 90, by - 480], [bx + bw / 2 + 10, by - 480]].forEach(([x, y], i) => paint(box(x, y, bw / 2 - 100, 140), { fill: '#9fb4c0', key: 'ws' + i, w: 3, tex: [{ k: 'hatch', a: 0.6, gap: 6, al: 0.3, dens: (qx) => clamp((qx - x) / 200) }] }));
  paint(box(bx + 150, by - 310, bw - 300, 280), { fill: GA.oliveD, key: 'grille', w: 3 });
  for (let i = 0; i < 8; i++) ink([[bx + 175 + i * 40, by - 295], [bx + 175 + i * 40, by - 45]], { w: 6, color: '#2a2a16', key: 'gr' + i });
  [[bx + 95, by - 190], [bx + bw - 95, by - 190]].forEach(([x, y], i) => paint(ellipsePts(x, y, 50, 50, 0, 24), { fill: '#e9e2c6', key: 'hl' + i, w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 4, al: 0.3, dens: gaShade(x - 50, y - 50, x + 50, y + 50) }] }));
  paint(box(bx, by, bw, bh), { fill: GA.oliveD, key: 'bump', w: 3.5, tex: [{ k: 'cross', c: '#2a2a16', al: 0.4, gap: 6 }] });
  // the stencil: held on, sprayed, lifted away -> white marks (illustrative, unreadable: no real unit code)
  const lifted = ev(tS1, 0.5), spraying = TT >= tS0 && TT < tS1;
  const marks = [[bx + 110, 70], [bx + 220, 40], [bx + 290, 110], [bx + 440, 40], [bx + 520, 60]];
  if (lifted > 0) marks.forEach(([x, w], i) => paint(box(x, by + 25, w, 60), { fill: '#f3efe2', key: 'mk' + i, w: 1.5, line: 'rgba(58,36,23,0.5)', tex: [{ k: 'stipple', c: '#b9b4a0', n: 60, s: 2 }] }));
  if (TT >= tSt && lifted < 1) {
    ctx.save(); ctx.translate(0, -lifted * 900);
    paint(box(bx + 80, by + 8, 530, 96), { fill: '#c9b58c', key: 'stc', w: 2.5, tex: [{ k: 'hatch', a: 0.8, gap: 5, al: 0.25 }] });
    marks.forEach(([x, w], i) => paint(box(x, by + 25, w, 60), { fill: GA.oliveD, key: 'hole' + i, w: 1.5 }));
    ctx.restore();
  }
  const sp = TT >= tSt - 0.6 && TT < tS1 + 0.8;
  const fig = gaFigure(1040, 1010, 430, { face: 1, pose: sp ? gaPose('spray', TT * 6) : gaPose('stand'), key: 'spr' });
  if (sp) paint(rrectPts(fig.hand[0] - 14, fig.hand[1] - 50, 28, 70, 8), { fill: '#c7c3b6', key: 'can', w: 2.5 });
  if (spraying) { const R = RNG('spray', B), nx = bx + 100 + mod((TT - tS0) * 260, 480); ctx.fillStyle = 'rgba(243,239,226,0.85)'; for (let i = 0; i < 140; i++) ctx.fillRect(nx + R.n(55), by + R.r(10, 100), 2.2, 2.2); }
  if (lifted >= 1) planInk(ellipsePts(bx + bw / 2, by + 55, bw * 0.58, 100, 0, 40), { closed: true, key: 'mkring', frac: ev(tS1 + 0.6, 0.5) });
  gaTag(s, 'Special effects');
  gaCap('fake shoulder patches, false vehicle markings', gaAt(s, 0.08, 0.6, 1.4));
  gaDefer(() => gaNote(['BETTEMBOURG, SEPT 1944', 'about 500 men played the', '~8,000-man 6th Armored Division'], 560, 40, 28, { t: tBett, colors: [C.ink, C.ink, GA.fake] }));
}
// a gentle push about a point chosen so the whole truck (x <= 1830) stays in frame at full zoom
function gaEffectsCam(s, t) { return push(t, s.start + 0.3, s.end, { z: 1.04, p: [900, 560], to: [900, 560] }); }

const thDozerX = (s) => lerp(TH.dozer.x0, TH.dozer.x1, EZ.io(clamp((TT - s.start - 0.4) / Math.max(1, s.dur - 1.2))));
function gaEngineers(s) {
  paperSheet('sky19', { fill: '#ecd6a8', ruled: false });
  paint(ellipsePts(1130, 380, 100, 100, 0, 40), { fill: '#f0b45a', key: 'sun19', w: 2.5, tex: [{ k: 'pencil', c: '#f7d48a', al: 0.5, per: 50 }] });
  [[300, 160, 240, 44], [1050, 120, 200, 38]].forEach(([x, y, w, h], i) => gaCloud(x + Math.sin(TT * 0.2 + i) * 30, y, w, h, 'c19' + i, { fill: '#f3e3c0' }));
  gaBirds(3, 250, 'b19', { v: 34 });
  paint([[-40, 600], [300, 540], [700, 570], [1100, 520], [1500, 560], [1960, 530], [1960, 680], [-40, 680]], { fill: '#9a9a62', key: 'hills19', w: 2.5, tex: [{ k: 'pencil', c: '#77783e', al: 0.45, per: 280 }] });
  [[160, 600, 200], [1820, 590, 230]].forEach(([x, y, h], i) => gaRoundTree(x, y, h, 'rt19' + i));
  gaTent(560, 640, 160, 100, 't19a'); gaTent(720, 645, 130, 80, 't19b');
  paint(box(-40, 650, 2000, 470), { raw: true, fill: '#b49a68', key: 'mud', line: false, tex: [{ k: 'pencil', c: '#8a6f44', al: 0.45, per: 380, a: 0.1, len: 26 }] });
  // the perimeter: posts and wire, a sentry walking it
  const sw = Math.sin((TT - s.start) * 0.35), sx = 760 + sw * 420;
  gaFigure(sx, 700, 190, { face: Math.cos((TT - s.start) * 0.35) >= 0 ? 1 : -1, pose: gaPose('sentry', TT * 5), rifle: true, key: 'sentry' });
  gaFence(-40, 1960, 720, 110, 'fe19', { gap: 150 });
  // the MPs at the crossroads (posing: red), a signpost, a truck waiting
  ink([[1660, 850], [1660, 640]], { w: 10, color: '#5a3d24', key: 'post' });
  [[1660, 670, 1], [1660, 720, -1]].forEach(([x, y, d], i) => paint([[x, y - 22], [x + d * 140, y - 22], [x + d * 170, y], [x + d * 140, y + 22], [x, y + 22]], { fill: '#e8dcc0', key: 'arrow' + i, w: 2.5 }));
  gaTruck(1880, 812, 200, { key: 't19' });
  gaFigure(1560, 860, 300, { face: 1, head: 'mp', armband: true, pose: gaPose('direct', TT * 2), key: 'mp1' });
  gaFigure(1770, 862, 300, { face: -1, head: 'mp', armband: true, pose: gaPose('stand'), key: 'mp2' });
  const tMp = gaAt(s, 0.55, 5.0, 1e9, 2.0);
  planInk(ellipsePts(1665, 720, 230, 190, 0, 40), { closed: true, key: 'mpring', frac: ev(tMp, 0.5) });
  if (TT >= tMp + 0.3) handText('posing as MPs', 1500, 515, 46, GA.fake, { key: 'mpt', frac: ev(tMp + 0.3, 0.6) });
  [[180, 1010, 120, 34], [420, 1050, 160, 30], [760, 1000, 90, 22]].forEach(([x, y, w, h], i) => paint(ellipsePts(x, y, w, h, 0, 22), { fill: '#8f8a7e', key: 'pud' + i, w: 2, tex: [{ k: 'hatch', a: 0.05, gap: 6, al: 0.3, c: '#ffffff' }] }));
  for (let i = 0; i < 5; i++) paint(gaCapsule([60 + (i % 3) * 20, 900 - i * 28], [330 + (i % 3) * 20, 900 - i * 28], 16, 5), { fill: '#8a6a44', key: 'log' + i, w: 2, tex: [{ k: 'hatch', a: 0, gap: 6, al: 0.35 }] });
  gaFigure(300, 960, 330, { face: 1, pose: gaPose('point'), key: 'eng1' }); gaFigure(130, 975, 320, { face: 1, pose: gaPose('stand'), rifle: true, key: 'eng2' });
  // the bulldozer lays fake tank tracks behind it (red: they are fake)
  const { y, s: ds } = TH.dozer, dx = thDozerX(s), rear = dx + ds * 0.48;
  for (const [ty, k] of [[y - 6, 0], [y + 50, 1]]) {
    paint(box(rear - 20, ty - 26, W + 60 - rear, 40), { fill: '#7a6240', key: 'trk' + k, w: 1.5, line: 'rgba(58,36,23,0.5)' });
    for (let x = rear; x < W + 40; x += 22) ink([[x, ty - 24], [x + 6, ty + 12]], { w: 3, color: '#4a3a24', key: 'tread' + k + Math.round(x), amt: 0.5 });
  }
  gaBulldozer(dx, y, ds, 'doz');
  const tTr = gaAt(s, 0.3, 2.6, 1e9, 3.0);
  if (TT >= tTr) { planInk([[rear + 40, y - 40], [Math.min(W - 40, rear + 700), y - 40]], { key: 'trline', frac: ev(tTr, 0.6) }); handText('fake tank tracks', rear + 60, y - 52, 42, GA.fake, { key: 'trt', frac: ev(tTr + 0.3, 0.6) }); }
  gaTag(s, '406th Engineers');
  gaCap('fake tank tracks, a guarded perimeter, soldiers posing as MPs', gaAt(s, 0.08, 0.6, 1.4), { y: 996, size: 40 });
}
const thBlade = (s) => { const { y, s: ds } = TH.dozer, dx = thDozerX(s); return [dx - ds * 0.5, y - ds * 0.36, ds * 0.11, ds * 0.37]; };
