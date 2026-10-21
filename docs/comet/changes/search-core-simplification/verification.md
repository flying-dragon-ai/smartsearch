---
generated_from_state_version: 27
---

# 验证

## 当前结果

- 结果: **验收通过，需要你确认**
- 验证情况: **已完成检查，但需要你确认验证结果**
- 目标周期: 3
- 迭代: 4
- 验证器尝试次数: 1
- 完成时间: 2026-09-23T13:37:59.445Z
- 摘要: A1–A10 全部通过。当前唯一未决项 A9 的 Jev/local 文档边界已修正并同步；其余结论复用输入未变的前轮独立验收和有效检查回执。

## 验收

| 编号 | 结果 | 来源 | 验收项 | 原因 |
| --- | --- | --- | --- | --- |
| A1 | passed | specs/search-core/spec.md | 最新 main 与 CLI 网页能力保留 WHEN 检查实施基线与交付树，THEN 实施分支包含已核对的 main，src/smart_search/assets/ui/index.html、ui_server、smart-search ui 入口及打包资源存在；已提交的上游能力保留，原 dirty 工作区保持原样。 | 当前 HEAD 为指定 main 916743469d8abf8d6eae300170d2bfd61fae4949，分支为 codex/search-core-simplification；工作区边界见 comet-state.yaml:13-16，180 项输入仍匹配已验证候选见 logs/checks/f8942a32-8433-47e1-94b5-64e87bafb2d9-unchanged-core-native-inputs.log:1。 |
| A2 | passed | specs/search-core/spec.md | 普通单轮没有隐藏研究步骤 WHEN 普通 search 使用默认、旧 hybrid 或显式 validation/extra-sources/研究配置，THEN 正常成功路径恰有一次 Jev 逻辑选路及一个渠道的单轮检索；无 embedding/classifier、Jev 选库、充分性评估、过滤、自动补搜或汇总。extra-sources 仅限制本轮结果数量。必要渠道依赖和失败兜底如实记录。 | 普通搜索限制为单轮并直接返回未评估结果，代码和回归证据见 src/smart_search/service.py:2253-2279、src/smart_search/jev_search.py:345-367,480-485、tests/test_search_modes.py:24-52；输入指纹确认这些代码未变。 |
| A3 | passed | specs/search-core/spec.md | 无 Jev 与旧配置不会启用另一条远程判断链 WHEN 新配置、旧 hybrid/rules/off、残留旧模型字段、缺失/失败/超时 Jev 或 fallback off 输入进入系统，THEN 行为符合上述映射，禁用远程路由得到尊重，无旧模型 HTTP 请求，用户配置与 Key 不被自动删除或改写，降级原因可见。 | hybrid→jev、rules/off→local，local 不调用 Jev 且旧字段保留的实现证据见 src/smart_search/intent_router.py:7-14、src/smart_search/jev_search.py:330-338,376,428-452；当前路由文档也明确 auto/off 与显式 local 边界，见 skills/smart-search-cli/references/provider-routing.md:11。 |
| A4 | passed | specs/search-core/spec.md | 深研按证据缺口组合动作并受控停止 WHEN 需要多来源或首轮证据不足，THEN 可并发多个互补渠道，按缺口换引擎/候选查询/读取正文，充分时提前停止；同 provider/操作/query/URL 不重复，预算和无新证据停止有效，保留实际执行记录，离线建议步骤不冒充已执行。 | research 使用统一执行器的有限多轮流程，按缺口继续并只引用已读取内容，证据见 src/smart_search/service.py:1597-1619、src/smart_search/jev_search.py:413-515,652-673、tests/test_jev.py:180-205、tests/test_search_modes.py:101-130；当前研究文档明确 Jev 或 local 路由，见 skills/smart-search-cli/references/deep-research-mode.md:35-38。 |
| A5 | passed | specs/search-core/spec.md | 模型与兜底不能突破允许渠道 WHEN 渠道缺凭据、禁用、被筛选排除、cooldown、仅允许显式调用，或 Jev 返回未知 ID/无效概率，THEN 不发出越界调用；失败保留其他渠道结果；同能力故障兜底不跨越这些限制。 | 允许渠道、cooldown、候选 ID 与概率校验及同能力兜底证据见 src/smart_search/jev_search.py:17-53,141-145、src/smart_search/jev.py:135-147,228-263、tests/test_jev.py:528-533；相关输入未变。 |
| A6 | passed | specs/search-core/spec.md | 同一时限内取消与保留部分结果 WHEN 存在慢 Jev、慢渠道、模型失败/重试、部分成功、取消或显式 timeout，THEN 使用真实剩余时限，普通默认仍 300 秒，终止及时、无期限后的新调用、已完成结果不丢失，尝试与停止原因真实。 | 共享 deadline、超时取消和保留已完成证据的实现及测试见 src/smart_search/service.py:330-416、src/smart_search/jev_search.py:320-321,455-465,584-610、tests/test_service.py:2977-3086、tests/test_jev.py:763-783；相关输入未变。 |
| A7 | passed | specs/search-core/spec.md | 检索成功不伪装研究或事实核验成功 WHEN 只有摘要、模型答案、库候选、部分正文或判断失败，THEN 区分检索状态、充分性与来源状态，普通模式不输出已充分核验结论，深研引用必须对应实际读取内容，缺口和部分状态可见。 | 普通结果标为 not_evaluated，research 引用限制为实际读取内容，证据见 src/smart_search/jev_search.py:480-485,538-543,601-610,652-673；相关输入未变。 |
| A8 | passed | specs/search-core/spec.md | 三种配置界面使用同一搜索合同 WHEN 核对 CLI 网页及基于 ccrui 已验证基准的两个原生端，THEN 显示有效的新路由方式及明确的深研参数，旧远程模型控件不再出现；保存继续走原有草稿/Key/原子保存/会话保护链，原生 CLI 环境管理不被重写。网页交互、共享 metadata/协议回归及原生增量源码核对提供本轮证据，继承基准测试与新平台实机测试分别标记。 | 网页及原生配置共享合同的回归证据见 tests/test_desktop_config.py:40-68；Windows 构建成功见 logs/checks/e9f96580-3ef2-41a0-907d-413596e1a188-windows-native.log:3-8，macOS 增量限定为路由显示和共享文案的源码核对见 logs/checks/e9f96580-3ef2-41a0-907d-413596e1a188-macos-baseline-delta.log:1。 |
| A9 | passed | specs/search-core/spec.md | CLI 与两份 Skill 无旧慢链路引导 WHEN 从 CLI/setup/help/agent-guide 或直接工具使用搜索，THEN 新旧配置映射和普通/深入边界一致，deep/route 默认保持离线，已退役校准不发网络请求，两份 Skill 一致且没有把旧路由作为正常操作的指导。 | 修正文档已说明 search/research 可走 Jev 或 local、普通 Jev 至多一次逻辑判断、缺 Key 或判断失败时 auto 本地兜底/off 失败、显式 local 不需 Key 且不调用 Jev：skills/smart-search-cli/SKILL.md:36-41、skills/smart-search-cli/references/provider-routing.md:7-15、skills/smart-search-cli/references/deep-research-mode.md:35-38,167；9 份公开/打包文件一致见 logs/checks/f8942a32-8433-47e1-94b5-64e87bafb2d9-skill-parity.log:1，退役指导扫描通过见 retired-guidance.log:1。 |
| A10 | passed | specs/search-core/spec.md | 候选回归和分发证据可复核 WHEN 交付架构精简候选，THEN 相关 Python、CLI/npm、网页/共享元数据、双语资源和 Windows 原生编译检查通过，ccrui 原生基准的提交及测试可追溯，本轮 macOS 搜索增量已核对，HTML 和指南仍随分发可用；独立 Verifier 覆盖所有场景与简化边界，未运行的新 macOS 编译/实机、真实 API 或完整用户 GUI 验收如实注明，个人安装及原工作区未被替换。 | 前轮 Python 1047 passed/19 skipped 与 Windows 构建证据仍适用于相同代码输入，见 logs/checks/e9f96580-3ef2-41a0-907d-413596e1a188-python-suite.log:16、windows-native.log:5-8；本轮 docs 回归 33 passed/1 skipped、9 份 Skill 同步、wheel 资源一致、退役措辞扫描和 diff --check 均通过，见本轮 f8942a32 检查日志及 .comet/runtime/native/changes/search-core-simplification/state.json:91-110。 |

