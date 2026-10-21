# Outcome
执行用户提供的桌面界面修复计划：操作收到明确反馈，等待期间防止重复请求；配置界面恢复旧 Web 版的任务顺序与信息层次，并保留 Windows/macOS 原生交互和现有业务能力。

2026-09-20 追加已获完整实施授权：参考 codex-tweaks 的更新体验，实现自动检查、点击下载以及 App 和独立 CLI 分别更新；集成 cr-zhichen 四个 PR，并补齐可选推荐 JEV 的连续检索与研究证据约束。原 A1–A8 的历史通过记录保留，最终统一覆盖 A1–A19。

# Scope
Windows 和 macOS 的配置、概览、搜索、活动、AI 接入、设置页面；共享测试适配器与桌面显示元数据；相关回归和 Windows 原生界面验证。

追加范围：设置中的版本与更新入口、更新元数据/下载状态、平台安装包选择与校验、外部 CLI 来源识别及状态刷新、发布附件契约。Q1/Q2 已确定为提示后点击下载、点击后由原 npm/mise 管理器更新独立 CLI；用户已明确“按此完整范围实施并验证合并”。

## Source coverage
| 来源条目与位置 | 读取状态 | 需要保留的内容 | Spec 位置 | 验收 ID | 覆盖状态 | 理由或替代关系 |
| --- | --- | --- | --- | --- | --- | --- |
| S1 用户直接请求“现在准备执行修复计划” | complete | 按已提供的 0–8 优先级实施修复 | specs/desktop-ui-refinement/spec.md 全文 | A1–A8 | covered | 本轮实施授权；不把粘贴点评中的“先不改”当作用户当前指令 |
| S2 点评第二部分：测试语义、空 overrides、动态按钮名、健康记录承诺 | complete | 未编辑叫“测试”，有修改明确使用未保存内容；响应来源和记录边界准确 | 第 1 节 | A1 | covered | 当前桌面 worker 已显式 record_health=False；点评混用了 Web 路径，不按错误推断改变桌面健康写入策略 |
| S3 点评第二部分：探针/保存/预览/Skills/运行无等待反馈，可连点 | complete | 每类异步操作立即忙碌、同操作去重，后台任务保持至真实终态 | 第 2 节 | A2 | covered | 所有入口一起核验；切页和后台事件不解除防重复保护 |
| S4 点评第一部分：颜色、容器、主题语义、字号、Opacity、深色图标白底 | complete | 小规模主题资源、状态标签、卡片、主次文字；保留图标 | 第 3 节 | A3 | covered | 采用已有原生控件、资源和系统字体，不换技术栈 |
| S5 点评第一部分：920 居中窄列、活动宽度阶梯、等宽数据 | complete | 宽度和对齐一致，路径/键名/数值可读；窄窗可重排 | 第 3、4 节 | A3、A4 | covered | 以实际原生窗口检验，不只改常数 |
| S6 点评第一部分：closed/live/provider.test/timeout 等枚举、英文 argparse 帮助、冗长免责声明 | complete | 普通界面用中文结论与短解释，技术码留高级详情 | 第 5 节 | A5 | covered | 桌面文案改动不改 CLI help/JSON 契约 |
| S7 点评第一部分 macOS：sections order、tier、placeholder/default/capability_chains | complete | 消费已有元数据，基本配置先行，advanced 折叠，不丢字段 | 第 4、7 节 | A4、A7 | covered | 两端分组与显示事实相同；macOS 实机沿用后续单独验收决定 |
| S8 用户截图 codex-clipboard-44f6a402-995a-4054-821d-10336adc467b.png 全图 | complete | 三类基础能力、白色卡片/浅色底、表单主次、来源标签、更多设置 | 第 3、4 节 | A3、A4 | covered | 已查看；视觉与信息组织参考，迁移为桌面原生布局 |
| S9 用户截图 codex-clipboard-4e2a8d6c-70a7-46a6-9e4c-5a06b806ed90.png 全图 | complete | 服务商清晰分组、就地测试、次级帮助/链接、高级折叠 | 第 1、3、4 节 | A1、A3、A4 | covered | 已查看；保留现有安全保存/密钥规则，不恢复旧 Web 缺陷 |
| S10 点评中“计划文件”及数字统计 | complete | 提供的优先级表已完整作为输入，统计需源码核验 | 本 brief Decisions | — | background | 未提供单独计划文件；粘贴内容已足以执行，不猜测另一个文件的额外要求 |
| S11 用户追加“自动检查更新和下载最新的包……考虑到 app 版本和 cli 版本的更新，看看怎么做”及 Q1/Q2 答复 | complete | 分别识别 App/内置引擎、独立 CLI，自动查新；点击下载；点击后由原管理器更新 CLI 并验证 | Spec 第 9–12 节 | A9–A12 | covered | Q1/Q2 及完整方案已统一确认 |
| S12 D:/Dev/30_第三方项目/30_AI与MCP工具/codex-tweaks，HEAD 54cca44 | complete | 参考更新状态、版本比较、渠道、下载进度及平台安装机制 | 本 brief 调查证据 | — | background | 用户指定为实现参考，不把全仓功能、签名材料或全部依赖视作需求；已读基础文档并定向审查更新链路 |
| S13 PR #38 / issue #37 全文及差异 | complete | Markdown 标识符不截断，保留转义；覆盖长路径与 URL | Spec 第 13 节 | A13 | covered | 审查并纳入集成候选，补确定性长值回归 |
| S14 PR #42 / issue #41 全文及差异 | complete | 可选 mise 开发入口，工具版本与项目 venv 一致，npm 分发仍保留 | Spec 第 13 节 | A13 | covered | Windows 实际任务验证；不以版本存在代替任务运行 |
| S15 PR #40 / issue #39 全文及差异 | complete | Tinyfish 搜索与抓取共享 Key、配置/路由/错误/冷却/文档接入 | Spec 第 14 节 | A14 | covered | 保留原 PR 基础 search/fetch 范围；issue 的筛选/缓存批处理参数作为接口背景，不将未提供的高级选项宣称已实现 |
| S16 PR #44 / issue #43、docs/jev-routing.md 全文及实际代码 | complete | 可选 JEV 多渠道选择、证据判断、补搜、过滤和汇总三态，费用及边界准确 | Spec 第 15–18 节 | A15–A18 | covered | 保留来源并修正与当前桌面版、research 证据契约不兼容的部分 |
| S17 用户第一次 JEV 追加目标“完全取缔目前的路由机制” | complete | 由 JEV 接管默认并删除旧模式的早期方向 | — | — | superseded | 后续用户明确修正为 S18：可选并推荐，不强制其他用户配置 |
| S18 用户后续答复：JEV 可选、主要推荐；日常判断相关性/可用性并决定重搜或换引擎；Deep Search 自主组合；固定能力兜底；确认只有 4 组 | complete | 可选 JEV 的完整迭代流程与兼容行为；4 PR 验证合并并与更新功能推进 | Spec 第 15–19 节 | A15–A19 | covered | 用户提供的两项凭据仅作授权联调，不收录任何键值 |

