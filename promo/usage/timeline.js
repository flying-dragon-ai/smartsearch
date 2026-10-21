// 日常使用: one timetable for picture and sound, read by usage.js and tools/events.mjs.
import { typing } from '../shared/motion.js';

export const DUR = 62;
export const BPM = 96;

export const T = {
  title: 0.2,
  // 1 在 AI 里直接问 (an agent terminal)
  s1: 2.6, type0: 3.2, tips: 5.2, enter: 7.2, bash1: 7.5, res1: 8.2, fetch1: 9.0, fres1: 9.7, answer: 10.1, alt: 13.8, s1end: 15.8,
  // 2 搜索与研究: 搜索
  s2: 16.2, navPress: 17.5, page: 17.65, qPress: 18.7, qType: 18.9, runPress: 21.0, busy: 21.15, done: 23.0, copyPress: 25.0, copied: 25.15,
  // 3 搜索与研究: 在线研究
  s3: 27.4, toolPress: 28.1, popScroll: 28.6, optPress: 30.0, q2Press: 30.9, q2Type: 31.1, run2Press: 33.3, busy2: 33.45, seePress: 34.7,
  // 4 活动
  s4: 34.85, rowPress1: 36.3, rowPress2: 38.5, s4end: 40.6,
  // 5 命令行
  s5: 41.0, c0: 41.6, c1: 43.2, c2: 44.8, c3: 46.4, s5end: 49.6,
  // 6 关掉 App 也能用
  s6: 50.0, closePress: 50.9, dlg: 51.05, bgPress: 52.7, gone: 52.85, type1: 54.0, bash2: 55.8, res2: 56.5,
  end: 58.0,
};

export const STEPS = [
  [T.s1, '1', '在 AI 里直接问', 'Codex、Claude Code、Cursor…'],
  [T.s2, '2', '搜索与研究', '在 App 里搜'],
  [T.s3, '3', '在线研究', '难题交给它'],
  [T.s4, '4', '活动', '看进度和服务商'],
  [T.s5, '5', '命令行', '四个常用命令'],
  [T.s6, '6', '关掉 App', 'AI 照样能用'],
];

export const PROMPT = '用 Smart Search 查 React 当前文档里 useEffect 的清理规则，读相关页面，并给出来源。';
export const PROMPT_HI = ['用 Smart Search', '读相关页面', '给出来源'];
export const ALT = '用 Smart Search 核对这篇文章里的说法：https://example.com/article';
export const PROMPT2 = '再查一下 useEffect 和 useLayoutEffect 的区别，给出来源。';
export const ANSWER = '依赖变化后的每次 commit，React 先用旧值运行清理函数，再用新值运行 setup；组件从 DOM 移除时也会运行一次清理。[1][2]';
export const SOURCES = [
  ['useEffect – React', 'https://react.dev/reference/react/useEffect'],
  ['Synchronizing with Effects – React', 'https://react.dev/learn/synchronizing-with-effects'],
];
// What the App shows for a Jev-routed search that Exa answered: evidence excerpts, the evidence line, then 来源
// (cli._format_markdown and jev_search._evidence_content). The excerpts are the pages' own words.
export const RESULT = `[e1] useEffect – React
Source: https://react.dev/reference/react/useEffect
After every commit with changed dependencies, React will first run the cleanup function (if you provided it) with the old values…

[e2] Synchronizing with Effects – React
Source: https://react.dev/learn/synchronizing-with-effects
React will call your cleanup function each time before the Effect runs again, and one final time when the component unmounts…

证据：not_evaluated

## 来源
- [useEffect – React](https://react.dev/reference/react/useEffect)
- [Synchronizing with Effects – React](https://react.dev/learn/synchronizing-with-effects)`;
export const Q1 = 'useEffect 清理函数什么时候执行';
export const Q2 = 'React 状态管理方案对比';

export const CHEAT = [
  ['smart-search search "useEffect 清理规则" --format markdown', '普通搜索：Jev 选一个渠道，返回结果和来源'],
  ['smart-search fetch "https://react.dev/reference/react/useEffect" --format markdown', '读原网页，拿回干净正文'],
  ['smart-search research "React 状态管理方案对比" --budget standard', '在线研究：多轮检索、读正文，Jev 判断证据够不够'],
  ['smart-search route "useEffect 清理规则"', '只在本地预览选路，不联网；加 --remote 才调用 Jev'],
];

// Cursor clicks in the App: [arrive, target id, press time].
export const CLICKS = [
  [17.1, 'a-n-search', T.navPress],
  [18.3, 'a-q', T.qPress],
  [20.6, 'a-run', T.runPress],
  [24.6, 'a-copy', T.copyPress],
  [27.75, 'a-tool', T.toolPress],
  [29.6, 'a-opt24', T.optPress],
  [30.55, 'a-q', T.q2Press],
  [32.9, 'a-run', T.run2Press],
  [34.35, 'a-seeact', T.seePress],
  [35.9, 'a-ar-res', T.rowPress1],
  [38.1, 'a-ar-ai', T.rowPress2],
  [50.5, 'a-close', T.closePress],
  [52.3, 'a-dlgok', T.bgPress],
];

