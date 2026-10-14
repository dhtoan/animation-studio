// =====================================================================
//  GHOST ARMY — figures (two-bone IK: give a pose by where the hands and feet go), portraits, vehicles, patches
// =====================================================================
function gaIK(S, T, a, b, lower) {
  let dx = T[0] - S[0], dy = T[1] - S[1]; const d0 = Math.hypot(dx, dy) || 1e-6, d = Math.min(d0, a + b - 0.5);
  dx *= d / d0; dy *= d / d0;
  const base = Math.atan2(dy, dx), al = Math.acos(clamp((a * a + d * d - b * b) / (2 * a * d), -1, 1));
  const j1 = [S[0] + a * Math.cos(base + al), S[1] + a * Math.sin(base + al)], j2 = [S[0] + a * Math.cos(base - al), S[1] + a * Math.sin(base - al)];
  return [lower(j1, j2) ? j1 : j2, [S[0] + dx, S[1] + dy]];
}
// poses: hands (hn near, hf far) as offsets from the shoulder, feet (fn, ff) from the hip, in figure heights; x is "forward"
function gaPose(name, ph = 0) {
  const s = Math.sin(ph), c = Math.cos(ph);
  const P = {
    stand: { hn: [0.05, 0.33], hf: [-0.04, 0.33], fn: [0.05, 0.47], ff: [-0.04, 0.47] },
    walk: { hn: [0.14 * s, 0.31], hf: [-0.14 * s, 0.31], fn: [0.14 * s, 0.47 - 0.04 * Math.max(0, c)], ff: [-0.14 * s, 0.47 - 0.04 * Math.max(0, -c)], bob: -0.012 * Math.abs(c) },
    binoc: { hn: [0.13, -0.1], hf: [0.11, -0.085], fn: [0.09, 0.47], ff: [-0.08, 0.47] },
    point: { hn: [0.37, -0.12], hf: [0.03, 0.32], fn: [0.09, 0.47], ff: [-0.06, 0.47] },
    lift: { hn: [0.07, -0.31], hf: [-0.02, -0.31], fn: [0.1 * s, 0.47], ff: [-0.1 * s, 0.47], bob: -0.01 * Math.abs(c) },
    pump: { hn: [0.25, 0.12 + 0.08 * s], hf: [0.22, 0.14 + 0.08 * s], fn: [0.14, 0.47], ff: [-0.1, 0.47], lean: 0.12 + 0.06 * s },
    paint: { hn: [0.3, -0.02 + 0.04 * s], hf: [0.13, 0.18], fn: [0.06, 0.47], ff: [-0.08, 0.47] },
    direct: { hn: [0.39, -0.03 + 0.03 * s], hf: [0.02, 0.32], fn: [0.08, 0.47], ff: [-0.06, 0.47] },
    sentry: { hn: [0.07, 0.04], hf: [-0.06, 0.3], fn: [0.14 * s, 0.47], ff: [-0.14 * s, 0.47], bob: -0.012 * Math.abs(c) },
    spray: { hn: [0.33, 0.02 + 0.03 * s], hf: [0.24, 0.1], fn: [0.1, 0.47], ff: [-0.08, 0.47], lean: 0.08 },
  };
  return P[name] || P.stand;
}
// a figure in profile. y = the ground. o: { face 1|-1, pose, dark, coat, jacket, trous, head: 'helmet'|'cap'|'mp'|'garrison'|'beret'|'hair', hair, binoc, rifle, armband, key }
function gaFigure(x, y, h, o = {}) {
  const f = o.face ?? 1, P = o.pose || gaPose('stand'), key = o.key ?? 'fig', dark = !!o.dark;
  const line = dark ? C.periD : C.ink, lw = Math.max(1.8, h * 0.008);
  const col = (c) => (dark ? GA.sil : c);
  const jacket = col(o.jacket ?? GA.khaki), trous = col(o.trous ?? GA.trous), boot = col(o.boot ?? GA.boot), skin = dark ? GA.sil : GA.skin;
  const farShade = (c) => (dark ? GA.sil : mixHex(c.length === 7 ? c : '#777777', '#2a2418', 0.25));
  const bob = (P.bob ?? 0) * h, lean = (P.lean ?? 0) * h;
  const hip = [x, y - h * 0.5 + bob], sh = [x + f * lean, y - h * 0.815 + bob];
  const fx = (p, base) => [base[0] + f * p[0] * h, base[1] + p[1] * h];
  const tex = (a) => (dark ? [{ k: 'hatch', a, gap: 7, c: C.periD, al: 0.3 }] : [{ k: 'hatch', a, gap: 4, al: 0.35 }]);
  const limb = (S, T, a, b, r0, r1, fill, k, lower) => {
    const [J, E] = gaIK(S, T, a * h, b * h, lower);
    paint(gaCapsule(S, J, r0 * h, 5), { fill, key: key + k + 'u', w: lw, line, tex: tex(0.9) });
    paint(gaCapsule(J, E, r1 * h, 5), { fill, key: key + k + 'l', w: lw, line, tex: tex(0.9) });
    return E;
  };
  const armLower = (j1, j2) => j1[1] > j2[1];
  const legFwd = (j1, j2) => (j1[0] - j2[0]) * f > 0;
  const foot = (E, k, fill) => paint(rrectPts(E[0] - h * 0.03 + f * h * 0.015 - (f < 0 ? h * 0.03 : 0), E[1] - h * 0.035, h * 0.09, h * 0.04, 4), { fill, key: key + 'ft' + k, w: lw, line });
  const hand = (E, k) => paint(ellipsePts(E[0], E[1], h * 0.024, h * 0.026, 0, 10), { fill: skin, key: key + 'hd' + k, w: lw * 0.8, line });
  // far leg, far arm (darker), then the body, then the near limbs
  const shF = [sh[0] - f * h * 0.02, sh[1] + h * 0.01], shN = [sh[0] + f * h * 0.01, sh[1] + h * 0.012];
  const eFF = limb([hip[0] - f * h * 0.015, hip[1]], fx(P.ff, hip), 0.25, 0.25, 0.048, 0.04, farShade(o.trous ?? GA.trous), 'lf', legFwd); foot(eFF, 'f', boot);
  const eHF = limb(shF, fx(P.hf, sh), 0.18, 0.17, 0.034, 0.03, farShade(o.jacket ?? GA.khaki), 'af', armLower); hand(eHF, 'f');
  const eFN = limb([hip[0] + f * h * 0.01, hip[1]], fx(P.fn, hip), 0.25, 0.25, 0.05, 0.042, trous, 'ln', legFwd); foot(eFN, 'n', boot);
  // torso (a jacket, or a long coat to the knee)
  const tor = [[sh[0] - f * h * 0.075, sh[1] - h * 0.005], [sh[0] + f * h * 0.06, sh[1] + h * 0.01], [sh[0] + f * h * 0.08, sh[1] + h * 0.12], [hip[0] + f * h * 0.07, hip[1] + h * 0.03], [hip[0] - f * h * 0.08, hip[1] + h * 0.03]];
  if (o.coat) { tor[3] = [hip[0] + f * h * 0.1, y - h * 0.22 + bob]; tor[4] = [hip[0] - f * h * 0.11, y - h * 0.22 + bob]; }
  const tb = bbox(tor);
  paint(tor, { fill: jacket, key: key + 'tor', w: lw, line, tex: dark ? tex(0.7) : [{ k: 'cross', al: 0.38, gap: 5, dens: gaShade(tb.x0, tb.y0, tb.x1, tb.y1) }] });
  ink([[hip[0] - f * h * 0.075, hip[1] - h * 0.015], [hip[0] + f * h * 0.07, hip[1] - h * 0.015]], { w: lw * 2, color: dark ? C.periD : '#3a3324', key: key + 'belt' });
  if (o.armband) { const a = [sh[0] - f * h * 0.01, sh[1] + h * 0.07]; paint(box(a[0] - h * 0.035, a[1], h * 0.07, h * 0.035), { fill: '#f2f0e8', key: key + 'ab', w: lw, line }); monoText('MP', a[0] - h * 0.025, a[1] + h * 0.03, h * 0.03, C.ink, { key: key + 'abt' }); }
  if (o.rifle) { const a = [sh[0] - f * h * 0.06, sh[1] - h * 0.07], b = [hip[0] - f * h * 0.09, hip[1] + h * 0.08]; ink([a, b], { w: h * 0.018, color: dark ? C.periD : '#5a3d24', key: key + 'rf' }); ink([a, [a[0] - (b[0] - a[0]) * 0.25, a[1] - (b[1] - a[1]) * 0.25]], { w: h * 0.01, color: '#2b2b2b', key: key + 'rb' }); }
  // neck and head
  const hc = [sh[0] + f * h * 0.025, y - h * 0.905 + bob];
  paint(gaCapsule([sh[0] + f * h * 0.01, sh[1]], [hc[0], hc[1] + h * 0.04], h * 0.022, 4), { fill: skin, key: key + 'nk', w: lw, line });
  paint(ellipsePts(hc[0], hc[1], h * 0.052, h * 0.062, 0, 18), { fill: skin, key: key + 'f', w: lw, line, tex: dark ? [] : [{ k: 'hatch', a: 0.7, gap: 4, al: 0.22, dens: (px) => ((px - hc[0]) * -f > 0 ? 0.9 : 0) }] });
  if (!dark) {
    paint([[hc[0] + f * h * 0.048, hc[1] - h * 0.005], [hc[0] + f * h * 0.068, hc[1] + h * 0.012], [hc[0] + f * h * 0.046, hc[1] + h * 0.02]], { fill: skin, key: key + 'nose', w: lw * 0.8, line });
    ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(hc[0] + f * h * 0.03, hc[1] - h * 0.006, Math.max(1.4, h * 0.007), 0, TAU); ctx.fill();
    paint(ellipsePts(hc[0] - f * h * 0.012, hc[1] + h * 0.004, h * 0.011, h * 0.016, 0, 8), { fill: GA.skinD, key: key + 'ear', w: lw * 0.6, line });
  }
  const hd = o.head ?? 'helmet', hcol = col(hd === 'mp' ? '#ecebe4' : o.hcol ?? GA.helmet);
  if (hd === 'helmet' || hd === 'mp') {
    paint([...arcPts(hc[0] - f * h * 0.004, hc[1] - h * 0.006, h * 0.072, Math.PI, TAU, 12).map(([a, b]) => [a, b]), [hc[0] + f * h * 0.085, hc[1] + h * 0.002], [hc[0] - f * h * 0.085, hc[1] + h * 0.002]].map(([a, b], i, A) => [a, b]), { fill: hcol, key: key + 'hm', w: lw, line, tex: dark ? tex(0.7) : [{ k: 'cross', al: hd === 'mp' ? 0.12 : 0.42, gap: 4 }] });
    if (hd === 'mp' && !dark) monoText('MP', hc[0] - h * 0.035, hc[1] - h * 0.03, h * 0.035, C.ink, { key: key + 'mpt' });
  } else if (hd === 'cap') {   // an officer's peaked cap: a crown wider at the top, a visor forward
    paint([[hc[0] - f * h * 0.055, hc[1] - h * 0.035], [hc[0] - f * h * 0.075, hc[1] - h * 0.085], [hc[0] + f * h * 0.075, hc[1] - h * 0.095], [hc[0] + f * h * 0.06, hc[1] - h * 0.04]], { fill: hcol, key: key + 'cap', w: lw, line, tex: tex(0.7) });
    paint([[hc[0] + f * h * 0.04, hc[1] - h * 0.04], [hc[0] + f * h * 0.1, hc[1] - h * 0.022], [hc[0] + f * h * 0.04, hc[1] - h * 0.028]], { fill: dark ? GA.sil : '#1e1e1e', key: key + 'vis', w: lw, line });
  } else if (hd === 'garrison') {
    paint([[hc[0] - f * h * 0.06, hc[1] - h * 0.045], [hc[0] - f * h * 0.04, hc[1] - h * 0.08], [hc[0] + f * h * 0.05, hc[1] - h * 0.075], [hc[0] + f * h * 0.065, hc[1] - h * 0.04]], { fill: hcol, key: key + 'gc', w: lw, line, tex: tex(0.7) });
  } else if (hd === 'beret') {
    paint(ellipsePts(hc[0] - f * h * 0.005, hc[1] - h * 0.055, h * 0.07, h * 0.025, -0.15 * f, 14), { fill: col('#2c2a33'), key: key + 'br', w: lw, line });
  } else {   // hair
    paint([...arcPts(hc[0] - f * h * 0.004, hc[1] - h * 0.004, h * 0.058, Math.PI * 1.02, Math.PI * 1.98, 10), [hc[0] - f * h * 0.05, hc[1] + h * 0.02]], { fill: col(o.hair ?? '#4a3426'), key: key + 'hr', w: lw, line });
  }
  // near arm last (in front of the body), binoculars at the eyes
  if (o.binoc) { const e = [hc[0] + f * h * 0.06, hc[1] - h * 0.004]; paint(gaCapsule(e, [e[0] + f * h * 0.07, e[1] + h * 0.012], h * 0.022, 4), { fill: dark ? GA.sil : '#2e2b26', key: key + 'bn', w: lw, line: dark ? C.peri : line }); }
  const eHN = limb(shN, fx(P.hn, sh), 0.18, 0.17, 0.036, 0.031, jacket, 'an', armLower); hand(eHN, 'n');
  return { head: hc, hand: eHN, handFar: eHF };
}

