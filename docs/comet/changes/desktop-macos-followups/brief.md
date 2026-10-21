# 目标

将 cr-zhichen 的三项 macOS 后续贡献整合到当前 main，保留作者已有测试证据、现有 Windows 与 Sparkle 更新能力。本轮用户原话为“cr-zhichen又提交macos上面的改动了，准备合并”；用户随后明确选择“按此方案整合并合入 main（推荐）”，授权最终测试通过后合并，包含现有 npm beta 自动流程，不包含新的稳定发行或本机安装修改。

# 范围

- #53：修复 Finder 显示隐藏文件时，DMG 背景和卷图标遮挡安装说明的问题。
- #55：接入维护者持有的稳定 macOS 自签名身份、临时钥匙串隔离、固定指纹验证、旧 ad-hoc 迁移及失败关闭。
- #57：统一下载文件名，增加 macOS Universal App/DMG、双后端原生选择、独立更新 feed、双架构验证和中英下载表。
- 在隔离分支保留三个 PR 的历史。建议先引入无冲突的 #53，再整合 #55/#57；不以整文件选 ours/theirs 覆盖双方需求。
- 对最终组合运行适用回归和完整桌面 CI，记录原 PR 与整合候选的不同证据边界；完成最终核验后再执行用户确认的主线合并。

## 来源覆盖

