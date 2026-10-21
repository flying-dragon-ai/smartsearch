---
generated_from_state_version: 12
---

# 验证

## 当前结果

- 结果: **已归档**
- 验证情况: **已完成检查，验证结果已确认**
- 目标周期: 2
- 迭代: 1
- 验证器尝试次数: 1
- 完成时间: 2026-09-21T02:53:14.442Z
- 摘要: 五项验收均有候选代码、公开证书、指定 Runtime 回执和 CI 35553684440 的相互印证。未读取 PFX、password.dpapi 或任何秘密值；未重跑全量测试、构建或下载。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | specs/desktop-windows-signing/spec.md | A1 持续身份与秘密隔离 首次准备产生可复用的 Windows 签名身份，公开证书确认没有私钥，PFX 受随机密码保护并置于仓库外的受限目录；仓库只出现公开证书和其公开元数据。GitHub Secrets 的设置只打印名称/操作状态。后续构建核对并复用该身份；证书指纹不匹配、用途错误、到期、缺少私钥或密码错误均不能用于发布。 | 公开 CER 实测 HasPrivateKey=false、SHA-256=9BECD07F73FF0B9ECB10D9C7D6D9B2E48584FBC6FA3D4759BF6661892DBBB35B、EKU=1.3.6.1.5.5.7.3.3；公开元数据见 desktop/packaging/windows/smart-search.json:2-5。生成脚本拒绝仓库内/既有身份并设置仅当前用户 ACL（desktop/scripts/New-WindowsSigningIdentity.ps1:9-18,29-36），导入脚本核对 pin、用途、期限和私钥且只写 CurrentUser/My（Import-WindowsSigningIdentity.ps1:7-34）。Runtime private-boundary=passed/exit 0，验证受限备份 ACL、私钥临时证书移除；Check-CiSigningEvidence.ps1:61-63 也确认无 tracked pfx/p12/dpapi、公开 CER 无私钥且未装为本机 Root。 |
| A2 | passed | specs/desktop-windows-signing/spec.md | A2 Windows 发布物完整签名 为 x64 和 ARM64 生成签名发布物后，App EXE/DLL、冻结后端、安装器及其实际携带的卸载器均带期望证书的 Authenticode 签名和时间戳，且内容完整性检查通过。产品名称和版本资源与构建版本一致。第三方库的签名前后摘要相同。证据必须区分本机实际构建、CI 实际构建、静态审查和未运行项目，不能以一种架构代替另一种架构。 | 签名器同时核对固定证书、SHA-256 CMS、PE 文件摘要、RFC3161 签名绑定和 TSA CA 链；仅允许 0x800B0109 自签根未信任（desktop/scripts/Windows-Signing.ps1:79-131）。构建只签 App EXE/DLL、backend EXE，并保持其余文件哈希（Build-Windows.ps1:181-190,268-290）；Inno Setup 配置 Setup+SignedUninstaller，构建后验签二者（SmartSearch.iss:38-45；Build-Windows.ps1:240-264）。CI 回执 .desktop-artifacts/ci-35553684440/verification-summary.json 显示 x64/arm64 各 5 个构建签名、4 个实际安装后签名；两架构 result.json 与 installed-signatures.json 均记录 integrity=verified、同一证书和时间戳。Check-CiSigningEvidence.ps1:31-59 对下载文件、产品/版本资源和安装后四文件逐一复验。 |
| A3 | passed | specs/desktop-windows-signing/spec.md | A3 异常和不受信任状态不会冒充成功 可运行检查覆盖：缺失签名秘密、错误密码、错误证书、内容被篡改、缺失时间戳、签名工具失败。对应发布操作失败并阻止上传；秘密不出现在错误信息中。正确自签名文件在未导入信任的环境仍明确报告不受系统默认信任，不能将其写成公开可信。构建与验收不永久修改本机信任库。 | 导入缺秘密/密码错误/无私钥/证书不匹配会抛错（Import-WindowsSigningIdentity.ps1:7-24）；Required 模式缺身份、签名工具失败或验签失败均停止且无 unsigned fallback（Build-Windows.ps1:25-33；Windows-Signing.ps1:134-142）。验证器不会以任意 UnknownError 跳过：PE hash 与策略错误均拒绝，唯一受限例外为明确的自签根未信任 0x800B0109（Windows-Signing.ps1:90-97）。两架构签名检查回执均为 passed，完整 14 项含 missing-secrets、wrong-password、wrong-certificate、PE/CMS/timestamp 篡改、missing-timestamp、sign-tool-failure、trust-store unchanged（.desktop-artifacts/ci-35553684440/windows-{x64,arm64}/evidence/.desktop-artifacts/signing-check-*/result.json）；测试实现见 Test-WindowsSigning.ps1:35-100。 |
| A4 | passed | specs/desktop-windows-signing/spec.md | A4 流水线失败阻断且更新器能识别签名资产 现有 release 文件名校验接受两种 Windows signed 安装器，并继续校验现有 macOS 资产与版本。App 的资产选择能识别新 Windows 文件、拒绝平台不符或冲突资产，并继续读取历史未签名资产。PR 测试不访问发布 Secrets。至少以真实 Windows 签名构建和可运行的发布/资产检查验证；只有实际成功运行 GitHub Actions 后，才报告线上 CI 已通过。 | workflow 仅在 workflow_dispatch 的 sign_windows 或 release_tag 条件下导入 Secrets/Required 签名（.github/workflows/desktop-build.yml:92-115），pull_request 无该路径；发布作业仅在非空 release_tag 且所有 jobs 成功后执行（:255-303）。release 文件名严格要求两架构 -signed.exe，macOS 原有 unsigned-test 保持（:280-284）。更新器接受 signed/unsigned/unsigned-test，平台或多候选冲突返回 None（src/smart_search/desktop_updates.py:77-91），测试覆盖历史兼容和冲突拒绝（tests/test_desktop_updates.py 新增 test_self_signed_assets_keep_legacy_compatibility_and_reject_ambiguity）。CI 回执 run.json 显示 HEAD 84ab6f9823f5426e85506ce092a937fea7892994 的 x64/arm64 签名 job 成功，release-assets=skipped；Runtime signed-ci-artifacts=passed。 |
| A5 | passed | specs/desktop-windows-signing/spec.md | A5 说明与证据保持一致 中英文下载/发布文档明确自签名、Windows 默认不信任、可能出现的首次运行提示、官方来源和证书指纹；不出现已获得 CA/SignPath 信任或 macOS 已签名等错误声明。报告列出实际验签文件、测试结果、CI 状态以及 GUI/干净机器/ARM64 实机等未运行边界。生成候选产物不自动发布新版本、覆盖旧发行附件或替换本机正式 App。 | 双语公开文档准确声明 self-signed、默认不信任、SmartScreen 仅是一次运行选择、官方 Releases 来源、CER/指纹、macOS 未签名未公证和未运行边界（docs/windows-signing.md:5-32,44-70；README.md:43；README.zh-CN.md:43；docs/guide/en/app.md:9；docs/guide/zh-CN/app.md:9）。文档明确区分 CMS/PE/固定证书/RFC3161 与普通 SHA256，不将 UnknownError 泛化为成功（docs/windows-signing.md:30-32,64-70）。run.json 证明本轮未发布：release-assets skipped；文档也明确 CI 不代替 GUI、干净机与实机验收。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Full Python regression | -m pytest -q | . | passed | 0 | 53051 ms |
| Verify exact CI commit, downloaded signatures and installed evidence | -NoProfile -File D:\Dev\20_个人项目\智能搜索\smartsearch-windows-signing\.desktop-artifacts\Check-CiSigningEvidence.ps1 | . | passed | 0 | 7926 ms |
| Private backup ACL and temporary-key cleanup | -NoProfile -Command $ErrorActionPreference='Stop' $directory=Join-Path $env:LOCALAPPDATA 'SmartSearch/signing/windows' $acl=Get-Acl -LiteralPath $directory $rules=@($acl.Access) $sid=[Security.Principal.WindowsIdentity]::GetCurrent().User.Value if(-not $acl.AreAccessRulesProtected -or $rules.Count -ne 1 -or $rules[0].IsInherited -or $rules[0].IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value -ne $sid -or $rules[0].AccessControlType -ne 'Allow'){throw 'Private backup ACL is not restricted to current user'} foreach($file in @('smart-search.pfx','password.dpapi')){if(-not(Test-Path -LiteralPath (Join-Path $directory $file) -PathType Leaf)){throw 'Encrypted private backup missing'}} if(Test-Path -LiteralPath 'Cert:/CurrentUser/My/6B9599874FE6DF6BB3C53664FDEFBA3159EB62FB'){throw 'Temporary signing private key remains installed'} Write-Output 'Private backup ACL and temporary-key cleanup passed.' | . | passed | 0 | 527 ms |
| Diff whitespace check | diff --check | . | passed | 0 | 40 ms |