# Non-goals
不改为 WebView、不重写业务引擎、不增加大型组件库。路由和 CLI 仅按已确认的 JEV/Tinyfish/mise 范围改动；真实 API 只执行用户授权的有限联调，不自动更改用户配置、全局 CLI/Skills 或覆盖本机安装。用户已授权 GitHub 合并；独立桌面正式发布/安装不由代码合并自动等同完成。

追加方案不包含静默安装、强制退出任务、自动降级、自动接入 beta、切换 CLI 管理器或批量升级工具。推荐沿用 Inno Setup/DMG，暂不迁移 Velopack/Sparkle 或自制整包覆盖/回滚器；按已确认的 Q2，仅在产品中的明确点击后调用已核实的原管理器。实现/本机安装/正式发布的授权仍分别处理。

# Acceptance examples
完整场景集中在 Spec 的 A1–A19；A1–A8 覆盖真实测试范围、忙碌与去重、视觉层次、元数据分组、中文文案、配置与结果保留、macOS 实现边界及 Windows 原生验证。

更新追加为 A9–A12；贡献、JEV 检索与合并为 A13–A19。全部范围已由用户一次确认，Runtime 已进入 Build。

# Constraints and invariants
基线为已发布 v0.1.19 对应 main 83b8b409。原工作区及历史 desktop-app change 保留；本轮独立 worktree/分支 codex/desktop-ui-refinement。保持协议版本 1，新增显示字段只做向后兼容扩展；有效配置、保存值、环境来源、密钥保留/显式清除、revision 冲突和活动隐私约定继续有效。

