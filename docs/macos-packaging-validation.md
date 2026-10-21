# macOS 打包修复验证（2026-09-21）

代码基线：`984176e46ae4bb08fb607d1f2b00510aada96451`（v0.1.22）。本次为本地修改，尚未提交、运行远端 CI 或替换 Release 附件。

## 原因与复现

用户下载的 `SmartSearch-0.1.22-macos-arm64-unsigned-test.dmg` 的 SHA-256 为
`5ce6c0f6f5ffa1f9e94789ddbdf9a7bf627335424bd0a8c48a4995ffb4957594`，与 GitHub Release 的 `SHA256SUMS.txt` 相同。

只读挂载后，`codesign --verify --deep --strict` 和 `spctl --assess` 都报：

```text
code has no resources but signature indicates they must be present
```

签名详情只有 `adhoc,linker-signed`，`Info.plist=not bound`，`Sealed Resources=none`。旧脚本将 Swift 可执行文件和 Python 后端复制进 `.app` 后直接生成 DMG，遗漏完整应用签名。对临时副本补齐 ad-hoc 签名后，严格校验通过。

## 修复及验收

- 全部资源复制后签名；打包前、DMG 内及临时安装副本均强制严格校验。
- DMG 使用与 Codex Tweaks / DJOneHub 相同的 660×440 窗口和 112pt 图标布局，提供 Applications 链接、双语提示、品牌青色箭头和 Retina 背景。
- 不使用 dmgbuild 的 `hide_extensions`：实测该选项添加 `com.apple.FinderInfo`，会破坏严格签名校验。成品校验已实际拦截这一失败。
- 忽略 Finder 的 `.DS_Store` 资源元数据；实测缺失真正的应用资源仍会报错。
- 重打既有 tag 时，macOS 脚本、验证器、安装资源及 mise 配置一起取自工作流提交，产品代码仍取自 tag。

本机 Apple Silicon 已通过：

```bash
mise run desktop:macos:install
mise run desktop:macos:build --architecture arm64
mise run desktop:packaging:lint
```

构建含实际 DMG 的只读挂载、完整签名、版本/架构/安装资源检查，复制安装后的签名检查与隔离配置下的后端 initialize/shutdown smoke。新验证器针对原始下载包运行，按预期拒绝其无效签名。

Finder 实际安装窗口已人工检查；截图在本地 `.desktop-artifacts/dmg-preview.png`。从 Finder 打开新包后，已观察到 SmartSearchDesktop 和私有后端进程运行。计算机使用工具读取 App 窗口时发生 `native pipe closed before response`，因此未据此宣称 App 全页面交互验收通过。

本地产物：`.desktop-artifacts/macos-arm64-20260921T013547Z-92783-3079/SmartSearch-0.1.22-macos-arm64-unsigned-test.dmg`。
SHA-256：`dfe3b8deabb0293f8bc9e3e16178b391dfe863bc7010cb4ceff4a8f56969e53b`。

## 未验范围

Intel runner、其他 macOS 版本、干净机器从浏览器下载后的 Gatekeeper 流程、全页面交互均未完成验收。本机没有有效的 Developer ID 签名身份；ad-hoc 签名只保证包完整性，不代表发行者信任或 Apple 公证。用户首次打开说明已加入中英排障手册。
