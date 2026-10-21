[手册目录](../README.md) · [English](../en/troubleshooting.md)

# 排障

## 排障

如果 `doctor` 返回 `config_error`：

```powershell
smart-search setup
smart-search config list --format json
smart-search doctor --format markdown
```

如果搜索慢：

- 降低 `--extra-sources`；
- 把大问题拆成多个小问题；
- 先用 `exa-search` 或 `zhipu-search` 找来源，再 `fetch` 关键网页。

如果想确认安装是否正常：

```powershell
smart-search --help
smart-search --version
smart-search regression
smart-search smoke --mock --format json
```

Windows npm/mise 安装后建议验证中文 JSON 管道：

```powershell
smart-search deep "深度搜索一下最近的比特币行情" --format json | ConvertFrom-Json
```

## 在 WSL 或 Linux 上使用

App 只有 Windows 和 macOS 版。在 WSL 或 Linux 中直接安装和配置 CLI（需要 glibc 2.35+，例如 Ubuntu 22.04 及以上）；Windows 版 App 也可以连接 WSL 里的 CLI，并在装有 Node.js 的发行版中安装或更新它，见 [Windows 本机和 WSL](app.md#windows-本机和-wsl)：

```bash
npm install -g @konbakuyomu/smart-search@latest
smart-search setup                                # 或用 smart-search ui 打开网页配置页
smart-search skills update --targets claude,codex
```

WSL 的配置（`~/.config/smart-search`）和 Skills（例如 `~/.claude/skills`）与 Windows 上的 App 分开保存。运行在 WSL 里的 Agent 只读取 WSL 这一份，所以 Key 和 Skills 要在 WSL 里各配一次；用 Windows App 管理时，先在“环境详情…”选择 WSL 的安装。

在 WSL 中运行 `smart-search ui` 会用 `wslview` 或 `explorer.exe` 打开 Windows 默认浏览器；设置了 `BROWSER` 时按 `BROWSER` 打开。WSL 默认的 NAT 网络模式会把 `127.0.0.1` 转发给 Windows。`.wslconfig` 设置 `networkingMode=mirrored` 时，Hyper-V 防火墙默认拦截从 Windows 进入 WSL 的连接，页面会一直加载不出来。这时在 WSL 中固定端口：

```bash
smart-search ui --port 8765
```

再按[微软文档](https://learn.microsoft.com/windows/wsl/networking#mirrored-mode-networking)在管理员 PowerShell 中放行这个端口：

```powershell
New-NetFirewallHyperVRule -Name SmartSearchUI -DisplayName "Smart Search UI" -Direction Inbound -VMCreatorId '{40E0AC32-46A5-438A-A0B2-2B479E8F2E90}' -Protocol TCP -LocalPorts 8765
```

## CLI 包已升级，但提示运行环境未就绪

新版 npm CLI 不依赖安装脚本或系统 Python。缺少平台运行包时，使用同一 npm 执行 `npm install -g @konbakuyomu/smart-search@latest --include=optional`，再重新检测；不要使用 `--omit=optional`。手动指定 npm 时，确认同目录有配套 Node.js，且全局 prefix 可写。旧版 npm 0.1.24 需要等待新的二进制版本发布后更新。

## App 更新失败或不可用

恢复网络后在设置页重新检查 App 更新。已下载仍需安装和重启；先处理 App 任务、受保护写入与未保存草稿。Windows 开发散包和旧 Inno 安装需先运行新的完整安装器；没有更新密钥的 macOS 测试候选不能更新。只使用官方且架构匹配的版本；签名或完整性失败不能绕过，保留当前安装并报告错误。App 更新不会自动修复或升级独立 CLI/Skills。

## macOS 提示“已损坏”或“无法验证开发者”

先确认下载自本项目发行页，按该版本的 `SHA256SUMS.txt` 核对 DMG；打开 DMG 后，将 **Smart Search** 拖入 **Applications**，再从“应用程序”启动。安装包仍为未公证测试包。

“已损坏”不一定是下载失败。修复前 v0.1.22 的 `.app` 未在资源组装完成后重新签名，完整性校验会报 `code has no resources but signature indicates they must be present`。可在终端检查已安装的副本：

```bash
codesign --verify --deep --strict --verbose=2 "/Applications/Smart Search.app"
```

校验失败时，使用包含打包修复的新构建；不要仅清除隔离属性来掩盖签名错误。SHA-256 一致只证明下载与发行附件一致，不代表附件本身的签名正确。

校验通过，且提示属于“无法验证开发者”或“Apple 无法检查此 App”时，按 Apple 的[安全打开应用说明](https://support.apple.com/zh-cn/102445)操作：

1. 先从“应用程序”尝试打开 **Smart Search** 一次。
2. 打开 **苹果菜单 → 系统设置 → 隐私与安全性**，向下滚动到“安全性”。
3. 在 Smart Search 的拦截提示旁点击 **仍要打开**，按需完成身份验证。
4. 在再次出现的确认窗口中点击 **打开**。以后可直接启动此 App。

未看到“仍要打开”时，再尝试启动一次后返回设置；受组织管理的设备可能不提供此操作。如果提示“将损坏你的电脑”或已检测到恶意内容，请停止打开并向项目反馈。

如果未公证测试包仍提示“已损坏”，仅在已核对官方来源、校验和及上述签名，且决定信任此测试包时，可清除这个应用的下载隔离标记后重新打开：

```bash
xattr -dr com.apple.quarantine "/Applications/Smart Search.app"
```

这只针对该应用，不需要关闭全局 Gatekeeper。ad-hoc 签名不验证开发者身份，也不等于 Apple 公证。

## 界面语言没有变化

App 在“设置与关于”选择语言，独立 CLI 用 `smart-search config set SMART_SEARCH_LANGUAGE zh` 保存偏好。如果 CLI 仍是另一种语言，检查单次 `--lang` 和 `SMART_SEARCH_LANGUAGE` 环境变量覆盖。`auto` 跟随 CLI 的 locale，可能与图形会话不同。可用 `smart-search --lang zh --help` 检查，不会改变设置。偏好无法读取时会提示并回退；修复该配置文件时保留服务商 Key。网页原文和第三方日志不随界面翻译。

## AI 接入仍显示待验证

在“更新 Skills”检查正式版并选择有差异的 Agent；仅软件版本变化不会要求同步 Skills。CLI 未就绪不阻止正文同步，但实际调用前仍需在“共用独立 CLI 环境”准备。设置页识别失败时，查看具体原因并点击“刷新已安装版本”，再检查更新。Skill 文件一致不代表 Agent 已加载，重新打开会话或使用 Gemini `/skills reload` 后验证实际版本。内容不同会先备份，结果显示恢复副本路径。详见 [App 配置](app.md)。
