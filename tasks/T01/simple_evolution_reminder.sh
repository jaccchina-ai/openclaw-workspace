#!/bin/bash
# T01进化阶段简单提醒脚本

# 设置环境变量
export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"

# 当前日期
TODAY=$(date +%Y-%m-%d)
WEEKDAY=$(date +%u)  # 1=周一, 7=周日

# 判断阶段
if [[ "$TODAY" < "2026-03-14" ]]; then
    STAGE="第一阶段: 基础强化 (3月10-14日)"
    TASKS="1.验证PATH修复 2.集成成功标准 3.预警机制 4.MoA反思"
    DAYS_LEFT=$(( ($(date -d "2026-03-14" +%s) - $(date +%s)) / 86400 ))
elif [[ "$TODAY" < "2026-03-21" ]]; then
    STAGE="第二阶段: 因子系统升级 (3月17-21日)"
    TASKS="1.IC值监控 2.因子正交化 3.权重优化 4.Alpha Decay应对"
    DAYS_LEFT=$(( ($(date -d "2026-03-21" +%s) - $(date +%s)) / 86400 ))
elif [[ "$TODAY" < "2026-03-31" ]]; then
    STAGE="第三阶段: 全系统进化 (3月24-31日)"
    TASKS="1.Alpha因子挖掘 2.深度归因分析 3.自适应阈值 4.全自动闭环"
    DAYS_LEFT=$(( ($(date -d "2026-03-31" +%s) - $(date +%s)) / 86400 ))
else
    STAGE="已完成所有进化阶段"
    TASKS="系统维护与持续优化"
    DAYS_LEFT=0
fi

# 只在工作日发送提醒，避免周末打扰
if [[ $WEEKDAY -ge 1 && $WEEKDAY -le 5 ]]; then
    # 构建消息
    if [[ $DAYS_LEFT -le 2 && $DAYS_LEFT -ge 0 ]]; then
        # 阶段即将结束
        MESSAGE="🚨 **T01进化阶段即将结束提醒**

**阶段**: $STAGE
**剩余时间**: ${DAYS_LEFT}天

**待完成任务**:
$TASKS

**紧急程度**: ⚠️ 请确保按时完成，以免影响后续计划。

**建议**: 检查进度，必要时调整计划。"
    else
        # 日常提醒
        MESSAGE="📌 **T01进化状态提醒 ($TODAY)**

**当前阶段**: $STAGE
**剩余时间**: ${DAYS_LEFT}天

**主要任务**:
$TASKS

**状态**: 按计划推进中

**建议**: 保持节奏，有任何问题及时调整。"
    fi
    
    # 发送飞书消息
    /root/.nvm/versions/node/v22.22.0/bin/openclaw message send \
        --channel feishu \
        --target "user:ou_b8a256a9cb526db6c196cb438d6893a6" \
        --message "$MESSAGE"
    
    # 记录日志
    echo "$(date): 发送T01进化提醒 - $STAGE (剩余${DAYS_LEFT}天)" >> /root/.openclaw/workspace/tasks/T01/logs/evolution_reminder.log
else
    echo "$(date): 周末跳过提醒" >> /root/.openclaw/workspace/tasks/T01/logs/evolution_reminder.log
fi