// ---- a portrait, front view (illustrative, no likeness): v picks hair and cap
function gaPortrait(x, y, s, v, key) {
  const lw = Math.max(2, s * 0.012);
  paint([[x - s * 0.62, y + s * 0.95], [x - s * 0.5, y + s * 0.62], [x - s * 0.16, y + s * 0.5], [x + s * 0.16, y + s * 0.5], [x + s * 0.5, y + s * 0.62], [x + s * 0.62, y + s * 0.95]], { fill: GA.khaki, key: key + 'sh', w: lw, tex: [{ k: 'cross', al: 0.35, gap: 5, dens: gaShade(x - s * 0.6, y + s * 0.5, x + s * 0.6, y + s) }] });
  paint([[x - s * 0.16, y + s * 0.5], [x, y + s * 0.72], [x + s * 0.16, y + s * 0.5]], { fill: '#a39368', key: key + 'col', w: lw });
  ink([[x, y + s * 0.6], [x, y + s * 0.95]], { w: s * 0.05, color: '#4b4430', key: key + 'tie' });
  paint(gaCapsule([x, y + s * 0.3], [x, y + s * 0.55], s * 0.13, 5), { fill: GA.skin, key: key + 'nk', w: lw });
  const fw = [0.36, 0.33, 0.38, 0.35][v % 4], fh = [0.46, 0.5, 0.44, 0.47][v % 4];
  [-1, 1].forEach((k) => paint(ellipsePts(x + k * s * fw, y + s * 0.02, s * 0.06, s * 0.1, 0, 10), { fill: GA.skinD, key: key + 'ear' + k, w: lw * 0.8 }));
  paint(ellipsePts(x, y, s * fw, s * fh, 0, 30), { fill: GA.skin, key: key + 'face', w: lw, tex: [{ k: 'hatch', a: 0.75, gap: 4, al: 0.3, dens: (px) => clamp((px - x) / (s * fw) + 0.1) }] });
  const hair = ['#3d2a1e', '#2a2420', '#6b4a2e', '#4a3426'][v % 4];
  if (v % 4 === 0) paint([...arcPts(x, y - s * 0.05, s * fw * 1.04, Math.PI * 1.02, Math.PI * 1.98, 12), [x + s * 0.1, y - s * 0.3], [x - s * 0.2, y - s * 0.22]], { fill: hair, key: key + 'hr', w: lw });
  if (v % 4 === 1) paint([...arcPts(x, y - s * 0.06, s * fw * 1.06, Math.PI, TAU, 12), [x + s * fw, y - s * 0.1], [x, y - s * 0.32], [x - s * fw, y - s * 0.1]], { fill: hair, key: key + 'hr', w: lw, tex: [{ k: 'hatch', a: 0.2, gap: 5, al: 0.4, c: '#ffffff' }] });
  if (v % 4 === 2) { paint([...arcPts(x, y - s * 0.08, s * fw * 1.02, Math.PI * 1.05, Math.PI * 1.95, 12)], { fill: hair, key: key + 'hr', w: lw }); paint([[x - s * 0.42, y - s * 0.3], [x - s * 0.3, y - s * 0.5], [x + s * 0.32, y - s * 0.52], [x + s * 0.44, y - s * 0.32]], { fill: GA.khaki, key: key + 'gc', w: lw, tex: [{ k: 'hatch', a: 0.7, gap: 4, al: 0.35 }] }); }
  if (v % 4 === 3) for (let i = 0; i < 9; i++) { const a = Math.PI * (1.05 + i * 0.1); paint(ellipsePts(x + Math.cos(a) * s * fw * 0.95, y - s * 0.06 + Math.sin(a) * s * fh * 0.9, s * 0.1, s * 0.08, 0, 10), { fill: hair, key: key + 'cu' + i, w: lw * 0.7 }); }
  for (const k of [-1, 1]) {
    ink([[x + k * s * 0.2, y - s * 0.1], [x + k * s * 0.08, y - s * (0.12 + 0.02 * (v % 2))]], { w: lw * 1.4, key: key + 'brow' + k, amt: 0.4 });
    const blink = (B + v * 13) % 47 < 2;
    if (blink) ink([[x + k * s * 0.18, y - s * 0.02], [x + k * s * 0.1, y - s * 0.02]], { w: lw, key: key + 'bl' + k, amt: 0.2 });
    else { ctx.fillStyle = C.ink; ctx.beginPath(); ctx.ellipse(x + k * s * 0.14, y - s * 0.02, s * 0.03, s * 0.035, 0, 0, TAU); ctx.fill(); }
  }
  ink([[x + s * 0.02, y], [x + s * 0.05, y + s * 0.14], [x - s * 0.02, y + s * 0.16]], { w: lw, key: key + 'nose', amt: 0.4 });
  ink(arcPts(x, y + s * 0.18, s * 0.12, Math.PI * 0.2, Math.PI * 0.8, 8), { w: lw * 1.1, key: key + 'mouth', amt: 0.4 });
}

