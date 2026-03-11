#!/usr/bin/env python3
"""
竞价分析监控系统
实时监控 T01 竞价分析过程，提供状态报告和自动修复
"""

import os
import sys
import time
import json
import datetime
import subprocess
import threading
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

class AuctionMonitor:
    def __init__(self):
        self.base_dir = Path(__file__).parent
        self.log_file = self.base_dir / "t01_limit_up.log"
        self.state_dir = self.base_dir / "state"
        self.monitor_running = False
        
    def check_scheduler_status(self):
        """检查调度器进程状态"""
        import psutil
        scheduler_pids = []
        
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info['cmdline']
                if cmdline and 'scheduler.py' in ' '.join(cmdline):
                    scheduler_pids.append(proc.info['pid'])
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue
        
        return {
            "running": len(scheduler_pids) > 0,
            "pids": scheduler_pids,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def check_candidate_files(self):
        """检查候选股票文件"""
        candidate_files = list(self.state_dir.glob("candidates_*.json"))
        if not candidate_files:
            return {
                "status": "missing",
                "count": 0,
                "latest": None,
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        # 按修改时间排序
        candidate_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_file = candidate_files[0]
        
        try:
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            candidates = data.get('candidates', [])
            t_date = data.get('t_date', '未知')
            t1_date = data.get('t1_date', '未知')
            
            return {
                "status": "valid",
                "count": len(candidates),
                "latest": str(latest_file),
                "t_date": t_date,
                "t1_date": t1_date,
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "invalid",
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def check_today_auction_status(self):
        """检查今日竞价分析状态"""
        today = datetime.datetime.now().strftime('%Y%m%d')
        
        # 检查是否有今日的竞价结果文件
        result_files = list(self.state_dir.glob(f"*{today}*.json"))
        result_files = [f for f in result_files if "result" in f.name.lower() or "auction" in f.name.lower()]
        
        # 检查日志中的今日记录
        log_entries = []
        if self.log_file.exists():
            try:
                with open(self.log_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                today_lines = [line for line in lines if today in line]
                auction_lines = [line for line in today_lines if "竞价" in line or "auction" in line.lower()]
                
                for line in auction_lines[-5:]:  # 取最近5行
                    log_entries.append(line.strip())
            except Exception as e:
                log_entries.append(f"读取日志失败: {e}")
        
        return {
            "today": today,
            "result_files": len(result_files),
            "log_entries": len(auction_lines) if 'auction_lines' in locals() else 0,
            "recent_logs": log_entries[-3:],  # 最近3条
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def check_auction_window(self):
        """检查当前是否在竞价窗口"""
        now = datetime.datetime.now()
        current_time = now.strftime("%H:%M")
        
        # 竞价窗口: 09:15-09:29
        is_in_window = False
        minutes_to_window = 0
        
        if now.hour == 9:
            if now.minute >= 15 and now.minute <= 29:
                is_in_window = True
                minutes_remaining = 29 - now.minute
            elif now.minute < 15:
                minutes_to_window = 15 - now.minute
            else:
                minutes_to_window = (24 * 60) - (now.hour * 60 + now.minute) + (9 * 60 + 15)
        elif now.hour < 9:
            minutes_to_window = (9 * 60 + 15) - (now.hour * 60 + now.minute)
        else:
            minutes_to_window = (24 * 60) - (now.hour * 60 + now.minute) + (9 * 60 + 15)
        
        return {
            "current_time": current_time,
            "in_auction_window": is_in_window,
            "minutes_to_window": minutes_to_window,
            "timestamp": datetime.datetime.now().isoformat()
        }
    
    def trigger_manual_auction(self):
        """手动触发竞价分析"""
        today = datetime.datetime.now().strftime('%Y%m%d')
        
        # 查找最新的候选文件
        candidate_files = list(self.state_dir.glob("candidates_*.json"))
        if not candidate_files:
            return {
                "success": False,
                "error": "未找到候选股票文件",
                "timestamp": datetime.datetime.now().isoformat()
            }
        
        candidate_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        latest_candidate = candidate_files[0]
        
        try:
            cmd = [
                "python3", "main.py", "t1-auction",
                "--date", today,
                "--candidates", str(latest_candidate)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=self.base_dir,
                capture_output=True,
                text=True,
                timeout=300  # 5分钟超时
            )
            
            success = result.returncode == 0
            
            return {
                "success": success,
                "returncode": result.returncode,
                "stdout": result.stdout[-500:] if result.stdout else "",  # 最后500字符
                "stderr": result.stderr[-500:] if result.stderr else "",
                "command": " ".join(cmd),
                "timestamp": datetime.datetime.now().isoformat()
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "执行超时 (5分钟)",
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def monitor_logs(self, duration_seconds=300):
        """实时监控日志文件"""
        if not self.log_file.exists():
            return {"error": "日志文件不存在"}
        
        start_time = time.time()
        new_entries = []
        
        # 获取当前文件大小
        initial_size = self.log_file.stat().st_size
        
        print(f"开始监控日志 {self.log_file} (持续{duration_seconds}秒)...")
        print("=" * 60)
        
        try:
            while time.time() - start_time < duration_seconds:
                current_size = self.log_file.stat().st_size
                
                if current_size > initial_size:
                    # 读取新增内容
                    with open(self.log_file, 'r', encoding='utf-8') as f:
                        f.seek(initial_size)
                        new_content = f.read()
                        initial_size = current_size
                        
                        if new_content:
                            lines = new_content.strip().split('\n')
                            for line in lines:
                                if line.strip():
                                    timestamp = datetime.datetime.now().strftime("%H:%M:%S")
                                    print(f"[{timestamp}] {line}")
                                    new_entries.append(line)
                
                time.sleep(2)  # 每2秒检查一次
            
            print("=" * 60)
            print(f"监控结束，共捕获 {len(new_entries)} 条新日志")
            
            return {
                "duration_seconds": duration_seconds,
                "new_entries_count": len(new_entries),
                "new_entries_sample": new_entries[-10:] if new_entries else [],
                "timestamp": datetime.datetime.now().isoformat()
            }
        except KeyboardInterrupt:
            print("\n监控被用户中断")
            return {
                "interrupted": True,
                "duration_seconds": time.time() - start_time,
                "new_entries_count": len(new_entries),
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "error": str(e),
                "timestamp": datetime.datetime.now().isoformat()
            }
    
    def generate_status_report(self):
        """生成状态报告"""
        print("=" * 60)
        print("T01 竞价分析监控报告")
        print(f"生成时间: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        report = {
            "timestamp": datetime.datetime.now().isoformat(),
            "checks": {}
        }
        
        # 执行检查
        report["checks"]["scheduler_status"] = self.check_scheduler_status()
        report["checks"]["candidate_files"] = self.check_candidate_files()
        report["checks"]["today_auction"] = self.check_today_auction_status()
        report["checks"]["auction_window"] = self.check_auction_window()
        
        # 打印报告
        scheduler_status = report["checks"]["scheduler_status"]
        print(f"📊 调度器状态: {'✅ 运行中' if scheduler_status['running'] else '❌ 未运行'}")
        if scheduler_status['running']:
            print(f"   进程PID: {scheduler_status['pids']}")
        
        candidate_status = report["checks"]["candidate_files"]
        if candidate_status["status"] == "valid":
            print(f"📋 候选文件: ✅ 有效 ({candidate_status['count']}只股票)")
            print(f"   最新文件: {Path(candidate_status['latest']).name}")
            print(f"   生成日期: T日={candidate_status['t_date']}, T+1日={candidate_status['t1_date']}")
        else:
            print(f"📋 候选文件: ❌ {candidate_status['status']}")
            if "error" in candidate_status:
                print(f"   错误: {candidate_status['error']}")
        
        today_auction = report["checks"]["today_auction"]
        print(f"📅 今日竞价状态: {today_auction['today']}")
        if today_auction['result_files'] > 0:
            print(f"   结果文件: ✅ {today_auction['result_files']}个")
        if today_auction['log_entries'] > 0:
            print(f"   日志记录: 📝 {today_auction['log_entries']}条")
            if today_auction['recent_logs']:
                print(f"   最近记录:")
                for log in today_auction['recent_logs']:
                    print(f"     - {log}")
        
        window_status = report["checks"]["auction_window"]
        print(f"⏰ 竞价窗口状态:")
        if window_status['in_auction_window']:
            print(f"   🚨 当前在竞价窗口内! ({window_status['current_time']})")
            print(f"   距离窗口结束: {29 - datetime.datetime.now().minute}分钟")
        else:
            print(f"   当前时间: {window_status['current_time']}")
            if window_status['minutes_to_window'] > 60:
                hours = window_status['minutes_to_window'] // 60
                minutes = window_status['minutes_to_window'] % 60
                print(f"   距离下次竞价窗口: {hours}小时{minutes}分钟")
            else:
                print(f"   距离下次竞价窗口: {window_status['minutes_to_window']}分钟")
        
        # 建议操作
        print("\n💡 建议操作:")
        if not scheduler_status['running']:
            print("  • 启动调度器: cd /root/.openclaw/workspace/tasks/T01 && python3 scheduler.py --mode run &")
        
        if candidate_status['status'] != 'valid':
            print("  • 生成候选股票: cd /root/.openclaw/workspace/tasks/T01 && python3 main.py t-day")
        
        if window_status['in_auction_window']:
            print("  • 🚨 立即执行竞价分析:")
            print("    cd /root/.openclaw/workspace/tasks/T01")
            print("    python3 auction_monitor.py --trigger-now")
        
        # 保存报告
        report_file = self.base_dir / "auction_monitor_report.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2, default=str)
        
        print(f"\n📁 详细报告保存到: {report_file}")
        
        return report

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='T01竞价分析监控系统')
    parser.add_argument('--status', action='store_true', help='生成状态报告')
    parser.add_argument('--monitor', type=int, default=300, help='监控日志时长(秒)，默认300秒')
    parser.add_argument('--trigger-now', action='store_true', help='立即触发竞价分析')
    parser.add_argument('--check-only', action='store_true', help='仅检查不监控')
    
    args = parser.parse_args()
    
    monitor = AuctionMonitor()
    
    if args.trigger_now:
        print("🚀 立即触发竞价分析...")
        result = monitor.trigger_manual_auction()
        print(f"执行结果: {'成功' if result.get('success') else '失败'}")
        if not result.get('success'):
            print(f"错误: {result.get('error', '未知错误')}")
        if result.get('stdout'):
            print(f"输出:\n{result['stdout'][-1000:]}")
        return
    
    if args.status or (not args.monitor and not args.trigger_now):
        monitor.generate_status_report()
    
    if args.monitor > 0 and not args.check_only:
        # 先显示状态报告
        monitor.generate_status_report()
        print("\n" + "=" * 60)
        # 然后开始监控
        monitor.monitor_logs(args.monitor)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n🛑 监控被用户中断")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 监控系统异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)