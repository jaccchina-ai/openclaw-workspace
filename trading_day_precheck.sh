#!/bin/bash
# 交易日准备检查清单
# 在交易日早上自动运行，确保所有交易系统就绪

set -e

LOG_FILE="/root/.openclaw/workspace/logs/trading_day_precheck.log"
CHECK_DATE=$(date '+%Y-%m-%d %H:%M:%S')
BEIJING_TIME=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo "[$CHECK_DATE] $1" | tee -a "$LOG_FILE"
}

# 检查磁盘空间
check_disk_space() {
    local usage=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    local available=$(df -h / | awk 'NR==2 {print $4}')
    
    log "📊 磁盘检查: 使用率 $usage%, 可用 $available"
    
    if [ "$usage" -gt 85 ]; then
        log "⚠️  磁盘使用率超过85%，建议清理"
        return 1
    elif [ "$usage" -gt 75 ]; then
        log "📈 磁盘使用率超过75%，需监控"
        return 2
    else
        log "✅ 磁盘空间健康"
        return 0
    fi
}

# 检查T01调度器状态
check_t01_scheduler() {
    if systemctl is-active --quiet t01-scheduler; then
        local pid=$(systemctl show t01-scheduler -p MainPID --value)
        local status=$(systemctl status t01-scheduler --no-pager -l | grep -o "Active:.*since" | sed 's/Active: //' | sed 's/ since//')
        log "✅ T01调度器运行中 (PID: $pid, 状态: $status)"
        return 0
    else
        log "❌ T01调度器未运行"
        return 1
    fi
}

