---
generated_from_state_version: 14
---

# 验证

## 当前结果

- 结果: **已归档**
- 验证情况: **已完成检查，验证结果已确认**
- 目标周期: 1
- 迭代: 2
- 验证器尝试次数: 1
- 完成时间: 2026-09-20T19:08:24.579Z
- 摘要: 独立只读核验完成：9/9 通过。未重跑已有全量检查，未改文件、未提交 Runtime。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | specs/desktop-agent-skills/spec.md | Trusted stable source WHEN 最新正式版比 App 内置副本更新，THEN 页面以官方稳定版归档中的 Skills 为基准，显示版本与检查时间；不执行远程代码，不使用 main 或预发布版本。 | 固定 npm latest 元数据源，拒绝非稳定版本、非预期 tarball、重定向和未通过 SHA512/归档校验的内容；只将归档作为数据读取。src/smart_search/desktop_skills.py:25-91；src/smart_search/desktop_updates.py:23-30；tests/test_desktop_skills.py:103-125。 |
| A2 | passed | specs/desktop-agent-skills/spec.md | Download failure preserves installations WHEN 网络失败、重定向不可信、摘要不符、归档路径越界或含特殊文件，THEN 检查失败可重试，已安装的 Skill 保持不变，旧缓存不得冒充本次最新检查成功。 | 校验或网络失败只置错误/缓存状态并禁用同步，不进入 Agent 写入；归档路径、类型、大小和摘要均校验。src/smart_search/desktop_skills.py:25-70,158-193；tests/test_desktop_skills.py:96-155。 |
| A3 | passed | specs/desktop-agent-skills/spec.md | Automatic checks do not install WHEN 到达自动检查周期，THEN 至多一个检查任务运行，只更新缓存与提示；关闭自动检查后不再自动联网；只有用户点击安装或更新所选目标才写入 Agent 目录。 | Skills 自身以 auto_check 与 24 小时节流控制，checking/busy 防止重复任务；自动检查仅下载缓存，写入只从显式 confirm 的 sync 进入。src/smart_search/desktop_skills.py:154-170,195-223；src/smart_search/desktop_backend.py:590-597；tests/test_desktop_skills.py:129-155。 |
| A4 | passed | specs/desktop-agent-skills/spec.md | Unified target list and honest status WHEN 打开页面，THEN Codex、Claude Code、Cursor、Copilot、Gemini、OpenCode、Cline、Roo Code 及保留目标在同一列表，显示准确目标路径、Skill 内容状态、差异文件和历史目录提示；刷新保留用户选择。 | 17 个共享注册目标含 Codex、Claude、Cursor、Copilot、Gemini、OpenCode、Cline、Roo 及保留项，状态返回路径、差异与历史位置；两端页面保留选择。src/smart_search/skill_installer.py:33-58,380-436；desktop/windows/MainWindow.xaml.cs:1125-1164；desktop/macos/Sources/SmartSearchDesktop/AppModel.swift:833-836；desktop/macos/Sources/SmartSearchDesktop/ContentView.swift:1212-1246。 |
| A5 | passed | specs/desktop-agent-skills/spec.md | Invocation stays consistent WHEN 已有 Skill 写着旧 CLI 路径而当前独立 CLI 路径改变，THEN 更新根据当前已验证独立 CLI 重建本机调用说明，状态和安装比较同一份预期内容，更新后不会因该说明一直显示有差异；通用 CLI 比较识别本机说明，不误报纯注记差异。 | 本机独立 CLI 注记由 with_invocation 重建，比较时剥离历史本机注记以避免永久差异，而实际同步比较完整预期字节。src/smart_search/skill_installer.py:89-115,351-373；src/smart_search/desktop_skills.py:138-152,205-206；tests/test_desktop_skills.py:60-93。 |
| A6 | passed | specs/desktop-agent-skills/spec.md | Selected updates preserve user files WHEN 用户更新指定目标，THEN 只写所选目标的托管文件，先备份不同内容，保留用户额外文件和其他目标，返回备份位置；重复同步相同内容不重写、不重复备份。 | 仅逐个所选目标写托管文件；不同内容先整目录备份，额外文件不在 changes 中，重复相同内容返回空备份且不写入。src/smart_search/skill_installer.py:129-182；src/smart_search/desktop_skills.py:212-227；tests/test_desktop_skills.py:60-93,172-187。 |
| A7 | passed | specs/desktop-agent-skills/spec.md | Unsafe targets and write failures WHEN 目标含链接、越界路径或写入失败，THEN 拒绝不安全写入，旧内容保持可恢复，显示失败和备份位置；并发环境安装、CLI 更新与 Skills 同步不能交叉写入。 | 共享写入先拒绝 symlink 与 Windows reparse point（含 Python 3.10/3.11 junction），使用跨进程 file_lock，并在失败时恢复已替换文件且保留备份。src/smart_search/skill_installer.py:118-181；src/smart_search/state_files.py:14-53；tests/test_desktop_skills.py:211-225。Runtime 绑定的完整 pytest 已通过真实 junction 回归。 |
| A8 | passed | specs/desktop-agent-skills/spec.md | Clear native pages WHEN 用户使用任一平台或语言，THEN 可以区分检查最新 Skills、更新所选 Skills 和共用 CLI 环境准备，看到结果、备份路径与重新加载说明；无收费搜索被自动触发。 | Windows/macOS 均提供“更新 Skills”专页、正式版检查、选择后确认同步、备份结果、重载说明和独立 CLI 区域；操作只调用 Skills/环境 RPC，不自动触发搜索。desktop/windows/MainWindow.xaml.cs:546-589,1114-1185；desktop/macos/Sources/SmartSearchDesktop/ContentView.swift:1172-1246；desktop/macos/Sources/SmartSearchDesktop/AppModel.swift:588-601。 |
| A9 | passed | specs/desktop-agent-skills/spec.md | Regression and evidence boundaries WHEN 提交候选实现，THEN 隔离目录与协议回归、双语资源检查、Windows 构建通过；App/CLI 原有搜索、配置与环境功能保持兼容。GUI 手测、macOS 实机、正式安装、发布和真实 AI 调用分别标记，不能由静态检查代替。 | 当前 candidate/worktree 绑定的 Runtime 回执均 passed：完整 pytest（含真实 junction）、Skills 镜像一致性、diff --check、Windows x64 原生与冻结后端构建、C# 原生 RPC 生命周期；回执绑定 candidateId、scope A1–A9 和本工作区。.desktop-artifacts/skills-verifier-dispatch-2.json:1；.comet/runtime/native/changes/desktop-agent-skills-update/logs/checks/cc58117e-3d09-41da-8742-0f9b52a457ef-windows-build.log:86。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| Python full regression with real Windows junction | -m pytest -q | . | passed | 0 | 41793 ms |
| Public and packaged Skill parity | npm/scripts/check-skill-parity.js | . | passed | 0 | 53 ms |
| Patch whitespace | diff --check | . | passed | 0 | 78 ms |
| Windows x64 native and packaged backend build | -NoProfile -File desktop/scripts/Build-Windows.ps1 -PythonPath .venv/Scripts/python.exe -Architecture x64 -InstallerMode Skip | . | passed | 0 | 50977 ms |
| Native C# backend lifecycle protocol | run --project desktop/tests/BackendLifecycleCheck -- D:\Dev\20_个人项目\智能搜索\smartsearch-desktop-agent-skills-update\.venv\Scripts\python.exe D:\Dev\20_个人项目\智能搜索\smartsearch-desktop-agent-skills-update\.desktop-artifacts\skills-lifecycle-config | . | passed | 0 | 3003 ms |

