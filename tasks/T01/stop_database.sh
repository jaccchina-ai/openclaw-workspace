#!/bin/bash
# T01 PostgreSQL + TimescaleDB 停止脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "🛑 停止 T01 PostgreSQL + TimescaleDB..."

docker-compose down

echo "✅ 数据库已停止"
