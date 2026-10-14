// =====================================================================
//  g10 — recruited from art schools and ad agencies: a studio (easel, drafting table, ad layout, sketchbook)
//        is wiped, left to right, into army kit (camouflage panel, decoy blueprint, swatches, field notebook).
//  g11 — four recruits as hand-lettered name cards with drawn portraits (illustrative, no likeness).
// =====================================================================
const RC = { book: [1170, 830, 330, 190], card0: [140, 150, 380, 660] };
function gaStudio(mode, s) {
  const army = mode === 'army', ph = (TT - s.start) * 2.4;
  // walls and floor
  if (!army) {
    paperSheet('studioW', { fill: '#e6dcc3', ruled: false });
    paint(box(1500, 690, 460, 40), { fill: '#b88f5a', key: 'shelf', w: 2.5 });
    [[640, 120, 150, 110], [820, 140, 120, 160], [980, 110, 170, 120]].forEach(([x, y, w, h], i) => { paint(box(x, y, w, h), { fill: '#f4ecd9', key: 'fr' + i, w: 3 }); ink(i === 1 ? ellipsePts(x + w / 2, y + h / 2, w * 0.3, h * 0.35, 0, 20) : [[x + 15, y + h - 20], [x + w * 0.4, y + 30], [x + w * 0.7, y + h * 0.6], [x + w - 15, y + 25]], { closed: i === 1, w: 2, color: 'rgba(80,70,60,0.7)', key: 'frs' + i }); });
    woodSurface(-60, 880, W + 60, H + 60, 'floorS');
  } else {
    paint(box(-40, -40, 2000, 960), { raw: true, fill: '#7d7a4e', key: 'tentW', line: false, tex: [{ k: 'cross', c: '#4b4a2c', al: 0.3, gap: 7 }, { k: 'pencil', c: '#9a9868', al: 0.3, per: 300 }] });
    for (let i = 0; i < 5; i++) ink([[i * 480 - 20, -20], [i * 480 + 10, 900]], { w: 12, color: '#5a3d24', key: 'pole' + i });
    paint(box(-40, 880, 2000, 260), { raw: true, fill: '#6b5a3a', key: 'duck', line: false, tex: [{ k: 'hatch', a: 0, gap: 22, c: '#3e3322', al: 0.6, w: 3 }] });
    paint(box(640, 120, 520, 150), { fill: '#d8cfb4', key: 'sign', w: 3 }); monoText('U.S. ARMY', 690, 220, 72, C.ink, { key: 'usa' });
  }
  // the easel and its canvas: a landscape -> a camouflage panel
  ink([[200, 900], [330, 260]], { w: 10, color: '#7a5434', key: 'el1' }); ink([[460, 900], [330, 260]], { w: 10, color: '#7a5434', key: 'el2' }); ink([[330, 300], [370, 900]], { w: 8, color: '#6a4424', key: 'el3' });
  paint(box(170, 330, 320, 380), { fill: '#f6f0de', key: 'cnv', w: 3 });
  if (!army) { paint([[170, 560], [260, 470], [360, 530], [490, 450], [490, 710], [170, 710]], { fill: '#8fa66a', key: 'hill', w: 2, tex: [{ k: 'pencil', c: '#6b844a', al: 0.5, per: 60 }] }); paint(ellipsePts(400, 420, 40, 40, 0, 20), { fill: '#f0c55a', key: 'sun', w: 2 }); }
  else { const R = RNG('camo'); for (let i = 0; i < 9; i++) paint(ellipsePts(R.r(200, 460), R.r(360, 680), R.r(40, 80), R.r(25, 50), R.r(0, 3), 18), { fill: ['#5d6a3a', '#7a5f3a', '#2f2f24'][i % 3], key: 'cm' + i, w: 1.6, tex: [{ k: 'hatch', a: 0.8, gap: 5, al: 0.25 }] }); }
  paint(box(180, 700, 300, 22), { fill: '#7a5434', key: 'ledge', w: 2 });
  // the painter (same person: shirt -> uniform)
  gaFigure(600, 900, 470, { face: -1, pose: gaPose('paint', ph), head: army ? 'garrison' : 'hair', hair: '#3d2a1e', jacket: army ? GA.khaki : '#7a8fa8', trous: army ? GA.trous : '#5b5245', key: 'pnt' });
  // the drafting table: a figure study -> a decoy tank blueprint
  ink([[880, 900], [960, 650]], { w: 10, color: '#5a3d24', key: 'dl1' }); ink([[1260, 900], [1180, 650]], { w: 10, color: '#5a3d24', key: 'dl2' });
  paint([[820, 660], [1320, 660], [1270, 430], [870, 430]], { fill: army ? '#c9d6e3' : '#efe7d2', key: 'board', w: 3, tex: [{ k: 'pencil', c: '#ffffff', al: 0.35, per: 200 }] });
  if (!army) { ink(ellipsePts(1000, 560, 50, 70, 0, 24), { closed: true, w: 2.2, color: 'rgba(80,70,60,0.8)', key: 'vase' }); ink([[1110, 620], [1130, 500], [1170, 470], [1200, 520], [1180, 620]], { w: 2.2, color: 'rgba(80,70,60,0.8)', key: 'fig' }); }
  else { ink(gaTankOutline(1070, 610, 300), { closed: true, w: 2.4, color: '#24456b', key: 'bp' }); ink([[920, 630], [1220, 630]], { w: 1.6, color: '#24456b', key: 'dim' }); monoText('DECOY', 990, 470, 30, '#24456b', { key: 'bpt' }); }
  ink([[840, 450], [840, 650]], { w: 6, color: '#c9a24a', key: 'tsq' }); ink([[830, 450], [1300, 450]], { w: 6, color: '#c9a24a', key: 'tsq2' });
  // the ad layout board: an ad (headline, a bottle) -> camouflage swatches
  paint(box(1440, 150, 400, 520), { fill: '#fbf7ec', key: 'ad', w: 3 });
  if (!army) { paint(box(1480, 190, 320, 50), { fill: '#d4382c', key: 'adh', w: 0, line: false }); ink([[1480, 270], [1760, 270]], { w: 8, color: '#555', key: 'adl1' }); ink([[1480, 300], [1700, 300]], { w: 8, color: '#555', key: 'adl2' }); paint([[1600, 620], [1600, 420], [1620, 380], [1660, 380], [1680, 420], [1680, 620]], { fill: '#6aa0b8', key: 'bot', w: 2.5, tex: [{ k: 'hatch', a: 0.7, gap: 4, al: 0.3 }] }); monoText('AD', 1490, 640, 40, C.ink, { key: 'adt' }); }
  else for (let i = 0; i < 6; i++) paint(box(1480 + (i % 2) * 170, 200 + Math.floor(i / 2) * 150, 140, 120), { fill: ['#5d6a3a', '#7a5f3a', '#2f2f24', '#8a8a5a', '#4b5534', '#6e5a3a'][i], key: 'sw' + i, w: 2, tex: [{ k: 'hatch', a: 0.8, gap: 5, al: 0.25 }] });
  // the sketchbook (bridge object) on a stool: figure sketches -> a field notebook with a tank
  ink([[1220, 1080], [1250, 1020]], { w: 10, color: '#5a3d24', key: 'st1' }); ink([[1450, 1080], [1420, 1020]], { w: 10, color: '#5a3d24', key: 'st2' });
  const [bx, by, bw, bh] = RC.book;
  paint(box(bx, by, bw, bh), { fill: army ? '#6f7046' : '#f2ead8', key: 'book', w: 3, tex: [{ k: 'pencil', c: army ? '#4a4b2c' : '#e2d4b0', al: 0.4, per: 90 }] });
  if (!army) { for (let i = 0; i < 8; i++) ink(ellipsePts(bx + 20 + i * 38, by - 2, 8, 10, 0, 10), { closed: true, w: 2, key: 'sp' + i }); ink([[bx + 60, by + 150], [bx + 80, by + 60], [bx + 110, by + 40], [bx + 130, by + 80], [bx + 120, by + 150]], { w: 2, color: 'rgba(80,70,60,0.8)', key: 'bfig' }); }
  else { paint(box(bx + 20, by + 20, bw - 40, bh - 40), { fill: '#f2ead8', key: 'bpage', w: 2 }); ink(gaTankOutline(bx + bw / 2, by + bh - 40, 200), { closed: true, w: 2, color: 'rgba(60,50,40,0.85)', key: 'btank' }); }
  // labels on the wall
  if (!army) { inkCard('art schools', 330, 250, 40, { rot: -0.04 }); inkCard('ad agencies', 1640, 110, 40, { rot: 0.03 }); }
}
function gaRecruit(s) {
  const t0 = gaAt(s, 0.42, 3.2), d = Math.max(1.2, Math.min(3.0, s.dur * 0.18)), u = EZ.io(clamp((TT - t0) / d)), wx = lerp(-80, W + 80, u);
  gaStudio('civ', s);
  if (u > 0) {
    ctx.save(); ctx.beginPath(); ctx.rect(-400, -400, wx + 400, H + 800); ctx.clip(); gaStudio('army', s); ctx.restore();
    if (u < 1) ink([[wx, -40], [wx + 10, H + 40]], { w: 6, color: C.ink, key: 'wipe', amt: 3 });
  }
  gaTag(s, u < 0.5 ? 'Art schools · ad agencies' : 'Art schools · ad agencies → U.S. Army', u < 0.5 ? s.start + 0.15 : t0 + d * 0.5);
  gaCap('Many were recruited from art schools and ad agencies', gaAt(s, 0.06, 0.5, 1.2));
}