## 检查

| 检查 | 命令 | 工作目录 | 状态 | 退出码 | 耗时 |
| --- | --- | --- | --- | ---: | ---: |
| unchanged-core-native-inputs | -c import hashlib from pathlib import Path files=sorted(p for root in ['src','tests','desktop','npm','scripts'] for p in Path(root).rglob('*') if p.is_file() and p.suffix in {'.py','.cs','.swift','.json','.html','.js','.csproj','.toml','.sh','.ps1'} and not any(part in {'bin','obj','__pycache__','.build'} for part in p.parts) and 'assets/skills' not in p.as_posix()) digest=hashlib.sha256() for p in files: data=p.read_bytes() if p.as_posix()=='tests/test_regression.py': for new,old in [('"public live executor",','"public live executor entrypoint",'),('"`smart-search research` is the public live executor",','"`smart-search research` is the public live executor command",'),('"does not change default `smart-search search` behavior",','"must not change default `smart-search search` behavior",'),('"`research --fallback auto` permits local outage fallback and follow-up searches",','"`research --fallback auto` permits same-capability fallback",')]: data=data.replace(new.encode(),old.encode()) digest.update(p.as_posix().encode());digest.update(b'\0');digest.update(data);digest.update(b'\0') assert len(files)==180 assert digest.hexdigest()=='84ceb3b5820085ffb4cabbe5a353391e0e6d4bfb91b95c23ddf39f84d9d4b698',digest.hexdigest() print('180 code/test/build inputs match the 1047-pass + Windows/Mac-baseline verified candidate; only four document assertion phrases were updated. Skills excluded here are checked separately.') | . | passed | 0 | 108 ms |
| docs-regression | -m pytest tests/test_regression.py tests/test_guide.py tests/test_desktop_skills.py -q --tb=short --show-capture=no | . | passed | 0 | 1697 ms |
| skill-parity | npm/scripts/check-skill-parity.js | . | passed | 0 | 60 ms |
| diff-whitespace | -c core.safecrlf=false diff --check | . | passed | 0 | 121 ms |
| wheel-resources | -c from pathlib import Path from zipfile import ZipFile with ZipFile('C:/Users/dxt98/AppData/Local/Temp/smartsearch-core-wheel/smart_search-0.1.25-py3-none-any.whl') as z: for p in Path('src/smart_search/assets/skills/smart-search-cli').rglob('*'): if p.is_file(): assert z.read(p.relative_to('src').as_posix())==p.read_bytes(),p for name in ('service.py','config.py','jev_search.py','intent_router.py','desktop_catalog.py','ui_metadata.py','assets/ui/index.html','assets/i18n/messages.json'): assert z.read('smart_search/'+name)==Path('src/smart_search',name).read_bytes(),name print('Current wheel matches repaired Skills and previously verified runtime/UI resources.') | . | passed | 0 | 75 ms |
| retired-guidance | -c from pathlib import Path for root in ('skills/smart-search-cli','src/smart_search/assets/skills/smart-search-cli'): text='\n'.join(p.read_text(encoding='utf-8') for p in Path(root).rglob('*.md')) for retired in ('Hybrid remote routing','two thirds of the budget','up to 240 seconds','Tavily receiving about 60%','only when neither Tavily nor Firecrawl', 'synthesis or discovery', 'Automatic routes select Context7', 'reinforcement selects Zhipu', 'single-pass retrieval: one Jev judgment', 'bounded Jev loop'): assert retired not in text,retired print('No retired extra-source allocator or hybrid reserved-budget instructions in either Skill tree.') | . | passed | 0 | 58 ms |

