#!/bin/bash
# 交易日监控脚本 - 2026-03-02 (周一)
# 监控T01/T99/T100任务执行状态

echo "=== 交易日监控脚本 ==="
echo "执行时间: $(date '+%Y-%m-%d %H:%M:%S %Z')"
echo "北京时间: $(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')"
echo ""

# 1. 系统状态检查
echo "## 1. 系统状态检查"
echo "当前用户: $(whoami)"
echo "工作目录: $(pwd)"
echo ""

# 2. T01调度器状态
echo "## 2. T01龙头战法调度器状态"
if systemctl is-active --quiet t01-scheduler; then
    echo "✅ T01调度器: 运行中"
    echo "    PID: $(systemctl show t01-scheduler -p MainPID --value)"
    echo "    运行时间: $(systemctl show t01-scheduler -p ActiveEnterTimestamp --value | cut -d' ' -f2-5)"
else
    echo "❌ T01调度器: 未运行"
fi
echo ""

# 3. T99扫描引擎状态
echo "## 3. T99复盘扫描引擎状态"
T99_DIR="/root/.openclaw/workspace/skills/a-share-short-decision"
if [ -d "$T99_DIR" ]; then
    echo "✅ T99目录存在: $T99_DIR"
    # 检查扫描脚本
    if [ -f "$T99_DIR/run_scan.sh" ]; then
        echo "✅ 扫描脚本存在: run_scan.sh"
    else
        echo "❌ 扫描脚本不存在"
    fi
    # 检查日志
    if [ -f "$T99_DIR/scan.log" ]; then
        echo "📊 扫描日志大小: $(wc -l < $T99_DIR/scan.log) 行"
        echo "   最后记录: $(tail -1 $T99_DIR/scan.log 2>/dev/null | cut -c1-100)"
    else
        echo "📝 扫描日志不存在 (首次运行)"
    fi
else
    echo "❌ T99目录不存在"
fi
echo ""

# 4. T100宏观监控状态
echo "## 4. T100宏观监控状态"
T100_DIR="/root/.openclaw/workspace/skills/macro-monitor"
if [ -d "$T100_DIR" ]; then
    echo "✅ T100目录存在: $T100_DIR"
    # 检查监控脚本
    if [ -f "$T100_DIR/run_monitor.py" ]; then
        echo "✅ 监控脚本存在: run_monitor.py"
    else
        echo "❌ 监控脚本不存在"
    fi
    # 检查日志
    if [ -f "$T100_DIR/monitor.log" ]; then
        echo "📊 监控日志大小: $(wc -l < $T100_DIR/monitor.log) 行"
        echo "   最后发送: $(grep -i "成功\|失败\|sent" $T100_DIR/monitor.log | tail -1 2>/dev/null | cut -c1-100)"
    else
        echo "📝 监控日志不存在"
    fi
else
    echo "❌ T100目录不存在"
fi
echo ""

# 5. 今日执行时间表
echo "## 5. 今日执行时间表 (北京时间)"
echo "🕐 09:25-09:29 - T01竞价分析推送 (自动)"
echo "🕐 09:30后    - T01选股推荐推送 (自动)"  
echo "🕐 14:30      - T99复盘扫描 (交易日)"
echo "🕐 22:00      - T100宏观监控报告 (每日)"
echo ""

# 6. 关键服务检查
echo "## 6. 关键服务检查"
# OpenClaw网关
if pgrep -f "openclaw.*gateway" > /dev/null; then
    echo "✅ OpenClaw网关: 运行中"
else
    echo "❌ OpenClaw网关: 未运行"
fi

# Node.js
if which node > /dev/null; then
    echo "✅ Node.js: $(node --version)"
else
    echo "❌ Node.js: 未安装"
fi

# Python
echo "✅ Python: $(python3 --version 2>&1)"
echo ""

# 7. Cron任务检查
echo "## 7. Cron任务检查"
echo "当前用户cron:"
crontab -l 2>/dev/null | grep -E "(T99|T100|14:30|22:00)" || echo "   未找到相关cron任务"
echo ""

# 8. 建议操作
echo "## 8. 建议操作"
echo "1. 09:25前 - 手动检查T01调度器状态: systemctl status t01-scheduler"
echo "2. 14:30前 - 验证T99扫描脚本可执行: cd $T99_DIR && ls -la"
echo "3. 22:00前 - 检查T100环境变量: echo \$PATH | grep node"
echo "4. 如有问题 - 查看日志: /tmp/openclaw/openclaw-*.log"
echo ""

echo "=== 监控完成 ==="
echo "提示: 将此脚本加入cron定期执行，如每30分钟一次"
echo "cron示例: */30 * * * * /root/.openclaw/workspace/trading_day_monitor.sh >> /root/.openclaw/workspace/trading_monitor.log 2>&1"