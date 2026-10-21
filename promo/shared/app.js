// The Smart Search Windows App (WinUI 3) as markup for the films, with the page structure and zh-CN strings
// of desktop/windows/*.cs and src/smart_search/ui_metadata.py. Pages are static; films change them through ids.
const svg = (d, w = 24, sw = 1.6) => `<svg width="${w}" height="${w}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="${sw}" stroke-linecap="round" stroke-linejoin="round">${d}</svg>`;
const teeth = [...Array(8)].map((_, i) => { const a = i * Math.PI / 4, c = Math.cos(a), s = Math.sin(a); return `M${(12 + 6.6 * c).toFixed(2)} ${(12 + 6.6 * s).toFixed(2)}L${(12 + 9 * c).toFixed(2)} ${(12 + 9 * s).toFixed(2)}`; }).join('');
export const ICON = {
  burger: svg('<path d="M4 7h16M4 12h16M4 17h16"/>'),
  home: svg('<path d="M4.5 10.2 12 4l7.5 6.2V20h-5v-5.5h-5V20h-5z"/>'),
  person: svg('<circle cx="12" cy="8.2" r="3.8"/><path d="M4.8 20c.9-3.7 3.7-5.6 7.2-5.6s6.3 1.9 7.2 5.6"/>'),
  search: svg('<circle cx="10.5" cy="10.5" r="6.2"/><path d="m15.2 15.2 5 5"/>'),
  list: svg('<path d="M4 6.5h2M4 12h2M4 17.5h2M9.5 6.5H20M9.5 12H20M9.5 17.5H20"/>'),
  skills: svg('<path d="M5 6.5 10.5 12 5 17.5M12.5 18h6.5"/>'),
  gear: svg(`<circle cx="12" cy="12" r="3"/><circle cx="12" cy="12" r="6.6"/><path d="${teeth}"/>`),
  msg: svg('<path d="M5 5.5h14v10H11l-4.5 3.5v-3.5H5z"/><path d="M8.5 9.5h7M8.5 12h5"/>', 26),
  refresh: svg('<path d="M18.5 12a6.5 6.5 0 1 1-1.9-4.6"/><path d="M18.5 4.5v4h-4"/>', 26),
  min: svg('<path d="M7 12h10"/>', 20, 1.2),
  max: svg('<rect x="7" y="7" width="10" height="10" rx="1.2"/>', 20, 1.2),
  close: svg('<path d="M7 7l10 10M17 7 7 17"/>', 20, 1.2),
  chevron: svg('<path d="m7 10 5 5 5-5"/>', 20),
  find: svg('<circle cx="10.5" cy="10.5" r="6.2"/><path d="m15.2 15.2 5 5"/>', 60, 1.2),
};
// Windows arrow pointer, 34 × 50.
export const CURSOR = `<svg width="34" height="50" viewBox="0 0 17 25"><path d="M1 1v19.5l4.6-4.3 2.9 6.9 3-1.3-2.8-6.6h6.3z" fill="#fff" stroke="#111" stroke-width="1.2" stroke-linejoin="round"/></svg>`;

export const NAV = [['overview', '概览', 'home'], ['providers', '服务商', 'person'], ['search', '搜索与研究', 'search'],
  ['activity', '活动', 'list'], ['skills', '更新 Skills', 'skills'], ['settings', '设置与关于', 'gear']];
export const PAGE_NAME = Object.fromEntries(NAV.map(([k, n]) => [k, n]));

const btn = (id, text, cls = '', style = '') => `<span class="ss-btn ${cls}" id="${id}"${style ? ` style="${style}"` : ''}>${text}</span>`;
const capRow = (p, i, name) => `<div id="${p}-r${i}"><div class="ss-divline"></div><div class="ss-row"><div class="ss-grow"><div class="ss-b">${name}</div><div class="ss-sub" id="${p}-r${i}d">选择一个服务商开始配置。</div></div><span class="ss-link" id="${p}-r${i}s">未配置</span></div></div>`;
const step = (p, n, title, sub, acts) => `<div class="ss-row"><div class="ss-grow ss-stack s8"><div class="ss-h2">${title}</div><div class="ss-sub" id="${p}-c${n}s">${sub}</div></div><div class="ss-acts">${acts}</div></div>`;