// ---- the tank (a Sherman-like silhouette). o: { inflate 0..1, gun 0..1, fake 0..1, valve, dark, key }
function gaTank(x, y, s, o = {}) {
  const key = o.key ?? 'tank', e = EZ.o2(o.inflate ?? 1), sy = lerp(0.14, 1, e), sx = lerp(1.14, 1, e), amt = lerp(16, 1.6, e);
  const T = gaTP(x, y, s, sx, sy), dark = !!o.dark, lineC = dark ? C.periD : C.ink, lw = Math.max(1.6, s * 0.006), hatchC = dark ? 'rgba(150,164,230,0.5)' : C.ink;
  paint(T(rrectPts(-0.47, -0.2, 0.95, 0.2, 0.09, 5)), { fill: dark ? GA.sil : GA.track, key: key + 'tr', w: lw, line: lineC, amt, tex: [{ k: 'hatch', a: Math.PI / 2, gap: Math.max(3, s * 0.016), c: dark ? C.periD : '#14120e', al: 0.5, w: 1.2 }] });
  if (e > 0.25) [[-0.42, -0.1, 0.055], [-0.29, -0.065, 0.06], [-0.15, -0.065, 0.06], [0.0, -0.065, 0.06], [0.14, -0.065, 0.06], [0.28, -0.065, 0.06], [0.41, -0.11, 0.055]].forEach(([u, v, r], i) => {
    const [cx, cy] = T([[u, v]])[0];
    paint(ellipsePts(cx, cy, r * s * sx, r * s * sy, 0, 22), { fill: dark ? GA.night2 : GA.steel, key: key + 'w' + i, w: lw * 0.8, line: lineC, amt: amt * 0.5, tex: [{ k: 'cross', c: hatchC, al: 0.3, gap: 4, dens: gaShade(cx - r * s, cy - r * s, cx + r * s, cy + r * s) }] });
    ink(ellipsePts(cx, cy, r * s * 0.35 * sx, r * s * 0.35 * sy, 0, 12), { closed: true, w: lw * 0.7, color: lineC, key: key + 'hub' + i, amt: 0.6 });
  });
  const hull = T([[-0.47, -0.2], [-0.47, -0.32], [-0.41, -0.37], [0.22, -0.37], [0.48, -0.25], [0.48, -0.2]]), bb = bbox(hull);
  paint(hull, { fill: dark ? GA.sil : GA.olive, key: key + 'h', w: lw * 1.2, line: lineC, amt, tex: dark ? [{ k: 'hatch', a: 0.7, gap: 6, c: hatchC, al: 0.35 }] : [{ k: 'pencil', c: GA.oliveL, al: 0.35, per: 120, dens: (px, py) => 1 - gaShade(bb.x0, bb.y0, bb.x1, bb.y1)(px, py) }, { k: 'cross', c: GA.oliveD, al: 0.5, gap: 5, dens: gaShade(bb.x0, bb.y0, bb.x1, bb.y1) }] });
  const tur = T([[-0.2, -0.37], ...arcPts(-0.02, -0.37, 0.18, Math.PI, Math.PI * 1.5, 8).map(([a, b]) => [a, -0.37 - (-0.37 - b) * 0.85]), [0.1, -0.53], [0.17, -0.47], [0.17, -0.37]]), tb = bbox(tur);
  paint(tur, { fill: dark ? GA.sil : GA.olive, key: key + 't', w: lw * 1.2, line: lineC, amt, tex: dark ? [{ k: 'hatch', a: 0.7, gap: 6, c: hatchC, al: 0.35 }] : [{ k: 'cross', c: GA.oliveD, al: 0.5, gap: 5, dens: gaShade(tb.x0, tb.y0, tb.x1, tb.y1) }] });
  const g = EZ.o3(o.gun ?? 1) * e, droop = lerp(0.28, 0, g), [mx, my] = T([[0.18, -0.445]])[0], L = s * 0.46 * lerp(0.8, 1, g);
  paint(gaCapsule([mx, my], [mx + Math.cos(droop) * L, my + Math.sin(droop) * L], Math.max(3, s * 0.016), 4), { fill: dark ? GA.sil : GA.oliveD, key: key + 'g', w: lw, line: lineC, amt: amt * 0.4 });
  paint(rrectPts(mx - s * 0.02, my - s * 0.035 * sy, s * 0.06, s * 0.07 * sy, 4), { fill: dark ? GA.sil : GA.oliveD, key: key + 'm', w: lw, line: lineC, amt: amt * 0.5 });
  if (e > 0.6 && !dark) { ink(T(arcPts(-0.05, -0.53, 0.05, Math.PI, TAU, 8)), { w: lw, key: key + 'cup', amt: 0.6 }); for (let i = 0; i < 7; i++) { const [rx, ry] = T([[-0.38 + i * 0.1, -0.29]])[0]; ctx.fillStyle = 'rgba(40,36,20,0.6)'; ctx.fillRect(rx - 2, ry - 2, 4, 4); } }
  if (e < 0.95) { const R = RNG('wr', key); for (let i = 0; i < 14; i++) { const u0 = R.r(-0.45, 0.4), v0 = R.r(-0.33, -0.05), du = R.r(0.04, 0.12); ink(T([[u0, v0], [u0 + du * 0.5, v0 - R.r(0.01, 0.04)], [u0 + du, v0 + R.r(-0.02, 0.02)]]), { w: Math.max(1.5, s * 0.004), color: dark ? C.peri : '#2b2a18', alpha: 0.75 * (1 - e), key: key + 'wk' + i, amt: 1.4 }); } }
  if (o.fake) planInk(gaTankOutline(x, y - s * 0.01, s * 1.04), { closed: true, key: key + 'fk', frac: clamp(o.fake), w: Math.max(2.4, s * 0.012), dash: [s * 0.04, s * 0.025] });
  const valve = T([[-0.44, -0.3]])[0];
  if (o.valve || o.fake) paint(ellipsePts(valve[0], valve[1], s * 0.02, s * 0.02, 0, 12), { fill: GA.fake, key: key + 'v', w: lw * 0.8, line: lineC });
  return { valve };
}
function gaTankOutline(x, y, s) {
  return gaTP(x, y, s)([[-0.46, 0], [0.44, 0], [0.5, -0.12], [0.48, -0.25], [0.22, -0.37], [0.17, -0.37], [0.17, -0.47], [0.1, -0.53], [-0.04, -0.55], [-0.15, -0.52], [-0.2, -0.45], [-0.2, -0.37], [-0.41, -0.37], [-0.48, -0.32], [-0.5, -0.12]]);
}
// a covered truck, side view
function gaTruck(x, y, s, o = {}) {
  const key = o.key ?? 'truck', dark = !!o.dark, T = gaTP(x, y, s), lc = dark ? C.periD : C.ink, f = dark ? GA.sil : GA.olive, ht = dark ? C.periD : C.ink;
  paint(T([[-0.52, -0.16], [-0.52, -0.5], ...arcPts(-0.3, -0.5, 0.22, Math.PI, Math.PI * 1.5, 5).map(([a, b]) => [a, b + 0.1]), [0.1, -0.62], [0.12, -0.16]]), { fill: dark ? GA.sil : '#7c7a52', key: key + 'cv', w: 2, line: lc, tex: [{ k: 'hatch', a: Math.PI / 2, gap: 9, c: ht, al: 0.3 }] });
  paint(T([[0.14, -0.16], [0.14, -0.44], [0.33, -0.44], [0.42, -0.28], [0.52, -0.26], [0.52, -0.16]]), { fill: f, key: key + 'c', w: 2, line: lc, tex: [{ k: 'hatch', a: 0.7, gap: 5, c: ht, al: 0.3 }] });
  paint(T([[0.2, -0.4], [0.31, -0.4], [0.37, -0.3], [0.2, -0.3]]), { fill: dark ? '#1d2150' : '#9fb4c0', key: key + 'win', w: 1.6, line: lc });
  [[-0.38, -0.08], [-0.18, -0.08], [0.36, -0.08]].forEach(([u, v], i) => { const [cx, cy] = T([[u, v]])[0]; paint(ellipsePts(cx, cy, s * 0.085, s * 0.085, 0, 14), { fill: dark ? GA.night2 : GA.track, key: key + 'w' + i, w: 1.6, line: lc }); });
  if (o.fake) planInk(T([[-0.56, 0.02], [0.56, 0.02], [0.56, -0.66], [-0.56, -0.66]]), { closed: true, key: key + 'fk', frac: clamp(o.fake), w: 2.6, dash: [10, 7] });
}
function gaGun(x, y, s, o = {}) {   // a towed field gun
  const key = o.key ?? 'gun', dark = !!o.dark, T = gaTP(x, y, s), lc = dark ? C.periD : C.ink, f = dark ? GA.sil : GA.olive;
  paint(gaCapsule(T([[-0.1, -0.22]])[0], T([[0.55, -0.48]])[0], s * 0.035, 4), { fill: f, key: key + 'b', w: 1.8, line: lc });
  paint(T([[-0.25, -0.12], [-0.25, -0.34], [0.12, -0.34], [0.2, -0.12]]), { fill: f, key: key + 's', w: 1.8, line: lc, tex: [{ k: 'hatch', a: 0.7, gap: 5, c: lc, al: 0.3 }] });
  ink(T([[-0.2, -0.1], [-0.6, 0.0]]), { w: 3, color: lc, key: key + 'tr' });
  const [cx, cy] = T([[-0.05, -0.1]])[0]; paint(ellipsePts(cx, cy, s * 0.11, s * 0.11, 0, 16), { fill: dark ? GA.night2 : GA.track, key: key + 'w', w: 1.8, line: lc });
  if (o.fake) planInk(T([[-0.66, 0.04], [0.62, 0.04], [0.62, -0.58], [-0.66, -0.58]]), { closed: true, key: key + 'fk', frac: clamp(o.fake), w: 2.6, dash: [10, 7] });
}
// a bulldozer, side view, facing left (blade at the left). Returns the blade's box [x, y, w, h].
function gaBulldozer(x, y, s, key = 'doz') {
  const T = gaTP(x, y, s), lw = Math.max(2, s * 0.006);
  paint(T(rrectPts(-0.38, -0.2, 0.86, 0.2, 0.1, 5)), { fill: GA.track, key: key + 'tr', w: lw, tex: [{ k: 'hatch', a: Math.PI / 2, gap: 6, c: '#14120e', al: 0.5 }] });
  for (let i = 0; i < 5; i++) { const [cx, cy] = T([[-0.28 + i * 0.165, -0.1]])[0]; paint(ellipsePts(cx, cy, s * 0.055, s * 0.055, 0, 16), { fill: GA.steel, key: key + 'w' + i, w: lw * 0.8 }); }
  paint(T([[-0.3, -0.2], [-0.3, -0.42], [0.1, -0.46], [0.1, -0.2]]), { fill: '#b79a3e', key: key + 'eng', w: lw, tex: [{ k: 'cross', c: '#6e5a1c', al: 0.4, gap: 5 }] });
  for (let i = 0; i < 5; i++) ink(T([[-0.26 + i * 0.07, -0.25], [-0.26 + i * 0.07, -0.4]]), { w: 2, color: '#6e5a1c', key: key + 'gr' + i });
  paint(T([[0.1, -0.2], [0.1, -0.7], [0.42, -0.7], [0.42, -0.2]]), { fill: '#b79a3e', key: key + 'cab', w: lw, tex: [{ k: 'hatch', a: 0.7, gap: 5, al: 0.3 }] });
  paint(T([[0.15, -0.64], [0.37, -0.64], [0.37, -0.46], [0.15, -0.46]]), { fill: '#9fb4c0', key: key + 'win', w: lw * 0.8 });
  ink(T([[-0.1, -0.44], [-0.1, -0.68]]), { w: s * 0.025, color: '#3b3a33', key: key + 'ex' });
  for (let i = 0; i < 3; i++) { const u = mod(TT * 0.9 + i / 3, 1), [ex, ey] = T([[-0.1 - u * 0.12, -0.72 - u * 0.25]])[0]; ctx.fillStyle = `rgba(70,64,58,${0.45 * (1 - u)})`; ctx.beginPath(); ctx.arc(ex, ey, s * (0.03 + u * 0.05), 0, TAU); ctx.fill(); }
  const blade = [x - s * 0.53, y - s * 0.34, s * 0.12, s * 0.36];
  ink(T([[-0.36, -0.24], [-0.43, -0.14]]), { w: s * 0.02, color: '#3b3a33', key: key + 'arm' });
  paint(box(...blade), { fill: '#8d7a3a', key: key + 'bl', w: lw, tex: [{ k: 'cross', c: '#4b3f1a', al: 0.45, gap: 5 }] });
  return blade;
}
// a shoulder patch (generic, illustrative)
function gaPatchPts(x, y, s) { return resample([[x - s * 0.5, y - s * 0.38], [x + s * 0.5, y - s * 0.38], [x, y + s * 0.48]], true, 12); }
function gaPatch(x, y, s, o = {}) {
  const key = o.key ?? 'patch', P = gaPatchPts(x, y, s), p = clamp(o.paint ?? 1);
  paint(P, { fill: '#d7c9a0', key: key + 'b', w: 3, tex: [{ k: 'hatch', a: 0.2, gap: 3, al: 0.25 }, { k: 'hatch', a: 1.77, gap: 3, al: 0.18 }] });
  const fields = [[[x - s * 0.44, y - s * 0.34], [x + s * 0.44, y - s * 0.34], [x + s * 0.3, y - s * 0.12], [x - s * 0.3, y - s * 0.12]], [[x - s * 0.3, y - s * 0.12], [x, y - s * 0.12], [x, y + s * 0.38]], [[x, y - s * 0.12], [x + s * 0.3, y - s * 0.12], [x, y + s * 0.38]]];
  ['#d9b23c', '#3c5a8c', '#7c6a8a'].forEach((c, i) => { if (p > i / 3) paint(fields[i], { fill: c, key: key + 'f' + i, w: 2, tex: [{ k: 'pencil', c: '#ffffff', al: 0.25, per: 50 }] }); });
  if (p >= 1) { ink([[x - s * 0.16, y - s * 0.2], [x + s * 0.16, y - s * 0.2]], { w: s * 0.03, key: key + 'm1' }); ink(ellipsePts(x, y - s * 0.2, s * 0.17, s * 0.06, 0, 18), { closed: true, w: s * 0.02, key: key + 'm2' }); }
  ink(P, { closed: true, w: 2, key: key + 'st', amt: 0.6, color: 'rgba(58,36,23,0.7)', double: true });
  if (o.fake) planInk(ellipsePts(x, y, s * 0.72, s * 0.62, 0.1, 40), { closed: true, key: key + 'fk', frac: clamp(o.fake) });
}
// a cyclist (g14's witnesses). y = the road. o: { k pedal phase, look 0..1 }
function gaCyclist(x, y, s, o = {}) {
  const key = o.key ?? 'cy', r = s * 0.3, wa = [x - s * 0.42, y - r], wb = [x + s * 0.42, y - r], lw = Math.max(2, s * 0.01), sp = o.k ?? 0;
  for (const [i, w] of [wa, wb].entries()) {
    ink(ellipsePts(w[0], w[1], r, r, 0, 36), { closed: true, w: lw * 1.8, key: key + 'wh' + i });
    for (let k = 0; k < 6; k++) { const a = sp + k / 6 * Math.PI; ink([[w[0] - Math.cos(a) * r * 0.92, w[1] - Math.sin(a) * r * 0.92], [w[0] + Math.cos(a) * r * 0.92, w[1] + Math.sin(a) * r * 0.92]], { w: lw * 0.5, alpha: 0.6, key: key + 'sp' + i + k, amt: 0.5 }); }
  }
  const bb = [x - s * 0.02, y - r * 0.95], seat = [x - s * 0.14, y - s * 0.62], bar = [x + s * 0.3, y - s * 0.7];
  ink([wa, bb, wb], { w: lw * 1.6, key: key + 'f1' }); ink([wa, seat, bb], { w: lw * 1.6, key: key + 'f2' }); ink([seat, [x + s * 0.24, y - s * 0.58], bb], { w: lw * 1.6, key: key + 'f3' }); ink([[x + s * 0.24, y - s * 0.58], bar, wb], { w: lw * 1.6, key: key + 'f4' });
  const hip = [seat[0] + s * 0.02, seat[1] - s * 0.04], shd = [x + s * 0.06, y - s * 1.08], pk = [bb[0] + Math.cos(sp * 2) * s * 0.1, bb[1] + Math.sin(sp * 2) * s * 0.1];
  const [kn] = gaIK(hip, pk, s * 0.3, s * 0.3, (a, b) => a[0] > b[0]);
  paint(gaCapsule(hip, kn, s * 0.05, 5), { fill: o.trous ?? '#4f5a6e', key: key + 'th', w: lw }); paint(gaCapsule(kn, pk, s * 0.045, 5), { fill: o.trous ?? '#4f5a6e', key: key + 'sh', w: lw });
  paint([[hip[0] - s * 0.08, hip[1]], [shd[0] - s * 0.1, shd[1]], [shd[0] + s * 0.1, shd[1] + s * 0.02], [hip[0] + s * 0.1, hip[1] + s * 0.02]], { fill: o.coat ?? '#7b6a4e', key: key + 'jk', w: lw, tex: [{ k: 'hatch', a: 0.8, gap: 4, al: 0.35 }] });
  const [el] = gaIK([shd[0] + s * 0.04, shd[1] + s * 0.04], bar, s * 0.24, s * 0.24, (a, b) => a[1] > b[1]);
  paint(gaCapsule([shd[0] + s * 0.04, shd[1] + s * 0.04], el, s * 0.035, 5), { fill: o.coat ?? '#7b6a4e', key: key + 'arm', w: lw }); paint(gaCapsule(el, bar, s * 0.03, 5), { fill: o.coat ?? '#7b6a4e', key: key + 'arm2', w: lw });
  const hx = shd[0] + s * 0.05, hy = shd[1] - s * 0.1, lk = clamp(o.look ?? 0);
  paint(ellipsePts(hx, hy, s * 0.075, s * 0.085, 0, 16), { fill: GA.skin, key: key + 'hd', w: lw });
  paint(ellipsePts(hx - s * 0.01, hy - s * 0.07, s * 0.09, s * 0.035, -0.15, 14), { fill: o.hat ?? '#2c2a33', key: key + 'bt', w: lw });
  ctx.fillStyle = C.ink; ctx.beginPath(); ctx.arc(hx + s * lerp(0.04, -0.035, lk), hy, Math.max(1.5, s * 0.012), 0, TAU); ctx.fill();
}