# Decisions
- 用户在本机 beta 测试中要求修复活动“模型未返回”、搜索结果外的裸来源链接、展开框随刷新周期抖动，并核查其他服务商。它们属于已确认 A3/A5/A6 的实现缺陷；保留原范围，继续 Build 修复。截图及随后粘贴的整段结果仅用作排错和渲染回归数据，不将其中新闻声明当作已核实事实。
- 非模型检索/抓取接口的活动不显示“模型未返回”；真正发起模型请求的探针记录实际请求的配置模型。阶段事件保留各自 provider/model，最终结果有明确主服务商信息时以其作为完成摘要，不把 Grok 模型附给 Exa 等补充来源。
- 活动行按 run_id 保留原控件和展开状态，周期刷新仅更新数据；来源链接收进有标题的结果区域并支持长标题换行。Firecrawl 仍是 presence 检查，按钮明确称“检查配置”；本次不新增或冒充真实鉴权/搜索/抓取探针。
- 用户已保存当前配置，并明确允许关闭当前测试窗口、启动修复后的隔离预览及自动验证。正式 0.1.20 发布继续等待用户本机测试确认，不因本轮修复自动发布稳定版。
- 用户已明确执行所贴修复计划。视觉方向由两张旧 Web 截图确定：任务顺序、紧凑字段、清楚的卡片与状态；不再询问已明确的样式方向。
- 先完成测试标签/范围和异步反馈，再统一样式及两端元数据消费。默认页面优先解释用户接下来要做的事，技术细节仍可展开查看。
- 核对实际链路后确认：桌面调用 Backend→独立 worker→service，已有 record_health=False；Web ui_api 的空字典合并为 None 是另一条路径。修复保持桌面测试只生成本次会话结果，不修改配置和正式健康记录；明确区分“当前有效配置”和“未保存修改”。
- 仅使用原生控件和小规模共享样式/函数，不引入新的 UI 框架或远程服务。状态标签同时有文字，颜色不独自表达结论。
- macOS 源码及模型测试一并修复，实际运行由用户后续单独验证；没有 macOS 执行环境时必须明确标注，不能以 Windows 结果替代。
- 检查采用隔离配置和本机模拟服务。用户已明确回复“没有，可以关闭当前 App 并验证新版”，允许在原生验证时关闭当前窗口并切换测试版。
- 用户追加的更新需求接入同一 change，并返回 Shape；这不代表上一轮结果已接受，也不授权现在升级本机或发布新版本。
- Q1 已确认：App 自动检查发现新版后提示，用户点击才下载；下载后仍须明确安装动作，不自动退出或安装。
- Q2 已确认：CLI 已明确识别为 npm 或 mise 安装时，用户点击更新后由 App 调用原管理器并验证结果；未知来源只提供说明。
- 后续确认：本次仅有 cr-zhichen 的四组贡献；授权验证、修复必要集成问题并合并 GitHub。更新功能及前述桌面修复一起集成，保留朋友提交的可追溯历史。
- 后续修正：JEV 是可选且推荐的模式，不删除 hybrid/rules/off，也不强迫未配置用户迁移。选择 JEV 时的故障或无合适选择，按已配置/允许能力进行固定兜底并标记降级，不调用旧 embedding/classifier 来掩盖失败。
- 后续目标：JEV 负责语义选择、相关/有用/充分性判断及下一步决策；程序仍负责可执行动作白名单、预算、取消、冷却及证据归属。JEV 的 Noul/Choice/Score 不生成自由文本查询；新检索词先复用现有研究计划与有限缺口候选，再由 JEV 选择。持续组合受显式预算约束，不实现无限无终止循环。
- 新增测试凭据均已收到并通过基础真实接口验证，仅暂存于工作区外 Windows 用户加密文件，测试结束清除。真实 Grok 仍返回额度耗尽；不静默换模型或据此认定 PR 失败。
- Supervisor 检查结论：保持单个 change。两端共用更新事实、下载状态和 CLI 来源判断，验收依赖同一协议和发布契约，拆成独立子任务会增加集成和版本一致性成本。
- App 与其内置引擎作为同一安装单元；独立 CLI 按实际安装来源处理。版本数字偶然相同不证明两者已一起更新，App 更新不覆盖独立 CLI。
- 已确认方案：App 运行时启动后后台检查，之后最多每 24 小时检查一次，可关闭；提供即时手动检查。稳定版优先，检查失败保留最后成功结果并标注时间/失败，不误报“已是最新”。
- 已确认方案：共享 Python 核心统一版本比较、来源判断和下载元数据，两端原生界面呈现相同事实；下载采用已有 httpx、hashlib 和原生文件/安装器入口，不引入新的更新框架。
- 已确认方案：下载完整官方安装包，显示真实进度、可取消和重试，先写临时文件、校验完整性后才提供安装；Windows 启动现有当前用户安装器，macOS 打开已验证的 DMG。需要无人值守替换、差分或自动回滚时再单独评估 Velopack/Sparkle 迁移。
- 已确认方案：外部 CLI 只读识别管理器/有效路径/版本，优先支持现有 npm 和 mise npm；未知、项目虚拟环境、开发检出或多来源冲突只提供定位与手动建议，不猜测升级命令。

