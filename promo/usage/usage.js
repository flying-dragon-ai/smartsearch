// 日常使用: ask the AI, search and research in the App, read 活动, the four CLI commands, and close the App.
// Every frame is a pure function of t; click targets and camera framings are measured once from the scene at that moment.
import { appMarkup, showPage, input, flyout, dialog, resultSources, activityList, activityDetail, CURSOR, TOOLS } from '../shared/app.js';
import { clamp, lerp, prog, easeInOut, easeOut, easeIn, spring, SPRING, hop, typed, loadFonts } from '../shared/motion.js';
import { $, css, html, vis, cls, Actor } from '../shared/actor.js';
import { pop, rectOf, framing, camAt, pointerAt, cheerAt, capText, stepChip, sparkles, marker } from '../shared/tutorial.js';
import { T, STEPS, PROMPT, PROMPT_HI, ALT, PROMPT2, ANSWER, SOURCES, RESULT, Q1, Q2, CHEAT, CLICKS, DLG, NOTICES, CAPS, TYPE } from './timeline.js';

const stage = $('stage');
const fit = () => { stage.style.transform = `scale(${innerWidth / 1920})`; };
fit(); addEventListener('resize', fit);

const A = { x: 160, y: 70, w: 1600, h: 940 };   // the App window, world coordinates
const TA = { x: 200, y: 110, w: 1520, h: 860 };  // the agent's terminal
const TB = { x: 160, y: 170, w: 1600, h: 740 };  // the command cheat sheet
$('appHost').innerHTML = appMarkup('a', { w: A.w, h: A.h, left: A.x, top: A.y });
$('cur').innerHTML = CURSOR;
$('cheat').innerHTML = CHEAT.map(([, e], i) => `<div class="crow" id="cr${i}" style="top:${40 + i * 165}px"><div class="ccmd"><span class="p">$ </span><span id="cc${i}"></span></div><div class="cexp" id="ce${i}"># ${e}</div></div>`).join('');
$('alt').innerHTML = `也可以这样问：<em>「${ALT}」</em>`;
const guide = new Actor($('aG'));
const esc = s => s.replace(/&/g, '&amp;').replace(/</g, '&lt;');
const DIR = 'C:\\Users\\me\\AppData\\Local\\smart-search';