export const DLG = { title: '仍有 Smart Search 任务在运行', ok: '继续在后台', second: '取消任务并退出', cancel: '返回',
  body: '继续后台运行可从通知区域恢复；取消任务并退出只会取消本 App 发起的任务，不会终止外部 CLI。' };
export const NOTICES = [[T.copied, T.copied + 1.8, '已复制', '已复制当前可读结果。']];

export const CAPS = [
  [T.s1 + 0.3, T.tips - 0.2, '平时直接跟 AI 说：<b>用 Smart Search 查…</b>'],
  [T.tips - 0.1, T.enter, '说清三件事：用它查、读原页、给来源'],
  [T.enter + 0.1, T.answer, 'AI 会先搜索，再读原网页'],
  [T.answer + 0.2, T.alt - 0.1, '回答里带上<b>来源</b>，点开就能核对'],
  [T.alt, T.s2 - 0.2, '核对一篇文章，也是一句话'],
  [T.s2 + 0.3, T.qType, 'App 里也能搜：打开<b>搜索与研究</b>'],
  [T.qType, T.busy, '工具选「搜索」，填问题'],
  [T.busy + 0.1, T.done, '任务在后台跑，可以去「活动」看进度'],
  [T.done + 0.1, T.copyPress - 0.1, '结果和<b>来源</b>一起给，原网页地址都在'],
  [T.copyPress, T.s3 - 0.2, '可以复制或导出'],
  [T.s3 + 0.2, T.optPress + 0.2, '难一点的问题：选<b>在线研究</b>'],
  [T.optPress + 0.3, T.run2Press, '拆子问题、读正文，Jev 判断证据够不够'],
  [T.run2Press + 0.1, T.s4, '研究要多跑一会儿'],
  [T.s4 + 0.2, T.rowPress2, '<b>活动</b>：每个任务的阶段和服务商'],
  [T.rowPress2 + 0.1, T.s5 - 0.2, 'AI 在终端里跑的搜索，也记在这里'],
  [T.s5 + 0.2, T.s6 - 0.2, '在终端里，四个命令就够用'],
  [T.s6 + 0.2, T.gone, '关掉 App：任务可以留在后台'],
  [T.gone + 0.2, T.end - 0.2, 'App 关了，AI 照样调用 CLI'],
];

export const TYPE = {
  prompt: typing(PROMPT, T.type0, 26, 11),
  answer: typing(ANSWER, T.answer, 44, 12),
  q1: typing(Q1, T.qType, 18, 13),
  q2: typing(Q2, T.q2Type, 16, 14),
  prompt2: typing(PROMPT2, T.type1, 28, 15),
  cheat: [T.c0, T.c1, T.c2, T.c3].map((t, i) => typing(CHEAT[i][0], t, 60, 20 + i)),
};

export function events() {
  const ev = [];
  const add = (t, type, pan = 0, gain = 1) => ev.push({ t: +t.toFixed(4), type, pan, gain });
  add(T.title + 0.1, 'whoosh', 0, 0.6); add(T.title + 0.3, 'pop', 0, 0.8);
  STEPS.forEach(([t]) => add(t, 'whoosh', 0, 0.4));
  TYPE.prompt.forEach((t, i) => { if (i % 2 === 0) add(t, 'key', -0.1, 0.5); });
  add(T.enter, 'enter', 0, 0.8);
  [T.bash1, T.fetch1].forEach(t => add(t, 'blip', 0.2, 0.5));
  [T.res1, T.fres1].forEach(t => add(t, 'stream', 0.2, 0.5));
  add(T.answer, 'stream', 0, 0.7);
  add(TYPE.answer[TYPE.answer.length - 1] + 0.3, 'success', 0, 0.7);
  PROMPT_HI.forEach((_, i) => add(T.tips + i * 0.5, 'marker', 0, 0.35));
  add(T.alt, 'pop', 0, 0.7);
  add(T.s2, 'whoosh', 0, 0.8);
  for (const [, , press] of CLICKS) add(press, 'click', 0, 0.7);
  [...TYPE.q1, ...TYPE.q2, ...TYPE.prompt2].forEach((t, i) => { if (i % 2 === 0) add(t, 'key', 0, 0.5); });
  for (let t = T.busy + 0.3; t < T.done; t += 0.5) add(t, 'tick', 0.2, 0.22);
  add(T.done, 'success', 0, 0.7);
  for (const [t0] of NOTICES) add(t0, 'chime', 0.3, 0.6);
  add(T.toolPress + 0.1, 'pop', 0, 0.5);
  add(T.dlg, 'pop', 0, 0.6);
  TYPE.cheat.forEach(times => times.forEach((t, i) => { if (i % 3 === 0) add(t, 'key', 0, 0.4); }));
  [T.c0, T.c1, T.c2, T.c3].forEach(t => add(t + 1.0, 'tickok', 0, 0.6));
  add(T.gone, 'whoosh', 0.4, 0.7);
  add(T.bash2, 'blip', 0.2, 0.5); add(T.res2, 'stream', 0.2, 0.5);
  add(T.end, 'whoosh', 0, 0.8); add(T.end + 0.2, 'impact', 0, 0.7); add(T.end + 0.5, 'sparkle', 0.2, 0.7);
  return ev.sort((a, b) => a.t - b.t);
}
