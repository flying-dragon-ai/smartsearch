# macOS 稳定自签名身份 / Stable macOS signing identity

## 上游作者必须完成的配置 / Maintainer setup required

**此变更不提供正式证书或私钥。正式签名身份必须由上游作者或指定维护者生成、保管和备份。** PR 使用一次性的测试证书验证实现；不要把贡献者或 CI 测试证书当成项目的长期身份。生成正式身份后，所有版本和两种架构持续复用同一套证书和私钥。

**This change ships no production certificate or private key. The upstream author or designated maintainer must generate and retain the production identity.** PR builds use a disposable test identity. Reuse the maintainer's identity for both architectures and future releases; never generate a new production identity on each CI run.

### 1. 在作者的 Mac 上生成一次 / Generate once on the maintainer's Mac

安装 Xcode 命令行工具与 mise，在合入此变更后的仓库根目录执行。Python 等工具版本由 `mise.toml` 管理；`security`、`codesign`、`xcrun` 与 `/usr/bin/openssl` 使用 macOS 自带工具。

```bash
mise install
mise run install
mkdir -p "$HOME/.local/share"
mise run desktop:macos:certificate "$HOME/.local/share/smart-search-macos-signing"
```

命令交互询问 P12 密码，不回显密码。请使用密码管理器保存强密码。目标目录必须尚不存在；脚本拒绝覆盖已有身份，且拒绝在当前仓库内保存私钥。生成结果：

| 文件 / File | 内容与保管 / Purpose |
| --- | --- |
| `smart-search.p12` | 证书与私钥的加密容器；仅由维护者保管，目录权限 0700、文件权限 0600。Encrypted certificate/private-key container; maintainer only. |
| `smart-search.cer` | 可公开的 DER 证书，不含私钥。Public DER certificate. |
| `smart-search.json` | 可公开的 SHA-256 指纹与用途。Public SHA-256 fingerprint and purpose. |

将 P12 做受限的加密备份，密码分开保管；不要上传到议题、PR、Release、CI artifact 或聊天。丢失私钥后不能靠重新生成同名证书恢复原身份。证书有效期为 10 年，当前导入流程拒绝过期证书；应在到期前另行规划身份轮换与迁移。

The command prompts for a password without echoing it and refuses an existing output directory. Keep an encrypted backup and retain the password separately. A new certificate with the same name is a different identity. The certificate lasts ten years; the importer rejects expired certificates, so plan renewal and migration before expiry.

### 2. 配置上游仓库 / Configure the upstream repository

在上游仓库 **Settings → Secrets and variables → Actions** 添加：

| 类型 / Type | 名称 / Name | 值 / Value |
| --- | --- | --- |
| Secret | `SMART_SEARCH_MACOS_P12_BASE64` | `smart-search.p12` 的 Base64；允许换行。Base64 of the encrypted P12. |
| Secret | `SMART_SEARCH_MACOS_P12_PASSWORD` | 第一步设置的密码。The P12 password. |
| Variable | `SMART_SEARCH_MACOS_CERT_SHA256` | `smart-search.json` 中的 `certificate_sha256`，64 位十六进制，不带冒号。The 64-character certificate SHA-256. |

可用已登录作者账户的 GitHub CLI 上传加密容器，避免在终端打印：

```bash
base64 < "$HOME/.local/share/smart-search-macos-signing/smart-search.p12" \
  | gh secret set SMART_SEARCH_MACOS_P12_BASE64 --repo konbakuyomu/smartsearch
gh secret set SMART_SEARCH_MACOS_P12_PASSWORD --repo konbakuyomu/smartsearch
```

第二条命令会交互询问密码。公开指纹可从 JSON 复制到仓库 Variable。建议将公开 CER 与 JSON 另行提交到 `desktop/packaging/macos/`，供下载者核对；P12 与密码始终不入库。CI 导入时先核对 SHA-256，再允许使用私钥；相同证书名称不足以通过检查。

Configure the two Secrets and the public Variable above using the upstream maintainer's account. Publish only the CER and its JSON metadata under `desktop/packaging/macos/` for independent fingerprint comparison. The importer pins the full certificate hash, not its display name.

### 3. 先生成不发布的正式身份候选 / Validate without publishing

在 **Actions → Desktop packages → Run workflow**：

1. 选择包含此功能的分支。
2. 开启 `sign_macos`，关闭 `windows_only`。
3. 保持 `release_tag` 为空；不必开启 `sign_windows` 或 `sign_macos_updates`。
4. 检查 macOS arm64、x86_64 任务成功，下载对应候选的 `signing.json`、`result.json` 与 Sparkle 检查回执。

