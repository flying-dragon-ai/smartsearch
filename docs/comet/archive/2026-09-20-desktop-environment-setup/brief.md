# Outcome

让中文和英文用户从简短的 README 看懂 Smart Search 的用途，并通过 App 配置搜索服务、准备独立 CLI 和接入 AI。完整命令与配置说明集中到 `docs/guide`。App 与 CLI 可分别选择语言；Codex、Claude Code 调用独立 CLI，关闭或卸载 App 后仍能使用已安装的 CLI。

# Scope

- Windows 与 macOS 的 AI 接入页提供“检测环境”“安装缺少的组件”“验证可用性”，显示步骤、进度、失败原因和下一步。
- 检测 Node/npm、支持 venv/pip 的 Python、独立 npm Smart Search CLI、当前用户环境中的 Codex/Claude Code 和接入文件；只读检测不安装或修复。
- 复用健康、兼容且来源明确的现有运行环境。缺失时安装经过完整性校验的受支持稳定运行环境和 npm 稳定版 CLI；mise 仅复用已有安装，不作为新用户前置要求。
- 安装资源、CLI 和必要调用入口放在用户可写且独立于 App 程序的目录，配置和已有安装保持原归属。已识别的 CLI 更新继续使用原管理器。
- 安装或更新用户所选 AI 的接入文件；已有不同内容先保留并提示差异，不静默覆盖个人修改。
- 验证独立 CLI 的真实启动、版本及本地配置就绪情况，分开显示环境、CLI、接入文件、需要重启和 AI 实际调用待验证状态。提供在 AI 内执行的测试指引，不自动发起收费 AI 请求。
- 重写中英文 README 的入门结构，回答工具是什么、适用场景、何时需要联网搜索、如何在 App 配置以及日常怎样使用。首页保留下载、手册和问题反馈入口；完整 CLI、配置、路由、排障和开发说明集中到双语手册。
- Windows/macOS App 与独立 CLI 支持自动、简体中文和 English。默认跟随系统，非中文环境回退英文；App 可在设置切换，CLI 支持持久偏好和单次 `--lang`。覆盖本工具拥有的界面、帮助、向导、状态及错误说明。
- 依据用户明确要求重组 README；中文成稿再按 `lieflat-less-ai-tone` 的规则清理明确命中的表达，不把该 Skill 当作任意增删事实的许可。

需求来源为本次对话及下表列明的 README 重组来源。仓库实现和官方资料用于事实核验，不自动扩张功能范围。

## Source coverage

以下 README 行号对应本轮改写前、`codex/desktop-environment-setup` 中的来源版本；两份全文已分块读完。现有内容迁移后须保留有效信息，过期版本标注改为历史或当前准确入口，不复制错误声明。表内同一节涵盖该节全部段落、列表、表格、示例和边界说明。