### Builder 报告的证据

以下为 Builder 报告，不等同于 Runtime 检查凭据或独立验收结果。

- docs-regression: passed — 33 passed、1 skipped；随后at most两词澄清交由Runtime重检。
- skill-parity: passed — 9文件匹配，最终副本由Runtime重检。
- wheel-build: passed — 当前文档已重新打包。
- 已知限制: 复用前轮1047 passed/19 skipped、Windows构建及ccrui PR51/PR61基准/源码增量；Runtime将再次校验180项输入指纹。
- 已知限制: 新Mac二进制未编译/实机运行，完整原生GUI保存重开及真实计费API质量耗时对比未执行。
- 已知限制: 未提交推送发布或替换个人安装。

## 阻塞项

- **user**: The generic Skill bridge cannot prove an independent Verifier execution; user confirmation is required before Archive. — next: `await-user`

## 风险与跳过的工作

- 新 macOS 二进制未编译或实机运行；PR51/PR61 基准加本轮源码增量核对不代表新二进制通过。
- 完整原生 GUI 保存重开验收、真实计费 API 的质量与耗时对比尚未执行。
- 记录中有 19 项 Python 测试和 1 项文档回归测试跳过；未将其计作通过。
- 本候选未提交、推送、发布或替换个人安装。

## 之前的迭代

