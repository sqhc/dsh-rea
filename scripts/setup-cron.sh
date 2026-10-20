#!/usr/bin/env bash
# dsh-rea 定时任务设置脚本
# 用法: ./scripts/setup-cron.sh [install|remove|show]
#
# 安装一条用户 crontab：每天 02:00 运行 scripts/monitor-upstream.mjs。
# 注意：这只启动本地 Node 监控脚本（npm 版本检查 + preflight + 生成
# .monitor/ 日报）。它不会启动任何 DSH 智能体或 Bot 团队。

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
NODE_BIN_DIR="$(dirname "$(command -v node)")"
LOG_DIR="$REPO_ROOT/logs"

CRON_JOB="0 2 * * * cd $REPO_ROOT && export PATH=\"$NODE_BIN_DIR:\$PATH\" && node scripts/monitor-upstream.mjs >> $LOG_DIR/monitor-\$(date +\\%F).log 2>&1"

# crontab -l 在没有任何任务时返回非零（部分实现还输出到 stderr），
# 且空管道会让 grep 以退出码 1 结束；set -e 下两者都会中断脚本。
# 这里统一忽略这两类失败，仅在真的写不进 crontab 时报错。
safe_crontab() {
    crontab -l 2>/dev/null || true
}

show_cron() {
    local found
    found="$(safe_crontab | grep -E "dsh-rea|monitor-upstream" || true)"
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
    { safe_crontab | grep -v "monitor-upstream.mjs" || true; echo "$CRON_JOB"; } | crontab -
    echo "✅ 已安装每日 02:00 定时任务"
    show_cron
}

remove_cron() {
    { safe_crontab | grep -v "monitor-upstream.mjs" || true; } | crontab -
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