| 来源条目与位置 | 读取状态 | 需要保留的内容 | Spec 位置 | 验收 ID | 覆盖状态 | 理由或替代关系 |
| --- | --- | --- | --- | --- | --- | --- |
| U1：用户本轮要求与三个已答问题 | complete | README 面向新手；双语手册选 docs/guide；沿用测试版；App/CLI 可切换语言 | 完整规格 §11–17 | A11–A17 | covered | 用户明确确认这些决定 |
| R1：EN/CN README 1–26 | complete | 项目名称、标识、语言入口、包/仓库/许可链接 | §11–12 | A11、A12 | covered | 简化首页导航；保留真实链接 |
| R2：EN/CN README 27–69 | complete | 无 Key 的 route 演示、离线边界和 JSON 例子 | §12 | A12 | covered | 迁移至 CLI/路由手册，不作为普通用户首页第一步 |
| R3：EN 70–102；CN 70–102 | complete | CLI/AI 职责、search/deep/research 区别、能力路由流程 | §11–12 | A11、A12 | covered | 首页用普通语言介绍；技术细节进入手册 |
| R4：EN 103–138；CN 103–136 | complete | App/CLI 安装、稳定与测试渠道、Node/Python 条件、独立运行 | §11–12、§17 | A11、A12、A17 | covered | 旧 v0.1.19 下载链接更新为准确发行入口；候选功能标明版本边界 |
| R5：EN 139–211；CN 137–202 | complete | 配置、搜索、读取、研究、Skill 安装/更新与历史路径保留 | §11–12 | A11、A12 | covered | App 主路径放首页；CLI 步骤和路径细节进入手册 |
| R6：EN 212–250；CN 203–241 | complete | 临时 Web UI、参数、语言、远程转发、Key 与环境覆盖 | §12、§15–16 | A12、A15、A16 | covered | 保留已有 `ui --lang zh/en` 和真实调用边界 |
| R7：EN 251–286；CN 242–289 | complete | 能力/服务商表、同能力回退、可观测字段、来源与证据边界 | §12、§16 | A12、A16 | covered | 迁入进阶手册，不弱化检索与证据区别 |
| R8：EN 287–354；CN 290–361 | complete | 研究计划、执行流程、预算、命令、路由与可配置覆盖 | §12 | A12 | covered | 保留完整研究使用说明 |
| R9：EN 355–375；CN 362–382 | complete | 每个服务商用途、Key/参数和官方入口表 | §12 | A12 | covered | 进入完整配置指南，按当前配置目录补齐缺项 |
| R10：EN 377–408；CN 384–416 | complete | 意图路由配置、Jev、embedding/classifier、校准与降级 | §12 | A12 | covered | 进入路由/进阶配置，不要求新手全部配置 |
| R11：EN 409–432；CN 418–441 | complete | 各服务商/API 模式、超时、回退、权限与实验功能边界 | §12 | A12 | covered | 保留有效限定条件和兼容说明 |
| R12：EN 433–473；CN 443–483 | complete | 非交互配置示例和三类最低能力要求 | §11–12 | A11、A12 | covered | 首页用三类用途说明，不误称仅填任意一个 Key 就够 |
| R13：EN 475–499；CN 485–515 | complete | AnySearch/Sciverse 命令、请求参数、ID、兼容和显式使用条件 | §12 | A12 | covered | 进入实验命令/配置参考 |
| R14：EN 500–519；CN 516–574 | complete | 配置路径、覆盖优先级、legacy Windows、环境变量与超时 | §12、§14 | A12、A14 | covered | 完整配置手册，并补充语言偏好规则 |
| R15：EN 520–537；CN 575–592 | complete | 冷却触发、跳过状态、自动恢复和 reset 命令 | §12 | A12 | covered | 进入排障/配置说明 |
| R16：EN 538–612；CN 593–663 | complete | 命令/别名表、smoke 语义及各种 CLI 例子 | §12、§15–16 | A12、A15、A16 | covered | 对照当前 parser 补全完整命令与参数参考 |
| R17：EN 613–656；CN 664–706 | complete | JSON/Markdown/content、部分成功、证据保存和先读正文后引用 | §12、§16 | A12、A16 | covered | 保留机器合同和用户内容边界 |
| R18：EN 657–696；CN 707–737 | complete | 配置错误、兼容接口卡住、慢搜索、安装和中文管道检查 | §12、§15–17 | A12、A15、A16、A17 | covered | 进入双语排障页，并覆盖语言切换问题 |
| R19：EN 697–721；CN 738–762 | complete | 开发工具链、测试、打包和 Skill parity | §12、§17 | A12、A17 | covered | 迁入开发文档，首页只留入口 |
| R20：EN 722–759；CN 763–800 | complete | v0.1.14 历史说明、稳定/测试发布和 CI 验证流程 | §12、§17 | A12、A17 | covered | 不再称 v0.1.14 为最新；历史保留到发行说明/开发指南 |
| R21：EN 760–770；CN 801–811 | complete | 致谢、Star History 与 MIT 许可 | §11–12 | A11、A12 | covered | 保留适用链接和许可信息 |
| D1：docs/desktop.md 全文 | complete | 安装、六页用途、配置草稿、CLI 解耦、活动/退出、更新/卸载 | §11–12、§17 | A11、A12、A17 | covered | 并入用户手册时处理入站链接，旧地址留简短入口 |
| S1：lieflat-less-ai-tone SKILL.md 全文 | complete | 白名单、事实保留、明确触发规则和中文成稿核验 | §11–12 | A11、A12 | covered | 用户明确授权重组；代码和英文不套用中文替换规则 |

# Non-goals

- 不安装 Codex 或 Claude Code 本体，不代登录账号或配置其模型服务，不自动配置 WSL/远程主机。
- 不强制安装 mise，不升级无关工具，不改写系统级运行环境、项目锁定环境或未知 CLI 来源。
- 不把 App 内置引擎作为本轮独立 CLI 的替代品，不建立后台驻留服务或通用软件商店。
- 不将文件存在、CLI 版本输出或 App 内搜索成功当作目标 AI 已加载技能并成功调用的证明。
- 本轮实现和测试不自动发布新版本或覆盖用户当前 App；交付方式在结果可审查后确定。
- 不增加 GitHub Wiki、独立文档网站或自动发布流程；手册唯一维护位置为仓库 `docs/guide`。
- 不翻译命令名、参数名、配置键、协议/JSON 机器字段及枚举，不翻译用户输入、搜索答案或网页原文。保留第三方原始错误/日志，外围解释使用所选语言。
- 首版只支持简体中文与英文；不改变搜索路由、服务商选择、API 合同或系统语言。

