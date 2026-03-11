#!/usr/bin/env python3
"""
T01进化计划监控脚本
基于evolution_plan.json跟踪三阶段实施计划的进度
定时发送详细进展报告和提醒
"""

import os
import sys
import json
from datetime import datetime, timedelta
import subprocess
from pathlib import Path
import yaml

# 添加当前目录到路径
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

class T01EvolutionMonitor:
    """T01进化计划监控器"""
    
    def __init__(self, plan_path='evolution_plan.json'):
        """初始化监控器"""
        self.plan_path = os.path.join(current_dir, plan_path)
        self.load_evolution_plan()
        
        # 日志目录
        self.log_dir = os.path.join(current_dir, "logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
    def load_evolution_plan(self):
        """加载进化计划"""
        try:
            with open(self.plan_path, 'r', encoding='utf-8') as f:
                self.plan = json.load(f)
            print(f"✅ 加载进化计划: {self.plan['version']}")
        except Exception as e:
            print(f"❌ 加载进化计划失败: {e}")
            self.plan = self.create_default_plan()
    
    def create_default_plan(self):
        """创建默认进化计划"""
        return {
            "version": "1.0",
            "created_date": datetime.now().strftime("%Y-%m-%d"),
            "phases": []
        }
    
    def get_current_phase(self):
        """获取当前进化阶段"""
        today = datetime.now()
        
        for phase in self.plan.get("phases", []):
            try:
                start_date = datetime.strptime(phase["start_date"], "%Y-%m-%d")
                end_date = datetime.strptime(phase["target_end_date"], "%Y-%m-%d")
                
                if start_date <= today <= end_date:
                    return phase
            except Exception as e:
                print(f"❌ 解析阶段日期失败: {e}")
                continue
        
        return None
    
    def get_upcoming_checkpoints(self, days_ahead=7):
        """获取未来几天的检查点"""
        today = datetime.now()
        upcoming = []
        
        for checkpoint in self.plan.get("implementation_checkpoints", []):
            try:
                check_date = datetime.strptime(checkpoint["date"], "%Y-%m-%d")
                days_diff = (check_date - today).days
                
                if 0 <= days_diff <= days_ahead:
                    checkpoint["days_until"] = days_diff
                    upcoming.append(checkpoint)
            except Exception as e:
                print(f"❌ 解析检查点日期失败: {e}")
                continue
        
        # 按日期排序
        upcoming.sort(key=lambda x: x.get("days_until", 999))
        return upcoming
    
    def calculate_phase_progress(self, phase):
        """计算阶段进度"""
        if not phase or "modules" not in phase:
            return 0
        
        total_modules = len(phase["modules"])
        if total_modules == 0:
            return 0
        
        # 计算完成和进行中的模块
        completed = sum(1 for module in phase["modules"] if module.get("status") == "completed")
        in_progress = sum(1 for module in phase["modules"] if module.get("status") == "in_progress")
        
        # 进度计算：已完成100%，进行中50%，待完成0%
        progress = (completed * 100 + in_progress * 50) / total_modules
        return round(progress, 1)
    
    def check_t01_system_status(self):
        """检查T01系统状态"""
        status = {
            "scheduler_running": False,
            "last_scoring": None,
            "candidate_files": 0,
            "database_exists": False
        }
        
        try:
            # 检查调度器进程
            ps_result = subprocess.run(
                ['ps', 'aux', '|', 'grep', 'scheduler.py', '|', 'grep', '-v', 'grep'],
                shell=True, capture_output=True, text=True
            )
            status["scheduler_running"] = bool(ps_result.stdout.strip())
            
            # 检查候选股文件
            state_dir = os.path.join(current_dir, "state")
            if os.path.exists(state_dir):
                import glob
                candidate_files = glob.glob(os.path.join(state_dir, "candidates_*.json"))
                status["candidate_files"] = len(candidate_files)
                
                if candidate_files:
                    # 获取最新文件日期
                    latest_file = max(candidate_files, key=os.path.getmtime)
                    mtime = datetime.fromtimestamp(os.path.getmtime(latest_file))
                    status["last_scoring"] = mtime.strftime("%Y-%m-%d %H:%M")
            
            # 检查数据库
            db_path = os.path.join(current_dir, "data", "t01_database.db")
            status["database_exists"] = os.path.exists(db_path)
            
        except Exception as e:
            print(f"❌ 检查T01状态异常: {e}")
        
        return status
    
    def send_feishu_message(self, message):
        """发送飞书消息"""
        try:
            # 确保PATH包含Node.js路径
            env = os.environ.copy()
            node_path = "/root/.nvm/versions/node/v22.22.0/bin"
            if node_path not in env.get('PATH', ''):
                env['PATH'] = node_path + ':' + env.get('PATH', '')
            
            # 使用openclaw发送消息
            cmd = [
                '/root/.nvm/versions/node/v22.22.0/bin/openclaw',
                'message', 'send',
                '--channel', 'feishu',
                '--target', 'user:ou_b8a256a9cb526db6c196cb438d6893a6',
                '--message', message
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                print("✅ 飞书消息发送成功")
                return True
            else:
                print(f"❌ 飞书消息发送失败: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"❌ 发送消息异常: {e}")
            return False
    
    def generate_daily_report(self):
        """生成每日报告"""
        today_str = datetime.now().strftime("%Y年%m月%d日")
        current_phase = self.get_current_phase()
        t01_status = self.check_t01_system_status()
        upcoming_checkpoints = self.get_upcoming_checkpoints(7)
        
        # 基础报告
        if current_phase:
            phase_progress = self.calculate_phase_progress(current_phase)
            
            # 计算阶段剩余天数
            end_date = datetime.strptime(current_phase["target_end_date"], "%Y-%m-%d")
            days_left = (end_date - datetime.now()).days
            
            # 阶段模块状态
            module_status = []
            for module in current_phase.get("modules", []):
                status_emoji = "✅" if module.get("status") == "completed" else "🔄" if module.get("status") == "in_progress" else "⏳"
                module_status.append(f"{status_emoji} {module['name']} ({module.get('progress', 0)}%)")
            
            report = f"""📊 **T01进化计划每日报告 ({today_str})**

**🎯 当前阶段**: {current_phase['name']}
**📅 剩余时间**: {days_left}天 | **📈 阶段进度**: {phase_progress}%
**🔧 优先级**: {current_phase['priority']}

**📋 阶段模块**:
{chr(10).join(f'  {status}' for status in module_status)}

**🚀 阶段目标**:
{chr(10).join(f'• {goal}' for goal in current_phase.get('modules', []))}

**⚙️ T01系统状态**:
• 调度器: {'✅ 运行中' if t01_status['scheduler_running'] else '❌ 已停止'}
• 候选股文件: {t01_status['candidate_files']} 个
• 最后评分: {t01_status['last_scoring'] or '未知'}
• 数据库: {'✅ 存在' if t01_status['database_exists'] else '❌ 缺失'}

**📅 未来7天检查点**:
{chr(10).join(f'• {checkpoint["date"]} ({checkpoint["days_until"]}天后): {checkpoint["check"]}' for checkpoint in upcoming_checkpoints[:3])}

**💡 今日建议**:
{self.generate_daily_advice(current_phase, phase_progress, days_left)}"""
        else:
            report = f"""📊 **T01进化计划每日报告 ({today_str})**

**🎯 当前状态**: 阶段间过渡期
**📈 总体匹配度**: {self.plan.get('overall_match_rate', 0.93)*100}%

**⚙️ T01系统状态**:
• 调度器: {'✅ 运行中' if t01_status['scheduler_running'] else '❌ 已停止'}
• 候选股文件: {t01_status['candidate_files']} 个
• 最后评分: {t01_status['last_scoring'] or '未知'}
• 数据库: {'✅ 存在' if t01_status['database_exists'] else '❌ 缺失'}

**📅 未来7天检查点**:
{chr(10).join(f'• {checkpoint["date"]} ({checkpoint["days_until"]}天后): {checkpoint["check"]}' for checkpoint in upcoming_checkpoints[:3])}

**💡 建议行动**: 利用过渡期准备下一个阶段的技术方案和资源。"""
        
        return report
    
    def generate_daily_advice(self, phase, progress, days_left):
        """生成每日建议"""
        if days_left <= 0:
            return "🚨 **阶段今天结束！** 请立即完成所有待办事项并准备阶段总结报告。"
        elif days_left == 1:
            return "⚠️ **阶段明天结束！** 检查未完成模块，优先处理关键任务。"
        elif days_left <= 3:
            return f"⏰ **阶段还剩{days_left}天结束**。加快进度，重点关注进度低于50%的模块。"
        elif progress < 30:
            return f"🐌 **进度较慢** ({progress}%)。建议增加资源投入，重新评估任务优先级。"
        elif progress < 60:
            return f"📈 **稳步推进** ({progress}%)。保持当前节奏，关注高风险模块。"
        elif progress < 90:
            return f"🚀 **良好进展** ({progress}%)。继续推进，准备验收测试。"
        else:
            return f"✅ **接近完成** ({progress}%)。进行最终测试，准备阶段总结。"
    
    def generate_phase_ending_alert(self):
        """生成阶段结束预警"""
        current_phase = self.get_current_phase()
        if not current_phase:
            return None
        
        end_date = datetime.strptime(current_phase["target_end_date"], "%Y-%m-%d")
        days_left = (end_date - datetime.now()).days
        
        if days_left > 2:  # 只提前2天预警
            return None
        
        phase_progress = self.calculate_phase_progress(current_phase)
        
        # 未完成模块
        incomplete_modules = []
        for module in current_phase.get("modules", []):
            if module.get("status") not in ["completed"]:
                incomplete_modules.append(module["name"])
        
        alert = f"""🚨 **T01进化阶段即将结束预警**

**阶段**: {current_phase['name']}
**剩余时间**: {days_left}天
**当前进度**: {phase_progress}%

**未完成模块** ({len(incomplete_modules)}个):
{chr(10).join(f'• {module}' for module in incomplete_modules[:5])}

**紧急程度**: {'🔴 高 (今天结束)' if days_left == 0 else '🟡 中 (明天结束)' if days_left == 1 else '🟠 低 (2天后结束)'}

**建议行动**:
1. 重新评估未完成模块的优先级
2. 如无法按时完成，考虑调整阶段边界
3. 准备阶段总结和下一步计划

请立即采取行动，确保进化计划按时推进！"""
        
        return alert
    
    def log_monitoring_session(self, report_sent, alert_sent):
        """记录监控会话"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "current_phase": self.get_current_phase()["name"] if self.get_current_phase() else None,
            "report_sent": report_sent,
            "alert_sent": alert_sent,
            "t01_status": self.check_t01_system_status()
        }
        
        log_file = os.path.join(self.log_dir, "evolution_monitor.log")
        with open(log_file, "a", encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False, default=str) + "\n")
    
    def run_daily_monitoring(self):
        """执行每日监控"""
        print("🔍 开始T01进化计划每日监控...")
        
        # 生成每日报告
        daily_report = self.generate_daily_report()
        print(f"📋 生成每日报告 ({len(daily_report)}字符)")
        
        # 检查是否需要阶段结束预警
        phase_alert = self.generate_phase_ending_alert()
        
        # 发送消息
        messages_sent = []
        
        # 发送每日报告（只在工作日）
        if datetime.now().weekday() < 5:  # 0-4是周一到周五
            if self.send_feishu_message(daily_report):
                messages_sent.append("每日报告")
        
        # 发送阶段预警（如有）
        if phase_alert:
            print("⚠️ 检测到阶段结束预警")
            if self.send_feishu_message(phase_alert):
                messages_sent.append("阶段结束预警")
        
        # 记录日志
        self.log_monitoring_session(
            report_sent="每日报告" in messages_sent,
            alert_sent="阶段结束预警" in messages_sent
        )
        
        print(f"✅ 监控完成，发送消息: {', '.join(messages_sent) if messages_sent else '无'}")
        return len(messages_sent) > 0

def main():
    """主函数"""
    try:
        monitor = T01EvolutionMonitor()
        success = monitor.run_daily_monitoring()
        return 0 if success else 1
    except Exception as e:
        print(f"❌ 监控执行失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)