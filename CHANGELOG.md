# Changelog

All notable changes to `dsh-rea` are documented in this file. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres
to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-10-20

### Added

- Configuration-only DeepSeek Harness bundle that connects the official REA MCP
  server over stdio through the harness-shipped
  `@deepseek-ai/dsh-mcp-client`.
- Pinned `rea-agents@6.7.0`; 207 REA tools exposed as `mcp__rea__<tool>`.
- Bounded catalog defaults: compact input schemas and output schemas off
  (~214 KiB, ~55k tokens).
- Locale metadata (English/Chinese), original SVG icon, bilingual README, and a
  NOTICE with upstream attribution.
- Dependency-free `scripts/preflight.mjs` that checks the Node version and npm
  cache, performs an MCP initialize + `tools/list` handshake, and reports the
  tool count and catalog size.
- Upstream monitoring helpers (`scripts/monitor-upstream.mjs`,
  `scripts/cron-monitor.mjs`, `scripts/run-preflight-scheduled.mjs`,
  `scripts/setup-cron.sh`) and `monitoring-baseline.md`.
- Promo assets (`promo.mp4`, `promo.webm`, `promo.gif`, `promo-poster.png`) and
  `PROMO_SCRIPT.md`.
- Version compatibility tables in both READMEs.

### Changed

- Helper scripts derive the repository and Node paths from the checkout and the
  running executable instead of hardcoding a local user path.
- The GitHub README uses an animated GIF preview plus MP4/WebM/poster links
  because GitHub's Markdown sanitizer strips `<video>` tags.
- Ignore dsh-ops lock files, generated `.monitor/` reports, logs, and Python
  caches.
- Resolve the README conflict markers left by the initial local commit.

### Verified

- macOS arm64, DeepSeek Harness with
  `@deepseek-ai/dsh-mcp-client@0.2.1-rc.2`.
- Node.js 24.21.0, REA 6.7.0, MCP protocol `2026-07-28`; 207 tools registered.
- `mcp__rea__binary_session` succeeds and the SQLite provider is available.
- Linux is expected to work the same way; Windows is untested.

### Known limitations

- MCP prompt templates are not supported by `dsh-mcp-client`; REA's six guided
  prompts are not exposed through this bundle.
- Native REA providers (Hopper, Ghidra, IDA, JADX, Frida, ...) require separate
  installations and licenses.
- The monitoring helper's GitHub release metadata query uses the `gh` CLI, which
  is not installed by default; npm version checks still work.

[0.1.0]: https://github.com/sqhc/dsh-rea/releases/tag/v0.1.0
