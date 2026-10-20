#!/usr/bin/env node
/**
 * 定时任务入口：上游监控 + 回归测试触发
 * 设计为 cron 调用：每天 02:00 运行
 * 
 * 流程：
 * 1. 运行 monitor-upstream.mjs 检查版本变化
 * 2. 如有变化且 PR 已合并（检测 cordis.patch.yml 版本已更新）→ 触发 preflight 回归测试
 * 3. 输出日志到 logs/ 目录
 */

import { spawn } from "node:child_process";
import { readFile, writeFile, mkdir, readdir } from "node:fs/promises";
import { dirname, join } from "node:path";
import { homedir } from "node:os";

const REPO_ROOT = join(import.meta.dirname, "..");
const LOGS_DIR = join(REPO_ROOT, "logs");
const CORDIS_PATCH = join(REPO_ROOT, "cordis.patch.yml");

async function runCommand(cmd, args, options = {}) {
  return new Promise((resolve, reject) => {
    const child = spawn(cmd, args, { ...options, shell: true });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", d => stdout += d.toString());
    child.stderr.on("data", d => stderr += d.toString());
    child.on("close", code => {
      if (code === 0) resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() });
      else resolve({ code, stdout: stdout.trim(), stderr: stderr.trim() });
    });
    child.on("error", reject);
  });
}

async function getCurrentReaVersion() {
  const content = await readFile(CORDIS_PATCH, "utf8");
  const match = content.match(/rea-agents@([\d.]+)/);
  return match ? match[1] : null;
}

async function getLastMonitoredVersion() {
  try {
    const files = await readdir(join(REPO_ROOT, ".monitor"));
    const reports = files.filter(f => f.startsWith("monitoring-") && f.endsWith(".md")).sort().reverse();
    if (reports.length === 0) return null;
    const latest = await readFile(join(REPO_ROOT, ".monitor", reports[0]), "utf8");
    const match = latest.match(/\| rea-agents \| ([^|]+) \|/);
    return match ? match[1].trim() : null;
  } catch {
    return null;
  }
}

async function runPreflight() {
  const env = {
    ...process.env,
    PATH: dirname(process.execPath) + ":" + process.env.PATH,
    DSH_REA_NPM_CACHE: "/tmp/dsh-rea-npm-cache"
  };
  return runCommand("node", ["scripts/preflight.mjs"], { env, timeout: 300000 });
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

async function main() {
  const timestamp = new Date().toISOString().replace(/[:.]/g, "-");
  const logFile = join(LOGS_DIR, `cron-${timestamp}.log`);
  
  await mkdir(LOGS_DIR, { recursive: true });
  
  const log = (msg) => {
    const line = `[${new Date().toLocaleString()}] ${msg}`;
    console.log(line);
    return line;
  };
  
  const logLines = [];
  const addLog = (msg) => logLines.push(log(msg));
  
  addLog("🕐 定时任务启动");
  
  try {
    // 步骤 1: 运行上游监控
    addLog("📡 步骤 1/3: 运行上游监控检查...");
    const monitorResult = await runCommand("node", ["scripts/monitor-upstream.mjs"], { 
      cwd: REPO_ROOT,
      timeout: 300000 
    });
    
    addLog(`监控退出码: ${monitorResult.code}`);
    if (monitorResult.stdout) addLog(`STDOUT: ${monitorResult.stdout.slice(-500)}`);
    if (monitorResult.stderr) addLog(`STDERR: ${monitorResult.stderr.slice(-500)}`);
    
    // 步骤 2: 检测是否有版本变化且已合并
    const currentVersion = await getCurrentReaVersion();
    const lastMonitored = await getLastMonitoredVersion();
    
    addLog(`当前锁定版本: ${currentVersion}`);
    addLog(`上次监控版本: ${lastMonitored}`);
    
    // 如果监控脚本退出码为 1（有变化）但当前版本已更新，说明 PR 已合并
    const versionUpdated = lastMonitored && currentVersion !== lastMonitored;
    const monitorDetectedChange = monitorResult.code === 1;
    
    if (versionUpdated || monitorDetectedChange) {
      addLog("🔄 检测到版本已更新，触发回归测试...");
      
      // 步骤 3: 运行 preflight 回归测试
      addLog("🧪 步骤 2/3: 运行 preflight 回归测试...");
      const preflightResult = await runPreflight();
      
      addLog(`Preflight 退出码: ${preflightResult.code}`);
      if (preflightResult.stdout) addLog(`STDOUT: ${preflightResult.stdout.slice(-800)}`);
      if (preflightResult.stderr) addLog(`STDERR: ${preflightResult.stderr.slice(-800)}`);
      
      const preflight = parsePreflight(preflightResult.stdout);
      addLog(`回归结果: ${preflight.tools} tools, ${preflight.catalogKiB} KiB, REA ${preflight.reaVersion}`);
      
      // 对比 baseline
      const baseline = { tools: 207, catalogKiB: 214.1, reaVersion: "6.7.0" };
      const toolDiff = preflight.tools - baseline.tools;
      const catalogDiff = (preflight.catalogKiB - baseline.catalogKiB).toFixed(1);
      const versionSame = preflight.reaVersion === baseline.reaVersion;
      
      addLog(`基线对比: tools ${toolDiff >= 0 ? "+" : ""}${toolDiff}, catalog ${catalogDiff >= 0 ? "+" : ""}${catalogDiff} KiB, version ${versionSame ? "同步" : "变化"}`);
      
      // 生成回归测试报告
      let regressionReport = `# 回归测试报告 ${new Date().toISOString().split("T")[0]}\n\n`;
      regressionReport += `**触发原因**: ${versionUpdated ? "版本已合并更新" : "监控检测到上游变化"}\n\n`;
      regressionReport += `## 指标对比\n\n`;
      regressionReport += `| 指标 | Baseline | 当前 | 变化 |\n`;
      regressionReport += `|------|----------|------|------|\n`;
      regressionReport += `| 工具数 | ${baseline.tools} | ${preflight.tools} | ${toolDiff >= 0 ? "+" : ""}${toolDiff} |\n`;
      regressionReport += `| Catalog | ${baseline.catalogKiB} KiB | ${preflight.catalogKiB} KiB | ${catalogDiff >= 0 ? "+" : ""}${catalogDiff} KiB |\n`;
      regressionReport += `| REA 版本 | ${baseline.reaVersion} | ${preflight.reaVersion} | ${versionSame ? "同步" : "变化"} |\n\n`;
      
      if (!versionSame || toolDiff !== 0 || Math.abs(catalogDiff) > 1) {
        regressionReport += `⚠️ **基线偏移**，请 Team Lead 评估是否接受\n`;
      } else {
        regressionReport += `✅ 基线一致，回归测试通过\n`;
      }
      
      const reportPath = join(REPO_ROOT, ".monitor", `regression-${new Date().toISOString().split("T")[0]}.md`);
      await writeFile(reportPath, regressionReport);
      addLog(`📝 回归报告: ${reportPath}`);
      
    } else {
      addLog("✅ 无版本变化，跳过回归测试");
    }
    
    addLog("🏁 定时任务完成");
    
  } catch (e) {
    addLog(`❌ 定时任务异常: ${e.message}`);
    if (e.stack) addLog(e.stack.split("\n").slice(0, 5).join("\n"));
  } finally {
    await writeFile(logFile, logLines.join("\n"));
    console.log(`日志已写入: ${logFile}`);
  }
}

main().catch(e => {
  console.error("Fatal:", e);
  process.exit(1);
});