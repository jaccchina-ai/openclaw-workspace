#!/usr/bin/env python3
"""
T01 T日评分实时监控器
监控20:00 T日评分任务执行，特别关注新舆情分析系统性能
"""

import os
import sys
import time
import json
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/.openclaw/workspace/tasks/T01/t_day_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class TDayMonitor:
    """T日评分监控器"""
    
    def __init__(self):
        """初始化监控器"""
        self.t01_dir = Path(__file__).parent
        self.log_file = self.t01_dir / "t01_limit_up.log"
        self.scheduler_pid = None
        self.monitor_start_time = datetime.now()
        self.metrics = {
            'start_time': self.monitor_start_time.isoformat(),
            't_day_task_started': False,
            't_day_task_completed': False,
            't_day_task_error': False,
            'sentiment_analysis_used': False,
            'chinese_crawler_used': False,
            'tavily_fallback_used': False,
            'chinese_news_count': 0,
            'english_news_count': 0,
            'sentiment_scores': [],
            'degradation_triggered': False,
            'execution_time': None,
            'error_messages': []
        }
        
        logger.info("T日评分监控器初始化完成")
        logger.info(f"监控开始时间: {self.monitor_start_time}")
        logger.info(f"日志文件: {self.log_file}")
    
    def check_scheduler_process(self) -> bool:
        """检查T01调度器进程状态"""
        try:
            result = subprocess.run(
                ['pgrep', '-f', 'python.*scheduler.py'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                pids = result.stdout.strip().split('\n')
                self.scheduler_pid = pids[0] if pids else None
                logger.info(f"T01调度器进程运行中 (PID: {self.scheduler_pid})")
                return True
            else:
                logger.warning("T01调度器进程未找到")
                return False
        except Exception as e:
            logger.error(f"检查调度器进程失败: {e}")
            return False
    
    def monitor_log_file(self, lines_to_check: int = 100) -> Dict[str, Any]:
        """监控日志文件，提取关键信息"""
        log_metrics = {
            't_day_started': False,
            't_day_completed': False,
            'sentiment_analysis_detected': False,
            'chinese_crawler_detected': False,
            'tavily_fallback_detected': False,
            'error_count': 0,
            'warning_count': 0,
            'recent_lines': []
        }
        
        if not self.log_file.exists():
            logger.warning(f"日志文件不存在: {self.log_file}")
            return log_metrics
        
        try:
            # 读取最后N行日志
            with open(self.log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()[-lines_to_check:]
            
            log_metrics['recent_lines'] = lines[-10:]  # 保存最后10行供分析
            
            for line in lines:
                line_lower = line.lower()
                
                # 检查T日评分开始
                if '执行t日评分任务' in line or 't-day' in line_lower:
                    log_metrics['t_day_started'] = True
                    logger.info("检测到T日评分任务开始")
                
                # 检查T日评分完成
                if '✅ t日评分任务完成' in line or 't日评分完成' in line_lower:
                    log_metrics['t_day_completed'] = True
                    logger.info("检测到T日评分任务完成")
                
                # 检查舆情分析
                if '舆情分析' in line or 'sentiment' in line_lower:
                    log_metrics['sentiment_analysis_detected'] = True
                    
                    # 检查是否使用中文爬虫
                    if '中文爬虫' in line or 'chinese crawler' in line_lower:
                        log_metrics['chinese_crawler_detected'] = True
                        logger.info("检测到中文新闻爬虫使用")
                    
                    # 检查是否降级到Tavily
                    if 'tavily' in line_lower or '降级' in line:
                        log_metrics['tavily_fallback_detected'] = True
                        logger.info("检测到Tavily降级使用")
                
                # 检查新闻数量统计
                news_match = re.search(r'找到\s*(\d+)\s*条新闻', line)
                if news_match:
                    news_count = int(news_match.group(1))
                    if '中文' in line:
                        self.metrics['chinese_news_count'] = news_count
                    elif '英文' in line:
                        self.metrics['english_news_count'] = news_count
                
                # 检查情感评分
                score_match = re.search(r'舆情评分.*?(\d+\.\d+)', line)
                if score_match:
                    score = float(score_match.group(1))
                    self.metrics['sentiment_scores'].append(score)
                
                # 统计错误和警告
                if 'error' in line_lower or '失败' in line:
                    log_metrics['error_count'] += 1
                    if '降级' in line or 'fallback' in line_lower:
                        self.metrics['degradation_triggered'] = True
                
                if 'warning' in line_lower or '警告' in line:
                    log_metrics['warning_count'] += 1
            
            return log_metrics
            
        except Exception as e:
            logger.error(f"监控日志文件失败: {e}")
            return log_metrics
    
    def update_metrics(self, log_metrics: Dict[str, Any]):
        """更新监控指标"""
        # 更新任务状态
        if log_metrics['t_day_started'] and not self.metrics['t_day_task_started']:
            self.metrics['t_day_task_started'] = True
            self.metrics['task_start_time'] = datetime.now().isoformat()
            logger.info("T日评分任务已开始")
        
        if log_metrics['t_day_completed'] and not self.metrics['t_day_task_completed']:
            self.metrics['t_day_task_completed'] = True
            self.metrics['task_end_time'] = datetime.now().isoformat()
            
            # 计算执行时间
            if 'task_start_time' in self.metrics:
                start_time = datetime.fromisoformat(self.metrics['task_start_time'])
                end_time = datetime.fromisoformat(self.metrics['task_end_time'])
                self.metrics['execution_time'] = (end_time - start_time).total_seconds()
                logger.info(f"T日评分任务完成，执行时间: {self.metrics['execution_time']:.2f}秒")
        
        # 更新舆情分析状态
        if log_metrics['sentiment_analysis_detected']:
            self.metrics['sentiment_analysis_used'] = True
        
        if log_metrics['chinese_crawler_detected']:
            self.metrics['chinese_crawler_used'] = True
        
        if log_metrics['tavily_fallback_detected']:
            self.metrics['tavily_fallback_used'] = True
            self.metrics['degradation_triggered'] = True
        
        # 更新错误统计
        if log_metrics['error_count'] > 0:
            self.metrics['error_messages'] = [
                line.strip() for line in log_metrics['recent_lines'] 
                if 'error' in line.lower() or '失败' in line
            ][:5]  # 只保存最近5个错误
    
    def generate_report(self) -> Dict[str, Any]:
        """生成监控报告"""
        report = {
            'monitor_summary': {
                'monitor_duration': (datetime.now() - self.monitor_start_time).total_seconds(),
                'monitor_start_time': self.metrics['start_time'],
                'current_time': datetime.now().isoformat(),
                'scheduler_running': self.scheduler_pid is not None
            },
            'task_status': {
                't_day_task_started': self.metrics['t_day_task_started'],
                't_day_task_completed': self.metrics['t_day_task_completed'],
                't_day_task_error': self.metrics['t_day_task_error'],
                'execution_time_seconds': self.metrics.get('execution_time'),
                'task_start_time': self.metrics.get('task_start_time'),
                'task_end_time': self.metrics.get('task_end_time')
            },
            'sentiment_analysis_performance': {
                'sentiment_analysis_used': self.metrics['sentiment_analysis_used'],
                'chinese_crawler_used': self.metrics['chinese_crawler_used'],
                'tavily_fallback_used': self.metrics['tavily_fallback_used'],
                'degradation_triggered': self.metrics['degradation_triggered'],
                'chinese_news_count': self.metrics['chinese_news_count'],
                'english_news_count': self.metrics['english_news_count'],
                'average_sentiment_score': round(
                    sum(self.metrics['sentiment_scores']) / len(self.metrics['sentiment_scores']) 
                    if self.metrics['sentiment_scores'] else 0, 2
                ),
                'sentiment_score_samples': len(self.metrics['sentiment_scores'])
            },
            'system_health': {
                'error_count': len(self.metrics['error_messages']),
                'recent_errors': self.metrics['error_messages'],
                'degradation_occurred': self.metrics['degradation_triggered']
            },
            'performance_insights': self._generate_insights(),
            'recommendations': self._generate_recommendations()
        }
        
        return report
    
    def _generate_insights(self) -> List[str]:
        """生成性能洞察"""
        insights = []
        
        # 舆情分析使用情况
        if self.metrics['sentiment_analysis_used']:
            if self.metrics['chinese_crawler_used']:
                insights.append("✅ 新舆情分析系统工作正常：成功使用中文新闻爬虫")
            elif self.metrics['tavily_fallback_used']:
                insights.append("⚠️ 舆情分析系统降级：使用Tavily作为备用方案")
            else:
                insights.append("⚠️ 舆情分析系统状态未知：检测到舆情分析但无法确定数据源")
        else:
            insights.append("❌ 舆情分析系统未使用：T日评分可能跳过了舆情分析")
        
        # 新闻数据量分析
        total_news = self.metrics['chinese_news_count'] + self.metrics['english_news_count']
        if total_news > 0:
            chinese_ratio = self.metrics['chinese_news_count'] / total_news
            if chinese_ratio > 0.7:
                insights.append(f"✅ 中文新闻覆盖率优秀：{chinese_ratio:.1%}（目标：>70%）")
            elif chinese_ratio > 0.3:
                insights.append(f"⚠️ 中文新闻覆盖率中等：{chinese_ratio:.1%}（目标：>70%）")
            else:
                insights.append(f"❌ 中文新闻覆盖率低：{chinese_ratio:.1%}（目标：>70%）")
        else:
            insights.append("❌ 未找到任何新闻数据：需要优化搜索词或检查爬虫")
        
        # 情感评分分析
        if self.metrics['sentiment_scores']:
            avg_score = sum(self.metrics['sentiment_scores']) / len(self.metrics['sentiment_scores'])
            if avg_score > 6:
                insights.append(f"✅ 舆情评分积极：平均{avg_score:.1f}/10.0")
            elif avg_score > 3:
                insights.append(f"⚠️ 舆情评分中性：平均{avg_score:.1f}/10.0")
            else:
                insights.append(f"❌ 舆情评分负面：平均{avg_score:.1f}/10.0")
        
        # 降级机制分析
        if self.metrics['degradation_triggered']:
            insights.append("⚠️ 系统触发了降级机制：检查中文爬虫或网络连接")
        
        return insights
    
    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 舆情分析建议
        if not self.metrics['sentiment_analysis_used']:
            recommendations.append("🔧 检查舆情分析配置：确保TAVILY_API_KEY已设置且功能已启用")
        
        if self.metrics['degradation_triggered']:
            recommendations.append("🔧 检查中文新闻爬虫：优化网站解析逻辑或尝试Simple模式")
        
        if self.metrics['chinese_news_count'] == 0 and self.metrics['sentiment_analysis_used']:
            recommendations.append("🔧 优化中文搜索词：调整股票搜索策略，提高新闻匹配度")
        
        # 性能优化建议
        if self.metrics.get('execution_time', 0) > 300:  # 超过5分钟
            recommendations.append("⚡ 优化执行时间：考虑减少舆情分析股票数量或优化爬虫超时")
        
        if len(self.metrics['error_messages']) > 0:
            recommendations.append("🔧 修复系统错误：检查日志中的具体错误信息")
        
        if not recommendations:
            recommendations.append("✅ 系统运行正常，无需改进")
        
        return recommendations
    
    def save_report(self, report: Dict[str, Any]):
        """保存监控报告"""
        report_file = self.t01_dir / f"t_day_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            # 同时生成Markdown格式报告
            self._generate_markdown_report(report, report_file.with_suffix('.md'))
            
            logger.info(f"监控报告已保存: {report_file}")
            return report_file
        except Exception as e:
            logger.error(f"保存监控报告失败: {e}")
            return None
    
    def _generate_markdown_report(self, report: Dict[str, Any], output_file: Path):
        """生成Markdown格式报告"""
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write("# T日评分任务监控报告\n\n")
                f.write(f"**监控时间**: {report['monitor_summary']['current_time']}\n")
                f.write(f"**监控时长**: {report['monitor_summary']['monitor_duration']:.2f}秒\n")
                f.write(f"**调度器状态**: {'运行中' if report['monitor_summary']['scheduler_running'] else '未运行'}\n\n")
                
                f.write("## 任务状态\n\n")
                task_status = report['task_status']
                f.write(f"- **任务开始**: {task_status.get('t_day_task_started', False)}\n")
                f.write(f"- **任务完成**: {task_status.get('t_day_task_completed', False)}\n")
                f.write(f"- **执行时间**: {task_status.get('execution_time_seconds', 'N/A')}秒\n")
                f.write(f"- **开始时间**: {task_status.get('task_start_time', 'N/A')}\n")
                f.write(f"- **结束时间**: {task_status.get('task_end_time', 'N/A')}\n\n")
                
                f.write("## 舆情分析性能\n\n")
                sentiment = report['sentiment_analysis_performance']
                f.write(f"- **舆情分析使用**: {sentiment['sentiment_analysis_used']}\n")
                f.write(f"- **中文爬虫使用**: {sentiment['chinese_crawler_used']}\n")
                f.write(f"- **Tavily降级使用**: {sentiment['tavily_fallback_used']}\n")
                f.write(f"- **降级触发**: {sentiment['degradation_triggered']}\n")
                f.write(f"- **中文新闻数量**: {sentiment['chinese_news_count']}\n")
                f.write(f"- **英文新闻数量**: {sentiment['english_news_count']}\n")
                f.write(f"- **平均舆情评分**: {sentiment['average_sentiment_score']}/10.0\n")
                f.write(f"- **评分样本数**: {sentiment['sentiment_score_samples']}\n\n")
                
                f.write("## 性能洞察\n\n")
                for insight in report.get('performance_insights', []):
                    f.write(f"- {insight}\n")
                
                f.write("\n## 改进建议\n\n")
                for rec in report.get('recommendations', []):
                    f.write(f"- {rec}\n")
                
                f.write("\n## 系统健康\n\n")
                health = report['system_health']
                f.write(f"- **错误数量**: {health['error_count']}\n")
                if health['error_count'] > 0:
                    f.write("**最近错误**:\n")
                    for error in health['recent_errors'][:3]:
                        f.write(f"  - {error[:100]}...\n")
                
                logger.info(f"Markdown报告已生成: {output_file}")
        except Exception as e:
            logger.error(f"生成Markdown报告失败: {e}")
    
    def run_monitoring_loop(self, duration_minutes: int = 30, interval_seconds: int = 10):
        """运行监控循环"""
        logger.info(f"开始监控循环，持续时间: {duration_minutes}分钟，间隔: {interval_seconds}秒")
        
        end_time = datetime.now() + timedelta(minutes=duration_minutes)
        check_count = 0
        
        while datetime.now() < end_time:
            check_count += 1
            logger.debug(f"监控检查 #{check_count}")
            
            # 检查调度器进程
            scheduler_running = self.check_scheduler_process()
            
            # 监控日志文件
            log_metrics = self.monitor_log_file()
            
            # 更新指标
            self.update_metrics(log_metrics)
            
            # 如果任务已完成，提前结束监控
            if self.metrics['t_day_task_completed'] and check_count > 5:
                logger.info("T日评分任务已完成，准备生成最终报告")
                break
            
            # 等待下次检查
            if datetime.now() < end_time:
                time.sleep(interval_seconds)
        
        # 生成最终报告
        logger.info("监控循环结束，生成最终报告")
        final_report = self.generate_report()
        report_file = self.save_report(final_report)
        
        # 输出关键信息
        logger.info("=" * 60)
        logger.info("监控摘要:")
        logger.info(f"  任务状态: {'已完成' if self.metrics['t_day_task_completed'] else '未完成'}")
        logger.info(f"  舆情分析: {'已使用' if self.metrics['sentiment_analysis_used'] else '未使用'}")
        logger.info(f"  中文爬虫: {'已使用' if self.metrics['chinese_crawler_used'] else '未使用'}")
        logger.info(f"  中文新闻: {self.metrics['chinese_news_count']}条")
        logger.info(f"  英文新闻: {self.metrics['english_news_count']}条")
        logger.info(f"  报告文件: {report_file}")
        logger.info("=" * 60)
        
        return final_report


def main():
    """主函数"""
    print("=== T日评分任务监控器 ===")
    print("监控开始时间:", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    print("预计监控时段: 20:00-20:30 (北京时间)")
    print()
    
    try:
        monitor = TDayMonitor()
        
        # 检查调度器状态
        if not monitor.check_scheduler_process():
            print("⚠️ 警告: T01调度器进程未找到")
            print("   请确保调度器已启动: cd /root/.openclaw/workspace/tasks/T01 && python3 scheduler.py --mode run")
            print("   继续监控...")
        
        # 运行监控循环（30分钟，每10秒检查一次）
        print("开始监控循环...")
        report = monitor.run_monitoring_loop(duration_minutes=30, interval_seconds=10)
        
        # 显示关键结果
        print("\n=== 监控结果摘要 ===")
        sentiment = report['sentiment_analysis_performance']
        
        print(f"📊 舆情分析性能:")
        print(f"   中文爬虫使用: {sentiment['chinese_crawler_used']}")
        print(f"   Tavily降级: {sentiment['tavily_fallback_used']}")
        print(f"   中文新闻数: {sentiment['chinese_news_count']}")
        print(f"   英文新闻数: {sentiment['english_news_count']}")
        print(f"   平均评分: {sentiment['average_sentiment_score']}/10.0")
        
        print(f"\n🚀 性能洞察:")
        for insight in report.get('performance_insights', []):
            print(f"   {insight}")
        
        print(f"\n🔧 改进建议:")
        for rec in report.get('recommendations', []):
            print(f"   {rec}")
        
        report_file = f"/root/.openclaw/workspace/tasks/T01/t_day_monitor_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        print(f"\n✅ 监控完成，详细报告已保存: {report_file}")
        
    except KeyboardInterrupt:
        print("\n⚠️ 监控被用户中断")
    except Exception as e:
        print(f"\n❌ 监控出错: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()