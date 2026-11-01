<div align="center">

<img src="docs/assets/logo.png" width="112" alt="boss-agent-cli logo">

# boss-agent-cli

*🤖 面向真人与 AI Agent 的招聘平台 CLI —— 纯终端向导 · 福利筛选 · 双角色工作流 · JSON 信封。*

[![Python](https://img.shields.io/badge/Python-≥3.10-3776AB?logo=python&logoColor=white&style=flat-square)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg?style=flat-square)](LICENSE)
[![GitHub Release](https://img.shields.io/github/v/release/can4hou6joeng4/boss-agent-cli?style=flat-square)](https://github.com/can4hou6joeng4/boss-agent-cli/releases)
[![PyPI Downloads](https://img.shields.io/pypi/dm/boss-agent-cli?style=flat-square)](https://pypi.org/project/boss-agent-cli/)
[![PRs Welcome](https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square)](https://github.com/can4hou6joeng4/boss-agent-cli/pulls)
[![MCP Toplist](https://mcptoplist.com/badge/glama%2Fcan4hou6joeng4%2Fboss-agent-cli.svg)](https://mcptoplist.com/server/glama%2Fcan4hou6joeng4%2Fboss-agent-cli)

[快速上手](docs/getting-started.md) · [Windows 便携包](#windows-portable-skill) · [Agent 集成](#-agent-集成) · [命令](#-命令) · [排障](docs/troubleshooting.md) · [路线图](ROADMAP.md) · **中文** | [English](README.en.md)

<a href="demo/showcase/boss-agent-cli-showcase.mp4" title="观看 48 秒产品发布会动画">
  <img src="demo/showcase/boss-agent-cli-showcase.gif?v=keynote-20261008" alt="boss-agent-cli 极光发布会动画：福利筛选、双角色工作流与 Agent 接入" width="100%">
</a>

**[观看 48 秒发布会动画](demo/showcase/boss-agent-cli-showcase.mp4)** · [交互版](https://can4hou6joeng4.github.io/boss-agent-cli/keynote-animation/) · [终端交互演示](demo/demo-zh.gif) · 福利筛选 · 双角色工作流 · Agent 接入

</div>

## 🧭 为什么

boss-agent-cli 把职位发现、福利筛选、本地简历与 AI、投递沟通、招聘者候选人处理和可恢复采集统一到一个 CLI。真人直接运行 `boss` 进入纯终端向导；Agent 使用 JSON、schema、MCP 或 Python API 调用同一套 workflow 与状态。`boss schema` 始终是能力真源。

## ⚠️ 运行边界

历史配置 `operating_mode=assisted|research` 继续兼容，但两种模式都可调用全部已实现能力，不再产生模式级 `COMPLIANCE_BLOCKED`。平台尚未实现的能力仍准确返回 `NOT_SUPPORTED`；认证失效、账号风险和网络错误保留结构化错误与恢复动作。长流程仍受 timeout、retry、预算、checkpoint 和 stop 控制。

## ✨ 核心能力

- **职位发现**：关键词搜索 + 8 维筛选，按编号回看缓存结果 —— `search` `show` `detail`
- **福利筛选（核心差异化）**：`--welfare "双休,五险一金"` 自动翻页补抓、按 AND 逻辑做**真实匹配**，并可 `--sort score` 按本地匹配分排序 —— `search --welfare`
- **HR 活跃度筛选**：`--active 3d` 只留最近活跃的 HR，避免把投递次数浪费在长期不上线的岗位上；`online` 只看列表、请求量与普通搜索相同，其余档位可能要逐个查职位详情，更慢、风控风险更高，低风险场景建议用 `--active online` —— `search --active`
- **纯终端向导**：直接运行 `boss` 或 `boss wizard`，选择角色、平台和目标；同一 workflow 也可用 `--input-json`、run ID 或 MCP 推进和恢复
- **本地候选池与统计**：查看详情后本地保存、读取带有效状态的网页职位收藏并仅同步有效项 / 用标签和备注复盘候选岗位、离线对比、查看漏斗统计 —— `shortlist` `stats` `watch` `preset` `favorites`
- **AI 求职增强 + 本地模型**：JD 分析、简历润色、定向优化、候选池匹配、模拟面试、沟通指导；本地模型权重外置，支持 Ollama/vLLM OpenAI 兼容接口 —— `ai analyze-jd` `ai local configure` `ai local smoke`
- **Schema 驱动 + JSON 信封**：stdout 只输出 `{ok, data, pagination, error, hints}` 信封，`boss schema` 是能力真源，适合 CLI 编排 / Shell Agent / MCP / Python SDK
- **招聘者完整链路**：先确认招聘者身份，再进入候选人搜索、推荐牛人、首次招呼、附件简历接收与下载、简历、聊天/最近消息、回复和职位管理 —— `hr whoami/candidates/recommendations/greet/applications/resume/chat/last-messages/reply/request-resume/accept-resume/download-resume/jobs`
- **平台抽象**：`Platform` / `RecruiterPlatform` 双注册表 + `--platform` 全局选项；当前注册平台为 `zhipin`（BOSS 直聘）

## 🚀 快速开始

```bash
# 安装（uv 推荐；浏览器内核仅用于用户主动登录 / 本地导出）
uv tool install boss-agent-cli
patchright install chromium

# 真人入口：直接进入角色、平台和目标向导
boss

# Agent / 高级用户仍可直接调用命令
boss doctor                                                   # 环境自检
boss login                                                    # 登录（按平台选择链路）
boss status                                                   # 验证登录态
boss search "Golang" --city 广州 --welfare "双休,五险一金"     # 搜索 + 福利筛选
boss search "Golang" --city 广州 --active 3d                  # 只看 3 日内活跃的 HR
boss detail <security_id>                                     # 查看详情
boss shortlist add <security_id> <job_id> --tags 后端,远程    # 加入本地候选池并打本地标签
boss shortlist compare --tag 远程                             # 离线对比候选岗位
boss stats                                                    # 本地统计

# 招聘者模式
boss hr candidates "Python" --city 101010100
boss hr recommendations --job-id <encJobId>
boss hr jobs list
```

所有命令输出结构化 JSON（`ok` 判断成败，默认 `exit 0/1`；可选 `--exit-codes sysexits` 返回按错误类别区分的语义化退出码）。完整上手见 [快速上手](docs/getting-started.md)。

## 🎭 角色与平台

| 平台 | 求职者 | 招聘者 | 状态 |
|------|:--:|:--:|------|
| BOSS 直聘 (`zhipin`) | ✅ | ✅ | 默认 |

```bash
boss platforms                             # 查看已注册平台与能力状态（当前仅 zhipin）
boss --platform zhipin search "Python"     # --platform 默认即 zhipin，可省略
```

`boss hr ...` 与招聘者侧 `agent` 自动化当前均只支持 `zhipin-recruiter`。设计细节见 [docs/platform-abstraction.md](docs/platform-abstraction.md)。

## 🤖 Agent 集成

推荐先读：[Agent Quickstart](docs/agent-quickstart.md) · [Capability Matrix](docs/capability-matrix.md) · [Host Examples](docs/agent-hosts.md)

项目内置[招聘 Skill](.agents/skills/boss-recruiter/SKILL.md)，使用本仓库 CLI 编排候选人搜索、简历分析及招聘沟通。Windows 用户从 [Release](https://github.com/yinchangbo/boss-agent-cli/releases) 下载便携包，解压后将整个 `boss-recruiter` 文件夹放入 Agent 的技能目录。包内已包含 Python、依赖和浏览器，无需安装；Codex 的个人技能目录为 `%USERPROFILE%\.agents\skills\`。

```powershell
& "$env:USERPROFILE\.agents\skills\boss-recruiter\boss.cmd" --json --role recruiter schema
```

支持该 Skill 目录的 Agent 宿主可通过 `$boss-recruiter` 调用；其他宿主也可直接加载 `SKILL.md` 并调用 `boss.cmd`。需要登录时按 Skill 指引扫码。仓库内的 Skill 是构建源码，不含便携运行环境；修改代码后的重新打包方法见下文。

```json
// 方式一：MCP（推荐）—— Claude Desktop / Cursor 等 MCP 宿主，暴露 78 个已实现工具
{ "mcpServers": { "boss-agent": { "command": "uvx", "args": ["--from", "boss-agent-cli[mcp]", "boss-mcp"] } } }
```

不想在本机配 Python 工具链，可用仓库自带的容器：`BOSS_UID=$(id -u) BOSS_GID=$(id -g) docker compose run --rm boss-mcp`。镜像刻意不含浏览器内核 —— 先在宿主机 `boss login`，再把 `~/.boss-agent` 挂进去，详见 [Docker 接入](docs/integrations/docker.md)。

OpenCode 源码项目可直接使用仓库示例：

```bash
cp examples/opencode/opencode.json ./opencode.json
uv sync --all-extras
uv run boss-mcp --data-dir ./.boss-agent --help
```

portable / 全局安装后，在任意 OpenCode 项目里使用 `examples/opencode.json`，它会启动 `boss-mcp --data-dir ./.boss-agent`，让 review、pending、日志按项目隔离。

```bash
# 方式二：subprocess —— 先让 Agent 读能力自描述，再解析 stdout JSON
boss schema
```

```python
# 方式三：Python 直接嵌入（随 py.typed 发布，可作类型化库）
from boss_agent_cli import AuthManager, BossClient, AuthRequired
with BossClient(AuthManager(...)) as client:
    result = client.search_jobs("Golang", city="广州")
```

<a id="windows-portable-skill"></a>

## Windows 便携版招聘 Skill：打包与更新

**打包命令只有一条，在仓库根目录执行：**

```powershell
python scripts/package_recruiter_skill.py
```

打包电脑需要 Windows x64、Python 3.10+、支持 `--python` 选项的 pip、7-Zip 和网络。接收者电脑无需安装 Python。脚本从当前工作区重新构建 CLI，内置 Python 3.14.10、Patchright 1.64.3、Chromium 修订版 1248、匹配的 Headless Shell 及全部运行依赖。

下次修改代码时：

1. 修改 `src/boss_agent_cli/` 中的 CLI 代码，或 `.agents/skills/boss-recruiter/` 中的 Skill 说明、启动器等文件。
2. 再运行同一条打包命令。不需要手动构建 wheel、复制 `.venv` 或删除下载缓存；普通代码改动不需要调整运行时版本锁。
3. 等待命令退出码为 `0`，并显示“已生成并通过迁移验收”。脚本会在仓库外的中文/空格路径中验证 CLI 和两种 Chromium 的实际启动，再生成 7z 并检查完整性。两种格式全部验证通过后才更新成品和报告。失败时可能仍保留上一次成功的产物，不要把它误当作本次新包。
4. 分发新包；接收者将其解压到空目录，整体替换旧 Skill，不混入旧 `.venv` 或旧运行环境。需要发布时，将新压缩包、对应校验文件及验收报告上传到新的 GitHub Release；打包命令不会自动提交、推送或发布。

| 自动生成的文件 | 用途 |
| --- | --- |
| `dist/boss-recruiter.zip` | 完整 Windows x64 便携包 |
| `dist/boss-recruiter.7z` | 同一便携版的高压缩格式 |
| `dist/boss-recruiter.zip.sha256` | ZIP 的 SHA-256 校验值 |
| `dist/boss-recruiter.7z.sha256` | 7z 的 SHA-256 校验值 |
| `dist/boss-recruiter.validation.json` | ZIP 运行验收、7z 完整性结果及两份压缩包摘要 |

下载缓存位于 `dist/windows-build/`。如需升级 Python、Patchright 或 Chromium，应一起更新 [runtime-lock.json](.agents/skills/boss-recruiter/assets/runtime-lock.json) 和 [requirements-windows.lock.txt](.agents/skills/boss-recruiter/assets/requirements-windows.lock.txt)，同步 Skill 中的版本说明，再重新打包验收。不要在接收者电脑上单独升级 Patchright。

### 7-Zip 工具定位

脚本自动从 PATH 和 Windows 常见安装目录查找 `7z.exe` / `7zz`。如果安装在自定义位置，可显式指定：

```powershell
python scripts/package_recruiter_skill.py --seven-zip "E:\Tools\7-Zip\7z.exe"
```

找不到 7-Zip 时，脚本会在开始下载和构建之前报错，不会静默只生成 ZIP。无需再手动解压 ZIP、执行压缩命令或生成校验文件。ZIP 和 7z 使用同一份本次构建目录，7z 采用 LZMA2、128 MiB 字典和固实压缩，并执行 `7z t` 完整性检查；高压缩可能耗时数分钟。

两种格式包含相同的完整便携版，任选其一分发即可。2026-11-01 版本实测 ZIP 为 383.1 MiB，7z 为 227.3 MiB；后续大小随代码和依赖变化。

更多构建及单独验收说明见 [scripts/README.md](scripts/README.md#package_recruiter_skillpy)。

## 📚 命令

`boss schema` 暴露 39 个顶层命令 + 14 个一级招聘者子命令，按工作流分组：

- **认证**：`login` · `logout` · `status` · `doctor`
- **职位发现**：`search` · `detail` · `show` · `cities` · `history`
- **本地整理**：`watch` · `preset` · `shortlist` · `stats` · `favorites`
- **可恢复采集**：`crawl configure/run/start/status/results/resume/stop/shortlist`
- **简历 / AI**：`resume` · `me` · `ai analyze-jd` · `ai polish` · `ai optimize` · `ai fit` · `ai suggest-keywords` · `ai resume-optimize` · `ai cover-letter` · `ai interview-prep` · `ai chat-coach` · `ai local`
- **系统 / workflow**：`wizard` · `schema` · `platforms` · `export` · `config` · `clean`
- **候选者动作**：`greet` · `batch-greet` · `apply` · `exchange` · `chat*` · `pipeline` · `digest`
- **招聘者**：`hr whoami/applications/candidates/recommendations/greet/resume/chat/chatmsg/last-messages/reply/request-resume/accept-resume/download-resume/jobs`

完整命令表、参数与福利筛选原理见 **[命令参考](docs/commands.md)**；能力真源是 `boss schema`（支持 `--format openai-tools` / `anthropic-tools` 导出工具定义）。

批量采集需要额外安装 `uv sync --extra crawl`。它使用独立的 `<data-dir>/crawl/chrome-profile`，不会接管日常 Chrome profile。默认不注入 Hook；如需使用本地脚本，必须同时显式提供 Hook 档位和包含 `SHA256SUMS` 的目录：

```powershell
boss crawl configure --max-requests 20 --max-details 50 --max-seconds 600 --max-retries 1
boss crawl run "AI" --city 杭州 --pages 3 --with-detail `
  --hook-profile screenshot-full --hook-dir E:\boss-agent-cli-local-hooks\AntiDebug_Breaker
boss crawl resume <run_id>
boss crawl stop <run_id>
boss agent crawl --run-id <run_id> --resume <简历名>
```

`crawl run` 顺序执行并保存 SQLite 断点和 JSON / CSV / XLSX 增量产物；请求数、详情数、墙钟时间和重试均受固定预算约束，`boss crawl stop` 可在下一个安全点停止。导出和 `crawl results` 默认不会暴露 `security_id`、职位 ID 或招聘者字段；执行 `boss clean --privacy` 会删除 crawl 状态、预算和导出。细粒度 MCP crawl tools 读取或导入已有 `run_id`；`boss_wizard` 可通过共享 workflow 启动、恢复和停止任务。出现平台风险码或安全页时停止并返回恢复命令。

## 🩺 诊断与排障

```bash
boss doctor             # 环境自检
boss status --live      # 可选：一次低频只读探测
boss doctor --live-probe
```

错误信封统一携带 `code` + `recoverable` + `recovery_action`，可程序化恢复。`boss doctor` 检查 CDP 可达性并汇总 `browser_channel` 状态。`chat` / `chatmsg` 在默认 `auto` 来源下使用本地凭据的 httpx；显式选择 `--browser-source existing-browser` 才会通过 CDP 复用已有目标页，且不读取 CLI 保存的 Cookie。现有浏览器候选耗尽返回 `BROWSER_SESSION_NOT_FOUND` + `boss doctor`，普通未登录路径仍返回 `AUTH_REQUIRED` + `boss login`。所有来源命中平台风控时都停止当前 workflow 并保存 checkpoint；适配器必须有限运行、脱敏、可停止，并只在风险状态解除后显式恢复。

**v3.0.0 迁移：Browser Bridge daemon、Chrome 扩展和 `[bridge]` 安装 extra 已移除。升级 CLI 不会停止旧 daemon，也不会卸载浏览器扩展。** 请手动停止旧 daemon，禁用或移除旧扩展，并从安装命令中去掉 `[bridge]`。浏览器默认降级链为 CDP → headless；若要只复用已有会话，先在本机 CDP 浏览器的官方页面手动登录，再运行：

```bash
boss --browser-source existing-browser --cdp-url http://localhost:9222 chat
```

该来源不新建页面、不导航、不注入 Cookie，也不启动浏览器。CDP 调试端口仅用于本机可信环境，不要暴露到公网或用来绕过平台风控。

完整检查项、CDP 启动示例与错误码见 **[诊断与排障](docs/troubleshooting.md)**；涉及 Cookie / CDP / patchright / 请求频率 / 接口漂移的问题先读 [平台风险边界](docs/platform-risk.md)。

## ⚙️ 配置

```bash
boss config list                    # 查看所有配置
boss config set log_level debug     # 设置日志级别
boss config reset                   # 恢复默认
```

配置位于 `~/.boss-agent/config.json`：运行模式（`operating_mode=assisted|research`）、请求间隔、批量打招呼间隔、日志级别、CDP 地址、导出目录、平台 / 角色。

## 🏗️ 技术架构

```
CLI (Click)
  └─ 兼容运行元数据（assisted / research 均开放已实现能力）
       └─ AuthManager ── 用户主动登录态（Fernet + PBKDF2 机器绑定加密）
       └─ Platform 双注册表 ── BossPlatform / BossRecruiterPlatform
       └─ BossClient ── httpx + 节流（高斯延迟）；兼容 CDP / patchright 登录与导出
       └─ CacheStore（SQLite WAL） · AIService（OpenAI-compatible / Ollama / vLLM）
            └─ output.py → JSON 信封 → stdout
```

**不变量**：stdout 仅 JSON 信封 · stderr 仅日志 · `exit 0/1`（可选 `--exit-codes sysexits` 语义化退出码） · 错误含 `code/recoverable/recovery_action` · `boss schema` 为能力真源。
**双受众提示**：`hints.next_actions` 是给 Agent 执行的后继命令，`hints.operator_actions` 是给真人操作者的自然语言指引（扫码、在浏览器里调整条件等需要离开终端完成的动作）；TTY 下只渲染后者到 stderr，Agent 应把它转述给操作者。
**命令还是 wizard**：单次、无状态的能力调用走顶层命令；需要跨步骤状态、可恢复、或中途要把指引递给真人的走 `boss wizard`（goal 取值见 `boss schema` 的 `wizard_catalog`）。
**选型**：Python ≥ 3.10 · Click · httpx · patchright / CDP（登录、导出与声明的浏览器 adapter）· cryptography（Fernet）· sqlite3（WAL）· pytest（2900+ 项）。

## 🔌 本地存储

所有状态在 `~/.boss-agent/`：加密登录态、搜索缓存、候选池、本地简历、AI 配置与外置模型登记。模型权重不进入 Python 包；除显式发起的 API 调用或本地模型下载外，数据不离开本机。

## 🤝 贡献者

欢迎 Issue / PR：`git clone` → `feat/xxx` 分支 → 写测试 → `python scripts/quality_baseline.py`（Windows 中文系统可先 `$env:PYTHONUTF8='1'`）→ PR。详见 [CONTRIBUTING.md](CONTRIBUTING.md)，上手路径见 [快速上手](docs/getting-started.md)。

感谢每一位让 boss-agent-cli 变得更好的贡献者，去关注他们！❤️

<a href="https://github.com/can4hou6joeng4/boss-agent-cli/graphs/contributors">
  <img src="./CONTRIBUTORS.svg" alt="贡献者" width="1000" />
</a>

## ❤️ 支持

- 如果它帮到了你，最直接的支持是点一个 [Star ⭐](https://github.com/can4hou6joeng4/boss-agent-cli)，或分享给正在找工作的人。
- 用出问题、有新想法，欢迎提 [Issue](https://github.com/can4hou6joeng4/boss-agent-cli/issues)；想动手就直接上 PR。
- 想看看船队的其他船，欢迎靠泊母港 [bobochang.cn](https://bobochang.cn) 🧭，航海记录在[掘金专栏](https://juejin.cn/user/1187904004821262)。

本项目受益于 [geekgeekrun](https://github.com/geekgeekrun/geekgeekrun) · [boss-cli](https://github.com/jackwener/boss-cli) · [opencli](https://github.com/jackwener/opencli)，一并致谢。

## ⭐ Star History

<picture>
  <source media="(prefers-color-scheme: dark)" srcset="docs/assets/star-history-dark.svg">
  <img alt="Star History" src="docs/assets/star-history.svg" width="100%">
</picture>

由 [mystarhistory](https://github.com/carsteneu/mystarhistory) 本地生成的静态 SVG，与仓库同源、不依赖第三方服务。

## ⚠️ 免责声明

使用时请遵守适用法律、平台协议和隐私要求。对批量触达、候选人个人数据和浏览器适配设置明确的输入、数量、超时和停止条件，并妥善保护本地凭据与导出产物。因不当使用产生的后果由使用者自行承担，与项目作者无关。

## 📑 许可证 & 友情链接

[MIT](LICENSE) © [can4hou6joeng4](https://github.com/can4hou6joeng4) · 友链 [LINUX DO](https://linux.do/)
