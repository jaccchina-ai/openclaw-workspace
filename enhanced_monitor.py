#!/usr/bin/env python3
"""增强版系统健康监控与警报"""

import os
import sys
import json
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

# 配置
CONFIG = {
    "alert_channel": "feishu",
    "alert_target": "chat:oc_ff08c55a23630937869cd222dad0bf14",
    "openclaw_path": "/root/.nvm/versions/node/v22.22.0/bin/openclaw",
    "check_interval_hours": 6,  # 每6小时检查一次
    "max_failures_before_alert": 2,  # 连续2次失败才报警
}

# 监控任务
# 注意: T99和T100任务已于2026-03-11停用清理，此处仅保留T01监控
MONITOR_TASKS = [
    {
        "id": "t01_auction_check",
        "name": "T01竞价准备检查",
        "log_path": "/root/.openclaw/workspace/tasks/T01/auction_preparation_check.log",
        "schedule": "工作日08:30",
        "max_age_hours": 48,
        "alert_message": "⚠️ T01竞价检查可能未执行"
    },
    {
        "id": "t01_tday_scoring",
        "name": "T01 T日评分",
        "log_path": "/root/.openclaw/workspace/tasks/T01/t01_daily_scoring.log",
        "schedule": "工作日12:00",
        "max_age_hours": 48,
        "alert_message": "⚠️ T01 T日评分可能未执行"
    }
]

# 进程监控
# 注意: scheduler_health_monitor.py 已不再使用，只监控核心调度器
PROCESS_MONITORS = [
    {
        "name": "T01调度器",
        "pattern": "python3 scheduler.py",
        "min_count": 1,
        "alert_message": "🚨 T01调度器进程可能已停止"
    }
    # 已删除: scheduler_health_monitor.py 监控 (该组件已不再使用)
]

