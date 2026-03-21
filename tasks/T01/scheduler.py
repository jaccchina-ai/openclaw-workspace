#!/usr/bin/env python3
"""
T01 定时任务调度器
负责协调T日晚上8点评分和T+1日早上9:25竞价分析
集成数据存储和绩效跟踪功能
"""

import os
import sys

# 强制使用北京时间（CST UTC+8），确保schedule库使用正确时区
os.environ['TZ'] = 'Asia/Shanghai'
import time
time.tzset()

import yaml
import json
import logging
import schedule
# time模块已在上面导入并配置时区
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
import pandas as pd
import tushare as ts
import psutil

# OpenClaw message工具导入 - 使用subprocess调用CLI
try:
    import subprocess
    import os
    MESSAGE_TOOL_AVAILABLE = True
    
    def message(action=None, channel=None, message=None, **kwargs):
        """通过subprocess调用openclaw message工具发送消息"""
        try:
            # 从环境变量获取飞书用户ID
            feishu_user_id = os.environ.get('FEISHU_USER_ID', 'ou_b8a256a9cb526db6c196cb438d6893a6')
            
            # 构建命令 - 指定目标用户
            cmd = ['/root/.nvm/versions/node/v22.22.0/bin/openclaw', 'message', 'send', 
                   '--channel', channel,
                   '--target', f'user:{feishu_user_id}',
                   '--message', message]
            
            # 设置环境变量
            env = os.environ.copy()
            env['PATH'] = '/root/.nvm/versions/node/v22.22.0/bin:' + env.get('PATH', '')
            
            # 执行命令
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return True
            else:
                # 如果失败，尝试使用fallback记录到日志
                print(f"Message send failed: {result.stderr}")
                # 记录到fallback日志
                fallback_log = Path('/root/.openclaw/workspace/logs/feishu_fallback.log')
                fallback_log.parent.mkdir(parents=True, exist_ok=True)
                with open(fallback_log, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Error: {result.stderr}\n")
                    f.write(f"Message:\n{message}\n")
                return False
        except Exception as e:
            print(f"Message send error: {e}")
            # 记录到fallback日志
            try:
                fallback_log = Path('/root/.openclaw/workspace/logs/feishu_fallback.log')
                fallback_log.parent.mkdir(parents=True, exist_ok=True)
                with open(fallback_log, 'a', encoding='utf-8') as f:
                    f.write(f"\n{'='*60}\n")
                    f.write(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    f.write(f"Exception: {e}\n")
                    f.write(f"Message:\n{message}\n")
            except:
                pass
            return False
            
except ImportError:
    MESSAGE_TOOL_AVAILABLE = False
    message = None

# 飞书增强模块导入（可选）
try:
    from feishu_message_enhanced import FeishuMessageSender
    FEISHU_ENHANCED_AVAILABLE = True
except ImportError:
    FEISHU_ENHANCED_AVAILABLE = False

# 飞书直接发送模块导入（新方案 - 绕过CLI）
try:
    from feishu_direct_sender import FeishuDirectSender, send_feishu_message_direct
    FEISHU_DIRECT_AVAILABLE = True
except ImportError:
    FEISHU_DIRECT_AVAILABLE = False

# React Loop 飞书发送器导入（彻底解决Node.js内存溢出问题）
try:
    from react_loop_feishu_sender import ReactLoopFeishuSender, send_feishu_message
    REACT_LOOP_AVAILABLE = True
except ImportError:
    REACT_LOOP_AVAILABLE = False

# 增强版飞书发送器导入（优先使用直接API调用）
try:
    from enhanced_feishu_sender import EnhancedFeishuSender, send_message as send_feishu_enhanced
    ENHANCED_SENDER_AVAILABLE = True
except ImportError:
    ENHANCED_SENDER_AVAILABLE = False

sys.path.insert(0, str(Path(__file__).parent))

from limit_up_strategy_new import LimitUpScoringStrategyV2
from data_storage import T01DataStorage
from performance_tracker import PerformanceTracker

# 健壮调度器修复 - 防止30分钟重启问题
class RobustScheduler:
    """健壮调度器，防止异常导致退出"""
    
    def __init__(self, original_scheduler):
        self.scheduler = original_scheduler
        self.logger = logging.getLogger(__name__)
        self.start_time = datetime.now()
        self.heartbeat_counter = 0
        self.last_heartbeat = time.time()
        
        # 监控配置
        self.max_memory_mb = 500  # 最大内存限制
        self.heartbeat_interval = 300  # 5分钟心跳
    
    def run_pending_with_safety(self):
        """安全运行pending任务"""
        try:
            # 检查内存使用
            self.check_memory_usage()
            
            # 运行任务
            schedule.run_pending()
            
            # 记录心跳
            current_time = time.time()
            if current_time - self.last_heartbeat > self.heartbeat_interval:
                self.heartbeat_counter += 1
                self.logger.info(
                    f"💓 调度器心跳 #{self.heartbeat_counter}, "
                    f"运行时间: {(datetime.now() - self.start_time).total_seconds() / 60:.1f}分钟, "
                    f"内存: {psutil.Process().memory_info().rss / 1024 / 1024:.1f}MB"
                )
                self.last_heartbeat = current_time
                
                # 定期垃圾回收
                if self.heartbeat_counter % 12 == 0:  # 每小时一次
                    import gc
                    gc.collect()
                    self.logger.info("🔄 执行定期垃圾回收")
            
            return True
            
        except Exception as e:
            self.logger.error(f"调度器主循环异常: {e}", exc_info=True)
            # 不重新抛出异常，避免退出
            return False
    
    def check_memory_usage(self):
        """检查内存使用"""
        import psutil
        mem_info = psutil.Process().memory_info()
        mem_mb = mem_info.rss / 1024 / 1024
        
        if mem_mb > self.max_memory_mb:
            self.logger.warning(f"⚠️ 内存使用过高: {mem_mb:.1f}MB > {self.max_memory_mb}MB")
            
            # 尝试释放内存
            import gc
            gc.collect()
            
            # 记录内存状态
            self.log_memory_state()
    
    def log_memory_state(self):
        """记录内存状态"""
        import gc
        import psutil
        mem_info = psutil.Process().memory_info()
        
        self.logger.info(
            f"内存状态 - RSS: {mem_info.rss / 1024 / 1024:.1f}MB, "
            f"VMS: {mem_info.vms / 1024 / 1024:.1f}MB, "
            f"垃圾回收对象: {len(gc.get_objects())}"
        )
    
    def run_forever(self, sleep_seconds=10):
        """永远运行调度器"""
        # 动态调整检查间隔：竞价窗口期间（09:24-09:30）减少到3秒
        current_time = datetime.now().strftime('%H:%M')
        if '09:24' <= current_time <= '09:30':
            sleep_seconds = 3
            self.logger.info(f"🚀 启动健壮调度器，检查间隔: {sleep_seconds}秒 (竞价窗口模式)")
        else:
            self.logger.info(f"🚀 启动健壮调度器，检查间隔: {sleep_seconds}秒")
        
        consecutive_failures = 0
        max_consecutive_failures = 5
        
        while True:
            try:
                success = self.run_pending_with_safety()
                
                if success:
                    consecutive_failures = 0
                else:
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        self.logger.error(f"连续失败 {consecutive_failures} 次，可能系统不稳定")
                
                time.sleep(sleep_seconds)
                
            except KeyboardInterrupt:
                self.logger.info("调度器被用户中断")
                break
            except Exception as e:
                self.logger.error(f"调度器意外异常: {e}", exc_info=True)
                consecutive_failures += 1
                
                # 如果连续失败太多，等待更长时间
                if consecutive_failures > max_consecutive_failures:
                    sleep_time = min(300, sleep_seconds * 2)  # 最多5分钟
                    self.logger.warning(f"连续失败过多，等待 {sleep_time} 秒后继续")
                    time.sleep(sleep_time)
                else:
                    time.sleep(sleep_seconds)


class T01Scheduler:
    """T01策略定时调度器"""
    
    def __init__(self, config_path='config.yaml'):
        """初始化调度器"""
        # 检查是否已有其他实例运行（防止僵尸进程）
        self._check_single_instance()
        
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 设置日志
        self.setup_logging()
        self.logger = logging.getLogger(__name__)
        
        # 记录当前进程信息
        import os
        self.pid = os.getpid()
        self.logger.info(f"🆔 调度器进程启动 (PID: {self.pid})")
        
        # 初始化策略
        ts.set_token(self.config['api']['api_key'])
        self.pro = ts.pro_api()
        self.strategy = LimitUpScoringStrategyV2(self.config)
        
        # 初始化数据存储和绩效跟踪
        self.data_storage = T01DataStorage(config_path)
        self.performance_tracker = PerformanceTracker(config_path)
        
        # 状态文件路径
        self.state_dir = Path("state")
        self.state_dir.mkdir(exist_ok=True)
        
        # 输出目录
        self.output_dir = Path("output")
        self.output_dir.mkdir(exist_ok=True)
        
        self.logger.info("T01调度器初始化完成 (集成数据存储和绩效跟踪)")
    
    def _check_single_instance(self):
        """检查是否已有其他scheduler实例运行"""
        import os
        import sys
        
        current_pid = os.getpid()
        other_pids = []
        
        try:
            # 读取/proc查找其他scheduler.py进程
            for pid_str in os.listdir('/proc'):
                if not pid_str.isdigit():
                    continue
                pid = int(pid_str)
                if pid == current_pid:
                    continue
                
                try:
                    cmdline_path = f'/proc/{pid}/cmdline'
                    with open(cmdline_path, 'r') as f:
                        cmdline = f.read()
                        if 'scheduler.py' in cmdline:
                            other_pids.append(pid)
                except (IOError, OSError):
                    continue
        except Exception:
            pass
        
        if other_pids:
            print(f"⚠️ 警告: 检测到 {len(other_pids)} 个其他scheduler进程正在运行: {other_pids}")
            print("   本实例将继续启动，但建议检查是否有僵尸进程")
            # 不退出，只是警告，让systemd或wrapper处理
    
    def setup_logging(self):
        """配置日志"""
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.StreamHandler(),
                logging.FileHandler(log_dir / 't01_scheduler.log', encoding='utf-8')
            ]
        )
    
    def load_trading_calendar(self):
        """加载本地交易日历文件，避免Tushare API挂起问题"""
        import json
        # datetime已在模块顶部导入，避免重复导入导致变量冲突
        
        calendar_path = '/root/.openclaw/workspace/trading_calendar.json'
        try:
            with open(calendar_path, 'r', encoding='utf-8') as f:
                self.trading_calendar = json.load(f)
            self.logger.info(f"✅ 本地交易日历加载成功: {calendar_path}")
        except Exception as e:
            self.logger.error(f"❌ 无法加载交易日历文件 {calendar_path}: {e}")
            self.trading_calendar = None
    
    def is_trading_day(self, date_str):
        """检查给定日期是否为交易日 - 使用Tushare API实时查询
        
        Args:
            date_str: 日期字符串，格式可以是 YYYY-MM-DD 或 YYYYMMDD
            
        Returns:
            bool: 是否为交易日
        """
        # 统一日期格式为 YYYY-MM-DD
        if len(date_str) == 8:  # YYYYMMDD
            formatted_date = f"{date_str[0:4]}-{date_str[4:6]}-{date_str[6:8]}"
            api_date = date_str
        else:
            formatted_date = date_str
            api_date = date_str.replace('-', '')
        
        # 首先检查是否为周末（周六/周日）- 这是硬性规则
        try:
            dt = datetime.strptime(formatted_date, '%Y-%m-%d')
            weekday_num = dt.weekday()  # 0=周一, 5=周六, 6=周日
            if weekday_num >= 5:  # 周六或周日
                self.logger.debug(f"📅 {formatted_date} 是周末(星期{weekday_num+1})，非交易日")
                return False
        except Exception as e:
            self.logger.warning(f"无法解析日期 {formatted_date}: {e}")
            return False
        
        # 使用Tushare API实时查询交易日历
        try:
            import signal
            
            def timeout_handler(signum, frame):
                raise TimeoutError("Tushare API timeout")
            
            # 设置5秒超时
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(5)
            
            try:
                cal = self.pro.trade_cal(exchange='SSE', start_date=api_date, end_date=api_date)
                signal.alarm(0)  # 取消超时
                
                if not cal.empty:
                    is_open = cal.iloc[0]['is_open'] == 1
                    self.logger.debug(f"📅 Tushare API查询: {formatted_date} 是{'交易日' if is_open else '非交易日'}")
                    return is_open
                else:
                    self.logger.warning(f"⚠️ Tushare API返回空数据: {formatted_date}")
                    return False
                    
            except TimeoutError:
                self.logger.warning(f"⚠️ Tushare API超时，回退到本地交易日历: {formatted_date}")
                signal.alarm(0)
                return self._is_trading_day_fallback(formatted_date)
                
        except Exception as e:
            self.logger.warning(f"⚠️ Tushare API查询失败: {e}，回退到本地交易日历")
            return self._is_trading_day_fallback(formatted_date)
    
    def _is_trading_day_fallback(self, formatted_date):
        """本地交易日历回退方案"""
        # 加载交易日历
        if not hasattr(self, 'trading_calendar') or self.trading_calendar is None:
            self.load_trading_calendar()
            if self.trading_calendar is None:
                self.logger.error("无法加载本地交易日历，默认视为非交易日")
                return False
        
        # 检查是否为节假日
        holidays = self.trading_calendar.get('2026', {}).get('holidays', [])
        if formatted_date in holidays:
            return False
        
        # 检查是否在交易日列表中
        trading_days = self.trading_calendar.get('2026', {}).get('trading_days', [])
        if formatted_date in trading_days:
            return True
        
        # 默认视为非交易日
        self.logger.warning(f"⚠️ {formatted_date} 不在本地交易日历中，默认视为非交易日")
        return False
    
    def get_trade_date(self, date_str: str = None, offset: int = 0) -> str:
        """获取交易日期
        
        Args:
            date_str: 指定日期字符串，如果提供则直接返回
            offset: 日期偏移量
                - 0: 最近交易日（今天如果是交易日则返回今天，否则返回最近交易日）
                - 1: 下一个交易日（暂时不支持）
                - -1: 前一个交易日
                - -2: 前两个交易日，依此类推
        """
        if date_str:
            return date_str
        
        # 如果没有提供日期，获取最近交易日
        today = datetime.now().strftime('%Y%m%d')
        
        # 获取最近60天交易日历（确保包含足够多的交易日）
        start_date = (datetime.now() - timedelta(days=60)).strftime('%Y%m%d')
        cal = self.pro.trade_cal(exchange='SSE', start_date=start_date, end_date=today)
        
        if cal.empty:
            self.logger.error("无法获取交易日历")
            return today
        
        # 确保按日期降序排列（最近的在前）
        cal = cal.sort_values('cal_date', ascending=False)
        
        trade_dates = cal[cal['is_open'] == 1]['cal_date'].tolist()
        
        if not trade_dates:
            self.logger.warning("没有找到交易日")
            return today
        
        # 处理偏移量
        if offset == 0:
            # 如果今天是交易日，返回今天；否则返回最近交易日
            if today in trade_dates:
                return today
            else:
                return trade_dates[0] if trade_dates else today
        elif offset < 0:
            # 负偏移：前N个交易日
            abs_offset = abs(offset)
            if abs_offset < len(trade_dates):
                # trade_dates[0]是最近交易日，trade_dates[1]是前一个交易日
                return trade_dates[abs_offset]
            else:
                self.logger.warning(f"偏移量 {offset} 超出范围，返回最早可用交易日")
                return trade_dates[-1] if trade_dates else today
        else:
            # 正偏移：下一个交易日（暂时不支持）
            self.logger.warning(f"正偏移量 {offset} 暂不支持，返回最近交易日")
            return trade_dates[0] if trade_dates else today
    
    def send_feishu_message(self, message_content: str) -> bool:
        """发送飞书消息 - 使用OpenClaw message工具

        直接使用OpenClaw的message工具通过飞书channel发送消息。

        Args:
            message_content: 消息内容

        Returns:
            bool: 是否发送成功
        """
        try:
            self.logger.info(f"📤 使用OpenClaw message工具发送飞书消息: {len(message_content)} 字符")

            # 使用OpenClaw message工具直接发送
            # 注意：使用导入的message函数，不是参数名
            result = message(
                action="send",
                channel="feishu",
                message=message_content
            )

            if result:
                self.logger.info("✅ 飞书消息发送成功")
                return True
            else:
                self.logger.error("❌ 飞书消息发送失败")
                return False

        except Exception as e:
            self.logger.error(f"❌ 发送飞书消息异常: {e}")
            return False
    
    def prepare_t_day_push_message(self, result: dict) -> str:
        """准备T日评分推送消息
        
        Args:
            result: T日评分结果字典
            
        Returns:
            推送消息字符串
        """
        if not result.get('success'):
            return f"⚠️ T日评分失败: {result.get('error', '未知错误')}"
        
        trade_date = result.get('trade_date', '未知日期')
        candidates = result.get('candidates', [])
        summary = result.get('summary', {})
        
        message_parts = []
        message_parts.append(f"📊 **T01策略 - T日评分结果 ({trade_date})**")
        message_parts.append("="*40)
        message_parts.append(f"**市场概况**:")
        message_parts.append(f"涨停股票: {summary.get('total_limit_up', 0)} 只")
        message_parts.append(f"有效评分: {summary.get('total_scored', 0)} 只")
        message_parts.append(f"候选筛选: {summary.get('top_n_selected', 0)} 只")
        message_parts.append("")
        message_parts.append(f"**🎯 候选股票榜单**")
        
        for i, stock in enumerate(candidates[:5], 1):
            name = stock.get('name', '未知')
            code = stock.get('ts_code', '未知')
            score = stock.get('total_score', 0)
            first_time = stock.get('first_limit_time', '')
            seal_ratio = stock.get('seal_ratio', 0)
            turnover = stock.get('turnover_rate', 0)
            industry = stock.get('industry', '未知')
            
            # 格式化首次涨停时间
            if first_time:
                # 补零到6位，确保格式为HHMMSS
                padded = first_time.zfill(6)
                # 格式化为 HH:MM:SS
                time_str = f"{padded[0:2]}:{padded[2:4]}:{padded[4:6]}"
                # 如果秒为00，可以省略秒部分
                if padded[4:6] == "00":
                    time_str = time_str[:-3]
            else:
                time_str = "未知"
            
            message_parts.append(f"#{i} **{name}** ({code})")
            message_parts.append(f"  评分: {score:.1f} | 涨停: {time_str}")
            message_parts.append(f"  封成比: {seal_ratio:.2f} | 换手: {turnover:.2f}%")
            message_parts.append(f"  行业: {industry}")
            message_parts.append("")
        
        message_parts.append("="*40)
        message_parts.append("**📋 明日计划**")
        message_parts.append("1. 明早09:25: 竞价数据分析")
        message_parts.append("2. 09:30前: 推送最终买入建议")
        message_parts.append("")
        message_parts.append("⏰ 生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return "\n".join(message_parts)
    
    def run_t_day_scoring(self, trade_date: str = None) -> dict:
        """
        运行T日涨停股评分
        
        Args:
            trade_date: 交易日期，如果为None则使用今天（如果是交易日）
            
        Returns:
            评分结果字典
        """
        if trade_date is None:
            trade_date = self.get_trade_date(offset=0)  # 使用今天（如果是交易日）
        
        self.logger.info(f"开始T日涨停股评分 (日期: {trade_date})")
        
        try:
            # 获取涨停股票
            limit_up_stocks = self.strategy.get_limit_up_stocks(trade_date)
            
            if limit_up_stocks.empty:
                self.logger.warning(f"日期 {trade_date} 没有涨停股票")
                return {
                    'success': False,
                    'error': f"日期 {trade_date} 没有涨停股票",
                    'trade_date': trade_date
                }
            
            self.logger.info(f"获取到 {len(limit_up_stocks)} 只涨停股票")
            
            # 计算评分
            scored_stocks = self.strategy.calculate_t_day_score(limit_up_stocks, trade_date)
            
            if scored_stocks.empty:
                self.logger.warning("评分失败，没有有效结果")
                return {
                    'success': False,
                    'error': "评分失败",
                    'trade_date': trade_date
                }
            
            self.logger.info(f"成功评分 {len(scored_stocks)} 只股票")
            
            # 选择前N名候选
            top_n = self.config['strategy']['output'].get('top_n_candidates', 5)
            candidates = scored_stocks.head(top_n).copy()
            
            # 准备结果
            result = {
                'success': True,
                'trade_date': trade_date,
                'candidates': candidates.to_dict('records'),
                'summary': {
                    'total_limit_up': len(limit_up_stocks),
                    'total_scored': len(scored_stocks),
                    'top_n_selected': len(candidates),
                    'top_score': candidates.iloc[0]['total_score'] if not candidates.empty else 0,
                    'generated_at': datetime.now().isoformat()
                }
            }
            
            # 保存结果到数据库
            self._save_recommendations_to_database(result)
            
            # 保存结果到文件
            self.save_t_day_result(result)
            
            # 保存候选股票用于T+1日分析
            self.save_candidates_for_t1(result)
            
            # 发送飞书推送消息
            try:
                push_message = self.prepare_t_day_push_message(result)
                self.send_feishu_message(push_message)
                self.logger.info("✅ T日评分推送消息已发送")
            except Exception as e:
                self.logger.error(f"T日评分推送消息发送失败: {e}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"T日评分失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'trade_date': trade_date
            }
    
    def run_t1_auction_analysis(self, trade_date: str = None, is_trading_hours: bool = True) -> dict:
        """
        运行T+1日竞价分析
        
        Args:
            trade_date: T+1日日期，如果为None则使用当日
            is_trading_hours: 是否在交易时间 (9:25-9:29)
            
        Returns:
            竞价分析结果字典
            
        Note:
            如果在交易时间且无法获取实时竞价数据，将返回错误
        """
        if trade_date is None:
            # 使用今天日期，而不是最近交易日
            trade_date = datetime.now().strftime('%Y%m%d')
        
        self.logger.info(f"开始T+1日竞价分析 (日期: {trade_date}, 交易时间: {is_trading_hours})")
        
        # 检查当前时间是否为交易日
        try:
            if not self.is_trading_day(trade_date):
                self.logger.warning(f"日期 {trade_date} 不是交易日")
                return {
                    'success': False,
                    'error': f"日期 {trade_date} 不是交易日",
                    'trade_date': trade_date
                }
        except Exception as e:
            self.logger.error(f"检查交易日失败: {e}")
        
        # 加载T日候选股票
        candidates = self.load_candidates_for_t1(trade_date)
        if not candidates:
            self.logger.warning(f"没有找到T日候选股票数据 (日期: {trade_date})")
            return {
                'success': False,
                'error': f"没有找到T日候选股票数据 (日期: {trade_date})",
                'trade_date': trade_date
            }
        
        # 转换为DataFrame
        candidates_df = pd.DataFrame(candidates)
        
        try:
            # 分析竞价数据
            t1_results = self.strategy.analyze_t1_auction(candidates_df, trade_date, is_trading_hours)
            
            # 检查是否在交易时间且无结果
            if is_trading_hours and t1_results.empty:
                self.logger.error("在交易时间但无法获取实时竞价数据，无法选股")
                return {
                    'success': False,
                    'error': "在交易时间 (9:25-9:29) 无法获取实时竞价数据，无法选股",
                    'trade_date': trade_date,
                    'is_trading_hours': is_trading_hours,
                    'message': "因无法获取实时竞价数据，无法选股"
                }
            
            if t1_results.empty:
                self.logger.warning("竞价分析失败，没有有效结果")
                return {
                    'success': False,
                    'error': "竞价分析失败",
                    'trade_date': trade_date,
                    'is_trading_hours': is_trading_hours
                }
            
            self.logger.info(f"成功分析 {len(t1_results)} 只股票的竞价数据")
            
            # 生成最终报告
            final_report = self.strategy.generate_final_report(candidates_df, t1_results)
            final_report['is_trading_hours'] = is_trading_hours
            
            # 保存结果
            self.save_t1_result(final_report)
            
            # 准备推送消息
            push_message = self.prepare_push_message(final_report)
            
            return {
                'success': True,
                'trade_date': trade_date,
                'is_trading_hours': is_trading_hours,
                'report': final_report,
                'push_message': push_message,
                'generated_at': datetime.now().isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"T+1日竞价分析失败: {e}", exc_info=True)
            return {
                'success': False,
                'error': str(e),
                'trade_date': trade_date,
                'is_trading_hours': is_trading_hours
            }
    
    def _save_recommendations_to_database(self, result: dict):
        """保存推荐记录到数据库"""
        try:
            if not result.get('success'):
                return
            
            trade_date = result.get('trade_date', '')
            candidates = result.get('candidates', [])
            
            if not trade_date or not candidates:
                return
            
            # 尝试获取T+1日
            t1_date = None
            try:
                t1_date = self.strategy._get_next_trading_day(trade_date)
            except:
                # 如果无法获取，使用默认值
                t1_date = '20260224'  # 简化处理
            
            saved_count = 0
            for candidate in candidates:
                try:
                    # 准备推荐数据
                    recommendation_data = {
                        'trade_date': trade_date,
                        't1_date': t1_date,
                        'ts_code': candidate.get('ts_code', ''),
                        'name': candidate.get('name', ''),
                        'total_score': candidate.get('total_score', 0),
                        't_day_score': candidate.get('total_score', 0),  # 初始时相同
                        'auction_score': 0,  # T+1时更新
                        'auction_data': {},
                        'seal_ratio': candidate.get('seal_ratio', 0),
                        'seal_to_mv': candidate.get('seal_to_mv', 0),
                        'turnover_ratio': candidate.get('turnover_ratio', 0),
                        'is_hot_sector': candidate.get('is_hot_sector', False),
                        'pct_chg': candidate.get('pct_chg', 0)
                    }
                    
                    # 保存到数据库
                    recommendation_id = self.data_storage.save_recommendation(recommendation_data)
                    saved_count += 1
                    
                    self.logger.debug(f"保存推荐记录到数据库: {candidate.get('name')}({candidate.get('ts_code')})")
                    
                except Exception as e:
                    self.logger.warning(f"保存单个推荐记录失败: {e}")
                    continue
            
            self.logger.info(f"已将 {saved_count}/{len(candidates)} 个推荐记录保存到数据库")
            
        except Exception as e:
            self.logger.error(f"保存推荐记录到数据库失败: {e}")
    
    def save_t_day_result(self, result: dict):
        """保存T日结果"""
        try:
            filename = self.state_dir / f"t_day_result_{result['trade_date']}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.logger.info(f"T日结果已保存: {filename}")
        except Exception as e:
            self.logger.error(f"保存T日结果失败: {e}")
    
    def save_candidates_for_t1(self, result: dict):
        """保存候选股票用于T+1日分析"""
        try:
            if not result.get('success'):
                return
            
            # 获取T+1日日期 (下一个交易日)
            t_date = result['trade_date']
            
            # 尝试获取下一个交易日作为T+1日
            t1_date = None
            try:
                # 使用策略类的方法获取下一个交易日
                t1_date = self.strategy._get_next_trading_day(t_date)
            except Exception as e:
                self.logger.warning(f"无法获取下一个交易日: {e}")
                # 如果无法获取，默认加1天 (简化处理)
                # 使用已经导入的datetime和timedelta，避免变量冲突
                current_dt = datetime.strptime(t_date, '%Y%m%d')
                next_dt = current_dt + timedelta(days=1)
                t1_date = next_dt.strftime('%Y%m%d')
            
            # 获取候选股票列表，并确保保存所有指标数据
            candidates = result.get('candidates', [])
            
            # 为每个候选股票添加完整的指标数据（方式1：动态保存所有指标）
            enriched_candidates = []
            for candidate in candidates:
                # 复制所有原始数据
                enriched_candidate = candidate.copy()
                
                # 确保包含以下关键字段（如果存在）
                key_fields = [
                    'ts_code', 'name', 'trade_date', 'total_score', 'basic_score',
                    'seal_ratio', 'seal_to_mv', 'fd_amount', 'amount', 'float_mv',
                    'turnover_ratio', 'turnover_20ma_ratio', 'volume_ratio',
                    'main_net_amount', 'main_net_ratio', 'medium_net_amount',
                    'is_hot_sector', 'dragon_score', 'first_limit_time',
                    'industry', 'close', 'pct_chg', 'open', 'high', 'low',
                    'pre_close', 'change', 'vol', 'score_details'
                ]
                
                # 记录保存的字段数量
                saved_fields = len(enriched_candidate)
                self.logger.debug(f"股票 {candidate.get('ts_code', 'unknown')}: 保存 {saved_fields} 个字段")
                
                enriched_candidates.append(enriched_candidate)
            
            filename = self.state_dir / f"candidates_{t_date}_to_{t1_date}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump({
                    't_date': t_date,
                    't1_date': t1_date,
                    'candidates': enriched_candidates,
                    'saved_at': datetime.now().isoformat(),
                    'total_candidates': len(enriched_candidates)
                }, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"候选股票已保存: {filename} (T+1日: {t1_date}, 共 {len(enriched_candidates)} 只，包含完整指标)")
        except Exception as e:
            self.logger.error(f"保存候选股票失败: {e}")
    
    def load_candidates_for_t1(self, t1_date: str) -> list:
        """加载T日候选股票用于T+1日分析
        
        支持两种文件格式:
        1. 字典格式: {'t_date': '...', 't1_date': '...', 'candidates': [...]}
        2. 列表格式: [...] (直接是候选股票列表)
        """
        try:
            # 查找所有候选文件
            candidate_files = list(self.state_dir.glob("candidates_*.json"))
            if not candidate_files:
                self.logger.warning(f"没有找到候选股票文件 (T+1日: {t1_date})")
                return []
            
            # 辅助函数：从文件名解析日期
            def parse_dates_from_filename(file_path):
                """从文件名解析t_date和t1_date"""
                import re
                match = re.search(r'candidates_(\d{8})_to_(\d{8})\.json', file_path.name)
                if match:
                    return match.group(1), match.group(2)
                return None, None
            
            # 辅助函数：提取候选股票列表
            def extract_candidates(data, file_path):
                """从数据中提取候选股票列表，支持两种格式"""
                if isinstance(data, list):
                    # 列表格式：直接是候选股票列表
                    self.logger.info(f"文件 {file_path.name} 使用列表格式")
                    return data
                elif isinstance(data, dict):
                    # 字典格式：提取candidates字段
                    return data.get('candidates', [])
                else:
                    self.logger.warning(f"文件 {file_path.name} 格式未知: {type(data)}")
                    return []
            
            # 辅助函数：提取t_date
            def extract_t_date(data, file_path):
                """从数据中提取t_date，支持两种格式"""
                if isinstance(data, dict):
                    return data.get('trade_date') or data.get('t_date')
                # 列表格式：尝试从文件名解析
                t_date, _ = parse_dates_from_filename(file_path)
                return t_date
            
            # 优先查找文件名中包含目标T+1日的文件
            matched_files = []
            for file_path in candidate_files:
                try:
                    # 从文件名解析日期
                    file_t_date, file_t1_date = parse_dates_from_filename(file_path)
                    
                    # 检查t1_date是否匹配
                    if file_t1_date == t1_date:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        matched_files.append((file_path, data))
                        self.logger.debug(f"找到匹配的候选文件: {file_path} (T+1日: {file_t1_date})")
                except Exception as e:
                    self.logger.debug(f"读取候选文件失败 {file_path}: {e}")
                    continue
            
            if matched_files:
                # 使用第一个匹配的文件 (通常只有一个)
                file_path, data = matched_files[0]
                self.logger.info(f"加载候选股票: {file_path} (T+1日: {t1_date})")
                
                # 提取候选股票列表
                candidates = extract_candidates(data, file_path)
                
                # 提取t_date
                t_date = extract_t_date(data, file_path)
                
                if t_date:
                    for candidate in candidates:
                        candidate['trade_date'] = t_date
                    self.logger.debug(f"为 {len(candidates)} 只候选股票添加trade_date字段: {t_date}")
                else:
                    self.logger.warning(f"候选文件缺少trade_date/t_date字段: {file_path}")
                
                return candidates
            
            # 如果没有找到完全匹配的，使用最新的文件
            self.logger.warning(f"未找到T+1日 {t1_date} 的候选文件，使用最新的文件")
            candidate_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
            latest_file = candidate_files[0]
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.logger.info(f"加载最新候选股票: {latest_file}")
            
            # 提取候选股票列表
            candidates = extract_candidates(data, latest_file)
            
            # 提取t_date
            t_date = extract_t_date(data, latest_file)
            
            if t_date:
                for candidate in candidates:
                    candidate['trade_date'] = t_date
                self.logger.debug(f"为 {len(candidates)} 只候选股票添加trade_date字段: {t_date}")
            else:
                self.logger.warning(f"候选文件缺少trade_date/t_date字段: {latest_file}")
            
            return candidates
            
        except Exception as e:
            self.logger.error(f"加载候选股票失败: {e}")
            return []
    
    def save_t1_result(self, result: dict):
        """保存T+1日结果"""
        try:
            trade_date = result.get('trade_date', datetime.now().strftime('%Y%m%d'))
            filename = self.output_dir / f"t1_result_{trade_date}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            self.logger.info(f"T+1日结果已保存: {filename}")
        except Exception as e:
            self.logger.error(f"保存T+1日结果失败: {e}")
    
    def prepare_push_message(self, report: dict) -> str:
        """准备推送消息"""
        try:
            market_condition = report.get('market_condition', {})
            recommendations = report.get('t1_recommendations', [])
            
            # 基础消息
            message_parts = []
            
            # 标题
            trade_date = report.get('trade_date', '未知日期')
            message_parts.append(f"📊 **T01策略推荐 - {trade_date}**")
            message_parts.append("="*40)
            
            # 市场状况
            message_parts.append(f"**市场状况**: {market_condition.get('condition', 'N/A')}")
            message_parts.append(f"**风险等级**: {market_condition.get('risk_level', 'N/A')}")
            message_parts.append(f"**建议**: {market_condition.get('suggestion', 'N/A')}")
            
            # 融资融券信息
            fin_balance = market_condition.get('financing_balance', 0)
            margin_balance = market_condition.get('margin_balance', 0)
            if fin_balance > 0:
                message_parts.append(f"**融资余额**: {fin_balance/1e12:.2f}万亿元")
                message_parts.append(f"**融券余额**: {margin_balance/1e9:.2f}亿元")
                
                # 显示详细风险因子
                risk_score = market_condition.get('risk_score', 0)
                fin_change = market_condition.get('financing_change_pct', 0)
                margin_change = market_condition.get('margin_change_pct', 0)
                fin_buy_ratio = market_condition.get('financing_buy_repay_ratio', 0)
                
                message_parts.append(f"**风险评分**: {risk_score}/10")
                message_parts.append(f"**融资变化**: {fin_change:+.2f}%")
                message_parts.append(f"**融券变化**: {margin_change:+.2f}%")
                message_parts.append(f"**融资买入/偿还比**: {fin_buy_ratio:.2f}")
                
                # 风险因子说明
                risk_factors_desc = []
                if fin_change < -2.0:
                    risk_factors_desc.append("融资余额下降>2%")
                if margin_change > 5.0:
                    risk_factors_desc.append("融券余额上升>5%")
                if fin_buy_ratio < 0.8:
                    risk_factors_desc.append("融资买入/偿还<0.8")
                if fin_balance > 800000000000:
                    risk_factors_desc.append("融资余额>8000亿")
                
                if risk_factors_desc:
                    message_parts.append(f"**风险因素**: {', '.join(risk_factors_desc)}")
            
            message_parts.append("="*40)
            
            # 推荐股票
            if recommendations:
                message_parts.append(f"**🎯 推荐股票 ({len(recommendations)}只)**")
                
                for i, rec in enumerate(recommendations, 1):
                    name = rec.get('name', 'N/A')
                    code = rec.get('ts_code', 'N/A')
                    final_score = rec.get('final_score', 0)
                    t_day_score = rec.get('t_day_score', 0)
                    auction_score = rec.get('auction_score', 0)
                    
                    rec_info = rec.get('recommendation', {})
                    action = rec_info.get('action', 'N/A')
                    position = rec_info.get('position', 0) * 100
                    confidence = rec_info.get('confidence', 'N/A')
                    
                    # 获取详细指标数据
                    auction_data = rec.get('auction_data', {})
                    open_change = auction_data.get('open_change_pct', 0)
                    auction_volume_ratio = auction_data.get('auction_volume_ratio', 0)
                    auction_amount = auction_data.get('auction_amount', 0)
                    
                    message_parts.append(f"\n#{i} **{name}** ({code})")
                    message_parts.append(f"  评分: {final_score:.1f} (T日: {t_day_score:.1f}, 竞价: {auction_score:.1f})")
                    message_parts.append(f"  操作: {action} | 仓位: {position:.1f}% | 置信度: {confidence}")
                    
                    reasons = rec_info.get('reasons', [])
                    if reasons:
                        message_parts.append(f"  理由: {', '.join(reasons)}")
                    
                    # 竞价数据指标
                    message_parts.append(f"  **竞价指标**:")
                    message_parts.append(f"    开盘涨幅: {open_change:+.2f}%")
                    message_parts.append(f"    竞价量比: {auction_volume_ratio:.2f}")
                    if auction_amount > 0:
                        message_parts.append(f"    竞价金额: {auction_amount/1e4:.2f}万")
                    
                    # 尝试获取T日详细指标 (如果数据中有)
                    # 注意: 这里需要从原始数据中提取更多指标，后面会优化
                    if 'pct_chg' in rec:
                        message_parts.append(f"  **涨停指标**:")
                        message_parts.append(f"    涨停涨幅: {rec.get('pct_chg', 0)}%")
                    
                    if 'first_time' in rec:
                        first_time = rec.get('first_time', '')
                        if first_time:
                            # 格式转换: 132036 -> 13:20:36
                            try:
                                time_str = f"{first_time[:2]}:{first_time[2:4]}:{first_time[4:6]}"
                                message_parts.append(f"    首次涨停: {time_str}")
                            except:
                                message_parts.append(f"    首次涨停: {first_time}")
                    
                    if 'fd_amount' in rec and 'amount' in rec:
                        fd_amount = rec.get('fd_amount', 0)
                        amount = rec.get('amount', 0)
                        if amount > 0:
                            seal_ratio = fd_amount / amount
                            message_parts.append(f"    封成比: {seal_ratio:.3f}")
                    
                    if 'fd_amount' in rec and 'float_mv' in rec:
                        fd_amount = rec.get('fd_amount', 0)
                        float_mv = rec.get('float_mv', 0)
                        if float_mv > 0:
                            seal_to_mv = fd_amount / float_mv
                            message_parts.append(f"    封单/流通: {seal_to_mv*10000:.2f}bp")
                    
                    if 'turnover_ratio' in rec:
                        turnover = rec.get('turnover_ratio', 0)
                        message_parts.append(f"    换手率: {turnover:.2f}%")
                    
                    if 'is_hot_sector' in rec:
                        is_hot = rec.get('is_hot_sector', False)
                        message_parts.append(f"    热点板块: {'是' if is_hot else '否'}")
                    
                    # 数据来源
                    data_source = auction_data.get('data_source', 'unknown')
                    if data_source == 'realtime':
                        message_parts.append(f"  **数据来源**: 实时竞价数据")
                    elif data_source == 'history':
                        message_parts.append(f"  **数据来源**: 历史竞价数据")
            else:
                message_parts.append("**⚠️ 今日无推荐股票**")
            
            # 注意事项
            message_parts.append("\n" + "="*40)
            message_parts.append("**📋 注意事项**")
            message_parts.append("1. 设置止损位（建议-6%）")
            message_parts.append("2. 关注大盘走势变化")
            message_parts.append("3. 严格执行仓位控制")
            
            # 数据来源说明
            is_trading_hours = report.get('is_trading_hours', False)
            if is_trading_hours:
                message_parts.append(f"\n**⏰ 数据来源**: 实时竞价数据 (9:25-9:29)")
            else:
                message_parts.append(f"\n**⏰ 数据来源**: 历史数据分析")
            
            return "\n".join(message_parts)
            
        except Exception as e:
            self.logger.error(f"准备推送消息失败: {e}")
            return f"T01策略分析完成，但生成消息失败: {e}"
    
    def schedule_t_day_task(self):
        """调度T日评分任务 (晚上8点)"""
        self.logger.info("调度T日评分任务: 每天20:00")
        
        def t_day_job():
            """T日评分任务"""
            self.logger.info("⏰ 执行T日评分任务")
            
            # 强制使用北京时间
            import os
            os.environ['TZ'] = 'Asia/Shanghai'
            import time
            time.tzset()
            from datetime import datetime
            
            # 获取当日日期 (如果是交易日)
            now = datetime.now()
            today = now.strftime('%Y%m%d')
            current_hour = now.hour
            
            # 详细日志记录时区信息
            self.logger.info(f"📍 T日评分 - 当前系统时区: {os.environ.get('TZ', 'not set')}")
            self.logger.info(f"📍 T日评分 - 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
            self.logger.info(f"📍 T日评分 - 当前小时: {current_hour}")
            
            # 严格检查：必须在20:00左右执行（北京时间）
            if not (20 <= current_hour <= 23):
                self.logger.warning(f"⚠️ T日评分在非标准时间执行: {now.strftime('%H:%M')}")
                self.logger.warning(f"    预期执行时间: 20:00-23:59（北京时间）")
            
            # 检查是否为交易日
            try:
                is_trading_day = self.is_trading_day(today)
                
                if is_trading_day:
                    result = self.run_t_day_scoring(today)
                    if result.get('success'):
                        self.logger.info("✅ T日评分任务完成")
                    else:
                        self.logger.error(f"❌ T日评分任务失败: {result.get('error')}")
                else:
                    self.logger.info(f"📅 今日 {today} 不是交易日，跳过T日评分")
            except Exception as e:
                self.logger.error(f"T日评分任务异常: {e}")
        
        # 调度任务 - schedule库使用系统本地时间(北京时间)
        schedule.every().day.at("20:00").do(t_day_job)
        self.logger.info(f"✅ T日评分任务已调度: 每天20:00 (北京时间)")
        return t_day_job
    
    def schedule_t1_task(self):
        """调度T+1日竞价分析任务 (早上9:25)"""
        self.logger.info("调度T+1日竞价分析任务: 每天09:25")
        
        def pre_auction_check():
            """竞价前检查任务 (09:20)"""
            self.logger.info("🔍 执行竞价前检查任务 (09:20)")
            
            # 导入诊断工具
            import sys
            import subprocess
            import json
            
            try:
                # 运行诊断工具
                diagnostic_script = Path(__file__).parent / "scheduler_diagnostic.py"
                if diagnostic_script.exists():
                    result = subprocess.run(
                        ["python3", str(diagnostic_script)],
                        cwd=Path(__file__).parent,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    if result.returncode == 0:
                        self.logger.info("✅ 竞价前检查完成，系统状态正常")
                        # 可以发送简要通知
                        check_message = "🕐 **竞价前检查报告**\n"
                        check_message += "系统状态正常，准备执行09:25竞价分析。\n"
                        check_message += f"检查时间: {datetime.now().strftime('%H:%M:%S')}"
                        self.send_feishu_message(check_message)
                    else:
                        self.logger.warning(f"⚠️ 竞价前检查发现问题，返回码: {result.returncode}")
                        error_message = "⚠️ **竞价前检查警告**\n\n"
                        error_message += "系统检查发现问题，可能影响09:25竞价分析。\n"
                        error_message += f"错误输出:\n```\n{result.stderr[-500:] if result.stderr else '无错误信息'}\n```"
                        self.send_feishu_message(error_message)
                else:
                    self.logger.warning("诊断脚本不存在，跳过详细检查")
                    # 简单检查候选文件
                    candidate_files = list(Path("state").glob("candidates_*.json"))
                    if not candidate_files:
                        self.logger.error("❌ 未找到候选股票文件")
                        error_message = "❌ **紧急: 候选股票文件缺失**\n\n"
                        error_message += "未找到候选股票文件，09:25竞价分析可能失败。\n"
                        error_message += "请立即运行 T日评分任务生成候选文件。"
                        self.send_feishu_message(error_message)
                    else:
                        self.logger.info(f"✅ 找到候选文件: {len(candidate_files)} 个")
            except Exception as e:
                self.logger.error(f"竞价前检查异常: {e}")
        
        def t1_job():
            """T+1日竞价分析任务"""
            self.logger.info("⏰ 执行T+1日竞价分析任务")
            
            # 获取当前时间（强制使用北京时间）
            import os
            os.environ['TZ'] = 'Asia/Shanghai'
            import time
            time.tzset()
            from datetime import datetime
            
            now = datetime.now()
            today = now.strftime('%Y%m%d')
            current_time = now.strftime('%H:%M')
            current_hour = now.hour
            
            # 详细日志记录时区信息
            self.logger.info(f"📍 当前系统时区: {os.environ.get('TZ', 'not set')}")
            self.logger.info(f"📍 当前时间: {now.strftime('%Y-%m-%d %H:%M:%S')} (北京时间)")
            self.logger.info(f"📍 当前小时: {current_hour}")
            
            # 严格检查：必须在09:25-09:29之间执行（北京时间）
            if not (9 == current_hour and 25 <= now.minute <= 29):
                self.logger.error(f"🚫 非交易时间触发竞价分析: {current_time}")
                self.logger.error(f"    竞价分析必须在09:25-09:29（北京时间）执行")
                self.logger.error(f"    当前小时: {current_hour}, 分钟: {now.minute}")
                self.logger.error(f"    跳过执行！")
                return
            
            # 检查是否为交易日
            try:
                is_trading_day = self.is_trading_day(today)
                
                if is_trading_day:
                    # 在交易时间执行
                    result = self.run_t1_auction_analysis(today, is_trading_hours=True)
                    
                    if result.get('success'):
                        self.logger.info("✅ T+1日竞价分析任务完成")
                        
                        # 推送消息
                        push_message = result.get('push_message')
                        if push_message:
                            self.logger.info(f"📤 准备推送消息: {len(push_message)} 字符")
                            # 实际发送飞书消息
                            if self.send_feishu_message(push_message):
                                self.logger.info("✅ T+1竞价分析推送消息已发送")
                            else:
                                self.logger.error("❌ T+1竞价分析推送消息发送失败")
                    else:
                        error_msg = result.get('error', '未知错误')
                        self.logger.error(f"❌ T+1日竞价分析任务失败: {error_msg}")
                        
                        # 如果是"无法获取实时竞价数据"的错误，需要特殊处理
                        if "无法获取实时竞价数据" in error_msg:
                            error_message = "⚠️ **无法选股通知**\n\n"
                            error_message += "在交易时间 (9:25-9:29) 无法获取实时竞价数据，\n"
                            error_message += "因此今日无法提供选股建议。\n\n"
                            error_message += "请检查网络连接或API权限。"
                            # 推送错误消息到飞书
                            self.send_feishu_message(error_message)
                else:
                    self.logger.info(f"📅 今日 {today} 不是交易日，跳过T+1日分析")
            except Exception as e:
                self.logger.error(f"T+1日竞价分析任务异常: {e}")
        
        # 调度任务 - schedule库使用系统本地时间(北京时间)
        schedule.every().day.at("09:20").do(pre_auction_check)
        schedule.every().day.at("09:25").do(t1_job)
        self.logger.info(f"✅ T+1竞价分析任务已调度: 每天09:20/09:25 (北京时间)")
        return t1_job
    
    def run_once(self, mode: str = 'test'):
        """
        运行一次任务 (用于测试或手动执行)
        
        Args:
            mode: 运行模式
                - 't-day': 只运行T日评分
                - 't1-auction': 只运行T+1竞价分析
                - 'test': 测试模式 (使用历史数据)
                - 'full': 完整流程
        """
        self.logger.info(f"运行一次任务 (模式: {mode})")
        
        if mode == 't-day':
            # 使用最近交易日
            trade_date = self.get_trade_date(offset=-1)
            result = self.run_t_day_scoring(trade_date)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif mode == 't1-auction':
            # 使用最近交易日，非交易时间模式
            trade_date = self.get_trade_date(offset=0)
            result = self.run_t1_auction_analysis(trade_date, is_trading_hours=False)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            
        elif mode == 'test':
            # 测试完整流程 (使用历史数据)
            t_date = '20240221'  # T日
            t1_date = '20240222'  # T+1日
            
            self.logger.info(f"测试完整流程: T日={t_date}, T+1日={t1_date}")
            
            # T日评分
            t_day_result = self.run_t_day_scoring(t_date)
            print("\n" + "="*60)
            print("T日评分结果:")
            print("="*60)
            print(json.dumps(t_day_result, ensure_ascii=False, indent=2))
            
            if t_day_result.get('success'):
                # T+1日竞价分析 (非交易时间模式)
                t1_result = self.run_t1_auction_analysis(t1_date, is_trading_hours=False)
                print("\n" + "="*60)
                print("T+1日竞价分析结果:")
                print("="*60)
                print(json.dumps(t1_result, ensure_ascii=False, indent=2))
                
                # 显示推送消息
                if t1_result.get('success'):
                    push_message = t1_result.get('push_message')
                    if push_message:
                        print("\n" + "="*60)
                        print("推送消息预览:")
                        print("="*60)
                        print(push_message)
            
        elif mode == 'full':
            # 完整的当日流程
            today = datetime.now().strftime('%Y%m%d')
            
            # 检查是否为交易日
            try:
                cal = self.pro.trade_cal(exchange='SSE', start_date=today, end_date=today)
                is_trading_day = not cal.empty and cal.iloc[0]['is_open'] == 1
                
                if is_trading_day:
                    # T日评分
                    t_day_result = self.run_t_day_scoring(today)
                    
                    if t_day_result.get('success'):
                        print("✅ T日评分完成")
                    else:
                        print(f"❌ T日评分失败: {t_day_result.get('error')}")
                else:
                    print(f"📅 今日 {today} 不是交易日")
            except Exception as e:
                print(f"❌ 检查交易日失败: {e}")
        
        else:
            print(f"❌ 未知模式: {mode}")
    
    def run_scheduler(self):
        """运行调度器主循环"""
        self.logger.info("启动T01策略调度器")
        # 记录当前时间和时区
        import datetime, time
        now = datetime.datetime.now()
        self.logger.info(f"当前系统时间: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        self.logger.info(f"系统时区: {time.tzname}")
        self.logger.info(f"UTC时间: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 调度任务
        self.logger.info("开始注册定时任务...")
        t_day_job = self.schedule_t_day_task()
        t1_job = self.schedule_t1_task()
        
        # 检查作业注册情况
        import schedule
        jobs = schedule.get_jobs()
        self.logger.info(f"已注册定时任务数量: {len(jobs)}")
        for i, job in enumerate(jobs):
            next_run = job.next_run.strftime('%Y-%m-%d %H:%M:%S') if hasattr(job, 'next_run') and job.next_run else '未知'
            self.logger.info(f"任务 #{i+1}: {job}")
            self.logger.info(f"     下次运行时间: {next_run}")
            self.logger.info(f"     调度时间: {job.at_time if hasattr(job, 'at_time') else '未知'}")
        
        self.logger.info("调度器已启动，进入主循环...")
        self.logger.info("按 Ctrl+C 停止")
        
        try:
            # 初始运行一次 (用于测试) - 临时跳过，避免卡住
            self.logger.info("跳过初始测试以避免卡住...")
            # self.run_once('test')
            
            # 使用健壮调度器防止30分钟重启问题
            robust_scheduler = RobustScheduler(self)
            robust_scheduler.run_forever(sleep_seconds=10)
                
        except KeyboardInterrupt:
            self.logger.info("调度器被用户中断")
        except Exception as e:
            self.logger.error(f"调度器异常: {e}", exc_info=True)


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='T01策略定时调度器')
    parser.add_argument('--mode', choices=['run', 'test', 't-day', 't1-auction', 'full'],
                       default='test', help='运行模式')
    parser.add_argument('--config', default='config.yaml', help='配置文件路径')
    
    args = parser.parse_args()
    
    # 创建调度器
    scheduler = T01Scheduler(args.config)
    
    if args.mode == 'run':
        # 运行调度器
        scheduler.run_scheduler()
    else:
        # 运行一次任务
        scheduler.run_once(args.mode)


if __name__ == "__main__":
    main()