# Outcome

修复真实 mise/npm 环境发现与首次准备链路；保留现有六项导航、业务能力和卡片美学，简化更新与重复环境管理，补全字段帮助。用户能从未就绪状态走到配置服务商、测试和可选 Skills 接入。

# Scope

- Windows/ macOS 原生客户端同步；以 main 703b038 为基线，旧四页候选保持原样，不直接合并。
- 概览是完整“本地环境”准备/管理入口；设置和 Skills 不复制该面板，依赖环境的页面未就绪时提供原因和“准备环境”动作。
- 沿全局 PATH 与 mise shim/官方解析追踪实际 Smart Search 安装与所属管理器；普通 npm 和 mise 工具都识别，更新使用原管理器，不重复安装或更改无关全局工具。
- 首次流程：自动检测 → 按缺失步骤引导安装/更新或手动下载/选择现有安装 → 验证连接 → 配置服务商 → 测试 → Skills。旧版、不兼容、未发布兼容版本和网络失败分别解释。
- App 更新一个手动检查按钮，发现新版本变“下载更新”；自动检查每次新进程启动执行，取消常驻 24 小时轮询；复用安装框架和草稿保护，散包真实提示安装版要求。
- API、模型、路由和路径字段补全用途、条件、格式、默认行为与示例；问号悬浮/焦点帮助和可点击详情，空字段占位不写入配置。
- CLI 未连接统一用实际产品名和可执行步骤解释，不再只显示“本地引擎未连接”。

## Source coverage

| 来源 | 已确认要求 | Spec | 状态 |
| --- | --- | --- | --- |
| 用户纠正旧删项方案与结构化选择，complete | 六导航和功能保留；只精简页内操作 | 界面及入口 | covered |
| 两张用户截图 4592d007 / e56aafec，complete | App 更新、CLI、Skills 的分组卡片不能删，保持主次和跨页一致 | 界面及入口 | covered |
| 用户更新反馈，complete | 检查→下载按钮；每次打开自动检查；删除冗余操作 | App 更新 | covered |
| 用户环境反馈及“mise有全局shim，所以开始吧”，complete | 追查实际安装，兼容mise/npm，明确引导到配置/测试，授权开始实施 | 环境发现及引导 | covered |
| 用户重复入口反馈，complete | Skills与设置不重复完整CLI管理 | 界面及入口 | covered |
| 用户字段/API/路径反馈，complete | 问号悬浮及占位说明，讲清路由API | 字段帮助 | covered |
| 当前实现和隔离发现探针，complete | npm可找到但遗漏mise独立工具；现有旧0.1.24缺binary标志；新包尚未发布 | 环境发现及引导 | background：不得冒充已修复或真实发布 |

# Non-goals

不删除导航、业务功能、卡片、用户数据或现有安装；不恢复内置CLI；不自动更新全局Node/mise、不引入新的包管理器、不绕过发行/签名限制。不自动发布、提交、推送或覆盖正式App/CLI/Skills；候选和测试使用独立目录。GUI由用户验收。

# Acceptance examples

详见 specs/desktop-guided-setup/spec.md 的完整 Scenario；覆盖真实mise路径、全新机器、旧安装、错误恢复、更新按钮与字段帮助。

# Constraints and invariants

旧配置位置不依赖App目录；App与CLI独立安装更新。保持来源所有权、Key脱敏、备份、草稿、写入互斥及取消保护。兼容安装只做无安装副作用的探针；旧wrapper不得因发现过程自动下载Python。

# Decisions

- 用户明确要求保留现有导航/功能和统一卡片，并在看过修订方案后说“mise我记得有全局的shim可以追查到的，所以开始吧”，授权实施上述范围。
- 采用概览统一环境入口，保留原生风格；缺少环境时从任意业务页回到同一引导流程。
- 优先复用本机已有安装及管理器；旧格式若能安全确认已准备的运行环境和协议则可连接，否则明确升级/手动路径，不执行旧wrapper的自动bootstrap。
- 原 desktop-configurator-simplification 仅作被替代的历史方案，保留目录和证据；本修订从当前main隔离实现。
- 同一主窗口和安装状态链紧密耦合，不拆Supervisor。主代理实施，只读agent做独立事实检索和最终验收。

- 实现沿 `mise ls --global` / `which` 核对工具，再读取单个全局工具条目。稳定 pin/latest 及 allow_low_downloads 选项可由原管理器更新；复杂条目保持只读并给出原终端提示。
- 手动路径仅接受完整独立 CLI 包，核对同目录包信息和运行文件后才做协议探针；全局 shim/旧 bootstrap 不作为手动独立包执行。

# Open questions

无需求阻塞；使用当前框架处理下载、安装与安全重启。实际Mac构建与GUI验证按可获得的环境分别标明，不冒充通过。

# Verification expectations

新增安装发现/管理器所有权与状态回归、字段metadata回归、UI结构和资源一致性检查；运行相关Python/Node/C#检查与Windows完整构建；安全的真实mise只读探针。新只读Verifier逐项验收；不把本机Windows证据当作Mac或GUI验收。
