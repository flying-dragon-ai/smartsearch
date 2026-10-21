# 原生 App 更新

## 平台与所有权

Windows 的 WinUI 3 前端使用 Velopack，macOS 的 SwiftUI 前端使用 Sparkle。框架拥有 App 更新的检查、下载、校验和应用安装；前端只接入 SDK、展示状态并执行产品已有的任务/草稿保护。Python sidecar 继续拥有搜索、配置、独立 CLI 和 Skills 业务，不再并行维护第二条 App 自更新下载/安装流程。

前端和冻结 Python 引擎必须作为一个版本整体交付。正常启动、框架安装/更新回调、单实例和重启不会互相阻塞；框架要求的早期回调先于正常窗口和后端启动。使用 Smart Search 自己的固定身份及官方 HTTPS 更新源。

### Scenario: Native frameworks own App updates
WHEN 安装当前候选并检查 App 更新，THEN Windows 实际进入 Velopack、macOS 实际进入 Sparkle，SDK 使用正确平台架构和稳定源；App 与内置后端版本一致，旧 Python App 下载/安装动作不再与框架同时执行，开发散包明确报告未安装或测试模式。

## 检查与提示

生产 App 启动后在到期时后台检查，运行期间至多每 24 小时自动检查一次；关闭自动检查后停止自动联网，保留手动检查。无额外后台服务，退出后不继续定时检查。自动检查只取元数据，不自动下载或安装 App。

发现更新以原生提示提供更新与稍后选项，同一版本在同一会话不重复打扰。正在进行不能打断的写入时先保留更新可用状态，直到可安全交互。页面展示当前版本、目标版本、检查状态和可重试错误；缓存不是本次成功检查，没有更新与检查失败可区分。中文和英文表达一致。

### Scenario: Background checks and explicit consent
WHEN 自动检查到期、用户关闭自动检查、手动重试或发现新版，THEN 检查频率和提示正确；未点击更新不下载或安装，稍后不会循环弹窗，关闭开关及退出 App 能停止后续自动检查，检查失败不显示已最新。

## 安装与安全退出

用户点击更新后由 SDK 下载、验证和安装。可显示框架提供的进度；可取消的阶段才提供取消，失败明确报告并可重试。下载完成不得宣称安装完成；重启后以实际 App/后端版本确认。

正式应用更新前继续执行现有未保存草稿、App 自有任务、CLI 升级和环境/Skills 写入门禁。必要时让用户保存/放弃草稿或等待任务，不强行停止外部 CLI。安全关闭 sidecar、释放单实例资源后由框架应用更新和重启。失败不丢弃配置或删除仍可用的正式程序。

### Scenario: Update and restart preserve active work
WHEN 存在草稿、自有任务或不可取消写入时请求安装，THEN 门禁生效且业务工作保留；解除门禁后 SDK 安装并重启，实际 App 和引擎均为目标版本；失败/取消不被记成成功，不终止外部 CLI。

## 差分与回退

CI 通过 Velopack/Sparkle 官方工具取回匹配平台、架构和渠道的上一版完整产物，生成并发布差分更新，同时保留目标版本完整包。Sparkle 更新使用递增且确定的 bundle version；同版本重打包不得悄悄覆盖正式基线。

没有历史版的首次发布只生成完整包并明确标记；下载旧基线失败、基线损坏或来源错误必须给出错误，不能伪装为首次发布。客户端在差分不可用、不适用或框架允许的差分失败情况下使用通过同等校验的完整包，不降低签名/来源要求。

### Scenario: Real delta update and full fallback
WHEN 为隔离的 A/B 两个版本打包并更新，THEN 两个平台各有真实差分包产出和 SDK 升级证据；结果版本/内容正确。移除或破坏差分后的完整包回退仍通过同等校验；缺失首版基线与基线下载失败分别记录，不把完整下载称为差分成功。

## 首次安装迁移与数据

Windows 新安装按当前用户使用 Velopack 布局，不要求管理员、不改变 CLI PATH。现有 Inno Setup 0.1.23 不能直接视作 Velopack 安装：提供一次完整安装和旧版处理引导，显示实际旧安装，避免把旧快捷方式误指认为新安装或两个程序互相更新。未经用户选择不静默卸载旧安装、不删除未知路径。

macOS 旧版没有 Sparkle 的安装需先完整替换一次 App，之后由 Sparkle 更新。现有配置、结果、独立 SmartSearchTools、全局 npm/mise CLI 和 Agent Skills 均在版本目录之外并保持原位置；本任务不自动迁移/删除这些用户数据。

