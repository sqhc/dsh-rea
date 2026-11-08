#!/usr/bin/env node
/**
 * Apply the upstream ds-bot fix for DSH 0.2.2+ compatibility.
 *
 * Symptom
 *   Every Bot turn fails with:
 *     Cannot read properties of undefined (reading 'filter')
 *   in `~/.dsh/bot/logs/diagnostics.jsonl` as `{"source":"turn","code":"UNKNOWN"}`.
 *
 * Root cause
 *   ds-bot's `filterBotAssembly()` listens on the `system-prompt/assemble` waterfall
 *   and filters `assembled.tools`. DSH 0.2.2 adds the tool list to the assembly
 *   only AFTER that waterfall runs (see `dsh-system-prompt`), so the object the
 *   plugin receives has `sections`/`contexts`/`variables` but no `tools`.
 *   `assembled.tools.filter(...)` therefore throws before the turn starts.
 *
 *   Upstream reference: https://github.com/Fei2411/DS-Bot/issues/953
 *   Fixed upstream in ds-bot 0.3.0/0.3.1.
 *
 * What this script does
 *   Rewrites the one unguarded call site to the same guarded form upstream uses:
 *
 *     tools: assembled.tools.filter(...)                     // 0.2.7 — throws
 *     ...Array.isArray(assembled.tools) ? { tools: ... } : {} // 0.3.1 — safe
 *
 * Usage
 *   node scripts/patch-ds-bot-assembly.mjs            # apply (idempotent)
 *   node scripts/patch-ds-bot-assembly.mjs --check    # report only, change nothing
 *   node scripts/patch-ds-bot-assembly.mjs --restore  # undo, from the .bak file
 *
 * Note
 *   A ds-bot upgrade overwrites the patch. Re-run this script afterwards, or
 *   upgrade ds-bot to >= 0.3.1 where the fix ships.
 */

import { existsSync, readFileSync, writeFileSync, copyFileSync, readdirSync } from "node:fs";
import { homedir } from "node:os";
import { join } from "node:path";

const DSH_HOME = process.env.DSH_HOME ?? join(homedir(), ".dsh");
const PROFILE = process.env.DSH_PROFILE ?? "desktop";
const TARGET = join(DSH_HOME, "profiles", PROFILE, "node_modules", "ds-bot", "src", "host", "tools.js");

const OLD = `      const assembled = await next()
      return {
        ...assembled,
        tools: assembled.tools.filter(tool => !HIDDEN_TOOLS.includes(tool.name)),
        sections: assembled.sections.filter(section => !HIDDEN_SECTIONS.has(section.name)),
      }`;

const NEW = `      const assembled = await next()
      // DSH 0.2.2 adds the tool list after this waterfall (#814), so only an
      // older assembly still carries tools to drop here.
      return {
        ...assembled,
        ...Array.isArray(assembled.tools) ? { tools: assembled.tools.filter(tool => !HIDDEN_TOOLS.includes(tool.name)) } : {},
        sections: assembled.sections.filter(section => !HIDDEN_SECTIONS.has(section.name)),
      }`;

const args = process.argv.slice(2);
const checkOnly = args.includes("--check");
const restore = args.includes("--restore");

if (!existsSync(TARGET)) {
  console.error(`❌ 未找到 ds-bot 源文件: ${TARGET}`);
  console.error("   请确认 ds-bot 已安装在该 profile 的 node_modules 中。");
  process.exit(1);
}

const source = readFileSync(TARGET, "utf8");
const alreadyFixed = source.includes("Array.isArray(assembled.tools)");
const needsPatch = source.includes(OLD);

if (restore) {
  const dir = TARGET.replace(/\/tools\.js$/, "");
  const backups = readdirSync(dir).filter(name => name.startsWith("tools.js.bak-")).sort();
  if (backups.length === 0) {
    console.error("❌ 未找到备份文件（tools.js.bak-*），无法还原。");
    process.exit(1);
  }
  const backup = join(dir, backups.at(-1));
  copyFileSync(backup, TARGET);
  console.log(`✅ 已从 ${backups.at(-1)} 还原。`);
  console.log("   记得重启 DeepSeek Harness 才会生效。");
  process.exit(0);
}

if (alreadyFixed && !needsPatch) {
  console.log(`✅ 已是修复后的版本，无需改动: ${TARGET}`);
  console.log("   （DSH 需重启后才会加载新代码）");
  process.exit(0);
}

if (!needsPatch) {
  console.error("❌ 未找到预期的旧代码片段，ds-bot 版本可能已变化，请人工检查:");
  console.error(`   ${TARGET}`);
  process.exit(1);
}

if (checkOnly) {
  console.log("⚠️  检测到需要修补（尚未应用）:");
  console.log(`   ${TARGET}`);
  console.log("   运行: node scripts/patch-ds-bot-assembly.mjs");
  process.exit(0);
}

const backup = TARGET.replace(/\/tools\.js$/, "/tools.js.bak-" + new Date().toISOString().replace(/[:.]/g, "-"));
copyFileSync(TARGET, backup);
writeFileSync(TARGET, source.replace(OLD, NEW));

console.log(`✅ 已修补: ${TARGET}`);
console.log(`   备份: ${backup.split("/").pop()}`);
console.log("   记得完全退出并重新打开 DeepSeek Harness 才会生效。");
