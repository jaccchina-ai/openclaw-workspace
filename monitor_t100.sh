#!/bin/bash
# 监控T100宏观监控任务执行状态

LOG_FILE="/root/.openclaw/workspace/skills/macro-monitor/monitor.log"
CRON_TIME="22:00"

echo "=== T100 宏观监控任务监控脚本 ==="
echo "执行时间: $(date)"
echo "日志文件: $LOG_FILE"
echo "计划执行时间: 北京时间 $CRON_TIME"
echo ""

# 检查当前时间
BEIJING_TIME=$(TZ='Asia/Shanghai' date '+%H:%M')
echo "当前北京时间: $BEIJING_TIME"

# 如果还没到22:00，计算剩余时间
if [[ "$BEIJING_TIME" < "22:00" ]]; then
    # 计算剩余分钟
    current_hour=$(date -d "TZ=\"Asia/Shanghai\" $BEIJING_TIME" +%H)
    current_minute=$(date -d "TZ=\"Asia/Shanghai\" $BEIJING_TIME" +%M)
    remaining_minutes=$(( (22 - 10#$current_hour) * 60 - 10#$current_minute ))
    echo "距离执行还有: $remaining_minutes 分钟"
    echo "建议在 22:05 后再次运行此脚本检查结果"
else
    # 已经过了22:00，检查日志
    echo "已过执行时间，检查日志..."
    echo ""
    
    # 检查日志最后50行
    echo "=== monitor.log 最后50行 ==="
    tail -50 "$LOG_FILE" 2>/dev/null || echo "日志文件不存在"
    
    echo ""
    echo "=== 关键错误检查 ==="
    tail -100 "$LOG_FILE" 2>/dev/null | grep -i "error\|fail\|❌\|失败" || echo "未发现错误信息"
    
    echo ""
    echo "=== 发送状态检查 ==="
    tail -100 "$LOG_FILE" 2>/dev/null | grep -i "成功\|✅\|成功发送\|发送成功" || echo "未发现成功发送信息"
    
    # 检查进程状态
    echo ""
    echo "=== 进程状态检查 ==="
    ps aux | grep -E "(python.*run_monitor|macro-monitor)" | grep -v grep || echo "无相关进程"
fi

echo ""
echo "=== cron配置检查 ==="
crontab -l | grep -A2 -B2 "T100" || echo "未找到T100 cron配置"

echo ""
echo "=== 环境变量检查 ==="
echo "Node.js路径: $(which node 2>/dev/null || echo '未找到')"
echo "OpenClaw路径: $(which openclaw 2>/dev/null || echo '未找到')"
echo "Python路径: $(which python3 2>/dev/null || echo '未找到')"

echo ""
echo "监控完成"