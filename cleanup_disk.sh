#!/bin/bash
# 磁盘清理脚本
# 清理Playwright缓存、npm缓存、Chrome安装包等

echo "=== 磁盘清理脚本 ==="
echo "当前磁盘使用情况:"
df -h / | grep -v Filesystem

# 1. Playwright浏览器缓存
PW_CACHE_DIR="/root/.cache/ms-playwright"
if [ -d "$PW_CACHE_DIR" ]; then
    PW_SIZE=$(du -sh "$PW_CACHE_DIR" | cut -f1)
    echo "清理Playwright缓存: $PW_CACHE_DIR ($PW_SIZE)"
    rm -rf "$PW_CACHE_DIR"/*
    echo "Playwright缓存已清理"
else
    echo "Playwright缓存目录不存在"
fi

# 2. npm缓存
NPM_CACHE_DIR="/root/.npm"
if [ -d "$NPM_CACHE_DIR" ]; then
    NPM_SIZE=$(du -sh "$NPM_CACHE_DIR" | cut -f1)
    echo "清理npm缓存: $NPM_CACHE_DIR ($NPM_SIZE)"
    npm cache clean --force
    echo "npm缓存已清理"
else
    echo "npm缓存目录不存在"
fi

# 3. Chrome安装包（如果存在）
CHROME_DEB="/root/chrome.deb"
if [ -f "$CHROME_DEB" ]; then
    CHROME_SIZE=$(du -h "$CHROME_DEB" | cut -f1)
    echo "删除Chrome安装包: $CHROME_DEB ($CHROME_SIZE)"
    rm -f "$CHROME_DEB"
    echo "Chrome安装包已删除"
fi

# 4. 临时文件
echo "清理/tmp目录中7天前的文件"
find /tmp -type f -mtime +7 -delete 2>/dev/null | wc -l | xargs echo "已删除文件数:"

echo "=== 清理完成 ==="
echo "清理后磁盘使用情况:"
df -h / | grep -v Filesystem