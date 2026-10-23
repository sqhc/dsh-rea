#!/usr/bin/env node
// dsh-rea 监控报告检查脚本
// 每日 02:30 运行，检查 02:00 生成的监控报告
// 若发现版本变化（退出码 1），触发工作流：生成评估 PR，通知 Chief 审批

import { readFileSync, readdirSync, existsSync } from 'fs';
import { join } from 'path';

const REPO_ROOT = join(process.cwd());
const MONITOR_DIR = join(REPO_ROOT, '.monitor');

function getLatestMonitorReport() {
    if (!existsSync(MONITOR_DIR)) {
        console.log('⚠️  监控目录不存在');
        return null;
    }

    const files = readdirSync(MONITOR_DIR)
        .filter(f => f.startsWith('monitoring-') && f.endsWith('.md'))
        .sort()
        .reverse();

    if (files.length === 0) {
        console.log('⚠️  无监控报告文件');
        return null;
    }

    const latest = files[0];
    const content = readFileSync(join(MONITOR_DIR, latest), 'utf-8');
    return { file: latest, content };
}

function parseReport(content) {
    // 检查报告中是否包含版本变化标记
    const hasVersionChange = content.includes('⚠️ **检测到版本差异**') ||
                            content.includes('⚠️ **基线偏移**') ||
                            content.includes('版本差异') ||
                            content.includes('has changes');

    // 从表格中提取版本信息
    const reaLockedMatch = content.match(/\| rea-agents\s*\|\s*([\d.]+)\s*\|/);
    const reaLatestMatch = content.match(/\| rea-agents\s*\|.*?\|\s*([\d.]+)\s*\|/);
    const dshLatestMatch = content.match(/\| @deepseek-ai\/dsh-mcp-client\s*\|.*?\|\s*([\d.-]+)\s*\|/);
    const preflightMatch = content.match(/\| 工具数\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|/);
    const catalogMatch = content.match(/\| Catalog\s*\|\s*([\d.]+)\s*KiB\s*\|\s*([\d.]+)\s*KiB\s*\|/);
    const reaVersionMatch = content.match(/\| REA 版本\s*\|\s*([\d.]+)\s*\|\s*([\d.]+)\s*\|/);

    return {
        hasVersionChange,
        reaVersion: reaLockedMatch ? reaLockedMatch[1] : (reaLatestMatch ? reaLatestMatch[1] : null),
        reaLatestVersion: reaLatestMatch ? reaLatestMatch[1] : null,
        dshVersion: dshLatestMatch ? dshLatestMatch[1] : null,
        preflight: (preflightMatch && catalogMatch && reaVersionMatch) ? {
            tools: parseInt(preflightMatch[2]),
            catalog: catalogMatch[2],
            rea: reaVersionMatch[2]
        } : null
    };
}

function checkBaselineDrift(parsed) {
    const BASELINE = { tools: 207, catalog: '214.1', rea: '6.7.0' };

    if (!parsed.preflight) return false;

    const drift = parsed.preflight.tools !== BASELINE.tools ||
                  parsed.preflight.catalog !== BASELINE.catalog ||
                  parsed.preflight.rea !== BASELINE.rea;

    return drift;
}

async function main() {
    console.log('🔍 检查每日监控报告...');

    const report = getLatestMonitorReport();
    if (!report) {
        console.log('❌ 无法读取监控报告，退出码 1');
        process.exit(1);
    }

    console.log(`📄 读取报告: ${report.file}`);

    const parsed = parseReport(report.content);
    const hasDrift = checkBaselineDrift(parsed);

    if (parsed.hasVersionChange || hasDrift) {
        console.log('🚨 发现版本变化或基线偏移！');
        console.log(`   rea-agents: ${parsed.reaVersion}`);
        console.log(`   dsh-mcp-client: ${parsed.dshVersion}`);
        if (parsed.preflight) {
            console.log(`   Preflight: ${parsed.preflight.tools} tools, ${parsed.preflight.catalog} KiB, REA ${parsed.preflight.rea}`);
        }
        if (hasDrift) {
            console.log('   ⚠️  基线偏移: 工具数/目录大小/REA版本与基线不符');
        }

        // 这里可以触发生成 PR 的逻辑
        // 例如：生成评估报告 PR、创建 GitHub Issue、发送通知等
        console.log('📋 应触发工作流：生成评估 PR，通知 Chief 审批');

        process.exit(1); // 非零退出码表示有变化，供上层捕获
    } else {
        console.log('✅ 无版本变化，基线一致，保持现状');
        console.log(`   rea-agents: ${parsed.reaVersion} (锁定 6.7.0)`);
        console.log(`   dsh-mcp-client: ${parsed.dshVersion} (latest 陈旧，next/alpha 活跃)`);
        process.exit(0);
    }
}

main().catch(err => {
    console.error('❌ 检查脚本异常:', err);
    process.exit(1);
});