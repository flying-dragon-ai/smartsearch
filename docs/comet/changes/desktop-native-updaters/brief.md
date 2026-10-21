# Outcome

Windows 接入 Velopack、macOS 接入 Sparkle，由成熟框架完成 Smart Search App 与内置 Python 引擎的整体更新，提供后台检查、新版提示、用户点击后下载和安装重启，以及真实可用的差分更新。

# Scope

- 保留 WinUI 3、SwiftUI、Python sidecar 和现有页面结构；采用各平台 SDK，不改为跨平台 Web 壳。
- 迁移 App 自更新和打包发布链；独立 CLI 保留原 npm/mise 管理器，Skills 保留按内容比较和显式同步。
- 带入上一候选 `desktop-update-state-fix` 已验证的 CLI 初始化、Windows stdin、缓存状态与 Skills 修复；原候选及验收记录保留。
- 保留默认每天检查一次和关闭开关。发现新版提示，用户点击后下载、安装并重启；应用退出后不运行常驻服务。
- Windows 用 Velopack 按用户安装；处理从现有 Inno Setup 安装转入新布局的首次完整安装。
- macOS 引入 Sparkle，按现有 arm64/x86_64 两种原生包分别发布可信 feed，保留当前最低系统要求。
- GitHub Actions 生成安装包、完整更新包、差分包、更新清单和校验信息。上一版不可用时明确记录完整包发布；网络/签名等错误不冒充正常首次发布。
- 测试使用独立工作区、独立安装身份/目录和测试更新源；修改、验证流水线源码不等于线上已运行或正式已发布。

## Source coverage

| 来源 | 读取状态 | 内容及用途 | 对应规格 | 验收 | 状态 |
| --- | --- | --- | --- | --- | --- |
| 用户要求正式向 Velopack / Sparkle 接入推进 | complete | 本次实现目标 | desktop-native-updaters 全文 | 全部 Scenario | covered |
| 本轮前文：静默检查、更新提醒、增量更新和 CI/CD | complete | 用户可见功能 | 检查与提示、差分、构建发布 | 对应 Scenario | covered |
| `D:/Dev/30_第三方项目/30_AI与MCP工具/codex-tweaks` | complete for relevant reference scope | 实现参考：WinUI/SwiftUI SDK 接入、打包脚本、发布 workflow；不导入其产品需求、标识、密钥或完整仓库规则 | 平台集成、差分、身份 | 对应 Scenario | background |
| Smart Search 当前 desktop/README.md、PROTOCOL.md 与 Windows 签名 Spec | complete | 当前架构及需要替换的旧 App 更新合同 | desktop-native-updaters、desktop-windows-signing | 对应 Scenario | covered |
| `desktop-update-state-fix` v21 的当前候选和 15 项验收报告 | complete | 待带入的已有修复依赖；不因此归档、提交或发布原任务 | CLI 和 Skills 边界 | Independent CLI and Skills stay healthy | covered |

# Non-goals

- 不更换前端或搜索后端，不重做界面，不引入新的通用更新抽象或后台服务。
- 不为 CLI/Skills 自制二进制差分更新，不改变 Provider、密钥或搜索行为。
- 不替换历史发行附件，不删除用户配置或改写个人 Skills。用户现已明确授权一直推进到正式发布，本轮准备并发布下一稳定版 `v0.1.24`，包括必要的 Sparkle 正式更新身份、GitHub Secrets、公钥、预检构建、提交推送、Tag、GitHub Release 与 npm latest；发布后升级本机 App 和实际生效的独立 CLI，核对版本、配置和启动状态。GUI 和旧安装迁移结果按实际记录，发布指令本身不等于所有平台全部实测通过。
- 不购买 Apple Developer 资格或 Windows 商业证书，不自动改变本机证书信任库。
- 不自动删除旧工作区、用户数据、真实 CLI 或个人 Skills。

# Acceptance examples

以两份完整目标 Spec 的 Scenario 为准。必须覆盖真实框架安装与升级、差分和完整回退、后台检查和显式安装、安全退出、首次迁移、签名失败阻断、四架构构建配置、CLI/Skills 修复回归，以及明确的实际运行证据边界。

# Constraints and invariants