# Acceptance examples

全部可执行验收条件集中在 [完整规格](specs/desktop-environment-setup/spec.md) 的 Scenario 中。原十项环境准备验收继续保留；新增七项覆盖 README、双语手册、语言范围、偏好优先级、CLI、原生 App 与打包回归。

# Constraints and invariants

- 沿用原生 Windows/SwiftUI 和共享 Python 后端、现有 stdio 协议、CLI 来源识别、更新与 Skill 能力；不新增 UI 框架或 HTTP 管理服务。
- 安装由用户在 App 明确点击触发，执行前能看到缺少哪些组件及其作用范围；普通检测不得触发 npm wrapper 的隐式运行时修复。
- 只使用固定可信来源、确切版本和匹配系统架构的包；先校验后执行，不执行网络返回的任意脚本或命令。
- 更新 PATH/启动入口时只处理本功能拥有的当前用户项，不覆盖其他同名命令；不能用新进程检查推断已打开 AI 的环境已刷新。
- 不因排错而泄露密钥、完整环境、账号信息或任意安装脚本输出；不终止用户的 AI 或外部 CLI。
- 本机测试使用隔离目录与合成数据，保留原始工作区及真实用户安装。未执行的 Mac/ARM64 安装与 GUI 验证保持未验状态。
- 内容迁移前登记入站链接，迁移后修正当前消费者并检查断链；历史证据保持原样。完整技术细节移入手册，不凭精简删掉有效条件和兼容说明。
- 中英文切换不改动 Key、当前配置目录、搜索内容或活动任务；App 与独立 CLI 各自保存语言偏好，不增加相互运行依赖。

# Decisions

- 用户随后明确回复“确认，开始实现”，确认本次扩展后的 README、双语手册、App/CLI 语言切换及原环境准备完整范围。继续沿用当前测试工作区，保留 App 与 CLI 解耦；GUI 仍由用户手工测试。

- 用户于 2026-09-20 追加 README 重组及 App/CLI 中英文切换，并明确选择 `docs/guide` 双语手册、沿用刚才测试版目录，以及默认跟随系统/可手动切换/CLI 单次覆盖的范围。
- 同目录新建 change 被 Runtime 以 `workspace-isolation-required` 拒绝；为落实用户选择，使用当前 change 的 `revise-requirements` 扩展完整目标，保留旧环境准备实现与验收记录。没有另建工作区或提交旧改动。
- 文档与语言开关共同覆盖现有 App 配置和 AI 接入流程，保留一个 Native change，按文档、共享语言层、CLI、原生界面的顺序落实，避免多个子任务反复集成同一批页面和配置代码。
- README 主入口为 App，新手不用先学命令。说明最新资料、来源核对和读网页的具体用途，不宣称任何搜索都必须安装本工具，也不虚构对比成绩。
- 完整手册按 App 入门、CLI 参考、服务商与配置、研究/路由、排障和开发组织；英文 README 为仓库默认首页，与中文页相互链接，两种语言覆盖相同操作与限制。
- 用户指定的 lieflat-less-ai-tone 用于中文成稿清理；用户另行明确授权的章节重组和精简独立执行。英文按准确、自然、简短的要求写作，不把中文规则当作英文机械替换表。
- 继续由用户负责 GUI 手工测试；实现侧提供两种语言的预期界面和测试清单，执行必要的自动回归/构建，不恢复自动 GUI 测试。
- 现状核验确认 Web 配置页及 setup 向导已具备部分中英机制，优先复用；原生页面固定取 `*_zh`，完整 CLI 帮助和桌面后端提示仍未统一。已有偏好存储可复用，不增加翻译服务或 UI 框架。
- `utils.fetch_prompt` 写死 `Language: 中文`，与本轮已确认的“网页原文保持原样”冲突；将这一处改为保留原页面语言，其他抓取要求不扩张。界面语言不成为翻译搜索答案或网页正文的开关。
- 现有测试把完整 provider 链接/技术合同硬编码在根 README；迁移时将其核验对象改为手册并保留覆盖。npm/Python 当前不打包 docs，手册入口需使用分发场景可访问的链接，避免为纯文档迁移引入冗余运行时资产。
- 用户于 2026-09-20 明确回复“确认，开始实现，要保证app和cli解耦”，确认完整方案与全部验收项，授权进入 Build；解耦包括运行目录、启动依赖与 App 关闭/卸载后的独立可用性。
- 用户已确认首版只准备 Node、Python、Smart Search CLI 和接入文件，检测已有 AI 软件；不代装 Codex/Claude Code 本体。
- 用户明确要求 App 与 CLI 解耦：App 为环境管理入口，AI 使用独立 npm CLI。已有 App 内置引擎继续支撑 App 自己的功能。
- 用户无需理解或手动输入安装命令。健康的已有 Node/npm/Python 优先复用；mise 不是必须安装的组件，已有 mise CLI 沿用原管理器。
- 实现采用当前用户目录中的 Node 官方稳定 LTS archive；缺失 Python 时优先采用 uv 管理的 Astral CPython，uv 仅作为内部安装辅助，不要求用户另行操作。它不是 Python.org 官方二进制，详情须标明来源；必须用隔离实装确认 `venv`/`pip` 和 npm 安装链，不能假定兼容。若该合同不成立，先修复安装链，不能退回需用户手工命令或系统提权的流程。
- Codex 新接入使用当前官方用户目录 `.agents/skills`，检测已有 `.codex/skills` 中的历史副本并保留；Claude Code 使用 `.claude/skills`。文件差异提示为“内容不同”，不直接断言用户修改的版本过期。
- 完整目标保留既有 Windows/macOS 产品范围。实现与测试证据按平台/架构分别报告，不用 Windows 本机结果代替其他平台验证。
- 目标围绕同一环境状态和安装流程，保持一个 Native change，不拆为多个 Supervisor 子任务。
- 采用独立工作区 `codex/desktop-environment-setup`，基线 `d857e6b709f8f2da15f28340e99cae04bb8ae4c9`。本文件为用户已确认的完整方案。

