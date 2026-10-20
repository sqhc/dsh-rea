# NOTICE

## Unofficial integration

`dsh-rea` is an independent DeepSeek Harness bundle. It is not affiliated with,
endorsed by, sponsored by, or published by the REA project or its maintainers.
The names "REA" and "Reverse Engineer Anything" refer to the upstream project.

## Upstream project

- Project: REA — Reverse Engineer Anything
- Source: https://github.com/morluto/rea
- Package: https://www.npmjs.com/package/rea-agents
- License: MIT (see the upstream LICENSE)
- Documentation: https://rea.tools/

## What this repository contains

This repository does **not** contain, copy, vendor, fork, or modify REA source
code, binaries, documentation, or artwork. It contains only:

- a DeepSeek Harness bundle manifest and Cordis patch,
- display metadata (locale JSON and an original SVG icon authored for this
  repository),
- installation and troubleshooting documentation,
- a dependency-free preflight script.

At runtime the bundle asks `npx` to download and run the official
`rea-agents` npm package, pinned to an exact version in `cordis.patch.yml`. That
package remains governed by its own MIT license, disclaimers, and security
policy.

## Upstream policies that still apply

Users of this bundle are expected to follow REA's own guidance:

- DISCLAIMER: https://github.com/morluto/rea/blob/main/DISCLAIMER.md
- SECURITY: https://github.com/morluto/rea/blob/main/SECURITY.md
- THIRD_PARTY_NOTICES: https://github.com/morluto/rea/blob/main/THIRD_PARTY_NOTICES.md

REA's native analysis providers (for example Hopper, Ghidra, IDA, JADX, and
Frida) are separate software with their own licenses and prerequisites. This
bundle does not install or license them.

## Trademarks

Any product names, logos, and brands are the property of their respective
owners. They are used here only for identification and attribution.
