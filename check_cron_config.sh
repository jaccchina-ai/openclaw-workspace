#!/bin/bash
# 检查cron配置和T100环境变量问题
# 主动惊喜：确保明日T100报告正常发送

echo "🔧 T100配置检查脚本"
echo "===================="
date

echo -e "\n1. 检查cron任务:"
crontab -l 2>/dev/null | grep -E "(T100|macro-monitor)" | head -5

echo -e "\n2. 检查TEST_MODE环境变量:"
echo "当前环境变量 TEST_MODE=$TEST_MODE"
echo "建议: 确保TEST_MODE未设置，以便报告正常发送"

echo -e "\n3. 检查OpenClaw路径:"
OPENCLAW_PATH="/root/.nvm/versions/node/v22.22.0/bin/openclaw"
if [ -f "$OPENCLAW_PATH" ]; then
    echo "✅ OpenClaw路径存在: $OPENCLAW_PATH"
else
    echo "❌ OpenClaw路径不存在: $OPENCLAW_PATH"
fi

echo -e "\n4. 检查T100数据目录:"
DATA_DIR="/root/.openclaw/workspace/skills/macro-monitor/data"
if [ -d "$DATA_DIR" ]; then
    echo "✅ T100数据目录存在"
    echo "   最新数据文件:"
    ls -la "$DATA_DIR"/*_2026-02-26.json 2>/dev/null | head -3
else
    echo "❌ T100数据目录不存在: $DATA_DIR"
fi

echo -e "\n5. 检查宏观监控脚本:"
MONITOR_SCRIPT="/root/.openclaw/workspace/skills/macro-monitor/run_monitor.py"
if [ -f "$MONITOR_SCRIPT" ]; then
    echo "✅ 宏观监控脚本存在"
    # 检查TEST_MODE相关代码
    if grep -q "TEST_MODE" "$MONITOR_SCRIPT"; then
        echo "   脚本中包含TEST_MODE检查"
    fi
else
    echo "❌ 宏观监控脚本不存在: $MONITOR_SCRIPT"
fi

echo -e "\n6. 建议修复措施:"
echo "如果明日T100报告可能失败，建议:"
echo "  a) 清除TEST_MODE环境变量: unset TEST_MODE"
echo "  b) 测试手动发送: cd /root/.openclaw/workspace/skills/macro-monitor && python3 run_monitor.py"
echo "  c) 检查cron环境: 确保cron任务没有设置TEST_MODE=1"

echo -e "\n✅ 检查完成。明日22:00前建议验证配置。"