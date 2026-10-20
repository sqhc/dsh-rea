#!/usr/bin/env node
/**
 * Scheduled preflight runner for dsh-rea.
 * Runs preflight and compares with baseline metrics.
 * Used by monitor-upstream.mjs after detecting upstream changes.
 *
 * Usage:
 *   node scripts/run-preflight-scheduled.mjs [--compare-baseline]
 *
 * Exit codes:
 *   0 - preflight OK, baseline matches (or no comparison requested)
 *   1 - preflight OK, but baseline drift detected
 *   2 - preflight failed
 */

import { spawn } from "node:child_process";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { join } from "node:path";
import { homedir } from "node:os";

const ROOT = join(import.meta.dirname, "..");
const PREFLIGHT_SCRIPT = join(ROOT, "scripts/preflight.mjs");
const BASELINE_FILE = join(ROOT, "monitoring-baseline.md");
const LOGS_DIR = join(ROOT, "logs");
const BASELINE = {
  tools: 207,
  catalogKiB: 214.1,
  reaVersion: "6.7.0",
};

function parseArgs() {
  return {
    compareBaseline: process.argv.includes("--compare-baseline"),
  };
}

async function runPreflight() {
  const env = {
    ...process.env,
    PATH: "/Users/shenqing/.nvm/versions/node/v24.21.0/bin:" + process.env.PATH,
    DSH_REA_NPM_CACHE: "/tmp/dsh-rea-npm-cache",
  };

  return new Promise((resolve, reject) => {
    const child = spawn("node", [PREFLIGHT_SCRIPT], {
      env,
      timeout: 300000,
      shell: false,
    });

    let stdout = "";
    let stderr = "";

    child.stdout.on("data", (d) => (stdout += d.toString()));
    child.stderr.on("data", (d) => (stderr += d.toString()));

    child.on("close", (code) => {
      if (code === 0) {
        resolve(stdout.trim());
      } else {
        reject(new Error(`preflight exited ${code}: ${stderr}`));
      }
    });

    child.on("error", reject);
  });
}

function parsePreflight(output) {
  const toolsMatch = output.match(/tools:\s+(\d+)/);
  const catalogMatch = output.match(/catalog:\s+([\d.]+)\s+KiB/);
  const versionMatch = output.match(/REA\s+([\d.]+):/);
  return {
    tools: toolsMatch ? parseInt(toolsMatch[1]) : null,
    catalogKiB: catalogMatch ? parseFloat(catalogMatch[1]) : null,
    reaVersion: versionMatch ? versionMatch[1] : null,
    raw: output,
    ok: output.includes("OK"),
  };
}

function compareWithBaseline(current) {
  const drifts = [];

  if (current.tools !== BASELINE.tools) {
    drifts.push({
      metric: "工具数",
      baseline: BASELINE.tools,
      current: current.tools,
      delta: current.tools - BASELINE.tools,
    });
  }

  if (Math.abs(current.catalogKiB - BASELINE.catalogKiB) > 1) {
    drifts.push({
      metric: "Catalog 大小",
      baseline: `${BASELINE.catalogKiB} KiB`,
      current: `${current.catalogKiB} KiB`,
      delta: (current.catalogKiB - BASELINE.catalogKiB).toFixed(1) + " KiB",
    });
  }

  if (current.reaVersion !== BASELINE.reaVersion) {
    drifts.push({
      metric: "REA 版本",
      baseline: BASELINE.reaVersion,
      current: current.reaVersion,
      delta: "版本变化",
    });
  }

  return drifts;
}

async function main() {
  const { compareBaseline } = parseArgs();

  console.log("🚀 运行定时 preflight...");

  try {
    await mkdir(LOGS_DIR, { recursive: true });

    const output = await runPreflight();
    const result = parsePreflight(output);

    console.log(output);

    if (!result.ok) {
      console.error("❌ Preflight 失败");
      process.exit(2);
    }

    console.log("\n📊 当前指标:");
    console.log(`  工具数: ${result.tools}`);
    console.log(`  Catalog: ${result.catalogKiB} KiB`);
    console.log(`  REA 版本: ${result.reaVersion}`);

    if (compareBaseline) {
      const drifts = compareWithBaseline(result);

      if (drifts.length > 0) {
        console.log("\n⚠️ 基线偏移检测:");
        for (const d of drifts) {
          console.log(`  ${d.metric}: ${d.baseline} → ${d.current} (${d.delta})`);
        }

        // 写入对比报告
        const date = new Date().toISOString().split("T")[0];
        const reportPath = join(LOGS_DIR, `preflight-drift-${date}.md`);
        let report = `# Preflight 基线偏移报告 ${date}\n\n`;
        report += `**检查时间**: ${new Date().toLocaleString()}\n\n`;
        report += `## 偏移详情\n\n`;
        report += `| 指标 | Baseline | 当前 | 变化 |\n`;
        report += `|------|----------|------|------|\n`;
        for (const d of drifts) {
          report += `| ${d.metric} | ${d.baseline} | ${d.current} | ${d.delta} |\n`;
        }
        report += `\n---\n\n## 完整输出\n\n\`\`\`\n${result.raw}\n\`\`\`\n`;
        await writeFile(reportPath, report);
        console.log(`\n📝 偏移报告已写入: ${reportPath}`);

        process.exit(1); // 有偏移
      } else {
        console.log("\n✅ 基线一致，无偏移");
        process.exit(0);
      }
    } else {
      console.log("\n✅ Preflight 通过（未对比 baseline）");
      process.exit(0);
    }
  } catch (e) {
    console.error("❌ 运行失败:", e.message);
    process.exit(2);
  }
}

main();