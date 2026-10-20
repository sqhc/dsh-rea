#!/usr/bin/env bash
# dsh-rea 定时任务设置脚本
# 用法: ./scripts/setup-cron.sh [install|remove|show]

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NODE_PATH="$(dirname "$(command -v node)")"
MONITOR_SCRIPT="$REPO_ROOT/scripts/monitor-upstream.mjs"
PREFLIGHT_SCRIPT="$REPO_ROOT/scripts/run-preflight-scheduled.mjs"
LOG_DIR="$REPO_ROOT/logs"

CRON_JOB="0 2 * * * cd $REPO_ROOT && export PATH=\"$NODE_PATH:\$PATH\" && node scripts/monitor-upstream.mjs >> $LOG_DIR/monitor-\$(date +\\%F).log 2>&1"

show_cron() {
    echo "当前计划任务:"
    crontab -l 2>/dev/null | grep -E "dsh-rea|monitor-upstream" || echo "  (无)"
}

install_cron() {
    mkdir -p "$LOG_DIR"
    # 移除旧的同名任务
    crontab -l 2>/dev/null | grep -v "monitor-upstream.mjs" | crontab -
    # 添加新任务
    (crontab -l 2>/dev/null; echo "$CRON_JOB") | crontab -
    echo "✅ 已安装每日 02:00 定时任务"
    show_cron
}

remove_cron() {
    crontab -l 2>/dev/null | grep -v "monitor-upstream.mjs" | crontab -
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