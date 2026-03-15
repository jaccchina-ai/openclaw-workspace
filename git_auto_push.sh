#!/bin/bash
# 自动推送 workspace 到 GitHub
# 每周日 6:00 (北京时间) 执行

set -e

WORKSPACE_DIR="/root/.openclaw/workspace"
LOG_FILE="/root/.openclaw/workspace/logs/git_auto_push.log"

# 确保日志目录存在
mkdir -p "$(dirname "$LOG_FILE")"

# 记录开始时间
echo "===== Git Auto Push Started: $(date '+%Y-%m-%d %H:%M:%S %Z') =====" >> "$LOG_FILE"

cd "$WORKSPACE_DIR"

# 检查是否有变更
if git diff --quiet && git diff --cached --quiet; then
    echo "No changes to commit." >> "$LOG_FILE"
    echo "===== Git Auto Push Completed: $(date '+%Y-%m-%d %H:%M:%S %Z') =====" >> "$LOG_FILE"
    exit 0
fi

# 配置 git 用户信息（如果未设置）
git config user.email "bot@openclaw.local" 2>/dev/null || true
git config user.name "OpenClaw Bot" 2>/dev/null || true

# 添加所有变更
echo "Adding changes..." >> "$LOG_FILE"
git add -A >> "$LOG_FILE" 2>&1

# 提交变更
COMMIT_MSG="Auto commit: $(date '+%Y-%m-%d %H:%M') - Weekly sync"
echo "Committing with message: $COMMIT_MSG" >> "$LOG_FILE"
git commit -m "$COMMIT_MSG" >> "$LOG_FILE" 2>&1

# 推送到远程
echo "Pushing to origin..." >> "$LOG_FILE"
if git push origin HEAD >> "$LOG_FILE" 2>&1; then
    echo "✅ Push successful!" >> "$LOG_FILE"
else
    echo "❌ Push failed!" >> "$LOG_FILE"
    exit 1
fi

echo "===== Git Auto Push Completed: $(date '+%Y-%m-%d %H:%M:%S %Z') =====" >> "$LOG_FILE"
echo "" >> "$LOG_FILE"