function gaNames(s) {
  paint(box(-40, -40, 2000, 1160), { raw: true, fill: '#c99a62', key: 'cork', line: false, tex: [{ k: 'stipple', c: '#8a5a2e', n: 2600, s: 2.4 }, { k: 'stipple', c: '#e3bb84', n: 1600, s: 2 }] });
  paint(box(-40, -40, 2000, 60), { raw: true, fill: '#7a5434', key: 'frT', line: false, tex: [{ k: 'hatch', a: 0, gap: 6, al: 0.3 }] });
  // background life: pinned sketches, string, a pencil
  [[70, 900, -0.08], [1850, 900, 0.06], [980, 40, 0.03], [560, 950, 0.04], [1280, 960, -0.05]].forEach(([x, y, r], i) => { ctx.save(); ctx.translate(x, y); ctx.rotate(r); paint(box(-70, -50, 140, 100), { fill: '#f4ecd9', key: 'bs' + i, w: 2 }); ink(gaTankOutline(0, 30, 100), { closed: true, w: 1.6, color: 'rgba(80,70,60,0.7)', key: 'bst' + i }); gaPin(0, -40); ctx.restore(); });
  ink([[120, 120], [960, 150], [1800, 118]], { w: 2, color: '#b0342a', key: 'string', amt: 2 });
  drawPencil(860, 1010, -0.12, 300, 0.9, 'pen11');
  const names = ['Ellsworth Kelly', 'Bill Blass', 'Arthur Singer', 'Art Kane'];
  names.forEach((n, i) => {
    const ti = i === 0 ? s.start - 1 : Math.max(gaAt(s, 0.06 + 0.17 * i, 0.4 + i * 1.3), s.start + i * 1.2), k = popS(ti); if (k <= 0) return;
    const [x0, y0, w, h] = [RC.card0[0] + i * 420, RC.card0[1] + (i % 2) * 24, RC.card0[2], RC.card0[3]], cx = x0 + w / 2;
    ctx.save(); ctx.translate(cx, y0 + h / 2); ctx.rotate([-0.03, 0.02, -0.015, 0.03][i]); ctx.scale(k, k); ctx.translate(-cx, -(y0 + h / 2));
    paint(box(x0 + 10, y0 + 14, w, h), { fill: 'rgba(58,36,23,0.35)', line: false, key: 'csh' + i, tex: [{ k: 'hatch', a: 0.8, gap: 4, al: 0.5 }] });
    paint(box(x0, y0, w, h), { fill: '#f6efd9', key: 'card' + i, w: 3, tex: [{ k: 'pencil', c: '#e8d6b0', al: 0.5, per: 90 }] });
    gaPortrait(cx, y0 + 230, 185, i, 'pt' + i);
    handText(n, x0 + (w - handW(n, 46)) / 2, y0 + h - 70, 46, C.ink, { key: 'nm' + i, frac: ev(ti + 0.3, 0.9) });
    paint(box(cx - 50, y0 - 14, 100, 34), { fill: 'rgba(239,226,180,0.85)', key: 'tape' + i, w: 1.2, line: 'rgba(58,36,23,0.4)' });
    ctx.restore();
  });
  gaLabel('portraits: illustrative', 1560, 1040, 22);
  gaTag(s, 'Among the recruits');
}
function gaNamesCam(s, t) { return push(t, s.start + 0.6, s.end, { z: 1.05, p: [960, 470], to: [960, 500] }); }
