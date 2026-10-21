// 配置教程: the App page by page. A pointer does the clicks; one camera follows it; Clawd cheers each finished step.
// Every frame is a pure function of t. Click targets and camera framings are measured once, from the App as it
// looks at that moment, so the pointer always lands on the real button.
import { appMarkup, showPage, providerList, skillRows, input, flyout, dialog, CURSOR } from '../shared/app.js';
import { clamp, lerp, prog, easeInOut, easeOut, easeIn, spring, SPRING, hop, typed, loadFonts } from '../shared/motion.js';
import { $, css, html, vis, cls, Actor } from '../shared/actor.js';
import { pop, rectOf, framing, camAt, pointerAt, cheerAt, capText, stepChip, sparkles, marker } from '../shared/tutorial.js';
import { T, DUR, STEPS, CLICKS, DLG1, DLG2, NOTICES, CAPS, TYPE } from './timeline.js';

const stage = $('stage');
const scale = () => innerWidth / 1920;
const fit = () => { stage.style.transform = `scale(${scale()})`; };
fit(); addEventListener('resize', fit);

const A = { x: 160, y: 70, w: 1600, h: 940 };   // the App window, world coordinates
$('appHost').innerHTML = appMarkup('a', { w: A.w, h: A.h, left: A.x, top: A.y });
$('cur').innerHTML = CURSOR;
const guide = new Actor($('aG'));
const STAMP = '2026-10-20 14:03:12';
const KEY_PH = '示例：your-api-key';
const VIEW = 724;   // visible height of a page above its footer

// Scroll offsets, measured at setup.
const SCROLL = { exa: 0, rt: 0, sk: 0, list: 0 };
const scrollAt = (t, t0, d, to) => to * easeInOut(prog(t, t0, t0 + d));

