#!/bin/bash
# T01调度器健康监控脚本
# 防止僵尸进程，确保单实例运行

set -e

SCRIPT_DIR="/root/.openclaw/workspace/tasks/T01"
LOCK_FILE="/tmp/t01_scheduler.lock"
LOG_FILE="/root/.openclaw/workspace/logs/t01_health_check.log"
MAX_INSTANCES=1

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查scheduler.py进程数量
check_process_count() {
    local count=$(pgrep -f "scheduler.py" | wc -l)
    echo "$count"
}

# 获取最老的scheduler进程PID
get_oldest_pid() {
    pgrep -f "scheduler.py" | head -1
}

# 获取最新的scheduler进程PID
get_newest_pid() {
    pgrep -f "scheduler.py" | tail -1
}

# 获取进程启动时间
get_start_time() {
    local pid=$1
    ps -o lstart= -p "$pid" 2>/dev/null || echo "未知"
}

# 获取进程运行时长
get_runtime() {
    local pid=$1
    ps -o etime= -p "$pid" 2>/dev/null || echo "未知"
}

# 主函数
main() {
    log "🔍 T01调度器健康检查开始"
    
    local count=$(check_process_count)
    log "当前scheduler.py进程数量: $count"
    
    if [ "$count" -eq 0 ]; then
        log "⚠️ 没有scheduler进程运行"
        log "建议: systemctl start t01-scheduler"
        exit 1
    elif [ "$count" -eq 1 ]; then
        local pid=$(get_oldest_pid)
        log "✅ 单实例运行正常 (PID: $pid)"
        log "   启动时间: $(get_start_time $pid)"
        log "   运行时长: $(get_runtime $pid)"
        exit 0
    else
        log "🚨 检测到 $count 个scheduler进程 (僵尸进程!)"
        
        # 列出所有进程
        log "进程列表:"
        for pid in $(pgrep -f "scheduler.py"); do
            log "  PID: $pid, 启动: $(get_start_time $pid), 运行: $(get_runtime $pid)"
        done
        
        # 保留最新的进程，终止其他的
        local newest_pid=$(get_newest_pid)
        log "保留最新进程: $newest_pid"
        
        for pid in $(pgrep -f "scheduler.py"); do
            if [ "$pid" != "$newest_pid" ]; then
                log "🛑 终止僵尸进程: $pid"
                kill -TERM "$pid" 2>/dev/null || true
                sleep 2
                # 强制终止如果还在
                if kill -0 "$pid" 2>/dev/null; then
                    log "⚠️ 进程 $pid 未响应，强制终止"
                    kill -9 "$pid" 2>/dev/null || true
                fi
            fi
        done
        
        # 清理锁文件
        if [ -f "$LOCK_FILE" ]; then
            log "🧹 清理锁文件"
            rm -f "$LOCK_FILE"
        fi
        
        log "✅ 僵尸进程清理完成"
        
        # 重启systemd服务
        log "🔄 重启systemd服务..."
        systemctl restart t01-scheduler
        sleep 3
        
        # 验证
        local new_count=$(check_process_count)
        if [ "$new_count" -eq 1 ]; then
            log "✅ 服务重启成功，单实例运行"
        else
            log "❌ 服务重启后仍有 $new_count 个进程"
        fi
    fi
}

main "$@"
