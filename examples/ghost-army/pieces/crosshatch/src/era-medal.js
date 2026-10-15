// =====================================================================
//  g41 — three veterans at the 2024 ceremony (illustrative portraits, no likeness): dignified, framed, named.
//  g45 — the end card: family stories in the comments; the next documentary; thanks for watching.
// =====================================================================
function gaElder(x, y, s, v, key) {   // an elderly man, front view, in a suit (illustrative)
  const lw = Math.max(2, s * 0.011);
  paint([[x - s * 0.7, y + s * 1.05], [x - s * 0.58, y + s * 0.62], [x - s * 0.17, y + s * 0.5], [x + s * 0.17, y + s * 0.5], [x + s * 0.58, y + s * 0.62], [x + s * 0.7, y + s * 1.05]], { fill: '#2f3446', key: key + 'suit', w: lw, tex: [{ k: 'cross', c: '#151824', al: 0.35, gap: 5, dens: gaShade(x - s * 0.7, y + s * 0.5, x + s * 0.7, y + s * 1.05) }] });
  paint([[x - s * 0.17, y + s * 0.5], [x, y + s * 0.95], [x + s * 0.17, y + s * 0.5]], { fill: '#f2efe6', key: key + 'shirt', w: lw });
  paint([[x - s * 0.05, y + s * 0.58], [x + s * 0.05, y + s * 0.58], [x + s * 0.07, y + s * 0.92], [x, y + s * 0.98], [x - s * 0.07, y + s * 0.92]], { fill: ['#3c5a8c', '#5a4a7a', '#4a5a3a'][v % 3], key: key + 'tie', w: lw * 0.8 });
  [[-1], [1]].forEach(([k]) => paint([[x + k * s * 0.17, y + s * 0.5], [x + k * s * 0.32, y + s * 0.62], [x + k * s * 0.1, y + s * 0.95]], { fill: '#262a3a', key: key + 'lap' + k, w: lw * 0.8 }));
  paint(ellipsePts(x - s * 0.36, y + s * 0.74, s * 0.035, s * 0.035, 0, 10), { fill: '#c9a227', key: key + 'pin', w: lw * 0.6 });
  paint(gaCapsule([x, y + s * 0.28], [x, y + s * 0.52], s * 0.13, 5), { fill: GA.skin, key: key + 'nk', w: lw });
  const fw = [0.37, 0.35, 0.38][v % 3], fh = [0.47, 0.5, 0.46][v % 3];
  [-1, 1].forEach((k) => paint(ellipsePts(x + k * s * fw, y + s * 0.03, s * 0.07, s * 0.12, 0, 10), { fill: GA.skinD, key: key + 'ear' + k, w: lw * 0.8 }));
  paint(ellipsePts(x, y, s * fw, s * fh, 0, 30), { fill: '#e9c3a2', key: key + 'face', w: lw, tex: [{ k: 'hatch', a: 0.75, gap: 4, al: 0.28, dens: (px) => clamp((px - x) / (s * fw) + 0.1) }] });
  // white hair: a fringe at the sides (v1 is bald on top), a full head (v0, v2)
  if (v % 3 === 1) [-1, 1].forEach((k) => paint(ellipsePts(x + k * s * fw * 0.92, y - s * 0.12, s * 0.09, s * 0.17, k * 0.2, 12), { fill: '#eceae4', key: key + 'hr' + k, w: lw * 0.8 }));
  else paint([...arcPts(x, y - s * 0.06, s * fw * 1.04, Math.PI * 1.04, Math.PI * 1.96, 12), [x + s * 0.12, y - s * 0.3], [x - s * 0.2, y - s * 0.26]], { fill: '#eceae4', key: key + 'hr', w: lw, tex: [{ k: 'hatch', a: 0.3, gap: 5, al: 0.25 }] });
  // the lines of age, the brows, glasses on v0 and v2, a calm mouth
  [[-0.24, -0.28, -0.08, -0.3], [-0.22, -0.22, -0.06, -0.24], [0.08, -0.3, 0.24, -0.28]].forEach(([a, b, c, d], i) => ink([[x + a * s, y + b * s], [x + c * s, y + d * s]], { w: lw * 0.6, color: 'rgba(90,60,40,0.55)', key: key + 'fh' + i, amt: 0.3 }));
  for (const k of [-1, 1]) {
    ink([[x + k * s * 0.22, y - s * 0.12], [x + k * s * 0.07, y - s * 0.14]], { w: lw * 1.5, color: '#bdb8ae', key: key + 'brow' + k, amt: 0.4 });
    const blink = (B + v * 17) % 53 < 2;
    if (blink) ink([[x + k * s * 0.19, y - s * 0.03], [x + k * s * 0.1, y - s * 0.03]], { w: lw, key: key + 'bl' + k, amt: 0.2 });
    else { ctx.fillStyle = C.ink; ctx.beginPath(); ctx.ellipse(x + k * s * 0.145, y - s * 0.03, s * 0.028, s * 0.03, 0, 0, TAU); ctx.fill(); }
    ink(arcPts(x + k * s * 0.15, y + s * 0.03, s * 0.06, 0.2, Math.PI - 0.2, 6), { w: lw * 0.6, color: 'rgba(90,60,40,0.5)', key: key + 'bag' + k, amt: 0.2 });
    if (v % 3 !== 1) ink(ellipsePts(x + k * s * 0.15, y - s * 0.03, s * 0.1, s * 0.08, 0, 18), { closed: true, w: lw, color: '#3a3530', key: key + 'gl' + k, amt: 0.3 });
  }
  if (v % 3 !== 1) ink([[x - s * 0.05, y - s * 0.04], [x + s * 0.05, y - s * 0.04]], { w: lw, color: '#3a3530', key: key + 'glb', amt: 0.2 });
  ink([[x + s * 0.02, y], [x + s * 0.05, y + s * 0.15], [x - s * 0.03, y + s * 0.17]], { w: lw, key: key + 'nose', amt: 0.4 });
  ink([[x - s * 0.18, y + s * 0.12], [x - s * 0.14, y + s * 0.26]], { w: lw * 0.6, color: 'rgba(90,60,40,0.5)', key: key + 'nl', amt: 0.3 }); ink([[x + s * 0.18, y + s * 0.12], [x + s * 0.14, y + s * 0.26]], { w: lw * 0.6, color: 'rgba(90,60,40,0.5)', key: key + 'nr', amt: 0.3 });
  ink(arcPts(x, y + s * 0.2, s * 0.11, Math.PI * 0.25, Math.PI * 0.75, 8), { w: lw * 1.1, key: key + 'mouth', amt: 0.3 });
}
function gaVeterans(s) {
  // the hall: marble columns, a soft drape, the flag
  paint(box(-40, -40, 2000, 1160), { raw: true, fill: '#e6e0d2', key: 'hall', line: false, tex: [{ k: 'pencil', c: '#cfc6b0', al: 0.4, per: 300 }] });
  for (let i = 0; i < 6; i++) { const x = 30 + i * 380; paint(box(x, 0, 90, 1080), { fill: '#f2eee4', key: 'col' + i, w: 2.5, tex: [{ k: 'hatch', a: Math.PI / 2, gap: 14, al: 0.2 }] }); }
  paint(box(-40, 900, 2000, 220), { raw: true, fill: '#3a4466', key: 'carpet', line: false, tex: [{ k: 'hatch', a: 0.05, gap: 9, c: '#1e2440', al: 0.4 }] });
  for (let i = 0; i < 9; i++) { const x = -40 + i * 250; paint([[x, -40], [x + 250, -40], [x + 250, 40], [x + 125, 110], [x, 40]], { fill: i % 2 ? '#2f3a6a' : '#e9e2cf', key: 'drape' + i, w: 2, tex: [{ k: 'hatch', a: Math.PI / 2, gap: 12, al: 0.25 }] }); }
  const vets = [['Bernard Bluestein', 100], ['John Christman', 99], ['Seymour Nussenbaum', 100]];
  vets.forEach(([n, age], i) => {
    const ti = i === 0 ? s.start - 1 : gaAt(s, 0.08 + 0.13 * i, 0.5 + i * 1.0), k = popS(ti); if (k <= 0) return;
    const cx = 380 + i * 580, y0 = 170, w = 470, h = 640;
    ctx.save(); ctx.translate(cx, y0 + h / 2); ctx.scale(k, k); ctx.translate(-cx, -(y0 + h / 2));
    paint(box(cx - w / 2 + 10, y0 + 14, w, h), { fill: 'rgba(58,36,23,0.3)', line: false, key: 'vsh' + i, tex: [{ k: 'hatch', a: 0.8, gap: 4, al: 0.5 }] });
    paint(box(cx - w / 2, y0, w, h), { fill: '#6b4a2e', key: 'vfr' + i, w: 3, tex: [{ k: 'hatch', a: 0.8, gap: 5, al: 0.3 }] });
    paint(box(cx - w / 2 + 24, y0 + 24, w - 48, h - 48), { fill: '#f3ecda', key: 'vin' + i, w: 2, tex: [{ k: 'pencil', c: '#e2d6bc', al: 0.45, per: 120 }] });
    ctx.save(); trace(box(cx - w / 2 + 24, y0 + 24, w - 48, h - 210), true); ctx.clip(); gaElder(cx, y0 + 240, 210, i, 'el' + i); ctx.restore();
    paint(box(cx - w / 2 + 24, y0 + h - 186, w - 48, 162), { fill: '#f6efd9', key: 'vpl' + i, w: 2 });
    handText(n, cx - handW(n, 44) / 2, y0 + h - 110, 44, C.ink, { key: 'vn' + i, frac: ev(ti + 0.3, 0.9) });
    monoText('age ' + age, cx - monoW(30) * 3.5, y0 + h - 52, 30, '#5a4a3a', { key: 'va' + i, count: TT > ti + 0.8 ? 7 : 0 });
    ctx.restore();
  });
  gaLabel('portraits: illustrative', 1560, 1050, 24, 'rgba(240,236,226,0.9)');
  gaTag(s, 'The 2024 ceremony');
  gaCap('three of the seven then-known surviving veterans attended', gaAt(s, 0.45, 4.6, 1e9, 2.6), { y: 990 });
}
function gaVetCam(s, t) { return push(t, s.start + 0.3, s.end, { z: 1.04, p: [960, 500], to: [960, 500] }); }

