---
generated_from_state_version: 28
---

# 验证

## 当前结果

- 结果: **已归档**
- 验证情况: **已完成检查，验证结果已确认**
- 目标周期: 4
- 迭代: 2
- 验证器尝试次数: 1
- 完成时间: 2026-09-20T15:25:38.302Z
- 摘要: 当前 Runtime 本地状态将 9 项通过收据绑定到 candidate 13482a77-2a7b-494d-95ec-7a9681c05488、stateVersion 22、同一 verificationRoot 和 verifier execution。A1-A15 的既有独立证据未被仅限 macOS 资源交付的修复失效；A16/A17 的确定资源缺失已由当前源码和 Runtime 静态打包合同修复。17 项均通过，但 macOS 原生安装、GUI 和真实 AI 调用保持明确未验边界。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | specs/desktop-environment-setup/spec.md | 检测准确且无安装副作用 在无环境、兼容版本、过旧版本、失效命令、Python 不支持 venv/pip、CLI 运行时缺损和检查超时的输入下，状态与后续动作准确；仅有 AI 配置目录不显示 AI 本体已可用。连续检测不下载、不创建 CLI 私有运行时、不安装技能、不修改 PATH 或配置。 | 上一轮独立结论的只读检测/无副作用覆盖仍有效（tests/test_desktop_environment.py:35-72）；本轮 Runtime 的 distribution-source-shebang-normalization 在当前候选核对 74 个 npm/Python/Skill 源文件与已安装 payload 一致，修复未触及该路径。 |
| A2 | passed | specs/desktop-environment-setup/spec.md | 干净环境可准备独立 CLI 隔离且最初没有 Node/npm、Python、Smart Search CLI 的环境中，用户一次确认安装计划后完成依赖与 npm CLI 安装。实际启动链使用独立目录中的组件，读回正确 CLI 版本；App 程序目录不可用时独立 CLI 仍可运行。重复安装不重复下载或制造同名副本，已验证组件保持可复用。 | 隔离实装收据 .desktop-artifacts/environment-smoke-20260920/result.json 保留 Node v24.21.0、Python 3.13.15、独立 CLI 0.1.20、external_runtime_verified=true、independent=true；本轮 frozen-environment 对同一 Windows 构建再次读回独立 CLI、Node 和 Python，exit 0。 |
| A3 | passed | specs/desktop-environment-setup/spec.md | 复用已有安装且保护来源 普通 npm、全局 mise、本功能拥有的用户目录、项目锁定和多来源冲突分别得到正确计划；健康项不重装，更新只针对 Smart Search 并使用原管理器。未知来源、权限不足或计划后来源变化不会被强改，也不会通过另建副本伪装解决。原环境和其他命令保持可用。 | 上一轮独立核验的来源识别/冲突拒绝及 npm 所有权回归保持有效（src/smart_search/desktop_cli.py:101-187；src/smart_search/desktop_environment.py:283-303；tests/test_desktop_environment.py:183-196）；本轮当前 npm/Python payload 一致性收据未发现修复后的漂移。 |
| A4 | passed | specs/desktop-environment-setup/spec.md | 安装失败不会产生虚假成功或破坏原环境 网络中断、摘要/大小不匹配、错误架构、越界归档、无写权限和 npm/Python 安装非零退出均停止依赖步骤并显示原因；错误包不能执行。重试复用已成功组件，日志不含合成密钥；未完成临时内容不会被当作可用安装。 | 上一轮已以当前产品实现的受信下载、摘要、大小、归档边界和失败回归判定通过（src/smart_search/desktop_environment.py:85-153、410-441、628-632；tests/test_desktop_environment.py:117-167、211-218）；本轮仅修复 macOS 资源交付，不影响该证据。 |
| A5 | passed | specs/desktop-environment-setup/spec.md | 调用入口与重启提示符合实际 在 PATH 最初缺失、App 运行期间被修改、同名命令冲突、路径含空格/中文，以及 macOS GUI 与 shell PATH 不同的情况下，能区分独立 CLI 本身可用与外部命令可达。接入指向被验证的独立入口，旧进程环境需要重启时明确提示，用户其他 PATH 项和命令不受覆盖。 | 上一轮验证的仅追加本功能拥有 Windows prefix、重开进程提示和既有 launcher/PATH 保护仍有效（src/smart_search/desktop_environment.py:534-573；tests/test_desktop_environment.py:221-250）；本轮 frozen-environment 对当前 Windows 构建仍通过。 |
| A6 | passed | specs/desktop-environment-setup/spec.md | 只配置所选 AI 且保留个人内容 在接入缺失、完全一致、自定义修改、额外文件、自定义根目录和历史重复目录的隔离样例中，检测与写入目标正确。未选 AI 不被修改；自定义内容未经明确替换不被覆盖，选择替换有可恢复副本；接入引用的命令/路径在准备环境中实际有效。 | 目标限定、内容不同默认保留、显式替换备份和额外文件保留的已验实现未变（src/smart_search/desktop_environment.py:499-532；tests/test_desktop_environment.py:76-97）；当前分发源核对未发现 Python/npm 漂移。 |
| A7 | passed | specs/desktop-environment-setup/spec.md | 就绪状态不夸大验证范围 覆盖环境正常但 Key 缺失、CLI 版本读回错误、技能文件就绪但 AI 不存在、AI 未重启、AI 尚未实际调用等情况；每层状态独立且解释清楚。验证不发收费请求，不修改配置，不因 App 内置搜索成功显示目标 AI 已验证。 | 分层环境/CLI/接入/AI 调用状态实现与隔离收据仍有效（src/smart_search/desktop_environment.py:313-330、353-370；.desktop-artifacts/environment-smoke-20260920/result.json）；本轮 frozen-environment 仍把 AI invocation 保留为 not-run，未夸大为实际调用通过。 |
| A8 | passed | specs/desktop-environment-setup/spec.md | 两端反馈持续且避免冲突操作 慢速安装期间连点只触发一次操作，切页返回仍显示实际阶段；失败、断开和重试状态真实。用户不能在写入期间误触另一 CLI 安装/更新或 App 安装；窄窗与键盘操作可访问主要按钮，状态同时有文字而非只用颜色。 | 检查合并和写入期间冲突操作拒绝的既有回归仍有效（tests/test_desktop_environment.py:56-72、198-207）；本轮修复不触及环境操作或原生交互逻辑。GUI 手工范围在风险中保留。 |
| A9 | passed | specs/desktop-environment-setup/spec.md | 准备环境不改变配置及原功能 安装和验证前后共享配置、草稿、真实/合成密钥和其他服务商设置不被改写；App 内置功能及独立 CLI 既有入口回归通过。显式配置目录与默认目录不同会得到准确提示，而非误称已同步。 | 本轮 frozen-language Runtime 收据对当前 Windows 构建报告 configuration_unchanged=true、windows_staged_source_matches=true、resource_matches_source=true；上一轮配置与原功能回归证据未被本次 macOS 文件修改失效。 |
| A10 | passed | specs/desktop-environment-setup/spec.md | 验证结果可追溯且平台边界准确 最终候选包含上述关键分支的可运行测试、实际执行结果和构建对应关系；另有新的只读 Verifier 判断全部场景。未执行的 Mac/ARM64 原生安装与真实 AI 调用明确列为未验，不以 Windows 或替身结果宣布全部平台通过；交付前用户原安装和配置保留。 | 当前 Runtime state.json 绑定 candidateId、stateVersion=22、同一 worktree 和 9 项 exit 0 收据；规格明确要求 macOS/ARM64 原生安装与真实 AI 调用未运行时单列未验（spec.md:99-105、181-185），本结果及风险遵守该边界。 |
| A11 | passed | specs/desktop-environment-setup/spec.md | README 能让新用户找到并完成第一步 两种语言的 README 都能在首页直接回答用途、场景、下载配置和日常使用问题，主要配置流程不要求输入命令；技术长表和长 JSON 已迁出。中英入口互通，下载与手册链接可用；最低配置、费用触发和证据边界准确，不把开发分支功能误标为已发布稳定包能力。中文成稿已按指定规则复核。 | README 双语入门结构的上一轮独立核验保持有效（README.md:19-72；README.zh-CN.md:19-72）；当前 Runtime language-repair-regression 对 tests/test_guide.py 与 tests/test_i18n.py 通过，34 passed。 |
| A12 | passed | specs/desktop-environment-setup/spec.md | 手册完整且迁移不造成断链或信息遗漏 来源覆盖表中的有效技术信息在双语手册中都有明确去处；全部公开 CLI 命令/参数和配置键与当前实现对应，中英主题和限制等价。检查 README、现有文档、Skill 及包元数据引用后没有新增本地断链，npm/分发入口使用可解析的手册链接。旧版本说明不再误标最新，未发布功能有清楚边界。 | 手册从当前 parser/CONFIG_FIELDS 生成并逐字核对的实现未变（scripts/generate_references.py:14-67；tests/test_guide.py:10-32）；本轮 34 项语言/手册回归和 9 个 public/packaged Skill parity 均通过。 |
| A13 | passed | specs/desktop-environment-setup/spec.md | 中英文覆盖本工具文案且保留用户和机器内容 中文和英文状态下，主要流程以及失败/恢复路径都使用对应语言，后端生成的文字与界面语言一致。静态检查或覆盖清单能识别遗漏的产品字符串。对相同固定输入和模拟服务响应，机器字段、枚举、命令、配置键、用户文本和搜索正文保持一致；抓取提示不再强制中文，而是要求保留页面原语言。第三方原始日志允许保留原文并能被辨识。 | 当前 Runtime 同时验证 Python/分发源、Windows 冻结协议、已编译 C# 双语嵌入资源及占位符；上一轮 i18n 覆盖和原页语言保留实现仍有效（src/smart_search/i18n.py:17-135；src/smart_search/utils.py:79-82）。 |
| A14 | passed | specs/desktop-environment-setup/spec.md | 自动语言与显式偏好按约定生效 覆盖中文/英文/其他/未知系统 locale、旧配置缺字段、保存后重启、环境覆盖和单次参数覆盖。App 与 CLI 的选择互不篡改，CLI 单次 `--lang` 不写文件；无效值明确失败或按规定安全回退。语言操作前后 Key、provider 设置、配置目录、PATH 和其他用户数据保持不变。 | 语言优先级与持久偏好的已验实现未变（src/smart_search/cli.py:3834-3885；tests/test_i18n.py:24-71）；本轮 tests/test_i18n.py 仍在 current-candidate 34 passed 收据中。 |
| A15 | passed | specs/desktop-environment-setup/spec.md | CLI 帮助向导和失败输出可以切换且脚本兼容 以中文和英文分别运行总帮助、多级子命令帮助、有效/无效参数、只读配置/诊断、无 Key 的离线命令及向导关键分支，能看到相应语言并维持原行为。无 TTY/JSON 管道、UTF-8 中文路径与 `--version` 正常；现有 `ui --lang zh/en` 仍可用且优先级明确。 | 多级帮助、参数错误、JSON/用户内容边界的既有 i18n 回归保持有效（tests/test_i18n.py:74-92）；当前 frozen-language 收据再次验证 en/zh 帮助和协议，且真实 npm 安装源与当前源一致。 |
| A16 | passed | specs/desktop-environment-setup/spec.md | 两端 App 可切换语言并保留当前工作 检查 Windows/macOS 的导航、服务商、搜索/研究、活动、AI 接入、设置、安装更新和失败确认路径的双语文案；切换并重启后选择保持，草稿/任务/配置不丢失。最小窗口和键盘主要操作可用。自动化验证模型/协议与 Windows 构建；GUI 按用户要求提供测试清单由用户操作，未实际执行的目标平台明确标记未验。 | 前次确定缺陷已闭环：desktop/macos/Sources/SmartSearchDesktop/Localization.swift:14-20 优先从安装 App 的 Bundle.main 读取 Localization.json，仅以 Bundle.module 作 SwiftPM 开发/测试回退；desktop/scripts/build-macos.sh:121-139 对 arm64/x86_64 共用装包链把 canonical src/smart_search/assets/i18n/messages.json 复制至 Contents/Resources/Localization.json，并以 cmp 失败即停。两份 JSON 当前 SHA-256 相同（00474B...EF53E）；Runtime macos-language-contract 已通过。实际 macOS GUI/安装仍明确未验。 |
| A17 | passed | specs/desktop-environment-setup/spec.md | 语言和文档的最终产物可追溯且原功能回归通过 最终候选具有文档/链接检查、双语覆盖与语言优先级回归、原环境准备/CLI 合同回归，以及包含语言资源的 npm/Python/Windows 打包检查。独立 Verifier 覆盖扩展后的全部验收。交付说明区分源码、测试包、用户 GUI 反馈、真实 AI 调用和各平台结果，没有未经授权的发布或原安装覆盖。 | 当前候选具备文档/语言回归、npm/Python/Windows 分发与资源核对、原环境合同回归和独立 Verifier；此前 macOS 分发缺资源已由 build-macos.sh:126-127 的 copy+cmp 及 Localization.swift:16-17 的 installed-bundle 优先读取修复。Runtime state.json 显示所有 9 项当前候选收据 passed，且修复文件时间 15:06 早于收据运行时间 15:10。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| npm bootstrap and locale contract | npm/scripts/test-wrapper-repair.js | . | passed | 0 | 334 ms |
| Public and packaged Skill parity | npm/scripts/check-skill-parity.js | . | passed | 0 | 312 ms |
| Windows frozen language protocol, CLI help and resource/source parity | .desktop-artifacts/check_packaged_language.py | . | passed | 0 | 761 ms |
| Windows frozen independent environment readback | .desktop-artifacts/check_packaged_environment.py | . | passed | 0 | 2484 ms |
| Compiled Windows locale and placeholder behavior | run --no-build --project .desktop-artifacts/native-language-check/check.csproj | . | passed | 0 | 996 ms |
| Git whitespace check | -c core.safecrlf=false diff --check | . | passed | 0 | 98 ms |
| Affected language and handbook regression | -m pytest tests/test_i18n.py tests/test_guide.py -q --tb=short | . | passed | 0 | 2129 ms |
| macOS packaging syntax and app resource path contract | .desktop-artifacts/check_macos_language_contract.py | . | passed | 0 | 126 ms |
| Installed npm source parity with exact executable shebang normalization | -B .desktop-artifacts/check_distribution_sources.py | . | passed | 0 | 93 ms |

