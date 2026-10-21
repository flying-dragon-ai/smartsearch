# 社区贡献、JEV 和桌面更新集成验证

2026-09-20。集成候选为 `codex/desktop-ui-refinement`，PR [#47](https://github.com/konbakuyomu/smartsearch/pull/47)。本报告区分源码/模拟检查、真实服务样本、原生交互和发布结果；最终合并状态以报告末尾及 GitHub 读回为准。

## 贡献和集成

| 贡献 | 核实的作者与 head | 集成处理 |
| --- | --- | --- |
| #38 / #37，Markdown 长标识符 | cr-zhichen，`5bfb6c6` | 保留路径/URL；补配置值表格与确定性长值回归，保留转义 |
| #40 / #39，Tinyfish | cr-zhichen，`425dda4` | 保留 search/fetch；接入当前桌面字段与共享探针，双能力验证、超时及逐 URL 错误分类 |
| #42 / #41，mise | cr-zhichen，`3c8f014` | 原工具固定版本保留；修复 Windows cmd 的解释器路径引号，CLI/Python 原样参数转发、检查覆盖 src/tests |
| #44 / #43，JEV | cr-zhichen，`561f374` | 保留可选路由及汇总三态；补新查询候选、偏好输入、正文研究证据、过滤后复核、到期停止与明确降级 |

合并提交保留四个原始 head 的祖先关系。原工作区的无关未提交文件未参与集成。早期原生配置修复仍见 [原生 UI 验证报告](desktop-ui-refinement-validation.md)。

## 可复核检查

| 检查 | 结果与边界 | 本机证据 |
| --- | --- | --- |
| Python 3.12 全量 | 834 passed，1 POSIX 平台 skip | `.desktop-artifacts/integrated-updates-pytest.log` |
| 后续完整 Runtime 回归 | 837 passed，1 POSIX 平台 skip；取消修复及 JEV 边界回归已纳入 | `.desktop-artifacts/native-updates-dispatch2.json`、`runtime-repair2-receipts.json` |
| npm 实际安装及测试/打包 | 834 passed，1 skip；包含包内容与 Skill 镜像验证 | `.desktop-artifacts/npm-install-updates.log`、`npm-test-updates.log` |
| mise 隔离 Python 3.13.14 | install、python/CLI help 参数转发、check、parity、test 均执行；834 passed，1 skip | `.desktop-artifacts/mise-interpreter.log`、`mise-*-help.log`、`mise-check.log`、`mise-parity.log`、`mise-test.log` |
| 后续定向回归 | JEV、更新管理器、包下载和 Tinyfish：116 passed | `.desktop-artifacts/final-focused-tests.log` |
| Windows x64 本机构建 | 原生编译 0 warnings / 0 errors，隔离预览 publish 成功 | `.desktop-artifacts/windows-updates-preview-build.log` |
| 桌面 CI 首轮 | Windows x64/ARM64、macOS Intel/ARM64 的构建/打包通过，macOS 模型测试通过；发行上传 job 按 PR 模式跳过 | [run 35494792485](https://github.com/konbakuyomu/smartsearch/actions/runs/35494792485) |

首次 mise 安装失败是 cmd 解析未加引号的 `.venv/Scripts/python.exe`；修复引号后成功。第一次 3.13 全量因验证副本漏复制品牌资源和 `.github` 文件产生 5 个缺文件失败，补全测试输入后全部通过。首次 PR CI 发现 Tinyfish 测试文件末尾多余空行，已修复；不是忽略检查或把失败计为通过。

## 真实服务样本

Tinyfish search 返回 Python 官方 asyncio 页面等结果，fetch 取得该官方页 47,607 字符正文。TypeSafe 返回合法 `jev-1.13.0` 判断和真实用量；单个文档问题上 Context7 适用概率最高。它们证明接口与样本通路，不证明整体路由质量。

增强后的端到端样本只配置用户授权的 Tinyfish/TypeSafe，关闭最终主模型汇总，使用独立配置/证据目录。最近一轮日常检索约 13.8 秒、5 次 JEV 调用，返回有用结果且未降级；研究约 14.5 秒、5 次 JEV 调用，实际读取 2 份正文，返回报告/引用。研究充分性低于阈值，按轮数上限结束并标记未解决缺口，不能描述为完整充分的研究结论。日志：`.desktop-artifacts/jev-live-integration.json`；正文/计划在 `live-research/`。

本机现有 Grok 返回 HTTP 402 额度耗尽，与接口和离线验证分开记录；没有更换用户模型来掩盖失败。真实凭据不在仓库、报告或示例中，仅用于有限联调。

## 更新后端与原生交互

后端测试使用合成官方元数据、本机 HTTP 流式下载服务器和实际隔离管理器子进程，覆盖：稳定版本比较、错架构/缺包、SHA256 清单、可信重定向、重复检查/下载、取消重试、错误大小/哈希、打开前重新校验、自动检查开关/24 小时节流、npm/mise 所有权、复杂选项/冲突来源拒绝、单包确切参数、失败与实际版本读回。识别不会运行可能自动修复运行时的公开 CLI wrapper；更新成功还要求私有运行时真实版本可验证。

真实只读发行检查从现有 v0.1.19 找到 Windows x64 安装器与匹配 digest：模拟 App 0.1.18 时可更新；独立 CLI 0.1.19 不误报更新。它没有下载安装该公开包。记录为 `.desktop-artifacts/public-update-check.json`。

Windows 原生预览使用独立 `SmartSearch.UpdatePreview` 程序、合成版本 App 0.1.18 / CLI 0.1.19 / 目标 0.1.20，以及仅写证据目录的管理器/安装器替身。已完成：

- 更新检查双击只产生一次检查 RPC、一次 GitHub 元数据请求和一次 npm 请求；按钮即时显示“检查中”并禁用。
- App 与内置引擎、独立 CLI 版本分别显示，不把 CLI 目标版本当成 App 已升级。
- 下载双击只发一次请求，显示真实累计字节；取消后恢复下载操作，安装入口保持不可用。
- 重试后完整包通过大小/SHA256 校验，显示“已下载并校验；尚未安装”，才启用安装入口。

记录：`.desktop-artifacts/update-preview-requests.jsonl`、`update-ui-evidence/checking-busy.txt`、`download-busy.txt`、`download-cancelled.txt`、`download-ready.txt`、`download-ready.png`。下载就绪的截图对应主流程，最后补充的请求期关闭保护由源码/编译与测试核验。

用户按物理 Esc 停止 Computer Use 后，停止了一切原生输入。CLI 确认后的界面执行、安装器启动，以及本轮新增更新卡片的浅色/窄窗检查未继续执行；不能拿已有单元测试冒称完成这些手动操作。管理器和下载 API 的隔离测试已完成。未升级本机 App、未更新全局 CLI、未改真实服务配置。

## 发布和剩余边界

桌面 workflow 增加显式 `release_tag` 的完整四平台附件/校验清单发布路径，普通 PR 仍仅生成短期 CI 包。此发行模式本轮未执行；未将 CI artifact 视为正式 App 更新包，未宣称系统签名、公证或物理设备验收完成。

macOS/ARM64 现有证据来自 CI 构建和协议/模型测试，原生系统安装、交互与实际设备验收后补。独立复核与最终 GitHub 合并读回仍待本轮完成后补充。

## 独立复核修正

两位只读审查者分别核对更新链路与 JEV 增强，发现四项并已修正：两端补充 mise `resolved_path`；Windows 安装器启动失败时保留可复用的后端客户端、恢复安装器 mutex 并重连；JEV 过滤只携带有界元数据并限制完整 question/groups 序列化大小；过滤判断失败后自动汇总不再发出第二次 JEV 判断。

JEV 新定向回归验证超长 title/URL、超长问题保留原文，以及过滤限流后请求在 filter 阶段停止。Windows 新增无界面的 `desktop/tests/BackendLifecycleCheck`，使用真实私有协议进程完成“启动 → 停止 → 再启动 → ping → 停止”，确认安装器失败恢复所需的客户端可复用；记录为 `.desktop-artifacts/backend-reconnect-check.log`。这项检查没有再次控制用户界面或执行安装器。

第一轮正式独立验收又发现两处共用遗漏：取消下载缺少“正在取消”与终态前去重；Windows 的已知质量/解析/服务商错误落成中性“状态未知”。已在共享取消方法中先发布 cancelling，再等待下载清理，并处理协程尚未启动就取消的情况；两端保持取消反馈与禁用，Windows 使用后端状态翻译表及错误色调。流式取消回归覆盖重复取消/下载，新 RPC 回归覆盖立即取消和重试。该修复继续使用自动测试、原生构建及源码核验，未恢复用户已停止的 UI 自动操作。

随后 CI 的 Python 3.10 暴露新增测试引用了 3.11 才支持的 `Task.cancelling()`。已改用标准库 Mock 记录真实 `cancel` 调用次数，仍验证重复取消只请求一次；产品实现不依赖该新接口。失败日志保留为 `.desktop-artifacts/ci-py310-cancel-failure.log`，修复后重新执行对应 CI。
