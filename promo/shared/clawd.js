// Clawd, the pixel mascot from the Claude Code terminal logo, as an 18x10 grid of square pixels.
// The logo is three lines of quadrant characters:   ▐▛███▜▌ / ▝▜█████▛▘ / ▘▘ ▝▝
// Every character cell is 2x2 quadrants and each quadrant row is doubled, so the quadrants
// become square pixels: a 12x8 body (cols 3-14), 2x2 arm stubs (cols 1-2 / 15-16, rows 4-5),
// four 1x2 legs (cols 4, 6, 11, 13) and two 1x2 eyes (cols 5 and 12, rows 2-3).
// Same derivation as lemomo-ai/lemo-opuscar (MIT). Unofficial fan depiction; Clawd belongs to Anthropic.

export const PAL = {
  body: '#D97757', shade: '#B85F40', eye: '#2A2622',
  ring: '#2B3040', lens: 'rgba(214,233,255,.62)', glint: '#FFFFFF',
  gold: '#F2C14E', green: '#2F9E4F', red: '#E0543A', sweat: '#7FB6E8', ink: '#2A2622', white: '#FFFFFF',
};

const EYES = {
  n: [[5, 2], [5, 3], [12, 2], [12, 3]],
  l: [[4, 2], [4, 3], [11, 2], [11, 3]],
  r: [[6, 2], [6, 3], [13, 2], [13, 3]],
  u: [[5, 1], [5, 2], [12, 1], [12, 2]],
  d: [[5, 3], [5, 4], [12, 3], [12, 4]],
  blink: [[5, 3], [12, 3]],
  happy: [[4, 3], [5, 2], [6, 3], [11, 3], [12, 2], [13, 3]],
  wide: [[5, 1], [5, 2], [5, 3], [12, 1], [12, 2], [12, 3]],
  shut: [[4, 3], [5, 3], [6, 3], [11, 3], [12, 3], [13, 3]],
  squint: [[4, 2], [5, 3], [4, 4], [13, 2], [12, 3], [13, 4]],
  none: [],
};
const ARMS = {
  down: [[1, 4], [2, 4], [1, 5], [2, 5], [15, 4], [16, 4], [15, 5], [16, 5]],
  // Raised stubs rise two pixels above the head so the silhouette reads as arms, not shoulders.
  up: [[1, -2], [2, -2], [1, -1], [2, -1], [1, 0], [2, 0], [1, 1], [2, 1], [15, -2], [16, -2], [15, -1], [16, -1], [15, 0], [16, 0], [15, 1], [16, 1]],
  wave: [[1, 4], [2, 4], [1, 5], [2, 5], [15, -2], [16, -2], [15, -1], [16, -1], [15, 0], [16, 0], [15, 1], [16, 1]],
  out: [[0, 4], [1, 4], [2, 4], [0, 5], [1, 5], [2, 5], [15, 4], [16, 4], [17, 4], [15, 5], [16, 5], [17, 5]],
  hold: [[1, 4], [2, 4], [1, 5], [2, 5], [15, 5], [16, 5], [15, 6], [16, 6]],
  tuck: [],
};
const LEGS = {
  stand: [[4, 2], [6, 2], [11, 2], [13, 2]],
  walkA: [[4, 2], [6, 1], [11, 2], [13, 1]],
  walkB: [[4, 1], [6, 2], [11, 1], [13, 2]],
  tuck: [[4, 1], [6, 1], [11, 1], [13, 1]],
  none: [],
};

// [[col, row, kind]] with kind 'body' | 'shade' | 'eye'.
export function cells({ eyes = 'n', arms = 'down', legs = 'stand' } = {}) {
  const m = new Map();
  const put = (c, r, k) => m.set(c + ',' + r, [c, r, k]);
  for (let r = 0; r < 8; r++) for (let c = 3; c <= 14; c++) put(c, r, r === 7 ? 'shade' : 'body');
  for (const [c, r] of ARMS[arms]) put(c, r, 'body');
  for (const [c, h] of LEGS[legs]) for (let r = 8; r < 8 + h; r++) put(c, r, 'body');
  for (const [c, r] of EYES[eyes]) put(c, r, 'eye');
  return [...m.values()];
}

