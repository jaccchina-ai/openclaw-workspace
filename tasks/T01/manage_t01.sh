#!/bin/bash
# T01调度器管理脚本

case "$1" in
    start)
        sudo systemctl start t01-scheduler.service
        echo "T01调度器已启动"
        ;;
    stop)
        sudo systemctl stop t01-scheduler.service
        echo "T01调度器已停止"
        ;;
    restart)
        sudo systemctl restart t01-scheduler.service
        echo "T01调度器已重启"
        ;;
    status)
        sudo systemctl status t01-scheduler.service --no-pager
        ;;
    enable)
        sudo systemctl enable t01-scheduler.service
        echo "T01调度器已设置为开机自启"
        ;;
    disable)
        sudo systemctl disable t01-scheduler.service
        echo "T01调度器已取消开机自启"
        ;;
    logs)
        sudo journalctl -u t01-scheduler.service -n 50 --no-pager
        ;;
    logs-follow)
        sudo journalctl -u t01-scheduler.service -f
        ;;
    check)
        echo "=== T01调度器状态检查 ==="
        sudo systemctl is-active t01-scheduler.service >/dev/null 2>&1 && echo "✅ 服务状态: 运行中" || echo "❌ 服务状态: 未运行"
        sudo systemctl is-enabled t01-scheduler.service >/dev/null 2>&1 && echo "✅ 开机自启: 已启用" || echo "❌ 开机自启: 未启用"
        echo "=== 进程检查 ==="
        ps aux | grep "scheduler.py --mode run" | grep -v grep | wc -l | xargs echo "运行进程数: "
        echo "=== 日志文件 ==="
        ls -la /root/.openclaw/workspace/tasks/T01/systemd*.log 2>/dev/null || echo "无systemd日志文件"
        ;;
    *)
        echo "用法: $0 {start|stop|restart|status|enable|disable|logs|logs-follow|check}"
        echo ""
        echo "命令说明:"
        echo "  start      - 启动T01调度器"
        echo "  stop       - 停止T01调度器"
        echo "  restart    - 重启T01调度器"
        echo "  status     - 查看服务状态"
        echo "  enable     - 设置开机自启"
        echo "  disable    - 取消开机自启"
        echo "  logs       - 查看最近50条日志"
        echo "  logs-follow - 实时查看日志"
        echo "  check      - 完整状态检查"
        exit 1
        ;;
esac
