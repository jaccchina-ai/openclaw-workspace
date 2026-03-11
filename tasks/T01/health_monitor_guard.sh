#!/bin/bash
# Health Monitor Guard - 自动重启健康监控器
# 用法：nohup ./health_monitor_guard.sh > guard.log 2>&1 &

MONITOR_SCRIPT="scheduler_health_monitor.py"
MONITOR_DIR="/root/.openclaw/workspace/tasks/T01"
LOG_FILE="$MONITOR_DIR/health_monitor_guard.log"
CHECK_INTERVAL=60  # 检查间隔（秒）
MAX_RETRIES=5      # 最大连续重试次数
RETRY_COUNT=0

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Health Monitor Guard 启动" >> "$LOG_FILE"

while true; do
    # 检查监控器进程是否运行
    if ! pgrep -f "python3.*$MONITOR_SCRIPT" > /dev/null; then
        RETRY_COUNT=$((RETRY_COUNT + 1))
        
        if [ $RETRY_COUNT -le $MAX_RETRIES ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 警告：健康监控器停止运行，尝试重启 (#$RETRY_COUNT/$MAX_RETRIES)" >> "$LOG_FILE"
            
            # 重启监控器
            cd "$MONITOR_DIR"
            nohup python3 "$MONITOR_SCRIPT" --mode monitor > health_monitor.log 2>&1 &
            sleep 5  # 等待进程启动
            
            # 验证是否启动成功
            if pgrep -f "python3.*$MONITOR_SCRIPT" > /dev/null; then
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] 成功：健康监控器已重启 (PID: $(pgrep -f "python3.*$MONITOR_SCRIPT"))" >> "$LOG_FILE"
                RETRY_COUNT=0  # 重置重试计数
            else
                echo "[$(date '+%Y-%m-%d %H:%M:%S')] 错误：健康监控器重启失败" >> "$LOG_FILE"
            fi
        else
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 严重：达到最大重试次数 ($MAX_RETRIES)，停止自动重启" >> "$LOG_FILE"
            # 可以发送警报通知
            RETRY_COUNT=0  # 重置计数，等待下一个检查周期
        fi
    else
        # 监控器正常运行，重置重试计数
        if [ $RETRY_COUNT -gt 0 ]; then
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] 信息：健康监控器恢复运行，重置重试计数" >> "$LOG_FILE"
            RETRY_COUNT=0
        fi
    fi
    
    sleep $CHECK_INTERVAL
done