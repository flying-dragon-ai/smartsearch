---
generated_from_state_version: 37
---

# 验证

## 当前结果

- 结果: **已阻塞**
- 验证情况: **解决报告中的阻塞项后恢复验证**
- 目标周期: 6
- 迭代: 1
- 验证器尝试次数: 1
- 完成时间: 2026-09-21T19:57:04.314Z
- 摘要: 候选 484e03c 的 Runtime 两项正式检查、CI 35645655049 三项任务、Desktop CI 35645656245 四架构正式密钥任务、36 项聚焦回归、草稿 Release 13 附件及签名/架构验证均与当前候选对应。12 项通过；A2/A3/A5 因已明确但未执行的 GUI/真实旧安装迁移验收而 blocked。未发现需要修复的确定产品缺陷。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | specs/desktop-native-updaters/spec.md | Native frameworks own App updates WHEN 安装当前候选并检查 App 更新，THEN Windows 实际进入 Velopack、macOS 实际进入 Sparkle，SDK 使用正确平台架构和稳定源；App 与内置后端版本一致，旧 Python App 下载/安装动作不再与框架同时执行，开发散包明确报告未安装或测试模式。 | Windows 使用 Velopack 的按架构稳定渠道，且只在已安装布局检查：desktop/windows/AppUpdater.cs:25、desktop/windows/AppUpdater.cs:32；macOS 使用 Sparkle：desktop/macos/Sources/SmartSearchDesktop/AppUpdater.swift:27。实际 SDK 升级检查验证目标 App/后端版本一致：desktop/tests/NativeUpdateCheck/Program.cs:14、desktop/tests/NativeUpdateCheck/Program.cs:47；四架构 CI 均绑定当前 HEAD：.desktop-artifacts/release-024-desktop-ci.json:1。 |
| A2 | blocked | specs/desktop-native-updaters/spec.md | Background checks and explicit consent WHEN 自动检查到期、用户关闭自动检查、手动重试或发现新版，THEN 检查频率和提示正确；未点击更新不下载或安装，稍后不会循环弹窗，关闭开关及退出 App 能停止后续自动检查，检查失败不显示已最新。 | 实现具备 24 小时节流、关闭自动检查、显式更新/稍后与无自动下载：desktop/windows/MainWindow.xaml.cs:713、desktop/windows/MainWindow.xaml.cs:720、desktop/macos/Sources/SmartSearchDesktop/AppUpdater.swift:27、desktop/macos/Sources/SmartSearchDesktop/AppUpdater.swift:75。当前只有 Windows 测试版的概括性用户反馈；未实跑 macOS GUI 的开关、手动重试、稍后和失败提示全链路，不能把源码或 CI 替代该交互验收。 |
| A3 | blocked | specs/desktop-native-updaters/spec.md | Update and restart preserve active work WHEN 存在草稿、自有任务或不可取消写入时请求安装，THEN 门禁生效且业务工作保留；解除门禁后 SDK 安装并重启，实际 App 和引擎均为目标版本；失败/取消不被记成成功，不终止外部 CLI。 | Windows 在下载前后复核草稿/任务/CLI 写入门禁，并由后端冻结后续操作：desktop/windows/MainWindow.xaml.cs:53、desktop/windows/MainWindow.xaml.cs:786、src/smart_search/desktop_backend.py:629；SDK 隔离检查覆盖取消不变成功与更新后版本一致：desktop/tests/NativeUpdateCheck/Program.cs:21、desktop/tests/NativeUpdateCheck/Program.cs:47。未在当前 macOS GUI 和真实草稿/自有任务/不可取消写入中完成安装重启验收。 |
| A4 | passed | specs/desktop-native-updaters/spec.md | Real delta update and full fallback WHEN 为隔离的 A/B 两个版本打包并更新，THEN 两个平台各有真实差分包产出和 SDK 升级证据；结果版本/内容正确。移除或破坏差分后的完整包回退仍通过同等校验；缺失首版基线与基线下载失败分别记录，不把完整下载称为差分成功。 | Windows 隔离安装实际选择 delta、损坏 delta 时下载 full，并核对 App/后端内容和版本：desktop/scripts/test_windows_updates.py:100、desktop/scripts/test_windows_updates.py:108；macOS 实际 Sparkle CLI 覆盖 delta、full-fallback、wrong-public-key：desktop/scripts/test_sparkle_updates.py:99、desktop/scripts/test_sparkle_updates.py:129。四架构正式密钥 CI 已通过：.desktop-artifacts/release-024-desktop-ci.json:1。首个正式框架版本只含 full 包的边界已如实记录：.github/releases/v0.1.24.md:12。 |
| A5 | blocked | specs/desktop-native-updaters/spec.md | First migration preserves user data WHEN 从旧 Inno 安装或旧 macOS App 转入第一版框架安装，THEN 操作路径清楚、安装身份和启动入口准确，能继续使用原配置和结果；CLI/Skills/SmartSearchTools 保留，未确认时不卸载旧程序；完成一次完整安装后下一版可走框架更新。 | 迁移提示和 Windows 安装器文案明确要求一次完整安装、不自动卸载并保留配置/CLI/Skills：desktop/windows/MainWindow.xaml.cs:730、desktop/packaging/windows/migration.txt:3、docs/guide/zh-CN/app.md:83。尚未从真实旧 Inno 安装或旧 macOS App 完成首次迁移，再完成下一版框架更新；当前 Windows 测试版反馈不覆盖该场景。 |
| A6 | passed | specs/desktop-native-updaters/spec.md | Signatures and trust fail closed WHEN 公钥不匹配、缺少正式密钥、下载包篡改或签名失败，THEN 正式发布或安装被阻止，不能降级到未签名正式更新。测试身份不能进入正式 feed，Secrets 不泄露，报告区分更新签名、Windows 自签名、Apple 代码签名、公证和系统信任。 | 正式 Sparkle 公钥独立保存并明确非 Developer ID：desktop/packaging/macos/sparkle-public-key.json:2；发布构建要求私钥与固定公钥：desktop/scripts/build-macos.sh:60、desktop/scripts/build-macos.sh:184；实际 Sparkle 错误公钥拒绝检查：desktop/scripts/test_sparkle_updates.py:122。Windows 负例覆盖缺密钥、错误密码/证书、篡改、缺时间戳与工具失败：desktop/scripts/Test-WindowsSigning.ps1:35、desktop/scripts/Test-WindowsSigning.ps1:76；正式 CI 绑定当前 HEAD：.comet/runtime/native/changes/desktop-native-updaters/logs/checks/4b050680-d5ee-473c-b9e0-23438e406006-release024-platform-ci.log:1。 |
| A7 | passed | specs/desktop-native-updaters/spec.md | Architecture and bundle integrity WHEN 构建和选择任一受支持架构的更新，THEN 包内前后端/helper/资源完整且架构匹配，错误架构、旧版本或不适用的更新不允许安装；真实原生构建和协议 smoke 分平台记录，不能把配置矩阵存在当作已经运行通过。 | 四平台包已核验包含当前 state_files 修复、macOS 内置固定公钥、Sparkle 签名和 Windows PE 架构：.desktop-artifacts/release-024-final-assets/asset-verification.json:2。Windows 包内前端、后端、helper 的架构检查逻辑见 .desktop-artifacts/verify-release-024-assets.py:35；四架构真实构建均成功：.desktop-artifacts/release-024-desktop-ci.json:1。 |
| A8 | passed | specs/desktop-native-updaters/spec.md | Release pipeline publishes complete updates WHEN 执行测试或受信发布流程，THEN PR 无发布 Secrets；必要检查失败时停止发布；成功候选包含所需安装器、完整包、适用差分、feed 及校验信息，feed 引用均可解析且不跨架构。只改 workflow 未运行时报告为未运行。 | 发布工作流在受控发布时汇总嵌套资产、拒绝同名冲突、验证全部 feed 后才上传包再上传 feed：.github/workflows/desktop-build.yml:290、.github/workflows/desktop-build.yml:317、.github/workflows/desktop-build.yml:338。当前候选的 13 个草稿附件均已上传且 targetCommitish 为 484e03c：.desktop-artifacts/release-024-draft.json:1；本次四架构候选运行中 release-assets 按无 release_tag 预期 skipped：.desktop-artifacts/release-024-desktop-ci.json:1。公开发布尚未发生，未被表述为已上线。 |
| A9 | passed | specs/desktop-native-updaters/spec.md | Independent CLI and Skills stay healthy WHEN 带入修复并完成 App 框架升级，THEN 原 CLI/Skills 回归继续通过，实际隔离 mise 升级无需用户手动运行版本命令触发修复；App 关闭后独立 CLI 可运行，测试不改真实全局安装或个人 Skills。 | 实际隔离 mise 升级回执证明私有 Python 运行时自动初始化、Skills 同步、未改个人安装且无 Provider 调用：.desktop-artifacts/isolated-cli-upgrade-0a37539a1af14e9095f5497fd483daed/receipt.json:1。该回执对应的 CLI/更新实现到 484e03c 的差异仅为版本文件和 state_files 锁修复，无 desktop_cli/desktop_updates/desktop_backend 行为差异；当前候选全套 npm 回归为 1004 passed/2 skipped：.desktop-artifacts/release-024-fixed-npm-test.log:104，正式 Windows CI 为 1005 passed/1 skipped：.desktop-artifacts/release-024-final-ci.log:356。 |
| A10 | passed | specs/desktop-native-updaters/spec.md | Delivery claims match actual evidence WHEN 交付本次候选，THEN 当前代码、打包程序、测试日志和新只读复核可对应；报告单列本机 Windows、macOS/ARM64、GUI、真实用户安装、CI 与发布状态，任何未运行项保留未运行/受阻，不宣称正式已上线；用户数据和原工作区保持不变。 | 当前 HEAD 精确为 484e03c，Runtime 回执记录两项检查均成功并绑定同一工作区/候选：.comet/runtime/native/changes/desktop-native-updaters/state.json:4、.comet/runtime/native/changes/desktop-native-updaters/state.json:24、.comet/runtime/native/changes/desktop-native-updaters/state.json:44。四平台资产验证为 12 个产品资产且附 SHA256SUMS：.desktop-artifacts/release-024-final-assets/asset-verification.json:2；草稿 Release 仍 isDraft=true，未声称公开上线或本机已升级：.desktop-artifacts/release-024-draft.json:1。 |
| A11 | passed | specs/desktop-windows-signing/spec.md | A1 持续身份与秘密隔离 首次准备产生可复用的 Windows 签名身份，公开证书确认没有私钥，PFX 受随机密码保护并置于仓库外的受限目录；仓库只出现公开证书和其公开元数据。GitHub Secrets 的设置只打印名称/操作状态。后续构建核对并复用该身份；证书指纹不匹配、用途错误、到期、缺少私钥或密码错误均不能用于发布。 | 仓库仅保存公开 Windows 证书元数据（固定指纹、到期、默认不受信任）：desktop/packaging/windows/smart-search.json:2；PFX 被 .gitignore 排除：.gitignore:12。导入脚本先以 EphemeralKeySet 核验固定身份，再导入 CurrentUser/My，并清除子进程环境秘密：desktop/scripts/Import-WindowsSigningIdentity.ps1:16、desktop/scripts/Import-WindowsSigningIdentity.ps1:41。 |
| A12 | passed | specs/desktop-windows-signing/spec.md | A2 Windows 发布物完整签名 为 x64 和 ARM64 生成签名发布物后，App EXE/DLL、冻结后端和自有安装器均带期望证书的 Authenticode 签名和时间戳，且内容完整性检查通过；框架更新/卸载 helper 的来源和签名按打包来源独立核对。产品名称和版本资源与构建版本一致。第三方库的签名前后摘要相同。证据必须区分本机实际构建、CI 实际构建、静态审查和未运行项目，不能以一种架构代替另一种架构。 | x64 与 ARM64 的 App EXE/DLL、冻结后端、Squirrel、ExecutionStub、Setup 共 12 个文件均为 integrity=verified、固定证书指纹匹配且有 RFC3161 时间戳：.desktop-artifacts/release-024-final-assets/windows-signatures.json:3、.desktop-artifacts/release-024-final-assets/windows-signatures.json:51、.desktop-artifacts/release-024-final-assets/windows-signatures.json:91。构建脚本对自有文件签名并检查第三方文件摘要不变：desktop/scripts/Build-Windows.ps1:163、desktop/scripts/Build-Windows.ps1:188。 |
| A13 | passed | specs/desktop-windows-signing/spec.md | A3 异常和不受信任状态不会冒充成功 可运行检查覆盖：缺失签名秘密、错误密码、错误证书、内容被篡改、缺失时间戳、签名工具失败。对应发布操作失败并阻止上传；秘密不出现在错误信息中。正确自签名文件在未导入信任的环境仍明确报告不受系统默认信任，不能将其写成公开可信。构建与验收不永久修改本机信任库。 | 可运行负例检查覆盖缺秘密、错误密码、无私钥、错误/过期证书、篡改内容/CMS/时间戳、缺时间戳、签名工具失败及信任库不变：desktop/scripts/Test-WindowsSigning.ps1:35、desktop/scripts/Test-WindowsSigning.ps1:76、desktop/scripts/Test-WindowsSigning.ps1:98。正式签名验证将自签名根不受信任单列为 untrusted-self-signed-root，而非成功信任：desktop/scripts/Windows-Signing.ps1:94、.desktop-artifacts/release-024-final-assets/windows-signatures.json:8。 |
| A14 | passed | specs/desktop-windows-signing/spec.md | A4 流水线失败阻断且更新器能识别签名资产 现有 release 文件名校验接受两种 Windows signed 安装器，并继续校验现有 macOS 资产与版本。旧版迁移入口能识别新 Windows 安装器；Velopack feed 与包校验拒绝平台不符、身份不符或冲突资产，不以历史未签名资产作为正式更新回退。PR 测试不访问发布 Secrets。至少以真实 Windows 签名构建和可运行的发布/资产检查验证；只有实际成功运行 GitHub Actions 后，才报告线上 CI 已通过。 | Windows 产物命名、每架构完整包/可选 delta、helper 重验签及同架构 feed 约束由打包脚本执行：desktop/scripts/Package-Windows.ps1:61、desktop/scripts/Package-Windows.ps1:80、desktop/scripts/Package-Windows.ps1:90。工作流 PR 仅 contents:read，发布写权限只在受控 release-assets job：.github/workflows/desktop-build.yml:36、.github/workflows/desktop-build.yml:290；当前两架构正式签名包和 feeds 已在草稿附件逐个 SHA-256/size 匹配：.desktop-artifacts/release-024-draft.json:1。 |
| A15 | passed | specs/desktop-windows-signing/spec.md | A5 说明与证据保持一致 中英文下载/发布文档明确自签名、Windows 默认不信任、可能出现的首次运行提示、官方来源和证书指纹；不出现已获得 CA/SignPath 信任或 macOS 已签名等错误声明。报告列出实际验签文件、测试结果、CI 状态以及 GUI/干净机器/ARM64 实机等未运行边界。生成候选产物不自动发布新版本、覆盖旧发行附件或替换本机正式 App。 | 中英文文档明确 Windows 自签名默认不受信任、SmartScreen 边界、macOS 无 Developer ID/公证和 Sparkle 独立签名：docs/windows-signing.md:5、docs/windows-signing.md:7、docs/guide/en/app.md:79、docs/guide/zh-CN/app.md:85。v0.1.24 说明明确 GUI/真实迁移仍需单独验收且不以 CI 替代：.github/releases/v0.1.24.md:25。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Exact candidate CI and four formal-key native packages | .desktop-artifacts/check-release-024-ci.py | . | passed | 0 | 5127 ms |
| Lock race, nested release files and signed workflow regressions | -m pytest -q tests/test_desktop_config.py tests/test_native_update_artifacts.py tests/test_release_workflow.py | . | passed | 0 | 2099 ms |

