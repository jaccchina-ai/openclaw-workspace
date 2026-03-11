#!/bin/bash
# T01完整crontab配置脚本
# 重新创建所有cron任务，包括进化监控系统

echo "=== 重新配置T01完整cron任务 ==="
echo "时间: $(date)"
echo ""

# 创建新的crontab内容
CRON_CONTENT="# T01完整自动化系统cron配置
# 生成时间: $(date)
# 系统: $(uname -a)

# 环境变量设置
SHELL=/bin/bash
PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/root/.nvm/versions/node/v22.22.0/bin
HOME=/root
MAILTO=\"\"

# 腾讯云监控任务 (保留)
*/5 * * * * flock -xn /tmp/stargate.lock -c '/usr/local/qcloud/stargate/admin/start.sh > /dev/null 2>&1 &'

# ==================== T100宏观监控 ====================
# 每日22:00 (北京时间) 生成宏观监控报告
0 22 * * * cd /root/.openclaw/workspace/skills/macro-monitor && PATH=/root/.nvm/versions/node/v22.22.0/bin:\$PATH env TEST_MODE=0 /usr/bin/python3 run_monitor.py >> monitor.log 2>&1

# ==================== T01龙头战法任务 ====================
# 竞价准备检查 (周一至周五 08:30 北京时间, UTC 00:30)
30 0 * * 1-5 /root/.openclaw/workspace/tasks/T01/run_auction_preparation.sh

# T日评分任务 (周一至周五 20:00 北京时间, UTC 12:00)
0 12 * * 1-5 /root/.openclaw/workspace/tasks/T01/run_daily_scoring.sh

# T01连续无选股预警监控 (T日评分后30分钟，北京时间20:30，UTC 12:30)
30 12 * * 1-5 cd /root/.openclaw/workspace/tasks/T01 && PATH=/root/.nvm/versions/node/v22.22.0/bin:\$PATH /usr/bin/python3 no_selection_warning.py >> /root/.openclaw/workspace/tasks/T01/logs/no_selection_warning_cron.log 2>&1

# ==================== T01进化系统监控 ====================
# T01进化阶段简单提醒 (周一至周五 09:00 北京时间, UTC 01:00)
0 1 * * 1-5 cd /root/.openclaw/workspace/tasks/T01 && PATH=/root/.nvm/versions/node/v22.22.0/bin:\$PATH ./simple_evolution_reminder.sh >> /root/.openclaw/workspace/tasks/T01/logs/evolution_cron.log 2>&1

# T01进化计划详细监控 (周一至周五 09:30 北京时间, UTC 01:30)
30 1 * * 1-5 cd /root/.openclaw/workspace/tasks/T01 && PATH=/root/.nvm/versions/node/v22.22.0/bin:\$PATH ./evolution_monitor_wrapper.sh >> /root/.openclaw/workspace/tasks/T01/logs/evolution_monitor.log 2>&1

# ==================== 系统维护任务 ====================
# 每周日22:00 (北京时间) 检查技能更新 (UTC 14:00)
0 14 * * 0 /root/.openclaw/scripts/check_skill_updates.sh

# 系统健康监控 (每6小时)
0 */6 * * * cd /root/.openclaw/workspace && /usr/bin/python3 enhanced_monitor.py >> /root/.openclaw/workspace/health_monitor.log 2>&1

# 月度磁盘清理 (每月1号02:00 UTC，北京时间10:00)
0 2 1 * * /root/.openclaw/workspace/monthly_disk_cleanup.sh >> /root/.openclaw/workspace/logs/monthly_cleanup.log 2>&1

# 交易日准备检查 (周一至周五 08:00 北京时间, UTC 00:00)
0 0 * * 1-5 /root/.openclaw/workspace/trading_day_precheck.sh >> /root/.openclaw/workspace/logs/trading_day_precheck.log 2>&1

# ==================== 测试任务 (可选) ====================
# 测试任务 - 每分钟执行，验证cron工作
# * * * * * /bin/echo \"Cron test at \$(date)\" >> /tmp/cron_test.log 2>&1

# T01 Cron Wrapper Test - 诊断任务（shell脚本包装器）
# 0 2 * * * /root/.openclaw/workspace/tasks/T01/cron_wrapper_test.sh >> /root/.openclaw/workspace/tasks/T01/logs/cron_test.log 2>&1
"

echo "创建新的crontab配置..."
echo "$CRON_CONTENT" | crontab -

# 验证配置
echo ""
echo "=== 验证crontab配置 ==="
crontab -l | head -20
echo "..."

# 检查任务数量
TASK_COUNT=$(crontab -l | grep -v '^#' | grep -v '^$' | wc -l)
echo ""
echo "配置完成！共设置了 $TASK_COUNT 个cron任务。"
echo "cron服务将自动重新加载配置。"

# 创建配置备份
BACKUP_DIR="/root/.openclaw/workspace/backups/cron"
mkdir -p "$BACKUP_DIR"
BACKUP_FILE="$BACKUP_DIR/crontab_backup_$(date +%Y%m%d_%H%M%S).txt"
crontab -l > "$BACKUP_FILE"
echo "配置已备份到: $BACKUP_FILE"

echo ""
echo "✅ T01完整cron配置完成！进化监控系统已集成。"