// ---------- the agent's terminal ----------
const bul = c => `<span class="bul ${c}"></span>`;
const elbow = '<span class="elbow"></span>';
const caret = on => on ? '<span class="caret"></span>' : '';
function promptHTML(t) {
  const n = typed(TYPE.prompt, t), chars = [...PROMPT];
  if (n < chars.length) return esc(chars.slice(0, n).join(''));
  // Once typed, the three things worth saying get a marker, one after another.
  let s = esc(PROMPT);
  PROMPT_HI.forEach((ph, i) => {
    const k = easeOut(prog(t, T.tips + i * 0.5, T.tips + i * 0.5 + 0.35));
    s = s.replace(esc(ph), `<span class="hi" style="background-size:${(k * 100).toFixed(1)}% 100%">${esc(ph)}</span>`);
  });
  return s;
}
function rowsA(t) {
  const n = typed(TYPE.prompt, t);
  const rows = [`<span class="p">&gt;</span> ${promptHTML(t)}${caret(t < T.enter && n >= [...PROMPT].length && Math.floor(t * 2.5) % 2 === 0)}`, ''];
  if (t >= T.bash1) rows.push(`${bul(t >= T.res1 ? 'ok' : (Math.floor(t * 6) % 2 ? 'ink' : ''))}<b>Bash</b>(smart-search search "useEffect 清理规则" --format markdown)`);
  if (t >= T.res1) rows.push(`${elbow}<span class="dim">…（检索结果与摘录）</span>`);
  if (t >= T.res1 + 0.05) rows.push('   <span class="dim">证据：not_evaluated</span>');
  if (t >= T.res1 + 0.1) rows.push('   ## 来源');
  SOURCES.forEach(([title, url], i) => { if (t >= T.res1 + 0.18 + i * 0.08) rows.push(`   - [${title}](<span class="url">${url}</span>)`); });
  if (t >= T.fetch1) rows.push('', `${bul(t >= T.fres1 ? 'ok' : 'ink')}<b>Bash</b>(smart-search fetch "<span class="url">${SOURCES[0][1]}</span>" --format markdown)`);
  if (t >= T.fres1) rows.push(`${elbow}<span class="dim">…（原网页正文，Markdown）</span>`);
  if (t >= T.answer) {
    rows.push('', `${bul('ink')}${esc([...ANSWER].slice(0, typed(TYPE.answer, t)).join(''))}`);
    const done = TYPE.answer[TYPE.answer.length - 1] + 0.15;
    if (t >= done) rows.push('', '  <b>来源</b>');
    SOURCES.forEach(([title, url], i) => { if (t >= done + 0.15 * (i + 1)) rows.push(`  [${i + 1}] ${title} · <span class="url">${url.replace('https://', '')}</span>`); });
  }
  // After the App is closed: a new question, answered through the same CLI.
  if (t >= T.type1 - 0.3) {
    rows.push('', `<span class="p">&gt;</span> ${esc([...PROMPT2].slice(0, typed(TYPE.prompt2, t)).join(''))}${caret(t < T.bash2 && Math.floor(t * 2.5) % 2 === 0)}`);
    if (t >= T.bash2) rows.push('', `${bul(t >= T.res2 ? 'ok' : (Math.floor(t * 6) % 2 ? 'ink' : ''))}<b>Bash</b>(smart-search search "useEffect useLayoutEffect 区别" --format markdown)`);
    if (t >= T.res2) rows.push(`${elbow}<span class="dim">…（检索结果与摘录）</span>`);
  }
  return rows;
}
function setRows(el, rows) {
  while (el.children.length < rows.length) { const d = document.createElement('div'); d.className = 'row'; el.appendChild(d); }
  [...el.children].forEach((d, i) => { if (i < rows.length) { html(d, rows[i]); vis(d, true); } else vis(d, false); });
}
let SCROLL_A = 0;

// ---------- the App ----------
const RUNS = {
  res: { title: '在线研究', time: '2026-10-20 14:06:40', origin: '桌面 App', phase: '处理请求', provider: '服务商：context7', button: '取消任务',
    events: ['2026-10-20 14:06:40 · 已启动 · 运行中', '2026-10-20 14:06:40 · 研究 · 运行中', '2026-10-20 14:06:41 · 处理请求 · 运行中 · 服务商：exa', '2026-10-20 14:06:41 · 处理请求 · 运行中 · 服务商：context7'] },
  app: { title: '搜索', time: '2026-10-20 14:06:12', origin: '桌面 App', status: '已完成', phase: '搜索', elapsed: '00:02' },
  fetch: { title: '读取网页', time: '2026-10-20 14:05:08', origin: '终端 / AI', status: '已完成', phase: '读取网页', elapsed: '00:03' },
  ai: { title: '搜索', time: '2026-10-20 14:05:01', origin: '终端 / AI', status: '已完成', phase: '搜索', elapsed: '00:06', provider: '服务商：exa',
    events: ['2026-10-20 14:05:01 · 已启动 · 运行中', '2026-10-20 14:05:01 · 搜索 · 运行中', '2026-10-20 14:05:02 · 处理请求 · 运行中 · 服务商：exa', '2026-10-20 14:05:07 · 搜索 · 已完成 · 服务商：exa'] },
};
const mmss = s => `00:${String(Math.max(0, Math.floor(s))).padStart(2, '0')}`;
let POP_SCROLL = 0;