### Builder 报告的证据

以下为 Builder 报告，不等同于 Runtime 检查凭据或独立验收结果。

- local-npm-test: passed — 1004 passed / 2 skipped；含 wrapper repair 与 pack dry-run，见 .desktop-artifacts/release-024-fixed-npm-test.log
- focused-release-regression: passed — 36 passed；旧实现可确定失败的新空锁回归转绿，附件嵌套及同名拒绝均覆盖
- workflow-and-skills: passed — actionlint 两条 workflow 与 9 文件 skill parity 通过
- 已知限制: 正式候选尚未公开发布，本机正式 App/CLI 升级将在发布后执行。
- 已知限制: 用户负责 GUI 测试，反馈当前 Windows 测试版无问题；不外推 macOS 最终 GUI 或首次旧安装迁移全部完成。
- 已知限制: Windows 自签名默认不受系统信任；macOS ad-hoc，无 Developer ID/公证。

## 阻塞项

- **user**: 候选 484e03c 的 Runtime 两项正式检查、CI 35645655049 三项任务、Desktop CI 35645656245 四架构正式密钥任务、36 项聚焦回归、草稿 Release 13 附件及签名/架构验证均与当前候选对应。12 项通过；A2/A3/A5 因已明确但未执行的 GUI/真实旧安装迁移验收而 blocked。未发现需要修复的确定产品缺陷。 (acceptance: A2, A3, A5) — next: `resolve-verifier-blocker`