// ---------- the App as a function of t ----------
function applyApp(t, settled = false) {
  const pages = [[0, 'overview'], [T.prov, 'providers'], [T.sk, 'skills'], [T.st, 'settings'], [T.ov, 'overview']];
  const [since, page] = pages.filter(([a]) => t >= a).pop();
  showPage('a', page, settled || since === 0 ? 1 : Math.min(1, spring(t - since, ...SPRING.card)));
  const connected = t >= T.ready;
  // 概览, card 1: install the CLI. While the App installs, the card shows only the operation, 环境详情… and progress.
  const installing = t >= T.installing && t < T.flyCli, connecting = t >= T.flyCli && t < T.ready;
  cls($('a-dot'), 'on', connected); cls($('a-dot'), 'wait', connecting);
  html($('a-c1s'), connected ? '0.1.30 · 已就绪' : connecting ? '正在检测本地环境…' : installing ? '正在通过原管理器安装或更新 CLI…'
    : 'Node.js/npm 已就绪，等待准备 Smart Search CLI');
  html($('a-c1b'), t >= T.c1Press ? '处理中…' : '安装 CLI');
  cls($('a-c1b'), 'off', t >= T.c1Press);
  // Once the install returns the App finds a compatible CLI: no install button or manual links, only 重新检测 while it connects.
  const idle = t < T.installing;
  vis($('a-c1b'), idle, 'inline-flex'); vis($('a-c1x'), idle, 'inline-flex'); vis($('a-c1m'), idle, 'inline');
  vis($('a-c1r'), !installing && !connected, 'inline-flex');
  vis($('a-c1e'), !installing);
  vis($('a-c1p'), installing);
  if (installing) css($('a-c1p').firstElementChild, { left: `${((((t - T.installing) * 0.9) % 1.3) - 0.3) * 100}%` });
  html($('a-c1g'), 'CLI 安装完成，正在重新连接。');
  vis($('a-c1g'), connecting);

  // Card 2: rows appear once the backend is connected; all three filled when we come back.
  const back = t >= T.ov;
  html($('a-c2s'), back ? '基础配置已完成，可以开始搜索。' : '选择搜索服务，填写 API Key。');
  vis($('a-c2go'), back, 'inline-flex');
  for (const id of ['a-c2b', 'a-c3b', 'a-c4b']) cls($(id), 'off', !connected);
  ['xAI', 'Exa', 'Jina'].forEach((name, i) => {
    vis($(`a-r${i}`), connected);
    html($(`a-r${i}d`), back ? name : '选择一个服务商开始配置。');
    html($(`a-r${i}s`), back ? '已配置' : '未配置');
    $(`a-r${i}s`).className = back ? 'ss-sub' : 'ss-link';
  });
  vis($('a-c2f'), connected, 'flex');

  // 服务商: the list, Exa, then 意图路由.
  const sel = t >= T.rtPress ? 'routing' : t >= T.exaPress ? 'exa' : 'routing';
  const nKey = typed(TYPE.exa, t), nRt = typed(TYPE.rt, t);
  const exaDraft = nKey > 0 && t < T.saved, rtDraft = nRt > 0 && t < T.rtSaved;
  const configured = [...(t >= T.saved ? ['exa'] : []), ...(t >= T.flipX ? ['xai'] : []), ...(t >= T.flipJ ? ['jina'] : [])];
  html($('a-pl'), providerList('a', { selected: sel, configured, unsaved: exaDraft ? ['exa'] : [] }));
  const ls = scrollAt(t, T.flipJ - 0.45, 0.35, SCROLL.list) * (1 - easeInOut(prog(t, T.s3, T.s3 + 0.4)));
  css($('a-pl'), { transform: `translateY(${-ls.toFixed(1)}px)` });
  vis($('a-pd-exa'), sel === 'exa'); vis($('a-pd-routing'), sel === 'routing');

  const keyFocus = t >= T.keyPress && t < T.testPress;
  input($('a-exa-key'), t >= T.saved ? { ph: '••••••••' } : { text: '•'.repeat(nKey), ph: KEY_PH, focus: keyFocus, caret: keyFocus && Math.floor(t * 2.2) % 2 === 0 });
  const testing = t >= T.testPress && t < T.testDone;
  html($('a-exa-test'), testing ? '测试中…' : exaDraft ? '用未保存的修改测试' : '测试');
  const pill = $('a-exa-pill');
  html(pill, testing ? '测试中' : t >= T.testDone ? '通过' : '尚未测试');
  pill.className = 'ss-pill' + (testing ? ' act' : t >= T.testDone ? ' ok' : '');
  html($('a-exa-res'), testing ? '<div class="ss-sub">正在等待服务商响应，请稍候。可在活动页取消。</div>'
    : t >= T.testDone ? `<div class="ss-stack s8"><div class="ss-sub">未保存修改的测试 · ${STAMP}</div><div class="ss-sub">此结果对应测试时尚未保存的修改；再次测试可确认当前配置。</div><div class="ss-sub">检查方式：真实请求</div><div class="ss-sub">技术详情 ⌄</div></div>` : '');
  css($('a-pd-exa'), { transform: `translateY(${-scrollAt(t, T.testPress - 1.3, 0.7, SCROLL.exa).toFixed(1)}px)` });

  const rtFocus = t >= T.rtKeyPress && t < T.rtScroll;
  input($('a-rt-key'), t >= T.rtSaved ? { ph: '••••••••' } : { text: '•'.repeat(nRt), ph: KEY_PH, focus: rtFocus, caret: rtFocus && Math.floor(t * 2.2) % 2 === 0 });
  css($('a-pd-routing'), { transform: `translateY(${-scrollAt(t, T.rtScroll, 0.6, SCROLL.rt).toFixed(1)}px)` });

  const unsaved = (exaDraft ? 1 : 0) + (rtDraft ? 1 : 0);
  html($('a-pfs'), unsaved ? `有 ${unsaved} 项未保存修改 · 密钥留空会保留原值` : '没有未保存的修改 · 测试不会自动保存配置');
  const saving = (t >= T.savePress && t < T.saved) || (t >= T.rtSavePress && t < T.rtSaved);
  html($('a-pfv'), saving ? '保存中…' : '保存更改');

  // 更新 Skills.
  const on = ['Codex', 'Claude Code', 'Cursor', ...(t >= T.gemPress ? ['Gemini CLI'] : [])];
  html($('a-skrows'), skillRows('a', { on, status: t >= T.synced ? Object.fromEntries(on.map(a => [a, '与来源一致'])) : {} }));
  html($('a-skc'), `已选择 ${on.length} 个 Agent`);
  html($('a-skgo'), t >= T.goPress && t < T.synced ? '更新中…' : '更新所选 Skills');
  html($('a-skres'), t >= T.syncing && t < T.synced ? '正在更新所选 Skills…' : t >= T.synced ? '已同步 4 个，失败 0 个。' : '');
  css($('a-sks'), { transform: `translateY(${-scrollAt(t, T.sk + 0.35, 0.55, SCROLL.sk).toFixed(1)}px)` });

  // Dialogs and the 操作提示 flyout.
  const d = t >= T.dlg1 && t < T.dlg1Press + 0.12 ? [T.dlg1, DLG1] : t >= T.dlg2 && t < T.dlg2Press + 0.12 ? [T.dlg2, DLG2] : null;
  dialog('a', d ? { on: true, k: Math.min(1, spring(t - d[0], ...SPRING.card)), ...d[1], appW: A.w, appH: A.h } : { on: false });
  const n = NOTICES.find(([a, b]) => t >= a && t < b);
  flyout('a', n ? { on: true, k: Math.min(1, spring(t - n[0], ...SPRING.card)) * (1 - prog(t, n[1] - 0.2, n[1])), title: n[2], msg: n[3], ...FLY } : { on: false });

  // Hover and press on whatever the pointer is over.
  for (const [arrive, id, press] of CLICKS) {
    const el = $(id);
    if (!el) continue;
    cls(el, 'hover', t >= arrive && t < press);
    cls(el, 'press', t >= press && t < press + 0.15);
  }
}
let FLY = { x: 0, y: 0 };