### Scenario: First migration preserves user data
WHEN 从旧 Inno 安装或旧 macOS App 转入第一版框架安装，THEN 操作路径清楚、安装身份和启动入口准确，能继续使用原配置和结果；CLI/Skills/SmartSearchTools 保留，未确认时不卸载旧程序；完成一次完整安装后下一版可走框架更新。

## 签名与发布信任

Windows 使用现有 Smart Search 自签名身份，沿用固定公开证书、内容摘要与时间戳校验，签名失败阻止正式上传；保持第三方原有签名。自签名不等于系统公开信任。

Sparkle 使用 Smart Search 独立 EdDSA 身份与可信 HTTPS feed，正式更新包和差分包必须由配置的私钥签名并与 App 内置公钥匹配。测试使用隔离的临时密钥与 feed，不复用 Codex Tweaks 身份。Apple Developer ID 和公证可通过明确配置接入，但本次不承诺购买或取得资格；缺失时文案如实说明。当前缺失正式 Sparkle 身份时只交付测试候选，对应正式发布失败关闭。

### Scenario: Signatures and trust fail closed
WHEN 公钥不匹配、缺少正式密钥、下载包篡改或签名失败，THEN 正式发布或安装被阻止，不能降级到未签名正式更新。测试身份不能进入正式 feed，Secrets 不泄露，报告区分更新签名、Windows 自签名、Apple 代码签名、公证和系统信任。

## 平台与架构

保留 Windows x64/ARM64 与 macOS arm64/x86_64。前端、冻结 Python、框架 helper 与更新资产必须匹配。macOS 保留当前最低系统版本；使用分架构 feed 或框架支持的等价严格筛选，避免把一种架构安装到另一种架构上。

### Scenario: Architecture and bundle integrity
WHEN 构建和选择任一受支持架构的更新，THEN 包内前后端/helper/资源完整且架构匹配，错误架构、旧版本或不适用的更新不允许安装；真实原生构建和协议 smoke 分平台记录，不能把配置矩阵存在当作已经运行通过。

## CI/CD 与产物

GitHub Actions 在 PR/普通测试中构建可审查的测试产物，不向 PR 提供发布 Secrets。受信发布路径运行测试、构建、签名、框架打包、清单和版本检查；全部成功后才允许发布更新文件。复用现有 Release 流程、权限和稳定版本命名，保留显式发布控制；本次开发不自动创建/推送 Tag 或正式 Release。

更新 feed 与其引用的完整/差分资产必须对应同一版本，先验证资产存在再使其可被客户端发现；上传失败不得发布悬空清单。Sparkle feed 具有长期稳定地址。四架构候选、测试日志、哈希和版本信息作为可审查产物保留。

### Scenario: Release pipeline publishes complete updates
WHEN 执行测试或受信发布流程，THEN PR 无发布 Secrets；必要检查失败时停止发布；成功候选包含所需安装器、完整包、适用差分、feed 及校验信息，feed 引用均可解析且不跨架构。只改 workflow 未运行时报告为未运行。

## 独立 CLI 与 Skills

带入 `desktop-update-state-fix` 当前已验证行为：mise/npm 原来源升级后补齐目标包私有 Python，实际验证通过才成功，同版本未就绪允许显式重试；普通探测只读，两次 Windows probe 不继承阻塞的 RPC stdin。Skills 以托管文件内容判断差异，保留额外文件、本机调用注记和未选目标；按钮与选择、缓存及真实状态一致。

App 框架不接管外部 CLI 和 Skills 安装。关闭、替换或卸载 App 后外部 CLI 仍可独立工作。App 迁移候选对原修复代码的带入须可追溯，原候选/验收状态不被自动覆盖或归档。

### Scenario: Independent CLI and Skills stay healthy
WHEN 带入修复并完成 App 框架升级，THEN 原 CLI/Skills 回归继续通过，实际隔离 mise 升级无需用户手动运行版本命令触发修复；App 关闭后独立 CLI 可运行，测试不改真实全局安装或个人 Skills。

## 用户说明与证据

中英文手册、设置页和构建说明描述新更新方式、首次完整安装、失败重试、自动检查开关、签名性质和平台限制；不把“已下载”写成“已安装”，不把“已写入 workflow”写成“线上已通过”。淘汰旧 App 更新流程的当前文档与消费者同步更新，历史证据保留。

### Scenario: Delivery claims match actual evidence
WHEN 交付本次候选，THEN 当前代码、打包程序、测试日志和新只读复核可对应；报告单列本机 Windows、macOS/ARM64、GUI、真实用户安装、CI 与发布状态，任何未运行项保留未运行/受阻，不宣称正式已上线；用户数据和原工作区保持不变。
