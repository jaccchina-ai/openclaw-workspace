#!/bin/bash
# T01 竞价准备检查任务包装器脚本
# 用于cron环境执行，解决PATH变量扩展问题

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR" || exit 1

LOG_FILE="auction_preparation_check.log"
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')

echo "=== 竞价准备检查任务开始于 $TIMESTAMP ===" >> "$LOG_FILE"
echo "工作目录: $(pwd)" >> "$LOG_FILE"
echo "PATH: $PATH" >> "$LOG_FILE"

# 执行竞价准备检查任务
/usr/bin/python3 auction_preparation_check.py --always-send >> "$LOG_FILE" 2>&1
EXIT_CODE=$?

echo "=== 竞价准备检查任务完成，退出码: $EXIT_CODE ===" >> "$LOG_FILE"
exit $EXIT_CODE
