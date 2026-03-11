#!/usr/bin/env python3
"""任务执行状态监控脚本"""

import os
import sys
import subprocess
from datetime import datetime, timedelta
import json

# 任务配置
TASKS = {
    "T99": {
        "name": "A股短线扫描",
        "log_path": "/root/.openclaw/workspace/skills/a-share-short-decision/scan.log",
        "schedule": "工作日 14:30",
        "max_age_hours": 48
    },
    "T100": {
        "name": "宏观监控报告", 
        "log_path": "/root/.openclaw/workspace/skills/macro-monitor/monitor.log",
        "schedule": "每日 22:00",
        "max_age_hours": 36
    },
    "T01_auction": {
        "name": "T01竞价准备检查",
        "log_path": "/root/.openclaw/workspace/tasks/T01/auction_preparation_check.log",
        "schedule": "工作日 08:30",
        "max_age_hours": 48
    },
    "T01_tday": {
        "name": "T01 T日评分",
        "log_path": "/root/.openclaw/workspace/tasks/T01/t01_daily_scoring.log", 
        "schedule": "工作日 12:00",
        "max_age_hours": 48
    }
}

def check_task_status(task_id, task_config):
    """检查单个任务状态"""
    log_path = task_config["log_path"]
    task_name = task_config["name"]
    max_age_hours = task_config["max_age_hours"]
    
    status = {
        "task_id": task_id,
        "task_name": task_name,
        "schedule": task_config["schedule"],
        "log_exists": False,
        "log_modified": None,
        "log_age_hours": None,
        "status": "unknown",
        "message": ""
    }
    
    # 检查日志文件是否存在
    if not os.path.exists(log_path):
        status["status"] = "error"
        status["message"] = f"日志文件不存在: {log_path}"
        return status
    
    status["log_exists"] = True
    
    # 获取文件修改时间
    try:
        mtime = os.path.getmtime(log_path)
        mod_time = datetime.fromtimestamp(mtime)
        now = datetime.now()
        age_hours = (now - mod_time).total_seconds() / 3600
        
        status["log_modified"] = mod_time.strftime("%Y-%m-%d %H:%M:%S")
        status["log_age_hours"] = round(age_hours, 1)
        
        # 判断状态
        if age_hours <= max_age_hours:
            status["status"] = "healthy"
            status["message"] = f"最近执行于 {mod_time.strftime('%m-%d %H:%M')} ({age_hours:.1f}小时前)"
        else:
            status["status"] = "stale"
            status["message"] = f"日志已过期: {mod_time.strftime('%m-%d %H:%M')} ({age_hours:.1f}小时前，超过{max_age_hours}小时)"
            
    except Exception as e:
        status["status"] = "error"
        status["message"] = f"读取日志文件错误: {e}"
    
    return status

def check_process_alive():
    """检查关键进程是否存活"""
    processes = {
        "T01_scheduler": ["python3", "scheduler.py"],
        "T01_monitor": ["python3", "scheduler_health_monitor.py"]
    }
    
    results = []
    for proc_name, proc_cmd in processes.items():
        try:
            # 使用pgrep检查进程
            cmd = ["pgrep", "-f", " ".join(proc_cmd)]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split()
                results.append({
                    "process": proc_name,
                    "status": "alive",
                    "pids": pids,
                    "count": len(pids)
                })
            else:
                results.append({
                    "process": proc_name,
                    "status": "dead",
                    "pids": [],
                    "count": 0
                })
        except Exception as e:
            results.append({
                "process": proc_name,
                "status": "error",
                "error": str(e)
            })
    
    return results

def generate_report(task_statuses, process_statuses):
    """生成状态报告"""
    report = []
    report.append("=== 任务执行状态监控报告 ===")
    report.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # 任务状态
    report.append("📊 任务执行状态:")
    healthy_count = sum(1 for s in task_statuses if s["status"] == "healthy")
    stale_count = sum(1 for s in task_statuses if s["status"] == "stale")
    error_count = sum(1 for s in task_statuses if s["status"] == "error")
    
    report.append(f"  健康: {healthy_count}, 过期: {stale_count}, 错误: {error_count}")
    
    for status in task_statuses:
        emoji = "✅" if status["status"] == "healthy" else "⚠️" if status["status"] == "stale" else "❌"
        report.append(f"  {emoji} {status['task_name']} ({status['task_id']}): {status['message']}")
    
    report.append("")
    
    # 进程状态
    report.append("🖥️ 进程运行状态:")
    alive_count = sum(1 for p in process_statuses if p["status"] == "alive")
    dead_count = sum(1 for p in process_statuses if p["status"] == "dead")
    
    for proc in process_statuses:
        if proc["status"] == "alive":
            report.append(f"  ✅ {proc['process']}: 运行中 (PID: {', '.join(proc['pids']) if proc['pids'] else '无'})")
        elif proc["status"] == "dead":
            report.append(f"  ❌ {proc['process']}: 未运行")
        else:
            report.append(f"  ⚠️ {proc['process']}: 检查错误 - {proc.get('error', '未知错误')}")
    
    report.append("")
    
    # 汇总建议
    if stale_count > 0 or error_count > 0 or dead_count > 0:
        report.append("🚨 需要关注:")
        for status in task_statuses:
            if status["status"] in ["stale", "error"]:
                report.append(f"  • {status['task_name']}: {status['message']}")
        
        for proc in process_statuses:
            if proc["status"] == "dead":
                report.append(f"  • {proc['process']}: 进程未运行")
        
        report.append("建议检查cron任务执行和进程启动状态。")
    else:
        report.append("✅ 所有系统运行正常！")
    
    return "\n".join(report)

def main():
    """主函数"""
    print("开始检查任务执行状态...")
    
    # 检查所有任务状态
    task_statuses = []
    for task_id, task_config in TASKS.items():
        print(f"检查任务: {task_config['name']}")
        status = check_task_status(task_id, task_config)
        task_statuses.append(status)
    
    # 检查进程状态
    print("检查进程状态...")
    process_statuses = check_process_alive()
    
    # 生成报告
    report = generate_report(task_statuses, process_statuses)
    print("\n" + report)
    
    # 保存报告到文件
    report_file = "/root/.openclaw/workspace/task_monitor_report.txt"
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    print(f"\n报告已保存到: {report_file}")
    
    # 如果有问题，返回非零退出码
    if any(s["status"] in ["stale", "error"] for s in task_statuses) or \
       any(p["status"] == "dead" for p in process_statuses):
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())