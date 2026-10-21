[手册目录](../README.md) · [English](../en/development.md)

# 开发与发布

## 开发验证

仓库用 `mise.toml` 声明开发工具链。安装 [mise](https://mise.jdx.dev) 后，`mise install` 会装好固定版本的 Python 和 Node，同一份文件也把常用命令暴露为 task：

```bash
mise run install      # 创建 .venv，以可编辑模式安装包和 dev 依赖
mise run test         # 安装 dev 依赖并运行 pytest
mise run cli -- --v   # 从当前检出运行 CLI
mise run regression
mise run smoke
mise run parity
mise run check
```

Python 任务共用当前检出的可编辑 `.venv`，包括 regression 和 smoke。额外开发脚本可通过 `mise run python path/to/script.py` 在同一环境执行。固定的 Python 3.13 满足项目版本约束；CI 独立覆盖 Python 3.10/3.12。mise 是可选的，下面的 `npm` 脚本仍受支持，CI 继续使用 `actions/setup-python` 与 `actions/setup-node`。

```powershell
.\.venv\Scripts\python.exe -m compileall -q src tests
.\.venv\Scripts\python.exe -m pytest tests -q
.\.venv\Scripts\python.exe -m smart_search.cli regression
.\.venv\Scripts\python.exe -m smart_search.cli smoke --mock --format json
npm test
npm pack --dry-run
```

## 发布通道

稳定版走 Git tag 和 npm `latest`：

```powershell
git tag vX.Y.Z
git push origin vX.Y.Z
```

测试版不移动 `latest`。推送到 `main` 会发布下一个 `<package.json version>-beta.N` 到 npm `next`，并且 `N` 按每个稳定版本重新从 1 开始。发布 beta 前，workflow 会比较当前稳定 `package.json` 版本和 first parent，因此 merge 或 squash 形式的稳定版升级都会跳过 beta，只由匹配的 `vX.Y.Z` tag 发布 npm `latest`；`chore(release): bump version to X.Y.Z` 标题保留为兼容兜底。例如 `0.1.10-beta.1`、`0.1.10-beta.2` 之后是 `0.1.10-beta.3`。

已发布 npm 版本不可变。旧的 `*-dev.*` 包不能原地改名，只能发布新的 `*-beta.N` 替代。

稳定版 GitHub Release 会读取 `.github/releases/vX.Y.Z.md` 作为正文，并自动追加 npm package、dist-tag、workflow run 等元数据。打稳定 tag 前先写这个文件，避免 Release 页面只显示包名和 workflow 链接。

只读 `CI` workflow 会在 pull request、推送到 `main` 和手动触发时运行，验证 Ubuntu Node 18/Python 3.10、Ubuntu Node 24/Python 3.12、Windows Node 22/Python 3.12，绝不发布。它会检查 public/package skill parity，打出真实 tarball，在新的临时 npm prefix 安装，并在那里运行版本、打包后的 regression 和 mock smoke。

发布收尾检查：

1. 先读 `npm view @konbakuyomu/smart-search versions --json`、`npm view @konbakuyomu/smart-search dist-tags --json`、`gh release list --repo konbakuyomu/smartsearch --limit 100`。
2. beta 发布必须保持 `latest` 不动，只移动 `next` 或指定的非 latest tag。
3. 遇到 npm `E409`，先查版本是否已经发布，再串行重跑对应版本。
4. 最后安装指定版本并运行 `smart-search --version`、`smart-search regression`、`smart-search smoke --mock --format json`。
5. Windows npm/mise 包装层额外跑中文 JSON 管道：`smart-search deep "深度搜索一下最近的比特币行情" --format json | ConvertFrom-Json`。

## 历史版本说明

### v0.1.14（历史版本）

这个稳定补丁版把已经验证过的 `0.1.13-beta.4` CLI 和内置 skill contract 推到 npm `latest`。

- 修复 GitHub issue #7：npm `latest` 现在包含新版 `smart-search-cli` skill 会调用的 `smart-search skills` 命令。
- `smart-search skills status` 可以只读检查用户级 skill 是缺失、过期、已最新，还是有额外文件。
- `smart-search skills update` 用于升级 CLI 后刷新指定 AI 工具里的托管 `smart-search-cli` 文件，不会改 provider key，也不会创建 Trellis/hooks/agents/commands。
- `smart-search diagnose openai-compatible --format markdown` 会生成适合复制给维护者的 OpenAI-compatible 卡住/超时诊断报告。
- 文档/API 路由现在优先用 Context7 处理库/框架文档，Exa 继续负责官方域名、论文、产品页和可信站点发现。
- README、打包 skill 资源、release notes 和测试已经同步说明并验证这次稳定包行为。

## 更新参考手册

修改命令、帮助或配置元数据后，在开发环境运行下面的命令，并检查两种语言的结果。

```sh
python scripts/generate_references.py
python -m pytest tests/test_guide.py
```
