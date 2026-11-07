#!/usr/bin/env bash
# dsh-rea 定时任务设置脚本
# 用法: ./scripts/setup-cron.sh [install|remove|show]
#
# 安装两条用户 crontab：每天 02:00 运行 scripts/monitor-upstream.mjs，
# 02:30 运行 scripts/check-monitoring-report.mjs。
# 注意：这只启动本地 Node 监控脚本（npm 版本检查 + preflight + 生成
# .monitor/ 日报）。它不会启动任何 DSH 智能体或 Bot 团队。
#
# 关键点：cron 用 /bin/sh 执行命令行，且 cron 的默认 PATH 不含 nvm 的 node。
# 因此这里把 PATH 与 node 路径在安装时固化进任务，并给带空格的路径加引号。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$REPO_ROOT/logs"

# 安装时解析 node 绝对路径（cron 的 PATH 里没有 nvm，直接写死最可靠）。
NODE_BIN="$(command -v node || true)"
if [ -z "$NODE_BIN" ]; then
    echo "❌ 未找到 node，请先安装 Node.js 或把 node 加入 PATH" >&2
    exit 1
fi
NODE_BIN_DIR="$(dirname "$NODE_BIN")"

# npm/npx 缓存目录：默认 ~/.npm 可能被 root 占用导致 EPERM，用 /tmp 更安全。
NPM_CACHE_DIR="${DSH_REA_NPM_CACHE:-/tmp/dsh-rea-npm-cache}"

# 仓库路径可能含空格（"Deepseek Harness"），必须加引号，否则 cron 的
# /bin/sh 会把 cd 的参数截断成 "/Users/shenqing/Desktop/Deepseek"。
SHELL_WRAPPER="cd \"$REPO_ROOT\" && export PATH=\"$NODE_BIN_DIR:\$PATH\" && export DSH_REA_NPM_CACHE=$NPM_CACHE_DIR &&"

CRON_JOB_MONITOR="0 2 * * * $SHELL_WRAPPER node scripts/monitor-upstream.mjs >> \"$LOG_DIR/monitor-\$(date +\\%F).log\" 2>&1"

# 02:30 检查监控报告，若发现版本变化则触发工作流（生成 PR、通知 Chief 审批）
CRON_JOB_CHECK="30 2 * * * $SHELL_WRAPPER node scripts/check-monitoring-report.mjs >> \"$LOG_DIR/check-\$(date +\\%F).log\" 2>&1"

# crontab -l 在没有任何任务时返回非零（部分实现还输出到 stderr），
# 且空管道会让 grep 以退出码 1 结束；set -e 下两者都会中断脚本。
# 这里统一忽略这两类失败，仅在真的写不进 crontab 时报错。
safe_crontab() {
    crontab -l 2>/dev/null || true
}

show_cron() {
    local found
    found="$(safe_crontab | grep -E "dsh-rea|monitor-upstream|check-monitoring" || true)"
    echo "当前计划任务:"
    if [ -n "$found" ]; then
        echo "$found"
    else
        echo "  (无)"
    fi
}

install_cron() {
    mkdir -p "$LOG_DIR"
    # 移除旧的同名任务后写入新任务（对空 crontab 保持幂等）。
    { safe_crontab | grep -v -E "monitor-upstream.mjs|check-monitoring-report.mjs" || true; echo "$CRON_JOB_MONITOR"; echo "$CRON_JOB_CHECK"; } | crontab -
    echo "✅ 已安装每日 02:00 监控 + 02:30 检查报告定时任务"
    echo "   node: $NODE_BIN"
    echo "   npm cache: $NPM_CACHE_DIR"
    show_cron
}

remove_cron() {
    { safe_crontab | grep -v -E "monitor-upstream.mjs|check-monitoring-report.mjs" || true; } | crontab -
    echo "✅ 已移除定时任务"
    show_cron
}

case "${1:-show}" in
    install)
        install_cron
        ;;
    remove)
        remove_cron
        ;;
    show|"")
        show_cron
        ;;
    *)
        echo "用法: $0 [install|remove|show]"
        exit 1
        ;;
esac
