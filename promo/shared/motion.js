// Time-only animation helpers: every value is a pure function of t, so any frame renders alone.

export const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v));
export const lerp = (a, b, k) => a + (b - a) * k;
// 0→1 progress of t through [a, b].
export const prog = (t, a, b) => clamp((t - a) / (b - a));
export const easeInOut = k => (k < 0.5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2);
export const easeOut = k => 1 - Math.pow(1 - k, 3);
export const easeIn = k => k * k * k;
export const smooth = k => k * k * (3 - 2 * k);

// Closed-form damped spring: 0→1 response x seconds after a target change (xilo craft rules).
export function spring(x, w = 16, z = 0.72) {
  if (x <= 0) return 0;
  const wd = w * Math.sqrt(1 - z * z);
  return 1 - Math.exp(-z * w * x) * (Math.cos(wd * x) + (z * w / wd) * Math.sin(wd * x));
}
// Value that springs through a list of [time, target] keys; starts at keys[0][1].
export function springTo(t, keys, w, z) {
  let v = keys[0][1];
  for (let i = 1; i < keys.length; i++) v += (keys[i][1] - keys[i - 1][1]) * spring(t - keys[i][0], w, z);
  return v;
}
// Spring presets by role, as in the craft rules table.
export const SPRING = { snappy: [24, 0.8], card: [15, 0.72], heavy: [10, 0.9], mascot: [18, 0.45] };

// Seeded pseudo-random in [0, 1).
export function rnd(seed) {
  const s = Math.sin(seed * 127.1 + 311.7) * 43758.5453;
  return s - Math.floor(s);
}

// Hop arc: 0 at both ends, 1 at the top.
export const hop = k => (k <= 0 || k >= 1 ? 0 : Math.sin(Math.PI * k));

// Quantise time to a frame rate, for pixel-art poses that update at 8–12 fps.
export const step = (t, fps) => Math.floor(t * fps) / fps;

// Per-character times for a typed string, with seeded jitter so the rhythm feels human.
export function typing(text, t0, cps, seed = 1) {
  const out = [];
  let t = t0;
  [...text].forEach((ch, i) => {
    out.push(t);
    t += (1 / cps) * (0.55 + 0.9 * rnd(seed * 97 + i)) * (ch === ' ' ? 1.5 : 1);
  });
  return out;
}
export const typed = (times, t) => { let n = 0; while (n < times.length && times[n] <= t) n++; return n; };

// Load every face/text pair before the first frame so unicode-range subsets are ready.
export async function loadFonts(pairs) {
  await Promise.all(pairs.map(([font, text]) => document.fonts.load(font, text)));
  await document.fonts.ready;
}
