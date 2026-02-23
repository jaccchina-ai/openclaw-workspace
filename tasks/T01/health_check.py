#!/usr/bin/env python3
"""
T01系统健康检查脚本
定期检查系统状态，确保正常运行
"""

import sys
import os
import yaml
import json
import logging
import psutil
from pathlib import Path
from datetime import datetime, timedelta
import pandas as pd
import tushare as ts

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SystemHealthChecker:
    """系统健康检查器"""
    
    def __init__(self, config_path='config.yaml'):
        self.config_path = config_path
        self.config = None
        self.pro = None
        
    def load_config(self) -> bool:
        """加载配置文件"""
        try:
            if not Path(self.config_path).exists():
                logger.error(f"配置文件不存在: {self.config_path}")
                return False
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                self.config = yaml.safe_load(f)
            
            return True
            
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            return False
    
    def check_tushare_connection(self) -> dict:
        """检查tushare连接状态"""
        try:
            api_key = self.config['api']['api_key']
            ts.set_token(api_key)
            self.pro = ts.pro_api()
            
            # 测试连接
            cal_df = self.pro.trade_cal(
                exchange='SSE',
                start_date='20260213',
                end_date='20260213',
                fields='cal_date,is_open'
            )
            
            return {
                'status': 'healthy',
                'message': 'tushare连接正常',
                'test_date': '2026-02-13',
                'is_trading_day': cal_df.iloc[0]['is_open'] == 1 if not cal_df.empty else False
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'tushare连接失败: {e}'
            }
    
    def check_log_files(self) -> dict:
        """检查日志文件状态"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return {
                'status': 'warning',
                'message': '日志目录不存在',
                'log_files': 0
            }
        
        log_files = list(log_dir.glob("*.log"))
        total_size = sum(f.stat().st_size for f in log_files)
        
        # 检查最新日志文件
        latest_log = None
        latest_time = None
        for log_file in log_files:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if latest_time is None or mtime > latest_time:
                latest_time = mtime
                latest_log = log_file
        
        # 检查日志文件是否过大（超过100MB）
        size_warning = total_size > 100 * 1024 * 1024  # 100MB
        
        return {
            'status': 'healthy' if not size_warning else 'warning',
            'message': '日志文件状态正常' if not size_warning else '日志文件总大小超过100MB',
            'log_files': len(log_files),
            'total_size_mb': total_size / (1024 * 1024),
            'latest_log': latest_log.name if latest_log else None,
            'latest_update': latest_time.isoformat() if latest_time else None
        }
    
    def check_disk_space(self) -> dict:
        """检查磁盘空间"""
        try:
            usage = psutil.disk_usage('/')
            free_gb = usage.free / (1024**3)
            free_percent = usage.free / usage.total * 100
            
            status = 'healthy'
            if free_percent < 10:
                status = 'critical'
                message = f'磁盘空间严重不足: {free_gb:.1f}GB ({free_percent:.1f}%) 可用'
            elif free_percent < 20:
                status = 'warning'
                message = f'磁盘空间不足: {free_gb:.1f}GB ({free_percent:.1f}%) 可用'
            else:
                message = f'磁盘空间充足: {free_gb:.1f}GB ({free_percent:.1f}%) 可用'
            
            return {
                'status': status,
                'message': message,
                'free_gb': free_gb,
                'free_percent': free_percent,
                'total_gb': usage.total / (1024**3)
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'message': f'磁盘空间检查失败: {e}'
            }
    
    def check_memory_usage(self) -> dict:
        """检查内存使用"""
        try:
            memory = psutil.virtual_memory()
            used_percent = memory.percent
            
            status = 'healthy'
            if used_percent > 90:
                status = 'critical'
                message = f'内存使用率过高: {used_percent:.1f}%'
            elif used_percent > 80:
                status = 'warning'
                message = f'内存使用率偏高: {used_percent:.1f}%'
            else:
                message = f'内存使用率正常: {used_percent:.1f}%'
            
            return {
                'status': status,
                'message': message,
                'used_percent': used_percent,
                'available_gb': memory.available / (1024**3),
                'total_gb': memory.total / (1024**3)
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'message': f'内存检查失败: {e}'
            }
    
    def check_recent_tasks(self) -> dict:
        """检查最近任务运行状态"""
        log_dir = Path("logs")
        if not log_dir.exists():
            return {
                'status': 'warning',
                'message': '日志目录不存在，无法检查任务状态'
            }
        
        # 查找最近24小时的日志条目
        scheduler_log = log_dir / "t01_scheduler.log"
        if not scheduler_log.exists():
            return {
                'status': 'warning',
                'message': '调度器日志文件不存在'
            }
        
        try:
            with open(scheduler_log, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # 获取最近24小时的日志
            cutoff_time = datetime.now() - timedelta(hours=24)
            recent_logs = []
            
            for line in lines[-1000:]:  # 检查最后1000行
                try:
                    # 解析日志时间（简单实现）
                    if ' - ' in line:
                        time_str = line.split(' - ')[0]
                        log_time = datetime.fromisoformat(time_str.replace(' ', 'T'))
                        if log_time > cutoff_time:
                            recent_logs.append(line)
                except:
                    continue
            
            # 分析日志内容
            has_errors = any('ERROR' in log or 'error' in log.lower() for log in recent_logs)
            has_warnings = any('WARNING' in log or 'warning' in log.lower() for log in recent_logs)
            has_success = any('成功评分' in log or '完成' in log for log in recent_logs)
            
            message_parts = []
            if has_errors:
                message_parts.append('有错误')
            if has_warnings:
                message_parts.append('有警告')
            if has_success:
                message_parts.append('有成功记录')
            
            message = '，'.join(message_parts) if message_parts else '无近期记录'
            
            status = 'healthy'
            if has_errors:
                status = 'unhealthy'
            elif has_warnings:
                status = 'warning'
            
            return {
                'status': status,
                'message': message,
                'recent_logs_count': len(recent_logs),
                'has_errors': has_errors,
                'has_warnings': has_warnings,
                'has_success': has_success
            }
            
        except Exception as e:
            return {
                'status': 'unknown',
                'message': f'日志分析失败: {e}'
            }
    
    def check_candidate_files(self) -> dict:
        """检查候选股票文件"""
        candidate_file = Path("state/candidates_20260213_to_20260224.json")
        
        if not candidate_file.exists():
            return {
                'status': 'warning',
                'message': '候选股票文件不存在',
                'file_exists': False
            }
        
        try:
            with open(candidate_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            candidates = data.get('candidates', [])
            generated_at = data.get('generated_at', '')
            
            # 检查文件生成时间（不超过7天）
            is_recent = True
            if generated_at:
                try:
                    file_time = datetime.fromisoformat(generated_at)
                    if datetime.now() - file_time > timedelta(days=7):
                        is_recent = False
                except:
                    pass
            
            return {
                'status': 'healthy' if is_recent else 'warning',
                'message': f'候选股票文件正常 ({len(candidates)}只股票)' if is_recent else f'候选股票文件较旧 ({len(candidates)}只股票)',
                'file_exists': True,
                'candidate_count': len(candidates),
                'generated_at': generated_at,
                'is_recent': is_recent
            }
            
        except Exception as e:
            return {
                'status': 'unhealthy',
                'message': f'候选股票文件读取失败: {e}',
                'file_exists': True
            }
    
    def check_api_quota(self) -> dict:
        """检查API配额（模拟）"""
        # tushare没有直接的配额查询接口，这里模拟检查
        # 实际可以检查调用频率或错误次数
        return {
            'status': 'healthy',
            'message': 'API配额检查通过（模拟）',
            'note': 'tushare配额需在官网查看'
        }
    
    def run_all_checks(self) -> dict:
        """运行所有健康检查"""
        if not self.load_config():
            return {
                'overall_status': 'critical',
                'message': '配置加载失败',
                'checks': []
            }
        
        checks = [
            ('tushare连接', self.check_tushare_connection),
            ('日志文件', self.check_log_files),
            ('磁盘空间', self.check_disk_space),
            ('内存使用', self.check_memory_usage),
            ('最近任务', self.check_recent_tasks),
            ('候选文件', self.check_candidate_files),
            ('API配额', self.check_api_quota),
        ]
        
        results = []
        overall_status = 'healthy'
        
        for check_name, check_func in checks:
            try:
                result = check_func()
                result['name'] = check_name
                results.append(result)
                
                # 更新整体状态（critical > unhealthy > warning > healthy）
                status_order = {'critical': 4, 'unhealthy': 3, 'warning': 2, 'healthy': 1, 'unknown': 0}
                if status_order.get(result['status'], 0) > status_order.get(overall_status, 0):
                    overall_status = result['status']
                    
            except Exception as e:
                error_result = {
                    'name': check_name,
                    'status': 'critical',
                    'message': f'检查异常: {e}'
                }
                results.append(error_result)
                overall_status = 'critical'
        
        return {
            'overall_status': overall_status,
            'timestamp': datetime.now().isoformat(),
            'checks': results
        }
    
    def generate_report(self, check_results: dict) -> str:
        """生成健康检查报告"""
        report_parts = []
        
        # 标题
        report_parts.append("="*60)
        report_parts.append("📊 T01系统健康检查报告")
        report_parts.append("="*60)
        report_parts.append(f"生成时间: {check_results['timestamp']}")
        report_parts.append(f"整体状态: {self._status_icon(check_results['overall_status'])} {check_results['overall_status']}")
        report_parts.append("")
        
        # 检查详情
        for check in check_results['checks']:
            icon = self._status_icon(check['status'])
            report_parts.append(f"{icon} {check['name']}: {check['status']}")
            report_parts.append(f"   {check['message']}")
            
            # 添加额外信息
            for key, value in check.items():
                if key not in ['name', 'status', 'message'] and value is not None:
                    if isinstance(value, (int, float)):
                        report_parts.append(f"   {key}: {value}")
                    elif isinstance(value, str) and len(value) < 50:
                        report_parts.append(f"   {key}: {value}")
            
            report_parts.append("")
        
        # 建议
        report_parts.append("="*60)
        report_parts.append("💡 建议")
        report_parts.append("="*60)
        
        if check_results['overall_status'] == 'healthy':
            report_parts.append("✅ 系统状态良好，无需操作")
        elif check_results['overall_status'] == 'warning':
            report_parts.append("⚠️  系统有警告，建议检查相关项")
        elif check_results['overall_status'] == 'unhealthy':
            report_parts.append("❌ 系统有问题，需要立即检查")
        elif check_results['overall_status'] == 'critical':
            report_parts.append("🚨 系统有严重问题，需要立即处理")
        
        report_parts.append("")
        report_parts.append("📋 日常维护建议:")
        report_parts.append("1. 定期清理日志文件 (logs/ 目录)")
        report_parts.append("2. 监控磁盘空间使用")
        report_parts.append("3. 检查tushare API调用频率")
        report_parts.append("4. 验证候选股票文件的时效性")
        report_parts.append("")
        report_parts.append("🔄 健康检查可定期运行:")
        report_parts.append("  python health_check.py")
        report_parts.append("  # 或添加到cron: 0 8 * * * cd /path/to/tasks/T01 && python health_check.py")
        
        return "\n".join(report_parts)
    
    def _status_icon(self, status: str) -> str:
        """获取状态图标"""
        icons = {
            'healthy': '✅',
            'warning': '⚠️ ',
            'unhealthy': '❌',
            'critical': '🚨',
            'unknown': '❓'
        }
        return icons.get(status, '❓')
    
    def save_report(self, report_text: str):
        """保存报告"""
        report_dir = Path("state")
        report_dir.mkdir(exist_ok=True)
        
        report_file = report_dir / "health_check_report.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        logger.info(f"健康检查报告已保存: {report_file}")
        return report_file


def main():
    """主函数"""
    print("🔍 T01系统健康检查开始...")
    
    checker = SystemHealthChecker()
    
    try:
        # 运行检查
        check_results = checker.run_all_checks()
        
        # 生成报告
        report_text = checker.generate_report(check_results)
        
        # 打印报告
        print("\n" + report_text)
        
        # 保存报告
        report_file = checker.save_report(report_text)
        
        # 根据状态返回退出码
        if check_results['overall_status'] in ['healthy', 'warning']:
            print(f"\n📝 详细报告已保存: {report_file}")
            sys.exit(0)
        else:
            print(f"\n❌ 系统健康检查发现严重问题，请查看报告: {report_file}")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"健康检查过程异常: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # 检查psutil是否安装
    try:
        import psutil
    except ImportError:
        print("❌ 需要安装psutil模块: pip install psutil")
        sys.exit(1)
    
    main()