## 风险与跳过的工作

- A2、A3、A5 缺少 macOS GUI 的交互验证，以及真实旧 Inno/macOS 首次迁移后下一版更新的证据；这是未运行边界，未发现确定产品缺陷。
- 当前 v0.1.24 Release 仍为 draft，tag 尚未公开；草稿附件 13/13 已逐项匹配远端 digest/size/state，但正式 feed 可访问性与本机 App/CLI 升级需在公开发布后实际核对。
- .desktop-artifacts/release-024-final-assets/windows-signatures.json:8 记录 Windows 自签名根不受默认信任；macOS 包为 ad-hoc、未公证，均已在文档中如实标注。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 0 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-21T10:46:39.126Z |
| 2 | 1 | 1 | fail | A1, A2, A3, A4, A5, A6, A7, A8, A11, A12, A13, A14 | 当前候选不通过：A3 已确认存在 Windows 安装准备 await 期间的新草稿可被重启丢失的缺陷。A9、A10、A15 有当前绑定证据；其余需要未授权或未具备的 macOS/ARM64/签名/CI/GUI/真实迁移证据，保留 blocked。 | 2026-09-21T12:25:40.665Z |
| 2 | 2 | 1 | blocked | A1, A2, A3, A4, A5, A6, A7, A8, A11, A12, A13, A14 | 当前候选为 blocked：A3 不再有上轮已确认的静态草稿丢失竞态，但 GUI 未实跑；A9、A10、A15 有当前绑定证据而通过。其余 12 项缺少规格明确要求的 macOS、ARM64、正式签名、GUI、真实迁移或远程 CI 证据，保持 blocked。 | 2026-09-21T12:43:07.689Z |
| 2 | 2 | 1 | recovery | — | 用户已确认提交、推送并运行候选CI；macOS由另一开发者推进，正式版本后续统一合并。本轮补充Windows-only候选开关后验证Windows x64/ARM64签名与升级，不发布。 | 2026-09-21T12:53:19.145Z |
| 2 | 3 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-21T12:53:54.680Z |
| 3 | 1 | 1 | blocked | A1, A2, A3, A4, A5, A6, A7, A8 | Blocked overall: the immutable CI snapshot is bound to current `77a225cc3529e33a8786cdeb9fc5225eac4c6dcc` and establishes signed Windows x64/arm64 build, negative signing checks, SDK delta/fallback/install-signature checks, and runner-key cleanup. A9-A15 pass; A1-A8 remain blocked where the full accepted Scenario requires macOS, GUI, real migration, or complete release evidence that this authorized Windows-only run explicitly did not execute. | 2026-09-21T13:17:37.415Z |
| 3 | 1 | 1 | recovery | — | 用户已体验 PR51 Windows 软件并要求完成剩余全部合并。基于已测 main65e7365 保留工程师两端界面、Mac签名和打包修复，整合已有原生更新及CLI/Skills修复；执行适用本机与四架构CI后完成合并。正式版本发布仍待最终包测试确认。 | 2026-09-21T17:05:17.479Z |
| 3 | 2 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-21T17:58:59.493Z |
| 4 | 1 | 0 | recovery | — | Mac实际SDK已正确拒绝错误公钥，保持旧版本。验证脚本却要求错误文本包含signatur，实际固定Sparkle2.9.6输出为improperly signed，需要修正这一错误文本断言后重验。产品签名验证不变。 | 2026-09-21T18:05:11.695Z |
| 4 | 2 | 1 | blocked | A2, A3, A5 | 无确定新增产品缺陷：当前735b48a保留PR51基线并以实际四架构CI、Windows签名负例/安装升级、Sparkle真实delta-fallback-wrong-key、冻结CLI/Skills回执证明核心实现。A2、A3、A5因当前整合GUI和真实旧安装迁移未实测而blocked，故总体blocked。 | 2026-09-21T18:32:13.155Z |
| 4 | 2 | 1 | recovery | — | 用户明确要求一直推进到正式发布，授权准备并发布下一稳定版0.1.24，包括必要的正式Sparkle更新身份与Secrets、公钥和不发布的签名预检、版本/说明、tag/GitHub/npm正式发布。GUI仍按用户此前安排由用户操作，已提供测试步骤；未收到结果的A2/A3/A5保持未验收，不冒充通过或自动改真实安装。 | 2026-09-21T18:57:41.812Z |
| 4 | 3 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-21T18:57:43.124Z |
| 5 | 1 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-21T19:10:20.828Z |
| 6 | 1 | 1 | blocked | A2, A3, A5 | 候选 484e03c 的 Runtime 两项正式检查、CI 35645655049 三项任务、Desktop CI 35645656245 四架构正式密钥任务、36 项聚焦回归、草稿 Release 13 附件及签名/架构验证均与当前候选对应。12 项通过；A2/A3/A5 因已明确但未执行的 GUI/真实旧安装迁移验收而 blocked。未发现需要修复的确定产品缺陷。 | 2026-09-21T19:57:04.314Z |



## 结论

候选 484e03c 的 Runtime 两项正式检查、CI 35645655049 三项任务、Desktop CI 35645656245 四架构正式密钥任务、36 项聚焦回归、草稿 Release 13 附件及签名/架构验证均与当前候选对应。12 项通过；A2/A3/A5 因已明确但未执行的 GUI/真实旧安装迁移验收而 blocked。未发现需要修复的确定产品缺陷。
