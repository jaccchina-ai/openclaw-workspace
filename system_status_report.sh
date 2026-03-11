#!/bin/bash
# 系统状态报告 - 主动惊喜：一键查看所有任务状态

echo "=== 系统状态报告 ==="
echo "生成时间: $(date)"
echo ""

# T01状态
echo "🔹 T01 龙头战法选股系统"
echo "------------------------"
T01_PROCESSES=$(ps aux | grep -E "scheduler|python3.*T01" | grep -v grep | wc -l)
echo "运行进程: $T01_PROCESSES"
if [ $T01_PROCESSES -ge 3 ]; then
    echo "状态: ✅ 正常"
else
    echo "状态: ⚠️  异常（进程数不足）"
fi

# 检查健康监控器
HEALTH_MONITOR=$(ps aux | grep "health_monitor" | grep -v grep | wc -l)
echo "健康监控器: $HEALTH_MONITOR 进程"
echo ""

# T99状态
echo "🔹 T99 复盘扫描任务"
echo "------------------------"
T99_LOG="/root/.openclaw/workspace/skills/a-share-short-decision/scan.log"
if [ -f "$T99_LOG" ]; then
    LAST_SCAN=$(tail -5 "$T99_LOG" | grep "=== Scan started at" | tail -1 | cut -d'=' -f3- | xargs || echo "未知")
    echo "上次扫描: $LAST_SCAN"
else
    echo "上次扫描: 日志文件不存在"
fi

# 交易日检查
echo -n "交易日检查: "
cd /root/.openclaw/workspace/skills/a-share-short-decision && python3 -c "
import sys
import tushare as ts
import pandas as pd
from datetime import datetime
try:
    ts.set_token('870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab')
    pro = ts.pro_api()
    today = datetime.now().strftime('%Y%m%d')
    cal = pro.trade_cal(exchange='SSE', start_date='20260201', end_date='20260310')
    today_cal = cal[cal['cal_date'] == today]
    if not today_cal.empty:
        is_open = int(today_cal.iloc[0]['is_open'])
        print('交易日' if is_open == 1 else '非交易日')
    else:
        print('检查失败')
except Exception as e:
    print('API错误')
" 2>/dev/null
echo ""

# T100状态
echo "🔹 T100 宏观监控任务"
echo "------------------------"
T100_LOG="/root/.openclaw/workspace/skills/macro-monitor/monitor.log"
if [ -f "$T100_LOG" ]; then
    LAST_RUN=$(stat -c %y "$T100_LOG" 2>/dev/null | cut -d' ' -f1,2 || echo "未知")
    echo "最后执行: $LAST_RUN"
    
    # 检查最后发送状态
    SEND_STATUS=$(tail -20 "$T100_LOG" | grep -E "✅ 报告成功发送|❌ 发送报告失败|测试模式" | tail -1 || echo "未知")
    echo "发送状态: $SEND_STATUS"
else
    echo "最后执行: 日志文件不存在"
fi

# 检查cron配置
echo -n "Cron配置: "
crontab -l 2>/dev/null | grep -q "PATH=/root/.nvm/versions/node/v22.22.0/bin" && echo "✅ 已修复（含Node.js路径）" || echo "⚠️  未修复"

# 下次执行时间
echo "下次执行: 今日22:00 (北京时间)"
echo ""

# 错误状态
echo "🔹 系统错误状态"
echo "------------------------"
ERRORS_FILE="/root/.openclaw/workspace/.learnings/ERRORS.md"
if [ -f "$ERRORS_FILE" ]; then
    IN_PROGRESS=$(grep -c "Status.*in_progress" "$ERRORS_FILE" || echo 0)
    PENDING=$(grep -c "Status.*pending" "$ERRORS_FILE" || echo 0)
    echo "进行中错误: $IN_PROGRESS"
    echo "待处理错误: $PENDING"
    
    if [ $IN_PROGRESS -gt 0 ]; then
        echo "待验证修复:"
        grep -B5 "Status.*in_progress" "$ERRORS_FILE" | grep "^\#" | head -2
    fi
else
    echo "错误文件不存在"
fi

echo ""
echo "=== 建议操作 ==="
echo "1. 今晚22:00后运行: /root/.openclaw/workspace/monitor_t100.sh"
echo "2. 周一14:30监控T99扫描执行"
echo "3. 查看详细日志获取更多信息"