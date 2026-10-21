---
generated_from_state_version: 16
---

# 验证

## 当前结果

- 结果: **已归档**
- 验证情况: **已完成检查，验证结果已确认**
- 目标周期: 2
- 迭代: 2
- 验证器尝试次数: 1
- 完成时间: 2026-09-22T14:31:24.535Z
- 摘要: Runtime 五项绑定检查均通过；当前候选的 Windows 源、App 和 standalone CLI 哈希均与回执一致。上一轮 A2/A7 的错误恢复入口及 A8 的双语指南不一致已修复；未发现新的失败验收项。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | specs/desktop-guided-setup/spec.md | 保留导航功能与卡片风格 WHEN 浏览全部页面，THEN 六项导航与现有业务功能仍可访问，概览及App更新、环境、Skills等功能组保留统一卡片，未变成散放的文字和按钮。 | Windows 保留六项 NavigationView，macOS 保留六个 Destination；概览和各功能页仍使用既有原生卡片/面板结构。 |
| A2 | passed | specs/desktop-guided-setup/spec.md | 统一环境入口 WHEN 在设置、Skills及业务页面查看环境状态，THEN 不重复整套CLI管理；完整操作进入概览的本地环境区，未就绪时给清楚原因与可用的准备动作。 | 完整 CLI 管理仅在概览的本地环境区；未就绪页指向概览。两端失效 CLI 错误已改为概览本地环境的重新检测或选择入口。 |
| A3 | passed | specs/desktop-guided-setup/spec.md | 发现mise全局shim及工具安装 WHEN Smart Search由mise单独管理且不在Node的npm全局prefix，THEN App沿shim/管理器找到实际安装并显示mise来源；探针无安装副作用，更新使用mise且保持该管理器所有权。 | mise 全局 shim/工具解析、所有权和原管理器更新由当前实现处理；Runtime 的隔离 npm/mise 管理检查及真实 mise 只读发现均通过。 |
| A4 | passed | specs/desktop-guided-setup/spec.md | 发现普通npm及多安装 WHEN Smart Search由普通npm安装，或机器有多个Node/npm/工具安装，THEN 能找到并固定所选有效安装，手动选择可覆盖自动选择，安装/更新使用对应管理器和prefix，不覆盖其他安装或全局设置。 | Runtime 管理检查覆盖多个 npm 安装、显式选择、失效手动路径不静默回退、含空格路径及原 prefix/manager 操作。 |
| A5 | passed | specs/desktop-guided-setup/spec.md | 旧格式安全兼容与可解释失败 WHEN 已有旧版包装器或损坏/不兼容安装，THEN 不自动执行会下载Python的bootstrap；可安全确定已准备运行环境及兼容协议时连接，否则明确是旧版/不兼容/损坏并给更新或手动下载路径，不简单标作未安装。 | 旧 wrapper 仅在 manifest 明示 smartSearchBinary=true 时才能力探针；fixture 断言旧 wrapper 未执行，手动路径要求完整独立包与协议匹配。 |
| A6 | passed | specs/desktop-guided-setup/spec.md | 首次准备直到配置和测试 WHEN 没有可用环境，THEN 概览显示当前步骤及下一动作，按需引导获取Node/npm、安装/更新或定位Smart Search，完成后自动验证连接并继续配置服务商、显式测试及可选Skills；已完成步骤复用，不因移动App目录重装。 | 概览按本地环境、服务商、测试和可选 Skills 组织步骤；Runtime standalone 检查验证无 Node/npm 的手动独立 CLI 发现、握手、停止和重连。 |
| A7 | passed | specs/desktop-guided-setup/spec.md | 断线和发行阻塞可以恢复 WHEN 用户进入服务商等页面但CLI不可用，或网络失败/兼容版本尚未发布，THEN 页面解释实际状态并提供准备/重试/手动获取动作，不停在“本地引擎未连接”；无法安装时不展示假成功或无效下载。 | 两端缺失 CLI 的实际启动路径均给出概览本地环境恢复入口；Runtime BackendLifecycleCheck 已断言该错误路径，概览同时给出重试和手动下载/选择动作。 |
| A8 | passed | specs/desktop-guided-setup/spec.md | 单一更新动作与启动检查 WHEN 启动两次App且间隔不到24小时或手动检查，THEN 每次启动均检查（支持更新的安装包且偏好开启），发现新版后原按钮变为下载更新；无重复检查/跳过操作阵列，下载和安装状态真实，失败可重试。 | Windows 每个新进程激活时检查，macOS 启动时静默检查；主按钮在发现版本后变为下载更新，双语指南已同步为无常驻 24 小时 App 轮询。 |
| A9 | passed | specs/desktop-guided-setup/spec.md | API与路由字段可理解 WHEN 查看或填写服务商/路由字段，THEN 每个字段都有相关而非仅内部变量名的说明和适用示例，地址合同正确；帮助支持鼠标和键盘，示例/默认/真实值清楚区分，Key不泄露。 | Runtime metadata/i18n/docs 回归通过；字段 metadata 覆盖双语帮助、URL 示例和默认/占位边界，Windows 与 macOS 均提供悬浮、键盘/辅助功能和详情入口，秘密值不在详情中回显。 |
| A10 | passed | specs/desktop-guided-setup/spec.md | 保留数据与管理器边界 WHEN 检测、安装失败、切页、取消或更新，THEN 配置/Key/结果/Skills和未保存工作受保护；不自动迁移、更改管理器或删除任何用户文件。 | CLI 操作限定当前所选 npm/mise 管理器和 prefix；更新前保护草稿及 App 自有任务，配置写入保持锁与原子替换，Skills 保留/备份语义未变。 |
| A11 | passed | specs/desktop-guided-setup/spec.md | 可运行验证与双端一致 WHEN 交付候选，THEN 环境发现、步骤恢复、更新、字段帮助和UI资源有可运行回归，Windows构建与实际mise只读检测留有证据；Mac编译和GUI分别标记实际覆盖情况，未经授权不发布或替换正式安装。 | 5 项 Runtime 检查均通过；独立复算当前 19/19 Windows 源文件与 staging SHA-256 匹配，App 与 standalone CLI 哈希也匹配候选回执。回执明确标记 macOS 新改动、GUI 和实际安装升级为未运行，且未替换正式安装或发布。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Metadata, bilingual resources and generated references | -m pytest tests/test_ui_metadata.py tests/test_guide.py tests/test_i18n.py tests/test_desktop_skills.py -q | . | passed | 0 | 3327 ms |
| Native npm/mise ownership and multi-install selection | -NoProfile -Command $fixtureRoot = Join-Path (Get-Location) ('.desktop-artifacts/guided-runtime-fixture-' + [guid]::NewGuid().ToString('N')); & .venv/Scripts/python.exe desktop/scripts/create_npm_fixture.py $fixtureRoot 'C:/Users/dxt98/AppData/Local/mise/installs/node/24.16.0/node.exe'; if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }; dotnet run --project desktop/tests/CLIManagementCheck --configuration Release -- $fixtureRoot; exit $LASTEXITCODE | . | passed | 0 | 12518 ms |
| Standalone CLI detection and private protocol reconnect without Node/npm | run --project desktop/tests/BackendLifecycleCheck --configuration Release -- --standalone D:\Dev\20_个人项目\智能搜索\smartsearch-desktop-guided-setup\.desktop-artifacts\windows-x64-20260922T141833Z-57120-30e2b75e\backend-20260922T141833Z-54456-23ee1cfe\dist\smart-search\smart-search.exe D:\Dev\20_个人项目\智能搜索\smartsearch-desktop-guided-setup\.desktop-artifacts\guided-runtime-standalone-r2 | . | passed | 0 | 3529 ms |
| Read-only discovery of actual global mise installation | run --no-build --project desktop/tests/CLIManagementCheck --configuration Release -- --discover D:\Dev\20_个人项目\智能搜索\smartsearch-desktop-guided-setup\.desktop-artifacts\guided-runtime-real-mise | . | passed | 0 | 6066 ms |
| Diff whitespace validation | diff --check | . | passed | 0 | 117 ms |

