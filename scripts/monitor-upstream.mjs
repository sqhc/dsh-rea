#!/usr/bin/env node
/**
 * dsh-rea 上游监控脚本
 * 每日运行，检查 rea-agents 和 dsh-mcp-client 版本变化
 * 有变化则生成评估报告并提 PR（不自动合并）
 */

import { spawn } from "node:child_process";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { homedir } from "node:os";

const ROOT = join(import.meta.dirname, "..");
const CORDIS_PATCH = join(ROOT, "cordis.patch.yml");
const MONITOR_DIR = join(ROOT, ".monitor");
const BASELINE_FILE = join(ROOT, "monitoring-baseline.md");
const NODE_BIN_DIR = dirname(process.execPath);

async function runCommand(cmd, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { ...options, shell: true });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", d => stdout += d.toString());
    child.stderr.on("data", d => stderr += d.toString());
    child.on("close", code => {
      if (code === 0) resolve(stdout.trim());
      else reject(new Error(`${cmd} exited ${code}: ${stderr}`));
    });
    child.on("error", reject);
  });
}

async function getCurrentReaVersion() {
  const content = await readFile(CORDIS_PATCH, "utf8");
  const match = content.match(/rea-agents@([\d.]+)/);
  return match ? match[1] : null;
}

async function getNpmVersion(pkg, tag = "latest") {
  try {
    const out = await runCommand("npm", ["view", `${pkg}@${tag}`, "version", "--json", "--cache=/tmp/npm-cache"]);
    return JSON.parse(out);
  } catch {
    return null;
  }
}

async function getNpmVersions(pkg) {
  try {
    const out = await runCommand("npm", ["view", pkg, "versions", "--json", "--cache=/tmp/npm-cache"]);
    return JSON.parse(out);
  } catch {
    return [];
  }
}

async function getGitHubReleases() {
  try {
    const out = await runCommand("gh", ["api", "repos/morluto/rea/releases", "--jq", ".[0].tag_name,.[0].published_at,.[0].body"]);
    const lines = out.split("\n");
    return {
      tag: lines[0],
      date: lines[1],
      body: lines.slice(2).join("\n")
    };
  } catch {
    return null;
  }
}

async function runPreflight() {
  const env = {
    ...process.env,
    PATH: NODE_BIN_DIR + ":" + process.env.PATH,
    DSH_REA_NPM_CACHE: "/tmp/dsh-rea-npm-cache"
  };
  try {
    const out = await runCommand("node", ["scripts/preflight.mjs"], { env, timeout: 300000 });
    return out;
  } catch (e) {
    return `FAIL: ${e.message}`;
  }
}

function parsePreflight(output) {
  const toolsMatch = output.match(/tools:\s+(\d+)/);
  const catalogMatch = output.match(/catalog:\s+([\d.]+)\s+KiB/);
  const versionMatch = output.match(/REA\s+([\d.]+):/);
  return {
    tools: toolsMatch ? parseInt(toolsMatch[1]) : null,
    catalogKiB: catalogMatch ? parseFloat(catalogMatch[1]) : null,
    reaVersion: versionMatch ? versionMatch[1] : null,
    raw: output
  };
}

