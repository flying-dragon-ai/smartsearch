---
generated_from_state_version: 9
---

# 验证

## 当前结果

- 结果: **验收通过，需要你确认**
- 验证情况: **已完成检查，但需要你确认验证结果**
- 目标周期: 2
- 迭代: 1
- 验证器尝试次数: 1
- 完成时间: 2026-09-22T03:42:20.644Z
- 摘要: 独立只读核验完成：A1–A7 全部通过，无需追加 Runtime checks。实时 GitHub 查询再次确认 PR53/55/57 HEAD 未漂移；General 35682109991 与 Desktop 35682113762 均精确对应产品提交 630f0034beec8d5a0b371b4a00640147e73fe4c9。recoveryContext 原文“Native Shape artifacts changed”仅对应已授权 brief 补录，当前 83f90d3 相对产品提交只差该 brief，Spec 的七项场景未改。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | specs/desktop-macos-followups/spec.md | Hidden resources do not cover installation instructions WHEN 用户在 Finder 开启显示隐藏文件并打开生成的 DMG，THEN 安装说明无遮挡，布局和隐藏标记符合规格，挂载与复制安装后的 App 签名仍有效；保留作者原始实测范围。 | 布局源码固定 16pt、两隐藏资源在 (330,1000) 且显式隐藏，并避免向已签名 App 写 FinderInfo：desktop/packaging/macos/dmg-settings.py:15、desktop/packaging/macos/dmg-settings.py:19、desktop/packaging/macos/dmg-settings.py:22、desktop/packaging/macos/dmg-settings.py:23。PR53 原始 Finder/DS_Store/codesign 实测及其 15 秒后端限制被保留：.desktop-artifacts/source-pr-53.json:2；最终组合 arm64 DMG 已挂载、复制安装并验签：.desktop-artifacts/integration-macos-arm64.log:857。 |
| A2 | passed | specs/desktop-macos-followups/spec.md | Stable identity and signing failures are preserved WHEN 使用测试身份、正确维护者身份、错误密码/证书、无代码签名用途、过期证书或缺失正式配置进行打包，THEN 仅有效身份可以用于相应模式；错误状态被拒绝，清理临时钥匙串，所有 Mach-O 架构、嵌套代码和复制安装后的 App 被逐项验证，秘密不泄露。 | 正式模式固定校验 P12 指纹、有效期、Code Signing EKU，并使用临时钥匙串后删除：desktop/scripts/macos_signing.py:114、desktop/scripts/macos_signing.py:116、desktop/scripts/macos_signing.py:119、desktop/scripts/macos_signing.py:123、desktop/scripts/macos_signing.py:152；逐架构验签及稳定 certificate-based DR：desktop/scripts/macos_signing.py:213、desktop/scripts/macos_signing.py:225、desktop/scripts/macos_signing.py:229；缺正式变量即失败而不生成回退身份：desktop/scripts/macos_signing.py:271、desktop/scripts/macos_signing.py:275。真实 macOS 测试套件通过 1042 passed/4 skipped：.desktop-artifacts/integration-macos-arm64.log:479；错误密码/指纹、缺 EKU、ad-hoc 冒充和 required-mode 回退均有实测断言：tests/test_macos_signing.py:97、tests/test_macos_signing.py:129、tests/test_macos_signing.py:142、tests/test_macos_signing.py:159。 |
| A3 | passed | specs/desktop-macos-followups/spec.md | Universal packaging keeps both backends and the intended identity WHEN 构建 Universal 并从同一 DMG 在原生 ARM 与 Intel 上复制安装和启动，THEN 前端和 launcher 包含双架构、后端选择正确、参数/stdin/stdout/退出码保持、复制路径变化不影响启动，两个后端版本一致；最终签名及固定指纹符合当前构建模式。 | Universal 组装先验证两原生 App/版本/共享资源，再保留两套后端并生成双架构 launcher：desktop/scripts/assemble_macos_universal.py:23、desktop/scripts/assemble_macos_universal.py:35、desktop/scripts/assemble_macos_universal.py:47、desktop/scripts/assemble_macos_universal.py:57。最终组装后按当前 signing context 签名：desktop/scripts/package-macos.sh:19、desktop/scripts/package-macos.sh:21；同一 Universal DMG 的 ARM 构建和原生 Intel 下载回执 SHA-256 一致，并完成复制安装后验签/Intel 后端启动：.desktop-artifacts/integration-macos-universal-intel.log:247、.desktop-artifacts/integration-macos-universal-intel.log:251、.desktop-artifacts/integration-macos-universal-intel.log:336。 |
| A4 | passed | specs/desktop-macos-followups/spec.md | Renamed assets remain compatible and download tables are complete WHEN 从已发布 v0.1.24 获取基线并生成下一候选的发布集合，THEN 旧名称可正确识别，更新器身份和原 feed 地址不变，五个安装链接存在，三种 Mac 资产与签名回执齐全；发布表幂等且不覆盖原说明，签名与公证声明真实。 | 旧 v0.1.24 名称仅接受正确架构的 Sparkle ZIP，Universal 明确没有伪造基线：desktop/scripts/update_artifacts.py:112、desktop/scripts/update_artifacts.py:114、desktop/scripts/update_artifacts.py:116；当前真实下载回执分别验证 arm64/x86_64，Universal 为 first-framework-release：.desktop-artifacts/v24-baseline-arm64.json:2、.desktop-artifacts/v24-baseline-x86_64.json:2、.desktop-artifacts/v24-baseline-universal.json:2。五入口下载表和真实签名模式文案由现行实现生成并拒绝混合签名：desktop/scripts/release_notes.py:21、desktop/scripts/release_notes.py:30、desktop/scripts/release_notes.py:39；发布集合要求三种 Mac DMG、feed 与正式签名回执齐备：desktop/scripts/update_artifacts.py:151、desktop/scripts/update_artifacts.py:155、desktop/scripts/update_artifacts.py:192。Windows Velopack ID/channel 保持架构固定：desktop/scripts/Package-Windows.ps1:29、desktop/scripts/Package-Windows.ps1:38。 |
| A5 | passed | specs/desktop-macos-followups/spec.md | Native update regressions survive integration WHEN 运行最终组合的 Windows 与 Mac SDK 更新检查，THEN 各自的差分/完整回退和错误签名检查通过，Mac 同证书升级与旧 ad-hoc 迁移保持，Universal 更新后仍具双后端；未实测的 GUI/权限继承明确单列。 | Sparkle 实测逻辑覆盖 delta、损坏 delta 后完整回退、错误公钥拒绝和 ad-hoc 迁移：desktop/scripts/test_sparkle_updates.py:103、desktop/scripts/test_sparkle_updates.py:149、desktop/scripts/test_sparkle_updates.py:153、desktop/scripts/test_sparkle_updates.py:159。arm64、x86_64、Universal 三份实际回执均通过四场景；例如 Universal：.desktop-artifacts/ci630-macos-universal/sparkle-check-0fb03ebc4ef4461f8bb7832c25ee06ba/receipt.json:2、.desktop-artifacts/ci630-macos-universal/sparkle-check-0fb03ebc4ef4461f8bb7832c25ee06ba/receipt.json:8、.desktop-artifacts/ci630-macos-universal/sparkle-check-0fb03ebc4ef4461f8bb7832c25ee06ba/receipt.json:35。最终 CI 的两 Windows 更新验证任务也均成功：.desktop-artifacts/integration-run-35682113762.json:104、.desktop-artifacts/integration-run-35682113762.json:422。 |
| A6 | passed | specs/desktop-macos-followups/spec.md | Final integration is checked against its exact source WHEN 提交整合候选供合并，THEN 来源提交可追溯，文本与无文本冲突的行为联动均被处理，打包检查、共享回归、两 Windows、两 Mac 原生包与 Universal ARM/Intel 检查绑定最终代码；作者原始证据保留，失败/等待/跳过与通过分开。 | 三个实时 PR HEAD 与记录 SHA 一致且均为候选祖先：.desktop-artifacts/check-macos-integration.py:6、.desktop-artifacts/check-macos-integration.py:20、.desktop-artifacts/source-pr-53.json:3、.desktop-artifacts/source-pr-55.json:3、.desktop-artifacts/source-pr-57.json:3。产品提交精确绑定 630f003，当前候选仅追加 brief 文档：.desktop-artifacts/check-macos-integration.py:14、.desktop-artifacts/check-macos-integration.py:16、.comet/runtime/native/changes/desktop-macos-followups/logs/checks/8be66486-4da9-4e08-a6f8-90a4e0d39e95-final-ci-and-source.log:4。实时复核的 General CI 三项与 Desktop CI 六项均 success，release-assets 因未发布预期 skipped：.desktop-artifacts/integration-run-35682109991.json:2、.desktop-artifacts/integration-run-35682113762.json:3、.desktop-artifacts/integration-run-35682113762.json:645、.desktop-artifacts/integration-run-35682113762.json:784、.desktop-artifacts/integration-run-35682113762.json:849。 |
| A7 | passed | specs/desktop-macos-followups/spec.md | Preparation and delivery preserve existing releases and user work WHEN 完成准备或后续授权的主线合并，THEN 操作与授权相符，原工作区和现有发行附件保留；准备阶段不发布或安装，合并阶段准确报告自动 beta 行为，正式签名配置和 GUI 验收的未完成边界继续保留。 | 当前 Scope 明确不发布、不改 v0.1.24、本机安装或个人 Skills：docs/comet/changes/desktop-macos-followups/brief.md:23、docs/comet/changes/desktop-macos-followups/brief.md:25；用户已授权最终通过后合入 main 及自动 npm beta，正式身份/稳定发布仍不在范围：docs/comet/changes/desktop-macos-followups/brief.md:49。Spec 同样限定准备阶段不得改 main/已发布版本/本机，并要求准确报告 main 自动 beta：docs/comet/changes/desktop-macos-followups/specs/desktop-macos-followups/spec.md:51、docs/comet/changes/desktop-macos-followups/specs/desktop-macos-followups/spec.md:53。Runtime status 的 workspace bindingState=aligned 且 isolation=worktree；当前 main 仍为 c05ad78，候选在独立 worktree。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Verify exact final product source, all CI jobs and real v0.1.24 baseline receipts | .desktop-artifacts/check-macos-integration.py | . | passed | 0 | 13976 ms |

