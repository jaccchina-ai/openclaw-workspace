#!/bin/bash
# T01进化监控脚本包装器
# 确保环境变量正确，并处理错误情况

# 设置环境变量
export PATH="/root/.nvm/versions/node/v22.22.0/bin:$PATH"
export PYTHONPATH="/root/.openclaw/workspace/tasks/T01:$PYTHONPATH"

# 切换到工作目录
cd /root/.openclaw/workspace/tasks/T01 || {
    echo "❌ 无法切换到工作目录"
    exit 1
}

# 当前日期
DATE=$(date +%Y-%m-%d)
TIME=$(date +%H:%M:%S)

echo "=== T01进化监控启动 ($DATE $TIME) ==="

# 检查是否是工作日（周一到周五）
WEEKDAY=$(date +%u)  # 1=周一, 7=周日
if [[ $WEEKDAY -ge 1 && $WEEKDAY -le 5 ]]; then
    echo "📅 工作日，执行完整监控..."
    
    # 执行Python监控脚本
    /usr/bin/python3 t01_evolution_monitor.py
    
    EXIT_CODE=$?
    
    if [[ $EXIT_CODE -eq 0 ]]; then
        echo "✅ 监控执行成功"
    else
        echo "❌ 监控执行失败，退出码: $EXIT_CODE"
    fi
    
    # 记录执行日志
    LOG_DIR="logs"
    mkdir -p "$LOG_DIR"
    
    echo "$DATE $TIME - Exit code: $EXIT_CODE" >> "$LOG_DIR/evolution_wrapper.log"
    
    exit $EXIT_CODE
else
    echo "🌴 周末，跳过监控执行"
    
    # 周末只记录日志，不发送消息
    LOG_DIR="logs"
    mkdir -p "$LOG_DIR"
    echo "$DATE $TIME - Weekend skip" >> "$LOG_DIR/evolution_wrapper.log"
    
    exit 0
fi