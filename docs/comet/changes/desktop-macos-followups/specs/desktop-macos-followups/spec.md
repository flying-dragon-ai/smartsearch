# macOS 后续贡献整合

## DMG 布局

保留现有应用与 Applications 图标、窗口和 Retina 背景，将 .background.tiff 与 .VolumeIcon.icns 定位于初始窗口外 (330, 1000)，显式设置隐藏标记，标签字号为 16pt。不能给已签名 App 添加破坏资源封印的 FinderInfo。

### Scenario: Hidden resources do not cover installation instructions
WHEN 用户在 Finder 开启显示隐藏文件并打开生成的 DMG，THEN 安装说明无遮挡，布局和隐藏标记符合规格，挂载与复制安装后的 App 签名仍有效；保留作者原始实测范围。

## 稳定身份及失败关闭

复用维护者的一套 macOS 代码签名证书、私钥与固定 SHA-256，两架构和后续版本使用同一身份。P12、密码只进入受控签名子进程和临时钥匙串，不进入源码、日志或 artifact，不更改系统信任设置。验证证书用途、有效期、指纹、私钥与完整代码签名。App 的 designated requirement 绑定证书和 bundle ID，不能依赖随版本改变的 cdhash。

普通 PR 使用一次性测试身份；正式候选缺配置或验签失败必须停止，不能降级。测试证书与正式身份分别标记，公开证书不等于私钥。当前准备不生成正式身份；下一正式发布前另行配置并验证。

### Scenario: Stable identity and signing failures are preserved
WHEN 使用测试身份、正确维护者身份、错误密码/证书、无代码签名用途、过期证书或缺失正式配置进行打包，THEN 仅有效身份可以用于相应模式；错误状态被拒绝，清理临时钥匙串，所有 Mach-O 架构、嵌套代码和复制安装后的 App 被逐项验证，秘密不泄露。

## Universal 组成及签名

保留 arm64、x86_64 独立包，新增 Universal 前端和原生 launcher；两套完整 PyInstaller 分发不混合其嵌入档案，由运行架构选择配套后端。输入版本、bundle ID、最低系统、共享资源、Sparkle 公钥和更新设置一致。Universal 独立 feed 在后续更新中继续保留双架构。

完成组成后，从内到外以 #55 的相应身份签署全部代码，不能被 #57 的 ad-hoc 默认步骤覆盖。正式 Universal 与两个正式独立包使用同一维护者证书；测试身份不得用于正式上传。

### Scenario: Universal packaging keeps both backends and the intended identity
WHEN 构建 Universal 并从同一 DMG 在原生 ARM 与 Intel 上复制安装和启动，THEN 前端和 launcher 包含双架构、后端选择正确、参数/stdin/stdout/退出码保持、复制路径变化不影响启动，两个后端版本一致；最终签名及固定指纹符合当前构建模式。

## 下载与历史兼容

五个安装入口分别为 Mac Universal、Mac arm64、Mac x86_64、Windows x86_64、Windows ARM64，使用 PR57 的 SmartSearch-vX.Y.Z 命名。Windows Velopack ID、渠道与 NUPKG 身份不变。Mac feed 保留原架构地址并新增 Universal 地址；旧 v0.1.24 Sparkle ZIP 名称仍可作为正确架构的更新基线，独立包不能冒充 Universal 基线。

完整包、适用差分、安装器、签名回执和校验表必须完整一致，拒绝同名覆盖、缺失附件、错架构、错误指纹及非法 URL。全部附件上传成功后才更新带受控标记的双语下载表，重复操作保留用户原版本说明。签名文案与真实构建模式一致，不继续硬编码 ad-hoc。保留 Apple 官方首次允许打开说明，区分开发者未验证与损坏/恶意提示。

### Scenario: Renamed assets remain compatible and download tables are complete
WHEN 从已发布 v0.1.24 获取基线并生成下一候选的发布集合，THEN 旧名称可正确识别，更新器身份和原 feed 地址不变，五个安装链接存在，三种 Mac 资产与签名回执齐全；发布表幂等且不覆盖原说明，签名与公证声明真实。

## 更新与迁移

保留现有 Smart Search Sparkle Ed25519 更新密钥、Windows 自签名身份和用户数据路径。按独立包与 Universal 的实际布局修改更新测试的所有后端版本清单；同证书版本升级、差分、损坏差分完整回退、错误更新公钥拒绝与旧 ad-hoc 迁移不能因整合而丢失。

### Scenario: Native update regressions survive integration
WHEN 运行最终组合的 Windows 与 Mac SDK 更新检查，THEN 各自的差分/完整回退和错误签名检查通过，Mac 同证书升级与旧 ad-hoc 迁移保持，Universal 更新后仍具双后端；未实测的 GUI/权限继承明确单列。

## 测试证据与合并边界

保留每个工程师提交及已记录的测试范围。最新 PR HEAD 与旧通过结果分开；最终组合必须有自己的检查，不因三份 PR 分别通过而声称组合通过。CI 的 Universal artifact 上传包含隐藏路径，Intel 验证使用同一 DMG，必要任务失败阻止发布。不得通过删除测试、放宽固定指纹或选择性忽略失败完成整合。

### Scenario: Final integration is checked against its exact source
WHEN 提交整合候选供合并，THEN 来源提交可追溯，文本与无文本冲突的行为联动均被处理，打包检查、共享回归、两 Windows、两 Mac 原生包与 Universal ARM/Intel 检查绑定最终代码；作者原始证据保留，失败/等待/跳过与通过分开。

## 范围与用户环境

当前阶段只准备整合，不修改主线、已发布 v0.1.24、本机安装、个人 Skills 或无关脏工作区。实际合入 main 使用用户确认后的候选，保留全部贡献历史；main 推送会触发现有 npm beta 流程，不能将其描述为没有任何发布副作用。新的稳定发行、正式私钥生成和本机替换需另行明确安排。

### Scenario: Preparation and delivery preserve existing releases and user work
WHEN 完成准备或后续授权的主线合并，THEN 操作与授权相符，原工作区和现有发行附件保留；准备阶段不发布或安装，合并阶段准确报告自动 beta 行为，正式签名配置和 GUI 验收的未完成边界继续保留。