async function generateReport(current, latest, dshClient, preflight, ghRelease) {
  const date = new Date().toISOString().split("T")[0];
  const hasChanges = current !== latest.rea || (ghRelease && current !== ghRelease.tag?.replace("rea-agents-", ""));
  
  let report = `# 上游监控日报 ${date}\n\n`;
  report += `**检查时间**: ${new Date().toLocaleString()}\n\n`;
  
  report += `## 版本对比\n\n`;
  report += `| 包 | 当前锁定 | npm latest | npm next | npm alpha | GitHub latest |\n`;
  report += `|------|----------|------------|----------|-----------|---------------|\n`;
  report += `| rea-agents | ${current} | ${latest.rea} | ${latest.reaNext || "-"} | ${latest.reaAlpha || "-"} | ${ghRelease?.tag?.replace("rea-agents-", "") || "-"} |\n`;
  report += `| @deepseek-ai/dsh-mcp-client | (DSH 管理) | ${dshClient.latest} | ${dshClient.next} | ${dshClient.alpha} | -\n\n`;
  
  report += `## 变更评估\n\n`;
  if (hasChanges) {
    report += `⚠️ **检测到版本差异**\n\n`;
    if (current !== latest.rea) {
      report += `- rea-agents: ${current} → ${latest.rea} (${latest.rea > current ? "可升级" : "版本回退"})\n`;
    }
    if (ghRelease && current !== ghRelease.tag.replace("rea-agents-", "")) {
      report += `- GitHub 有新 release: ${ghRelease.tag} (${ghRelease.date})\n`;
    }
  } else {
    report += `✅ 无版本变化，保持当前锁定版本 ${current}\n`;
  }
  
  report += `\n## Preflight 基线对比\n\n`;
  if (preflight.tools) {
    report += `| 指标 | Baseline | 当前 | 变化 |\n`;
    report += `|------|----------|------|------|\n`;
    report += `| 工具数 | 207 | ${preflight.tools} | ${preflight.tools - 207 >= 0 ? "+" : ""}${preflight.tools - 207} |\n`;
    report += `| Catalog | 214.1 KiB | ${preflight.catalogKiB} KiB | ${(preflight.catalogKiB - 214.1).toFixed(1)} KiB |\n`;
    report += `| REA 版本 | 6.7.0 | ${preflight.reaVersion} | ${preflight.reaVersion === "6.7.0" ? "同步" : "变化"} |\n\n`;
    
    if (preflight.tools !== 207 || Math.abs(preflight.catalogKiB - 214.1) > 1 || preflight.reaVersion !== "6.7.0") {
      report += `⚠️ **基线偏移**，需人工评估是否跟随升级\n`;
    } else {
      report += `✅ 基线一致\n`;
    }
  } else {
    report += `❌ Preflight 失败: ${preflight.raw}\n`;
  }
  
  if (ghRelease) {
    report += `\n## GitHub Release Notes 摘要\n\n`;
    const body = ghRelease.body.slice(0, 2000);
    report += body + (ghRelease.body.length > 2000 ? "\n...(截断)" : "");
  }
  
  report += `\n## 建议行动\n\n`;
  if (hasChanges) {
    report += `1. **创建评估 PR**：更新 cordis.patch.yml 和 preflight.mjs 中的版本号\n`;
    report += `2. **Team Lead 审批**：决定是否跟随、跳过中间版本\n`;
    report += `3. **合并后回归**：跑 preflight 对比 baseline\n`;
  } else {
    report += `1. 保持现状，下次定时检查再评估\n`;
  }
  
  return report;
}

async function main() {
  console.log("🔍 开始上游监控检查...");
  
  await mkdir(MONITOR_DIR, { recursive: true });
  
  // 1. 获取当前锁定版本
  const currentRea = await getCurrentReaVersion();
  console.log(`当前锁定: rea-agents@${currentRea}`);
  
  // 2. 检查 npm 版本
  const [reaLatest, reaNext, reaAlpha, dshLatest, dshNext, dshAlpha] = await Promise.all([
    getNpmVersion("rea-agents", "latest"),
    getNpmVersion("rea-agents", "next"),
    getNpmVersion("rea-agents", "alpha"),
    getNpmVersion("@deepseek-ai/dsh-mcp-client", "latest"),
    getNpmVersion("@deepseek-ai/dsh-mcp-client", "next"),
    getNpmVersion("@deepseek-ai/dsh-mcp-client", "alpha"),
  ]);
  
  console.log(`rea-agents: latest=${reaLatest}, next=${reaNext}, alpha=${reaAlpha}`);
  console.log(`dsh-mcp-client: latest=${dshLatest}, next=${dshNext}, alpha=${dshAlpha}`);
  
  // 3. 检查 GitHub releases
  const ghRelease = await getGitHubReleases();
  console.log(`GitHub latest: ${ghRelease?.tag}`);
  
  // 4. 跑 preflight
  console.log("🚀 运行 preflight...");
  const preflightOutput = await runPreflight();
  const preflight = parsePreflight(preflightOutput);
  console.log(`Preflight: ${preflight.tools} tools, ${preflight.catalogKiB} KiB, REA ${preflight.reaVersion}`);
  
  // 5. 生成报告
  const report = await generateReport(
    currentRea,
    { rea: reaLatest, reaNext, reaAlpha },
    { latest: dshLatest, next: dshNext, alpha: dshAlpha },
    preflight,
    ghRelease
  );
  
  const date = new Date().toISOString().split("T")[0];
  const reportPath = join(MONITOR_DIR, `monitoring-${date}.md`);
  await writeFile(reportPath, report);
  console.log(`📝 报告已写入: ${reportPath}`);
  
  // 6. 判断是否需要创建 PR
  const hasChanges = currentRea !== reaLatest || (ghRelease && currentRea !== ghRelease.tag.replace("rea-agents-", ""));
  
  if (hasChanges) {
    console.log("⚠️ 检测到版本变化，建议创建 PR");
    // 这里可以集成 gh CLI 创建 PR
    // 暂时只输出报告路径，供人工处理
    process.exit(1); // 非零退出码表示有变化
  } else {
    console.log("✅ 无变化，保持现状");
    process.exit(0);
  }
}

main().catch(e => {
  console.error("❌ 监控失败:", e);
  process.exit(2);
});