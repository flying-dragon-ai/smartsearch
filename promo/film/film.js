// 同一个问题: the built-in search on the left (8 fps, grey) against Smart Search on the right (60 fps).
// Every frame is a pure function of t; all times come from timeline.js, which the sound script reads too.
import { clawdSVG, pixartSVG, MAGNIFIER, BIG_EYE, OLD_MAGNIFIER, FOG_EYE, ICONS } from '../shared/clawd.js';
import { clamp, lerp, prog, easeInOut, easeOut, easeIn, spring, springTo, SPRING, hop, rnd, loadFonts } from '../shared/motion.js';
import { T, PROMPT, INSTALL, SETUP, QUESTION, ANSWER_R, ANSWER_L, QUOTE, QUOTE_HI, SOURCES, AGENTS, ROUTES, RESEARCH, nodeT, TYPE, typed } from './timeline.js';
import { appMarkup, showPage, providerList, input as appInput } from '../shared/app.js';

const $ = id => document.getElementById(id);
const stage = $('stage');
const fit = () => { stage.style.transform = `scale(${innerWidth / 1920})`; };
fit(); addEventListener('resize', fit);
// The montage's App window is injected first so its text is part of the font preload.
document.getElementById('appMB').innerHTML = appMarkup('mbA', { w: 1440, h: 800, left: 240, top: 220 });

const step8 = t => Math.floor(t * 8) / 8;
const PX = 9;
const css = (el, props) => { for (const k in props) if (el.style[k] !== props[k]) el.style[k] = props[k]; };
const html = (el, h) => { if (el._h !== h) { el.innerHTML = h; el._h = h; } };
const vis = (el, on) => css(el, { display: on ? 'block' : 'none' });
const pop = (t, t0, preset = SPRING.mascot) => spring(t - t0, ...preset);

// ---------- Clawd actors (drawn in the overlay, positioned through the world cameras) ----------
class Actor {
  constructor(el) { this.el = el; this.key = ''; }
  draw(o) {
    if (!o) { vis(this.el, false); return; }
    vis(this.el, true);
    const pose = o.pose || {};
    const key = JSON.stringify(pose) + (o.extra || '') + (o.flip ? 'f' : '');
    if (key !== this.key) { this.el.innerHTML = clawdSVG({ px: PX, pad: 3, glint: true, flip: o.flip, extra: o.extra || '', ...pose }); this.key = key; }
    const W = 24 * PX, feet = 13 * PX, z = o.z ?? 1, sq = o.sq || 0;
    css(this.el, {
      transformOrigin: `${W / 2}px ${feet}px`,
      transform: `translate(${(o.x - W / 2).toFixed(2)}px, ${(o.y - feet).toFixed(2)}px) scale(${(z * (1 + sq * 0.7)).toFixed(4)}, ${(z * (1 - sq)).toFixed(4)}) rotate(${o.rot || 0}deg)`,
      filter: o.grey ? `grayscale(${o.grey})` : 'none', opacity: String(o.op ?? 1),
    });
  }
}
const actorL = new Actor($('aL')), actorR = new Actor($('aR')), actorE = new Actor($('aE'));
const LENS = pixartSVG(MAGNIFIER, 9, -1) + pixartSVG(BIG_EYE, 12, 1);
const OLD_LENS = pixartSVG(OLD_MAGNIFIER, 9, -1) + pixartSVG(FOG_EYE, 11, 1);
const Q = pixartSVG(ICONS.question, 15, -12), SWEAT = pixartSVG(ICONS.sweat, 17, -1), BANG = pixartSVG(ICONS.bang, 16, -11);

// ---------- cameras ----------
// A camera maps world point (cx, cy) to screen point (sx, sy) at zoom z.
const cam = (z, cx, cy, sx, sy) => ({ z, tx: sx - cx * z, ty: sy - cy * z });
const proj = (c, x, y) => [c.tx + x * c.z, c.ty + y * c.z];

function camL(t) {
  if (t < T.split) {
    // Open tight on the prompt and Clawd, ease back to the whole terminal as the search starts.
    const k = easeInOut(prog(t, 0.6, 3.0));
    return cam(lerp(1.4, 1.2, k) + 0.04 * easeInOut(prog(t, 3.0, T.split)), lerp(700, 890, k), lerp(330, 455, k), 960, 540);
  }
  if (t < T.route) { const k = easeInOut(prog(t, T.split, T.split + 0.5)); return cam(lerp(1.24, 0.74, k), 890, lerp(455, 500, k), lerp(960, 480, k), lerp(540, 560, k)); }
  if (t < T.r2) return cam(0.95, 760, 430, 480, 560);   // the spinning tool calls, through routing and search
  if (t < T.r3) return cam(1.0, 1380, 560, 480, 560);   // the summary card
  return cam(0.9, 820, 560, 480, 560);                  // the answer from memory
}

// ---------- Clawd R (right world coordinates) ----------
const TOP_R = 300;   // top edge of the right terminal
const CARD = i => ({ x: 1050, y: 540 + 128 * i, w: 800, h: 112 });
const PAGE = { x: 1000, y: 250, w: 880, h: 680 };
let LINES = [];   // highlighted quote lines, measured once: [{x, y, w, h}] relative to #quote
const QX = 48, QY = 400;   // #quote offset inside the page
const pageRect = t => {
  const k = spring(t - T.expand, ...SPRING.card), c = CARD(0);
  return { x: lerp(c.x, PAGE.x, k), y: lerp(c.y, PAGE.y, k), w: lerp(c.w, PAGE.w, k), h: lerp(c.h, PAGE.h, k), k };
};
const line1 = () => LINES[0] || { x: 0, y: 0, w: 760, h: 50 };
const walkX = t => PAGE.x + QX + line1().x + lerp(36, line1().w - 36, easeInOut(prog(t, T.walk0, T.walk1)));
const JEV = { x: 1010, y: 600, row: 58, row0: 74 };   // the routing panel (right world), below the Bash row
const RANK = ROUTES.map(r => [...ROUTES].sort((a, b) => b.p - a.p).indexOf(r));