function overview(p) {
  return `<div class="ss-scroll ss-stack" id="${p}-ovs">
  <div class="ss-stack s8"><div class="ss-h1">概览</div><div class="ss-sub">配置、运行与结果，都在这台电脑上管理。</div></div>
  <div class="ss-card" id="${p}-c1">${step(p, 1, '1. 准备本地环境', 'Node.js/npm 已就绪，等待准备 Smart Search CLI',
    btn(`${p}-c1b`, '安装 CLI', 'pri') + btn(`${p}-c1r`, '重新检测') + btn(`${p}-c1d`, '环境详情…') + `<span class="ss-link" id="${p}-c1m" style="align-self:center">手动下载 CLI</span>` + btn(`${p}-c1x`, '选择已有 CLI…'))}
    <div class="ss-sub" id="${p}-c1e" style="margin-top:14px">App 通过本机独立安装的 Smart Search CLI 读取配置并运行搜索，两者分别安装和更新。检测会复用已有的 mise 或 npm 安装。</div>
    <div class="ss-prog" id="${p}-c1p" style="margin-top:16px; display:none"><i></i></div>
    <div class="ss-sub" id="${p}-c1g" style="margin-top:14px; display:none"></div></div>
  <div class="ss-card" id="${p}-c2">${step(p, 2, '2. 配置服务商', '选择搜索服务，填写 API Key。', btn(`${p}-c2b`, '配置服务商') + btn(`${p}-c2go`, '开始搜索', 'pri', 'display:none'))}
    ${capRow(p, 0, '主搜索')}${capRow(p, 1, '文档检索')}${capRow(p, 2, '网页抓取')}
    <div class="ss-row" id="${p}-c2f" style="margin-top:20px"><span class="ss-btn">更多能力 ${ICON.chevron}</span><span class="ss-grow"></span><span class="ss-btn">配置详情…</span></div></div>
  <div class="ss-card" id="${p}-c3">${step(p, 3, '3. 测试连接', '在服务商页面点击“测试”，确认地址和密钥可用后开始搜索。', btn(`${p}-c3b`, '去测试服务商'))}</div>
  <div class="ss-card" id="${p}-c4">${step(p, 4, '4. 接入 Skills（可选）', '添加 Skills，让 Agent 使用搜索。', btn(`${p}-c4b`, '管理 Skills'))}</div>
</div>`;
}

// Provider list: configured providers float to the top of their group, the rest sort by id.
export const PROVIDER_GROUPS = [
  ['主搜索', [['openai', 'OpenAI 兼容接口'], ['xai', 'xAI']]],
  ['文档检索', [['context7', 'Context7'], ['exa', 'Exa']]],
  ['网页搜索', [['deepseek', 'DeepSeek'], ['tavily', 'Tavily'], ['tinyfish', 'tinyfish'], ['zhipu', '智谱'], ['zhipu-mcp', '智谱 Coding Plan']]],
  ['网页抓取', [['firecrawl', 'Firecrawl'], ['jina', 'Jina'], ['zhipu-reader', '智谱网页阅读']]],
];
export function providerList(p, { configured = [], unsaved = [], selected = 'routing', hover = '', router = 'JEV 语义路由', sortBy = null } = {}) {
  const item = (id, title, sub) => `<div class="ss-li${selected === id ? ' on' : ''}${hover === id ? ' hover' : ''}" id="${p}-li-${id}"><div>${title}</div><div class="ss-sub">${sub}</div></div>`;
  let s = `<div style="padding:30px 36px 6px"><div class="ss-in"><span class="ph">查找服务商</span></div></div>` + item('routing', '意图路由', router);
  for (const [group, items] of PROVIDER_GROUPS) {
    s += `<div class="ss-lh">${group}</div>`;
    const float = sortBy || configured;
    const sorted = [...items].sort((a, b) => (float.includes(b[0]) - float.includes(a[0])));
    for (const [id, title] of sorted) s += item(id, title, (configured.includes(id) ? '已配置' : '未配置') + (unsaved.includes(id) ? ' · 未保存' : ''));
  }
  return s;
}
const field = (p, id, label, ph, links = ['申请 Key', '文档']) => `<div class="ss-stack s8"><div class="ss-row" style="gap:12px"><span class="ss-b ss-grow">${label}</span><span class="ss-q">?</span></div>
  <div class="ss-in" id="${p}-${id}"><span class="ph">${ph}</span></div>${links.length ? `<div class="ss-row" style="gap:24px">${links.map(l => `<span class="ss-link">${l}</span>`).join('')}</div>` : ''}</div>`;
