# Outcome

按用户“把这个项目的图标换成这个，注意背景透明”的明确要求，将现有项目品牌图标替换为提供的人物图，保留透明背景并同步所有已有图标入口。

# Scope

- 基于已完成 Windows 自签名的 84ab6f9，新 worktree/分支 codex/desktop-brand-icon；签名任务的待验收现场保持独立。
- 复用 desktop/scripts/Build-Icons.ps1，更新 assets/branding/source.png、1024 PNG、Windows PNG/九尺寸 ICO、macOS 四尺寸 ICNS 和 Web UI 两处嵌入图标；README 沿用现有同名路径。
- 用户附件是唯一外观来源。实际附件为 1254×1254 RGB、无 alpha；使用内置 imagegen 去除深色背景并清理透明边缘，保留人物、配饰、两颗星星和原有底部裁切，不新增造型。

## Source coverage

| 来源 | 读取状态 | 要求 | Spec | 验收 | 覆盖 |
| --- | --- | --- | --- | --- | --- |
| 用户文字“图标换成这个”及所附完整图片 | complete | 替换现有标识，保持人物/星星/配饰 | specs/desktop-brand-icon/spec.md | A1/A2 | covered |
| 用户文字“背景是透明” | complete | 产物具备真实 alpha，不能将深色底当作图标背景 | specs/desktop-brand-icon/spec.md | A1 | covered |

# Non-goals

不改业务、布局、更新/签名机制，不发布版本、不替换本机已安装 App，不以新图标构建沿用旧二进制签名验收。

# Acceptance examples

以完整 Spec 的两项 Scenario 验证透明素材与既有图标入口一致性。

# Constraints and invariants

不覆盖原工作区未提交内容或签名验收记录，不批量删除。用户提供图像只用于其指定的项目图标，不引入新依赖或图标生成框架。

# Decisions

- 用户已直接指定要替换的图片和透明要求，没有待选择的视觉方向；按该明确授权执行可逆资源替换。
- 只去背景，不另画图标；复用现有确定性格式转换保持多端同源。
- 原附件实际无透明通道，已向用户说明并使用 imagegen 提取透明版本。
- 使用独立候选目录基于已签名实现继续，避免改动此前已经通过的签名产物。

# Open questions

无未决的用户需求问题。

# Verification expectations

检查源 PNG/输出 PNG/ICO/ICNS/Web 各帧的尺寸和真实 alpha，运行现有 tests/test_brand_assets.py 并确认重复生成一致；查看最终图标效果。必要的候选 Windows 构建只验证资源打包，不代表旧签名验收可沿用，也不代替实机 GUI 验收。
