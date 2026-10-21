# Outcome

把原“AI 接入”页改为含义明确的“Skills 安装与更新”，让用户按编程 Agent 安装或同步最新的 Smart Search skill，并能准确判断软件已更新但个人 skill 未同步的情况。

# Scope

- Windows 与 macOS 原生页面同步调整，使用中英文一致的术语。
- 用现有 Agent 注册表统一列出支持目标、用户级安装目录、Smart Search skill 状态和安装/更新操作；状态不能冒充 Agent 软件的安装或版本状态。
- 核对当前仓库、发行包及本机 Skills 的来源与差异，支持独立获取所选更新源的 skill，避免旧 App 内置副本被当作最新。
- 保留共用独立 CLI 的环境准备和 App/CLI 解耦，把环境管理与 Agent 专属 skill 同步分开呈现。
- 更新技能前展示目标和变更，保留其他 skill、额外文件与个人修改的可恢复副本；界面说明 AI 重新加载和实际调用验证。
- 用户前一条截图用于当前 UI 歧义诊断，属于参考，不作为待逐像素复刻的设计稿。

# Non-goals

- 不安装、登录或升级 Agent 软件，不改变主搜索/Jev/provider 的行为。
- 不创建 MCP Server，不批量删除文件，不静默迁移历史技能副本。
- 本轮实现授权不自动延伸为发布新版本、替换正式 App 或覆盖全部个人 Skills。

# Acceptance examples

正式场景在完整目标 Spec 中定义：准确状态、可信最新源、所选目标更新、备份及恢复、旧软件与新 skill 的兼容提示、双平台双语界面及原功能回归。

# Constraints and invariants

- 基线为 main 4d104b5；独立工作区 codex/desktop-agent-skills-update，保留其他工作区。
- 不把文件不同等同损坏或过期；机器专属调用信息不能造成永久“有更新”。
- 只读检查不修改技能/配置、不发收费搜索；下载、验证、安装成功是不同状态。
- 下载失败、摘要错误、路径越界或写入失败不能破坏旧版 Skills。
- 配置 Key 不写入技能正文、日志或备份摘要。

# Decisions

- 用户明确要求直接修改页面与机制，名称采用 Skills，不再以“AI 接入”概括技能维护。
- 页面按 Agent 管理同一套 Smart Search skill；Agent 目录和加载约定应显式处理。
- 以现有原生控件、技能注册表和安全写入逻辑为基础，不增加独立管理框架。
- 这是一项紧密关联的单个 Native change，不拆成多会话 Supervisor。
- 用户已选择最新正式版；自动检查只提示，更新由用户点击触发。

# Open questions

Q1 已确认：从最新正式版获取 Skills，不使用 GitHub main 未发布内容。
Q2 已确认：自动检查并提示，用户点击后才更新所选 Agent 的 Skills。

# Verification expectations

结合隔离目录回归、可信下载与失败模拟、实际发行源只读检查、Windows 构建和协议检查验证。需要新的独立只读验收；GUI 手测及 macOS/ARM64 实机范围继续单独标记，不能用代码检查冒充。具体检查在事实调查完成后绑定到候选实现。