- 独立候选目录 `smartsearch-native-updaters`，分支 `codex/desktop-native-updaters`，基线 main `b5773df01b111bd107dbdeb5b73ff35ca0e72e17`；原目录与其他候选的未提交工作保留。
- 本轮整合已测 main `65e736501330adf64f5be506c0e7a10dca0462d8`，其产品树与工程师 PR #51 的 `92224fb` 相同；保留 `codex/native-updaters-before-pr51` 指向原候选 `76d00a6`。两端 PR 页面、主题、图标、表单草稿及 Mac SDK/IPC/完整 bundle 签名/DMG 校验保留，仅适配原生更新入口与对应共享状态。
- 正式包仅使用 Smart Search 自己的应用标识、官方源和签名身份；不复用 Codex Tweaks 的 feed、key 或应用标识。
- Windows 继续复用现有自签名身份和内容/身份/时间戳验证，不能退回未签名正式发布。
- macOS 的 Sparkle EdDSA 更新签名与 Apple Developer ID/公证是不同能力。当前只查到 Windows 仓库 Secrets，没有 macOS/Sparkle 配置；缺少正式配置必须明确阻止对应正式发布，不能称为已签名、公证或生产验证。
- 测试密钥只能用于隔离测试产物，不进入正式 feed。秘密值不进入代码、日志、聊天或 artifact。
- 自有任务、未保存配置、CLI/环境/Skills 写入未处理前，不允许更新器强制退出 App；不终止外部 CLI。

# Decisions

- 2026-09-22 用户看过三项手工测试步骤并确认需要安装最新整合候选后，反馈“没什么问题，正式合并发布吧，然后把我目前的版本升级为最新的”。据此记录当前 Windows 测试版的用户验收反馈，并明确授权正式合并发布后升级本机 App 与当前实际生效的独立 CLI。完整 `0.1.23 → 0.1.24` 更新源交互仍需在正式 feed 可用后核对；不据此宣称 macOS 最终整合 GUI 或所有边界场景已实测。安装前保存配置证据，正常退出 App，避免强行终止正在进行的任务；个人 Skills 不因版本号变化而改写。

- 2026-09-22 用户在收到“代码全部合并、12/15验收通过，3项GUI/旧安装迁移和正式Sparkle配置待补”的结果后，明确要求“一直推进到正式发布”。本轮据此推进 `v0.1.24`，沿用已通过的四平台代码基线及 Windows 签名身份；为 Sparkle 创建独立、持续复用的 Ed25519 更新身份，公开公钥随仓库保存，私钥在仓库外以当前用户 DPAPI 加密备份并配置到 GitHub Secrets。先执行使用正式密钥的不发布预检，核对完整资产和签名后开放正式发行。Sparkle 更新签名不等于 Apple Developer ID 或公证，Mac App 保留工程师已验证的 ad-hoc 完整性签名。
- 用户继续自行负责 GUI 测试，并询问三项如何操作；已提供旧版迁移、更新提示、草稿/任务保护的顺序和通过标准。新框架候选 `0.1.23` 到正式 `0.1.24` 的交互升级测试需要正式更新源可用后完成。在获得实际结果前，A2/A3/A5保留待验收；发布授权不转换为这些测试已通过，也不自动归档 Native 变更。

- 2026-09-22 用户已体验工程师 Windows 版本，反馈“不错，看了下没啥大问题，完成剩余的全部合并吧”。本轮据此恢复 Build，完成已有 Velopack/Sparkle、CLI/Skills 修复与 PR51 的整合并合入 main；不再停留在只合 #51 的第一步。保留已测试界面，适配后的 Windows/Mac 更新代码执行新的构建、后端和隔离 SDK 升级检查，工程师原始测试仍作为界面基线证据。正式稳定版本在用户测试最终包后发布，新增整合的实机/GUI 与正式 Sparkle 密钥边界如实记录。

- #51 合并后 main CI `35627327676` 的 Linux/Windows 三项矩阵全部通过，保留原 PR 四架构打包通过记录；本结论仅覆盖已原样合入的产品树，原生更新候选仍待后续整合。

- 2026-09-22 用户明确回复“是的，要记住他那边是做完了测试的，开始合并吧”，授权第一步原样合并 #51，并要求保留工程师已测基线的事实。已通过匹配 PR head 的 merge 操作合入远端 main，合并提交 `65e736501330adf64f5be506c0e7a10dca0462d8`，第二父提交为工程师已测的 `92224fbc8dc1ee832694593b2eb442971ca833b1`；两者文件树均为 `92b64fbd48b506eda06eb644d02a71becde1049d`，完全一致。认可 PR 已记录的 Mac 实机测试和双 Mac 架构 CI，不因本方没有 Mac 而将原样基线改记为未测试；后续新增整合才需要对应复验。本地 main 工作区已快进同步，当前主目录和其他候选的未提交工作保持原状。main 推送触发现有 npm 工作流并创建 `v0.1.23-beta.1` GitHub 预发布（无桌面附件）；正式 npm latest 读回仍为 `0.1.23`。此前“第一步不会发布版本”的预计不准确，实际自动发布行为按本条纠正。