# 检查交易日判断
check_trading_day() {
    local today=$(date '+%Y%m%d')
    local calendar_file="/root/.openclaw/workspace/trading_calendar.json"
    
    if [ -f "$calendar_file" ]; then
        local is_trading=$(python3 -c "
import json, sys
try:
    with open('$calendar_file', 'r') as f:
        cal = json.load(f)
    trading_days = cal.get('2026', {}).get('trading_days', [])
    holidays = cal.get('2026', {}).get('holidays', [])
    date_str = '$today'
    if len(date_str) == 8:
        formatted = f'{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}'
    else:
        formatted = date_str
    if formatted in trading_days and formatted not in holidays:
        print('TRADING_DAY')
    else:
        print('NON_TRADING_DAY')
except Exception as e:
    print(f'ERROR: {e}')
" 2>/dev/null)
        
        if [ "$is_trading" = "TRADING_DAY" ]; then
            log "✅ 今日为交易日 ($today)"
            return 0
        elif [ "$is_trading" = "NON_TRADING_DAY" ]; then
            log "📅 今日为非交易日 ($today)"
            return 2
        else
            log "⚠️  交易日历检查失败: $is_trading"
            return 1
        fi
    else
        log "❌ 交易日历文件不存在: $calendar_file"
        return 1
    fi
}

# 检查T99扫描功能
check_t99_scan() {
    local scan_dir="/root/.openclaw/workspace/skills/a-share-short-decision"
    
    if [ -d "$scan_dir" ]; then
        # 检查核心模块导入
        local import_test=$(cd "$scan_dir" && python3 -c "
try:
    from tools.market_data import is_trading_day_local
    from tools.fusion_engine import short_term_signal_engine
    print('IMPORT_OK')
except Exception as e:
    print(f'IMPORT_ERROR: {e}')
" 2>/dev/null)
        
        if [ "$import_test" = "IMPORT_OK" ]; then
            log "✅ T99扫描模块导入正常"
            return 0
        else
            log "❌ T99扫描模块导入失败: $import_test"
            return 1
        fi
    else
        log "❌ T99扫描目录不存在: $scan_dir"
        return 1
    fi
}

# 检查T100宏观监控
check_t100_monitor() {
    local monitor_dir="/root/.openclaw/workspace/skills/macro-monitor"
    
    if [ -d "$monitor_dir" ]; then
        if [ -f "$monitor_dir/run_monitor.py" ]; then
            # 检查Python环境
            local py_check=$(cd "$monitor_dir" && python3 -c "
import sys, os
try:
    import json, datetime, subprocess
    print('ENV_OK')
except Exception as e:
    print(f'ENV_ERROR: {e}')
" 2>/dev/null)
            
            if [ "$py_check" = "ENV_OK" ]; then
                log "✅ T100宏观监控环境正常"
                return 0
            else
                log "⚠️  T100环境检查失败: $py_check"
                return 1
            fi
        else
            log "❌ T100监控脚本不存在: $monitor_dir/run_monitor.py"
            return 1
        fi
    else
        log "❌ T100监控目录不存在: $monitor_dir"
        return 1
    fi
}

# 检查API连接性
check_api_connectivity() {
    log "🌐 检查API连接性..."
    
    # 检查Tushare连接
    local tushare_test=$(python3 -c "
try:
    import tushare as ts
    ts.set_token('870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab')
    pro = ts.pro_api()
    # 简单API调用测试
    cal = pro.trade_cal(exchange='SSE', start_date='20260301', end_date='20260301', timeout=5)
    print('TUSHARE_OK')
except Exception as e:
    print(f'TUSHARE_ERROR: {e}')
" 2>/dev/null)
    
    if [[ "$tushare_test" == TUSHARE_OK* ]]; then
        log "✅ Tushare API连接正常"
        tushare_ok=0
    else
        log "⚠️  Tushare API连接问题: $tushare_test"
        tushare_ok=1
    fi
    
    # 检查AKShare连接
    local akshare_test=$(python3 -c "
try:
    import akshare as ak
    # 简单测试
    import pandas as pd
    print('AKSHARE_OK')
except Exception as e:
    print(f'AKSHARE_ERROR: {e}')
" 2>/dev/null)
    
    if [[ "$akshare_test" == AKSHARE_OK* ]]; then
        log "✅ AKShare环境正常"
        akshare_ok=0
    else
        log "⚠️  AKShare环境问题: $akshare_test"
        akshare_ok=1
    fi
    
    return $((tushare_ok + akshare_ok))
}

# 检查飞书连接性
check_feishu_connectivity() {
    log "📱 检查飞书消息连接性..."
    
    # 使用飞书监控工具获取详细报告
    local monitor_result=$(cd /root/.openclaw/workspace && python3 feishu_monitor.py 2>&1)
    local exit_code=$?
    
    # 提取健康度评分
    local health_score=$(echo "$monitor_result" | grep -o "健康度评分: [0-9.]*/100" | grep -o "[0-9.]*" || echo "0")
    
    # 提取关键信息
    local success_rate=$(echo "$monitor_result" | grep -o "成功率: [0-9.]*%" | grep -o "[0-9.]*" || echo "0")
    local consecutive_failures=$(echo "$monitor_result" | grep -o "连续失败: [0-9]*" | grep -o "[0-9]*" || echo "0")
    local has_fallback=$(echo "$monitor_result" | grep -c "最近24小时有" || echo "0")
    
    # 记录详细结果
    log "📊 飞书健康度评分: $health_score/100"
    log "📈 消息成功率: $success_rate%"
    log "🔄 连续失败次数: $consecutive_failures"
    
    if [ "$has_fallback" -gt 0 ]; then
        local fallback_count=$(echo "$monitor_result" | grep -o "最近24小时有 [0-9]*" | grep -o "[0-9]*" || echo "0")
        log "⚠️  最近24小时有 $fallback_count 条fallback记录"
    else
        log "✅ 最近24小时无fallback记录"
    fi
    
    # 根据健康度评分返回状态
    if (( $(echo "$health_score >= 70" | bc -l 2>/dev/null || echo "0") )); then
        log "✅ 飞书消息系统健康"
        return 0
    elif (( $(echo "$health_score >= 50" | bc -l 2>/dev/null || echo "0") )); then
        log "⚠️  飞书消息系统状态一般，需要注意"
        return 1
    else
        log "❌ 飞书消息系统状态不佳，建议立即检查"
        # 显示建议
        local suggestion=$(echo "$monitor_result" | grep -A2 "## 🔧 行动建议" | tail -1)
        if [ -n "$suggestion" ]; then
            log "💡 建议: $suggestion"
        fi
        return 2
    fi
}

# 生成总结报告
generate_summary() {
    local total_checks=6
    local passed_checks=0
    local warnings=0
    local errors=0
    
    # 统计检查结果（这里简化处理，实际应该从各函数返回值收集）
    log ""
    log "📋 === 交易日准备检查总结 ==="
    log "检查时间: $CHECK_DATE"
    log "北京时间: $BEIJING_TIME"
    log ""
    log "建议:"
    log "1. 如果今日为交易日，请确保:"
    log "   - T01调度器运行正常"
    log "   - 磁盘空间充足 (>15%可用)"
    log "   - API连接正常"
    log "   - 飞书消息系统健康 (健康度≥70分)"
    log "2. 今日关键时间点:"
    log "   - 09:25: T01竞价分析 (首次增强模块实战验证)"
    log "   - 14:30: T99复盘扫描 (本地交易日历修复验证)"
    log "   - 20:00: T01 T日评分"
    log "   - 22:00: T100宏观监控"
    log ""
    log "⚠️  注意: 此检查为预防性检查，不保证交易时段100%无故障"
    log "✅ 检查完成，结果已保存至: $LOG_FILE"
}

# 主函数
main() {
    log "🚀 启动交易日准备检查"
    log "检查时间: $CHECK_DATE"
    log "北京时间: $BEIJING_TIME"
    log ""
    
    # 执行各项检查
    check_disk_space
    disk_result=$?
    
    check_t01_scheduler
    t01_result=$?
    
    check_trading_day
    trading_result=$?
    
    check_t99_scan
    t99_result=$?
    
    check_t100_monitor
    t100_result=$?
    
    check_api_connectivity
    api_result=$?
    
    check_feishu_connectivity
    feishu_result=$?
    
    # 生成报告
    generate_summary
    
    # 返回整体状态
    local overall=$((disk_result + t01_result + trading_result + t99_result + t100_result + api_result + feishu_result))
    
    if [ $overall -eq 0 ]; then
        log "✅ 所有检查通过，系统准备就绪"
        exit 0
    elif [ $overall -le 3 ]; then
        log "⚠️  部分检查有警告，系统基本可用"
        exit 1
    else
        log "❌ 多个检查失败，需要立即处理"
        exit 2
    fi
}

# 捕获信号
trap 'log "检查被中断"; exit 3' INT TERM

# 运行主函数
main "$@"