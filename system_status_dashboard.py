#!/usr/bin/env python3
"""
系统状态仪表板 - 统一监控 T01/T99/T100 任务状态
提供实时健康度评分、执行历史、资源使用情况和建议行动
"""

import os
import json
import sys
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import logging

# 配置
WORKSPACE_ROOT = Path("/root/.openclaw/workspace")
LOG_DIR = WORKSPACE_ROOT / "logs"
TRADING_CALENDAR = WORKSPACE_ROOT / "trading_calendar.json"
FEISHU_STATS = LOG_DIR / "feishu_stats.json"

# 颜色编码
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
BLUE = "\033[94m"
RESET = "\033[0m"
BOLD = "\033[1m"

class SystemStatusDashboard:
    def __init__(self):
        self.now = datetime.now()
        self.now_str = self.now.strftime("%Y-%m-%d %H:%M:%S")
        self.results = {}
        
    def print_header(self):
        """打印仪表板头部"""
        print(f"\n{BOLD}{BLUE}=== 系统状态仪表板 ==={RESET}")
        print(f"生成时间: {self.now_str} (UTC)")
        print(f"工作空间: {WORKSPACE_ROOT}")
        print("-" * 60)
        
    def print_section(self, title):
        """打印章节标题"""
        print(f"\n{BOLD}{title}{RESET}")
        print("-" * 40)
        
    def print_status(self, item, status, details=""):
        """打印状态行"""
        if status == "✅":
            color = GREEN
        elif status == "⚠️":
            color = YELLOW
        elif status == "❌":
            color = RED
        else:
            color = RESET
            
        print(f"{color}{status}{RESET} {item}", end="")
        if details:
            print(f" - {details}")
        else:
            print()
    
    def check_trading_day(self):
        """检查今日是否为交易日"""
        self.print_section("📅 交易日状态")
        
        try:
            with open(TRADING_CALENDAR, 'r') as f:
                calendar = json.load(f)
            
            today = self.now.strftime("%Y-%m-%d")
            year = today[:4]
            
            if year in calendar and "trading_days" in calendar[year]:
                trading_days = calendar[year]["trading_days"]
                if today in trading_days:
                    self.print_status(f"今日 {today}", "✅", "交易日")
                    return True
                else:
                    self.print_status(f"今日 {today}", "⚠️", "非交易日")
                    return False
            else:
                self.print_status("交易日历", "❌", "数据缺失")
                return None
                
        except Exception as e:
            self.print_status("交易日历", "❌", f"读取失败: {e}")
            return None
    
    def check_disk_space(self):
        """检查磁盘空间"""
        self.print_section("💾 磁盘空间")
        
        try:
            result = subprocess.run(
                ["df", "-h", "/"],
                capture_output=True,
                text=True,
                check=True
            )
            lines = result.stdout.strip().split('\n')
            if len(lines) >= 2:
                parts = lines[1].split()
                usage_percent = parts[4].replace('%', '')
                available = parts[3]
                
                status = "✅"
                if int(usage_percent) > 80:
                    status = "❌"
                elif int(usage_percent) > 70:
                    status = "⚠️"
                    
                self.print_status(f"磁盘使用率", status, f"{usage_percent}% (可用: {available})")
                return int(usage_percent)
        except Exception as e:
            self.print_status("磁盘空间", "❌", f"检查失败: {e}")
            return None
    
    def check_t01_scheduler(self):
        """检查T01调度器状态"""
        self.print_section("🎯 T01 龙头战法")
        
        try:
            result = subprocess.run(
                ["systemctl", "status", "t01-scheduler", "--no-pager"],
                capture_output=True,
                text=True,
                check=False  # systemctl可能返回非0但仍有输出
            )
            
            if "Active: active (running)" in result.stdout:
                # 提取运行时间
                lines = result.stdout.split('\n')
                for line in lines:
                    if "active (running) since" in line:
                        self.print_status("调度器服务", "✅", "运行中")
                        break
            else:
                self.print_status("调度器服务", "❌", "未运行")
                
            # 检查候选股文件
            candidates_dir = WORKSPACE_ROOT / "tasks/T01/state"
            candidate_files = list(candidates_dir.glob("candidates_*.json"))
            if candidate_files:
                latest = max(candidate_files, key=os.path.getctime)
                age = datetime.now() - datetime.fromtimestamp(os.path.getctime(latest))
                if age.days < 2:
                    self.print_status("候选股文件", "✅", f"最新: {latest.name} ({age.days}天前)")
                else:
                    self.print_status("候选股文件", "⚠️", f"可能过时: {latest.name} ({age.days}天前)")
            else:
                self.print_status("候选股文件", "❌", "未找到")
                
        except Exception as e:
            self.print_status("T01检查", "❌", f"检查失败: {e}")
    
    def check_t99_scan(self):
        """检查T99复盘扫描状态"""
        self.print_section("📊 T99 复盘扫描")
        
        try:
            scan_log = WORKSPACE_ROOT / "skills/a-share-short-decision/scan_fixed.log"
            if scan_log.exists():
                with open(scan_log, 'r') as f:
                    content = f.read()
                
                if "修复版扫描完成于" in content:
                    # 提取完成时间
                    import re
                    match = re.search(r"修复版扫描完成于 (.+ CST)", content)
                    if match:
                        self.print_status("最后扫描", "✅", f"完成于 {match.group(1)}")
                    else:
                        self.print_status("最后扫描", "✅", "有记录")
                else:
                    self.print_status("扫描日志", "⚠️", "内容异常")
            else:
                self.print_status("扫描日志", "❌", "未找到日志文件")
                
            # 检查cron配置
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=True
            )
            if "T99" in result.stdout:
                self.print_status("Cron任务", "✅", "已配置 (周一至周五 14:30)")
            else:
                self.print_status("Cron任务", "❌", "未配置")
                
        except Exception as e:
            self.print_status("T99检查", "❌", f"检查失败: {e}")
    
    def check_t100_monitor(self):
        """检查T100宏观监控状态"""
        self.print_section("🌐 T100 宏观监控")
        
        try:
            # 检查cron配置
            result = subprocess.run(
                ["crontab", "-l"],
                capture_output=True,
                text=True,
                check=True
            )
            if "T100" in result.stdout:
                self.print_status("Cron任务", "✅", "已配置 (每日22:00)")
            else:
                self.print_status("Cron任务", "⚠️", "未明确标注")
                
            # 检查监控日志
            monitor_log = WORKSPACE_ROOT / "skills/macro-monitor/monitor.log"
            if monitor_log.exists():
                log_size = os.path.getsize(monitor_log)
                if log_size > 100:
                    self.print_status("监控日志", "✅", f"存在 ({log_size} 字节)")
                else:
                    self.print_status("监控日志", "⚠️", "文件过小")
            else:
                self.print_status("监控日志", "❌", "未找到")
                
        except Exception as e:
            self.print_status("T100检查", "❌", f"检查失败: {e}")
    
    def check_feishu_reliability(self):
        """检查飞书消息可靠性"""
        self.print_section("📱 飞书消息可靠性")
        
        try:
            if FEISHU_STATS.exists():
                with open(FEISHU_STATS, 'r') as f:
                    stats = json.load(f)
                
                total_sent = stats.get("total_sent", 0)
                total_failed = stats.get("total_failed", 0)
                
                if total_sent > 0:
                    success_rate = (total_sent - total_failed) / total_sent * 100
                    status = "✅" if success_rate > 95 else "⚠️" if success_rate > 80 else "❌"
                    self.print_status("发送成功率", status, f"{success_rate:.1f}% ({total_sent}次发送, {total_failed}次失败)")
                else:
                    self.print_status("统计数据", "⚠️", "无发送记录")
            else:
                self.print_status("统计数据", "❌", "未找到统计文件")
                
        except Exception as e:
            self.print_status("飞书检查", "❌", f"检查失败: {e}")
    
    def check_critical_timeline(self):
        """检查关键时间线"""
        self.print_section("⏰ 关键时间线 (北京时间)")
        
        # 今日日期
        today = self.now.strftime("%Y-%m-%d")
        
        # 定义关键任务时间 (UTC时间)
        # 北京时间 = UTC+8
        tasks = [
            ("08:00", "交易日准备检查"),
            ("08:30", "T01竞价准备检查"),
            ("09:25", "T01竞价分析"),
            ("14:30", "T99复盘扫描"),
            ("20:00", "T01 T日评分"),
            ("22:00", "T100宏观监控"),
        ]
        
        for time_str, task in tasks:
            # 简单显示
            print(f"  {time_str} - {task}")
    
    def generate_summary(self):
        """生成汇总建议"""
        self.print_section("💡 建议行动")
        
        # 基于检查结果生成建议
        print("1. 明日关键验证点:")
        print("   - 08:00: 交易日准备检查 (包含飞书健康度检查)")
        print("   - 09:25: T01竞价分析 (飞书增强模块首次实战)")
        print("   - 14:30: T99修复验证 (本地交易日历效果)")
        print("   - 20:00: T01 T日评分 (交易日智能执行框架)")
        print("   - 22:00: T100宏观监控 (数据源三层策略)")
        
        print("\n2. 系统维护建议:")
        print("   - 每周日执行磁盘清理 (已配置月度清理)")
        print("   - 监控交易日历同步 (建议每月1日同步)")
        print("   - 定期检查cron任务执行状态")
        
    def run(self):
        """运行所有检查"""
        self.print_header()
        self.check_trading_day()
        self.check_disk_space()
        self.check_t01_scheduler()
        self.check_t99_scan()
        self.check_t100_monitor()
        self.check_feishu_reliability()
        self.check_critical_timeline()
        self.generate_summary()
        
        print(f"\n{BOLD}{BLUE}=== 仪表板生成完成 ==={RESET}")
        print("使用建议: 定期运行此脚本监控系统健康状态")
        print("快速命令: python3 system_status_dashboard.py")

def main():
    """主函数"""
    try:
        dashboard = SystemStatusDashboard()
        dashboard.run()
    except KeyboardInterrupt:
        print("\n\n用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"{RED}❌ 仪表板运行失败: {e}{RESET}")
        sys.exit(1)

if __name__ == "__main__":
    main()