### Builder 报告的证据

以下为 Builder 报告，不等同于 Runtime 检查凭据或独立验收结果。

- Post-repair focused tests: passed — 86 passed/1 host symlink skipped; includes manual frozen Skill invocation.
- Native missing CLI and standalone lifecycle: passed — BackendLifecycleCheck executed new missing-file guard and standalone stop/reconnect.
- Windows rebuilt candidate: passed — .desktop-artifacts\windows-x64-20260922T141833Z-57120-30e2b75e\result.json
- Mac native/GUI and actual candidate updater install: not-run — Local host lacks Mac toolchain; user GUI pending; portable build does not prove actual Velopack installation.
- 已知限制: Mac native compile and GUI of new changes not run; preserve prior PR51 baseline separately.
- 已知限制: Actual Agent invocation not tested; frozen Skill generation now covered and full path guide documented.
- 已知限制: Windows native updater SDK behavior preserved; this portable candidate has no actual upgrade/install receipt.
- 已知限制: Compatible npm publication remains paused; no real user CLI/App replacement, commits, push or release.

## 阻塞项

_无。_

## 风险与跳过的工作

- 本轮 macOS 新改动未在本机原生编译或运行，GUI 仍待用户验收；PR51 保留的两端基线证据不能替代这些新增 macOS 改动的验证。
- 当前 Windows 候选是 portable build，未取得本轮 Velopack 实际安装、下载、差分回退或升级回执。
- 手动独立 CLI 的 frozen Skill 生成和完整调用说明已有回归，但没有真实 Agent 调用回执。
- 兼容 npm 发布仍暂停；未替换真实用户 App/CLI，未提交、集成、推送或发布。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-22T13:57:18.699Z |
| 2 | 1 | 1 | fail | A2, A7, A8 | Runtime 五项检查均通过，且 19/19 Windows staged-source 哈希仍匹配当前候选；A2/A7 的失效 CLI 恢复入口和 A8 的双语更新指南不一致使本轮不能通过。 | 2026-09-22T14:15:19.529Z |
| 2 | 2 | 1 | pass | — | Runtime 五项绑定检查均通过；当前候选的 Windows 源、App 和 standalone CLI 哈希均与回执一致。上一轮 A2/A7 的错误恢复入口及 A8 的双语指南不一致已修复；未发现新的失败验收项。 | 2026-09-22T14:31:24.535Z |



## 结论

Runtime 五项绑定检查均通过；当前候选的 Windows 源、App 和 standalone CLI 哈希均与回执一致。上一轮 A2/A7 的错误恢复入口及 A8 的双语指南不一致已修复；未发现新的失败验收项。
