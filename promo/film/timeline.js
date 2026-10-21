// One timetable for picture and sound. Pure data and functions: the page and tools/events.mjs both import it.
import { rnd, typing, typed } from '../shared/motion.js';
export { typing, typed };

export const DUR = 53;
export const BPM = 120;
export const BEAT = 60 / BPM;      // 0.5 s
export const BAR = 4 * BEAT;       // 2 s

export const T = {
  // S1 the question (single screen, smooth)
  type0: 0.3, enter: 1.9, ws: 2.25,
  // S2 stuck: the world drops to 8 fps and loses its colour
  stuck: 4.0, fetch: 4.9, summary: 5.9, oldLens: 6.5,
  // S3 split and install
  split: 8.0, rIn: 8.2, install: 8.75, setup: 9.75, skill: 10.25, upgrade: 10.5, ready: 11.0, go: 11.55, clear: 11.3,
  // round 1: Jev routing (candidates scored by Noul, sorted, the top one dispatched)
  route: 12.0, search: 12.3, jevOpen: 12.75, bars: 13.25, sort: 14.9, pick: 15.5,
  // round 2: search
  r1: 18.0, results: 18.25, lift: 18.8, hopR1: 19.8, lensR1: 20.6,
  // round 3: read the original
  r2: 24.0, fetchR: 24.2, expand: 24.5, toLine: 25.35, walk0: 25.75, walk1: 27.3, cite: 28.1, gloss: 28.4,
  // round 4: answer
  r3: 30.0, answer: 30.35, answerL: 30.6, stampR: 32.5, stampL: 33.3,
  // S7 merge
  merge: 36.0, peek: 36.6, jump: 37.0, land: 37.6, tear: 37.7, cheer: 38.4,
  // S8 montage and S9 end card
  montage: 40.0, cutB: 43.0, cutC: 45.5, end: 48.0,
};

export const PROMPT = '查 React 当前文档里 useEffect 的清理规则，读相关页面，并给出来源。';
export const INSTALL = 'npm install -g @konbakuyomu/smart-search';
export const SETUP = 'smart-search setup --non-interactive --install-skills claude';
export const QUESTION = 'useEffect 的清理函数什么时候执行？';
export const ANSWER_R = '依赖变化后的每次 commit，React 先用旧值运行清理函数，再用新值运行 setup；组件从 DOM 移除时也会运行一次清理。[1][2]';
export const ANSWER_L = '搜索暂不可用，我先凭记忆回答：每次 re-render 之后，React 会先执行清理……吧？';
export const QUOTE = 'After every commit with changed dependencies, React will first run the cleanup function (if you provided it) with the old values, and then run your setup function with the new values.';
export const QUOTE_HI = 'After every commit with changed dependencies, React will first run the cleanup function';
export const SOURCES = [
  ['useEffect – React', 'https://react.dev/reference/react/useEffect'],
  ['Synchronizing with Effects – React', 'https://react.dev/learn/synchronizing-with-effects'],
  ['Lifecycle of Reactive Effects – React', 'https://react.dev/learn/lifecycle-of-reactive-effects'],
];
// Candidate operations for round 1, in the order the program lists them, with illustrative Noul probabilities.
export const ROUTES = [
  { name: 'Tavily', cap: '网页搜索', p: 0.42 },
  { name: 'Context7', cap: '文档检索', p: 0.71 },
  { name: 'xAI', cap: '主搜索', p: 0.35 },
  { name: 'Exa', cap: '文档检索', p: 0.86 },
  { name: '智谱', cap: '网页搜索', p: 0.18 },
];
// The research cut: actions and Jev's judgments between rounds (judgments are styled differently).
export const RESEARCH = [
  { text: '第 1 轮：Exa + Context7 并发', judge: false },
  { text: 'Jev：只有摘要，要读原文', judge: true },
  { text: '第 2 轮：读原网页', judge: false },
  { text: 'Jev：证据够了 ✓ 只引用读过的正文', judge: true },
];
export const nodeT = i => T.montage + 0.4 + i * 0.55;
export const AGENTS = ['Codex', 'Claude Code', 'Cursor', 'OpenCode', 'GitHub Copilot', 'Gemini CLI', 'Cline', 'Roo Code', 'Kiro',
  'Qoder', 'CodeBuddy', 'Factory Droid', 'Pi Agent', 'Kilo CLI', 'Antigravity', 'Windsurf', 'Hermes Agent'];

export const TYPE = {
  prompt: typing(PROMPT, T.type0, 24, 1),
  install: typing(INSTALL, T.install, 46, 2),
  setup: typing(SETUP, T.setup, 120, 3),
  answerR: typing(ANSWER_R, T.answer, 42, 4),
  // The built-in side types in 8 fps chunks.
  answerL: typing(ANSWER_L, T.answerL, 16, 5).map(x => Math.ceil(x * 8) / 8),
};