class HealthMonitor:
    def __init__(self):
        self.state_file = "/root/.openclaw/workspace/.monitor_state.json"
        self.alerts = []
        self.state = self.load_state()
        
    def load_state(self):
        """加载监控状态"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                pass
        return {"task_failures": {}, "last_check": None, "alert_history": []}
    
    def save_state(self):
        """保存监控状态"""
        self.state["last_check"] = datetime.now().isoformat()
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"保存状态失败: {e}")
    
    def check_task_health(self, task):
        """检查任务健康状态"""
        log_path = task["log_path"]
        task_id = task["id"]
        
        if not os.path.exists(log_path):
            return {"healthy": False, "reason": f"日志文件不存在: {log_path}"}
        
        try:
            mtime = os.path.getmtime(log_path)
            mod_time = datetime.fromtimestamp(mtime)
            age_hours = (datetime.now() - mod_time).total_seconds() / 3600
            
            if age_hours <= task["max_age_hours"]:
                return {"healthy": True, "age_hours": age_hours, "last_run": mod_time.isoformat()}
            else:
                return {"healthy": False, "reason": f"日志过期: {age_hours:.1f}小时前更新", "age_hours": age_hours}
                
        except Exception as e:
            return {"healthy": False, "reason": f"检查日志失败: {e}"}
    
    def check_process_health(self, process_monitor):
        """检查进程健康状态"""
        pattern = process_monitor["pattern"]
        min_count = process_monitor["min_count"]
        
        try:
            cmd = ["pgrep", "-f", pattern]
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                pids = result.stdout.strip().split()
                count = len(pids)
                if count >= min_count:
                    return {"healthy": True, "count": count, "pids": pids}
                else:
                    return {"healthy": False, "reason": f"进程数量不足: {count} < {min_count}", "count": count}
            else:
                return {"healthy": False, "reason": "进程未找到", "count": 0}
                
        except Exception as e:
            return {"healthy": False, "reason": f"检查进程失败: {e}", "count": 0}
    
    def record_failure(self, item_id, item_type="task"):
        """记录失败次数"""
        key = f"{item_type}_{item_id}"
        if key not in self.state["task_failures"]:
            self.state["task_failures"][key] = {"count": 0, "first_failure": None}
        
        failures = self.state["task_failures"][key]
        failures["count"] += 1
        
        if not failures["first_failure"]:
            failures["first_failure"] = datetime.now().isoformat()
        
        # 检查是否需要报警
        if failures["count"] >= CONFIG["max_failures_before_alert"]:
            return True
        return False
    
    def reset_failures(self, item_id, item_type="task"):
        """重置失败计数"""
        key = f"{item_type}_{item_id}"
        if key in self.state["task_failures"]:
            self.state["task_failures"][key] = {"count": 0, "first_failure": None}
    
    def send_alert(self, message):
        """发送警报"""
        try:
            cmd = [
                CONFIG["openclaw_path"],
                "message", "send",
                "--channel", CONFIG["alert_channel"],
                "--target", CONFIG["alert_target"],
                "--message", message
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print(f"✅ 警报已发送: {message[:50]}...")
                # 记录警报历史
                alert_record = {
                    "timestamp": datetime.now().isoformat(),
                    "message": message[:200],
                    "sent": True
                }
                self.state["alert_history"].append(alert_record)
                # 保持历史记录长度
                if len(self.state["alert_history"]) > 50:
                    self.state["alert_history"] = self.state["alert_history"][-50:]
                return True
            else:
                print(f"❌ 发送警报失败: {result.stderr[:100]}")
                return False
                
        except Exception as e:
            print(f"❌ 发送警报异常: {e}")
            return False
    
    def generate_report(self, task_results, process_results):
        """生成健康报告"""
        report = []
        report.append("🏥 系统健康检查报告")
        report.append(f"检查时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # 任务状态
        healthy_tasks = sum(1 for r in task_results if r["healthy"])
        total_tasks = len(task_results)
        
        report.append(f"📊 任务状态 ({healthy_tasks}/{total_tasks} 健康):")
        for task, result in zip(MONITOR_TASKS, task_results):
            emoji = "✅" if result["healthy"] else "❌"
            report.append(f"  {emoji} {task['name']}: {result.get('reason', '正常')}")
        
        report.append("")
        
        # 进程状态
        healthy_processes = sum(1 for r in process_results if r["healthy"])
        total_processes = len(process_results)
        
        report.append(f"🖥️ 进程状态 ({healthy_processes}/{total_processes} 健康):")
        for proc, result in zip(PROCESS_MONITORS, process_results):
            emoji = "✅" if result["healthy"] else "❌"
            report.append(f"  {emoji} {proc['name']}: {result.get('reason', '正常')}")
        
        report.append("")
        
        # 汇总
        if healthy_tasks == total_tasks and healthy_processes == total_processes:
            report.append("🎉 所有系统运行正常！")
        else:
            report.append("⚠️ 发现系统问题，建议检查:")
            for task, result in zip(MONITOR_TASKS, task_results):
                if not result["healthy"]:
                    report.append(f"  • {task['name']}: {result.get('reason', '未知问题')}")
            
            for proc, result in zip(PROCESS_MONITORS, process_results):
                if not result["healthy"]:
                    report.append(f"  • {proc['name']}: {result.get('reason', '未知问题')}")
        
        return "\n".join(report)
    
    def run(self):
        """运行监控检查"""
        print("开始系统健康检查...")
        
        # 检查所有任务
        task_results = []
        for task in MONITOR_TASKS:
            result = self.check_task_health(task)
            task_results.append(result)
            
            if result["healthy"]:
                self.reset_failures(task["id"])
            else:
                needs_alert = self.record_failure(task["id"])
                if needs_alert:
                    alert_msg = f"{task['alert_message']}\n原因: {result['reason']}\n时间: {datetime.now().strftime('%m-%d %H:%M')}"
                    self.send_alert(alert_msg)
                    self.alerts.append(alert_msg)
        
        # 检查所有进程
        process_results = []
        for proc in PROCESS_MONITORS:
            result = self.check_process_health(proc)
            process_results.append(result)
            
            if result["healthy"]:
                self.reset_failures(proc["name"], "process")
            else:
                needs_alert = self.record_failure(proc["name"], "process")
                if needs_alert:
                    alert_msg = f"{proc['alert_message']}\n原因: {result['reason']}\n时间: {datetime.now().strftime('%m-%d %H:%M')}"
                    self.send_alert(alert_msg)
                    self.alerts.append(alert_msg)
        
        # 生成报告
        report = self.generate_report(task_results, process_results)
        print("\n" + report)
        
        # 保存状态
        self.save_state()
        
        # 保存报告到文件
        report_file = "/root/.openclaw/workspace/health_monitor_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        
        print(f"\n报告已保存到: {report_file}")
        
        # 如果有警报，返回非零退出码
        return 1 if self.alerts else 0

def main():
    """主函数"""
    monitor = HealthMonitor()
    return monitor.run()

if __name__ == "__main__":
    sys.exit(main())