const valueField = (p, id, label, value, dd = false) => `<div class="ss-stack s8"><div class="ss-row" style="gap:12px"><span class="ss-b ss-grow">${label}</span><span class="ss-q">?</span></div>
  <div class="ss-in${dd ? ' dd' : ''}" id="${p}-${id}">${value}</div></div>`;
const section = (title, body) => `<div class="ss-stack s12"><div class="ss-h2">${title}</div><div class="ss-card ss-stack" style="--g:20px">${body}</div></div>`;

function providers(p) {
  return `<div class="ss-split" style="bottom:90px">
  <div class="ss-left"><div id="${p}-pl" style="position:absolute;left:0;right:0;top:0">${providerList(p)}</div></div>
  <div class="ss-right">
    <div class="ss-scroll ss-stack" id="${p}-pd-exa" style="display:none">
      <div class="ss-stack s8"><div class="ss-h1">Exa</div><div class="ss-sub">查找网页并返回链接和相关摘录。</div>
        <div class="ss-sub">擅长发现文档、论文与产品页面；不适合必须按域名、日期或相似页面筛选的路由请求。</div></div>
      <div class="ss-card"><div class="ss-row"><div class="ss-grow"><div class="ss-b">启用服务商</div><div class="ss-sub">禁用后保留配置，不再发起请求。保存更改后生效。</div></div><span class="ss-tg on"></span></div></div>
      ${section('连接设置', field(p, 'exa-key', 'Exa API Key', '示例：your-api-key'))}
      ${section('高级参数', valueField(p, 'exa-url', 'Exa 地址', 'https://api.exa.ai') + valueField(p, 'exa-to', 'Exa 超时（秒）', '30'))}
      <div class="ss-stack s8" id="${p}-exa-st"><div><span class="ss-pill" id="${p}-exa-pill">尚未测试</span></div><div id="${p}-exa-res"></div></div>
      <div>${btn(`${p}-exa-test`, '测试')}</div>
    </div>
    <div class="ss-scroll ss-stack" id="${p}-pd-routing">
      <div class="ss-stack s8"><div class="ss-h1">意图路由</div><div class="ss-sub">先选择路由方式，再填写该模式使用的参数。</div></div>
      ${section('路由模式', valueField(p, 'rt-mode', '路由模式', 'JEV 语义路由', true))}
      <div class="ss-sub" id="${p}-rt-note">普通搜索只选路一次；深入搜索按证据缺口继续。未配置 Jev 时使用本地路由。</div>
      ${section('JEV 连接', field(p, 'rt-key', 'JEV / TypeSafe API Key', '示例：your-api-key', ['文档']) + valueField(p, 'rt-url', 'TypeSafe 地址', 'https://api.typesafe.ai/v1') + valueField(p, 'rt-model', 'JEV 模型', 'jev-latest'))}
      ${section('检索与判断', valueField(p, 'rt-to', 'JEV 单次判断超时（秒）', '15') + valueField(p, 'rt-rounds', '深入搜索最多轮数', '3') + valueField(p, 'rt-ch', '深入搜索每轮渠道数', '3')
        + valueField(p, 'rt-n', 'JEV 每个渠道结果数', '5') + valueField(p, 'rt-th', 'JEV 渠道适用概率阈值', '0.5') + valueField(p, 'rt-suf', '深入搜索证据充分阈值', '0.75'))}
    </div>
  </div></div>
  <div class="ss-foot"><span class="ss-sub ss-grow" id="${p}-pfs">没有未保存的修改 · 测试不会自动保存配置</span>${btn(`${p}-pfx`, '放弃修改')}${btn(`${p}-pfc`, '检查配置')}${btn(`${p}-pfv`, '保存更改', 'pri')}</div>`;
}