- 2026-09-22 用户提供 PR #51，要求优先采用工程师的修改及页面美化。已核对其固定提交 `92224fbc8dc1ee832694593b2eb442971ca833b1`，范围同时包含 Windows/macOS 页面、服务商开关、Mac 签名/打包和共享后端；因此前条“Windows 保留本方已验证实现”指保留更新、CLI/Skills 修复行为，界面和页面结构也优先沿用 PR。PR 合入当前 main `b5773df` 的结果树与 PR 完全相同，无冲突；与本候选 `76d00a6` 合并有 12 个文件冲突，且新旧更新 RPC 不兼容。建议先原样接收 #51，再基于其页面和 Mac 构建链整合原生更新；本次仅检查、隔离构建并提出该顺序，未执行正式合并。PR 的 7 项远端 CI 已成功，本机原样候选全测 963 passed/2 skipped，Windows x64 便携构建与后端 smoke 通过。PR 没有 Sparkle，现有原生更新目标和未完成验收继续保留；最终 Mac 集成提交仍交工程师验证。

- 2026-09-21 用户进一步明确：本方没有 macOS 测试环境，对方开发者在 Mac 上使用 Codex 开发并全面测试，因此后续完整接收对方交付的 macOS 成果，以其测试通过的确切提交作为 macOS 集成基线。macOS 界面、签名、打包及平台生命周期冲突采用对方经验证的实现；本方未验证的 macOS 候选仅供参考，不覆盖或未经对方验证叠加到该基线。Windows 保留本方已验证的实现。共享 Python 后端、协议和 CI 按功能合并，优先适配对方已验证的调用合同，不对整个仓库使用一方覆盖；若已有 Sparkle 等目标尚未被对方成果覆盖，交由对方补齐并在 Mac 验证，不视作需求已取消或验收已通过。后续在独立集成分支保留双方提交，取得对方测试提交、覆盖范围和结果；本方执行 Windows/共享层回归，对方验证最终集成提交的 macOS 行为。对方原分支的通过记录不自动证明合并后版本通过。本次记录整合原则，不执行合并、修改产品实现或接受未完成验收。

- 2026-09-21 用户确认提交、推送并运行候选 CI，同时明确 macOS 由另一开发者推进，后续统一合并正式版本。本轮只执行 Windows x64/ARM64 签名及升级验证；保留现有 macOS 候选供整合参考，不继续修改其实现，也不把未运行项计为通过。正式合并、发布及正式 Sparkle 密钥配置仍待后续授权。

- 用户已明确确认上述完整范围及 15 项验收，授权进入实现；本轮新增提交推送授权见上条，正式发布、真实用户安装和新正式密钥配置仍需后续授权。

- 用户已明确要求正式接入 Velopack / Sparkle，并指定 Codex Tweaks 作为实现参考。
- App 与内置引擎整体更新；外部 CLI/Skills 保持独立。这与前文已讨论的接入方向一致。
- 沿用现有 24 小时检查频率、稳定渠道和用户点击安装的行为；不增加预发布渠道选择或自动安装设置。
- 本次保持单个 Native change。两个平台共用发布合同、旧路径迁移和 CLI/Skills 基线，集中协调和验收；只读调查可并行，不为两个平台额外引入 Supervisor 集成分支。
- 参考项目本地 Windows 脚本只收集完整包，macOS 明确 `--maximum-deltas 0`。本次使用框架自带工具补齐真实差分产出和回退测试，不照搬关闭差分的配置。
- 先完成并验证可审查候选、打包脚本和发布流水线。正式密钥配置、上传和正式环境迁移保持独立的发布步骤。
- 首次 Windows 迁移拟采用一次完整安装及清晰的旧版处理引导；后续版本交给 Velopack。具体引导与旧安装识别纳入验收，不静默删除用户原安装。

# Open questions

用户已明确回复“确认，按此范围实现”，确认已展示的完整行为、15 项验收和非目标；没有待决的实现范围问题。macOS 正式签名配置缺失是发布前置条件，开发可用隔离测试身份继续，不能把发布前置条件当作已满足。

# Verification expectations

复用已有测试体系及当前 Windows 构建工具；开发时仅执行适用检查。先验证当前已修复基线，再验证平台 SDK 接入、真实 A→B 差分升级和完整包回退。对网络失败、签名/内容篡改、运行中写入及首次迁移做有意义的回归。macOS 与 ARM64 在对应 runner 或实机上获取独立证据；未运行项必须保留未运行/受阻，不由 Windows x64 或源码审查代替。最终由新的只读 Verifier 核对全部 Scenario。
