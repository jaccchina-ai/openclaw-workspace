#!/usr/bin/env python3
"""
T01 调度器健康监控器
实时监控调度器进程状态，分析重启原因，自动恢复
"""

import os
import sys
import time
import json
import logging
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import psutil
import schedule

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/t01_health_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SchedulerHealthMonitor:
    """调度器健康监控器"""
    
    def __init__(self, scheduler_script='scheduler.py', config_file='config.yaml'):
        self.scheduler_script = scheduler_script
        self.config_file = config_file
        self.scheduler_dir = Path(__file__).parent
        
        # 状态文件
        self.status_file = Path('/tmp/t01_scheduler_status.json')
        self.crash_history_file = Path('/tmp/t01_scheduler_crashes.json')
        
        # 初始化状态
        self.init_status()
        
        # 崩溃阈值
        self.crash_threshold = 3  # 30分钟内崩溃3次触发警报
        self.restart_delay = 60   # 重启延迟(秒)
        
    def init_status(self):
        """初始化状态文件"""
        if not self.status_file.exists():
            status = {
                'start_time': datetime.now().isoformat(),
                'last_check': None,
                'process_pid': None,
                'running': False,
                'uptime_seconds': 0,
                'total_crashes': 0,
                'last_crash': None,
                'check_count': 0,
                'health_score': 100,
                'last_restart': None
            }
            self.save_status(status)
            
        if not self.crash_history_file.exists():
            self.save_crash_history([])
    
    def save_status(self, status):
        """保存状态"""
        with open(self.status_file, 'w') as f:
            json.dump(status, f, indent=2, default=str)
    
    def load_status(self):
        """加载状态"""
        if not self.status_file.exists():
            return {}
        with open(self.status_file, 'r') as f:
            return json.load(f)
    
    def save_crash_history(self, history):
        """保存崩溃历史"""
        with open(self.crash_history_file, 'w') as f:
            json.dump(history, f, indent=2, default=str)
    
    def load_crash_history(self):
        """加载崩溃历史"""
        if not self.crash_history_file.exists():
            return []
        with open(self.crash_history_file, 'r') as f:
            return json.load(f)
    
    def find_scheduler_process(self):
        """查找调度器进程"""
        for proc in psutil.process_iter(['pid', 'name', 'cmdline', 'create_time']):
            try:
                # 检查是否是Python调度器进程
                if proc.info['cmdline'] and 'scheduler.py' in ' '.join(proc.info['cmdline']):
                    # 确保是我们目录的调度器
                    cmd_str = ' '.join(proc.info['cmdline'])
                    if '--mode run' in cmd_str:
                        return proc.info['pid'], proc.info['create_time']
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                continue
        return None, None
    
    def analyze_crash_pattern(self):
        """分析崩溃模式"""
        history = self.load_crash_history()
        if len(history) < 2:
            return "数据不足，无法分析模式"
        
        # 计算时间间隔
        recent_crashes = history[-5:]  # 最近5次崩溃
        intervals = []
        for i in range(1, len(recent_crashes)):
            crash1 = datetime.fromisoformat(recent_crashes[i-1]['timestamp'])
            crash2 = datetime.fromisoformat(recent_crashes[i]['timestamp'])
            interval = (crash2 - crash1).total_seconds() / 60  # 分钟
            intervals.append(interval)
        
        if not intervals:
            return "无足够间隔数据"
        
        # 分析模式
        avg_interval = sum(intervals) / len(intervals)
        
        # 检查是否是定时重启（如30分钟模式）
        if 25 <= avg_interval <= 35:  # 接近30分钟
            return f"⚠️ 疑似定时重启模式: 平均 {avg_interval:.1f} 分钟重启一次"
        elif avg_interval < 5:  # 频繁崩溃
            return f"🚨 频繁崩溃: 平均 {avg_interval:.1f} 分钟崩溃一次"
        else:
            return f"🔄 不规则重启: 平均 {avg_interval:.1f} 分钟重启一次"
    
    def check_scheduler_health(self):
        """检查调度器健康状况"""
        status = self.load_status()
        
        # 查找进程
        pid, create_time = self.find_scheduler_process()
        current_time = time.time()
        
        if pid:
            # 进程存在
            status['process_pid'] = pid
            status['running'] = True
            
            # 计算运行时间
            if create_time:
                uptime_seconds = current_time - create_time
                status['uptime_seconds'] = uptime_seconds
                
                # 健康评分
                if uptime_seconds > 3600:  # 运行超过1小时
                    status['health_score'] = 95
                elif uptime_seconds > 1800:  # 运行超过30分钟
                    status['health_score'] = 85
                else:  # 运行时间短
                    status['health_score'] = 70
            
            logger.info(f"✅ 调度器运行中 (PID: {pid}, 运行时间: {status['uptime_seconds']:.0f}秒)")
            
        else:
            # 进程不存在
            if status['running']:
                # 从运行状态变为停止 -> 崩溃
                logger.warning(f"🚨 调度器进程消失，疑似崩溃 (原PID: {status['process_pid']})")
                
                # 记录崩溃
                crash_data = {
                    'timestamp': datetime.now().isoformat(),
                    'previous_pid': status['process_pid'],
                    'previous_uptime': status['uptime_seconds'],
                    'health_score_before': status['health_score']
                }
                history = self.load_crash_history()
                history.append(crash_data)
                if len(history) > 20:  # 保留最近20次
                    history = history[-20:]
                self.save_crash_history(history)
                
                # 更新状态
                status['total_crashes'] += 1
                status['last_crash'] = datetime.now().isoformat()
                status['health_score'] = max(30, status['health_score'] - 20)
                
                # 分析崩溃模式
                pattern = self.analyze_crash_pattern()
                logger.warning(f"崩溃模式分析: {pattern}")
                
                # 检查是否需要自动重启
                recent_crashes = [c for c in history if 
                                 (datetime.now() - datetime.fromisoformat(c['timestamp'])).total_seconds() < 1800]  # 30分钟内
                if len(recent_crashes) >= self.crash_threshold:
                    logger.error(f"🚨 30分钟内崩溃 {len(recent_crashes)} 次，达到阈值，发送警报")
                    # 这里可以添加飞书/钉钉通知
                
                # 自动重启逻辑
                if status['total_crashes'] % 2 == 0:  # 每2次崩溃自动重启一次
                    logger.info("触发自动重启逻辑")
                    self.restart_scheduler()
            
            status['process_pid'] = None
            status['running'] = False
            status['uptime_seconds'] = 0
        
        # 更新检查时间
        status['last_check'] = datetime.now().isoformat()
        status['check_count'] = status.get('check_count', 0) + 1
        
        self.save_status(status)
        
        # 返回健康报告
        return self.generate_health_report()
    
    def restart_scheduler(self):
        """重启调度器"""
        logger.info("🔄 尝试重启调度器...")
        
        # 切换到工作目录
        os.chdir(self.scheduler_dir)
        
        # 使用包装脚本重启（避免多个实例）
        try:
            result = subprocess.run(
                ['./scheduler_wrapper.sh'],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                logger.info("✅ 调度器重启成功")
                status = self.load_status()
                status['last_restart'] = datetime.now().isoformat()
                status['health_score'] = min(100, status['health_score'] + 10)
                self.save_status(status)
                return True
            else:
                logger.error(f"❌ 调度器重启失败: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("❌ 调度器启动超时")
            return False
        except Exception as e:
            logger.error(f"❌ 调度器重启异常: {e}")
            return False
    
    def generate_health_report(self):
        """生成健康报告"""
        status = self.load_status()
        history = self.load_crash_history()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'process_running': status['running'],
            'process_pid': status['process_pid'],
            'uptime_minutes': round(status['uptime_seconds'] / 60, 1) if status['running'] else 0,
            'total_crashes': status['total_crashes'],
            'health_score': status['health_score'],
            'last_crash': status['last_crash'],
            'crash_pattern': self.analyze_crash_pattern(),
            'recent_crashes': len([c for c in history if 
                                  (datetime.now() - datetime.fromisoformat(c['timestamp'])).total_seconds() < 1800]),
            'check_count': status['check_count'],
            'recommendation': self.generate_recommendation(status, history)
        }
        
        return report
    
    def generate_recommendation(self, status, history):
        """生成建议"""
        if not status['running']:
            if status['total_crashes'] == 0:
                return "建议: 启动调度器"
            else:
                return f"建议: 立即重启调度器（已崩溃 {status['total_crashes']} 次）"
        
        # 运行中但健康评分低
        if status['health_score'] < 50:
            return "建议: 监控高频率崩溃，考虑代码优化"
        
        # 最近有崩溃
        recent_crashes = [c for c in history if 
                         (datetime.now() - datetime.fromisoformat(c['timestamp'])).total_seconds() < 3600]
        if recent_crashes:
            return f"建议: 关注最近 {len(recent_crashes)} 次崩溃"
        
        return "状态良好，继续监控"
    
    def run_monitor(self, interval_seconds=300):
        """运行监控器主循环（每5分钟检查一次）"""
        logger.info(f"🚀 启动T01调度器健康监控器 (检查间隔: {interval_seconds}秒)")
        
        # 立即检查一次
        report = self.check_scheduler_health()
        logger.info(f"初始检查报告: {json.dumps(report, indent=2, default=str)}")
        
        # 调度定期检查
        schedule.every(interval_seconds).seconds.do(self.monitoring_job)
        
        # 主循环
        try:
            while True:
                schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("监控器被用户中断")
        except Exception as e:
            logger.error(f"监控器异常: {e}", exc_info=True)
    
    def monitoring_job(self):
        """监控任务"""
        try:
            report = self.check_scheduler_health()
            
            # 只记录重要事件
            if not report['process_running']:
                logger.warning(f"⚠️ 调度器未运行: {report['recommendation']}")
            elif report['health_score'] < 60:
                logger.warning(f"⚠️ 调度器健康评分低 ({report['health_score']}): {report['crash_pattern']}")
            
            # 每小时记录一次详细报告
            if int(time.time()) % 3600 < 5:  # 每小时开头5秒内
                logger.info(f"每小时健康报告: {json.dumps(report, indent=2, default=str)}")
                
        except Exception as e:
            logger.error(f"监控任务异常: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='T01调度器健康监控器')
    parser.add_argument('--mode', choices=['monitor', 'check', 'restart', 'report'],
                       default='check', help='运行模式')
    parser.add_argument('--interval', type=int, default=300, help='监控间隔(秒)')
    
    args = parser.parse_args()
    
    monitor = SchedulerHealthMonitor()
    
    if args.mode == 'monitor':
        monitor.run_monitor(args.interval)
    elif args.mode == 'check':
        report = monitor.check_scheduler_health()
        print(json.dumps(report, indent=2, default=str))
    elif args.mode == 'restart':
        monitor.restart_scheduler()
    elif args.mode == 'report':
        report = monitor.generate_health_report()
        print(json.dumps(report, indent=2, default=str))


if __name__ == "__main__":
    main()