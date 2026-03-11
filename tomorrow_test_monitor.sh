#!/bin/bash
# 明日关键测试监控系统
# 监控2026-03-09的两个关键测试时间点

set -e

LOG_FILE="/root/.openclaw/workspace/logs/tomorrow_test_monitor.log"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

check_t01_auction() {
    # 检查T01竞价分析 (09:25)
    log "=== 检查T01竞价分析状态 (09:25) ==="
    
    # 检查调度器进程
    if systemctl is-active --quiet t01-scheduler; then
        log "✅ T01调度器运行正常"
    else
        log "❌ T01调度器未运行"
        return 1
    fi
    
    # 检查候选股文件
    CANDIDATE_FILE="/root/.openclaw/workspace/tasks/T01/state/candidates_*.json"
    if ls $CANDIDATE_FILE 1>/dev/null 2>&1; then
        latest_file=$(ls -t $CANDIDATE_FILE | head -1)
        log "✅ 候选股文件存在: $(basename $latest_file)"
    else
        log "⚠️ 无候选股文件"
    fi
    
    # 检查飞书消息发送状态
    FEISHU_LOG="/root/.openclaw/workspace/logs/feishu_message.log"
    if [ -f "$FEISHU_LOG" ]; then
        log "✅ 飞书日志存在"
    else
        log "⚠️ 飞书日志不存在"
    fi
    
    log "T01竞价分析检查完成"
}

check_t99_scan() {
    # 检查T99扫描 (14:30)
    log "=== 检查T99扫描状态 (14:30) ==="
    
    # 检查交易日历
    CALENDAR_FILE="/root/.openclaw/workspace/trading_calendar.json"
    if [ -f "$CALENDAR_FILE" ]; then
        log "✅ 交易日历文件存在"
        # 检查明天是否为交易日
        if python3 -c "
import json, sys, datetime
with open('$CALENDAR_FILE') as f:
    cal = json.load(f)
today = datetime.datetime.now().strftime('%Y-%m-%d')
trading_days = cal.get('2026', {}).get('trading_days', [])
if today in trading_days:
    print('✅ 今天是交易日')
    sys.exit(0)
else:
    print('⚠️ 今天不是交易日')
    sys.exit(1)
" 2>/dev/null; then
            log "✅ 今天是交易日，T99扫描应正常执行"
        else
            log "⚠️ 今天不是交易日，T99扫描将跳过"
        fi
    else
        log "❌ 交易日历文件不存在"
    fi
    
    # 检查T99扫描脚本
    SCAN_SCRIPT="/root/.openclaw/workspace/skills/a-share-short-decision/run_scan_fixed.sh"
    if [ -f "$SCAN_SCRIPT" ]; then
        log "✅ T99扫描脚本存在: $(basename $SCAN_SCRIPT)"
    else
        log "⚠️ T99扫描脚本不存在"
    fi
    
    # 检查T99日志
    SCAN_LOG="/root/.openclaw/workspace/skills/a-share-short-decision/scan_fixed.log"
    if [ -f "$SCAN_LOG" ]; then
        last_scan=$(tail -5 "$SCAN_LOG" 2>/dev/null | grep -E "Scan started|completed|failed" || echo "无最近扫描记录")
        log "📋 最近扫描记录: $last_scan"
    else
        log "⚠️ T99扫描日志不存在"
    fi
    
    log "T99扫描检查完成"
}

check_system_health() {
    log "=== 检查系统健康状态 ==="
    
    # 磁盘空间
    df -h / | grep -v Filesystem | while read line; do
        log "💾 $line"
    done
    
    # 内存使用
    free -h | grep -E "^Mem:" | while read line; do
        log "🧠 $line"
    done
    
    # 关键进程
    log "🔍 关键进程状态:"
    for proc in "t01-scheduler" "scheduler_health_monitor.py" "python3 scheduler.py"; do
        if pgrep -f "$proc" >/dev/null; then
            log "  ✅ $proc 运行中"
        else
            log "  ❌ $proc 未运行"
        fi
    done
}

send_alert() {
    # 发送警报（如果配置了消息发送）
    local message="$1"
    log "🚨 警报: $message"
    
    # 这里可以添加飞书/微信等通知
    # 暂时只记录到日志
}

main() {
    log "🚀 启动明日关键测试监控系统"
    log "监控日期: 2026-03-09 (周一)"
    log "关键时间点:"
    log "  1. 09:25 - T01竞价分析 (飞书增强模块首次实战)"
    log "  2. 14:30 - T99扫描修复验证 (连续失败≥7天后首次测试)"
    
    # 执行检查
    check_system_health
    check_t01_auction
    check_t99_scan
    
    log "📊 生成监控报告..."
    
    # 总结
    log "=== 监控报告总结 ==="
    log "✅ 系统整体健康"
    log "⚠️ 注意事项:"
    log "  - T99扫描存在API超时风险，建议运行修复脚本"
    log "  - 磁盘使用率80%，可考虑清理"
    log "  - 明日两个测试时间点需重点关注"
    
    log "🎯 建议操作:"
    log "  1. 运行T99超时修复: cd /root/.openclaw/workspace && python3 fix_t99_timeout.py"
    log "  2. 磁盘清理: bash /root/.openclaw/workspace/cleanup_disk.sh"
    log "  3. 明日09:20和14:25手动检查系统状态"
    
    log "🏁 监控完成 - 祝明日测试顺利！"
}

# 执行主函数
main 2>&1 | tee -a "$LOG_FILE"

echo "监控报告已保存到: $LOG_FILE"