// Round 1: Clawd jumps down onto the routing panel, nods with every bar and cheers when one channel is picked.
function routeR(t) {
  const j0 = T.jevOpen + 0.35, j1 = T.jevOpen + 0.75;
  if (t < j0 - 0.15) return { x: 1700, y: TOP_R, sq: 0.03 * Math.sin(t * Math.PI * 4), pose: { eyes: t > T.search ? 'd' : 'n', arms: 'down', legs: 'stand' } };
  if (t < j0) return { x: 1700, y: TOP_R, sq: 0.25 * easeOut(prog(t, j0 - 0.15, j0)), pose: { eyes: 'd', arms: 'down', legs: 'tuck' } };
  if (t < j1) { const k = prog(t, j0, j1); return { x: 1700, y: lerp(TOP_R, JEV.y, easeIn(k)) - 70 * hop(k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
  let sq = 0.28 * Math.exp(-(t - j1) * 9) * Math.cos((t - j1) * 22);
  ROUTES.forEach((_, i) => { const d = t - (T.bars + i * 0.22 + 0.32); if (d > 0 && d < 0.4) sq += 0.1 * Math.exp(-d * 12) * Math.cos(d * 30); });
  if (t < T.pick) return { x: 1700, y: JEV.y, sq, pose: { eyes: t < T.sort ? 'l' : 'd', arms: 'down', legs: 'stand' }, land: j1 };
  const c = t - T.pick;
  if (c < 0.5) return { x: 1700, y: JEV.y - 46 * hop(c / 0.5), sq: -0.1, pose: { eyes: 'happy', arms: 'up', legs: 'tuck' } };
  const d = c - 0.5;
  return { x: 1700, y: JEV.y, sq: 0.22 * Math.exp(-d * 9) * Math.cos(d * 22), land: T.pick + 0.5,
    pose: { eyes: c < 1.6 ? 'happy' : (c > 2.1 && c < 2.2 ? 'blink' : 'd'), arms: c < 1.2 ? 'up' : 'down', legs: 'stand' } };
}

function clawdR(T0) {
  const t = T0 < T.upgrade ? step8(T0) : T0;
  const blink = (a) => t > a && t < a + 0.1;
  if (t < T.rIn) return null;
  if (t < T.rIn + 0.55) {
    const k = prog(t, T.rIn, T.rIn + 0.55);
    return { x: lerp(2080, 1700, k), y: lerp(650, TOP_R, k) - 180 * hop(k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } };
  }
  if (t < T.upgrade) return { x: 1700, y: TOP_R, sq: t < T.rIn + 0.75 ? 0.25 : 0, pose: { eyes: blink(9.9) ? 'blink' : 'l', arms: 'down', legs: 'stand' } };
  if (t < T.route) {
    const d = t - T.upgrade;
    return { x: 1700, y: TOP_R - (d < 0.5 ? 34 * hop(d / 0.5) : 0), sq: d < 0.5 ? -0.1 : 0.2 * Math.exp(-(d - 0.5) * 8) * Math.cos((d - 0.5) * 24),
      pose: { eyes: d < 1.0 ? 'happy' : 'n', arms: d < 1.0 ? 'up' : 'down', legs: d < 0.5 ? 'tuck' : 'stand' } };
  }
  if (t < T.r1) return routeR(t);
  if (t < T.r2) {
    const J0 = T.hopR1, J1 = T.hopR1 + 0.42, to = { x: 1420, y: CARD(0).y }, back = T.r1 + 0.5;
    if (t < back) { const k = prog(t, T.r1, back); return { x: 1700, y: lerp(JEV.y, TOP_R, k) - 480 * k * (1 - k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
    if (t < J0 - 0.15) { const d = t - back; return { x: 1700, y: TOP_R, sq: 0.25 * Math.exp(-d * 9) * Math.cos(d * 22) + 0.03 * Math.sin(t * Math.PI * 4), pose: { eyes: t > T.results ? 'd' : 'n', arms: 'down', legs: 'stand' }, land: back }; }
    if (t < J0) return { x: 1700, y: TOP_R, sq: 0.25 * easeOut(prog(t, J0 - 0.15, J0)), pose: { eyes: 'd', arms: 'down', legs: 'tuck' } };
    if (t < J1) { const k = prog(t, J0, J1); return { x: lerp(1700, to.x, easeInOut(k)), y: lerp(TOP_R, to.y, k) - 120 * hop(k), sq: -0.15 * hop(k), pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
    const d = t - J1, sq = 0.3 * Math.exp(-d * 9) * Math.cos(d * 22);
    if (t < T.lensR1) return { x: to.x, y: to.y, sq, pose: { eyes: d < 0.3 ? 'shut' : 'd', arms: 'down', legs: 'stand' }, land: J1 };
    return { x: to.x, y: to.y, sq: sq + 0.1 * Math.exp(-(t - T.lensR1) * 10) * Math.sin((t - T.lensR1) * 30), pose: { eyes: 'none', arms: 'hold', legs: 'stand' }, extra: LENS, land: J1 };
  }
  if (t < T.r3) {
    if (t < T.expand) return { x: 1420, y: CARD(0).y, pose: { eyes: 'none', arms: 'hold', legs: 'stand' }, extra: LENS };
    if (t < T.toLine) { const p = pageRect(t); return { x: lerp(1420, 1130, p.k), y: p.y, pose: { eyes: 'none', arms: 'hold', legs: 'stand' }, extra: LENS }; }
    const ly = PAGE.y + QY + line1().y + 4, lx0 = walkX(T.walk0);
    if (t < T.toLine + 0.36) { const k = prog(t, T.toLine, T.toLine + 0.36); return { x: lerp(1130, lx0, k), y: lerp(PAGE.y, ly, k) - 70 * hop(k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
    const d = t - T.toLine - 0.36;
    if (t < T.walk0) return { x: lx0, y: ly, sq: 0.28 * Math.exp(-d * 9) * Math.cos(d * 22), pose: { eyes: 'd', arms: 'hold', legs: 'stand' }, extra: LENS, land: T.toLine + 0.36 };
    if (t < T.walk1) return { x: walkX(t), y: ly, pose: { eyes: 'none', arms: 'hold', legs: Math.floor(t * 8) % 2 ? 'walkA' : 'walkB' }, extra: LENS };
    const happy = t > T.cite;
    return { x: walkX(T.walk1), y: ly, sq: happy ? 0.18 * Math.exp(-(t - T.cite) * 8) * Math.cos((t - T.cite) * 24) : 0,
      pose: { eyes: happy ? 'happy' : 'none', arms: happy ? 'up' : 'hold', legs: 'stand' }, extra: happy ? '' : LENS };
  }
  // Round 3 and the merge: back on the terminal, watching the answer, celebrating.
  const home = { x: 1640, y: TOP_R };
  const from = { x: walkX(T.walk1), y: PAGE.y + QY + line1().y + 4 };
  if (t < T.r3 + 0.45) { const k = prog(t, T.r3, T.r3 + 0.45); return { x: lerp(from.x, home.x, easeInOut(k)), y: lerp(from.y, home.y, k) - 110 * hop(k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
  if (t < T.stampR + 0.05) { const d = t - T.r3 - 0.45; return { ...home, sq: 0.25 * Math.exp(-d * 9) * Math.cos(d * 22), pose: { eyes: blink(T.r3 + 1.6) ? 'blink' : 'd', arms: 'down', legs: 'stand' }, land: T.r3 + 0.45 }; }
  if (t < T.merge + 1.6) {
    const beat = (t - T.stampR) % 0.5, k = beat / 0.5;
    return { x: home.x, y: home.y - 26 * hop(Math.min(1, k * 1.6)), sq: k > 0.62 ? 0.18 * Math.sin((k - 0.62) / 0.38 * Math.PI) : -0.06,
      pose: { eyes: 'happy', arms: Math.floor((t - T.stampR) / 0.5) % 2 ? 'up' : 'wave', legs: k < 0.62 ? 'tuck' : 'stand' } };
  }
  const c = t - T.cheer;
  return { ...home, y: home.y - (c > 0 && c < 0.5 ? 40 * hop(c / 0.5) : 0), sq: c > 0 && c < 0.5 ? -0.1 : 0,
    pose: { eyes: 'happy', arms: c > -0.4 && c < 1.2 ? 'up' : 'wave', legs: c > 0 && c < 0.5 ? 'tuck' : 'stand' } };
}

function camR(t) {
  let z = springTo(t, [[0, 1], [T.route + 0.3, 0.92], [T.r1 + 0.3, 1.06], [T.r2 + 0.2, 1.02], [T.r3 + 0.1, 1.03], [T.tear + 0.1, 1.0]], 6, 0.95);
  let cx = springTo(t, [[0, 1440], [T.r1 + 0.3, 1470], [T.r2 + 0.2, 1440], [T.r3 + 0.1, 1440]], 6, 0.95);
  const cy = springTo(t, [[0, 540], [T.route + 0.3, 650], [T.r1 + 0.3, 580], [T.r2 + 0.2, 560], [T.r3 + 0.1, 560]], 6, 0.95);
  if (t >= T.r2 && t < T.r3 + 0.6) {
    // Follow Clawd along the quote with a little lag.
    const c = clawdR(Math.max(T.r2, t - 0.25));
    const f = prog(t, T.r2 + 0.3, T.r2 + 1.0) * (1 - prog(t, T.r3, T.r3 + 0.6));
    if (c) cx = lerp(cx, clamp(c.x, 1400, 1480), f);
  }
  const sx = springTo(t, [[0, 1440], [T.tear + 0.1, 960]], 9, 0.9);
  return cam(z, cx, cy, sx, 540);
}

// ---------- Clawd L (left world coordinates, 8 fps once stuck) ----------
function clawdL(T0) {
  if (T0 >= T.merge) return null;
  const t = T0 < T.stuck ? T0 : step8(T0);
  if (t < T.stuck) {
    const n = typed(TYPE.prompt, t) / PROMPT.length;
    let eyes = n < 0.35 ? 'l' : n < 0.7 ? 'n' : 'r';
    if (t > T.ws) eyes = t > 3.2 && t < 3.3 ? 'blink' : 'd';
    const e = t - T.enter;
    const jumping = e > 0 && e < 0.4;
    return { x: 760, y: 250 - (jumping ? 30 * hop(e / 0.4) : 0), sq: jumping ? -0.1 : 0.03 * Math.sin(t * Math.PI * 4), pose: { eyes, arms: jumping ? 'up' : 'down', legs: jumping ? 'tuck' : 'stand' } };
  }
  if (t < T.split) {
    const k = (t * 2) % 1, up = k < 0.25;   // an impatient hop on every beat
    const extra = (t > 4.4 ? Q : '') + (t > 5.3 ? SWEAT : '');
    if (t >= T.oldLens) return { x: 760, y: 250, pose: { eyes: 'none', arms: 'hold', legs: 'stand' }, extra: OLD_LENS + (t > 7.0 ? Q : '') };
    return { x: 760, y: 250 - (up ? 16 : 0), sq: !up && k < 0.4 ? 0.14 : 0, pose: { eyes: t > T.summary ? 'r' : 'u', arms: up ? 'up' : 'down', legs: up ? 'tuck' : 'stand' }, extra };
  }
  if (t < T.route) return { x: 760, y: 250, pose: { eyes: t > 9.0 && t < 9.12 ? 'blink' : 'r', arms: 'down', legs: 'tuck' }, extra: SWEAT };
  if (t < T.r1) return { x: 720, y: 250, pose: { eyes: 'u', arms: 'out', legs: 'stand' }, extra: (t > T.route + 0.75 ? Q : '') + SWEAT };   // nothing to choose from
  if (t < T.r2) return { x: 720, y: 250, pose: { eyes: Math.floor(t * 8) % 24 === 0 ? 'blink' : 'd', arms: 'down', legs: 'tuck' } };
  if (t < T.r3) return { x: 1290, y: 420, pose: { eyes: 'none', arms: 'hold', legs: 'stand' }, extra: OLD_LENS + SWEAT + (t > T.r2 + 1.5 ? Q : '') };
  if (t < T.stampL) return { x: 900, y: 250, pose: { eyes: t < T.r3 + 1.4 ? 'u' : 'd', arms: 'down', legs: 'stand' } };
  if (t < T.stampL + 0.6) return { x: 900, y: 250, sq: 0.2, pose: { eyes: 'wide', arms: 'up', legs: 'stand' }, extra: BANG + SWEAT };
  return { x: 900, y: 250, pose: { eyes: 'r', arms: 'down', legs: 'stand' }, extra: SWEAT };
}

// ---------- the crossing Clawd (screen coordinates during the merge) ----------
function clawdM(t) {
  if (t < T.merge) return null;
  const startS = proj(camL(T.merge), 900, 250);
  const z0 = camL(T.merge).z;
  if (t < T.jump) {
    const ts = step8(t);
    const walking = ts < T.peek;
    const x = walking ? lerp(startS[0], 860, prog(ts, T.merge, T.peek)) : 860 + (Math.floor(ts * 8) % 2) * 6;
    return { x, y: startS[1], z: z0, grey: 1, pose: { eyes: walking ? 'r' : 'wide', arms: 'down', legs: walking ? (Math.floor(ts * 8) % 2 ? 'walkA' : 'walkB') : 'stand' }, extra: walking ? SWEAT : BANG };
  }
  const land = proj(camR(t), 1420, TOP_R);
  if (t < T.land) {
    const k = prog(t, T.jump, T.land);
    const crossed = k > 0.45;
    const kk = crossed ? k : step8(t - T.jump) / (T.land - T.jump);
    const x = lerp(860, land[0], easeInOut(kk)), y = lerp(startS[1], land[1], kk) - 130 * hop(kk);
    return { x, y, z: lerp(z0, camR(t).z, kk), grey: crossed ? Math.max(0, 1 - (k - 0.45) * 6) : 1, sq: -0.15, pose: { eyes: crossed ? 'happy' : 'wide', arms: 'up', legs: 'tuck' } };
  }
  const d = t - T.land, c = t - T.cheer;
  const cheering = c > 0 && c < 0.5;
  return { x: land[0], y: land[1] - (cheering ? 40 * camR(t).z * hop(c / 0.5) : 0), z: camR(t).z,
    sq: cheering ? -0.1 : 0.28 * Math.exp(-d * 9) * Math.cos(d * 22), land: T.land,
    pose: { eyes: 'happy', arms: c > -0.4 && c < 1.2 ? 'up' : 'wave', legs: cheering ? 'tuck' : 'stand' }, flip: true };
}

// ---------- terminals ----------
const caret = on => on ? '<span class="caret"></span>' : '';
const spin = a => `<span class="spin" style="transform:rotate(${a}deg)"></span>`;
const bul = cls => `<span class="bul ${cls}"></span>`;
const elbow = '<span class="elbow"></span>';
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');

function rowsLeft(T0) {
  const t = T0 < T.stuck ? T0 : step8(T0);
  const n = typed(TYPE.prompt, t);
  const rows = [`<span class="p">&gt;</span> ${esc(PROMPT.slice(0, n))}${caret(t < T.enter && Math.floor(t * 2.5) % 2 === 0)}`, ''];
  const a = Math.floor(t * 8) * 45, stopped = t >= T.answerL;
  if (t >= T.ws) rows.push(`${bul('')}<b>Web Search</b>("useEffect 清理时机")`, `${elbow}${spin(stopped ? 0 : a)}`);
  if (t >= T.fetch) rows.push(`${bul('')}<b>Fetch</b>(<span class="url">https://react.dev/reference/react/useEffect</span>)`, `${elbow}${spin(stopped ? 0 : a + 90)}`);
  if (t >= T.answerL) { rows.push(''); rows.push(`${bul('ink')}${esc([...ANSWER_L].slice(0, typed(TYPE.answerL, t)).join(''))}`); }
  return rows;
}
function rowsRight(T0) {
  const t = T0 < T.upgrade ? step8(T0) : T0;
  if (t < T.clear) {
    const rows = [`<span class="p">$</span> ${esc(INSTALL.slice(0, typed(TYPE.install, t)))}${caret(t < T.setup && Math.floor(t * 2.5) % 2 === 0)}`];
    if (t >= T.setup - 0.05) rows.push(`<span class="p">$</span> ${esc(SETUP.slice(0, typed(TYPE.setup, t)))}`);
    return rows;
  }
  const rows = [`<span class="p">&gt;</span> ${esc(PROMPT)}`, ''];
  if (t >= T.search) {
    rows.push(`${bul(t > T.results ? 'ok' : (Math.floor(t * 6) % 2 ? 'ink' : ''))}<b>Bash</b>(smart-search search "useEffect 清理时机" --format markdown)`);
    const lifted = i => t > T.lift + i * 0.14 ? ' style="opacity:.06"' : '';
    if (t >= T.results) rows.push(`${elbow}<span class="dim">…（检索结果与摘录）</span>`);
    if (t >= T.results + 0.05) rows.push(`   <span class="dim">证据：not_evaluated</span>`);
    if (t >= T.results + 0.1) rows.push(`   ## 来源`);
    SOURCES.forEach(([title, url], i) => { if (t >= T.results + 0.2 + i * 0.08) rows.push(`<span${lifted(i)}>   - [${title}](<span class="url">${url}</span>)</span>`); });
  }
  if (t >= T.fetchR) {
    rows.push('', `${bul(t > T.fetchR + 0.3 ? 'ok' : 'ink')}<b>Bash</b>(smart-search fetch "<span class="url">https://react.dev/reference/react/useEffect</span>")`);
    if (t >= T.fetchR + 0.3) rows.push(`${elbow}<span class="dim">…（原网页正文，Markdown）</span>`);
  }
  if (t >= T.answer) {
    const n = typed(TYPE.answerR, t);
    rows.push('', `${bul('ink')}${esc([...ANSWER_R].slice(0, n).join(''))}`);
    const done = TYPE.answerR[TYPE.answerR.length - 1] + 0.15;
    if (t >= done) rows.push('', '  <b>来源</b>');
    SOURCES.slice(0, 2).forEach(([title, url], i) => { if (t >= done + 0.15 * (i + 1)) rows.push(`  [${i + 1}] ${title} · <span class="url">${url.replace('https://', '')}</span>`); });
  }
  return rows;
}
function setRows(el, rows) {
  while (el.children.length < rows.length) { const d = document.createElement('div'); d.className = 'row'; el.appendChild(d); }
  [...el.children].forEach((d, i) => { if (i < rows.length) { html(d, rows[i]); vis(d, true); } else vis(d, false); });
}

// ---------- overlay helpers ----------
function zig(x) {
  const p = [];
  for (let y = -22, i = 0; y <= 1110; y += 44, i++) p.push([x + (i % 2 ? 16 : -16), y]);
  return p;
}
const poly = pts => `polygon(${pts.map(([x, y]) => `${x.toFixed(1)}px ${y}px`).join(',')})`;
function edgeX(t) {
  if (t < T.split) return 2000;
  const inK = spring(t - T.split, 16, 0.85);
  const outK = t > T.tear ? spring(t - T.tear - 0.05, 9, 0.9) : 0;
  return lerp(lerp(2000, 960, inK), -80, outK);
}
function capText(el, t, items) {
  // items: [t0, t1, html]; springs in and out from the bottom.
  const it = items.find(([a, b]) => t >= a && t < b);
  if (!it) { css(el, { opacity: '0' }); return; }
  html(el, it[2]);
  const k = Math.min(spring(t - it[0], ...SPRING.card), 1 - easeIn(prog(t, it[1] - 0.2, it[1])));
  css(el, { opacity: String(clamp(k * 1.5)), transform: `translateX(-50%) translateY(${((1 - k) * 36).toFixed(1)}px)` });
}
function sparkles(x, y, t, t0, n = 5, spread = 90, scale = 7) {
  let s = '';
  const k = prog(t, t0, t0 + 0.9);
  if (k <= 0 || k >= 1) return s;
  for (let i = 0; i < n; i++) {
    const a = (i / n) * Math.PI * 2 + rnd(i + t0) * 0.6, r = spread * easeOut(k) * (0.7 + 0.5 * rnd(i * 7 + t0));
    const on = Math.floor((t - t0) * 12 + i) % 3 !== 0;
    if (!on) continue;
    s += `<svg style="position:absolute;left:${x + Math.cos(a) * r - 2.5 * scale}px;top:${y - 40 + Math.sin(a) * r * 0.7 - 2.5 * scale}px;opacity:${1 - k}" width="${5 * scale}" height="${5 * scale}" viewBox="0 0 5 5" shape-rendering="crispEdges">${pixartSVG(i % 2 ? ICONS.spark : ICONS.sparkW)}</svg>`;
  }
  return s;
}
function dust(x, y, t, t0, z = 1) {
  const dk = prog(t, t0, t0 + 0.45);
  if (dk <= 0 || dk >= 1) return '';
  let s = '';
  for (let i = 0; i < 8; i++) {
    const side = i % 2 ? 1 : -1, n = (i >> 1) + 1, e = easeOut(dk), sz = 9 * z * (1 - dk * 0.6);
    s += `<div style="position:absolute;left:${x + side * (60 + n * 22 + rnd(i) * 10) * e * z - sz / 2}px;top:${y - 6 - (10 + n * 6) * Math.sin(Math.PI * dk) * z - sz}px;width:${sz}px;height:${sz}px;background:#CFC6B5;opacity:${1 - dk}"></div>`;
  }
  return s;
}

// ---------- montage ----------
const nodePos = [[190, 520], [520, 640], [850, 760], [1180, 880]];
const MB_FLIPS = ['xai', 'exa', 'jina'], flipT = i => T.cutB + 0.45 + i * 0.3, MB_PASS = T.cutB + 1.45;
function montage(t) {
  const a = t >= T.montage && t < T.cutB, b = t >= T.cutB && t < T.cutC, c = t >= T.cutC && t < T.end;
  vis($('ma'), a); vis($('mb'), b); vis($('mc'), c);
  const drift = (t0) => `scale(${1 + 0.03 * prog(t, t0, t0 + 2)})`;
  const lab = (el, t0) => { const k = pop(t, t0 + 0.05, SPRING.card); css(el, { transform: `translateX(${(1 - k) * -80}px)`, opacity: String(clamp(k * 1.4)) }); };
  if (a) {
    css($('ma'), { transform: drift(T.montage), transformOrigin: '960px 540px' });
    lab($('ma').querySelector('.label'), T.montage);
    const cmd = 'smart-search research "React 状态管理方案对比" --budget standard';
    const n = Math.floor(clamp(prog(t, T.montage + 0.05, T.montage + 0.45)) * cmd.length);
    setRows($('rowsD'), [`<span class="p">$</span> ${esc(cmd.slice(0, n))}`]);
    const sub = pop(t, T.montage + 0.2, SPRING.card);
    css($('ma').querySelector('.sublabel'), { opacity: String(clamp(sub * 1.5)), transform: `translateX(${(1 - sub) * -60}px)` });
    nodePos.forEach(([x, y], i) => {
      const k = pop(t, nodeT(i));
      css($('nd' + i), { left: `${x}px`, top: `${y}px`, transform: `scale(${k})`, opacity: String(clamp(k * 2)) });
      if (i < nodePos.length - 1) {
        const [x2, y2] = nodePos[i + 1], len = Math.hypot(x2 - x, y2 - y), lk = easeOut(prog(t, nodeT(i) + 0.12, nodeT(i) + 0.4));
        css($('lk' + i), { left: `${x + 120}px`, top: `${y + 40}px`, width: `${len * lk}px`, transform: `rotate(${Math.atan2(y2 - y, x2 - x)}rad)` });
      }
    });
    // Clawd hops down the steps as each one appears.
    // Clawd stands near each step's right end, clear of the step above.
    const hopTo = (i) => [nodePos[i][0] + $('nd' + i).offsetWidth - 100, nodePos[i][1]], start = [1500, 290], last = nodePos.length - 1;
    let p = start, pose = { eyes: 'd', arms: 'down', legs: 'stand' }, sq = 0;
    for (let i = 0; i <= last; i++) {
      const j0 = nodeT(i) + 0.08, j1 = j0 + 0.3;
      const from = i === 0 ? start : hopTo(i - 1), to = hopTo(i);
      if (t >= j0 && t < j1) { const k = prog(t, j0, j1); p = [lerp(from[0], to[0], k), lerp(from[1], to[1], k) - 90 * hop(k)]; pose = { eyes: 'wide', arms: 'up', legs: 'tuck' }; sq = -0.12; break; }
      if (t >= j1) { p = to; pose = { eyes: i === last ? 'happy' : 'd', arms: i === last ? 'up' : 'down', legs: 'stand' }; sq = 0.25 * Math.exp(-(t - j1) * 9) * Math.cos((t - j1) * 22); }
    }
    return { x: p[0], y: p[1], sq, pose };
  }
  if (b) {
    css($('mb'), { transform: drift(T.cutB), transformOrigin: '960px 540px' });
    lab($('mb').querySelector('.label'), T.cutB);
    const w = pop(t, T.cutB, SPRING.card);
    css($('mbA'), { transform: `translateY(${((1 - w) * 90).toFixed(1)}px)`, opacity: String(clamp(w * 2)) });
    // Three providers turn 已配置 one by one; the list keeps its final order so nothing jumps.
    const n = MB_FLIPS.filter((_, i) => t >= flipT(i)).length;
    html($('mbA-pl'), providerList('mbA', { selected: 'exa', configured: MB_FLIPS.slice(0, n), sortBy: MB_FLIPS, hover: n && t - flipT(n - 1) < 0.25 ? MB_FLIPS[n - 1] : '' }));
    const passed = t >= MB_PASS, pill = $('mbA-exa-pill');
    html(pill, passed ? '通过' : '尚未测试');
    pill.classList.toggle('ok', passed);
    css(pill, { transform: `scale(${passed ? pop(t, MB_PASS, [22, 0.55]) : 1})` });
    vis($('mbA-exa-res'), passed);
    // Scroll from the key down to the test result, as the page would.
    css($('mbA-pd-exa'), { transform: `translateY(${-lerp(190, 560, easeInOut(prog(t, T.cutB + 0.85, T.cutB + 1.35))).toFixed(1)}px)` });
    const wave = Math.floor((t - T.cutB) * 4) % 2;
    return { x: 1500, y: 220 + (1 - w) * 90, pose: { eyes: 'happy', arms: wave ? 'wave' : 'down', legs: 'tuck' } };
  }
  if (c) {
    css($('mc'), { transform: drift(T.cutC), transformOrigin: '960px 540px' });
    lab($('mc').querySelector('.label'), T.cutC);
    const els = $('agents').children;
    AGENTS.forEach((_, i) => {
      const on = t > T.cutC + 0.3 + i * 0.055;
      const k = pop(t, T.cutC + 0.08 + i * 0.03, SPRING.card);
      els[i].classList.toggle('on', on);
      css(els[i], { transform: `translateY(${(1 - k) * 60}px)`, opacity: String(clamp(k * 1.6)) });
      html(els[i], AGENTS[i] + (on ? '<i>✓</i>' : ''));
    });
    const r = agentRect(1), j0 = T.cutC + 0.35, j1 = j0 + 0.4;
    if (t < j0) return null;
    if (t < j1) { const k = prog(t, j0, j1); return { x: lerp(1980, r.x + 150, k), y: lerp(200, r.y, k) - 150 * hop(k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
    const d = t - j1;
    return { x: r.x + 150, y: r.y, sq: 0.28 * Math.exp(-d * 9) * Math.cos(d * 22), pose: { eyes: 'happy', arms: Math.floor(d * 4) % 2 ? 'wave' : 'up', legs: 'stand' }, land: j1 };
  }
  return null;
}
function agentRect(i) {
  const perRow = 5, w = 300, h = 92, gx = 28, gy = 30;
  const row = Math.floor(i / perRow), col = i % perRow, inRow = Math.min(perRow, AGENTS.length - row * perRow);
  const left = (1920 - (inRow * w + (inRow - 1) * gx)) / 2;
  return { x: left + col * (w + gx), y: 330 + row * (h + gy), w, h };
}

// ---------- end card ----------
function endCard(t) {
  const on = t >= T.end;
  vis($('endc'), on);
  if (!on) return null;
  const e = t - T.end;
  const k1 = pop(t, T.end, SPRING.heavy);
  css($('eIcon'), { left: '150px', top: '240px', transform: `scale(${0.5 + 0.5 * k1})`, opacity: String(clamp(k1 * 2)) });
  const k2 = pop(t, T.end + 0.08, SPRING.card);
  css($('eWord'), { left: '334px', top: '252px', transform: `translateX(${(1 - k2) * -60}px)`, opacity: String(clamp(k2 * 1.5)) });
  const k3 = pop(t, T.end + 0.35, SPRING.card);
  css($('eTag'), { left: '150px', top: '440px', transform: `translateY(${(1 - k3) * 30}px)`, opacity: String(clamp(k3 * 1.5)) });
  const k4 = pop(t, T.end + 0.6, SPRING.card);
  css($('eCmd'), { left: '150px', top: '570px', transform: `translateY(${(1 - k4) * 30}px)`, opacity: String(clamp(k4 * 1.5)) });
  const k5 = pop(t, T.end + 1.05, SPRING.card);
  css($('eGh'), { left: '154px', top: '705px', opacity: String(clamp(k5 * 1.5)) });
  const k6 = pop(t, T.end + 1.0, SPRING.mascot);
  css($('eMascot'), { left: '1230px', top: `${lerp(1100, 470, k6) + 6 * Math.sin(e * 2.6)}px` });
  css($('eNote'), { opacity: String(clamp(pop(t, T.end + 1.4, SPRING.card))) });
  // Clawd drops onto the mascot's head as she peeks up, and waves.
  const bob = 6 * Math.sin(e * 2.6);
  const headX = 1478, headY = lerp(1100, 470, k6) + bob + 212, j0 = T.end + 1.15, j1 = j0 + 0.32;
  if (t < j0) return null;
  if (t < j1) { const k = prog(t, j0, j1); return { x: headX + 60 * (1 - k), y: lerp(-80, headY, easeIn(k)), sq: -0.15, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
  const d = t - j1;
  const blink = e > 3.2 && e < 3.3;
  return { x: headX, y: headY, sq: 0.3 * Math.exp(-d * 9) * Math.cos(d * 22), land: j1,
    pose: { eyes: blink ? 'blink' : (d < 0.3 ? 'shut' : 'happy'), arms: d > 0.4 ? (Math.floor(d * 3.5) % 2 ? 'wave' : 'down') : 'down', legs: 'tuck' } };
}

// ---------- render ----------
let SCROLL_R3 = 0;
const fx = $('fx');

window.render = function (t) {
  const tL = t < T.stuck ? t : step8(t);
  const tR = t < T.upgrade ? step8(t) : t;
  const worlds = t < T.montage;
  vis($('wl'), worlds); vis($('wr'), worlds && t >= T.split);

  // Left world.
  const cL = camL(t);
  css($('camL'), { transform: `translate(${cL.tx.toFixed(2)}px, ${cL.ty.toFixed(2)}px) scale(${cL.z.toFixed(4)})` });
  const ex = edgeX(t);
  const greyL = t < T.stuck ? 0 : 1;
  let wlT = 'none';
  if (t > T.tear) { const f = easeIn(prog(t, T.tear, T.tear + 0.85)); wlT = `translate(${-60 * f}px, ${1250 * f}px) rotate(${-9 * f}deg)`; }
  css($('wl'), { filter: greyL ? 'grayscale(1) contrast(.94)' : 'none', clipPath: t >= T.split ? poly([[-2000, -40], ...zig(ex), [-2000, 1120]]) : 'none', transform: wlT, transformOrigin: '960px 0px' });
  css($('ovL'), { transform: wlT, transformOrigin: '960px 0px' });
  setRows($('rowsL'), rowsLeft(t));
  css($('termL'), { opacity: tL >= T.r2 && tL < T.r3 ? '0.3' : '1' });
  css($('sumL'), { opacity: tL >= T.summary ? '1' : '0', transform: tL >= T.summary ? `rotate(${Math.floor(tL * 8) % 2 ? -2.5 : -1}deg) scale(${tL < T.summary + 0.25 ? 0.9 : 1})` : 'none' });

  // Right world.
  if (t >= T.split) {
    const cR = camR(t);
    css($('camR'), { transform: `translate(${cR.tx.toFixed(2)}px, ${cR.ty.toFixed(2)}px) scale(${cR.z.toFixed(4)})` });
    const greyR = t < T.upgrade ? 1 : 1 - easeOut(prog(t, T.upgrade, T.upgrade + 0.45));
    css($('wr'), { clipPath: poly([...zig(ex), [3920, 1120], [3920, -40]]), filter: greyR > 0.01 ? `grayscale(${greyR.toFixed(3)})` : 'none' });
    html($('titleR'), tR < T.clear ? '~ — zsh' : 'my-app — claude');
    setRows($('rowsR'), rowsRight(t));
    const sc = springTo(t, [[0, 0], [T.r3 + 0.05, SCROLL_R3]], ...SPRING.card);
    css($('rowsR'), { transform: `translateY(${-sc.toFixed(1)}px)` });
    // Source cards lift out of the terminal rows, then leave when the page opens.
    for (let i = 0; i < 3; i++) {
      const el = $('c' + i), k = spring(t - (T.lift + i * 0.14), ...SPRING.card);
      const out = t > T.expand ? spring(t - T.expand - i * 0.05, ...SPRING.card) : 0;
      const row = $('rowsR').children[6 + i];
      const start = { x: 1030, y: TOP_R + 52 + 26 + (row && row.style.display !== 'none' ? row.offsetTop : (6 + i) * 31), w: 820, h: 31 }, end = CARD(i);
      const r = { x: lerp(start.x, end.x, k), y: lerp(start.y, end.y, k) + out * 420, w: lerp(start.w, end.w, k), h: lerp(start.h, end.h, k) };
      const shown = t >= T.lift + i * 0.14 && !(i === 0 && t >= T.expand) && out < 0.98;
      vis(el, shown);
      if (shown) css(el, { left: `${r.x}px`, top: `${r.y}px`, width: `${r.w}px`, height: `${r.h}px`, opacity: String(clamp(k * 2) * (1 - out)) });
      if (i === 0) css(el.querySelector('.ring'), { opacity: String(clamp((t - T.lensR1 - 0.2) * 3) * (t < T.expand ? 1 : 0)) });
    }
    // The page grows out of the first card, and slides away for round 3.
    const pg = $('page');
    const pOn = t >= T.expand && t < T.r3 + 0.7;
    vis(pg, pOn);
    if (pOn) {
      const p = pageRect(t), away = easeIn(prog(t, T.r3, T.r3 + 0.6));
      css(pg, { left: `${p.x}px`, top: `${p.y + away * 900}px`, width: `${p.w}px`, height: `${p.h}px` });
      css(pg.querySelector('.pin'), { opacity: String(prog(p.k, 0.45, 0.9)) });
      // Highlight: the first line trails Clawd, the rest sweeps after him.
      const hl = [...pg.querySelectorAll('.hl')];
      const x1 = clawdR(t) ? clawdR(t).x - (PAGE.x + QX) + 26 : 0;
      LINES.forEach((L, i) => {
        let w = 0;
        if (i === 0) w = t < T.walk0 ? 0 : t < T.walk1 ? clamp(x1 - L.x, 0, L.w) : L.w;
        else w = L.w * easeInOut(prog(t, T.walk1 + (i - 1) * 0.35, T.walk1 + i * 0.35 + 0.1));
        css(hl[i], { width: `${w}px` });
      });
      css($('cite'), { transform: `scale(${pop(t, T.cite)})` });
      const g = pop(t, T.gloss, SPRING.card);
      css($('gloss'), { opacity: String(clamp(g * 1.5)), transform: `translateY(${(1 - g) * 24}px)` });
    }
    // Round 1: the routing panel. Bars fill in program order, rows sort by probability, the top one is dispatched.
    const jv = $('jev'), jOn = t >= T.jevOpen && t < T.r1 + 0.4;
    vis(jv, jOn);
    if (jOn) {
      const k = spring(t - T.jevOpen, ...SPRING.card), out = easeIn(prog(t, T.r1 + 0.02, T.r1 + 0.4));
      css(jv, { transform: `translateY(${((1 - k) * -40 + out * 50).toFixed(1)}px) scale(${((0.84 + 0.16 * k) * (1 - 0.25 * out)).toFixed(4)})`, opacity: String((clamp(k * 2) * (1 - out)).toFixed(3)) });
      const ks = t >= T.sort ? spring(t - T.sort, ...SPRING.card) : 0;
      ROUTES.forEach((r, i) => {
        const row = $('jr' + i), kb = spring(t - T.bars - i * 0.22, ...SPRING.card);
        const picked = t >= T.pick && RANK[i] === 0, dim = t >= T.pick && !picked;
        row.classList.toggle('on', picked);
        css(row, { top: `${(JEV.row0 + JEV.row * lerp(i, RANK[i], ks)).toFixed(1)}px`, zIndex: String(10 - RANK[i]), opacity: dim ? (1 - 0.5 * clamp((t - T.pick) * 4)).toFixed(3) : '1' });
        css(row.querySelector('.jb'), { width: `${(320 * r.p * kb).toFixed(1)}px` });
        html(row.querySelector('.jv'), t >= T.bars + i * 0.22 ? (r.p * Math.min(1, kb)).toFixed(2) : '—');
        css(row.querySelector('.jp'), { transform: `scale(${picked ? pop(t, T.pick + 0.05, [22, 0.55]) : 0})` });
      });
      const kf = pop(t, T.pick + 0.6, SPRING.card);
      css(jv.querySelector('.jf'), { opacity: String(clamp(kf * 1.5)), transform: `translateY(${((1 - kf) * 16).toFixed(1)}px)` });
    }
    // Upgrade ring from Clawd's feet.
    const rk = prog(t, T.upgrade, T.upgrade + 0.7), rr = 30 + 1400 * easeOut(rk);
    css($('ringR'), { left: `${1700 - rr}px`, top: `${TOP_R - rr}px`, width: `${2 * rr}px`, height: `${2 * rr}px`, borderWidth: `${8 + 22 * (1 - rk)}px`, opacity: rk > 0 && rk < 1 ? String(1 - rk) : '0' });
  }

  // Overlay: divider, VS, banner, round labels, tags, onomatopoeia, stamps, captions.
  const zp = zig(ex);
  $('zig').setAttribute('points', zp.map(p => p.join(',')).join(' '));
  css($('divider'), { opacity: t >= T.split && t < T.tear + 0.6 ? '1' : '0' });
  const vsK = pop(t, T.vs);
  css($('vs'), { left: `${ex - 56}px`, top: '560px', transform: `scale(${t > T.tear ? 1 - prog(t, T.tear, T.tear + 0.25) : vsK}) rotate(-8deg)`, opacity: t >= T.vs && worlds ? '1' : '0' });
  const bK = pop(t, T.split + 0.4, SPRING.card), bOut = easeIn(prog(t, T.merge, T.merge + 0.4));
  html($('banner'), `同一个问题：${QUESTION}`);
  css($('banner'), { transform: `translateX(-50%) translateY(${(1 - bK) * -140 - bOut * 170}px)`, opacity: t >= T.split + 0.4 && worlds ? '1' : '0' });
  const rounds = [[T.ready, 'READY…'], [T.go, 'GO!'], [T.route, '第 1 回合 · 选路'], [T.r1, '第 2 回合 · 搜索'], [T.r2, '第 3 回合 · 读原文'], [T.r3, '第 4 回合 · 回答']];
  const cur = rounds.filter(([a]) => t >= a).pop();
  if (cur && t < T.merge + 0.4) {
    html($('round').firstElementChild, cur[1]);
    const k = pop(t, cur[0], [20, 0.55]);
    css($('round'), { opacity: '1', transform: `translateX(-50%) scale(${(0.4 + 0.6 * k) * (1 - bOut)}) rotate(${(1 - k) * -10}deg)` });
  } else css($('round'), { opacity: '0' });
  css($('tagL'), { opacity: t >= T.stuck && worlds ? '1' : '0', transform: `translateY(${(1 - pop(t, T.stuck, SPRING.card)) * -80}px)` });
  css($('tagR'), { opacity: t >= T.split + 0.3 && worlds ? '1' : '0', transform: `translateY(${(1 - pop(t, T.split + 0.3, SPRING.card)) * -80}px)` });
  html($('fpsR'), t < T.upgrade ? '8 FPS' : '60 FPS');
  $('fpsR').classList.toggle('fast', t >= T.upgrade);

  const onoL = $('onoL');
  const ono = tL >= T.r1 + 0.4 && tL < T.r2 ? '卡……' : tL >= T.r2 + 0.4 && tL < T.r3 ? '糊……' : '';
  html(onoL, ono);
  css(onoL, { left: '70px', top: '190px', transform: `rotate(${-7 + (Math.floor(tL * 8) % 2) * 3}deg) translate(${(Math.floor(tL * 8) % 3) * 4}px, 0)`, opacity: ono ? '1' : '0' });
  // 叮！when Jev picks a channel, 唰！when the sources lift out.
  const ding = t < T.r1, o0 = ding ? T.pick : T.lift;
  const sw = pop(t, o0 + 0.05), swOut = prog(t, o0 + 1.4, o0 + 1.7);
  html($('onoR'), ding ? '叮！' : '唰！');
  css($('onoR'), { left: ding ? '1390px' : '1630px', top: ding ? '388px' : '470px', fontSize: ding ? '96px' : '104px', transform: `scale(${sw * (1 - swOut)}) rotate(${-12 + 8 * sw}deg)`, opacity: t > o0 && t < o0 + 1.7 ? '1' : '0' });
  const stR = pop(t, T.stampR, [22, 0.5]), stL = pop(t, T.stampL, [22, 0.5]);
  css($('stampR'), { left: '1480px', top: '745px', transform: `scale(${t >= T.stampR ? 2.2 - 1.2 * stR : 0}) rotate(-8deg)`, opacity: t >= T.stampR && t < T.tear + 0.5 && worlds ? String(clamp((t - T.stampR) * 10)) : '0' });
  css($('stampL'), { left: '300px', top: '640px', transform: `scale(${t >= T.stampL ? 2.2 - 1.2 * stL : 0}) rotate(7deg)`, opacity: t >= T.stampL ? String(clamp((t - T.stampL) * 10)) : '0' });

  capText($('cap'), t, [
    [0.5, 3.9, '让 Claude Code 去查一下<b>当前文档</b>'],
    [T.stuck + 0.3, T.split - 0.05, '内置搜索：一直<b>转圈</b>，读网页只拿到<b>摘要</b>'],
    [T.split + 0.6, T.route - 0.05, '同一个问题，右边换上 <b>Smart Search</b>'],
  ]);
  css($('cap'), { left: '960px', top: '940px' });
  capText($('capL'), tL, [[T.route + 0.5, T.r1 - 0.1, '只有一个内置搜索'], [T.r1 + 0.5, T.r2 - 0.1, '还在转圈……'], [T.r2 + 0.5, T.r3 - 0.1, '只拿到摘要'], [T.r3 + 0.6, T.merge, '只能凭记忆']]);
  css($('capL'), { left: '480px', top: '950px' });
  capText($('capR'), t, [[T.jevOpen + 0.5, T.pick - 0.05, '<b>Jev</b> 给每个渠道打分'], [T.pick + 0.1, T.r1 - 0.1, '只派发<b>最合适</b>的那个'], [T.results + 0.3, T.r2 - 0.1, '<b>来源</b>一次列全'], [T.expand + 0.4, T.r3 - 0.1, '抓下原网页，<b>原话</b>可引用'], [T.answer + 0.3, T.merge, '回答带<b>出处</b>，点开就能核对']]);
  css($('capR'), { left: '1440px', top: '950px' });

  const sk = pop(t, T.skill, SPRING.card);
  css($('skill'), { left: '1080px', top: '720px', opacity: t >= T.skill && t < T.route ? String(clamp(sk * 2)) : '0', transform: `scale(${0.6 + 0.4 * sk})` });
  const kk = pop(t, T.enter, [24, 0.6]);
  css($('key'), { left: '1360px', top: '860px', opacity: t >= T.enter && t < T.enter + 0.9 ? String(1 - prog(t, T.enter + 0.6, T.enter + 0.9)) : '0', transform: `scale(${0.7 + 0.3 * kk}) translateY(${t < T.enter + 0.12 ? 6 : 0}px)` });
  const ck = pop(t, T.cheer - 0.1, SPRING.card);
  css($('cmd'), { left: '960px', top: '930px', opacity: t >= T.cheer - 0.1 && t < T.montage ? String(clamp(ck * 2)) : '0', transform: `translateX(-50%) scale(${0.7 + 0.3 * ck})` });

  // Actors.
  let fxs = '';
  const cl = worlds ? clawdL(t) : null;
  if (cl) { const [x, y] = proj(cL, cl.x, cl.y); actorL.draw({ ...cl, x, y, z: cL.z, grey: t >= T.stuck ? 1 : 0 }); }
  else {
    const cm = worlds ? clawdM(t) : null;
    actorL.draw(cm);
    if (cm && cm.land) fxs += dust(cm.x, cm.y, t, cm.land, cm.z);
    if (cm && t > T.land - 0.25 && t < T.land + 0.6) fxs += sparkles(cm.x, cm.y, t, T.land - 0.2, 6, 110);
  }
  const cr = worlds && t >= T.split ? clawdR(t) : null;
  if (cr) {
    const cR = camR(t), [x, y] = proj(cR, cr.x, cr.y);
    actorR.draw({ ...cr, x, y, z: cR.z, grey: t < T.upgrade ? 1 : 0 });
    if (cr.land) fxs += dust(x, y, t, cr.land, cR.z);
    if (t > T.stampR && t < T.stampR + 1) fxs += sparkles(x, y, t, T.stampR + 0.1);
    if (t > T.cheer && t < T.cheer + 1) fxs += sparkles(x, y, t, T.cheer, 6, 120);
    if (t > T.upgrade && t < T.upgrade + 1) fxs += sparkles(x, y, t, T.upgrade, 6, 110);
    if (t > T.pick && t < T.pick + 1) fxs += sparkles(x, y, t, T.pick, 6, 110);
  } else actorR.draw(null);

  // Montage and end card use their own actor.
  const ce = montage(t) || endCard(t);
  actorE.draw(ce ? { ...ce, z: 1 } : null);
  if (ce && ce.land) fxs += dust(ce.x, ce.y, t, ce.land);
  if (t > T.end && t < T.end + 1.2) fxs += sparkles(225, 330, t, T.end + 0.1, 7, 150, 8);
  if (t > T.end + 1.0) {
    const tw = Math.floor((t - T.end) * 5);
    for (const [x, y, ph] of [[1300, 650, 0], [1790, 700, 1], [1740, 600, 2]]) if ((tw + ph) % 3 !== 0)
      fxs += `<svg style="position:absolute;left:${x}px;top:${y}px" width="35" height="35" viewBox="0 0 5 5" shape-rendering="crispEdges">${pixartSVG((tw + ph) % 2 ? ICONS.spark : ICONS.sparkW)}</svg>`;
  }
  html(fx, fxs);
};

// ---------- setup ----------
function buildQuote() {
  const q = $('quote');
  const words = QUOTE.split(' ');
  const hiCount = QUOTE_HI.split(' ').length;
  q.innerHTML = words.map((w, i) => `<span data-i="${i}">${esc(w)}</span>`).join(' ');
  const spans = [...q.querySelectorAll('span')].slice(0, hiCount);
  const lines = new Map();
  for (const s of spans) {
    const L = lines.get(s.offsetTop) || { x: s.offsetLeft, y: s.offsetTop, r: 0, h: s.offsetHeight };
    L.x = Math.min(L.x, s.offsetLeft); L.r = Math.max(L.r, s.offsetLeft + s.offsetWidth);
    lines.set(s.offsetTop, L);
  }
  LINES = [...lines.values()].sort((a, b) => a.y - b.y).map(L => ({ x: L.x - 4, y: L.y, w: L.r - L.x + 8, h: L.h }));
  LINES.forEach(L => { const d = document.createElement('div'); d.className = 'hl'; Object.assign(d.style, { left: `${L.x}px`, top: `${L.y + 8}px`, height: `${L.h - 12}px`, width: '0px' }); q.appendChild(d); });
}
function measureScroll() {
  // Lay out the final round-3 rows once to find how far the terminal must scroll for the answer.
  setRows($('rowsR'), rowsRight(T.merge));
  const rows = [...$('rowsR').children].filter(d => d.style.display !== 'none');
  const fetchRow = rows.find(d => d.textContent.includes('smart-search fetch'));
  SCROLL_R3 = fetchRow ? Math.max(0, fetchRow.offsetTop - 10) : 0;
}
function buildCards() {
  for (let i = 0; i < 3; i++) {
    const el = $('c' + i);
    el.querySelector('.t').textContent = SOURCES[i][0];
    el.querySelector('.u').textContent = SOURCES[i][1].replace('https://', '');
  }
  $('agents').innerHTML = AGENTS.map((a, i) => { const r = agentRect(i); return `<div class="agent" style="left:${r.x}px;top:${r.y}px">${a}</div>`; }).join('');
  ROUTES.forEach((r, i) => {
    const row = $('jr' + i);
    row.querySelector('.jn').textContent = r.name; row.querySelector('.jc').textContent = r.cap;
    row.querySelector('.jb').classList.toggle('hi', r.p >= 0.5);
  });
  RESEARCH.forEach((r, i) => { $('nd' + i).textContent = r.text; $('nd' + i).classList.toggle('j', r.judge); });
  showPage('mbA', 'providers');
  vis($('mbA-pd-exa'), true); vis($('mbA-pd-routing'), false);
  appInput($('mbA-exa-key'), { ph: '••••••••' });
  $('mbA-exa-res').innerHTML = '<div class="ss-sub">测试时的有效配置 · 2026-10-20 14:03:12</div><div class="ss-sub">检查方式：真实请求</div>';
}

const TEXT = document.body.textContent + PROMPT + INSTALL + SETUP + QUESTION + ANSWER_R + ANSWER_L + QUOTE + AGENTS.join('') + SOURCES.flat().join('')
  + ROUTES.map(r => r.name + r.cap).join('') + RESEARCH.map(r => r.text).join('') + '0123456789.—'
  + '同一个问题：READY…GO!第回合选路搜索读原文回答卡糊……叮唰！还在转圈只拿到摘要只能凭记忆只有一个内置搜索给每个渠道打分只派发最合适的那个来源一次列全检索结果与摘录证据：not_evaluated原网页正文抓下原网页，原话可引用回答带出处，点开就能核对让去查一下当前文档内置搜索：一直转圈，读网页只拿到摘要右边换上✓有出处？（）正文行Markdown8FPS60$>…'
  + '已配置未配置通过尚未测试测试时的有效配置 · 2026-10-20 14:03:12检查方式：真实请求••••••••';
loadFonts([
  ['400 22px "JetBrains Mono"', TEXT], ['700 22px "JetBrains Mono"', TEXT],
  ['400 22px "Noto Sans SC"', TEXT], ['500 44px "Noto Sans SC"', TEXT], ['700 44px "Noto Sans SC"', TEXT], ['900 44px "Noto Sans SC"', TEXT],
  ['400 22px Inter', TEXT], ['600 26px Inter', TEXT], ['700 50px Inter', TEXT], ['400 56px "ZCOOL KuaiLe"', TEXT],
]).then(() => {
  buildCards();
  // Hidden elements have no layout, so show the right world and the page while measuring.
  const els = [$('wr'), $('page')], prev = els.map(e => e.style.display);
  els.forEach(e => { e.style.display = 'block'; });
  buildQuote(); measureScroll();
  els.forEach((e, i) => { e.style.display = prev[i]; });
  window.render(0); window.ready = true;
});