function search(p) {
  return `<div class="ss-split">
  <div class="ss-left" style="width:510px"><div class="ss-scroll ss-stack" id="${p}-sl">
    <div class="ss-stack s8"><div class="ss-h2">输入</div><div class="ss-sub">选择工具并填写请求，结果会显示在右侧。</div></div>
    <div style="position:relative"><div class="ss-in dd" id="${p}-tool">搜索</div>
      <div class="ss-pop" id="${p}-pop"><div id="${p}-popl">${TOOLS.map((n, i) => `<div class="ss-opt" id="${p}-opt${i}">${n}</div>`).join('')}</div></div></div>
    <div class="ss-stack" style="--g:18px">
      <div id="${p}-tdesc">选择一个合适渠道检索，返回结果和来源；普通搜索只运行一轮。</div>
      <div class="ss-stack s8"><div class="ss-b">问题或关键词</div><div class="ss-sub">要问的问题或关键词。</div><div class="ss-in" id="${p}-q"></div></div>
      <div class="ss-stack s8" id="${p}-depth" style="display:none"><div class="ss-b">研究深度</div><div class="ss-sub">研究预算上限；达到目标后会提前停止。</div><div class="ss-in dd" id="${p}-depthv">deep</div></div>
      <div class="ss-stack s8" id="${p}-evd" style="display:none"><div class="ss-b">研究证据目录</div><div class="ss-in" id="${p}-evdv"></div></div>
    </div>
    <div class="ss-row" style="gap:12px">${btn(`${p}-run`, '开始 搜索', 'pri')}<span id="${p}-opts">${btn(`${p}-optsb`, '搜索选项…')}</span></div>
  </div></div>
  <div class="ss-right">
    <div id="${p}-empty" style="position:absolute;left:0;right:0;top:0;bottom:0;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:18px;text-align:center">
      <span style="color:#5F5F5F">${ICON.find}</span><div class="ss-h2">结果会显示在这里</div><div class="ss-sub">先选择工具并运行一次请求。</div></div>
    <div id="${p}-busy" style="position:absolute;left:0;right:0;top:0;bottom:0;display:none;flex-direction:column;align-items:center;justify-content:center;gap:24px;text-align:center">
      <div class="ss-spin" id="${p}-spin" style="width:48px;height:48px;border-width:4px"></div><div>任务正在运行。完成后会显示可读结果和来源。</div>${btn(`${p}-seeact`, '查看活动')}</div>
    <div class="ss-scroll ss-stack" id="${p}-res" style="display:none">
      <div class="ss-row" style="gap:12px">${btn(`${p}-copy`, '复制结果')}${btn(`${p}-export`, '导出结果')}${btn(`${p}-json`, '高级 JSON')}</div>
      <div class="ss-pre" id="${p}-text" style="line-height:1.55"></div>
      <div class="ss-stack s8" id="${p}-srcs"></div>
    </div>
  </div></div>`;
}

function activity(p) {
  return `<div class="ss-split">
  <div class="ss-left" style="width:420px">
    <div style="padding:24px 24px 12px" class="ss-stack s12"><div class="ss-sub">活动筛选</div>
      <div class="ss-row" style="gap:6px" id="${p}-tabs"><span class="ss-pill act">全部</span><span class="ss-pill" style="background:none">运行中</span><span class="ss-pill" style="background:none">失败</span></div>
      <div class="ss-row" style="gap:12px">${btn(`${p}-arefresh`, '刷新')}${btn(`${p}-amore`, '更多')}</div></div>
    <div id="${p}-alist"></div>
  </div>
  <div class="ss-right"><div class="ss-scroll ss-stack" id="${p}-adetail"></div></div></div>`;
}

export const AGENTS_ALL = ['Codex', 'Claude Code', 'Cursor', 'OpenCode', 'GitHub Copilot', 'Gemini CLI', 'Cline', 'Roo Code', 'Kiro',
  'Qoder', 'CodeBuddy', 'Factory Droid', 'Pi Agent', 'Kilo CLI', 'Antigravity', 'Windsurf', 'Hermes Agent'];
