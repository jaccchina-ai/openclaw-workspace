#!/bin/bash
# T日评分脚本 - 收盘后运行

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

# 运行T日评分
cd "$PROJECT_DIR"
python3 main.py --mode t_day --date "$DATE" >> "$PROJECT_DIR/logs/t_day_scoring.log" 2>&1

echo "T日评分完成: $DATE"
