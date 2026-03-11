#!/bin/bash
# 月度磁盘清理脚本
# 每月自动清理缓存文件，释放磁盘空间
# 清理内容包括：npm缓存、Playwright缓存、临时文件等

set -e

LOG_FILE="/root/.openclaw/workspace/logs/disk_cleanup.log"
CLEANUP_DATE=$(date '+%Y-%m-%d %H:%M:%S')

# 创建日志目录
mkdir -p "$(dirname "$LOG_FILE")"

# 日志函数
log() {
    echo "[$CLEANUP_DATE] $1" | tee -a "$LOG_FILE"
}

# 检查磁盘空间
check_disk_space() {
    local before=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    local available=$(df -h / | awk 'NR==2 {print $4}')
    
    log "=== 磁盘清理开始 ==="
    log "清理前磁盘使用率: $before%"
    log "可用空间: $available"
    
    return $before
}

# 清理npm缓存
clean_npm_cache() {
    local npm_cache_dir="$HOME/.npm/_cacache"
    local npm_cache_size=""
    
    if [ -d "$npm_cache_dir" ]; then
        npm_cache_size=$(du -sh "$npm_cache_dir" 2>/dev/null | cut -f1)
        log "清理npm缓存: $npm_cache_dir ($npm_cache_size)"
        
        # 清理npm缓存
        rm -rf "$npm_cache_dir" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log "✅ npm缓存清理完成 (释放: $npm_cache_size)"
        else
            log "⚠️ npm缓存清理失败"
        fi
    else
        log "📊 npm缓存目录不存在: $npm_cache_dir"
    fi
}

# 清理Playwright浏览器缓存
clean_playwright_cache() {
    local playwright_cache="$HOME/.cache/ms-playwright"
    local playwright_size=""
    
    if [ -d "$playwright_cache" ]; then
        playwright_size=$(du -sh "$playwright_cache" 2>/dev/null | cut -f1)
        log "清理Playwright缓存: $playwright_cache ($playwright_size)"
        
        rm -rf "$playwright_cache" 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log "✅ Playwright缓存清理完成 (释放: $playwright_size)"
        else
            log "⚠️ Playwright缓存清理失败"
        fi
    else
        log "📊 Playwright缓存目录不存在: $playwright_cache"
    fi
}

# 清理Python缓存
clean_python_cache() {
    local pycache_dirs=(
        "/root/.openclaw/workspace/tasks/T01/__pycache__"
        "/root/.openclaw/workspace/skills/a-share-short-decision/__pycache__"
        "/root/.openclaw/workspace/skills/macro-monitor/__pycache__"
    )
    
    local total_cleaned=0
    
    for dir in "${pycache_dirs[@]}"; do
        if [ -d "$dir" ]; then
            local dir_size=$(du -sh "$dir" 2>/dev/null | cut -f1)
            log "清理Python缓存: $dir ($dir_size)"
            
            rm -rf "$dir" 2>/dev/null
            
            if [ $? -eq 0 ]; then
                log "✅ Python缓存清理完成: $dir"
                total_cleaned=$((total_cleaned + 1))
            else
                log "⚠️ Python缓存清理失败: $dir"
            fi
        fi
    done
    
    if [ $total_cleaned -gt 0 ]; then
        log "✅ 共清理 $total_cleaned 个Python缓存目录"
    fi
}

# 清理旧日志文件 (保留最近30天)
clean_old_logs() {
    local log_dirs=(
        "/root/.openclaw/workspace/tasks/T01/logs"
        "/root/.openclaw/workspace/skills/a-share-short-decision"
        "/root/.openclaw/workspace/skills/macro-monitor"
    )
    
    local total_cleaned=0
    
    for dir in "${log_dirs[@]}"; do
        if [ -d "$dir" ]; then
            # 查找超过30天的.log文件
            local old_logs=$(find "$dir" -name "*.log" -type f -mtime +30 2>/dev/null | wc -l)
            
            if [ "$old_logs" -gt 0 ]; then
                log "清理旧日志: $dir (超过30天: $old_logs 个文件)"
                
                find "$dir" -name "*.log" -type f -mtime +30 -delete 2>/dev/null
                
                if [ $? -eq 0 ]; then
                    log "✅ 旧日志清理完成: $old_logs 个文件"
                    total_cleaned=$((total_cleaned + old_logs))
                else
                    log "⚠️ 旧日志清理失败: $dir"
                fi
            fi
        fi
    done
    
    if [ $total_cleaned -gt 0 ]; then
        log "✅ 共清理 $total_cleaned 个旧日志文件"
    fi
}

# 安全清理 - 确保不删除重要文件
clean_tmp_files() {
    # 清理超过7天的临时文件 (仅限/tmp目录下我们自己的文件)
    local tmp_files=$(find /tmp -name "*openclaw*" -type f -mtime +7 2>/dev/null | wc -l)
    
    if [ "$tmp_files" -gt 0 ]; then
        log "清理临时文件: /tmp (超过7天: $tmp_files 个文件)"
        
        find /tmp -name "*openclaw*" -type f -mtime +7 -delete 2>/dev/null
        
        if [ $? -eq 0 ]; then
            log "✅ 临时文件清理完成: $tmp_files 个文件"
        else
            log "⚠️ 临时文件清理失败"
        fi
    fi
}

# 清理后检查磁盘空间
check_after_cleanup() {
    sleep 2  # 等待文件系统更新
    
    local after=$(df -h / | awk 'NR==2 {print $5}' | tr -d '%')
    local available=$(df -h / | awk 'NR==2 {print $4}')
    
    log "=== 磁盘清理完成 ==="
    log "清理后磁盘使用率: $after%"
    log "可用空间: $available"
    
    # 计算释放的空间 (近似值)
    local before_usage="$1"
    if [ -n "$before_usage" ]; then
        local released=$((before_usage - after))
        if [ "$released" -gt 0 ]; then
            log "✅ 释放磁盘空间: 约${released}%"
        else
            log "📊 磁盘使用率变化: $before_usage% → $after%"
        fi
    fi
    
    log "清理时间: $CLEANUP_DATE"
    log "日志文件: $LOG_FILE"
}

# 主函数
main() {
    log "🚀 启动月度磁盘清理任务"
    
    # 检查清理前磁盘空间
    check_disk_space
    local before_usage=$?
    
    # 执行各项清理任务
    clean_npm_cache
    clean_playwright_cache
    clean_python_cache
    clean_old_logs
    clean_tmp_files
    
    # 检查清理结果
    check_after_cleanup "$before_usage"
    
    log "✅ 月度磁盘清理任务完成"
    
    # 返回最终状态
    exit 0
}

# 捕获信号
trap 'log "脚本被中断"; exit 1' INT TERM

# 运行主函数
main "$@"