# Brief：日常使用

一支 62 秒的教程：配好之后平时怎么用。和配置教程共用 App 组件、镜头、鼠标和字幕（`shared/app.js`、`shared/tutorial.js`）。

## 分镜

| 时间 | 场景 | 内容 | 依据 |
| --- | --- | --- | --- |
| 0–2.6 | 片头 | 「日常使用」和五项目录 | — |
| 2.6–16.2 | ① 在 AI 里直接问 | 终端里打出 README 的示例提问，「用 Smart Search」「读相关页面」「给出来源」依次画上荧光笔；AI 先 `smart-search search`，输出检索结果、`证据：not_evaluated`、`## 来源`，再 `smart-search fetch` 原网页，最后回答带 [1][2]；贴纸给出第二个示例「核对这篇文章里的说法」 | README 示例原句；`cli._format_markdown`；Skill 的「Prefer citing fetched pages」 |
| 16.2–27.4 | ② 搜索与研究 | 侧栏进「搜索与研究」，工具「搜索」，填问题，「开始 搜索」→ 运行中 → 结果：`[e1] useEffect – React / Source: …` 两段原文摘录、证据行、`## 来源`、「来源链接（2）」；「复制结果」→ 操作提示「已复制」 | `desktop_worker` 的 `display_text`；`jev_search._evidence_content` 的 `[e1]` 编号；摘录是 react.dev 原文 |
| 27.4–34.85 | ③ 在线研究 | 工具下拉滚到「在线研究」，出现研究深度（deep）和研究证据目录，填「React 状态管理方案对比」，开始 → 「查看活动」 | `desktop_catalog` 的标签和说明 |
| 34.85–41 | ④ 活动 | 列表里有运行中的在线研究、App 发起的搜索、AI 在终端发起的读取网页和搜索；点开研究看阶段事件，再点开 AI 的搜索（来源「终端 / AI」） | `MainWindow.Activity.cs` 的三行格式；`activity.py` 的事件（starting→命令→provider 进度→finished） |
| 41–50 | ⑤ 命令行 | 四条命令逐条打出，每条下面一句说明：search、fetch、research、route（加 `--remote` 才调用 Jev） | CLI 参数定义；`docs/jev-routing.md` |
| 50–58 | ⑥ 关掉 App | 点窗口关闭 → 「仍有 Smart Search 任务在运行」→ 「继续在后台」，窗口缩向托盘；终端里 AI 继续用 CLI 查新问题 | `MainWindow.xaml.cs` 关闭确认框原文；README「使用时可以关闭 Smart Search App」 |
| 58–62 | 片尾 | 「就这么用」、安装命令、手册链接 | — |

## 与真实 App 的出入

- 研究任务的阶段事件是按 `activity.py` 的写法排出的示例，真实任务的条数和时刻会不同；时间戳、耗时和路径都是示例。
- 片中 App 界面为 v0.1.30 的示意重绘。

## 构建

```sh
bash tools/build.sh usage smart-search-usage
node tools/render.mjs "usage/index.html?gif" out/gif/ask.mp4 --size 1280x720 --fps 15 --start 3.0 --duration 10.6 --crf 0
node tools/render.mjs "usage/index.html?gif" out/gif/usage.mp4 --size 1280x720 --fps 15 --start 17.3 --duration 9.1 --crf 0
```
