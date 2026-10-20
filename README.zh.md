<p align="center">
  <img src="icon.svg" alt="dsh-rea 图标" width="96" height="96">
</p>

<<<<<<< HEAD
=======
<p align="center">
  <video width="100%" max-width="720" controls preload="metadata" poster="promo-poster.png">
    <source src="promo.webm" type="video/webm">
    <source src="promo.mp4" type="video/mp4">
    您的浏览器不支持视频标签。
  </video>
  <br>
  <sub>🇨🇳 中文版 | 🇺🇸 <a href="README.md">English</a></sub>
</p>

>>>>>>> Initial: baseline + monitoring + video + compat table
# dsh-rea

[English](README.md) | 简体中文

> **非官方项目。** 本仓库是一个独立的 DeepSeek Harness 插件包，与 REA 项目没有隶属、
> 背书或发布关系。仓库不包含 REA 源码：运行时从 npm 安装官方
> [`rea-agents`](https://www.npmjs.com/package/rea-agents) 包，并把它提供的 MCP
> 服务器接入 Harness。详见 [NOTICE.md](NOTICE.md)。

一个“纯配置”的 [DeepSeek Harness](https://deepseek-harness.github.io/deepseek-harness/)
插件，用于连接 REA 逆向工程 MCP 服务器。安装后，智能体可以像调用原生工具一样调用
`mcp__rea__<tool>`：分析原生二进制、应用包、JavaScript/Electron 应用、托管程序集、
网站、流量抓包、固件镜像和运行时行为。

## 项目来源与归属

- **上游项目：** [REA — Reverse Engineer Anything](https://github.com/morluto/rea)，
  作者 **morluto**，MIT 许可。npm 包为
  [`rea-agents`](https://www.npmjs.com/package/rea-agents)，文档在
  [rea.tools](https://rea.tools/)。
- **本仓库：** <https://github.com/sqhc/dsh-rea>，由
  [sqhc](https://github.com/sqhc) 维护。这里只做打包与接入，不是 REA 的分叉。
- **关系：** 非官方集成。它把 REA 自带的 `rea setup --client dsh` 所写入的
  `rea-mcp` 注册，封装成一个带本地化元数据和图标的可安装 DSH bundle。仓库不复制
  REA 的源码、二进制或素材；运行时从 npm 获取官方包。
- **打包契约：** DeepSeek Harness 的 `dsh.bundle.patch` 格式，以及 Harness 自带的
  `@deepseek-ai/dsh-mcp-client`。

## 这个插件实际做了什么

插件只向 Harness 的组合配置插入一行：

```yaml
- insert:
    - id: rea-mcp
      name: '@deepseek-ai/dsh-mcp-client'
      config:
        serverName: rea
        transport: stdio
        command: npx
        args: ['-y', 'rea-agents@6.7.0', 'mcp']
```

`@deepseek-ai/dsh-mcp-client` 由 DSH 自带。本仓库不复制、不分叉、不重新构建 REA；
官方 npm 包以本地 stdio MCP 服务器的形式运行。

## 要求

- 已安装 DeepSeek Harness，并带有内置的 `@deepseek-ai/dsh-mcp-client`
  （已在 `0.2.1-rc.2` 上验证）。
- Harness 进程的 `PATH` 中有 Node.js 和 npm。REA 官方支持 Node.js 22.x（>=22.19）、
  24.x（>=24.11）或 26+。Node.js 20 可以启动服务器，但不在官方支持范围内。
- 首次启动需要网络，供 `npx` 拉取 `rea-agents@6.7.0`。
- 本次验证环境是 macOS。Linux 预期相同；Windows 未验证，且 REA 的原生 provider
  还有各自的前置条件。

<<<<<<< HEAD
=======
## 版本兼容性

| REA 版本 | Bundle 版本 | DSH 版本（已验证） | 备注 |
|---|---|---|---|
| `rea-agents@6.7.0` | `0.1.0` | `0.2.1-rc.2` | 基线版本；207 个工具，compact 输入 schema，output schema 关闭 |
| `rea-agents@6.x.x` | `0.1.x` | `0.2.x` | 仅补丁版本；在 `cordis.patch.yml` 中固定确切 REA 版本 |

*升级前务必阅读 REA 发布说明。工具名和 schema 属于模型可见契约。*

>>>>>>> Initial: baseline + monitoring + video + compat table
## 安装

先克隆本仓库，然后让 Harness 中的智能体用 `plugin_manager`
（`action: install_bundle`）安装这个目录，参数是仓库的绝对路径。安装会修改当前
DSH profile，并跨重启保留。

安装前可以先运行自检脚本：

```bash
node scripts/preflight.mjs
```

它会检查 Node 版本、npm 缓存可写性，对 `rea-agents@6.7.0` 执行一次 MCP initialize +
`tools/list` 握手，并输出工具数量和 catalog 大小；同时预热 npx 缓存，让 Harness
首次启动快很多。

## 首次启动

首次启动可能需要等待 `npx` 下载 REA。插件使用 `failOnStartupError: false` 并开启
自动重连，所以首次下载慢不会直接让插件行失效；在服务器就绪前，工具调用会失败。
如果几分钟后仍看不到 REA 工具，请检查 Harness 日志。

## 验证

让智能体无参数调用 `mcp__rea__binary_session`。它只报告当前目标、provider 和服务器
身份，不会启动分析。正常结果会显示 REA 服务器版本（`6.7.0`）。

## 工具目录与上下文成本

REA 会公布 207 个工具。完整 catalog 有好几 MB，因此本插件固定设置：

- `REA_MCP_INPUT_SCHEMA_PROFILE=compact`：输入 schema 有大小上限；REA 仍按完整的
  canonical 契约校验每次调用。
- `REA_MCP_OUTPUT_SCHEMA_PROFILE=off`：发现阶段不返回 output schema；REA 仍在服务端
  校验结构化结果。

在 REA 6.7.0 上实测约 **215–230 KiB 工具 JSON（约 55–57k tokens）**。对
deepseek-flash 的 1M 上下文来说可以接受，但这是插件启用期间每个请求的固定开销。
不做逆向任务时建议禁用插件。

如果确认模型路由能接受完整 schema，可以把 `REA_MCP_INPUT_SCHEMA_PROFILE` 改为
`full`。不要在未测量的情况下把 `full` 输入和 output schema 同时打开：完整 catalog
约 3.4 MB。

## 配置

修改仓库中的 `cordis.patch.yml`，然后重新安装/重载插件。

| 配置项 | 值 | 说明 |
|---|---|---|
| `serverName` | `rea` | 工具前缀为 `mcp__rea__` |
| `toolCallTimeoutMs` | `600000` | 原生分析和 provider 启动可能远超默认 60 秒 |
| `failOnStartupError` | `false` | 首次 npx 下载慢时应重连，而不是让插件行失败 |
| `NPM_CONFIG_CACHE` | `!!js` → `$DSH_HOME/cache/dsh-rea/npm` | 避开 root 属主 `~/.npm` 导致的 `EPERM`；可用 `DSH_REA_NPM_CACHE` 覆盖 |
| `REA_MCP_INPUT_SCHEMA_PROFILE` | `compact` | 控制公布 schema 的大小 |
| `REA_MCP_OUTPUT_SCHEMA_PROFILE` | `off` | 去掉数 MB 的 output schema |

## 排障

### `npm error code EPERM` / npm 缓存被 root 占用

patch 中的 `NPM_CONFIG_CACHE` 表达式会把 npx 缓存指到
`$DSH_HOME/cache/dsh-rea/npm`（如果取得到 profile 目录则优先
`<profile>/cache/dsh-rea/npm`），再回退到 `~/.dsh/cache/dsh-rea/npm`。在已验证的
Desktop profile 中实际解析为 `~/.dsh/cache/dsh-rea/npm`。如果要用别的目录，可以在
Harness 进程环境中设置 `DSH_REA_NPM_CACHE`（需要重启 Harness），或把 `!!js`
表达式换成字面量路径。不建议为了这个插件对整个 npm 缓存执行 `sudo chown -R`。

### 看不到 `mcp__rea__*` 工具

- 先运行 `node scripts/preflight.mjs`，把 Node/npm/REA 的问题与 DSH 问题分开。
- 确认 `npx` 解析到的 Node 版本在 REA 支持范围内。
- 确认 `rea-mcp` 行处于启用状态，且没有被标为 `disabled`。
- 如果该行加载失败，重载插件或重启 Harness。

### REA 重复注册

不要同时对同一个 profile 运行 `rea setup --client dsh`。两个注册都会使用
`serverName: rea`，MCP client 会拒绝重复项，其中一套工具会消失。选择一种集成方式，
删除另一种。

### 指定某个 Node 安装

patch 从 `PATH` 调用 `npx`。如果要固定到某个 Node 24，可把 command 改成该 Node
可执行文件，并把 args 指向已安装的 REA 启动器
（`<npm root -g>/rea-agents/scripts/rea.mjs`，再加 `mcp`）。改完重启 Harness。

### 可选：REA 工作流 skill

REA 还提供了智能体 skill。它自己的 setup 可以安装到 `~/.agents/skills`，DSH 会自动
发现：

```bash
npx -y rea-agents@6.7.0 setup --skill --dry-run
npx -y rea-agents@6.7.0 setup --skill --yes
```

这与本插件提供的 MCP 连接相互独立。

## 升级 REA

1. 阅读 REA 的 release notes，确认 MCP 工具是否有变化。
2. 修改 `cordis.patch.yml` 中固定的版本号（例如 `rea-agents@6.7.1`）。
3. 重新安装/重载插件，并重新运行 `node scripts/preflight.mjs`。

工具名和 schema 属于模型可见契约；修改它们会使提示词缓存失效，并可能破坏引用旧
工具名的历史会话。

## 卸载

让 Harness 智能体用 `plugin_manager`（`action: remove_bundle`）移除 `dsh-rea` 插件；
如果只是想暂停，可用 `set_bundle` 禁用。卸载插件不会删除 npm 的 npx 缓存，也不会
删除可选的 `~/.agents/skills` 副本；需要时请自行清理。

## 限制

- `dsh-mcp-client` 不支持 MCP prompt templates，因此 REA 的六个引导式 prompt 不会
  通过本插件暴露；工具调用不受影响。
- `dsh-mcp-client` 在发现工具后才暴露工具；npx 子进程崩溃后，旧工具列表会保留到
  重连预算耗尽。
- REA 的原生 provider（Hopper、Ghidra、IDA、JADX、Frida 等）需要各自安装；本插件
  不负责安装或许可。
- 本次没有验证 Windows。

## 安全与法律

REA 会分析本地文件，并可能启动外部辅助程序。请只检查你有权分析的软件，并阅读 REA
自己的 [DISCLAIMER](https://github.com/morluto/rea/blob/main/DISCLAIMER.md) 与
[SECURITY](https://github.com/morluto/rea/blob/main/SECURITY.md)。本插件不添加遥测，
也不保存凭据。

REA 由其作者以 MIT 许可发布。本仓库的配置、文档和图标同样以 MIT 许可发布；见
[LICENSE](LICENSE) 与 [NOTICE.md](NOTICE.md)。
