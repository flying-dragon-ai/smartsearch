# Outcome

为 Smart Search Windows x64/ARM64 发布物加入持续复用的自签名 Authenticode 身份、时间戳和失败阻断，参考用户指定的 codex-tweaks。目标是让文件来源与完整性可验证，不将自签名说成 Windows 默认公开信任。

# Scope

- 基线 main 984176e（v0.1.22），隔离工作区 codex/desktop-windows-signing；保留原 dirty 工作区。
- 延续原请求的 Windows 范围。自有 App EXE/DLL、PyInstaller 后端、Inno Setup 安装器及卸载器全部纳入签名，x64/ARM64 共用一个 Windows 签名身份。
- 一次生成代码签名证书。公开 CER 和指纹进入仓库；包含私钥的加密 PFX 及密码分别放 GitHub Actions Secrets。构建不按次生成身份。
- 复用现有 GitHub Actions、PowerShell 和 Inno Setup；不迁移到参考项目的 Velopack，不重签第三方库。
- 用户已确认的操作范围包含：配置上述签名 Secrets，推送专用 codex/desktop-windows-signing 分支并运行不发布版本的 CI，以取得两种 Windows 架构的真实签名证据。
- 公开文档说明自签名状态、获取来源、核对指纹及 Windows 实际提示；CI 验签通过不等同普通用户电脑已信任。
- 用户提供 D:/Dev/30_第三方项目/30_AI与MCP工具/codex-tweaks 作为实现参考，不将该项目整体功能作为移植需求。

# Non-goals

- 不处理 macOS 签名或公证，不申请 SignPath、不购买 CA 证书，不迁移 Microsoft Store。
- 不自动修改用户 Root/TrustedPublisher 信任库，不关闭 SmartScreen，不承诺只点一次后永久无提示。
- 本 change 不自行提升版本、发布 Release、覆盖历史安装包或替换本机正式 App；这些交付动作按后续明确授权执行。

# Acceptance examples

以 specs/desktop-windows-signing/spec.md 的完整 Scenario 作为验收项：证书保管、Windows 全链路签名、失败阻断、现有更新兼容、文档和证据边界。

# Constraints and invariants

- 私钥、PFX、密码、Base64 私钥包不得进入仓库、聊天、日志或构建 artifact。公开 CER 不含私钥。
- 本地签名身份材料放仓库外的当前用户私有目录，并限制 ACL；只向明确的 konbakuyomu/smartsearch 仓库写所需 Secrets，不读取现有秘密值。
- 本机信任库不作永久修改；若 CI 验证需要临时信任，仅限可丢弃的 GitHub runner，并准确区分身份匹配、内容完整性、时间戳与系统信任。
- 无实际签名及验签证据时不得声称签名完成；没有实际 CI 运行时不得声称线上流程已通过。
- 不批量删除，不覆盖无关工作；新增测试与证书临时文件清理逐个明确路径。

# Decisions

- 用户于 2026-09-21 明确回复“确认，开始实施”，授权按已展示的 Windows 完整方案实施、设置签名 Secrets、提交推送专用分支并运行不发布的 CI。

- 用户明确选择参考 codex-tweaks 的自签名证书 + GitHub Secrets 路线，替代最初建议的公开 CA/SignPath 路线。
- 自签名保留用户首次运行提示这一限制；“仍然可能弹窗”不是签名失败，也不意味着后续每个版本一定无提示。
- Windows 两种架构共用一张证书。CER 和 PFX 是同一身份的公开/私有导出，不是两张不同证书；macOS 是另一个平台身份，不在本轮原始 Windows 范围内。
- 采用 Smart Search 作为 Windows 自签名发布者；源码已有 App 产品名。后端需补齐产品/版本资源。
- 签名后的 Windows 安装器沿用更新器已支持的 -signed.exe 后缀；发布说明明确 self-signed。旧 unsigned 包的读取保持兼容。
- 正式发布的签名必须失败即中止，不能在缺少 Secrets 或签名失败时降级为未签名发行物。无秘密的 PR 测试仍可生成明确标识的 unsigned-test 产物。

# Open questions

无未决问题。用户明确回复“确认，开始实施”，已接受完整范围与五项验收。

# Verification expectations

实施前基线：本机 App EXE/DLL、后端与卸载器均 NotSigned，v0.1.22 安装器亦 NotSigned；证书库未发现代码签名证书，仓库 Secrets/variables/environments 为空。发现 Windows SDK 10.0.22621.0 的 signtool.exe。该基线检查时尚未实施。后续实现与验收记录以 Runtime 检查和报告为准。

实现后检查证书与私钥边界、修改文件拒绝验签、缺失或错误秘密阻断、Windows 构建及协议 smoke、安装器/卸载器签名覆盖、release 文件名与 App 更新兼容。本机 x64 与 GitHub ARM64/平台运行证据分别标注；用户负责 GUI 手动验收。

技术参考：
- 用户指定 codex-tweaks 的签名脚本与 release workflow。
- https://learn.microsoft.com/en-us/windows/apps/package-and-deploy/code-signing-options
- https://jrsoftware.org/ishelp/topic_setup_signtool.htm
- https://jrsoftware.org/ishelp/topic_setup_signeduninstaller.htm