// ---------- measuring ----------
// Camera framings: [time, ids | 'app', max zoom, measure at]. The usable frame sits between the step chip and the caption.
const CAMS = [
  [0, 'app', 0.92], [T.appIn, 'app', 0.92],
  [T.s1 + 0.2, ['a-c1'], 1.45],
  [T.dlg1 + 0.05, ['a-dlg'], 1.4, T.dlg1 + 0.6],
  [T.installing + 0.05, ['a-c1'], 1.45],
  [T.flyCli - 0.1, ['a-c1', 'a-fly'], 1.3, T.flyCli + 0.5],
  [T.ready + 0.1, 'app', 0.95],
  [T.s2 - 0.3, ['a-c2'], 1.3],
  [T.prov + 0.05, 'app', 0.95],
  [T.exaPress - 0.5, ['a-li-routing', 'a-li-exa'], 1.35],
  [T.exa + 0.3, ['a-li-exa', 'a-exa-key'], 1.3, T.exa + 0.5],
  [T.keyPress - 0.3, ['a-exa-key'], 1.7, T.keyPress],
  [T.testPress - 1.2, ['a-exa-test', 'a-exa-st'], 1.6, T.testPress - 0.4],
  [T.testPress + 0.1, ['a-exa-test', 'a-fly'], 1.3, T.testPress + 0.5],   // widen so the notice shows whole
  [T.testDone, ['a-exa-st', 'a-exa-test'], 1.45, T.testDone + 0.2],
  [T.savePress - 0.8, ['a-pfs', 'a-pfv'], 1.25],
  [T.saved + 0.1, ['a-li-exa', 'a-fly'], 1.05, T.saved + 0.4],
  [T.flipX - 0.4, ['a-li-xai', 'a-li-exa'], 1.35, T.flipX + 0.1],
  [T.flipJ - 0.3, ['a-li-jina', 'a-li-firecrawl'], 1.35, T.flipJ + 0.2],
  [T.s3 + 0.1, 'app', 0.95],
  [T.rt + 0.2, ['a-rt-mode', 'a-rt-note'], 1.5, T.rt + 0.4],
  [T.rtKeyPress - 0.4, ['a-rt-key'], 1.7, T.rtKeyPress],
  [T.rtScroll + 0.3, ['a-rt-th', 'a-rt-suf'], 1.5, T.rtScroll + 0.8],
  [T.rtSavePress - 0.7, ['a-pfs', 'a-pfv'], 1.25],
  [T.rtSaved + 0.1, ['a-li-routing', 'a-fly'], 1.05, T.rtSaved + 0.4],
  [T.s4, 'app', 0.95],
  [T.sk + 0.7, ['a-sk2', 'a-sk6'], 1.35, T.sk + 1.3],
  [T.goPress - 0.7, ['a-skc', 'a-skgo'], 1.25],
  [T.dlg2 + 0.05, ['a-dlg'], 1.3, T.dlg2 + 0.6],
  [T.syncing + 0.1, ['a-sk0', 'a-skres'], 1.3, T.synced + 0.1],
  [T.s5, 'app', 0.95],
  [T.tour0 - 0.15, ['a-st-lang', 'a-st-look'], 1.45, T.tour0],
  [T.tour1 - 0.15, ['a-st-dir'], 1.5, T.tour1],
  [T.tour2 - 0.15, ['a-st-upd'], 1.4, T.tour2],
  [T.s6, 'app', 0.95],
  [T.done - 0.2, ['a-c2'], 1.35, T.done],
];
const HIGHLIGHTS = [
  [T.ready + 0.3, T.s2 - 0.3, ['a-dot'], 14],
  [T.note, T.note + 1.9, ['a-rt-note'], 10],
  [T.thr, T.thr + 2.4, ['a-rt-th', 'a-rt-suf'], 12, 56],
  [T.tour0, T.tour1 - 0.1, ['a-st-lang', 'a-st-look'], 14],
  [T.tour1, T.tour2 - 0.1, ['a-st-dir'], 14],
  [T.tour2, T.s6 - 0.3, ['a-st-upd'], 12],
  [T.done, T.end - 0.2, ['a-c2'], 10],
];
let CAM = [], CLK = [], HL = [];
function measure() {
  css($('cam'), { transform: 'none' }); css($('a'), { transform: 'none', opacity: '1' });
  vis($('world'), true);
  const page = (id) => rectOf(id);
  // Scroll distances, from the layout with nothing scrolled.
  applyApp(T.testPress - 2, true);
  const test = page('a-exa-test');
  SCROLL.exa = Math.max(0, test.y + test.h + 260 - (A.y + 48 + 78 + VIEW));   // room for the result lines
  applyApp(T.rtScroll - 0.1, true);
  const suf = page('a-rt-suf');
  SCROLL.rt = Math.max(0, suf.y + suf.h + 60 - (A.y + 48 + 78 + VIEW));
  applyApp(T.sk + 0.2, true);
  const res = page('a-sk6');
  SCROLL.sk = Math.max(0, res.y + res.h + 120 - (A.y + 48 + 78 + VIEW));
  applyApp(T.flipJ - 1, true);
  const jina = page('a-li-firecrawl');
  SCROLL.list = Math.max(0, jina.y + jina.h * 3 + 40 - (A.y + 48 + 78 + VIEW));
  // The flyout opens under the 操作提示 button, kept inside the window.
  const fb = rectOf('a-fb');
  FLY = { x: clamp(fb.x - A.x + fb.w / 2 - 260, 12, A.w - 532), y: fb.y - A.y + fb.h + 8 };
  CAM = CAMS.map(([t, ids, zMax, at]) => {
    if (ids === 'app') return [t, { cx: A.x + A.w / 2, cy: A.y + A.h / 2, z: zMax }];
    applyApp(at ?? t, true);
    return [t, framing(rectOf(ids), zMax)];
  });
  // Measured at the press, when the page under the pointer has settled.
  CLK = CLICKS.map(([arrive, id, press]) => { applyApp(press - 0.01, true); const r = rectOf(id); return { arrive, press, x: r.x + r.w / 2, y: r.y + r.h / 2 }; });
  HL = HIGHLIGHTS.map(([a, b, ids, pad, padTop]) => { applyApp(a + 0.3, true); const r = rectOf(ids); return { a, b, x: r.x - pad, y: r.y - (padTop ?? pad), w: r.w + 2 * pad, h: r.h + pad + (padTop ?? pad) }; });
}

