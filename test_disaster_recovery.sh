#!/bin/bash
# 灾难恢复系统测试脚本
# 演示完整的版本更新和回退流程

set -e

echo "🚀 开始灾难恢复系统测试"
echo "=========================================="

# 1. 验证当前状态
echo "1. 验证当前T01版本..."
python3 verify_version.py --task T01 --version 1.2.0 --report

# 2. 模拟版本升级到v1.3.0
echo ""
echo "2. 模拟创建T01 v1.3.0..."
echo "当前版本: v1.2.0"
echo "假设我们开发了新功能，需要升级到v1.3.0"

# 备份当前配置文件
cp tasks/T01/config.yaml tasks/T01/config.yaml.backup

# 修改版本号为1.3.0（模拟升级）
echo "version: \"1.3.0\"" > tasks/T01/config.yaml.tmp
grep -v "version:" tasks/T01/config.yaml.backup >> tasks/T01/config.yaml.tmp
mv tasks/T01/config.yaml.tmp tasks/T01/config.yaml

echo "✅ T01已升级到v1.3.0（模拟）"

# 3. 验证新版本
echo ""
echo "3. 验证新版本v1.3.0..."
python3 verify_version.py --task T01 --version 1.3.0 --report

# 4. 创建v1.3.0快照
echo ""
echo "4. 为v1.3.0创建快照..."
python3 create_snapshot.py --task T01 --version 1.3.0 --message "测试版本：模拟新功能"

# 5. 演示发现问题，需要回退
echo ""
echo "5. 假设v1.3.0有问题，需要回退到v1.2.0..."
echo "准备执行灾难恢复..."

# 6. 检查回退目标版本是否存在
echo ""
echo "6. 检查v1.2.0快照是否存在..."
ls -la snapshots/snapshot_T01_v1.2.0_*.json

# 7. 执行回退（模拟）
echo ""
echo "7. 执行回退到v1.2.0（模拟命令）..."
echo "实际命令: python3 disaster_recovery.py --task T01 --version 1.2.0"
echo ""
echo "注：为避免实际执行，这里只展示命令"
echo "如果需要实际测试，请运行:"
echo "  python3 disaster_recovery.py --task T01 --version 1.2.0"
echo "然后输入 'YES' 确认"

# 8. 恢复原始配置
echo ""
echo "8. 恢复原始配置（模拟测试结束）..."
mv tasks/T01/config.yaml.backup tasks/T01/config.yaml
echo "✅ 配置已恢复为v1.2.0"

# 9. 最终验证
echo ""
echo "9. 最终验证..."
python3 verify_version.py --task T01 --version 1.2.0 --report

echo ""
echo "=========================================="
echo "✅ 灾难恢复系统测试完成"
echo ""
echo "📋 已测试的功能："
echo "  1. 版本验证工具"
echo "  2. 快照创建工具"
echo "  3. 灾难恢复流程演示"
echo ""
echo "🛡️ 实际回退操作："
echo "  如需测试实际回退，请运行："
echo "  python3 disaster_recovery.py --task T01 --version 1.2.0"