function applyApp(t, settled = false) {
  const pages = [[0, 'overview'], [T.page, 'search'], [T.seePress + 0.15, 'activity']];
  const [since, page] = pages.filter(([a]) => t >= a).pop();
  showPage('a', page, settled || since === 0 ? 1 : Math.min(1, spring(t - since, ...SPRING.card)));

  // 搜索与研究: 搜索 first, then 在线研究.
  const research = t >= T.optPress;
  html($('a-tool'), research ? '在线研究' : '搜索');
  html($('a-tdesc'), research ? '真正执行深度研究：拆子问题、找来源、抓正文、核对后给结论。耗时较长。' : '选择一个合适渠道检索，返回结果和来源；普通搜索只运行一轮。');
  vis($('a-depth'), research); vis($('a-evd'), research);
  const q = research ? [...Q2].slice(0, typed(TYPE.q2, t)).join('') : [...Q1].slice(0, typed(TYPE.q1, t)).join('');
  const qFocus = research ? t >= T.q2Press && t < T.run2Press : t >= T.qPress && t < T.runPress;
  input($('a-q'), { text: q, focus: qFocus, caret: qFocus && Math.floor(t * 2.2) % 2 === 0 });
  const busyA = t >= T.runPress && t < T.done, busyB = t >= T.run2Press;
  html($('a-run'), busyA || busyB ? '运行中…' : research ? '开始 在线研究' : '开始 搜索');
  cls($('a-run'), 'off', busyA || busyB);
  const showBusy = (t >= T.busy && t < T.done) || t >= T.busy2, showRes = t >= T.done && t < T.busy2;
  vis($('a-empty'), !showBusy && !showRes, 'flex'); vis($('a-busy'), showBusy, 'flex'); vis($('a-res'), showRes);
  css($('a-spin'), { transform: `rotate(${((t * 400) % 360).toFixed(1)}deg)` });
  html($('a-text'), esc(RESULT));
  html($('a-srcs'), resultSources(SOURCES));
  // The tool list opens, scrolls down to 在线研究 and closes on the pick.
  const popOn = t >= T.toolPress + 0.05 && t < T.optPress + 0.12;
  vis($('a-pop'), popOn);
  css($('a-popl'), { transform: `translateY(${-(POP_SCROLL * easeInOut(prog(t, T.popScroll, T.popScroll + 0.8))).toFixed(1)}px)` });
  cls($('a-opt0'), 'on', true);

  // 活动: the research keeps running; the AI's own search and fetch are listed too.
  const live = { ...RUNS.res, status: '运行中', elapsed: mmss(t - T.run2Press) };
  const rows = [{ key: 'res', ...live }, { key: 'app', ...RUNS.app }, { key: 'fetch', ...RUNS.fetch }, { key: 'ai', ...RUNS.ai }];
  const sel = t >= T.rowPress2 ? 'ai' : t >= T.rowPress1 ? 'res' : '';
  html($('a-alist'), activityList('a', rows, sel));
  const run = sel === 'ai' ? RUNS.ai : sel === 'res' ? live : null;
  html($('a-adetail'), run ? activityDetail('a', { ...run, started: run.time, dir: DIR })
    : `<div style="height:640px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:12px;text-align:center"><div class="ss-h2">选择一条活动记录</div><div class="ss-sub">在左侧选择任务，查看状态、阶段事件和结果。</div></div>`);

  // Notices, the close dialog, hover and press.
  const n = NOTICES.find(([a, b]) => t >= a && t < b);
  flyout('a', n ? { on: true, k: Math.min(1, spring(t - n[0], ...SPRING.card)) * (1 - prog(t, n[1] - 0.2, n[1])), title: n[2], msg: n[3], ...FLY } : { on: false });
  const d = t >= T.dlg && t < T.bgPress + 0.12;
  dialog('a', d ? { on: true, k: Math.min(1, spring(t - T.dlg, ...SPRING.card)), ...DLG, w: 760, appW: A.w, appH: A.h } : { on: false });
  for (const [arrive, id, press] of CLICKS) {
    const el = $(id);
    if (!el) continue;
    cls(el, 'hover', t >= arrive && t < press);
    cls(el, 'press', t >= press && t < press + 0.15);
  }
}
let FLY = { x: 0, y: 0 };