// ---------- camera, pointer, guide ----------
const START = { x: A.x + 1150, y: A.y + 820 };
const CHEERS = [T.cheer1, T.cheer2, T.cheer3, T.cheer4, T.cheer6];
function guideAt(t) {
  if (t < T.appIn + 0.5) {
    // Title: hops in, lands on the title, waves; leaves as the App comes up.
    const j0 = 0.55, j1 = 0.95;
    if (t < j0) return null;
    if (t < j1) { const k = prog(t, j0, j1); return { x: lerp(2000, 560, k), y: lerp(240, 392, k) - 160 * hop(k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
    const d = t - j1, out = prog(t, T.appIn, T.appIn + 0.45);
    if (out > 0) return { x: lerp(560, 760, out), y: lerp(392, 1300, easeIn(out)) - 120 * hop(Math.min(1, out * 1.6)), sq: -0.1, pose: { eyes: 'happy', arms: 'up', legs: 'tuck' } };
    return { x: 560, y: 392, sq: 0.25 * Math.exp(-d * 9) * Math.cos(d * 22), land: j1, pose: { eyes: d < 0.3 ? 'shut' : 'happy', arms: Math.floor(d * 4) % 2 ? 'wave' : 'up', legs: 'stand' } };
  }
  if (t >= T.end) {
    // Lands on the 配好了！ label and waves.
    const j0 = T.end + 0.7, j1 = j0 + 0.35, r = END_LABEL, x = r.x + r.w - 90;
    if (t < j0) return null;
    if (t < j1) { const k = prog(t, j0, j1); return { x: lerp(2000, x, k), y: lerp(300, r.y, k) - 160 * hop(k), sq: -0.12, pose: { eyes: 'wide', arms: 'up', legs: 'tuck' } }; }
    const d = t - j1;
    return { x, y: r.y, sq: 0.28 * Math.exp(-d * 9) * Math.cos(d * 22), land: j1, pose: { eyes: d > 2.4 && d < 2.5 ? 'blink' : 'happy', arms: Math.floor(d * 3.5) % 2 ? 'wave' : 'down', legs: 'stand' } };
  }
  // Each finished step: Clawd pops up from the bottom-right corner.
  return cheerAt(t, CHEERS);
}
let END_LABEL = { x: 0, y: 0, w: 0 };

// ---------- render ----------
window.render = function (t) {
  const inApp = t >= T.appIn - 0.05 && t < T.end + 0.4;
  vis($('world'), inApp);
  vis($('title'), t < T.appIn + 0.6);
  vis($('endc'), t >= T.end);

  // Title card.
  if (t < T.appIn + 0.6) {
    const out = easeIn(prog(t, T.appIn - 0.1, T.appIn + 0.4));
    [['tKicker', 0.15, 330], ['tBig', 0.25, 380], ['tSub', 0.5, 560]].forEach(([id, t0, y]) => {
      const k = pop(t, t0, SPRING.card);
      css($(id), { left: '110px', top: `${y - 90 * out}px`, opacity: String(clamp(k * 1.5) * (1 - out)), transform: `translateY(${((1 - k) * 40).toFixed(1)}px)` });
    });
    // The five pages as a contents list on the right.
    [...$('toc').children].forEach((el, i) => {
      const k = pop(t, 0.7 + i * 0.12, SPRING.card);
      css(el, { opacity: String(clamp(k * 1.5) * (1 - out)), transform: `translateX(${((1 - k) * 60).toFixed(1)}px) translateY(${(-90 * out).toFixed(1)}px)` });
    });
  }

  // The App.
  if (inApp) {
    applyApp(t);
    const kIn = spring(t - T.appIn, ...SPRING.card);
    css($('a'), { transform: `translateY(${((1 - kIn) * 700).toFixed(1)}px)`, opacity: String(clamp(kIn * 3)) });
    const c = camAt(t, CAM);
    css($('cam'), { transform: `translate(${c.tx.toFixed(2)}px, ${c.ty.toFixed(2)}px) scale(${c.z.toFixed(4)})` });
    // Pointer and click ripple.
    const p = pointerAt(t, CLK, START, T.appIn + 0.4, T.end);
    vis($('cur'), !!p);
    if (p) css($('cur'), { transform: `translate(${(p.x - 2).toFixed(1)}px, ${(p.y - 2).toFixed(1)}px) scale(${p.down ? 0.88 : 1})`, transformOrigin: '2px 2px' });
    const cl = CLK.find(c => t >= c.press && t < c.press + 0.4);
    vis($('rip'), !!cl);
    if (cl) { const k = easeOut(prog(t, cl.press, cl.press + 0.4)), r = 10 + 34 * k; css($('rip'), { left: `${cl.x - r}px`, top: `${cl.y - r}px`, width: `${2 * r}px`, height: `${2 * r}px`, opacity: String(1 - k) }); }
    // Marker ring.
    marker($('hl'), t, HL);
  }

  // Step chip, fast-forward badge, captions.
  stepChip(t, STEPS, T.end);
  const ff = t >= T.flipX - 0.3 && t < T.flipJ + 0.7;
  css($('ff'), { opacity: ff ? '1' : '0', transform: `scale(${ff ? pop(t, T.flipX - 0.3, [22, 0.55]) : 0})` });
  capText($('cap'), t, CAPS);

  // End card.
  if (t >= T.end) {
    [['eBig', 0.0, 210], ['eL1', 0.3, 420], ['eCmd', 0.55, 520], ['eL2', 0.75, 640], ['eGh', 1.0, 760]].forEach(([id, d, y]) => {
      const k = pop(t, T.end + d, SPRING.card);
      css($(id), { left: '110px', top: `${y}px`, opacity: String(clamp(k * 1.5)), transform: `translateY(${((1 - k) * 40).toFixed(1)}px)` });
    });
    css($('eNote'), { opacity: String(clamp(pop(t, T.end + 1.2, SPRING.card))) });
    const km = pop(t, T.end + 0.9, SPRING.mascot);
    css($('eMascot'), { left: '1240px', top: `${lerp(1100, 470, km) + 6 * Math.sin((t - T.end) * 2.6)}px` });
  }

  // Guide.
  let fx = '';
  const g = guideAt(t);
  guide.draw(g);
  if (g && g.cheer !== undefined && t > g.cheer && t < g.cheer + 1) fx += sparkles(g.x, g.y, t, g.cheer);
  if (g && t >= T.end && t > T.end + 1.05 && t < T.end + 2.0) fx += sparkles(g.x, g.y, t, T.end + 1.05);
  html($('fx'), fx);
};

// ---------- setup ----------
const TEXT = document.body.textContent + CAPS.map(c => c[2]).join('') + STEPS.map(s => s.join('')).join('') + DLG1.body + DLG1.title + DLG2.body + DLG2.title
  + NOTICES.map(n => n[2] + n[3]).join('') + '处理中…正在检测本地环境…正在通过原管理器安装或更新 CLI…CLI 安装完成，正在重新连接。0.1.30 · 已就绪基础配置已完成，可以开始搜索。'
  + '测试中…用未保存的修改测试通过尚未测试正在等待服务商响应，请稍候。可在活动页取消。未保存修改的测试 · 2026-10-20 14:03:12此结果对应测试时尚未保存的修改；再次测试可确认当前配置。检查方式：真实请求技术详情⌄'
  + '有 1 2 项未保存修改 · 密钥留空会保留原值保存中…更新中…正在更新所选 Skills…已同步 4 个，失败 0 个。与来源一致已选择个 Agent已配置未配置 · 未保存••••••••⏩快进';
loadFonts([
  ['400 21px "Noto Sans SC"', TEXT], ['500 21px "Noto Sans SC"', TEXT], ['700 21px "Noto Sans SC"', TEXT], ['900 38px "Noto Sans SC"', TEXT],
  ['400 21px Inter', TEXT], ['600 21px Inter', TEXT], ['700 21px Inter', TEXT],
  ['400 21px "JetBrains Mono"', TEXT], ['700 21px "JetBrains Mono"', TEXT], ['400 60px "ZCOOL KuaiLe"', TEXT],
]).then(() => {
  measure();
  // Clawd ends standing on the 配好了！ label, which the end card places at (110, 210).
  vis($('endc'), true);
  css($('eBig'), { left: '110px', top: '210px' });
  END_LABEL = rectOf('eBigS');
  window.render(0);
  window.ready = true;
});
