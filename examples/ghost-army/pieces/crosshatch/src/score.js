  // =====================================================================
  //  SCORE BODY — Ghost Army crosshatch scenes (inside buildScore(); kit/score-head.js). Derived from GA_SCENES.
  //  Each era: a pad on its own chord, a sparse pluck line on the beat, its own sound effects at its own beats.
  //  g03: silence on the held Rhine, then the loudest hit on the reveal. (The studio mixes narration on top.)
  // =====================================================================
  const each = (t0, t1, step, fn) => { for (let k = 0; t0 + k * step < t1 - 1e-6; k++) fn(t0 + k * step, k); };
  const CH = { g01: ['D3', 'A3', 'F3'], g03: ['D3', 'A3', 'F3'], g04: ['D3', 'F3', 'A3', 'D4'], g05: ['E3', 'A3', 'C4'], g10: ['F3', 'A3', 'C4'],
    g11: ['F3', 'C4', 'A3'], g13: ['D3', 'A3', 'E4'], g14: ['G3', 'D4', 'B3'], g18: ['D3', 'A3', 'E4', 'A4'], g19: ['E3', 'B3', 'G3'],
    g21: ['D3', 'A3', 'E4'], g25: ['F3', 'A3', 'C4'], g27: ['D3', 'A3'], g32: ['E3', 'G3', 'B3'], g33: ['D3', 'F3'], g35: ['F3', 'A3', 'C4'], g41: ['D3', 'Fs3', 'A3', 'D4'], g45: ['D3', 'A3', 'Fs4'] };
  const QUIET = { g27: true, g33: true };
  for (const s of GA_SCENES) {
    const ch = CH[s.id] || ['D3', 'A3'], quiet = s.id === 'g03' ? rhReveal(s) + 0.2 : s.start;
    to = 'm';
    if (s.id === 'g01' || s.id === 'g03') drone(quiet, s.end + 0.2, nz('D2'), 0.035, { att: 1.0, rel: 0.5 });
    pad(quiet, s.end + 0.15, ch, 0.026, { type: 'triangle', cut: 900, att: 0.5, rel: 0.3, send: 0.3 });
    const arp = ch.map((n) => nz(n) * 2);
    if (!QUIET[s.id]) each(quiet + 0.5, s.end - 0.3, BEAT * (s.id === 'g18' || s.id === 'g13' ? 0.5 : 1), (t, k) => pluck(t, arp[k % arp.length], 0.035 * (k % 2 ? 0.75 : 1), Math.sin(k) * 0.3, 0.4, 2400, 0.25));
    to = 's';
    if (s.id === 'g01') each(s.start, s.end, 1.7, (t, k) => noiseHit(t, 1.2, 'bandpass', 500 + (k % 3) * 120, 0.8, 0.012, Math.sin(k) * 0.5, 0.4));
    if (s.id === 'g03') {
      const rv = rhReveal(s);
      to = 'm'; ['D3', 'A3', 'D4', 'F4'].forEach((n) => pluck(rv, nz(n), 0.22, 0, 0.5, 2600, 0.3));
      to = 's'; sub(rv, 0.5); noiseHit(rv, 0.4, 'lowpass', 900, 0.8, 0.3, 0, 0.3);
      each(gaAt(s, 0.36, 3.0), s.end - 0.3, BEAT, (t) => noiseHit(t, 0.4, 'lowpass', 160, 1, 0.05, 0.4));   // the recorded engines
    }
    if (s.id === 'g04') { const t0 = gaAt(s, 0.05, 0.4, 1.2); each(t0, t0 + 2.0, E16, (t, k) => { if (k % 3 !== 2) noiseHit(t, 0.05, 'bandpass', 3800, 2, 0.04, -0.2); }); noiseHit(gaAt(s, 0.68, 6.0), 0.12, 'lowpass', 400, 1, 0.12, 0.2); }
    if (s.id === 'g05') { const t0 = gaAt(s, 0.32, 3.0); each(t0, t0 + gaNoteLen(['MEMO', 'R. INGERSOLL PROPOSES', 'A UNIT DEDICATED', 'TO DECEPTION']), 0.09, (t) => blip(t, 1500, 1300, 0.02, 0.03)); }
    if (s.id === 'g10') { const t0 = gaAt(s, 0.42, 3.2); sweep(t0, t0 + Math.max(1.2, Math.min(3.0, s.dur * 0.18)), 0.01, 300, 2200, 0); }
    if (s.id === 'g11') for (let i = 1; i < 4; i++) { const ti = Math.max(gaAt(s, 0.06 + 0.17 * i, 0.4 + i * 1.3), s.start + i * 1.2); noiseHit(ti, 0.08, 'lowpass', 600, 1, 0.08, 0); each(ti + 0.3, ti + 1.2, E16, (t) => noiseHit(t, 0.05, 'bandpass', 3800, 2, 0.03, 0.1)); }
    if (s.id === 'g13') { const [i0, i1] = dcInflate(s); each(i0, i1, BEAT, (t) => noiseHit(t, 0.35, 'highpass', 2500, 0.7, 0.05, -0.4, 0.2, 6000)); }
    if (s.id === 'g14') { each(dcLift(s) + 1.2, s.end - 0.2, BEAT / 2, (t, k) => noiseHit(t, 0.06, 'lowpass', 300, 1, 0.07, k % 2 ? 0.3 : -0.3)); chime(gaAt(s, 0.16, 1.4, 3.0) + 2.4, [nz('A5'), nz('E6')], 0.05); }
    if (s.id === 'g18') each(gaAt(s, 0.45, 5.0), gaAt(s, 0.62, 6.5), 0.3, (t) => noiseHit(t, 0.25, 'highpass', 5000, 0.7, 0.04, 0.3));
    if (s.id === 'g21') { const f0 = gaAt(s, 0.5, 4.2, 1e9, 4.0); for (let i = 0; i < 5; i++) noiseHit(f0 + i * Math.max(0.6, s.dur * 0.05), 0.5, 'lowpass', 220, 1, 0.1, -0.3 + i * 0.15, 0.3); }
    if (s.id === 'g25') each(s.start + 0.5, s.end - 0.3, BEAT, (t, k) => noiseHit(t, 0.05, 'lowpass', 320, 1, 0.04, k % 2 ? 0.2 : -0.2));
    if (s.id === 'g32') each(gaAt(s, 0.05, 0.5), gaAt(s, 0.05, 0.5) + s.dur * 0.5, 0.11, (t, k) => { if (k % 5 !== 4) noiseHit(t, 0.03, 'bandpass', 2600, 2, 0.05, 0.1); });
    if (s.id === 'g33') each(gaAt(s, 0.12, 1.2), gaAt(s, 0.72, 8.0, 1e9, 3.0), 0.6, (t) => blip(t, 900, 600, 0.03, 0.02));
    if (s.id === 'g35') { const tp = gaAt(s, 0.5, 9.0, 1e9, 6.0); noiseHit(tp, 0.08, 'lowpass', 500, 1, 0.1, 0.3); each(tp, s.end - 0.2, 0.9, (t) => noiseHit(t, 0.9, 'highpass', 6000, 0.7, 0.006, 0.3)); }
    if (s.id === 'g19') each(s.start + 0.3, s.end - 0.2, BEAT, (t) => noiseHit(t, 0.45, 'lowpass', 140, 1, 0.06, -0.2));
  }
  to = 's';
  for (const b of BRIDGES) sweep(b.tc - 0.45, b.tc + 0.05, 0.01, 400, 2400, 0);
