#!/bin/bash
# T99实时测试监控仪表板
# 监控14:30 T99扫描修复验证测试

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志文件
LOG_FILE="/root/.openclaw/workspace/logs/t99_realtime_monitor_$(date +%Y%m%d_%H%M%S).log"
exec > >(tee -a "$LOG_FILE") 2>&1

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   T99实时测试监控仪表板${NC}"
echo -e "${BLUE}   测试时间: 2026-03-09 14:30 (北京时间)${NC}"
echo -e "${BLUE}   当前时间: $(date)${NC}"
echo -e "${BLUE}========================================${NC}"

# 第一阶段：预测试健康检查 (测试前60分钟)
echo -e "\n${YELLOW}=== 第一阶段：预测试健康检查 ===${NC}"

# 1. 系统资源检查
echo -e "\n${BLUE}1. 系统资源检查${NC}"
DISK_USAGE=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
MEM_USAGE=$(free | grep Mem | awk '{printf "%.1f", $3/$2 * 100}')
echo "   磁盘使用率: ${DISK_USAGE}% $( [ $DISK_USAGE -lt 80 ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}" )"
echo "   内存使用率: ${MEM_USAGE}% $( [ $(echo "$MEM_USAGE < 90" | bc) -eq 1 ] && echo -e "${GREEN}✓${NC}" || echo -e "${RED}✗${NC}" )"

# 2. T99扫描脚本检查
echo -e "\n${BLUE}2. T99扫描脚本检查${NC}"
SCAN_SCRIPT="/root/.openclaw/workspace/skills/a-share-short-decision/run_scan_fixed.sh"
if [ -f "$SCAN_SCRIPT" ] && [ -x "$SCAN_SCRIPT" ]; then
    echo -e "   扫描脚本: ${GREEN}✓ 存在且可执行${NC}"
    echo "   脚本大小: $(wc -l < "$SCAN_SCRIPT") 行"
    echo "   最后修改: $(stat -c %y "$SCAN_SCRIPT" | cut -d'.' -f1)"
else
    echo -e "   扫描脚本: ${RED}✗ 缺失或不可执行${NC}"
fi

# 3. 交易日历检查
echo -e "\n${BLUE}3. 交易日历检查${NC}"
TRADING_CAL="/root/.openclaw/workspace/trading_calendar.json"
if [ -f "$TRADING_CAL" ]; then
    TODAY=$(date +%Y-%m-%d)
    if grep -q "\"$TODAY\": true" "$TRADING_CAL"; then
        echo -e "   今日($TODAY): ${GREEN}✓ 交易日${NC}"
    else
        echo -e "   今日($TODAY): ${RED}✗ 非交易日${NC}"
    fi
    echo "   日历文件: $(jq '. | length' "$TRADING_CAL" 2>/dev/null || echo '未知') 天数据"
else
    echo -e "   交易日历: ${RED}✗ 文件不存在${NC}"
fi

# 4. API连接测试（有限测试，避免触发限制）
echo -e "\n${BLUE}4. API连接快速测试${NC}"
echo "   运行模块导入测试..."
cd /root/.openclaw/workspace/skills/a-share-short-decision
timeout 10 python3 -c "
import sys
sys.path.insert(0, '.')
try:
    from tools.fusion_engine import short_term_signal_engine
    print('   引擎导入: ${GREEN}✓ 成功${NC}')
except Exception as e:
    print(f'   引擎导入: ${RED}✗ 失败: {str(e)[:50]}${NC}')
" 2>&1 | tail -2

# 5. 超时机制验证
echo -e "\n${BLUE}5. 超时机制验证${NC}"
if grep -q "MAIN_TIMEOUT=600" "$SCAN_SCRIPT"; then
    echo -e "   主超时设置: ${GREEN}✓ 600秒${NC}"
else
    echo -e "   主超时设置: ${RED}✗ 未找到或值不同${NC}"
fi

# 第二阶段：测试执行监控（需要手动触发或等待cron）
echo -e "\n${YELLOW}=== 第二阶段：测试执行监控 ===${NC}"
echo "   监控将在14:25启动（测试前5分钟）"
echo "   将监控以下指标："
echo "   - 扫描进程启动状态"
echo "   - 实时执行日志"
echo "   - 超时警告（>300秒）"
echo "   - 退出代码分析"

# 第三阶段：结果分析框架
echo -e "\n${YELLOW}=== 第三阶段：结果分析框架 ===${NC}"
echo "   测试完成后将分析："
echo "   1. 扫描退出代码"
echo "   2. 日志关键错误信息"
echo "   3. 执行时间分析"
echo "   4. 修复效果评估"
echo "   5. 改进建议"

# 第四阶段：自动修复建议
echo -e "\n${YELLOW}=== 第四阶段：自动修复建议 ===${NC}"
echo "   基于测试结果提供："
echo "   - 成功: 验证报告和持续监控建议"
echo "   - 失败: 根本原因分析和一键修复脚本"
echo "   - 超时: 超时设置优化建议"

# 监控计划
echo -e "\n${BLUE}=== 监控计划 ===${NC}"
echo "   14:25 - 启动实时监控"
echo "   14:30 - 测试开始执行"
echo "   14:35 - 检查进程状态"
echo "   14:40 - 中期健康检查"
echo "   15:20 - 最终结果分析（600秒超时）"

# 健康状态总结
echo -e "\n${GREEN}=== 预测试健康状态总结 ===${NC}"
HEALTH_COUNT=0
TOTAL_CHECKS=5

[ $DISK_USAGE -lt 80 ] && ((HEALTH_COUNT++))
[ $(echo "$MEM_USAGE < 90" | bc) -eq 1 ] && ((HEALTH_COUNT++))
[ -f "$SCAN_SCRIPT" ] && [ -x "$SCAN_SCRIPT" ] && ((HEALTH_COUNT++))
[ -f "$TRADING_CAL" ] && ((HEALTH_COUNT++))
# 最后一个检查（API）比较难自动化评估，暂时跳过

HEALTH_SCORE=$((HEALTH_COUNT * 100 / TOTAL_CHECKS))
echo -e "   健康度: ${HEALTH_SCORE}% (${HEALTH_COUNT}/${TOTAL_CHECKS})"

if [ $HEALTH_SCORE -ge 80 ]; then
    echo -e "   ${GREEN}✅ 系统准备就绪，T99测试有望成功${NC}"
elif [ $HEALTH_SCORE -ge 60 ]; then
    echo -e "   ${YELLOW}⚠️ 系统基本就绪，但存在风险${NC}"
else
    echo -e "   ${RED}❌ 系统健康度不足，测试可能失败${NC}"
fi

echo -e "\n${BLUE}=== 后续操作 ===${NC}"
echo "   1. 在14:25运行此脚本查看实时监控"
echo "   2. 或运行: bash /root/.openclaw/workspace/t99_realtime_monitor.sh"
echo "   3. 测试结果将保存到: $LOG_FILE"

echo -e "\n${BLUE}========================================${NC}"
echo -e "${BLUE}   监控仪表板生成完成${NC}"
echo -e "${BLUE}   祝测试顺利！${NC}"
echo -e "${BLUE}========================================${NC}"