## 调查证据与方案依据

- Smart Search `src/smart_search/desktop_backend.py:387–395` 只读 GitHub `/releases/latest` 并返回 tag 和总发行页；Windows `MainWindow.xaml.cs:977–996` 用字符串不相等判断更新，没有资产、下载、版本大小或架构判断。
- `desktop_backend.py:119–170,383–384` 缓存 CLI 检测且手动刷新不失效；安全探测刻意避开可能修复安装的 npm wrapper，这一约束要保留。现有代码没有 mise shim 专用解析。
- 本机只读检查独立 CLI 当前为 mise 管理的 `@konbakuyomu/smart-search@0.1.19`，直接 npm .CMD 和 mise shim 都存在。不能照抄旧会话的 0.1.18 结论；界面必须重新解析实际生效路径。
- 2026-09-20 GitHub API 读回 v0.1.19 为非 prerelease，资产只有 Windows x64 未签名安装器（76,831,938 字节）与 SHA256SUMS.txt；安装器 SHA256 为 `263f8e99c916e563b25a7497bbee48eeb874ebe20151f751d7b06cfbab45ba8a`。npm Registry 的 latest 为 0.1.19。检查未下载安装或执行更新。
- `publish-npm.yml:147–179` 自动创建 Release；`desktop-build.yml` 仅上传短期 CI 产物。npm 发布成功不能证明任一桌面架构的安装包已上传。App 查找最新兼容、附件齐全的稳定发布；若存在更新 tag 但目标架构包尚未就绪，单独说明。
- 参考仓库 `backend/internal/core/controller_update.go:8–56` 有检查去重、成功时间、跳过版本；`windows/CodexTweaks.Windows/Services/VelopackUpdateService.cs:16–68` 把检查、真实进度和应用重启分开。`scripts/package-windows.ps1:43–86` 配套 `.nupkg`、架构/渠道 feed 和 Setup。
- 参考仓库 `app/Resources/Info.plist:40–53` 与 `app/Sources/SparkleUpdateController.swift:37–73` 使用 Sparkle、EdDSA 和签名 feed，关闭自动下载/安装；`scripts/package-sparkle-update.sh` 和 release workflow 配套签名归档和 appcast 分支。当前 Smart Search 缺少这套发布基础，不能只复制按钮或下载类。
- 参考实现的 Windows 下载使用 CancellationToken.None，且有两套版本检查；不直接继承其不可取消下载或展示/可安装版本可能不同步的结构。参考仓库构建脚本中的递归清理也不复制。
- 官方依据：[Velopack 集成](https://docs.velopack.io/integrating/overview) 要求启动集成与专用安装布局/feed；[Sparkle 文档](https://sparkle-project.org/documentation/) 要求正确 appcast 和更新签名；[mise upgrade](https://mise.jdx.dev/cli/upgrade.html) 会受版本范围和配置影响，须指定单个工具，不能把不带工具参数的批量升级当作 CLI 更新。

# Open questions
Q1–Q5 均已明确：点击下载、原管理器显式更新 CLI、已提供 TypeSafe 联调凭据、JEV 固定能力降级、仅四组 PR。完整追加范围已由 Runtime 保存确认，没有待回答的行为问题。

## 2026-09-20 追加贡献与 JEV 调查

- 用户明确授权：验证并合并 cr-zhichen 提交的 PR/issue；Tinyfish/JEV 使用用户提供的凭据进行受控验证；JEV 作为可选推荐模式用于日常路由及 Deep Research，结合渠道专长选择；与自动检查/点击下载、显式 CLI 更新一并推进。凭据不进入任何正式产物。
- 已核对 GitHub API 作者与 head：#38 `5bfb6c6fe2815bbee4ba98985767bc034ed54e48`，#40 `425dda4a95ee93c0fabe57fca7c68b0352fdc74d`，#42 `3c8f0140991dc590f967accc4568acac341c61d2`，#44 `561f374a9f9b5bfe79aa910f32b27ab3390e7171`。全部 PR/issue 正文已读取；#40/#44 与当前 main 存在合并冲突，需集成修复后验证，不能直接认作可合并。
- JEV PR 保留 hybrid/rules/off，默认仍是 hybrid，故“让 JEV 接管默认日常路由”属于用户追加目标，不等同原 PR 本身。`docs/jev-routing.md` 已完整读取，实际实现及全量回归正在核验。
- TypeSafe 官方 API 使用独立 `TYPESAFE_API_KEY`、`jev-latest` 和 `/v1/systemone`；Noul 是命题为真的概率，Score 才是按等级标准评分，不能把二者或渠道偏好权重混为一谈。来源：https://docs.typesafe.ai/api 与 https://docs.typesafe.ai/primitives/noul。
- 初始只读检查 TypeSafe 未配置，后续用户提供了凭据并完成真实判断；Tinyfish search 返回 3 个结果、fetch 成功获取 Python 官方文档。全局 doctor 的主模型请求返回 HTTP 402 额度耗尽；不以此判定 PR 实现失败。凭据仅作授权测试，不在这里复制。
- 四 PR 已在独立 `codex/contributions-check` 合并本地候选，保留原分支未提交界面改动。第一轮完整 Python 测试 769 passed、3 failed、1 POSIX skip；失败均为 16 个新增配置缺 UI 元数据，待修复。
- 独立源码审查发现：JEV 多轮会换渠道但原查询不变、同引擎不能按缺口再搜；JEV research 绕过旧计划/抓取证据/报告字段；过滤后可能沿用过期充分性判断；selection 耗尽时间仍可派发请求；route 的无网络承诺与 JEV 远程判断冲突。以上均在集成验收中处理，不按原 PR 的 Mac 测试通过声明跳过 Windows 和桌面回归。
- 用户提及“Context.ai 查文档”按本项目实际 Context7 文档渠道理解；Exa 偏新闻、Grok 偏通用是用户期望的渠道使用偏好，不硬编码成服务商仅有能力。

# Verification expectations
共享 Python 相关回归与全量检查；Windows 构建及原生浅/深色、窄/宽窗、延迟探针、连点、失败恢复、切页/保存等验证；macOS 模型测试按可用环境执行并单列未验范围。最终由新的只读 Verifier 核对全部 A1–A19，保留失败与阻塞，不把源码/构建当实机通过。

更新实现确认后补充：合成 GitHub/npm 响应与本地下载服务器覆盖新旧版本/缺包/错架构/离线/限流/取消/哈希错误；隔离安装升级及 CLI 管理器测试替身验证目标和结果读回，不能拿真实全局安装做单元测试。macOS 下载/DMG 与安装体验按可用平台单独验证，未做的部分保持未验。
