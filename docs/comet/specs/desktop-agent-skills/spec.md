# Desktop Agent Skills

## Purpose

“更新 Skills”是 Windows 与 macOS 原生 App 中维护 Smart Search Agent Skill 的入口。它维护 Agent 使用的说明文件，不安装或升级 Agent 软件。独立 CLI 继续共用用户配置，在 App 关闭后仍可运行。

## Source and checks

从官方 npm 包 `@konbakuyomu/smart-search` 的 latest 稳定版本取得 Skills；不能把 App 内置版本称为最新。只读取发行元数据和归档，不执行其中的程序或安装脚本。校验 SHA512 完整性、受信 HTTPS 地址、文件路径、类型、数量和大小后才使用文件。最近一次检查时间、来源版本、离线错误明确显示。

默认每天自动检查一次并在页面提示；自动检查可以关闭。检查只写 App 自有缓存，不修改任何 Agent Skills。手动检查可随时重试。缓存不代表最新在线检查成功。

### Scenario: Trusted stable source
WHEN 最新正式版比 App 内置副本更新，THEN 页面以官方稳定版归档中的 Skills 为基准，显示版本与检查时间；不执行远程代码，不使用 main 或预发布版本。

### Scenario: Download failure preserves installations
WHEN 网络失败、重定向不可信、摘要不符、归档路径越界或含特殊文件，THEN 检查失败可重试，已安装的 Skill 保持不变，旧缓存不得冒充本次最新检查成功。

### Scenario: Automatic checks do not install
WHEN 到达自动检查周期，THEN 至多一个检查任务运行，只更新缓存与提示；关闭自动检查后不再自动联网；只有用户点击安装或更新所选目标才写入 Agent 目录。

## Targets and content

使用共享 Agent 注册表，保留现有目标并加入已核实的 Cline、Roo Code。显示 Agent 名、用户级目标路径和 Smart Search Skill 状态；Claude 尊重绝对 `CLAUDE_CONFIG_DIR`。历史目录只提示、不迁移或删除。Codex 的 `.agents/skills` 可由其他兼容 Agent 读取，页面提示共享目录语义。

状态表示“未安装”“内容不同，可同步”“与所选来源一致”“读取失败”。不声称 Agent 软件已安装、已更新、已加载 Skill 或已成功调用。未记录的旧 Skill 版本保持未知。

### Scenario: Unified target list and honest status
WHEN 打开页面，THEN Codex、Claude Code、Cursor、Copilot、Gemini、OpenCode、Cline、Roo Code 及保留目标在同一列表，显示准确目标路径、Skill 内容状态、差异文件和历史目录提示；刷新保留用户选择。

### Scenario: Invocation stays consistent
WHEN 已有 Skill 写着旧 CLI 路径而当前独立 CLI 路径改变，THEN 更新根据当前已验证独立 CLI 重建本机调用说明，状态和安装比较同一份预期内容，更新后不会因该说明一直显示有差异；通用 CLI 比较识别本机说明，不误报纯注记差异。

## Explicit update and recovery

用户先选目标，再点击“更新所选 Skills”。界面展示来源、目标与覆盖内容，确认后先为已有不同内容建立可恢复副本，再原子替换托管文件。保留额外文件、其他 Skills、未选目标和历史目录；拒绝链接或越界写入。失败显示原因及备份位置，不能宣称全部完成。复用同一安全写入实现，不另建安装框架。

### Scenario: Selected updates preserve user files
WHEN 用户更新指定目标，THEN 只写所选目标的托管文件，先备份不同内容，保留用户额外文件和其他目标，返回备份位置；重复同步相同内容不重写、不重复备份。

### Scenario: Unsafe targets and write failures
WHEN 目标含链接、越界路径或写入失败，THEN 拒绝不安全写入，旧内容保持可恢复，显示失败和备份位置；并发环境安装、CLI 更新与 Skills 同步不能交叉写入。

## Native UI and compatibility

两端保留原生系统控件和中英文，主页面名称为“更新 Skills”。独立 CLI 准备与版本状态作为共用前提单独呈现；Skills 同步不升级 CLI。CLI 未验证或版本落后于来源时说明并引导准备/更新。更新完成后提示 Agent 重新加载（Gemini `/skills reload`，其他 Agent 重新打开会话），实际 AI 调用由用户验证。

### Scenario: Clear native pages
WHEN 用户使用任一平台或语言，THEN 可以区分检查最新 Skills、更新所选 Skills 和共用 CLI 环境准备，看到结果、备份路径与重新加载说明；无收费搜索被自动触发。

### Scenario: Regression and evidence boundaries
WHEN 提交候选实现，THEN 隔离目录与协议回归、双语资源检查、Windows 构建通过；App/CLI 原有搜索、配置与环境功能保持兼容。GUI 手测、macOS 实机、正式安装、发布和真实 AI 调用分别标记，不能由静态检查代替。