function gaEndCard(s) {
  woodSurface(-200, -200, W + 200, H + 200, 'desk45');
  inkMug(1800, 160, 90, 'mug45');
  ink(gaTankOutline(1660, 1010, 200), { closed: true, w: 2.4, color: 'rgba(80,70,60,0.7)', key: 'endtank' });
  planInk(gaTankOutline(1660, 1012, 208), { closed: true, key: 'endtankR', frac: ev(gaAt(s, 0.05, 0.6), 0.8), w: 2.6 });
  // the card: an invitation, written on line by line
  ctx.save(); ctx.translate(140, 120); ctx.rotate(-0.015);
  paint(box(10, 14, 1100, 600), { fill: 'rgba(58,36,23,0.3)', line: false, key: 'ecsh', tex: [{ k: 'hatch', a: 0.8, gap: 4, al: 0.5 }] });
  paint(box(0, 0, 1100, 600), { fill: C.paper, key: 'ecard', w: 3, tex: [{ k: 'pencil', c: '#fffaf0', al: 0.45, per: 300 }] });
  ctx.save(); ctx.strokeStyle = C.paperLine; ctx.lineWidth = 1.3; ctx.beginPath(); for (let y = 110; y < 590; y += 70) { ctx.moveTo(30, y); ctx.lineTo(1070, y); } ctx.stroke(); ctx.restore();
  const L = [['Do you have a family story', 64], ['connected to the 23rd Headquarters', 56], ['Special Troops?', 56], ['Tell us in the comments.', 64]];
  let tt = gaAt(s, 0.04, 0.4);
  L.forEach(([str, sz], i) => { handText(str, 60, 120 + i * 120, sz, i === 3 ? '#26315f' : C.ink, { key: 'el' + i, frac: ev(tt, 1.1) }); tt += 1.0 + 0.04 * str.length; });
  const wEnd = 60 + handW('Tell us in the comments.', 64); ink([[60, 500], [wEnd, 494]], { w: 5, color: '#26315f', key: 'eul', frac: ev(tt - 0.3, 0.5), amt: 2 });
  ctx.restore();
  drawPencil(220 + 700 * clamp((TT - s.start) / Math.max(1, s.dur * 0.45)), 640, -0.5, 260, 0.9, 'pen45');
  // comment bubbles arrive (blank lines: no invented stories)
  [[1320, 300], [1450, 470], [1330, 640]].forEach(([x, y], i) => { const k = popS(gaAt(s, 0.3 + 0.07 * i, 3.0 + i * 0.6)); if (k <= 0) return; ctx.save(); ctx.translate(x, y); ctx.scale(k, k); paint(rrectPts(-160, -60, 320, 120, 30), { fill: '#f6f1e6', key: 'bub' + i, w: 3 }); paint([[-110, 55], [-140, 95], [-70, 58]], { fill: '#f6f1e6', key: 'bubt' + i, w: 3 }); for (let j = 0; j < 2; j++) ink([[-120, -18 + j * 36], [100 - j * 60, -18 + j * 36]], { w: 6, color: 'rgba(58,36,23,0.4)', key: 'bl' + i + j }); ctx.restore(); });
  // the next film: a sealed envelope
  const ke = popS(gaAt(s, 0.55, 6.5, 1e9, 4.5));
  if (ke > 0) { ctx.save(); ctx.translate(560, 860); ctx.rotate(0.03); ctx.scale(ke, ke); paint(box(-360, -120, 720, 240), { fill: '#e9dcc0', key: 'envN', w: 3, tex: [{ k: 'pencil', c: '#d4c29a', al: 0.4, per: 120 }] }); ink([[-360, -120], [0, 20], [360, -120]], { w: 3, key: 'envNf' }); monoText('NEXT DOCUMENTARY', -230, -60, 34, C.ink, { key: 'nxt' }); ctx.restore(); gaCap('another group of Americans whose wartime work stayed secret for decades', gaAt(s, 0.58, 7.0, 1e9, 4.2), { y: 1010, size: 34 }); }
  const kt = gaAt(s, 0.8, 11.0, 1e9, 2.4);
  if (TT >= kt) handText('Thanks for watching.', 1180, 860, 70, '#26315f', { key: 'thx', frac: ev(kt, 1.2) });
}