// Magnifying glass from the Smart Search icon: dark ring, pale blue lens, white glint.
// The ring spans cells 0-7, so the lens centre is (4, 4): placing the art at (9, -1) puts the
// lens over the right eye (col 12-13, rows 1-4) with the handle in the 'hold' hand.
export const MAGNIFIER = {
  rows: [
    '..kkkk....',
    '.kbbbbk...',
    'kbwbbbbk..',
    'kbwbbbbk..',
    'kbbbbbbk..',
    'kbbbbbbk..',
    '.kbbbbkh..',
    '..kkkkhhh.',
    '.......hhh',
    '........hh',
  ],
  pal: { k: PAL.ring, b: PAL.lens, w: PAL.glint, h: PAL.ring },
  lens: [4, 4],
};
// The eye seen through the lens: twice the size, drawn after the lens.
export const BIG_EYE = { rows: ['ee', 'ee', 'ee', 'ee'], pal: { e: PAL.eye } };
// The old magnifier (the built-in search): grey ring, fogged lens, a crack across it.
export const OLD_MAGNIFIER = {
  rows: MAGNIFIER.rows.map((row, r) => [...row].map((ch, c) => (ch === 'b' || ch === 'w') && (c + r === 7 || c + r === 8 && r % 2) ? 'x' : ch).join('')),
  pal: { k: '#8E8A84', b: 'rgba(200,200,196,.88)', w: 'rgba(200,200,196,.88)', h: '#6E5440', x: '#5A5650' },
};
// What Clawd sees through the fogged lens: a smudge instead of an eye.
export const FOG_EYE = { rows: ['.ss.', 'ssss', 'ssss', '.ss.'], pal: { s: 'rgba(120,116,110,.55)' } };
// Pixel art from a glyph mask: '#' cells get `fill`, and every empty neighbour gets an `ink` outline.
export function outlined(mask, fill, ink = PAL.ink) {
  const H = mask.length + 2, W = mask[0].length + 2;
  const on = (c, r) => r >= 1 && r <= mask.length && c >= 1 && c <= mask[0].length && mask[r - 1][c - 1] === '#';
  const rows = [];
  for (let r = 0; r < H; r++) {
    let row = '';
    for (let c = 0; c < W; c++) {
      let near = false;
      for (let dr = -1; dr <= 1; dr++) for (let dc = -1; dc <= 1; dc++) near ||= on(c + dc, r + dr);
      row += on(c, r) ? 'f' : near ? 'k' : '.';
    }
    rows.push(row);
  }
  return { rows, pal: { f: fill, k: ink } };
}

export const ICONS = {
  bang: outlined(['#', '#', '#', '#', '.', '#'], PAL.white),
  question: outlined(['.###.', '#...#', '....#', '..##.', '..#..', '.....', '..#..'], PAL.white),
  spark: { rows: ['..y..', '..y..', 'yy.yy', '..y..', '..y..'], pal: { y: PAL.gold } },
  sparkW: { rows: ['..y..', '.yyy.', 'yyyyy', '.yyy.', '..y..'], pal: { y: PAL.white } },
  sweat: { rows: ['.b.', 'bbb', 'bbb', '.b.'], pal: { b: PAL.sweat } },
  heart: { rows: ['.rr.rr.', 'rrrrrrr', 'rrrrrrr', '.rrrrr.', '..rrr..', '...r...'], pal: { r: PAL.red } },
  check: { rows: ['.....g', '....gg', 'g..gg.', 'gggg..', '.gg...'], pal: { g: PAL.green } },
  cross: { rows: ['r...r', '.r.r.', '..r..', '.r.r.', 'r...r'], pal: { r: PAL.red } },
};

const COLOR = { body: PAL.body, shade: PAL.shade, eye: PAL.eye };