### Builder 报告的证据

以下为 Builder 报告，不等同于 Runtime 检查凭据或独立验收结果。

- Affected language/document regression: passed — 34 passed in1.37s. Git Bash syntax validation passed. Native macOS build not executed on Windows.
- Existing full regression and distributions: passed — Previous bound full suite893 passed1skipped; unchanged Python/npm/Windows sources verified against real npm install and staged Windows source/resources. Existing Windows package SHA and source paths unchanged.
- macOS native and GUI: not-run — Code-level resource omission fixed. Actual macOS x86_64/arm64 builds/installations and user-owned GUI remain unexecuted, not promoted to pass.
- 已知限制: macOS x86_64/arm64 native build/install/resource lookup not run on this Windows host; CI build now includes required cp+cmp guard.
- 已知限制: GUI checks remain user-owned; no automated GUI, real target-AI call, commit/push/publish or installed-App replacement.
- 已知限制: Historical distribution-source failure was an exact shebang-line-ending comparison false positive; corrected explicit Runtime check passed and all other file bytes matched.

## 阻塞项

_无。_

## 风险与跳过的工作

- macOS x86_64/arm64 原生构建、DMG/已安装 .app 的 Bundle.main 实际资源查找尚未在 macOS 宿主执行；本轮通过的是源码、Bash 语法和资源路径合同，不能表述为真实 macOS 安装通过。
- Windows/macOS GUI、最小窗口和键盘手工检查仍由用户负责，未执行；源码/协议收据不能代替可见界面验收。
- 真实 Codex/Claude Code 调用未执行；当前结论仅覆盖本地环境、CLI、接入文件与语言资源，不把它们当作收费 AI 调用成功。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 0 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-20T11:31:51.809Z |
| 2 | 1 | 1 | fail | A5 | 候选的 9 项验收成立，但 A5 会把复用的外部 Node 目录写入用户 PATH，违反 PATH 所有权约束；应回 Build 修复后重新验收。 | 2026-09-20T12:36:58.429Z |
| 2 | 2 | 1 | pass | — | 本轮仅修复的 A5 已由源码、隔离回归、后续 Windows 构建和打包独立验证交叉确认；A1–A10 均满足。未执行的平台与真实 AI 调用已按规格明确保留为未验边界。 | 2026-09-20T12:49:42.894Z |
| 2 | 2 | 1 | recovery | — | 用户明确要求在当前测试版目录继续扩展：精简中英文README，将完整CLI与配置指南集中到docs/guide，App和CLI默认跟随系统并可切换中文/English；保留已核验的独立环境准备功能 | 2026-09-20T12:55:13.283Z |
| 3 | 1 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-20T14:40:11.871Z |
| 4 | 1 | 1 | fail | A16, A17 | A1–A15 由当前源码、绑定运行收据和针对性测试支持通过；A16、A17 因 macOS SwiftPM Localization.json 未被 build-macos.sh 复制进 .app 而失败。旧 distribution-source 失败是已核实的 shebang CRLF/LF 误报，新的唯一补充检查已通过，但不影响 macOS 分发缺陷的 fail 结论。 | 2026-09-20T15:05:42.022Z |
| 4 | 2 | 1 | pass | — | 当前 Runtime 本地状态将 9 项通过收据绑定到 candidate 13482a77-2a7b-494d-95ec-7a9681c05488、stateVersion 22、同一 verificationRoot 和 verifier execution。A1-A15 的既有独立证据未被仅限 macOS 资源交付的修复失效；A16/A17 的确定资源缺失已由当前源码和 Runtime 静态打包合同修复。17 项均通过，但 macOS 原生安装、GUI 和真实 AI 调用保持明确未验边界。 | 2026-09-20T15:25:38.302Z |



## 结论

当前 Runtime 本地状态将 9 项通过收据绑定到 candidate 13482a77-2a7b-494d-95ec-7a9681c05488、stateVersion 22、同一 verificationRoot 和 verifier execution。A1-A15 的既有独立证据未被仅限 macOS 资源交付的修复失效；A16/A17 的确定资源缺失已由当前源码和 Runtime 静态打包合同修复。17 项均通过，但 macOS 原生安装、GUI 和真实 AI 调用保持明确未验边界。