| 来源 | 读取状态 | 保留内容 | 对应验收 | 状态 |
| --- | --- | --- | --- | --- |
| 用户本轮请求 | complete | 合并准备、保留贡献者已测成果 | A6、A7 | covered |
| [PR53](https://github.com/konbakuyomu/smartsearch/pull/53) 描述及 a733b71fa8569efca40e2b7378d4d1bf64551ae3 | complete | 两隐藏资源坐标、隐藏标记、16pt 标签；保留 Finder/codesign 实测及原有后端超时限制 | A1、A6 | covered |
| [PR55](https://github.com/konbakuyomu/smartsearch/pull/55) 描述、维护者指南及 3ad3c8365cb7b84815641db76130501e0265d786 | complete | 稳定证书身份、临时钥匙串、正式配置失败关闭、签名/迁移负例、EKU 校验；启动检查对齐 App 的 30 秒超时并保留初始化后的 5 秒 IPC 检查 | A2、A3、A5、A6 | covered |
| [PR57](https://github.com/konbakuyomu/smartsearch/pull/57) 描述及 15e4ce28b1db9d2086d34b7d74bd38e44d82fa48 | complete | 五个下载入口、通用包双后端/双架构、改名兼容、发布说明、隐藏目录附件上传 | A3、A4、A5、A6 | covered |
| 当前 main c05ad78、v0.1.24 及发布工作流 | complete | Windows Velopack 身份、既有 Sparkle 公钥、正式发行与本机安装边界 | A4、A5、A7 | covered |

# 非目标

- 本轮准备不发布 v0.1.25、不覆盖 v0.1.24 附件、不改已发布 Tag、不替换本机 App/CLI、不同步个人 Skills。
- 不在准备阶段生成或设置 macOS 正式私钥，不接收贡献者测试身份作为项目长期身份；证书生成和正式发布另行明确安排。
- 不购买 Developer ID、不增加 Apple 公证，不将自签名称为 Apple 信任。
- 不重做工程师界面，不因当前宿主没有 Mac 而抹去作者明确记录的 Mac 实测；本方不执行 GUI 自动化。

# 验收示例

完整行为与 7 项 Scenario 见 specs/desktop-macos-followups/spec.md；来源表中的 A1–A7 对应该文件顺序。测试通过只能按实际版本与范围记录，不能把三份独立 PR 的结果直接视为组合候选通过。

# 约束与不变量

- 基线 main 为 c05ad78cd14a9811055a5f746f8922161c01b54b；工作区 smartsearch-desktop-macos-followups，分支 codex/desktop-macos-followups。原主目录与其他候选的未提交工作保留。
- 当前三 PR 均从同一 main 分叉，不互相包含；#53 与其余两个没有文本冲突，#55/#57 存在 8 个文本冲突。
- 冲突文件：.github/workflows/desktop-build.yml、desktop/README.md、desktop/scripts/build-macos.sh、desktop/scripts/test_sparkle_updates.py、desktop/scripts/update_artifacts.py、desktop/scripts/verify_macos_dmg.py、docs/windows-signing.md、mise.toml。
- 还需同步调整无文本冲突的新文件：#57 的 package-macos.sh 目前固定 ad-hoc 签名，release_notes.py 固定输出 ad-hoc 文案；Universal 构建/验证 job 也必须接入 #55 的签名上下文及指纹校验。只消除冲突标记不能视为整合完成。
- 正式 Mac 代码签名需要 SMART_SEARCH_MACOS_P12_BASE64、SMART_SEARCH_MACOS_P12_PASSWORD、SMART_SEARCH_MACOS_CERT_SHA256；当前仓库列表均未配置。现有 Windows 与 Sparkle 身份保留。这是下一次正式发布前提，不是读取/整合代码的阻塞。
- Windows 安装器改名不能改变 Velopack package ID、渠道或 NUPKG 身份；Mac 按架构 feed 地址保留，Universal 使用独立 feed。

# 决策

- 2026-09-22：将三个当前开放的 cr-zhichen PR 纳入准备范围，实际组合方案在本 brief 与 Spec 中明确后请求确认；尚未执行正式合并、推送或发布。
- 2026-09-22：只读 git merge-tree 已确认 #55/#57 的 8 个冲突，#53 可以独立干净组合。采用“DMG 修复先引入，签名与通用包一起整合验证”的建议顺序。
- 2026-09-22：发现作者继续提交后，已将 #55 基线从 e4c203d 更新到 827e894，将 #57 从 7f4186c 更新到 15e4ce2；新增差异分别是 EKU 精确校验与隐藏目录 artifact 上传。实施前再次核对远端 HEAD。
- main 推送会触发现有 npm beta 预发布工作流；本次尚未推送 main。新的稳定版桌面发布与正式签名配置不包含在当前“准备合并”的执行中。
- 2026-09-22：用户明确确认一起整合 #53、#55、#57，保留稳定签名，处理 8 处冲突和 Universal 联动，最终测试通过后合入 main；无需重复请求相同合并授权。发布稳定版、修改本机安装及正式 macOS 身份配置仍不在本轮范围。
- 2026-09-22：实施中纳入作者 #55 的 3ad3c83 启动诊断修正。三个 PR 的贡献提交均以 merge 保留；共享打包器、Universal ARM/Intel 验证和发布说明已衔接签名模式及固定指纹，实际效果以最终组合 CI 为准。

# 待解决问题

无未解决的用户决定。整合与主线合并已获明确授权；最终组合 CI 和独立验收完成前不执行主线合并。按精确提交记录成功、失败、等待与跳过；不以来源 PR 的旧结果代替最终组合检查。

# 验证预期

- 保留 PR53 的七项 CI 成功及作者 Finder 布局/实际 DMG 证据；保留其原始与重打包版本均曾出现的 15 秒后端 smoke 超时说明，不擅自改记为已解决。
- 保留 PR55 的作者完整 pytest、真实签名负例、arm64 App/DMG、Sparkle 四场景证据，以及最新追加 EKU 回归的独立状态。
- 保留 PR57 的作者打包测试、双架构组成、ARM 启动/退出、Sparkle 通用包升级证据；最新 CI 的 Universal ARM 和原生 Intel 安装任务需要实际完成。
- 整合后执行打包检查、必要 Python 回归、两 Windows 架构、两 Mac 原生包、Universal ARM 与同包原生 Intel 验证；核对固定身份和签名回执、原/新命名基线、差分/完整回退、错误公钥拒绝、ad-hoc 迁移。
- 合并前核对 PR HEAD 与测试 SHA、主线无新增冲突、最终完整验收报告及实际授权范围。GUI 与真实系统权限继承由用户/工程师验证，报告单列，不能以 CI 代替。