两种原生架构及通用版的 `certificate_sha256` 应与公开指纹一致；App 的 `designated_requirement` 应一致且绑定证书和 `com.smartsearch.desktop`。文件名统一为 `SmartSearch-vX.Y.Z{可选架构后缀}.dmg`，`result.json` 与 `signing.json` 记录 `self-signed` 状态。钥匙串只在一次构建/验证命令期间存在，成功和失败都会清理；不更改用户的系统信任设置。

Run the workflow with `sign_macos=true`, `windows_only=false`, and an empty `release_tag`. Both native Mac jobs and the universal ARM/Intel checks must pass. Compare the certificate fingerprint and App designated requirement across all three packages. Signing status is in `result.json` and `signing.json`, not the filename. Inspect the copied-install verification and native-update receipts. This run does not publish a release.

### 4. 后续正式发布 / Subsequent releases

填写 `release_tag` 时强制使用作者的 macOS 证书、Windows 证书及 Sparkle 更新密钥。开启 `sign_macos_updates` 同样要求正式 macOS 证书。缺少 Secrets、密码错误、指纹不符、签名/验签失败均中止，不降级为 ad-hoc 或自动生成测试身份。先配置作者证书，再启用新的发布流程。

普通 PR 和未开启正式签名的手动构建使用临时测试证书，元数据标为 `self-signed-test`。测试身份不跨运行复用；测试私钥、P12 和临时钥匙串不进入 Secrets 或 artifact，公开测试证书会嵌入签名并随候选产物分发。它只证明实现能够正确签名与验证，不能作为正式身份的验收。普通本地 `mise run desktop:macos:build --architecture arm64` 仍默认 ad-hoc，元数据标为 `ad-hoc-test`；三种模式使用相同命名规则，不能凭文件名判断身份。

Release mode requires the maintainer's Mac certificate as well as the existing Windows and Sparkle keys. Missing or invalid configuration stops the release. Secret-free PR/manual candidates record `self-signed-test`; local ad-hoc builds record `ad-hoc-test`. Neither is accepted by the signed release-asset gate. These modes share the download naming scheme, so inspect the signing metadata.

本地验证正式身份时，可通过安全凭据管理方式设置上述三个环境变量，然后执行：

```bash
mise run desktop:macos:with-signing --mode required -- \
  mise run desktop:macos:build --architecture arm64
```

首次检查流程、没有正式密钥时：

```bash
mise run desktop:macos:signing-test
mise run desktop:macos:install
mise run desktop:macos:with-signing --mode test -- \
  mise run desktop:macos:build --architecture arm64
```

## 身份连续性与迁移 / Continuity and migration

签名器从内向外处理 App、嵌套 framework/helper 和 PyInstaller 的 Mach-O 文件。App 的身份规则绑定固定证书和 Bundle ID，不绑定每版变化的代码哈希。打包、DMG 挂载和复制安装均检查真实签名及证书指纹。`signing.json` 是这些检查的记录，不能代替对文件本身的验签。

从历史 ad-hoc 版本首次切换到自签名证书会发生一次身份变化。Sparkle EdDSA 公私钥保持原值；原生升级检查覆盖 ad-hoc → 自签名、同证书版本升级、差分损坏后的完整包回退及错误更新密钥拒绝。系统权限是否继承仍由具体 macOS 权限机制决定，真实设备的 GUI/授权行为需维护者另行验证。

The first move from ad-hoc signing changes the App identity once. Sparkle's existing EdDSA identity is retained. Automated checks cover ad-hoc migration, stable-identity upgrades, delta/full fallback and wrong-update-key rejection. Device permission retention and GUI behavior still need device validation. Self-signing does not establish Apple Developer ID trust or notarization.

参考实现 / Implementation reference: [Codex Tweaks signing import](https://github.com/codex-tweaks/codex-tweaks/blob/main/scripts/import-macos-signing-identity.sh) 与 [artifact verification](https://github.com/codex-tweaks/codex-tweaks/blob/main/scripts/verify-release.sh)。本项目直接使用 `codesign` 完成最终签名，使用临时钥匙串而不添加系统信任；不复用参考项目的证书、私钥或发布身份。

Apple 参考 / References: [TN3127: code identity and requirements](https://developer.apple.com/documentation/technotes/tn3127-inside-code-signing-requirements), [TN2206: self-signed identities](https://developer.apple.com/library/archive/technotes/tn2206/).
