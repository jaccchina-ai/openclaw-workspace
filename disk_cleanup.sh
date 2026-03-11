#!/bin/bash
# 磁盘清理脚本 - 清理系统缓存，释放磁盘空间
# 创建时间: 2026-03-08
# 作者: 小虾米

set -e

echo "=== 磁盘清理开始 ==="
echo "当前磁盘使用情况:"
df -h /root/

echo -e "\n🔍 扫描可清理的缓存文件..."

# Playwright浏览器缓存
PLAYWRIGHT_CACHE="/root/.cache/ms-playwright"
if [ -d "$PLAYWRIGHT_CACHE" ]; then
    PLAYWRIGHT_SIZE=$(du -sh "$PLAYWRIGHT_CACHE" | cut -f1)
    echo "✅ Playwright缓存: $PLAYWRIGHT_SIZE"
else
    echo "ℹ️  Playwright缓存不存在"
fi

# npm缓存
NPM_CACHE="/root/.npm"
if [ -d "$NPM_CACHE" ]; then
    NPM_SIZE=$(du -sh "$NPM_CACHE" | cut -f1)
    echo "✅ npm缓存: $NPM_SIZE"
else
    echo "ℹ️  npm缓存不存在"
fi

# Chrome安装包
CHROME_PKGS=$(find /tmp -name "*chrome*" -o -name "*google*" -type f 2>/dev/null | wc -l)
if [ "$CHROME_PKGS" -gt 0 ]; then
    CHROME_SIZE=$(find /tmp -name "*chrome*" -o -name "*google*" -type f 2>/dev/null | xargs du -ch 2>/dev/null | tail -1 | cut -f1)
    echo "✅ Chrome安装包: ${CHROME_SIZE:-未知} (${CHROME_PKGS}个文件)"
else
    echo "ℹ️  Chrome安装包不存在"
fi

# 系统临时文件
TEMP_FILES=$(find /tmp -type f -atime +7 2>/dev/null | wc -l)
if [ "$TEMP_FILES" -gt 0 ]; then
    echo "✅ 7天以上临时文件: ${TEMP_FILES}个"
fi

# 日志文件（保留7天）
LOG_FILES=$(find /var/log -name "*.log" -type f -mtime +7 2>/dev/null | wc -l)
if [ "$LOG_FILES" -gt 0 ]; then
    echo "✅ 7天以上日志文件: ${LOG_FILES}个"
fi

echo -e "\n📋 清理选项:"
echo "1) 仅清理Playwright缓存 (安全)"
echo "2) 清理所有缓存 (包括npm, Chrome安装包)"
echo "3) 仅查看，不清理"
echo "4) 退出"

read -p "请选择操作 [1-4]: " choice

case $choice in
    1)
        echo "清理Playwright缓存..."
        if [ -d "$PLAYWRIGHT_CACHE" ]; then
            rm -rf "$PLAYWRIGHT_CACHE"
            echo "✅ Playwright缓存已清理"
        fi
        ;;
    2)
        echo "清理所有缓存..."
        # Playwright缓存
        if [ -d "$PLAYWRIGHT_CACHE" ]; then
            rm -rf "$PLAYWRIGHT_CACHE"
            echo "✅ Playwright缓存已清理"
        fi
        
        # npm缓存 (使用npm命令清理，更安全)
        if command -v npm &> /dev/null; then
            npm cache clean --force
            echo "✅ npm缓存已清理"
        elif [ -d "$NPM_CACHE" ]; then
            echo "⚠️  警告: 直接删除npm缓存可能影响npm功能"
            read -p "是否继续删除npm缓存? (y/N): " confirm
            if [[ $confirm =~ ^[Yy]$ ]]; then
                rm -rf "$NPM_CACHE"
                echo "✅ npm缓存已清理"
            else
                echo "⏭️  跳过npm缓存清理"
            fi
        fi
        
        # Chrome安装包
        if [ "$CHROME_PKGS" -gt 0 ]; then
            find /tmp -name "*chrome*" -o -name "*google*" -type f -delete 2>/dev/null
            echo "✅ Chrome安装包已清理"
        fi
        
        # 7天以上临时文件
        if [ "$TEMP_FILES" -gt 0 ]; then
            find /tmp -type f -atime +7 -delete 2>/dev/null
            echo "✅ 7天以上临时文件已清理"
        fi
        
        echo "✅ 所有缓存清理完成"
        ;;
    3)
        echo "仅查看模式，未执行清理"
        ;;
    4|*)
        echo "操作取消"
        exit 0
        ;;
esac

echo -e "\n📊 清理后磁盘使用情况:"
df -h /root/

echo "=== 磁盘清理完成 ==="