// Sound cues: [time, type, pan (-1 left … 1 right), gain]. sound.py turns each type into a synthesized sound.
export function events() {
  const ev = [];
  const add = (t, type, pan = 0, gain = 1) => ev.push({ t: +t.toFixed(4), type, pan, gain });
  TYPE.prompt.forEach((t, i) => add(t, 'key', -0.1 + 0.2 * rnd(i), 0.7));
  add(T.enter, 'enter');
  add(T.ws, 'blip', 0, 0.6);
  // Stuck: tape stop, then spinner ticks in 8 fps steps on the left.
  add(T.stuck, 'tapestop');
  for (let t = T.stuck + 0.25; t < T.split; t += 0.5) add(t, 'tick', -0.4, 0.35);
  add(T.fetch, 'blip', -0.2, 0.5);
  add(T.summary, 'thud', -0.2, 0.8);
  add(T.oldLens, 'squeak', -0.2, 0.7);
  add(T.oldLens + 0.6, 'sad', -0.2, 0.6);
  // Split and install.
  add(T.split, 'rip', 0, 1);
  add(T.rIn + 0.4, 'boing', 0.5, 0.8);
  TYPE.install.forEach((t, i) => add(t, 'key', 0.5, 0.55));
  TYPE.setup.forEach((t, i) => { if (i % 3 === 0) add(t, 'key', 0.5, 0.45); });
  add(T.skill, 'pop', 0.5, 0.9);
  add(T.upgrade, 'upgrade', 0.4, 1);
  add(T.ready, 'pop', 0, 0.8);
  add(T.go, 'pop', 0, 1);
  for (let t = T.split + 0.5; t < T.r3 + 4; t += 1.0) add(t, 'tick', -0.6, 0.25);
  // Round 1: routing.
  add(T.route, 'slam', 0, 1);
  add(T.search, 'blip', 0.5, 0.6);
  add(T.jevOpen, 'whoosh', 0.5, 0.6);
  add(T.jevOpen + 0.05, 'pop', 0.5, 0.8);
  add(T.jevOpen + 0.35, 'boing', 0.5, 0.7);
  add(T.jevOpen + 0.75, 'land', 0.5, 0.6);
  ROUTES.forEach((r, i) => add(T.bars + i * 0.22 + 0.32, 'meter', 0.5, 0.35 + 0.5 * r.p));
  add(T.sort, 'whoosh', 0.5, 0.45);
  add(T.pick, 'select', 0.5, 1);
  add(T.r1, 'boing', 0.5, 0.6);
  add(T.r1 + 0.5, 'land', 0.5, 0.5);
  // Round 2: search.
  add(T.r1, 'slam', 0, 1);
  add(T.results, 'stream', 0.5, 0.6);
  [0, 1, 2].forEach(i => add(T.lift + i * 0.14, 'pop', 0.5, 0.75 + 0.1 * i));
  add(T.lift + 0.1, 'whoosh', 0.5, 0.7);
  add(T.hopR1 - 0.15, 'boing', 0.5, 0.8);
  add(T.hopR1 + 0.42, 'land', 0.5, 0.8);
  add(T.lensR1, 'ching', 0.5, 0.9);
  // Round 3: read.
  add(T.r2, 'slam', 0, 1);
  add(T.fetchR, 'blip', 0.5, 0.6);
  add(T.expand, 'whoosh', 0.5, 0.8);
  add(T.toLine, 'boing', 0.5, 0.7);
  add(T.toLine + 0.36, 'land', 0.5, 0.7);
  for (let t = T.walk0; t < T.walk1; t += 0.25) add(t, 'step', 0.5, 0.4);
  add(T.walk0, 'marker', 0.5, 0.8);
  add(T.cite, 'pop', 0.5, 1);
  add(T.gloss, 'chime', 0.5, 0.5);
  add(T.r2 + 0.6, 'sad', -0.6, 0.5);
  // Round 4: answer.
  add(T.r3, 'slam', 0, 1);
  add(T.answer, 'stream', 0.5, 0.9);
  TYPE.answerL.forEach((t, i) => { if (i % 4 === 0) add(t, 'key', -0.6, 0.4); });
  add(T.stampR, 'stamp', 0.5, 1);
  add(T.stampR + 0.12, 'success', 0.5, 0.8);
  add(T.stampL, 'stamp', -0.5, 1);
  add(T.stampL + 0.1, 'buzz', -0.5, 0.7);
  // Merge.
  for (let t = T.merge; t < T.peek; t += 0.25) add(t, 'step', -0.5, 0.45);
  add(T.jump, 'boing', -0.2, 0.9);
  add((T.jump + T.land) / 2, 'upgrade', 0, 0.8);
  add(T.land, 'land', 0.2, 0.8);
  add(T.tear, 'rip', -0.4, 1);
  add(T.tear + 0.25, 'whoosh', -0.5, 0.9);
  add(T.cheer, 'success', 0, 0.9);
  // Montage cuts and end card.
  [T.montage, T.cutB, T.cutC].forEach(t => add(t, 'whoosh', 0, 0.9));
  RESEARCH.forEach((_, i) => add(nodeT(i), i === 3 ? 'success' : 'pop', 0, 0.6));
  [0, 1, 2].forEach(i => add(T.cutB + 0.45 + i * 0.3, 'tickok', 0, 0.8));
  add(T.cutB + 1.45, 'pop', 0.2, 0.7);   // the Exa test pill turns 通过
  AGENTS.forEach((_, i) => add(T.cutC + 0.3 + i * 0.055, 'tickok', -0.6 + 1.2 * (i % 6) / 5, 0.35));
  add(T.end - 1.6, 'riser', 0, 1);
  add(T.end, 'impact', 0, 1);
  add(T.end + 0.25, 'sparkle', 0.2, 0.8);
  add(T.end + 0.8, 'land', 0, 0.7);
  add(T.end + 1.0, 'peek', 0.4, 0.7);
  add(T.end + 3.0, 'sparkle', 0.4, 0.5);
  return ev.sort((a, b) => a.t - b.t);
}