// The overview the App opens on: CLI ready, basic configuration done.
function staticOverview() {
  html($('a-c1s'), '0.1.30 · 已就绪');
  for (const id of ['a-c1b', 'a-c1r', 'a-c1x', 'a-c1m']) vis($(id), false);
  html($('a-c2s'), '基础配置已完成，可以开始搜索。');
  vis($('a-c2go'), true, 'inline-flex');
  ['xAI', 'Exa', 'Jina'].forEach((name, i) => { html($(`a-r${i}d`), name); html($(`a-r${i}s`), '已配置'); $(`a-r${i}s`).className = 'ss-sub'; });
  input($('a-evdv'), {});
}

// ---------- scenes: which windows are on the desk ----------
function scenes(t) {
  const out = (a, b) => easeIn(prog(t, a, b)), into = t0 => Math.min(1, spring(t - t0, ...SPRING.card));
  // Agent terminal: scene 1, then back after the App is closed.
  const aOn = t < T.s2 + 0.5 || t >= T.gone - 0.1;
  vis($('termA'), aOn);
  if (aOn) {
    const k = t < T.s2 + 0.5 ? 1 - out(T.s2 - 0.05, T.s2 + 0.45) : into(T.gone - 0.1);
    css($('termA'), { opacity: String(clamp(k * 1.5)), transform: `translateY(${((1 - k) * -80).toFixed(1)}px)` });
  }
  // App: scenes 2–4, and again to be closed in scene 6.
  const appOn = (t >= T.s2 - 0.05 && t < T.s5 + 0.45) || (t >= T.s6 - 0.05 && t < T.gone + 0.6);
  vis($('a'), appOn);
  if (appOn) {
    let k, tr = '';
    if (t < T.s5 + 0.45) { k = into(T.s2 - 0.05) * (1 - out(T.s5 - 0.05, T.s5 + 0.4)); tr = `translateY(${((1 - k) * 600).toFixed(1)}px)`; }
    else if (t < T.gone) { k = into(T.s6 - 0.05); tr = `translateY(${((1 - k) * 600).toFixed(1)}px)`; }
    else { const g = out(T.gone, T.gone + 0.55); k = 1 - g; tr = `translate(${(g * 700).toFixed(1)}px, ${(g * 420).toFixed(1)}px) scale(${(1 - 0.85 * g).toFixed(4)})`; }
    css($('a'), { opacity: String(clamp(k * 2)), transform: tr, transformOrigin: '100% 100%' });
  }
  // Cheat sheet terminal: scene 5.
  const bOn = t >= T.s5 - 0.05 && t < T.s6 + 0.45;
  vis($('termB'), bOn);
  if (bOn) {
    const k = into(T.s5 - 0.05) * (1 - out(T.s6 - 0.05, T.s6 + 0.4));
    css($('termB'), { opacity: String(clamp(k * 2)), transform: `translateY(${((1 - k) * 600).toFixed(1)}px)` });
    [T.c0, T.c1, T.c2, T.c3].forEach((t0, i) => {
      vis($(`cr${i}`), t >= t0 - 0.05);
      html($(`cc${i}`), esc([...CHEAT[i][0]].slice(0, typed(TYPE.cheat[i], t)).join('')));
      const ke = pop(t, TYPE.cheat[i][TYPE.cheat[i].length - 1] + 0.1, SPRING.card);
      css($(`ce${i}`), { opacity: String(clamp(ke * 1.5)), transform: `translateX(${((1 - ke) * -30).toFixed(1)}px)` });
    });
  }
  // The second example prompt.
  const altOn = t >= T.alt && t < T.s2 + 0.3;
  css($('alt'), { left: '300px', top: '860px', display: altOn ? 'block' : 'none' });
  if (altOn) { const k = pop(t, T.alt, [20, 0.6]) * (1 - out(T.s2 - 0.1, T.s2 + 0.25)); css($('alt'), { opacity: String(clamp(k * 2)), transform: `scale(${(0.6 + 0.4 * k).toFixed(4)}) rotate(-1.5deg)` }); }
  setRows($('rowsA'), rowsA(t));
  css($('rowsA'), { transform: `translateY(${-(SCROLL_A * easeInOut(prog(t, T.type1 - 0.5, T.type1))).toFixed(1)}px)` });
}

