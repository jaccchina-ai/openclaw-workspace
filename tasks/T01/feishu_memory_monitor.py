#!/usr/bin/env python3
"""
T01 飞书消息发送内存监控器
监控Node.js内存使用情况，自动检测和报告内存溢出问题
"""

import os
import sys
import json
import time
import logging
import subprocess
import psutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/logs/feishu_memory_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class FeishuMemoryMonitor:
    """飞书消息发送内存监控器"""

    def __init__(self):
        self.log_file = Path('/root/.openclaw/workspace/logs/feishu_fallback.log')
        self.alert_threshold = 5  # 5分钟内错误次数阈值
        self.memory_threshold_mb = 1500  # 系统内存阈值
        self.check_interval = 60  # 检查间隔（秒）
        self.error_history: List[dict] = []

    def check_nodejs_memory_errors(self) -> Dict:
        """检查Node.js内存错误"""
        errors = []

        if not self.log_file.exists():
            return {'count': 0, 'errors': errors}

        try:
            with open(self.log_file, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 查找内存错误
            if 'FATAL ERROR' in content and 'JavaScript heap out of memory' in content:
                # 统计错误次数
                error_count = content.count('FATAL ERROR:')

                # 查找最近的错误时间
                lines = content.split('\n')
                recent_errors = []

                for i, line in enumerate(lines):
                    if 'FATAL ERROR:' in line:
                        # 尝试找到时间戳（在前几行）
                        timestamp = None
                        for j in range(max(0, i-10), i):
                            if lines[j].startswith('20') and '-' in lines[j]:
                                timestamp = lines[j][:19]
                                break

                        if not timestamp:
                            timestamp = datetime.now().isoformat()

                        recent_errors.append({
                            'timestamp': timestamp,
                            'type': 'heap_out_of_memory',
                            'line': i
                        })

                return {
                    'count': error_count,
                    'recent_errors': recent_errors[-10:],  # 最近10个错误
                    'needs_attention': error_count > 10
                }

        except Exception as e:
            logger.error(f"读取日志文件失败: {e}")

        return {'count': 0, 'errors': errors}

    def check_system_memory(self) -> Dict:
        """检查系统内存状态"""
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()

        return {
            'total_mb': memory.total / 1024 / 1024,
            'available_mb': memory.available / 1024 / 1024,
            'used_mb': memory.used / 1024 / 1024,
            'percent': memory.percent,
            'swap_used_mb': swap.used / 1024 / 1024,
            'swap_percent': swap.percent,
            'is_critical': memory.percent > 90 or memory.available / 1024 / 1024 < 200
        }

    def check_openclaw_processes(self) -> Dict:
        """检查openclaw相关进程"""
        processes = []

        for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'cmdline']):
            try:
                cmdline = ' '.join(proc.info['cmdline'] or [])
                if 'openclaw' in cmdline.lower() or 'openclaw' in proc.info['name'].lower():
                    processes.append({
                        'pid': proc.info['pid'],
                        'name': proc.info['name'],
                        'memory_mb': proc.info['memory_info'].rss / 1024 / 1024,
                        'cmdline': cmdline[:100]
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        total_memory = sum(p['memory_mb'] for p in processes)

        return {
            'count': len(processes),
            'processes': processes,
            'total_memory_mb': total_memory
        }

    def generate_report(self) -> str:
        """生成监控报告"""
        nodejs_errors = self.check_nodejs_memory_errors()
        system_memory = self.check_system_memory()
        openclaw_procs = self.check_openclaw_processes()

        report = f"""
📊 **T01飞书消息内存监控报告**
生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**1. Node.js内存错误统计**
- 总错误次数: {nodejs_errors.get('count', 0)}
- 需要关注: {'⚠️ 是' if nodejs_errors.get('needs_attention') else '✅ 否'}
- 最近错误数: {len(nodejs_errors.get('recent_errors', []))}

**2. 系统内存状态**
- 总内存: {system_memory['total_mb']:.0f} MB
- 可用内存: {system_memory['available_mb']:.0f} MB
- 使用率: {system_memory['percent']}%
- Swap使用: {system_memory['swap_used_mb']:.0f} MB ({system_memory['swap_percent']}%)
- 状态: {'🔴 危急' if system_memory['is_critical'] else '🟢 正常'}

**3. OpenClaw进程状态**
- 进程数量: {openclaw_procs['count']}
- 总内存占用: {openclaw_procs['total_memory_mb']:.1f} MB
"""

        if openclaw_procs['processes']:
            report += "\n**进程详情:**\n"
            for proc in openclaw_procs['processes'][:5]:  # 只显示前5个
                report += f"- PID {proc['pid']}: {proc['memory_mb']:.1f} MB\n"

        # 添加建议
        report += "\n**建议措施:**\n"

        if nodejs_errors.get('needs_attention'):
            report += "- 🔴 Node.js内存错误频繁，建议立即检查增强版发送器配置\n"

        if system_memory['is_critical']:
            report += "- 🔴 系统内存危急，建议重启服务或升级内存\n"
        elif system_memory['percent'] > 80:
            report += "- 🟡 系统内存使用率较高，建议监控\n"

        if openclaw_procs['total_memory_mb'] > 1000:
            report += "- 🟡 OpenClaw进程内存占用较高\n"

        report += "- ✅ 当前使用增强版发送器（直接API + CLI回退）\n"

        return report

    def run_check(self) -> bool:
        """运行一次检查"""
        logger.info("运行内存监控检查...")

        nodejs_errors = self.check_nodejs_memory_errors()
        system_memory = self.check_system_memory()

        # 记录到历史
        self.error_history.append({
            'timestamp': datetime.now().isoformat(),
            'nodejs_errors': nodejs_errors.get('count', 0),
            'memory_percent': system_memory['percent']
        })

        # 只保留最近100条记录
        if len(self.error_history) > 100:
            self.error_history = self.error_history[-100:]

        # 检查是否需要告警
        needs_alert = (
            nodejs_errors.get('needs_attention') or
            system_memory['is_critical']
        )

        if needs_alert:
            logger.warning("检测到内存问题，生成报告...")
            report = self.generate_report()
            print(report)

            # 保存报告
            report_file = Path(f"/root/.openclaw/workspace/logs/memory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(report_file, 'w', encoding='utf-8') as f:
                f.write(report)

            return False

        logger.info("内存检查通过")
        return True

    def run_continuous(self):
        """持续运行监控"""
        logger.info(f"启动持续监控，检查间隔: {self.check_interval}秒")

        while True:
            try:
                self.run_check()
                time.sleep(self.check_interval)
            except KeyboardInterrupt:
                logger.info("监控停止")
                break
            except Exception as e:
                logger.error(f"监控异常: {e}")
                time.sleep(self.check_interval)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description='T01飞书消息内存监控器')
    parser.add_argument('--mode', choices=['check', 'monitor'], default='check',
                        help='运行模式: check=单次检查, monitor=持续监控')
    parser.add_argument('--interval', type=int, default=60,
                        help='监控间隔（秒），默认60')

    args = parser.parse_args()

    monitor = FeishuMemoryMonitor()
    monitor.check_interval = args.interval

    if args.mode == 'monitor':
        monitor.run_continuous()
    else:
        report = monitor.generate_report()
        print(report)

        # 保存报告
        report_file = Path(f"/root/.openclaw/workspace/logs/memory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\n报告已保存到: {report_file}")


if __name__ == "__main__":
    main()