### Builder 报告的证据

以下为 Builder 报告，不等同于 Runtime 检查凭据或独立验收结果。

- targeted regression and real Windows junction: passed — 162 passed, 1 symlink privilege skip. Real junction refused without Path.is_junction; existing outside files unchanged.
- prior full Runtime suite/build/protocol: passed — Previous candidate 914 passed,2 skips and Windows build/C#RPC passed. Final rebuild and regression requested for repaired candidate.
- 已知限制: GUI manual testing belongs to user; no GUI automation.
- 已知限制: No macOS/ARM64 native build or device verification on Windows x64.
- 已知限制: No release/commit/push/official App replacement or real personal Skill writes.

## 阻塞项

_无。_

## 风险与跳过的工作

- 未执行用户负责的 GUI 手测、macOS/ARM64 实机、正式安装/发布或真实 Agent 调用；这些限制已在 Builder handoff 与 Spec A9 中明确标记，不能由本次 Windows 静态/构建证据替代。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | execution-error | — | 独立只读Verifier运行超过项目单轮10分钟核查阈值；已报告A7旧Python junction漏洞，但多次收束请求后未返回完整9项结果，主代理中断该执行并保留现有证据。主代理已在隔离目录以真实Windows junction复现。先修复已确认缺陷，再使用新候选重新验收，不把本轮当通过。 | 2026-09-20T18:50:54.793Z |
| 1 | 1 | 1 | recovery | — | 复核已发现并实际复现旧Python的Windows junction写入绕过；保持已确认需求，回Build修复共享安全写入并增加真实junction回归。 | 2026-09-20T18:51:03.872Z |
| 1 | 2 | 1 | pass | — | 独立只读核验完成：9/9 通过。未重跑已有全量检查，未改文件、未提交 Runtime。 | 2026-09-20T19:08:24.579Z |



## 结论

独立只读核验完成：9/9 通过。未重跑已有全量检查，未改文件、未提交 Runtime。