| 目标周期 | 迭代 | 尝试 | 结果 | 未解决项 | 摘要 | 完成时间 |
| ---: | ---: | ---: | --- | --- | --- | --- |
| 1 | 1 | 1 | fail | A6, A8, A10 | A6 因显式取消会丢失已完成证据而失败；A8 与 A10 因本轮 macOS 原生改动缺少编译及交互证据而阻塞。其余验收项通过。Runtime 回执来自候选 worktree，未重跑完整套件或调用真实 provider。 | 2026-09-23T10:24:31.310Z |
| 1 | 2 | 1 | blocked | A8, A10 | A1-A7、A9 通过；A6 五个取消阶段均保留已完成证据且本轮回归通过。A8 因缺少原生 GUI 验收阻塞，A10 因 macOS 改动缺少构建证据阻塞；没有发现本轮代码检查失败。 | 2026-09-23T10:42:47.880Z |
| 1 | 2 | 1 | recovery | — | 用户明确指定采用 ccrui（cr-zhichen）已提交且经过回测的 macOS 原生实现作为可信基准，在此之上集成本轮搜索配置改动，并按第一性原理继续核查及删除冗余。保留已核实基准的原生测试证据，本轮区分继承基准与集成增量；不因当前 Windows 主机无法重复 Mac 实机测试而推翻已有基准。当前未授权提交、推送或发布。 | 2026-09-23T12:27:28.488Z |
| 2 | 1 | 0 | recovery | — | Native Shape artifacts changed | 2026-09-23T12:41:02.684Z |
| 3 | 1 | 1 | fail | A9 | A1–A8、A10 通过；A9 因 Skill 仍保留旧 extra-sources 路由和旧预算描述而失败。 | 2026-09-23T12:57:37.439Z |
| 3 | 2 | 1 | fail | A9 | A1–A8、A10通过；A9仍有普通search synthesis与空extra_sources相关的残留引导，故候选未通过。 | 2026-09-23T13:13:51.478Z |
| 3 | 3 | 1 | fail | A9 | A1–A8、A10 通过；A9 因根 Skill 将 Jev 搜索描述成无条件行为，与文档和实现支持的 local 配置不一致而失败。 | 2026-09-23T13:25:36.839Z |
| 3 | 4 | 1 | pass | — | A1–A10 全部通过。当前唯一未决项 A9 的 Jev/local 文档边界已修正并同步；其余结论复用输入未变的前轮独立验收和有效检查回执。 | 2026-09-23T13:37:59.445Z |



## 结论

A1–A10 全部通过。当前唯一未决项 A9 的 Jev/local 文档边界已修正并同步；其余结论复用输入未变的前轮独立验收和有效检查回执。
