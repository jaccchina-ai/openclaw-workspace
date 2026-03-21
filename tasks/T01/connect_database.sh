#!/bin/bash
# T01 PostgreSQL + TimescaleDB 连接脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

DB_USER=${DB_USER:-t01_user}
DB_PASSWORD=${DB_PASSWORD:-t01_password}
DB_NAME=${DB_NAME:-t01_strategy}
DB_PORT=${DB_PORT:-5432}

# 如果有参数，执行命令
if [ $# -gt 0 ]; then
    docker-compose exec -T timescaledb psql -U "$DB_USER" -d "$DB_NAME" -c "$@"
else
    # 交互式连接
    echo "🔌 连接到 T01 PostgreSQL..."
    echo "  按 Ctrl+D 或输入 \\q 退出"
    echo ""
    docker-compose exec timescaledb psql -U "$DB_USER" -d "$DB_NAME"
fi
