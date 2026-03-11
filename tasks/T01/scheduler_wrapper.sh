#!/bin/bash
# T01调度器包装脚本 - 确保单实例运行
# 使用文件锁防止重复启动

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOCK_FILE="/tmp/t01_scheduler.lock"
LOG_FILE="/tmp/t01_scheduler_wrapper.log"

# 日志函数
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# 检查锁文件
check_lock() {
    if [ -f "$LOCK_FILE" ]; then
        local pid=$(cat "$LOCK_FILE" 2>/dev/null)
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            log "⚠️ 调度器进程已在运行 (PID: $pid)"
            log "   启动时间: $(ps -o lstart= -p "$pid" 2>/dev/null || echo '未知')"
            log "   运行时长: $(ps -o etime= -p "$pid" 2>/dev/null || echo '未知')"
            return 1
        else
            log "⚠️ 发现陈旧的锁文件，清理中..."
            rm -f "$LOCK_FILE"
        fi
    fi
    return 0
}

# 使用flock获取锁
acquire_lock() {
    exec 200>"$LOCK_FILE"
    flock -n 200 || {
        log "❌ 无法获取锁，调度器可能已在其他终端运行"
        return 1
    }
    echo $$ > "$LOCK_FILE"
    log "✅ 锁文件创建成功 (PID: $$)"
}

# 清理函数
cleanup() {
    log "🔄 清理锁文件..."
    rm -f "$LOCK_FILE"
    log "✅ 清理完成"
}

# 主函数
main() {
    log "🚀 启动T01调度器包装脚本"
    log "工作目录: $SCRIPT_DIR"
    
    # 检查是否已有实例运行
    if ! check_lock; then
        log "❌ 退出: 已有调度器实例运行"
        exit 1
    fi
    
    # 获取锁
    if ! acquire_lock; then
        log "❌ 退出: 无法获取锁"
        exit 1
    fi
    
    # 设置退出时清理
    trap cleanup EXIT
    
    # 切换到工作目录
    cd "$SCRIPT_DIR"
    
    # 启动调度器
    log "📊 启动调度器进程..."
    log "命令: python3 scheduler.py --mode run"
    
    # 执行调度器
    python3 scheduler.py --mode run
    
    local exit_code=$?
    
    if [ $exit_code -eq 0 ]; then
        log "✅ 调度器正常退出"
    else
        log "⚠️ 调度器异常退出 (代码: $exit_code)"
    fi
    
    return $exit_code
}

# 运行主函数
main "$@"