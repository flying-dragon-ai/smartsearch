// 配置教程: one timetable for picture and sound, read by config.js and tools/events.mjs.
import { typing } from '../shared/motion.js';

export const DUR = 69;
export const BPM = 96;

export const T = {
  title: 0.2, appIn: 2.4,
  // 1 概览: install the CLI
  s1: 3.4, c1Press: 5.0, dlg1: 5.15, dlg1Press: 6.9, installing: 7.05, flyCli: 9.4, ready: 10.9, cheer1: 11.6,
  // 2 服务商: one provider in full, two more fast-forwarded
  s2: 13.2, c2Press: 14.0, prov: 14.15, exaPress: 15.3, exa: 15.45, keyPress: 16.6, type0: 16.8, testPress: 19.6, testDone: 21.8,
  savePress: 23.4, saved: 23.9, flipX: 25.6, flipJ: 26.2, cheer2: 26.9,
  // 3 意图路由: the TypeSafe key turns on Jev routing
  s3: 28.6, rtPress: 29.4, rt: 29.55, note: 30.6, rtKeyPress: 32.6, rtType: 32.8, rtScroll: 34.8, thr: 35.6, rtSavePress: 38.2, rtSaved: 38.7, cheer3: 39.6,
  // 4 更新 Skills
  s4: 41.4, skPress: 42.2, sk: 42.35, gemPress: 43.8, goPress: 45.2, dlg2: 45.35, dlg2Press: 47.4, syncing: 47.55, synced: 49.6, cheer4: 50.3,
  // 5 设置与关于
  s5: 52.0, stPress: 52.8, st: 52.95, tour0: 53.8, tour1: 55.0, tour2: 56.2,
  // back to 概览: basic configuration complete
  s6: 58.0, ovPress: 58.8, ov: 58.95, done: 59.8, cheer6: 60.6,
  end: 64.0,
};

// Chapters for the step chip.
export const STEPS = [
  [T.s1, '1', '概览', '安装 CLI'],
  [T.s2, '2', '服务商', '填 Key → 测试 → 保存'],
  [T.s3, '3', '意图路由', '打开 Jev 选路'],
  [T.s4, '4', '更新 Skills', '接入你的 AI 工具'],
  [T.s5, '5', '设置与关于', '语言、外观、配置目录'],
  [T.s6, '✓', '概览', '基础配置完成'],
];

// Cursor: [arrive, target id, press time | null]. Targets are measured from the App at that moment.
export const CLICKS = [
  [4.55, 'a-c1b', T.c1Press],
  [6.45, 'a-dlgok', T.dlg1Press],
  [13.6, 'a-c2b', T.c2Press],
  [14.9, 'a-li-exa', T.exaPress],
  [16.2, 'a-exa-key', T.keyPress],
  [19.15, 'a-exa-test', T.testPress],
  [22.95, 'a-pfv', T.savePress],
  [29.0, 'a-li-routing', T.rtPress],
  [32.2, 'a-rt-key', T.rtKeyPress],
  [37.8, 'a-pfv', T.rtSavePress],
  [41.8, 'a-n-skills', T.skPress],
  [43.35, 'a-skt5', T.gemPress],
  [44.75, 'a-skgo', T.goPress],
  [46.95, 'a-dlgok', T.dlg2Press],
  [52.4, 'a-n-settings', T.stPress],
  [58.4, 'a-n-overview', T.ovPress],
];

export const DLG1 = { title: '安装或更新独立 CLI？', ok: '继续',
  body: 'Windows · C:\\Users\\me\\AppData\\Roaming\\npm\nCLI 最新版本：0.1.30\n\n只处理所选 CLI；配置和 Skills 保留。App 自身不会更新。' };
const SKILL_DIRS = [['Codex', '.agents'], ['Claude Code', '.claude'], ['Cursor', '.cursor'], ['Gemini CLI', '.gemini']];
export const DLG2 = { title: '更新所选 Skills', ok: '备份并更新',
  body: '来源版本：0.1.30\n' + SKILL_DIRS.map(([n, d]) => `${n}\nC:\\Users\\me\\${d}\\skills\\smart-search`).join('\n\n') + '\n将同步所选目标的托管文件；不同内容先备份，额外文件保留。' };

// Notices open the 操作提示 flyout: [from, to, title, message]. The App clears the install notice once it reconnects.
export const NOTICES = [
  [T.flyCli, T.ready, '独立 CLI', 'CLI 安装完成，正在重新连接。'],
  [T.testPress + 0.15, T.testDone - 0.2, '正在测试未保存的修改', '这次测试不会保存配置。结果会显示在对应服务商下方。'],
  [T.saved, T.saved + 1.6, '已保存', '新配置会用于下一次任务；已经开始的任务继续使用它自己的配置快照。'],
  [T.rtSaved, T.rtSaved + 1.5, '已保存', '新配置会用于下一次任务；已经开始的任务继续使用它自己的配置快照。'],
];