### Builder 报告的证据

以下为 Builder 报告，不等同于 Runtime 检查凭据或独立验收结果。

- 最终通用与桌面 CI: passed — 630f003；3 个通用环境、6 个桌面任务通过。每项 SHA/任务详情和源 PR 在 Runtime 检查中重新读取并保存。
- 本机 npm 全套回归与静态检查: passed — 此前产品树791f687：1027 passed/19 skipped；后续3ad3c83仅Swift生命周期检查，已由630f003远端各平台重验。actionlint、9个shell脚本ShellCheck、git diff --check通过。
- 真实 v0.1.24 旧名称基线: passed — 当前脚本实际下载并验证arm64/x86_64旧名ZIP及feed；Universal返回首次框架发行。结果位于.desktop-artifacts/v24-baseline-*.json。
- GUI与真实系统权限继承: not-run — 用户/工程师负责GUI，本轮不自动化GUI；保留PR53原始Finder实测范围。
- 已知限制: Mac CI使用一次性self-signed-test身份；尚未配置长期维护者P12/密码/固定SHA256，正式发布前需另行完成。
- 已知限制: Sparkle/Velopack升级回归使用隔离测试App及synthetic旧版本；本轮不宣称真实用户权限继承或GUI验收。
- 已知限制: 本轮用户已授权最终通过后合入main及自动npm beta，不包含稳定版发布、本机安装或个人Skills修改。

