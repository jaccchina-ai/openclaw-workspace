#!/bin/bash
# T01 PostgreSQL + TimescaleDB 完整部署脚本

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=============================================="
echo "T01 PostgreSQL + TimescaleDB 部署脚本"
echo "=============================================="
echo ""

# 检查 Docker
if ! command -v docker &> /dev/null; then
    echo "❌ Docker 未安装，请先安装 Docker"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose 未安装，请先安装 Docker Compose"
    exit 1
fi

# 创建必要目录
echo "📁 创建必要目录..."
mkdir -p init
mkdir -p backups
mkdir -p logs
mkdir -p data

# 设置脚本权限
echo "🔧 设置脚本权限..."
chmod +x start_database.sh
chmod +x stop_database.sh
chmod +x connect_database.sh

# 启动数据库
echo ""
echo "🚀 启动 PostgreSQL + TimescaleDB..."
docker-compose up -d timescaledb

# 等待数据库就绪
echo ""
echo "⏳ 等待数据库启动（最多60秒）..."
for i in {1..30}; do
    if docker-compose exec -T timescaledb pg_isready -U t01_user -d t01_strategy > /dev/null 2>&1; then
        echo "✅ 数据库已就绪"
        break
    fi
    echo "  等待中... ($i/30)"
    sleep 2
done

# 验证数据库
echo ""
echo "🔍 验证数据库..."

# 检查 TimescaleDB 扩展
echo "  - 检查 TimescaleDB 扩展..."
docker-compose exec -T timescaledb psql -U t01_user -d t01_strategy -c "
SELECT extname, extversion 
FROM pg_extension 
WHERE extname = 'timescaledb';
" | grep -q timescaledb && echo "    ✅ TimescaleDB 扩展已加载" || echo "    ⚠️ TimescaleDB 扩展未找到"

# 检查表结构
echo "  - 检查表结构..."
docker-compose exec -T timescaledb psql -U t01_user -d t01_strategy -c "\dt" | grep -q stock_recommendations && echo "    ✅ 主表已创建" || echo "    ⚠️ 主表未找到"

# 检查 Hypertable
echo "  - 检查 Hypertable..."
docker-compose exec -T timescaledb psql -U t01_user -d t01_strategy -c "
SELECT hypertable_name 
FROM timescaledb_information.hypertables 
WHERE hypertable_name = 'stock_recommendations';
" | grep -q stock_recommendations && echo "    ✅ Hypertable 已创建" || echo "    ⚠️ Hypertable 未找到"

# 检查连续聚合
echo "  - 检查连续聚合视图..."
docker-compose exec -T timescaledb psql -U t01_user -d t01_strategy -c "
SELECT view_name 
FROM timescaledb_information.continuous_aggregates 
WHERE view_name = 'daily_recommendation_stats';
" | grep -q daily_recommendation_stats && echo "    ✅ 连续聚合已创建" || echo "    ⚠️ 连续聚合未找到"

# 显示连接信息
echo ""
echo "=============================================="
echo "✅ 部署完成！"
echo "=============================================="
echo ""
echo "📊 数据库连接信息:"
echo "  主机: localhost"
echo "  端口: 5432"
echo "  数据库: t01_strategy"
echo "  用户: t01_user"
echo "  密码: t01_password"
echo ""
echo "🔌 连接命令:"
echo "  ./connect_database.sh"
echo ""
echo "🛑 停止命令:"
echo "  ./stop_database.sh"
echo ""
echo "📈 常用查询:"
echo "  ./connect_database.sh -c 'SELECT * FROM daily_recommendation_stats LIMIT 5;'"
echo ""
echo "🧪 运行测试:"
echo "  python3 test_postgres_storage.py"
echo ""
