#!/bin/bash
# 任务监控脚本 - 检查T01、T99、T100状态

echo "=== 任务状态监控 $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
echo "当前时间: $(date)"
echo "时区: $(date +%Z)"
echo

# 1. T01龙头战法调度器状态
echo "🔧 T01龙头战法调度器:"
if ps aux | grep -q "[p]ython3.*scheduler.py"; then
    echo "  ✅ 运行中 (进程数: $(ps aux | grep -c '[p]ython3.*scheduler.py'))"
else
    echo "  ❌ 未运行"
fi

# 2. T99复盘扫描状态
echo "📊 T99复盘扫描:"
SCAN_LOG="/root/.openclaw/workspace/skills/a-share-short-decision/scan.log"
if [ -f "$SCAN_LOG" ]; then
    LAST_SCAN=$(tail -1 "$SCAN_LOG" 2>/dev/null | grep -o "Scan started at.*" || echo "无记录")
    if [ -n "$LAST_SCAN" ]; then
        echo "  📅 最后扫描: $LAST_SCAN"
    else
        echo "  📅 最后扫描: 日志文件中无开始记录"
    fi
    
    # 检查是否有超时记录
    if tail -20 "$SCAN_LOG" | grep -q "timeout.*s)\.\.\."; then
        echo "  ⚠️  检测到超时记录"
    fi
else
    echo "  ❌ 扫描日志不存在"
fi

# 3. T100宏观监控状态
echo "📈 T100宏观监控:"
MONITOR_LOG="/root/.openclaw/workspace/skills/macro-monitor/monitor.log"
if [ -f "$MONITOR_LOG" ]; then
    LAST_MODIFIED=$(stat -c %y "$MONITOR_LOG" 2>/dev/null | cut -d'.' -f1)
    echo "  📅 日志最后修改: $LAST_MODIFIED"
    
    # 检查最后报告状态
    if tail -10 "$MONITOR_LOG" | grep -q "测试模式：跳过飞书发送"; then
        echo "  ⚠️  最后执行: 测试模式 (报告未发送)"
    elif tail -10 "$MONITOR_LOG" | grep -q "✅ 报告成功发送到飞书群"; then
        echo "  ✅ 最后执行: 报告已发送"
    else
        echo "  🔄 最后执行状态: 未知"
    fi
else
    echo "  ❌ 监控日志不存在"
fi

# 4. Cron任务状态
echo "⏰ Cron任务配置:"
echo "  T99: $(crontab -l 2>/dev/null | grep 'T99' | wc -l) 个任务"
echo "  T100: $(crontab -l 2>/dev/null | grep 'macro-monitor' | wc -l) 个任务"

# 5. 系统资源
echo "💻 系统资源:"
echo "  内存: $(free -h | awk '/^Mem:/{print $3"/"$2" ("$7" available)"}')"
echo "  磁盘: $(df -h /root/.openclaw/workspace | awk 'NR==2{print $3"/"$2" ("$5" used)"}')"

echo
echo "=== 监控完成 ==="