// Captions: [from, to, html].
export const CAPS = [
  [T.s1 + 0.4, T.dlg1, '第一步：在<b>概览</b>里一键安装 CLI'],
  [T.dlg1 + 0.2, T.installing, '只装 CLI，配置和 Skills 都保留'],
  [T.installing + 0.2, T.ready, '用本机的 npm 安装，装完自动连接'],
  [T.ready + 0.1, T.s2 - 0.2, '显示<b>已就绪</b>，左下角亮绿灯'],
  [T.s2 + 0.2, T.exaPress, '<b>服务商</b>：每类能力选一个'],
  [T.exaPress + 0.2, T.type0, '比如文档检索选 <b>Exa</b>'],
  [T.type0, T.testPress - 0.3, '粘贴你自己的 <b>API Key</b>'],
  [T.testPress - 0.2, T.testDone + 0.3, '先<b>测试</b>：会发一次真实请求'],
  [T.testDone + 0.4, T.flipX - 0.2, '测试通过，再<b>保存更改</b>'],
  [T.flipX - 0.1, T.s3 - 0.2, '主搜索、网页抓取照做一遍'],
  [T.s3 + 0.2, T.note, '<b>意图路由</b>默认是 Jev 语义路由'],
  [T.note, T.rtType - 0.2, '普通搜索选一次路，深入搜索按缺口继续'],
  [T.rtType - 0.1, T.rtScroll, '填 <b>TypeSafe Key</b>，Jev 就会来选渠道'],
  [T.rtScroll + 0.2, T.rtSavePress - 0.3, '阈值都有默认值，一般不用改'],
  [T.rtSavePress - 0.2, T.s4 - 0.2, '不填 Key 也能用：按本地规则选路'],
  [T.s4 + 0.2, T.goPress - 0.3, '<b>更新 Skills</b>：勾选你用的 AI 工具'],
  [T.goPress - 0.2, T.synced, '内容不同会先备份，个人修改保留'],
  [T.synced + 0.1, T.s5 - 0.2, '同步好了，重新打开 Agent 会话'],
  [T.s5 + 0.2, T.tour1, '<b>设置与关于</b>：界面语言、外观'],
  [T.tour1, T.tour2, '配置都存在这个目录里'],
  [T.tour2, T.s6 - 0.2, 'App 更新：确认后才下载'],
  [T.s6 + 0.2, T.end - 0.3, '回到概览：<b>基础配置已完成</b>'],
];

export const EXA_KEY = '•'.repeat(28);
export const TYPE = {
  exa: typing('x'.repeat(28), T.type0, 30, 7),
  rt: typing('x'.repeat(28), T.rtType, 30, 8),
};

export function events() {
  const ev = [];
  const add = (t, type, pan = 0, gain = 1) => ev.push({ t: +t.toFixed(4), type, pan, gain });
  add(T.title + 0.1, 'whoosh', 0, 0.6);
  add(T.title + 0.3, 'pop', 0, 0.8);
  add(T.appIn, 'whoosh', 0, 0.8);
  for (const [, , press] of CLICKS) add(press, 'click', 0, 0.7);
  STEPS.forEach(([t]) => add(t, 'whoosh', 0, 0.4));
  add(T.dlg1, 'pop', 0, 0.6); add(T.dlg2, 'pop', 0, 0.6);
  for (let t = T.installing + 0.3; t < T.flyCli - 0.2; t += 0.5) add(t, 'tick', 0.2, 0.25);
  for (const [t0] of NOTICES) add(t0, 'chime', 0.3, 0.6);
  add(T.ready, 'success', 0, 0.8);
  [...TYPE.exa, ...TYPE.rt].forEach((t, i) => { if (i % 2 === 0) add(t, 'key', 0, 0.5); });
  add(T.testDone, 'success', 0, 0.7);
  [T.flipX, T.flipJ].forEach(t => add(t, 'tickok', 0, 0.8));
  add(T.note, 'marker', 0, 0.5);
  add(T.thr, 'marker', 0, 0.5);
  for (let t = T.syncing + 0.3; t < T.synced - 0.2; t += 0.5) add(t, 'tick', 0.2, 0.25);
  add(T.synced, 'success', 0, 0.8);
  [T.tour0, T.tour1, T.tour2].forEach(t => add(t, 'marker', 0, 0.4));
  add(T.done, 'success', 0, 0.9);
  [T.cheer1, T.cheer2, T.cheer3, T.cheer4, T.cheer6].forEach(t => { add(t, 'boing', 0.5, 0.6); add(t + 0.45, 'land', 0.5, 0.5); });
  add(T.end, 'whoosh', 0, 0.8);
  add(T.end + 0.2, 'impact', 0, 0.7);
  add(T.end + 0.5, 'sparkle', 0.2, 0.7);
  return ev.sort((a, b) => a.t - b.t);
}
