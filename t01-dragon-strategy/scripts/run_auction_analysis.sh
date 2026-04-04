#!/bin/bash
# T+1竞价分析脚本 - 次日9:25运行

set -e

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

# 加载环境变量
if [ -f "$PROJECT_DIR/.env" ]; then
    source "$PROJECT_DIR/.env"
fi

# 检查必要的环境变量
if [ -z "$TUSHARE_TOKEN" ]; then
    echo "错误: 未设置 TUSHARE_TOKEN 环境变量"
    exit 1
fi

# 获取当前日期
DATE=$(date +%Y%m%d)

# 创建日志目录
mkdir -p "$PROJECT_DIR/logs"

# 运行T+1竞价分析
cd "$PROJECT_DIR"
python3 main.py --mode t1_auction --date "$DATE" >> "$PROJECT_DIR/logs/t1_auction.log" 2>&1

echo "T+1竞价分析完成: $DATE"
