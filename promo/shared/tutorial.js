// Shared machinery of the tutorial films: measured camera framings, the pointer's path, captions,
// the step chip, sparkles and Clawd's corner cheers. Every function is a pure function of t.
import { clamp, lerp, prog, easeInOut, easeOut, easeIn, spring, springTo, SPRING, hop, rnd } from './motion.js';
import { pixartSVG, ICONS } from './clawd.js';
import { $, css, html } from './actor.js';

export const pop = (t, t0, preset = SPRING.mascot) => spring(t - t0, ...preset);
// The usable frame sits between the step chip and the caption.
export const FRAME = { x0: 60, x1: 1860, y0: 140, y1: 930 };

const stageScale = () => innerWidth / 1920;
// World rectangle of one or more elements, measured with the camera at identity.
export function rectOf(ids) {
  const s = stageScale(), sr = $('stage').getBoundingClientRect();
  let x0 = Infinity, y0 = Infinity, x1 = -Infinity, y1 = -Infinity;
  for (const id of [].concat(ids)) {
    const r = $(id).getBoundingClientRect();
    x0 = Math.min(x0, (r.left - sr.left) / s); y0 = Math.min(y0, (r.top - sr.top) / s);
    x1 = Math.max(x1, (r.right - sr.left) / s); y1 = Math.max(y1, (r.bottom - sr.top) / s);
  }
  return { x: x0, y: y0, w: x1 - x0, h: y1 - y0 };
}
export function framing(r, zMax) {
  const z = Math.min(zMax, (FRAME.x1 - FRAME.x0 - 80) / r.w, (FRAME.y1 - FRAME.y0 - 60) / r.h);
  return { cx: r.x + r.w / 2, cy: r.y + r.h / 2, z };
}
// ?gif in the page URL cuts between framings instead of easing, so a GIF only stores what changes inside a shot.
export const GIF = new URLSearchParams(location.search).has('gif');
// cams: [[t, {cx, cy, z}], ...] springing from one framing to the next (or cutting, in GIF mode).
export function camAt(t, cams) {
  if (GIF) {
    // Cut halfway through each move, where the eased camera would be.
    const f = cams.filter(([k]) => t >= k + 0.35).pop() || cams[0];
    return { z: f[1].z, tx: 960 - f[1].cx * f[1].z, ty: (FRAME.y0 + FRAME.y1) / 2 - f[1].cy * f[1].z };
  }
  const z = springTo(t, cams.map(([k, f]) => [k, f.z]), 5, 0.95);
  const cx = springTo(t, cams.map(([k, f]) => [k, f.cx]), 5, 0.95);
  const cy = springTo(t, cams.map(([k, f]) => [k, f.cy]), 5, 0.95);
  return { z, tx: 960 - cx * z, ty: (FRAME.y0 + FRAME.y1) / 2 - cy * z };
}
// clicks: [{arrive, press, x, y}]. The pointer glides on a slight arc, rests, presses, then waits for the next move.
export function pointerAt(t, clicks, start, from, until) {
  if (t < from || t >= until) return null;
  let prev = start, prevT = from;
  for (const c of clicks) {
    const t0 = Math.max(prevT, c.arrive - 0.8);
    if (t < t0) return { ...prev };
    if (t < c.arrive) {
      const k = easeInOut(prog(t, t0, c.arrive)), dx = c.x - prev.x, dy = c.y - prev.y, len = Math.hypot(dx, dy) || 1;
      const arc = Math.min(80, len * 0.12) * Math.sin(Math.PI * k);
      return { x: lerp(prev.x, c.x, k) - dy / len * arc, y: lerp(prev.y, c.y, k) + dx / len * arc };
    }
    if (t < c.press + 0.2) return { x: c.x, y: c.y, down: t >= c.press && t < c.press + 0.12 };
    prev = c; prevT = c.press + 0.2;
  }
  return { ...prev };
}
// Clawd pops up from the bottom-right corner for each finished step, jumps, and sinks back.
export function cheerAt(t, cheers, x = 1740) {
  const c = cheers.find(c => t >= c - 0.35 && t < c + 1.9);
  if (c === undefined) return null;
  const up = easeOut(prog(t, c - 0.35, c)), down = easeIn(prog(t, c + 1.5, c + 1.9));
  const jump = t >= c && t < c + 0.45 ? hop((t - c) / 0.45) : 0, d = t - c - 0.45;
  return { x, y: 1080 + 150 * (1 - up) + 170 * down - 80 * jump, sq: jump ? -0.12 : d > 0 ? 0.25 * Math.exp(-d * 9) * Math.cos(d * 22) : 0,
    pose: { eyes: 'happy', arms: jump ? 'up' : Math.floor((t - c) * 4) % 2 ? 'wave' : 'up', legs: jump ? 'tuck' : 'stand' }, cheer: c };
}
// items: [t0, t1, html]; springs in from below and fades out.
export function capText(el, t, items) {
  const it = items.find(([a, b]) => t >= a && t < b);
  if (!it) { css(el, { opacity: '0' }); return; }
  html(el, it[2]);
  const k = Math.min(spring(t - it[0], ...SPRING.card), 1 - easeIn(prog(t, it[1] - 0.2, it[1])));
  css(el, { opacity: String(clamp(k * 1.5)), transform: `translateX(-50%) translateY(${((1 - k) * 36).toFixed(1)}px)` });
}
export function stepChip(t, steps, until) {
  const st = steps.filter(([a]) => t >= a).pop();
  const on = st && t < until;
  css($('chip'), { opacity: on ? '1' : '0' });
  if (!on) return;
  html($('chipN'), st[1]); html($('chipT'), st[2]); html($('chipS'), st[3]);
  const k = pop(t, st[0], [20, 0.55]);
  css($('chip'), { transform: `scale(${(0.5 + 0.5 * k).toFixed(4)}) rotate(${((1 - k) * -6).toFixed(2)}deg)` });
}
export function sparkles(x, y, t, t0, n = 6, spread = 110, s = 7) {
  let out = '';
  const k = prog(t, t0, t0 + 0.9);
  if (k <= 0 || k >= 1) return out;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + rnd(i + t0) * 0.6, r = spread * easeOut(k) * (0.7 + 0.5 * rnd(i * 7 + t0));
    if (Math.floor((t - t0) * 12 + i) % 3 === 0) continue;
    out += `<svg style="position:absolute;left:${x + Math.cos(a) * r - 2.5 * s}px;top:${y - 50 + Math.sin(a) * r * 0.7 - 2.5 * s}px;opacity:${1 - k}" width="${5 * s}" height="${5 * s}" viewBox="0 0 5 5" shape-rendering="crispEdges">${pixartSVG(i % 2 ? ICONS.spark : ICONS.sparkW)}</svg>`;
  }
  return out;
}
// A marker ring: {a, b, x, y, w, h} in world coordinates.
export function marker(el, t, rings) {
  const h = rings.find(h => t >= h.a && t < h.b);
  css(el, { display: h ? 'block' : 'none' });
  if (!h) return;
  const k = Math.min(1, spring(t - h.a, ...SPRING.snappy)), out = prog(t, h.b - 0.2, h.b);
  css(el, { left: `${h.x}px`, top: `${h.y}px`, width: `${h.w}px`, height: `${h.h}px`, opacity: String(clamp(k * 2) * (1 - out)), transform: `scale(${1.06 - 0.06 * k})` });
}