export function skillRows(p, { on = ['Codex', 'Claude Code', 'Cursor'], status = {} } = {}) {
  return AGENTS_ALL.slice(0, 7).map((a, i) => `${i ? '<div class="ss-divline" style="margin:12px 0"></div>' : ''}<div class="ss-row" id="${p}-sk${i}"><div class="ss-grow"><div class="ss-b">${a}</div><div class="ss-sub" id="${p}-sks${i}">${status[a] || '未安装'}</div></div>${btn(`${p}-skf${i}`, '文件详情')}<span class="ss-tg${on.includes(a) ? ' on' : ''}" id="${p}-skt${i}"></span></div>`).join('');
}
function skills(p) {
  return `<div class="ss-scroll ss-stack" id="${p}-sks" style="bottom:90px">
    <div class="ss-stack s8"><div class="ss-h1">更新 Skills</div><div class="ss-sub">Skills 由当前 CLI 提供；自动维护已接入目标，保留个人修改。</div></div>
    <div class="ss-card ss-stack s12"><div class="ss-h2">当前 CLI 提供的 Skills</div><div>CLI 0.1.30</div><div class="ss-row" style="gap:12px">${btn(`${p}-skr`, '刷新 CLI 提供的 Skills')}${btn(`${p}-skp`, '检查详情与偏好')}</div></div>
    <div class="ss-stack s12"><div class="ss-h2">选择 Agent</div><div class="ss-sub">状态只表示 Smart Search Skill 内容。Codex 使用的 .agents/skills 也可能被其他兼容 Agent 读取。</div>
      <div class="ss-card" id="${p}-skrows">${skillRows(p)}</div></div>
    <div id="${p}-skres"></div>
  </div>
  <div class="ss-foot"><span class="ss-sub ss-grow" id="${p}-skc">已选择 3 个 Agent</span>${btn(`${p}-sks1`, '刷新本机状态')}${btn(`${p}-sks2`, '移除 Skills')}${btn(`${p}-skgo`, '更新所选 Skills', 'pri')}</div>`;
}

function settings(p) {
  return `<div class="ss-scroll ss-stack">
    <div class="ss-card"><div class="ss-row"><img src="../assets/smart-search-256.png" alt="" style="width:72px;height:72px;border-radius:15px"><div class="ss-grow"><div class="ss-h2">Smart Search</div><div class="ss-sub">版本 0.1.30 · konbakuyomu/smartsearch</div></div><span class="ss-link">GitHub</span></div></div>
    <div class="ss-stack s12"><div class="ss-h2">通用</div><div class="ss-sub">管理语言、外观和配置目录。</div>
      <div class="ss-card" id="${p}-st-gen"><div class="ss-row" id="${p}-st-lang"><div class="ss-grow"><div class="ss-b">界面语言</div><div class="ss-sub">App 与独立 CLI 分别保存语言选择。</div></div><div class="ss-in dd" style="width:240px">跟随系统</div></div>
        <div class="ss-divline"></div><div class="ss-row" id="${p}-st-look"><div class="ss-grow"><div class="ss-b">外观</div><div class="ss-sub">跟随系统外观，或单独选择浅色、深色模式。</div></div><div class="ss-in dd" style="width:240px">跟随系统</div></div>
        <div class="ss-divline"></div><div class="ss-row" id="${p}-st-dir"><div class="ss-grow"><div class="ss-b">当前配置目录</div><div class="ss-sub ss-mono">C:\\Users\\me\\AppData\\Local\\smart-search</div></div>${btn(`${p}-st-dirb`, '选择配置目录…')}</div>
        <div class="ss-sub" style="margin-top:12px">保存服务商配置和本地记录的文件夹；移动 App 不会改变此目录。</div></div></div>
    <div class="ss-stack s12" id="${p}-st-upd"><div class="ss-h2">App 更新</div><div class="ss-sub">独立更新 App，不改变 CLI 安装。</div>
      <div class="ss-card"><div class="ss-row"><div class="ss-grow"><div class="ss-b">自动检查更新</div><div class="ss-sub">每次打开 App 时检查，确认后才下载。</div></div><span class="ss-tg on"></span></div></div></div>
  </div>`;
}

const PAGES = { overview, providers, search, activity, skills, settings };

