// =====================================================================
//  g04 — the title card on a desk.   g05 — Ralph Ingersoll proposes a unit dedicated to deception (Fortitude planning).
// =====================================================================
function gaTitle(s) {
  woodSurface(-200, -200, W + 200, H + 200, 'desk4');
  const tTitle = gaAt(s, 0.05, 0.4, 1.2), tUnit = gaAt(s, 0.3, 2.6), tMen = gaAt(s, 0.42, 3.6), tArt = gaAt(s, 0.55, 4.8), tStamp = gaAt(s, 0.68, 6.0);
  // desk life: a mug of coffee, an ink bottle, paper clips, a ruler
  inkMug(1790, 230, 95, 'mug4');
  paint(ellipsePts(1770, 800, 62, 62, 0, 24), { fill: '#262a3a', key: 'ink4', w: 3, tex: [{ k: 'cross', c: '#000000', al: 0.4, gap: 5 }] });
  paint(ellipsePts(1770, 800, 26, 26, 0, 18), { fill: '#3a3f55', key: 'ink4c', w: 2 });
  ctx.save(); ctx.translate(60, 980); ctx.rotate(-0.05); paint(box(0, 0, 900, 46), { fill: '#e6cf98', key: 'rul4', w: 2.5 }); for (let i = 0; i < 60; i++) ink([[i * 15, 0], [i * 15, i % 5 ? 12 : 22]], { w: 1.4, key: 'rt' + i, amt: 0.2 }); ctx.restore();
  // the folder and the sheet
  ctx.save(); ctx.translate(150, 105); ctx.rotate(-0.02);
  paint(box(-20, -10, 1500, 840), { fill: '#d9b77a', key: 'folder', w: 3, tex: [{ k: 'pencil', c: '#c79c58', al: 0.4, per: 90 }, { k: 'hatch', a: 0.8, gap: 6, al: 0.15, dens: (x, y) => clamp((x + y - 1200) / 900) }] });
  paint(box(40, 40, 1380, 760), { fill: C.paper, key: 'sheet4', w: 3, tex: [{ k: 'pencil', c: '#fffaf0', al: 0.45, per: 400 }] });
  ctx.save(); ctx.strokeStyle = C.paperLine; ctx.lineWidth = 1.3; ctx.beginPath(); for (let y = 150; y < 790; y += 58) { ctx.moveTo(70, y); ctx.lineTo(1400, y); } ctx.stroke(); ctx.restore();
  ink([[1340, 20], [1340, -40], [1380, -40], [1380, 60], [1352, 60], [1352, 0]], { w: 4, color: '#8a8590', key: 'clip4' });
  monoText('U.S. ARMY · 23rd HEADQUARTERS SPECIAL TROOPS', 100, 120, 32, '#5a4a3a', { key: 'unit', count: Math.floor(clamp((TT - tUnit) / 1.4) * 44) });
  ctx.restore();
  handText('The Ghost Army', 300, 440, 165, C.ink, { key: 'ttl', frac: ev(tTitle, 2.0) });
  ink([[300, 480], [1290, 472]], { w: 5, color: C.ink, key: 'ul', frac: ev(tTitle + 1.8, 0.5), amt: 2 });
  handText('about 1,100 soldiers', 320, 620, 66, '#5a3a24', { key: 'men', frac: ev(tMen, 1.0) });
  handText('many of them artists', 320, 720, 66, '#5a3a24', { key: 'art', frac: ev(tArt, 1.0) });
  // artists: pencil studies of a tank appear in the margin as the line is written
  [[1000, 840, 170, 0], [1150, 760, 120, 0.4]].forEach(([x, y, sz, d], i) => { const fr = ev(tArt + 0.4 + d, 1.0); if (fr > 0) ink(gaTankOutline(x, y, sz), { closed: true, w: 2, color: 'rgba(80,70,60,0.75)', key: 'doodle' + i, frac: fr, amt: 1.2 }); });
  drawPencil(330 + 560 * ev(tArt, 1.0), 790, -0.5, 260, 0.9, 'pen4');
  ctx.save(); ctx.translate(1210, 960); ctx.rotate(-0.22);
  paint(rrectPts(0, -10, 330, 20, 8), { fill: '#a46a3a', key: 'brush', w: 2.5, tex: [{ k: 'hatch', a: 0, gap: 4, al: 0.3 }] });
  paint(rrectPts(-50, -16, 60, 32, 6), { fill: '#b8b5ac', key: 'ferr', w: 2.5 }); paint([[-50, -14], [-110, -2], [-120, 6], [-50, 14]], { fill: '#3c5a8c', key: 'tip', w: 2 });
  ctx.restore();
  const k = popS(tStamp);
  if (k > 0) {
    const [sx, sy, sr] = [1390, 650, 140];
    ctx.save(); ctx.translate(sx, sy); ctx.rotate(-0.12); ctx.scale(k, k);
    ink(ellipsePts(0, 0, sr, sr, 0, 64), { closed: true, w: 7, color: 'rgba(38,49,95,0.9)', key: 'st1' });
    ink(ellipsePts(0, 0, sr * 0.78, sr * 0.78, 0, 56), { closed: true, w: 3, color: 'rgba(38,49,95,0.9)', key: 'st2' });
    const txt = 'GHOST ARMY · 23rd HQ SPECIAL TROOPS · '; ctx.font = `700 21px ${MONO}`; ctx.fillStyle = 'rgba(38,49,95,0.9)';
    for (let i = 0; i < txt.length; i++) { ctx.save(); ctx.rotate(-Math.PI / 2 + i / txt.length * TAU); ctx.translate(0, -sr * 0.86); ctx.fillText(txt[i], -6, 0); ctx.restore(); }
    monoText('1944', -52, 14, 42, 'rgba(38,49,95,0.9)', { key: 'yr' });
    ctx.restore();
  }
  gaTag(s, '23rd Headquarters Special Troops');
}