// Canvas. x, y = point between the feet; px = size of one Clawd pixel; sq > 0 squashes,
// sq < 0 stretches; flip faces left. Edges snap to whole canvas pixels so a low-resolution
// pixel canvas stays crisp under squash.
export function drawClawd(ctx, { x, y, px = 1, flip = false, sq = 0, alpha = 1, outline = null, ...pose }) {
  const sx = px * (1 + sq * 0.7), sy = px * (1 - sq);
  const ox = x - 9 * sx, oy = y - 10 * sy;
  const R = (c, r) => {
    const cc = flip ? 17 - c : c;
    const x0 = Math.round(ox + cc * sx), x1 = Math.round(ox + (cc + 1) * sx);
    const y0 = Math.round(oy + r * sy), y1 = Math.round(oy + (r + 1) * sy);
    return [x0, y0, x1 - x0, y1 - y0];
  };
  ctx.save();
  ctx.globalAlpha *= alpha;
  const list = cells(pose);
  if (outline) {
    const o = Math.max(1, Math.round(px * 0.5));
    ctx.fillStyle = outline;
    for (const [c, r] of list) { const [a, b, w, h] = R(c, r); ctx.fillRect(a - o, b - o, w + 2 * o, h + 2 * o); }
  }
  for (const [c, r, k] of list) { ctx.fillStyle = COLOR[k]; const [a, b, w, h] = R(c, r); ctx.fillRect(a, b, w, h); }
  ctx.restore();
}

// Canvas pixel art from rows of palette keys; (x, y) is the top-left corner.
export function drawPixart(ctx, art, x, y, px = 1, alpha = 1) {
  ctx.save();
  ctx.globalAlpha *= alpha;
  art.rows.forEach((row, r) => [...row].forEach((ch, c) => {
    const col = art.pal[ch];
    if (!col) return;
    ctx.fillStyle = col;
    ctx.fillRect(Math.round(x + c * px), Math.round(y + r * px), Math.round(x + (c + 1) * px) - Math.round(x + c * px), Math.round(y + (r + 1) * px) - Math.round(y + r * px));
  }));
  ctx.restore();
}

function rectsPath(list) {
  return list.map(([c, r]) => `M${c} ${r}h1v1h-1z`).join('');
}

// SVG string in Clawd-pixel units (viewBox 18x10, padded by `pad` for outlines and props).
// Position it with CSS; the caller owns transforms such as springs and squash.
export function clawdSVG({ px = 8, flip = false, outline = null, outlineWidth = 0.6, pad = 1, glint = false, extra = '', ...pose } = {}) {
  const list = cells(pose).map(([c, r, k]) => [flip ? 17 - c : c, r, k]);
  let s = '';
  if (outline) {
    const o = outlineWidth;
    s += `<path fill="${outline}" d="${list.map(([c, r]) => `M${c - o} ${r - o}h${1 + 2 * o}v${1 + 2 * o}h${-1 - 2 * o}z`).join('')}"/>`;
  }
  for (const k of ['body', 'shade', 'eye']) s += `<path fill="${COLOR[k]}" d="${rectsPath(list.filter(e => e[2] === k))}"/>`;
  if (glint) {
    // A small catch-light on the top cell of each eye column: cute at high resolution, skipped on pixel canvases.
    const tops = new Map();
    for (const [c, r, k] of list) if (k === 'eye' && (!tops.has(c) || r < tops.get(c))) tops.set(c, r);
    s += `<path fill="${PAL.glint}" d="${[...tops].map(([c, r]) => `M${c + 0.12} ${r + 0.12}h0.38v0.38h-0.38z`).join('')}"/>`;
  }
  const W = 18 + 2 * pad, H = 10 + 2 * pad;
  return `<svg viewBox="${-pad} ${-pad} ${W} ${H}" width="${W * px}" height="${H * px}" shape-rendering="crispEdges" style="overflow:visible">${s}${extra}</svg>`;
}

// SVG fragment of pixel art at grid offset (x, y) inside a Clawd SVG or any pixel-unit SVG.
export function pixartSVG(art, x = 0, y = 0) {
  const by = {};
  art.rows.forEach((row, r) => [...row].forEach((ch, c) => { if (art.pal[ch]) (by[art.pal[ch]] ||= []).push([x + c, y + r]); }));
  return Object.entries(by).map(([col, list]) => `<path fill="${col}" d="${rectsPath(list)}"/>`).join('');
}
