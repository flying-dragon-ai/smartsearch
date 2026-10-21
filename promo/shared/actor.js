// DOM helpers and the Clawd actor shared by the tutorial films (the feature film keeps its own copy).
import { clawdSVG } from './clawd.js';

export const $ = id => document.getElementById(id);
export const css = (el, props) => { for (const k in props) if (el.style[k] !== props[k]) el.style[k] = props[k]; };
export const html = (el, h) => { if (el._h !== h) { el.innerHTML = h; el._h = h; } };
export const vis = (el, on, mode = 'block') => css(el, { display: on ? mode : 'none' });
export const cls = (el, name, on) => { if (el && el.classList.contains(name) !== !!on) el.classList.toggle(name, !!on); };

// Clawd drawn as an SVG grid; feet sit at (x, y).
export class Actor {
  constructor(el, px = 9) { this.el = el; this.px = px; this.key = ''; }
  draw(o) {
    if (!o) { vis(this.el, false); return; }
    vis(this.el, true);
    const pose = o.pose || {}, PX = this.px;
    const key = JSON.stringify(pose) + (o.extra || '') + (o.flip ? 'f' : '');
    if (key !== this.key) { this.el.innerHTML = clawdSVG({ px: PX, pad: 3, glint: true, flip: o.flip, extra: o.extra || '', ...pose }); this.key = key; }
    const W = 24 * PX, feet = 13 * PX, z = o.z ?? 1, sq = o.sq || 0;
    css(this.el, {
      transformOrigin: `${W / 2}px ${feet}px`,
      transform: `translate(${(o.x - W / 2).toFixed(2)}px, ${(o.y - feet).toFixed(2)}px) scale(${(z * (1 + sq * 0.7)).toFixed(4)}, ${(z * (1 - sq)).toFixed(4)}) rotate(${o.rot || 0}deg)`,
      opacity: String(o.op ?? 1),
    });
  }
}