// ---------- measuring ----------
// A band of the agent's terminal, from its left margin to x1.
const term = (y0, y1, x1 = TA.x + TA.w - 20) => ({ x: TA.x + 20, y: y0, w: x1 - TA.x - 20, h: y1 - y0 });
const CAMS = [
  [0, 'termA', 0.86], [T.s1, 'termA', 0.86],
  [T.type0 - 0.3, term(150, 340, 1440), 1.32],
  [T.bash1 - 0.2, term(150, 500, 1560), 1.25],
  [T.answer - 0.2, term(450, 820, 1640), 1.2],
  [T.alt - 0.3, 'termA+alt', 0.86],
  [T.s2, 'app', 0.92],
  [T.navPress - 0.6, ['a-n-overview', 'a-n-skills'], 1.3],
  [T.page + 0.1, 'app', 0.95],
  [T.qPress - 0.5, ['a-tool', 'a-run'], 1.45, T.qPress + 0.5],
  [T.busy + 0.05, ['a-run', 'a-busy'], 1.0, T.busy + 0.3],
  [T.done + 0.05, ['a-text', 'a-srcs'], 1.25, T.done + 0.4],
  [T.copyPress - 0.6, ['a-copy', 'a-fly'], 1.2, T.copied + 0.3],
  [T.s3, 'app', 0.95],
  [T.toolPress - 0.4, ['a-tool', 'a-pop'], 1.3, T.popScroll + 0.9],
  [T.optPress + 0.3, ['a-tool', 'a-run'], 1.4, T.q2Press + 0.4],
  [T.busy2 + 0.1, ['a-run', 'a-busy'], 1.0, T.busy2 + 0.4],
  [T.s4 + 0.1, 'app', 0.95],
  [T.rowPress1 + 0.2, ['a-alist', 'a-aev'], 1.0, T.rowPress1 + 0.4],
  [T.rowPress2 + 0.2, ['a-ar-ai', 'a-aev'], 1.05, T.rowPress2 + 0.4],
  [T.s5, 'termB', 0.98],
  [T.s6, 'app', 0.92],
  [T.dlg, ['a-dlg'], 1.25, T.dlg + 0.6],
  [T.gone + 0.2, term(540, 960, 1640), 1.2],
];
let CAM = [], CLK = [];
// Lay out the desk as at time t, with every window at rest, for measuring.
function settle(t) {
  scenes(t); applyApp(t, true);
  for (const id of ['a', 'termA', 'termB']) css($(id), { transform: 'none', opacity: '1' });
}
function measure() {
  css($('cam'), { transform: 'none' });
  vis($('world'), true);
  staticOverview();
  // How far the terminal scrolls in scene 6, and the tool list to reach 在线研究.
  scenes(T.end - 0.01); css($('rowsA'), { transform: 'none' });
  const vp = $('termA').querySelector('.viewport').getBoundingClientRect(), last = $('rowsA').getBoundingClientRect();
  SCROLL_A = Math.max(0, last.bottom - vp.bottom + 40) / (innerWidth / 1920);
  settle(T.popScroll);
  css($('a-popl'), { transform: 'none' });
  const list = rectOf('a-pop'), opt = rectOf('a-opt24');
  POP_SCROLL = Math.max(0, opt.y + opt.h - (list.y + list.h) + 60);
  settle(T.copied);
  const fb = rectOf('a-fb');
  FLY = { x: clamp(fb.x - A.x + fb.w / 2 - 260, 12, A.w - 532), y: fb.y - A.y + fb.h + 8 };
  CAM = CAMS.map(([t, what, zMax, at]) => {
    if (what === 'app') return [t, { cx: A.x + A.w / 2, cy: A.y + A.h / 2, z: zMax }];
    if (what === 'termA') return [t, { cx: TA.x + TA.w / 2, cy: TA.y + TA.h / 2, z: zMax }];
    if (what === 'termA+alt') return [t, { cx: TA.x + TA.w / 2, cy: TA.y + TA.h / 2 + 30, z: zMax }];
    if (what === 'termB') return [t, { cx: TB.x + TB.w / 2, cy: TB.y + TB.h / 2, z: zMax }];
    if (!Array.isArray(what) && typeof what === 'object') return [t, framing(what, zMax)];
    settle(at ?? t);
    return [t, framing(rectOf(what), zMax)];
  });
  CLK = CLICKS.map(([arrive, id, press]) => { settle(press - 0.01); const r = rectOf(id); return { arrive, press, x: r.x + r.w / 2, y: r.y + r.h / 2 }; });
}