### Builder 报告的证据

以下为 Builder 报告，不等同于 Runtime 检查凭据或独立验收结果。

- full pytest: passed — 917 passed,2 skipped; subsequent test harness exit0 validated locally and in CI.
- real signed build and negative checks: passed — Localx64 build 5signatures+658unchangedfiles; bothCIarchitectures14checks,5buildsignatures+4installedsignatures. Downloadsummary .desktop-artifacts/ci-35553684440/verification-summary.json.
- source/doc checks: passed — PowerShell syntax,gitdiffcheck,localdoclinks passed.
- 已知限制: Self-signed is not public CA trust or a promise of no SmartScreen prompts.
- 已知限制: No GUI/physical-device acceptance,macOS signing,main merge,new release or installedAppreplacement.
- 已知限制: Inno uninstaller ProductVersion matches app; internal FileVersion remains compiler-owned.

## 阻塞项

_无。_

## 风险与跳过的工作

- 自签名证书仍非 Windows 默认公开信任；普通用户 SmartScreen、受管设备策略和真实 GUI 行为未由本轮证实。
- CI 已在 Windows arm64 runner 生成并验签，但用户实体 ARM64 设备、完整升级/卸载流程和干净机 GUI 验收仍未运行。
- 工作树存在未提交的 docs/comet/changes/desktop-windows-signing/comet-state.yaml 运行期改动；审查结论绑定提交 84ab6f9 的 984176e..HEAD 范围，未将该状态文件当作候选实现。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-21T02:33:58.381Z |
| 2 | 1 | 1 | pass | — | 五项验收均有候选代码、公开证书、指定 Runtime 回执和 CI 35553684440 的相互印证。未读取 PFX、password.dpapi 或任何秘密值；未重跑全量测试、构建或下载。 | 2026-09-21T02:53:14.442Z |



## 结论

五项验收均有候选代码、公开证书、指定 Runtime 回执和 CI 35553684440 的相互印证。未读取 PFX、password.dpapi 或任何秘密值；未重跑全量测试、构建或下载。
