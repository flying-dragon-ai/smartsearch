# Brief：配置教程

一支 69 秒的实用教程：跟着 Smart Search 的 Windows App 逐页配置，从安装 CLI 一直到「基础配置已完成」。
界面是 `shared/app.js` 按 WinUI 3 重绘的 App，按 150% 缩放画进 1080p；页面结构和文字取自 `desktop/windows/*.cs`、
`src/smart_search/ui_metadata.py` 和 `src/smart_search/assets/i18n/messages.json`（v0.1.30）。

## 形式

- 鼠标真的去点按钮：每次点击的落点在渲染前从当时的界面量出来（`config.js` 的 `measure()`），按钮有悬停和按下状态，点击处有一圈波纹。
- 一台镜头跟着操作走：每一步的取景框按元素的位置算出，镜头在取景之间用闭式弹簧过渡；`?gif` 模式改成直接切镜，方便压成 GIF。
- 左上角是步骤贴纸，底部是字幕；每完成一步，Clawd 从右下角跳出来欢呼一下。
- 片头列出五页目录，片尾是「配好了！」、`smart-search setup` 和看板娘探头。

## 分镜

| 时间 | 页面 | 操作 | 界面原文 |
| --- | --- | --- | --- |
| 0–3.4 | 片头 | 标题和五页目录 | — |
| 3.4–13.2 | ① 概览 | 点「安装 CLI」→ 确认框「安装或更新独立 CLI？」点「继续」→ 卡片只剩进度 → 操作提示「独立 CLI」，重新连接时状态点变黄 → 「0.1.30 · 已就绪」，状态点变绿，提示自动清除 | 「Node.js/npm 已就绪，等待准备 Smart Search CLI」「Windows · C:\Users\me\AppData\Roaming\npm」「CLI 最新版本：0.1.30」「只处理所选 CLI；配置和 Skills 保留。App 自身不会更新。」「正在通过原管理器安装或更新 CLI…」「CLI 安装完成，正在重新连接。」「正在检测本地环境…」 |
| 13.2–28.6 | ② 服务商 | 「配置服务商」→ 选 Exa → 粘贴 Key → 「用未保存的修改测试」→ 「通过」→ 「保存更改」→ 「已保存」；快进：xAI、Jina 变成已配置 | 「查找网页并返回链接和相关摘录。」「示例：your-api-key」「有 1 项未保存修改 · 密钥留空会保留原值」「正在测试未保存的修改」「检查方式：真实请求」「新配置会用于下一次任务；已经开始的任务继续使用它自己的配置快照。」 |
| 28.6–41.4 | ③ 意图路由 | 选「意图路由」→ 圈出说明 → 填 JEV / TypeSafe API Key → 滚到「检索与判断」，圈出 0.5 和 0.75 → 保存 | 「JEV 语义路由」「普通搜索只选路一次；深入搜索按证据缺口继续。未配置 Jev 时使用本地路由。」「JEV 渠道适用概率阈值」「深入搜索证据充分阈值」 |
| 41.4–52 | ④ 更新 Skills | 打开 Gemini CLI 的开关（默认已选 Codex、Claude Code、Cursor）→ 「更新所选 Skills」→ 确认框「备份并更新」→ 「已同步 4 个，失败 0 个。」 | 「来源版本：0.1.30」+ 各目标的 `skills\smart-search` 路径 +「将同步所选目标的托管文件；不同内容先备份，额外文件保留。」 |
| 52–58 | ⑤ 设置与关于 | 依次圈出界面语言和外观、当前配置目录、App 更新 | 「App 与独立 CLI 分别保存语言选择。」「保存服务商配置和本地记录的文件夹；移动 App 不会改变此目录。」「每次打开 App 时检查，确认后才下载。」 |
| 58–64 | 回到概览 | 第 2 步显示三类已配置 | 「基础配置已完成，可以开始搜索。」 |
| 64–69 | 片尾 | 「配好了！」、`smart-search setup` | — |

## 与真实 App 的出入

- 新装环境里，概览第 2 步的副标题实际显示「待配置：retrieval」：`service._minimum_profile_result` 返回 `missing=["retrieval"]`，而 `MainWindow.xaml.cs` 的 `CapabilityLabel` 没有这一项的中文名。片中用的是同一卡片在未连接时的文字「选择搜索服务，填写 API Key。」。
- 片中的路径用 `C:\Users\me\…`，时间戳是示例。
- 片中是一台没有 WSL 的 Windows，只有一个安装目标，所以按钮是「安装 CLI」。有 WSL 发行版时按钮变为「安装到 Windows」「安装到 WSL <发行版>」，状态前面多一个「Windows · 」（`MainWindow.CLI.cs` 的 `InstallTargetTitle`、`CliStatus`）。

## 构建

```sh
bash tools/build.sh config smart-search-config          # out/config/smart-search-config.mp4
bash tools/build.sh config smart-search-config draft    # 960×540 小样
node tools/render.mjs "config/index.html?gif" out/gif/config.mp4 --size 1280x720 --fps 15 --start 14.4 --duration 11.2 --crf 0
```