## 阻塞项

- **user**: The generic Skill bridge cannot prove an independent Verifier execution; user confirmation is required before Archive. — next: `await-user`

## 风险与跳过的工作

- 当前最终 CI 使用一次性 self-signed-test；三份实物回执均如实标记测试身份，而非长期维护者证书：.desktop-artifacts/ci630-macos-universal/macos-universal-XARJwf/result.json:7。正式发行前仍须配置并以 required/self-signed 模式重新验证维护者 P12、密码和固定 SHA-256；这是已声明的后续前提，不是本轮合并阻塞。
- Finder 的交互式显示隐藏文件结论继承 PR53 的原始 Mac 实测；本轮最终组合未自动化 GUI。Sparkle 回执也明确 gui_tested=false、production_install_modified=false：.desktop-artifacts/ci630-macos-universal/sparkle-check-0fb03ebc4ef4461f8bb7832c25ee06ba/receipt.json:44。
- 更新回归使用隔离 test App 与 synthetic 0.0.1 旧版本；真实用户设备权限继承和生产安装未被本轮声称验证。稳定 release-assets 未运行，因 workflow 仅在显式 release_tag 下执行：.github/workflows/desktop-build.yml:457。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-22T03:31:06.597Z |
| 2 | 1 | 1 | pass | — | 独立只读核验完成：A1–A7 全部通过，无需追加 Runtime checks。实时 GitHub 查询再次确认 PR53/55/57 HEAD 未漂移；General 35682109991 与 Desktop 35682113762 均精确对应产品提交 630f0034beec8d5a0b371b4a00640147e73fe4c9。recoveryContext 原文“Native Shape artifacts changed”仅对应已授权 brief 补录，当前 83f90d3 相对产品提交只差该 brief，Spec 的七项场景未改。 | 2026-09-22T03:42:20.644Z |



## 结论

独立只读核验完成：A1–A7 全部通过，无需追加 Runtime checks。实时 GitHub 查询再次确认 PR53/55/57 HEAD 未漂移；General 35682109991 与 Desktop 35682113762 均精确对应产品提交 630f0034beec8d5a0b371b4a00640147e73fe4c9。recoveryContext 原文“Native Shape artifacts changed”仅对应已授权 brief 补录，当前 83f90d3 相对产品提交只差该 brief，Spec 的七项场景未改。
