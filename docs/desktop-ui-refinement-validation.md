# 桌面界面修复验证（本地候选）

## 输入与复用

- 基线：已发布 `main` 的 `83b8b409`。本轮没有提交、合并、推送或替换本机正式安装。
- 用户补充的 Claude 分支：`1462bef728c453ad82ca1e820faa58f935460de3`，包含 6 个界面修复提交。在独立 `smartsearch-cloud-ui-fix-check` 中保持产品文件不变，Windows 构建成功，Python 696 passed / 1 skipped。
- Claude 原版的 Windows 实际测试复现：输入合成 Exa Key 后，测试请求使用了新 Key，但页面重建清空了输入并跳回顶部。只禁用启动 RPC 的按钮也没有覆盖 worker 生命周期。深色标签对比度偏低、首屏仍为 AnySearch。未把这些问题带入最终候选。
- 复用 Claude 的 macOS 配置分组/BusyLabel、桌面命令中文说明及状态元数据；补齐对应调用端和持久忙碌状态。Windows 保留已实现的输入连续性和基础能力布局，不重复移植会丢输入的页面重建逻辑。

## 当前实现

- Windows 与 macOS 的请求忙碌和后台任务忙碌分别跟踪，任务收到 run_id 后继续禁止同一操作重复提交；终态补读用于恢复早到/漏收事件，断开清理状态。
- 未修改时显示“测试”，修改对应服务商后显示“用未保存的修改测试”。后台记录 current/draft 范围；桌面测试不保存配置或写正式健康记录。Web 明确传入空 overrides 与未传参数保持不同语义。
- 先呈现主搜索、文档检索和网页抓取；高级字段按 metadata 折叠，保存栏固定在底部。Windows 对已配置的选项优先显示，其他选项可展开。
- 主题资源控制主次文字、状态标签和卡片；路径和技术值使用等宽字体，窄窗表单改为上下排列。测试原始响应保留在技术详情。
- 切页/探针完成不清空未保存配置；保存、预览、刷新和切换配置目录互斥。macOS 补读结果不会覆盖完整活动记录，探针刷新不回滚 profile/revision。

## 已执行检查

| 检查 | 结果与证据 |
|---|---|
| Python 完整回归 | **699 passed, 1 skipped**；跳过项为 POSIX 专用。见 [日志](../.desktop-artifacts/integrated-pytest-final.log)。|
| 最终 Windows Debug x64 构建 | **0 warning / 0 error**；见 [构建日志](../.desktop-artifacts/windows-final-build.log)。使用唯一预览程序集名避免 Computer Use 与已安装同名 exe 混淆。|
| Windows 原生启动 | 最终产物已启动；[启动记录](../.desktop-artifacts/preview-launch.json) 和 [源码/程序集 SHA256](../.desktop-artifacts/final-source-hashes.json)。|
| Windows 等待与去重 | 合成本机 HTTP 延迟 10 秒，双击一次操作产生 **1 条** POST；界面显示测试中与禁用按钮。[截图](../.desktop-artifacts/ui-evidence/probe-busy.png)、[请求日志](../.desktop-artifacts/preview-requests.jsonl)。|
| Windows 输入保留 | 输入新 Key → 测试 → 切到活动 → 返回配置，输入仍在、修改计数为 1；完成后显示通过和测试范围。[控件记录](../.desktop-artifacts/ui-evidence/probe-finished-draft-preserved.txt)。|
| Windows 配置安全与保存 | 测试后隔离 config.json 仍为旧合成 Key，未生成 provider_health.json；主动保存后新合成 Key 写入、修改计数归零。真实配置未用于测试。|
| Windows 外观 | 深色、浅色、1069 像素宽窄窗、2560 像素宽最大化已查看；卡片左对齐、窄窗字段上下排、保存操作可见。[深色](../.desktop-artifacts/ui-evidence/providers-dark.png)、[浅色设置](../.desktop-artifacts/ui-evidence/settings-light.png)、[窄窗](../.desktop-artifacts/ui-evidence/providers-light-narrow.png)、[最大化](../.desktop-artifacts/ui-evidence/providers-light-maximized.png)。|
| 原生操作模型 | Windows Debug 启动执行 OperationState 自检；macOS 新增可运行的模型测试覆盖去重、后台生命周期、断开复位和元数据解析。|
| 独立 macOS 静态审查 | 检出了活动记录覆盖、探针刷新竞争和遗漏的反馈入口；已据此修正。正式验收另由新的只读 Verifier 判断。|

截图记录的是本轮同一界面实现的交互检查，随后只补了测试原始响应折叠、历史测试范围文案与完成时关闭旧“正在测试”提示；最终构建日志与源码哈希单列，不把较早截图冒充最后产物截图。

## 证据边界

- 全部业务测试使用隔离目录和 127.0.0.1 合成服务；没有调用真实计费 API。
- 连接失败、超时、取消、worker 崩溃、配置冲突、健康记录隔离等共享核心路径由 Python 回归覆盖。Windows GUI 已实测上述表格列出的关键路径；不声称每种异常与每个按钮都重复进行了手动界面测试。
- macOS 无本机 Swift/macOS 环境，**Swift build/test 与原生 GUI 均未运行**；源码和模型测试已提供。该限制沿用用户后续单独验证 macOS 的决定。
- 当前是本地候选，未签名、未发布、未替换已安装的 0.1.19。

## 独立验收后的补充

第一轮 A1/A2/A3/A4/A6/A8 通过；A5/A7 指出 macOS 活动事件阶段仍直出内部代码。已在 DesktopState.phaseLabel 统一复用命令中文标签和状态元数据，服务商测试、版本查询有显式名称，活动列表与详情均调用该映射；原始事件保留在高级详情。增加对应 Swift 模型测试。此修正仅涉及三份 macOS Swift 文件，Windows/Python 实现及已执行检查输入保持不变；Swift 测试仍明确未运行。