function gaPlan(s) {
  const tArrows = gaAt(s, 0.12, 1.0), tMemo = gaAt(s, 0.32, 3.0), tPoint = gaAt(s, 0.2, 1.5);
  paperSheet('wall5', { fill: '#cdbb94', ruled: false });
  paint(box(-40, 700, 2000, 200), { raw: true, fill: '#a98a5e', key: 'wains', line: false, tex: [{ k: 'hatch', a: Math.PI / 2, gap: 60, al: 0.3, w: 2 }] });
  // the wall map: sea, two coasts, a grid, pins; the plan is drawn on it in red dashes (red = deception)
  paint(box(100, 70, 1100, 640), { fill: '#6e5236', key: 'mapF', w: 3 });
  paint(box(122, 92, 1056, 596), { fill: '#a9c4cf', key: 'sea', w: 2, tex: [{ k: 'hatch', a: 0.05, gap: 8, c: '#5f8796', al: 0.35, dash: [20, 70] }] });
  const coastA = [[122, 92], [700, 92], [690, 150], [610, 190], [560, 260], [470, 300], [380, 290], [300, 330], [200, 320], [122, 360]];
  const coastB = [[1178, 300], [1100, 320], [1020, 380], [990, 450], [900, 500], [860, 580], [760, 620], [700, 688], [1178, 688]];
  paint(coastA, { fill: '#d9c48e', key: 'landA', w: 2.5, tex: [{ k: 'pencil', c: '#b89a5a', al: 0.4, per: 140 }] });
  paint(coastB, { fill: '#d9c48e', key: 'landB', w: 2.5, tex: [{ k: 'pencil', c: '#b89a5a', al: 0.4, per: 140 }] });
  ctx.save(); ctx.strokeStyle = 'rgba(58,36,23,0.25)'; ctx.lineWidth = 1.2; ctx.beginPath(); for (let x = 222; x < 1178; x += 100) { ctx.moveTo(x, 92); ctx.lineTo(x, 688); } for (let y = 192; y < 688; y += 100) { ctx.moveTo(122, y); ctx.lineTo(1178, y); } ctx.stroke(); ctx.restore();
  [[300, 240], [520, 220], [960, 470], [1080, 400], [820, 600]].forEach(([x, y], i) => gaPin(x, y, i < 2 ? '#2f5d8a' : '#c9a227'));
  [[[330, 260], [520, 420], [880, 520]], [[540, 240], [720, 380], [1000, 430]], [[300, 270], [430, 470], [800, 610]]].forEach((P, i) => {
    const fr = ev(tArrows + i * 0.7, 1.2); if (fr <= 0) return;
    planInk(P, { key: 'arr' + i, frac: fr, w: 4 });
    if (fr >= 1) { const [a, b] = [P[1], P[2]], ang = Math.atan2(b[1] - a[1], b[0] - a[0]); ink([[b[0] - Math.cos(ang - 0.5) * 28, b[1] - Math.sin(ang - 0.5) * 28], b, [b[0] - Math.cos(ang + 0.5) * 28, b[1] - Math.sin(ang + 0.5) * 28]], { w: 4, color: GA.fakeA, key: 'ah' + i }); }
  });
  // the room: a clock, a filing cabinet, a blackout blind
  gaWallClock(1360, 180, 70, 'clk5');
  paint(box(1560, 360, 260, 520), { fill: '#7b8068', key: 'cab', w: 3, tex: [{ k: 'cross', c: '#3e4232', al: 0.35, gap: 6, dens: gaShade(1560, 360, 1820, 880) }] });
  for (let i = 0; i < 4; i++) { paint(box(1580, 380 + i * 125, 220, 105), { fill: '#868b72', key: 'dr' + i, w: 2 }); paint(box(1660, 420 + i * 125, 60, 16), { fill: '#c9c3b0', key: 'hn' + i, w: 1.5 }); }
  paint(box(1290, 300, 200, 300), { fill: '#2c2f3a', key: 'win5', w: 3, tex: [{ k: 'hatch', a: 0, gap: 14, c: '#11131a', al: 0.6, w: 3 }] });
  // the officer at the map (illustrative figure, no likeness), pointing at the plan
  const pu = EZ.io(clamp((TT - tPoint) / 0.6));
  gaFigure(1290, 960, 560, { face: -1, head: 'garrison', pose: gaPoseMix(gaPose('stand'), gaPose('point'), pu), jacket: '#7a6e4c', key: 'ing' });
  // the desk in front: lamp, telephone, mug, the FORTITUDE folder, the typed memo
  woodSurface(-120, 880, W + 120, H + 160, 'desk5');
  gaLamp(60, 960, 150, 'lamp5');
  paint(rrectPts(940, 900, 170, 70, 14), { fill: '#1e1e1e', key: 'tel', w: 2.5 }); paint(gaCapsule([950, 890], [1100, 890], 22, 5), { fill: '#262626', key: 'telh', w: 2.5 });
  gaMug(1210, 1000, 90, 'mug5');
  ctx.save(); ctx.translate(1480, 905); ctx.rotate(0.04); paint(box(0, 0, 420, 150), { fill: '#d9b77a', key: 'fold5', w: 2.5, tex: [{ k: 'pencil', c: '#c79c58', al: 0.4, per: 90 }] }); monoText('FORTITUDE', 30, 60, 34, C.ink, { key: 'ft' }); monoText('planning', 30, 108, 28, '#5a4a3a', { key: 'fp' }); ctx.restore();
  gaNote(['MEMO', 'R. INGERSOLL PROPOSES', 'A UNIT DEDICATED', 'TO DECEPTION'], 250, 730, 32, { t: tMemo, colors: [C.ink, C.ink, GA.fake, GA.fake] });
  gaLabel('figure: illustrative', 1560, 340, 22);
  gaTag(s, 'Fortitude planning');
  gaCap('Ralph Ingersoll proposed a unit dedicated to deception', gaAt(s, 0.06, 0.5, 1.2), { y: 1010 });
}
function gaPlanCam(s, t) { return push(t, gaAt(s, 0.55, 5.0), gaAt(s, 0.8, 7.0), { z: 1.1, p: [520, 830], to: [600, 750] }); }