// Tools in the 搜索与研究 dropdown, in catalog order (src/smart_search/desktop_catalog.py).
export const TOOLS = ['搜索', '查看路由', '读取网页', '站点地图', 'Exa 搜索', 'Exa 相似网页', '智谱搜索', '智谱 MCP 搜索', '智谱 MCP 网页阅读',
  '智谱 仓库文档检索', '智谱 仓库目录', '智谱 仓库文件阅读', 'AnySearch 查询领域（实验性）', 'AnySearch 搜索（实验性）', 'AnySearch 读取网页（实验性）',
  'AnySearch 批量搜索（实验性）', 'SciVerse 目录（实验性）', 'SciVerse 搜索（实验性）', 'SciVerse 语义搜索（实验性）', 'SciVerse 文献阅读（实验性）',
  'SciVerse 关联检索（实验性）', 'Context7 查找库', 'Context7 查文档', '离线研究计划', '在线研究', '冒烟检查', '服务商全面诊断（在线）',
  '诊断 OpenAI 兼容接口', '当前模型', '离线回归检查'];

// 搜索与研究 result: the readable text and the 来源链接 disclosure.
export function resultSources(sources) {
  return `<div class="ss-row" style="gap:10px"><span class="ss-b">来源链接（${sources.length}）</span>${ICON.chevron}</div>`
    + sources.map(([title, url]) => `<div class="ss-link" style="white-space:normal">${title} · ${new URL(url).host}</div>`).join('');
}

// 活动: list rows [{key, title, time, origin, status, phase, elapsed}] and one run's detail.
export function activityList(p, rows, selected = '') {
  return rows.map(r => `<div class="ss-li${r.key === selected ? ' on' : ''}" id="${p}-ar-${r.key}" style="margin:0 12px;padding:15px 18px">
    <div class="ss-b">${r.title}</div><div class="ss-sub">${r.time} · ${r.origin}</div><div class="ss-sub">${r.status} · ${r.phase} · ${r.elapsed}</div></div>`).join('');
}
export function activityDetail(p, r) {
  const tone = r.status === '已完成' ? 'ok' : r.status === '运行中' ? 'act' : 'bad';
  const kv = (k, v) => `<div class="ss-stack s8" style="--g:6px"><div class="ss-sub">${k}</div><div class="ss-mono" style="font-size:18px">${v}</div></div>`;
  return `<div class="ss-row" style="gap:16px"><span class="ss-h1" style="font-size:33px">${r.title}</span><span class="ss-pill ${tone}">${r.status}</span></div>
    <div class="ss-sub">${r.origin} · ${r.phase} · 用时 ${r.elapsed}</div>
    <div class="ss-card ss-stack s12">${kv('开始', r.started)}${kv('配置目录', r.dir)}<div>${r.provider}</div></div>
    ${r.button ? `<div><span class="ss-btn" id="${p}-adb">${r.button}</span></div>` : ''}
    <div class="ss-stack s12" id="${p}-aev"><div class="ss-h2">阶段事件</div>${r.events.map(e => `<div style="font-size:19px">${e}</div>`).join('')}</div>`;
}

