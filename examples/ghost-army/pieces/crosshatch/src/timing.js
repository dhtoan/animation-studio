// Scene timing for the crosshatch eras. The studio pipeline OVERWRITES this file in its work copy with the
// narration-driven times (scenes in timeline order; start/end in seconds on this piece's own clock).
// bridge_next: true = shape-morph into the next listed scene (they are adjacent on the final timeline);
//              false = a clean cut (the next timeline scene is drawn by another engine).
window.GA_TIMING = {
  fps: 30,
  scenes: [
    { id: 'g01', start: 0, end: 13, bridge_next: false },
    { id: 'g03', start: 13, end: 26, bridge_next: false },
    { id: 'g04', start: 26, end: 38, bridge_next: false },
    { id: 'g05', start: 38, end: 52, bridge_next: false },
    { id: 'g10', start: 52, end: 65, bridge_next: true },
    { id: 'g11', start: 65, end: 78, bridge_next: false },
    { id: 'g13', start: 78, end: 94, bridge_next: true },
    { id: 'g14', start: 94, end: 108, bridge_next: false },
    { id: 'g18', start: 108, end: 123, bridge_next: true },
    { id: 'g19', start: 123, end: 136, bridge_next: false },
  ],
};