# Open questions

本轮范围问题和全部十七项验收已获用户确认，正在实现与验证，没有待决的需求问题。

# Verification expectations

- 以现有测试工具覆盖真实状态分支和安装边界：无环境、已有兼容环境、版本过旧、损坏运行时、来源冲突、下载校验失败、安装失败、重试、重复操作、PATH 尚未生效和 Skill 内容不同。
- 用隔离的实际 npm 包安装验证 Node → CLI 包 → Python 私有环境 → Smart Search 的完整启动链；测试不得覆盖真实全局 CLI 或真实 AI 技能目录。
- 复用现有回归和两端构建入口，保留源码/产物对应关系。UI 重点验证步骤反馈、主操作、失败恢复、重启提示、窄窗和键盘可用性。
- 候选实现稳定后交给新的只读 Verifier 覆盖全部 Scenario；失败、阻塞和未运行分别记录。端到端 AI 调用未实际执行时保持待验证。
- README/手册核查中英主题与命令覆盖、配置键覆盖、Markdown 链接和 npm/Python 包中的入口可用性；不能让 npm 页面上的相对手册链接失效。
- 语言测试覆盖系统自动选择、显式覆盖、保存/读取、无效值、非交互帮助和报错、两种语言参数错误、JSON/内容不变、后端/原生界面与打包资源。App GUI 验收按用户选择交给用户，Mac/ARM64 没有宿主时仍明确列为未验。

## 核验依据（2026-09-20）

- [Node 官方 LTS 分发目录](https://nodejs.org/dist/latest-v24.x/)提供 Windows x64/ARM64 zip、macOS x64/ARM64 tarball 和 SHA256 清单；版本在实际安装计划中锁定，不把当前目录别名作为下载中的浮动版本。
- [uv 管理 Python 的说明](https://docs.astral.sh/uv/concepts/python-versions/#managed-python-distributions)明确 CPython 来自 Astral python-build-standalone；[存储说明](https://docs.astral.sh/uv/reference/storage/)定义可改写的用户目录。
- [Python Windows 嵌入包说明](https://docs.python.org/3/using/windows.html#the-embeddable-package)说明不含 pip，常规 pip 依赖管理不受支持；当前 `npm/scripts/postinstall.js` 必须创建 venv 并执行 pip，不能直接用嵌入 ZIP 替代。
- [OpenAI 官方 Skills 文档](https://learn.chatgpt.com/docs/build-skills)列出的用户目录为 `.agents/skills`；[Claude Code Skills 文档](https://code.claude.com/docs/en/skills)说明个人目录、自动发现与新建顶层目录后的重启条件。
- 已抽查 `skill_installer.py` 的当前固定路径和 `write_bytes` 覆盖行为；已有 status 只做文件比较，不是 AI 实际调用验证。现有桌面只读 CLI 探测绕开公开 wrapper 的自动修复，这一约束继续保留。
