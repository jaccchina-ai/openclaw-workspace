#!/bin/bash
# Git pre-commit hook示例 - 自动同步Task Registry

echo "🔍 检查Task Registry同步状态..."

cd /root/.openclaw/workspace

# 运行同步检查
python3 sync_registry.py check

# 询问是否执行同步
read -p "是否同步Registry? (y/n): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python3 sync_registry.py sync
    echo "✅ Registry已同步"
else
    echo "⏭️  跳过同步"
fi

exit 0