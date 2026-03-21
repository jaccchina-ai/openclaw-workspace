#!/bin/bash
# Daily Memory Backup Script
# 在每天 OpenClaw refresh session 之前，将今天的关键进展写入记忆文件
# 运行时间: 每天 03:30 (北京时间) = 每天 refresh session 前 30 分钟

WORKSPACE="/root/.openclaw/workspace"
MEMORY_DIR="$WORKSPACE/memory"
DATE=$(TZ='Asia/Shanghai' date '+%Y-%m-%d')
DATETIME=$(TZ='Asia/Shanghai' date '+%Y-%m-%d %H:%M:%S')
LOG_FILE="$WORKSPACE/logs/daily_memory_backup.log"

# 确保日志目录存在
mkdir -p "$WORKSPACE/logs"
mkdir -p "$MEMORY_DIR"

echo "=== Daily Memory Backup Started at $DATETIME ===" >> "$LOG_FILE"

# 创建/追加记忆文件
MEMORY_FILE="$MEMORY_DIR/${DATE}.md"

# 如果文件不存在，创建标题
if [ ! -f "$MEMORY_FILE" ]; then
    echo "# ${DATE} 工作记录" > "$MEMORY_FILE"
    echo "" >> "$MEMORY_FILE"
    echo "## 📝 关键进展摘要" >> "$MEMORY_FILE"
    echo "" >> "$MEMORY_FILE"
    echo "*备份时间: ${DATETIME}*" >> "$MEMORY_FILE"
    echo "" >> "$MEMORY_FILE"
fi

# 收集今天的关键信息
echo "" >> "$MEMORY_FILE"
echo "### 📊 T01系统状态 ($(TZ='Asia/Shanghai' date '+%H:%M'))" >> "$MEMORY_FILE"
echo "" >> "$MEMORY_FILE"

# 检查T01调度器状态
if pgrep -f "scheduler.py" > /dev/null; then
    SCHEDULER_PID=$(pgrep -f "scheduler.py" | head -1)
    echo "- **T01调度器**: ✅ 运行中 (PID: $SCHEDULER_PID)" >> "$MEMORY_FILE"
else
    echo "- **T01调度器**: ❌ 未运行" >> "$MEMORY_FILE"
fi

# 检查今天的候选股文件
TODAY=$(TZ='Asia/Shanghai' date '+%Y%m%d')
CANDIDATE_FILE="$WORKSPACE/tasks/T01/state/candidates_${TODAY}_to_*.json"
if ls $CANDIDATE_FILE 1> /dev/null 2>&1; then
    CANDIDATE_COUNT=$(ls $CANDIDATE_FILE 2>/dev/null | wc -l)
    echo "- **今日候选股**: ✅ 已生成 ($CANDIDATE_COUNT 个文件)" >> "$MEMORY_FILE"
else
    echo "- **今日候选股**: ⏳ 待生成" >> "$MEMORY_FILE"
fi

# 检查最近的消息发送状态
if [ -f "$WORKSPACE/logs/feishu_fallback.log" ]; then
    TODAY_ERRORS=$(grep -c "$(TZ='Asia/Shanghai' date '+%Y-%m-%d')" "$WORKSPACE/logs/feishu_fallback.log" 2>/dev/null || echo "0")
    if [ "$TODAY_ERRORS" -gt 0 ]; then
        echo "- **消息发送**: ⚠️ 今日有 $TODAY_ERRORS 条fallback记录" >> "$MEMORY_FILE"
    else
        echo "- **消息发送**: ✅ 今日正常" >> "$MEMORY_FILE"
    fi
else
    echo "- **消息发送**: ✅ 无错误记录" >> "$MEMORY_FILE"
fi

# 检查系统资源
echo "" >> "$MEMORY_FILE"
echo "### 💻 系统状态" >> "$MEMORY_FILE"
echo "" >> "$MEMORY_FILE"

# 内存使用情况
MEMORY_INFO=$(free -h | grep "Mem:")
MEMORY_USED=$(echo $MEMORY_INFO | awk '{print $3}')
MEMORY_TOTAL=$(echo $MEMORY_INFO | awk '{print $2}')
echo "- **内存使用**: $MEMORY_USED / $MEMORY_TOTAL" >> "$MEMORY_FILE"

# 磁盘使用情况
DISK_USAGE=$(df -h / | tail -1 | awk '{print $5}')
echo "- **磁盘使用**: $DISK_USAGE" >> "$MEMORY_FILE"

# 添加待办事项区域（供明天使用）
echo "" >> "$MEMORY_FILE"
echo "### 📋 明日待办" >> "$MEMORY_FILE"
echo "" >> "$MEMORY_FILE"
echo "- [ ] 检查09:25竞价分析执行" >> "$MEMORY_FILE"
echo "- [ ] 检查20:00 T日评分执行" >> "$MEMORY_FILE"
echo "- [ ] 验证飞书消息发送状态" >> "$MEMORY_FILE"

echo "✅ 记忆备份完成: $MEMORY_FILE" >> "$LOG_FILE"
echo "=== Backup Completed ===" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