// The whole window. p prefixes every id so two Apps can share a page.
export function appMarkup(p, { w = 1600, h = 940, left = 0, top = 0 } = {}) {
  const nav = NAV.map(([k, n, ic], i) => `<div class="ss-ni" id="${p}-n-${k}" style="top:${72 + i * 66}px">${ICON[ic]}<span>${n}</span></div>`).join('');
  return `<div class="ss-app" id="${p}" style="left:${left}px;top:${top}px;width:${w}px;height:${h}px">
  <div class="ss-tb"><img src="../assets/smart-search-256.png" alt=""><span>Smart Search</span><span class="ss-wc"><i>${ICON.min}</i><i>${ICON.max}</i><i id="${p}-close">${ICON.close}</i></span></div>
  <div class="ss-nav"><div class="ss-burger">${ICON.burger}</div>${nav}
    <div class="ss-mascot"><img src="../assets/mascot-720.png" alt=""></div><div class="ss-dot on" id="${p}-dot"></div></div>
  <div class="ss-main">
    <div class="ss-hdr"><span class="ss-pn" id="${p}-pn">概览</span><span class="ss-ib" id="${p}-fb">${ICON.msg}</span><span class="ss-ib">${ICON.refresh}</span></div>
    ${Object.entries(PAGES).map(([k, f]) => `<div class="ss-page" id="${p}-pg-${k}">${f(p)}</div>`).join('')}
  </div>
  <div class="ss-fly" id="${p}-fly"><div class="hd"><span class="ss-h2" style="font-size:24px">操作提示</span><span class="ss-btn" style="height:42px">清除提示</span></div>
    <div class="ss-b" id="${p}-flyt"></div><div class="ss-sub" id="${p}-flym" style="margin-top:6px"></div></div>
  <div class="ss-scrim" id="${p}-scrim"><div class="ss-dlg" id="${p}-dlg"><div class="bd ss-stack s12"><div class="ss-h2" id="${p}-dlgt"></div><div class="ss-pre" id="${p}-dlgb"></div></div>
    <div class="ft"><span class="ss-btn pri" id="${p}-dlgok"></span><span class="ss-btn" id="${p}-dlg2" style="display:none"></span><span class="ss-btn" id="${p}-dlgno">取消</span></div></div></div>
</div>`;
}

// ---------- per-frame helpers ----------
const st = (el, props) => { for (const k in props) if (el.style[k] !== props[k]) el.style[k] = props[k]; };
const hx = (el, h) => { if (el._h !== h) { el.innerHTML = h; el._h = h; } };
export const $id = (id) => document.getElementById(id);
export { st as setStyle, hx as setHTML };
export const cls = (el, name, on) => { if (el.classList.contains(name) !== !!on) el.classList.toggle(name, !!on); };

// Show one page; k is the page's entrance progress (0→1) for WinUI's slide-in.
export function showPage(p, page, k = 1) {
  for (const [key] of NAV) {
    const el = $id(`${p}-pg-${key}`);
    st(el, { display: key === page ? 'block' : 'none' });
    if (key === page) st(el, { transform: `translateY(${((1 - k) * 36).toFixed(1)}px)`, opacity: String(Math.min(1, k * 1.3)) });
    cls($id(`${p}-n-${key}`), 'on', key === page);
  }
  hx($id(`${p}-pn`), PAGE_NAME[page]);
}
// A text box: typed text, placeholder, focus caret.
export function input(el, { text = '', ph = '', focus = false, caret = false, mask = false } = {}) {
  const shown = mask ? '•'.repeat([...text].length) : text;
  hx(el, (shown ? `<span>${shown.replace(/</g, '&lt;')}</span>` : (ph ? `<span class="ph">${ph}</span>` : '')) + (caret ? '<span class="cv"></span>' : ''));
  cls(el, 'focus', focus);
}
export function flyout(p, { on = false, k = 1, title = '', msg = '', x = 0, y = 0 } = {}) {
  const el = $id(`${p}-fly`);
  st(el, { display: on ? 'block' : 'none', left: `${x}px`, top: `${y}px`, opacity: String(Math.min(1, k * 1.4)), transform: `translateY(${((1 - k) * -16).toFixed(1)}px)` });
  if (on) { hx($id(`${p}-flyt`), title); hx($id(`${p}-flym`), msg); }
}
export function dialog(p, { on = false, k = 1, title = '', body = '', ok = '继续', second = '', cancel = '取消', w = 720, h = 0, appW = 1600, appH = 940 } = {}) {
  const sc = $id(`${p}-scrim`), d = $id(`${p}-dlg`);
  st(sc, { display: on ? 'block' : 'none', opacity: String(Math.min(1, k * 2)) });
  if (!on) return;
  hx($id(`${p}-dlgt`), title); hx($id(`${p}-dlgb`), body); hx($id(`${p}-dlgok`), ok); hx($id(`${p}-dlgno`), cancel);
  hx($id(`${p}-dlg2`), second); st($id(`${p}-dlg2`), { display: second ? 'inline-flex' : 'none' });
  st(d, { width: `${w}px`, left: `${(appW - w) / 2}px`, top: `${(appH - (h || d.offsetHeight)) / 2}px`, transform: `scale(${(1.05 - 0.05 * Math.min(1, k)).toFixed(4)})` });
}
