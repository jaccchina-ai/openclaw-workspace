#!/bin/bash
# 情绪指标预警系统 - 定时运行脚本
# 建议运行时间: 交易日 09:35, 14:55 (收盘前)

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 日志文件
LOG_FILE="./logs/sentiment_monitor.log"
mkdir -p ./logs

# Python 路径
PYTHON="${PYTHON:-python3}"

echo "$(date '+%Y-%m-%d %H:%M:%S') - 启动情绪指标监控..." >> "$LOG_FILE"

# 运行情绪分析
$PYTHON sentiment_monitor.py --alert --config ./config.yaml 2>&1 | tee -a "$LOG_FILE"

EXIT_CODE=${PIPESTATUS[0]}

if [ $EXIT_CODE -eq 0 ]; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 情绪监控完成" >> "$LOG_FILE"
else
    echo "$(date '+%Y-%m-%d %H:%M:%S') - 情绪监控失败 (exit code: $EXIT_CODE)" >> "$LOG_FILE"
fi

echo "---" >> "$LOG_FILE"

exit $EXIT_CODE
