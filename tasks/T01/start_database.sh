#!/bin/bash
# T01 PostgreSQL + TimescaleDB 启动脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 加载环境变量
if [ -f .env ]; then
    export $(cat .env | grep -v '^#' | xargs)
fi

# 创建备份目录
mkdir -p backups
mkdir -p logs

echo "🚀 启动 T01 PostgreSQL + TimescaleDB..."

# 检查 Docker 是否运行
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker 未运行，请先启动 Docker"
    exit 1
fi

# 启动容器
docker-compose up -d timescaledb

# 等待数据库就绪
echo "⏳ 等待数据库启动..."
for i in {1..30}; do
    if docker-compose exec -T timescaledb pg_isready -U ${DB_USER:-t01_user} -d ${DB_NAME:-t01_strategy} > /dev/null 2>&1; then
        echo "✅ 数据库已就绪"
        break
    fi
    echo "  等待中... ($i/30)"
    sleep 2
done

# 验证 TimescaleDB 扩展
echo "🔍 验证 TimescaleDB 扩展..."
docker-compose exec -T timescaledb psql -U ${DB_USER:-t01_user} -d ${DB_NAME:-t01_strategy} -c "
SELECT extname, extversion 
FROM pg_extension 
WHERE extname = 'timescaledb';
" | grep -q timescaledb && echo "✅ TimescaleDB 扩展已加载" || echo "⚠️ TimescaleDB 扩展未找到"

# 显示连接信息
echo ""
echo "📊 数据库连接信息:"
echo "  主机: localhost"
echo "  端口: ${DB_PORT:-5432}"
echo "  数据库: ${DB_NAME:-t01_strategy}"
echo "  用户: ${DB_USER:-t01_user}"
echo "  密码: ${DB_PASSWORD:-t01_password}"
echo ""
echo "🔌 连接命令:"
echo "  ./connect_database.sh"
echo ""
echo "📈 查看表结构:"
echo "  ./connect_database.sh -c '\\dt'"
echo ""