// ---------- Clawd ----------
const CHEERS = [TYPE.answer[TYPE.answer.length - 1] + 0.9, T.done + 0.5, T.rowPress2 + 0.8, T.c3 + 1.7, T.res2 + 0.5];
let END_LABEL = { x: 0, y: 0, w: 0 };
function guideAt(t) {
  if (t < T.s1 + 0.4) {
    const j0 = 0.55, j1 = 0.95;
    if (t < j0) return null;
    if (t < j1) { const k = prog(t, j0, j1); return { x: lerp(2000, 560, k), y: lerp(240, 392, k) - 160 * hop(k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
    const d = t - j1, out = prog(t, T.s1 - 0.1, T.s1 + 0.35);
    if (out > 0) return { x: lerp(560, 760, out), y: lerp(392, 1300, easeIn(out)) - 120 * hop(Math.min(1, out * 1.6)), sq: -0.1, pose: { eyes: 'happy', arms: 'up', legs: 'tuck' } };
    return { x: 560, y: 392, sq: 0.25 * Math.exp(-d * 9) * Math.cos(d * 22), land: j1, pose: { eyes: d < 0.3 ? 'shut' : 'happy', arms: Math.floor(d * 4) % 2 ? 'wave' : 'up', legs: 'stand' } };
  }
  if (t >= T.end) {
    const j0 = T.end + 0.7, j1 = j0 + 0.35, r = END_LABEL, x = r.x + r.w - 90;
    if (t < j0) return null;
    if (t < j1) { const k = prog(t, j0, j1); return { x: lerp(2000, x, k), y: lerp(300, r.y, k) - 160 * hop(k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
    const d = t - j1;
    return { x, y: r.y, sq: 0.28 * Math.exp(-d * 9) * Math.cos(d * 22), land: j1, pose: { eyes: d > 2.4 && d < 2.5 ? 'blink' : 'happy', arms: Math.floor(d * 3.5) % 2 ? 'wave' : 'down', legs: 'stand' } };
  }
  return cheerAt(t, CHEERS);
}

// ---------- render ----------
window.render = function (t) {
  const inWorld = t >= T.s1 - 0.4 && t < T.end + 0.4;
  vis($('world'), inWorld);
  vis($('title'), t < T.s1 + 0.6);
  vis($('endc'), t >= T.end);

  if (t < T.s1 + 0.6) {
    const out = easeIn(prog(t, T.s1 - 0.2, T.s1 + 0.3));
    [['tKicker', 0.15, 330], ['tBig', 0.25, 380], ['tSub', 0.5, 560]].forEach(([id, t0, y]) => {
      const k = pop(t, t0, SPRING.card);
      css($(id), { left: '110px', top: `${y - 90 * out}px`, opacity: String(clamp(k * 1.5) * (1 - out)), transform: `translateY(${((1 - k) * 40).toFixed(1)}px)` });
    });
    [...$('toc').children].forEach((el, i) => {
      const k = pop(t, 0.7 + i * 0.12, SPRING.card);
      css(el, { opacity: String(clamp(k * 1.5) * (1 - out)), transform: `translateX(${((1 - k) * 60).toFixed(1)}px) translateY(${(-90 * out).toFixed(1)}px)` });
    });
  }

  if (inWorld) {
    scenes(t);
    applyApp(t);
    const c = camAt(t, CAM);
    css($('cam'), { transform: `translate(${c.tx.toFixed(2)}px, ${c.ty.toFixed(2)}px) scale(${c.z.toFixed(4)})` });
    // The pointer belongs to the App; it is hidden while the cheat sheet is up.
    const p = t >= T.s5 - 0.1 && t < T.s6 + 0.1 ? null : pointerAt(t, CLK, { x: A.x + 1150, y: A.y + 820 }, T.s2 + 0.5, T.gone + 0.1);
    vis($('cur'), !!p);
    if (p) css($('cur'), { transform: `translate(${(p.x - 2).toFixed(1)}px, ${(p.y - 2).toFixed(1)}px) scale(${p.down ? 0.88 : 1})`, transformOrigin: '2px 2px' });
    const cl = CLK.find(c => t >= c.press && t < c.press + 0.4);
    vis($('rip'), !!cl);
    if (cl) { const k = easeOut(prog(t, cl.press, cl.press + 0.4)), r = 10 + 34 * k; css($('rip'), { left: `${cl.x - r}px`, top: `${cl.y - r}px`, width: `${2 * r}px`, height: `${2 * r}px`, opacity: String(1 - k) }); }
  }

  stepChip(t, STEPS, T.end);
  capText($('cap'), t, CAPS);

  if (t >= T.end) {
    [['eBig', 0.0, 210], ['eL1', 0.3, 420], ['eCmd', 0.55, 520], ['eL2', 0.75, 640], ['eGh', 1.0, 760]].forEach(([id, d, y]) => {
      const k = pop(t, T.end + d, SPRING.card);
      css($(id), { left: '110px', top: `${y}px`, opacity: String(clamp(k * 1.5)), transform: `translateY(${((1 - k) * 40).toFixed(1)}px)` });
    });
    css($('eNote'), { opacity: String(clamp(pop(t, T.end + 1.2, SPRING.card))) });
    const km = pop(t, T.end + 0.9, SPRING.mascot);
    css($('eMascot'), { left: '1240px', top: `${lerp(1100, 470, km) + 6 * Math.sin((t - T.end) * 2.6)}px` });
  }

  let fx = '';
  const g = guideAt(t);
  guide.draw(g);
  if (g && g.cheer !== undefined && t > g.cheer && t < g.cheer + 1) fx += sparkles(g.x, g.y, t, g.cheer);
  if (g && t > T.end + 1.05 && t < T.end + 2.0) fx += sparkles(g.x, g.y, t, T.end + 1.05);
  html($('fx'), fx);
};

// ---------- setup ----------
const TEXT = document.body.textContent + CAPS.map(c => c[2]).join('') + STEPS.map(s => s.join('')).join('') + PROMPT + PROMPT2 + ANSWER + RESULT + Q1 + Q2
  + CHEAT.flat().join('') + DLG.title + DLG.body + DLG.ok + DLG.second + DLG.cancel + NOTICES.map(n => n[2] + n[3]).join('') + TOOLS.join('')
  + JSON.stringify(RUNS) + '运行中…开始 搜索在线研究选择一条活动记录在左侧选择任务，查看状态、阶段事件和结果。来源链接（2）· react.dev 用时阶段事件取消任务配置目录开始'
  + '检索结果与摘录证据：not_evaluated原网页正文来源Bash(smart-search)>[]-#0123456789:';
loadFonts([
  ['400 21px "Noto Sans SC"', TEXT], ['500 21px "Noto Sans SC"', TEXT], ['700 21px "Noto Sans SC"', TEXT], ['900 38px "Noto Sans SC"', TEXT],
  ['400 21px Inter', TEXT], ['600 21px Inter', TEXT], ['700 21px Inter', TEXT],
  ['400 21px "JetBrains Mono"', TEXT], ['700 21px "JetBrains Mono"', TEXT], ['400 60px "ZCOOL KuaiLe"', TEXT],
]).then(() => {
  measure();
  vis($('endc'), true);
  css($('eBig'), { left: '110px', top: '210px' });
  END_LABEL = rectOf('eBigS');
  window.render(0);
  window.ready = true;
});
