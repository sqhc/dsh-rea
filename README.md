<p align="center">
  <img src="icon.svg" alt="dsh-rea icon" width="96" height="96">
</p>

<p align="center">
  <a href="promo.mp4">
    <img src="promo.gif" alt="dsh-rea promo video" width="720">
  </a>
  <br>
  <sub><a href="promo.mp4">MP4</a> · <a href="promo.webm">WebM</a> · <a href="promo-poster.png">Poster</a></sub>
  <br>
  <sub>🇨🇳 <a href="README.zh.md">中文版</a> | 🇺🇸 English</sub>
</p>

# dsh-rea

English | [简体中文](README.zh.md) · [Releases](https://github.com/sqhc/dsh-rea/releases) · [Changelog](CHANGELOG.md)

> **Unofficial.** This repository is an independent DeepSeek Harness bundle. It is
> not affiliated with, endorsed by, or published by the REA project. It contains
> no REA source code: at runtime it installs the official
> [`rea-agents`](https://www.npmjs.com/package/rea-agents) package from npm and
> connects its MCP server to the Harness. See [NOTICE.md](NOTICE.md).

A configuration-only [DeepSeek Harness](https://deepseek-harness.github.io/deepseek-harness/)
bundle that connects the REA reverse-engineering MCP server. Once installed, the
agent can call REA tools as `mcp__rea__<tool>` — inspect native binaries, app
bundles, JavaScript/Electron applications, managed assemblies, websites, packet
captures, firmware images, and runtime behavior.

## Origin and provenance

- **Upstream project:** [REA — Reverse Engineer Anything](https://github.com/morluto/rea)
  by **morluto**, MIT-licensed. The npm package is
  [`rea-agents`](https://www.npmjs.com/package/rea-agents); documentation lives at
  [rea.tools](https://rea.tools/).
- **This repository:** <https://github.com/sqhc/dsh-rea>, maintained by
  [sqhc](https://github.com/sqhc). It is a packaging layer, not a fork.
- **Relationship:** unofficial integration. It turns the `rea-mcp` registration
  that REA's own `rea setup --client dsh` writes into an installable DSH bundle
  with locale metadata and an icon. No REA source code, binaries, or artwork are
  copied; the official package is fetched from npm at runtime.
- **Packaging contract:** DeepSeek Harness's `dsh.bundle.patch` format and the
  harness-shipped `@deepseek-ai/dsh-mcp-client`.

## What this bundle actually does

The bundle inserts one row into the Harness plugin composition:

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

`@deepseek-ai/dsh-mcp-client` is shipped with DSH. REA is not vendored, forked, or
rebuilt here — the official npm package runs as a local stdio MCP server.

## Requirements

- DeepSeek Harness with the shipped `@deepseek-ai/dsh-mcp-client` (verified with
  `0.2.1-rc.2`).
- Node.js and npm on the Harness process `PATH`. REA officially supports
  Node.js 22.x (>=22.19), 24.x (>=24.11), or 26+. Node.js 20 can start the server
  but is outside REA's supported range.
- Network access on the first launch so `npx` can fetch `rea-agents@6.7.0`.
- macOS is what this bundle was verified on. Linux should work the same way.
  Windows is untested; native REA providers also have their own prerequisites.

## Version compatibility

| REA version | Bundle version | DSH version (verified) | Notes |
|---|---|---|---|
| `rea-agents@6.7.0` | `0.1.0` | `0.2.1-rc.2` | Baseline; 207 tools, compact input schema, output schema off |
| `rea-agents@6.x.x` | `0.1.x` | `0.2.x` | Patch versions only; pin exact REA version in `cordis.patch.yml` |

*Always read REA release notes before upgrading. Tool names and schemas are part of the model-facing contract.*

## Install

Clone this repository, then ask the Harness agent to install the bundle
directory with `plugin_manager` (`action: install_bundle`). The agent needs the
absolute path to the checkout. Installing changes the current DSH profile and
survives restarts.

Before installing, you can run the preflight script:

```bash
node scripts/preflight.mjs
```

It checks the Node version and npm cache, performs an MCP initialize +
`tools/list` handshake against `rea-agents@6.7.0`, and reports the tool count and
catalog size. It also warms the npx cache, which makes the first Harness launch
much faster.

## First launch

The first launch may take a while because `npx` downloads REA. The bundle starts
with `failOnStartupError: false` and automatic reconnect, so a slow first
download does not disable the row; calls fail until the server is ready. Check
the Harness log if no REA tools appear after a few minutes.

## Verify

Ask the agent to call `mcp__rea__binary_session` with no arguments. It reports
the current target/provider/server identity without starting analysis. A healthy
result identifies the REA server version (`6.7.0`).

## Tool catalog and context cost

REA advertises 207 tools. Rendering the complete catalog would cost several
megabytes, so this bundle always sets:

- `REA_MCP_INPUT_SCHEMA_PROFILE=compact` — bounded input schemas; REA still
  validates calls against the full canonical contract.
- `REA_MCP_OUTPUT_SCHEMA_PROFILE=off` — output schemas are omitted from
  discovery; REA still validates structured results server-side.

Measured at REA 6.7.0: about **215–230 KiB of tool JSON (~55–57k tokens)**. With
deepseek-flash's 1M-token context this is acceptable, but it is a real fixed
cost on every request while the plugin is enabled. Disable the bundle when you
are not doing reverse engineering.

If you prefer the full advertisement and your model route accepts it, change
`REA_MCP_INPUT_SCHEMA_PROFILE` to `full`. Do not combine `full` input with output
schemas unless you have measured the cost: the complete catalog is ~3.4 MB.

## Configuration

Edit `cordis.patch.yml` in the checkout and reinstall/reload the bundle.

| Key | Value | Why |
|---|---|---|
| `serverName` | `rea` | Tool prefix `mcp__rea__` |
| `toolCallTimeoutMs` | `600000` | Native analysis and provider startup can exceed the 60 s default |
| `failOnStartupError` | `false` | A slow first npx download should reconnect, not fail the row |
| `NPM_CONFIG_CACHE` | `!!js` → `$DSH_HOME/cache/dsh-rea/npm` | Avoid `EPERM` from a root-owned `~/.npm`; override with `DSH_REA_NPM_CACHE` |
| `REA_MCP_INPUT_SCHEMA_PROFILE` | `compact` | Keep the advertised catalog bounded |
| `REA_MCP_OUTPUT_SCHEMA_PROFILE` | `off` | Remove multi-megabyte output schemas |

## Troubleshooting

### `npm error code EPERM` / root-owned npm cache

The `NPM_CONFIG_CACHE` expression in the patch points npx at
`$DSH_HOME/cache/dsh-rea/npm` (or `<profile>/cache/dsh-rea/npm` when the profile
directory is available), falling back to `~/.dsh/cache/dsh-rea/npm`. In the
verified Desktop profile it resolved to `~/.dsh/cache/dsh-rea/npm`. If you need a
different directory, set `DSH_REA_NPM_CACHE` in the environment of the Harness
process (requires a Harness restart), or replace the `!!js` expression with a
literal path. We do not recommend `sudo chown -R` on your whole npm cache just
for this plugin.

### No `mcp__rea__*` tools

- Run `node scripts/preflight.mjs`; it isolates Node/npm/REA problems from DSH.
- Check that `npx` resolves to a Node version REA supports.
- Check that the `rea-mcp` row is active and not `disabled`.
- If the row failed to load, reload the bundle or restart the Harness.

### Duplicate REA registration

Do **not** also run `rea setup --client dsh` for this profile. Both registrations
would use `serverName: rea`; the MCP client rejects the duplicate and one tool set
disappears. Pick one integration and remove the other.

### Use a specific Node installation

The patch runs `npx` from `PATH`. To pin a Node 24 installation instead, replace
the command with that Node binary and point `args` at the installed REA launcher
(`<npm root -g>/rea-agents/scripts/rea.mjs`, then `mcp`). Restart the Harness
after editing.

### Optional: REA workflow skill

REA also publishes an agent skill. Its own setup can install it into
`~/.agents/skills`, which DSH discovers:

```bash
npx -y rea-agents@6.7.0 setup --skill --dry-run
npx -y rea-agents@6.7.0 setup --skill --yes
```

This is independent of the MCP connection provided by this bundle.

## Upgrade REA

1. Read the REA release notes for MCP tool changes.
2. Change the pinned version in `cordis.patch.yml` (for example
   `rea-agents@6.7.1`).
3. Reinstall/reload the bundle and re-run `node scripts/preflight.mjs`.

Tool names and schemas are part of the model-facing contract; changing them
invalidates prompt caches and may break saved sessions that reference old tool
names.

## Uninstall

Ask the Harness agent to remove the `dsh-rea` bundle with `plugin_manager`
(`action: remove_bundle`), or disable it with `set_bundle` when you only want to
pause it. Uninstalling the bundle does not remove npm's npx cache or the optional
`~/.agents/skills` copy; remove those separately if you want them gone.

## Limitations

- MCP prompt templates are not supported by `dsh-mcp-client`; REA's six guided
  prompts are not exposed through this bundle. Tools work normally.
- `dsh-mcp-client` exposes tools only after discovery; a crashed npx child keeps
  the last tool set listed until reconnect exhausts its budget.
- REA native providers (Hopper, Ghidra, IDA, JADX, Frida, …) require their own
  installations. The bundle does not install or license them.
- Windows behavior is untested here.

## Security and legal

REA analyzes local artifacts and can launch external helper programs. Only use it
on software you are authorized to inspect, and review REA's own
[DISCLAIMER](https://github.com/morluto/rea/blob/main/DISCLAIMER.md) and
[SECURITY](https://github.com/morluto/rea/blob/main/SECURITY.md) policies. This
bundle adds no telemetry and stores no credentials.

REA is MIT-licensed by its authors. This repository's configuration, docs, and
artwork are MIT-licensed as well; see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md).
