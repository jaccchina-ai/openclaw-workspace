#!/bin/bash
# T01 T日评分任务包装器脚本
# 用于cron环境执行，解决PATH变量扩展问题

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

LOG_FILE="t01_daily_scoring.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "=== T日评分任务开始于 $TIMESTAMP ===" >> "$LOG_FILE"
echo "工作目录: $(pwd)" >> "$LOG_FILE"
echo "PATH: $PATH" >> "$LOG_FILE"

# 获取今日日期（北京时间）
TODAY=$(TZ='Asia/Shanghai' date '+%Y%m%d')
echo "使用日期: $TODAY" >> "$LOG_FILE"

# 执行T日评分任务（强制指定日期）
/usr/bin/python3 main.py t-day --date "$TODAY" >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "=== T日评分任务完成，退出码: $EXIT_CODE ===" >> "$LOG_FILE"
exit $EXIT_CODE
