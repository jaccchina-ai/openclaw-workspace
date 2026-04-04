#!/usr/bin/env python3
"""
Performance Guardian Module - T01 Phase 3

Monitors system health, performance metrics, and factor IC values.
Provides alerting capabilities for system anomalies.
"""

import os
import sys
import json
import logging
import psutil
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class AlertLevel(Enum):
    """告警级别枚举"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class Alert:
    """告警数据类"""
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    metric_name: str = ""
    metric_value: float = 0.0
    threshold: float = 0.0


class PerformanceGuardian:
    """
    性能守护器
    
    职责:
    1. 监控系统健康状态（CPU、内存、磁盘）
    2. 监控策略绩效指标
    3. 监控因子IC值
    4. 发送告警通知
    """
    
    DEFAULT_THRESHOLDS = {
        'memory_percent': 80.0,
        'cpu_percent': 80.0,
        'disk_percent': 85.0,
        'win_rate': 40.0,
        'max_drawdown': 20.0,
        'ic_value': 0.03,
    }
    
    def __init__(self, config_path: str = 'config.yaml',
                 performance_tracker=None,
                 ic_monitor=None):
        """
        初始化性能守护器
        
        Args:
            config_path: 配置文件路径
            performance_tracker: 绩效跟踪器实例
            ic_monitor: IC监控器实例
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        guardian_config = self.config.get('performance_guardian', {})
        self.thresholds = guardian_config.get('thresholds', self.DEFAULT_THRESHOLDS)
        self.alert_cooldown = guardian_config.get('alert_cooldown_minutes', 60)
        
        self.performance_tracker = performance_tracker
        self.ic_monitor = ic_monitor
        
        # 告警历史
        self.alert_history: List[Alert] = []
        self.last_alert_time: Dict[str, datetime] = {}
        
        # 状态文件
        self.status_file = Path('state/performance_guardian_status.json')
        self.status_file.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info("PerformanceGuardian初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"加载配置失败: {e}，使用默认配置")
            return {}
    
    def check_system_health(self) -> Dict[str, Any]:
        """
        检查系统健康状态
        
        Returns:
            系统健康状态
        """
        try:
            # 内存使用
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            
            # CPU使用
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # 磁盘使用
            disk = psutil.disk_usage('/')
            disk_percent = (disk.used / disk.total) * 100
            
            # 检查阈值
            status = 'healthy'
            issues = []
            
            if memory_percent > self.thresholds.get('memory_percent', 80):
                status = 'critical'
                issues.append(f"内存使用率过高: {memory_percent:.1f}%")
            
            if cpu_percent > self.thresholds.get('cpu_percent', 80):
                if status == 'healthy':
                    status = 'warning'
                issues.append(f"CPU使用率过高: {cpu_percent:.1f}%")
            
            if disk_percent > self.thresholds.get('disk_percent', 85):
                if status == 'healthy':
                    status = 'warning'
                issues.append(f"磁盘使用率过高: {disk_percent:.1f}%")
            
            return {
                'healthy': status == 'healthy',
                'status': status,
                'memory_percent': memory_percent,
                'memory_available_gb': memory.available / (1024**3),
                'cpu_percent': cpu_percent,
                'disk_percent': disk_percent,
                'disk_free_gb': disk.free / (1024**3),
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"系统健康检查失败: {e}")
            return {
                'healthy': False,
                'status': 'error',
                'error': str(e)
            }
    
    def check_performance(self) -> Dict[str, Any]:
        """
        检查策略绩效
        
        Returns:
            绩效检查结果
        """
        if self.performance_tracker is None:
            logger.warning("绩效跟踪器未设置")
            return {
                'healthy': True,
                'status': 'unknown',
                'message': '绩效跟踪器未设置'
            }
        
        try:
            perf_data = self.performance_tracker.calculate_portfolio_performance()
            
            if not perf_data or 'summary' not in perf_data:
                return {
                    'healthy': False,
                    'status': 'error',
                    'message': '无法获取绩效数据'
                }
            
            summary = perf_data['summary']
            win_rate = summary.get('win_rate_pct', 0)
            max_drawdown = summary.get('max_drawdown_pct', 0)
            profit_factor = summary.get('profit_factor', 0)
            
            status = 'healthy'
            issues = []
            
            if win_rate < self.thresholds.get('win_rate', 40):
                status = 'degraded'
                issues.append(f"胜率过低: {win_rate:.1f}%")
            
            if max_drawdown > self.thresholds.get('max_drawdown', 20):
                status = 'critical'
                issues.append(f"回撤过大: {max_drawdown:.1f}%")
            
            if profit_factor < 1.0:
                if status == 'healthy':
                    status = 'warning'
                issues.append(f"盈亏因子过低: {profit_factor:.2f}")
            
            return {
                'healthy': status == 'healthy',
                'status': status,
                'win_rate': win_rate,
                'max_drawdown': max_drawdown,
                'profit_factor': profit_factor,
                'total_trades': summary.get('total_trades', 0),
                'issues': issues
            }
            
        except Exception as e:
            logger.error(f"绩效检查失败: {e}")
            return {
                'healthy': False,
                'status': 'error',
                'message': str(e)
            }
    
    def check_factor_ic(self) -> Dict[str, Any]:
        """
        检查因子IC值
        
        Returns:
            IC检查结果
        """
        if self.ic_monitor is None:
            logger.warning("IC监控器未设置")
            return {
                'healthy': True,
                'status': 'unknown',
                'message': 'IC监控器未设置'
            }
        
        try:
            report = self.ic_monitor.get_latest_report()
            
            if not report:
                return {
                    'healthy': False,
                    'status': 'error',
                    'message': '无法获取IC报告'
                }
            
            # 获取失效因子
            invalid_factors = []
            warning_factors = []
            
            if hasattr(report, 'factors'):
                for factor in report.factors:
                    if not getattr(factor, 'is_valid', True):
                        invalid_factors.append(factor.factor_name)
                    elif getattr(factor, 'trend', 'stable') == 'declining':
                        warning_factors.append(factor.factor_name)
            
            # 检查是否有过多的失效因子
            total_factors = len(getattr(report, 'factors', []))
            invalid_ratio = len(invalid_factors) / total_factors if total_factors > 0 else 0
            
            status = 'healthy'
            if invalid_ratio > 0.3 or len(invalid_factors) >= 3:
                status = 'critical'
            elif invalid_ratio > 0.1 or len(invalid_factors) >= 1:
                status = 'degraded'
            
            return {
                'healthy': status == 'healthy',
                'status': status,
                'invalid_factors': invalid_factors,
                'warning_factors': warning_factors,
                'invalid_factors_count': len(invalid_factors),
                'total_factors': total_factors,
                'invalid_ratio': invalid_ratio
            }
            
        except Exception as e:
            logger.error(f"IC检查失败: {e}")
            return {
                'healthy': False,
                'status': 'error',
                'message': str(e)
            }
    
    def run_all_checks(self) -> Dict[str, Any]:
        """
        运行所有检查
        
        Returns:
            综合检查结果
        """
        system_health = self.check_system_health()
        performance = self.check_performance()
        factor_ic = self.check_factor_ic()
        
        # 综合判断
        all_healthy = all([
            system_health.get('healthy', False),
            performance.get('healthy', False),
            factor_ic.get('healthy', False)
        ])
        
        # 确定整体状态
        statuses = [
            system_health.get('status', 'unknown'),
            performance.get('status', 'unknown'),
            factor_ic.get('status', 'unknown')
        ]
        
        overall_status = 'healthy'
        if 'critical' in statuses:
            overall_status = 'critical'
        elif 'degraded' in statuses:
            overall_status = 'degraded'
        elif 'warning' in statuses:
            overall_status = 'warning'
        
        return {
            'healthy': all_healthy,
            'status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': {
                'system': system_health,
                'performance': performance,
                'factor_ic': factor_ic
            }
        }
    
    def send_feishu_alert(self, level: AlertLevel, title: str, 
                          message: str) -> bool:
        """
        发送飞书告警
        
        Args:
            level: 告警级别
            title: 告警标题
            message: 告警消息
            
        Returns:
            是否发送成功
        """
        try:
            # 检查冷却时间
            alert_key = f"{level.value}:{title}"
            last_time = self.last_alert_time.get(alert_key)
            
            if last_time:
                cooldown = timedelta(minutes=self.alert_cooldown)
                if datetime.now() - last_time < cooldown:
                    logger.info(f"告警冷却中，跳过: {alert_key}")
                    return True
            
            # 构建告警消息
            emoji_map = {
                AlertLevel.INFO: "ℹ️",
                AlertLevel.WARNING: "⚠️",
                AlertLevel.ERROR: "❌",
                AlertLevel.CRITICAL: "🚨"
            }
            
            full_message = f"""{emoji_map.get(level, '🔔')} **{title}**

**级别**: {level.value.upper()}
**时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{message}
"""
            
            # 发送消息（使用subprocess调用openclaw）
            import subprocess
            
            env = os.environ.copy()
            node_path = '/root/.nvm/versions/node/v22.22.0/bin'
            if node_path not in env.get('PATH', ''):
                env['PATH'] = node_path + ':' + env.get('PATH', '')
            
            # 从环境变量获取飞书用户ID
            feishu_user_id = os.environ.get('FEISHU_USER_ID', '')
            if not feishu_user_id:
                logger.error("FEISHU_USER_ID 环境变量未设置，无法发送告警")
                return False
            
            cmd = [
                '/root/.nvm/versions/node/v22.22.0/bin/openclaw',
                'message', 'send',
                '--channel', 'feishu',
                '--target', f'user:{feishu_user_id}',
                '--message', full_message
            ]
            
            result = subprocess.run(cmd, env=env, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                # 记录告警
                alert = Alert(
                    level=level,
                    title=title,
                    message=message,
                    timestamp=datetime.now()
                )
                self.alert_history.append(alert)
                self.last_alert_time[alert_key] = datetime.now()
                
                logger.info(f"告警已发送: {title}")
                return True
            else:
                logger.error(f"发送告警失败: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"发送告警异常: {e}")
            return False
    
    def log_alert(self, level: AlertLevel, title: str, message: str):
        """
        记录告警到日志
        
        Args:
            level: 告警级别
            title: 告警标题
            message: 告警消息
        """
        log_message = f"[{level.value.upper()}] {title}: {message}"
        
        if level == AlertLevel.CRITICAL:
            logger.critical(log_message)
        elif level == AlertLevel.ERROR:
            logger.error(log_message)
        elif level == AlertLevel.WARNING:
            logger.warning(log_message)
        else:
            logger.info(log_message)
        
        # 记录到历史
        alert = Alert(
            level=level,
            title=title,
            message=message,
            timestamp=datetime.now()
        )
        self.alert_history.append(alert)
    
    def save_status(self):
        """保存状态到文件"""
        try:
            status = self.run_all_checks()
            with open(self.status_file, 'w', encoding='utf-8') as f:
                json.dump(status, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存状态失败: {e}")
    
    def get_alert_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """
        获取告警历史
        
        Args:
            hours: 最近多少小时
            
        Returns:
            告警历史列表
        """
        cutoff = datetime.now() - timedelta(hours=hours)
        recent_alerts = [
            {
                'level': a.level.value,
                'title': a.title,
                'message': a.message,
                'timestamp': a.timestamp.isoformat()
            }
            for a in self.alert_history
            if a.timestamp > cutoff
        ]
        return recent_alerts


def main():
    """测试函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Performance Guardian 模块测试")
    print("="*60)
    
    guardian = PerformanceGuardian()
    
    # 测试系统健康检查
    print("\n1. 系统健康检查...")
    system = guardian.check_system_health()
    print(f"   健康: {system['healthy']}")
    print(f"   状态: {system['status']}")
    print(f"   内存: {system.get('memory_percent', 0):.1f}%")
    print(f"   CPU: {system.get('cpu_percent', 0):.1f}%")
    
    # 测试绩效检查
    print("\n2. 绩效检查...")
    perf = guardian.check_performance()
    print(f"   健康: {perf['healthy']}")
    print(f"   状态: {perf['status']}")
    
    # 测试IC检查
    print("\n3. IC检查...")
    ic = guardian.check_factor_ic()
    print(f"   健康: {ic['healthy']}")
    print(f"   状态: {ic['status']}")
    
    # 测试综合检查
    print("\n4. 综合检查...")
    all_checks = guardian.run_all_checks()
    print(f"   整体健康: {all_checks['healthy']}")
    print(f"   整体状态: {all_checks['status']}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == '__main__':
    main()
