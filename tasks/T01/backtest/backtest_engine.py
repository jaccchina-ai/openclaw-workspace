"""
回测引擎模块

核心回测逻辑，协调数据加载、信号生成、交易模拟和结果输出
"""

import logging
import pandas as pd
import tushare as ts
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .data_loader import DataLoader
from .trade_simulator import TradeSimulator
from .metrics_calculator import MetricsCalculator

# 导入策略V2
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from limit_up_strategy_new import LimitUpScoringStrategyV2

logger = logging.getLogger(__name__)


class BacktestEngine:
    """
    回测引擎

    T01龙头战法策略回测的核心引擎，负责：
    - 加载历史数据
    - 执行策略信号生成
    - 模拟交易执行
    - 计算绩效指标
    - 生成回测报告

    Attributes:
        start_date: 回测开始日期
        end_date: 回测结束日期
        data_loader: 数据加载器实例
        trade_simulator: 交易模拟器实例
        metrics_calculator: 指标计算器实例
    """

    def __init__(self, config: Dict[str, Any], start_date: str, end_date: str, 
                 strategy: Optional[Any] = None):
        """
        初始化回测引擎
        
        Args:
            config: 配置字典
            start_date: 回测开始日期 (格式: YYYYMMDD)
            end_date: 回测结束日期 (格式: YYYYMMDD)
            strategy: 策略实例，如果为None则使用LimitUpScoringStrategyV2
        """
        self.config = config
        self.start_date = start_date
        self.end_date = end_date
        
        # 从配置中提取回测参数
        backtest_config = config.get('backtest', {})
        self.initial_capital = backtest_config.get('initial_capital', 1000000)
        self.commission_rate = backtest_config.get('commission_rate', 0.0003)
        self.slippage = backtest_config.get('slippage', 0.005)
        self.position_size = backtest_config.get('position_size', 0.2)
        self.max_positions = backtest_config.get('max_positions', 5)
        
        # 策略参数
        strategy_config = config.get('strategy', {})
        output_config = strategy_config.get('output', {})
        self.top_n_candidates = output_config.get('top_n_candidates', 10)
        
        # 初始化Tushare API
        api_config = config.get('api', {})
        self.token = api_config.get('api_key', '')
        if self.token:
            ts.set_token(self.token)
            self.pro_api = ts.pro_api()
        else:
            logger.error("Tushare token未配置")
            self.pro_api = None
        
        # 初始化组件
        self.data_loader = DataLoader(self.pro_api, config)
        self.trade_simulator = TradeSimulator(
            initial_capital=self.initial_capital,
            commission_rate=self.commission_rate,
            slippage=self.slippage
        )
        self.metrics_calculator = MetricsCalculator()
        
        # 初始化策略
        if strategy is not None:
            self.strategy = strategy
        else:
            self.strategy = LimitUpScoringStrategyV2(config)
        
        # 数据存储
        self.limit_up_data = pd.DataFrame()
        self.limit_up_by_date: Dict[str, pd.DataFrame] = {}
        self.trading_days: List[str] = []
        
        # 回测结果
        self.trades: List[Dict[str, Any]] = []
        self.equity_curve: List[Dict[str, Any]] = []
        self.positions_history: List[Dict[str, Any]] = []
        self.daily_results: List[Dict[str, Any]] = []
        self.metrics: Dict[str, Any] = {}
        self.final_capital = self.initial_capital
        self.backtest_completed = False
        
        # 候选股记录
        self.candidates_by_t_day: Dict[str, pd.DataFrame] = {}
        
        logger.info(f"BacktestEngine初始化完成: {start_date} - {end_date}")

    def load_historical_data(self):
        """
        加载历史数据
        
        使用DataLoader加载回测期间的所有涨停股数据，并按日期分组存储
        """
        logger.info(f"开始加载历史数据: {self.start_date} - {self.end_date}")
        
        # 加载涨停股数据
        self.limit_up_data = self.data_loader.load_limit_up_data(
            self.start_date, 
            self.end_date
        )
        
        if self.limit_up_data.empty:
            logger.warning("未加载到任何涨停数据")
            self.limit_up_by_date = {}
        else:
            # 按日期分组
            self.limit_up_by_date = {
                date: group for date, group in self.limit_up_data.groupby('trade_date')
            }
            logger.info(f"涨停数据加载完成: {len(self.limit_up_by_date)} 个交易日")
        
        # 获取交易日历
        self._load_trading_days()
        
        logger.info("历史数据加载完成")

    def _load_trading_days(self):
        """加载交易日历"""
        try:
            cal_df = self.pro_api.trade_cal(
                exchange='SSE',
                start_date=self.start_date,
                end_date=self.end_date,
                is_open='1'
            )
            
            if not cal_df.empty:
                self.trading_days = cal_df['cal_date'].tolist()
                logger.info(f"交易日历加载完成: {len(self.trading_days)} 个交易日")
            else:
                self.trading_days = []
                logger.warning("未获取到交易日历")
        except Exception as e:
            logger.error(f"加载交易日历失败: {e}")
            self.trading_days = []

    def _get_next_trading_day(self, trade_date: str) -> Optional[str]:
        """获取下一个交易日"""
        if not self.trading_days:
            return None
        
        try:
            idx = self.trading_days.index(trade_date)
            if idx + 1 < len(self.trading_days):
                return self.trading_days[idx + 1]
        except ValueError:
            pass
        return None

    def _get_next_next_trading_day(self, trade_date: str) -> Optional[str]:
        """获取下下个交易日 (T+2)"""
        if not self.trading_days:
            return None
        
        try:
            idx = self.trading_days.index(trade_date)
            if idx + 2 < len(self.trading_days):
                return self.trading_days[idx + 2]
        except ValueError:
            pass
        return None

    def run_backtest(self):
        """
        执行回测（核心方法）
        
        遍历回测期间的每个交易日：
        1. T日：获取涨停股列表，使用Strategy V2评分，选择前N名候选股
        2. T+1日：获取候选股的开盘价，执行买入操作
        3. T+2日：获取持仓股的收盘价，执行卖出操作
        4. 每日结束时：更新持仓市值，记录权益曲线
        """
        logger.info("开始执行回测...")
        
        if not self.trading_days:
            logger.warning("没有交易日，回测结束")
            self.backtest_completed = True
            return
        
        # 重置交易模拟器
        self.trade_simulator.reset()
        
        # 清空历史记录
        self.trades = []
        self.equity_curve = []
        self.positions_history = []
        self.daily_results = []
        self.candidates_by_t_day = {}
        
        # 遍历每个交易日
        for i, t_day in enumerate(self.trading_days):
            logger.info(f"处理T日: {t_day} ({i+1}/{len(self.trading_days)})")
            
            # 获取T+1和T+2日
            t1_day = self._get_next_trading_day(t_day)
            t2_day = self._get_next_next_trading_day(t_day)
            
            if not t1_day or not t2_day:
                logger.warning(f"日期 {t_day} 没有足够的后续交易日，跳过")
                continue
            
            # ===== T日：评分和选股 =====
            self._process_t_day(t_day, t1_day)
            
            # ===== T+1日：买入 =====
            self._process_t1_day(t1_day, t_day)
            
            # ===== T+2日：卖出 =====
            self._process_t2_day(t2_day)
            
            # ===== 每日结束时：记录权益 =====
            self._record_daily_equity(t1_day)
        
        # 回测完成
        self.backtest_completed = True
        self.final_capital = self.trade_simulator.get_cash()
        
        # 获取持仓市值
        positions = self.trade_simulator.get_all_positions()
        if positions and self.trading_days:
            last_day = self.trading_days[-1]
            position_value = self._calculate_position_value(positions, last_day)
            self.final_capital += position_value
        
        logger.info(f"回测完成: 初始资金={self.initial_capital}, 最终资金={self.final_capital:.2f}")

    def _process_t_day(self, t_day: str, t1_day: str):
        """
        处理T日：评分和选股
        
        Args:
            t_day: T日日期
            t1_day: T+1日日期
        """
        # 获取T日涨停股
        if t_day not in self.limit_up_by_date:
            logger.debug(f"T日 {t_day} 无涨停数据")
            return
        
        limit_up_stocks = self.limit_up_by_date[t_day]
        if limit_up_stocks.empty:
            logger.debug(f"T日 {t_day} 无涨停股票")
            return
        
        logger.info(f"T日 {t_day}: 发现 {len(limit_up_stocks)} 只涨停股")
        
        try:
            # 使用Strategy V2进行评分
            scored_stocks = self.strategy.calculate_t_day_score(limit_up_stocks, t_day)
            
            if scored_stocks.empty:
                logger.warning(f"T日 {t_day} 评分后无候选股")
                return
            
            # 选择前N名
            top_candidates = scored_stocks.head(self.top_n_candidates)
            self.candidates_by_t_day[t_day] = top_candidates
            
            logger.info(f"T日 {t_day}: 选出 {len(top_candidates)} 只候选股")
            
            # 输出前几名信息
            for idx, row in top_candidates.head(3).iterrows():
                logger.info(f"  TOP{idx+1}: {row['name']} ({row['ts_code']}) - 总分: {row['total_score']:.1f}")
        
        except Exception as e:
            logger.error(f"T日 {t_day} 评分失败: {e}")

    def _process_t1_day(self, t1_day: str, t_day: str):
        """
        处理T+1日：买入
        
        Args:
            t1_day: T+1日日期
            t_day: T日日期（用于获取候选股）
        """
        # 获取T日的候选股
        if t_day not in self.candidates_by_t_day:
            return
        
        candidates = self.candidates_by_t_day[t_day]
        if candidates.empty:
            return
        
        logger.info(f"T+1日 {t1_day}: 处理 {len(candidates)} 只候选股的买入")
        
        # 获取当前持仓数量
        current_positions = len(self.trade_simulator.get_all_positions())
        available_slots = self.max_positions - current_positions
        
        if available_slots <= 0:
            logger.info(f"T+1日 {t1_day}: 已达最大持仓数量 {self.max_positions}，跳过买入")
            return
        
        # 计算每只股票的目标仓位
        cash = self.trade_simulator.get_cash()
        position_value = cash * self.position_size
        
        # 遍历候选股，尝试买入
        buy_count = 0
        for idx, row in candidates.iterrows():
            if buy_count >= available_slots:
                break
            
            ts_code = row['ts_code']
            name = row.get('name', '')
            
            # 检查是否已有持仓
            if self.trade_simulator.get_position(ts_code) is not None:
                logger.debug(f"股票 {ts_code} 已有持仓，跳过")
                continue
            
            try:
                # 获取T+1日开盘价
                daily_data = self.data_loader.load_daily_price(ts_code, t1_day)
                
                if not daily_data:
                    logger.warning(f"T+1日 {t1_day}: 无法获取 {ts_code} 的日线数据")
                    continue
                
                open_price = daily_data['open']
                if open_price <= 0:
                    logger.warning(f"T+1日 {t1_day}: {ts_code} 开盘价无效 {open_price}")
                    continue
                
                # 计算可买入数量（100股为单位）
                amount = int(position_value / open_price / 100) * 100
                
                if amount < 100:
                    logger.warning(f"T+1日 {t1_day}: {ts_code} 资金不足，无法买入")
                    continue
                
                # 执行买入
                trade_record = self.trade_simulator.execute_buy(
                    ts_code=ts_code,
                    name=name,
                    price=open_price,
                    amount=amount,
                    trade_date=t1_day
                )
                
                self.trades.append(trade_record)
                buy_count += 1
                
                logger.info(f"T+1日 {t1_day}: 买入 {name} ({ts_code}) {amount}股 @ {open_price:.2f}")
            
            except ValueError as e:
                logger.warning(f"T+1日 {t1_day}: 买入 {ts_code} 失败 - {e}")
            except Exception as e:
                logger.error(f"T+1日 {t1_day}: 买入 {ts_code} 异常 - {e}")
        
        if buy_count > 0:
            logger.info(f"T+1日 {t1_day}: 成功买入 {buy_count} 只股票")

    def _process_t2_day(self, t2_day: str):
        """
        处理T+2日：卖出
        
        Args:
            t2_day: T+2日日期
        """
        # 获取当前持仓
        positions = self.trade_simulator.get_all_positions()
        
        if not positions:
            return
        
        logger.info(f"T+2日 {t2_day}: 处理 {len(positions)} 只持仓的卖出")
        
        sell_count = 0
        for position in positions:
            ts_code = position['ts_code']
            
            try:
                # 获取T+2日收盘价
                daily_data = self.data_loader.load_daily_price(ts_code, t2_day)
                
                if not daily_data:
                    logger.warning(f"T+2日 {t2_day}: 无法获取 {ts_code} 的日线数据")
                    continue
                
                close_price = daily_data['close']
                if close_price <= 0:
                    logger.warning(f"T+2日 {t2_day}: {ts_code} 收盘价无效 {close_price}")
                    continue
                
                # 执行卖出
                trade_record = self.trade_simulator.execute_sell(
                    ts_code=ts_code,
                    price=close_price,
                    trade_date=t2_day
                )
                
                if trade_record:
                    self.trades.append(trade_record)
                    sell_count += 1
                    
                    profit = trade_record.get('profit', 0)
                    profit_pct = trade_record.get('profit_pct', 0) * 100
                    logger.info(f"T+2日 {t2_day}: 卖出 {ts_code} @ {close_price:.2f}, "
                              f"盈亏: {profit:.2f} ({profit_pct:.2f}%)")
            
            except Exception as e:
                logger.error(f"T+2日 {t2_day}: 卖出 {ts_code} 异常 - {e}")
        
        if sell_count > 0:
            logger.info(f"T+2日 {t2_day}: 成功卖出 {sell_count} 只股票")

    def _calculate_position_value(self, positions: List[Dict], trade_date: str) -> float:
        """
        计算持仓市值
        
        Args:
            positions: 持仓列表
            trade_date: 交易日期
            
        Returns:
            持仓总市值
        """
        total_value = 0.0
        
        for position in positions:
            ts_code = position['ts_code']
            amount = position['amount']
            
            try:
                daily_data = self.data_loader.load_daily_price(ts_code, trade_date)
                if daily_data:
                    close_price = daily_data['close']
                    total_value += close_price * amount
            except Exception as e:
                logger.debug(f"计算持仓市值失败 {ts_code}: {e}")
                # 使用持仓中的当前价格
                total_value += position.get('market_value', 0)
        
        return total_value

    def _record_daily_equity(self, date: str):
        """
        记录每日权益
        
        Args:
            date: 日期
        """
        cash = self.trade_simulator.get_cash()
        positions = self.trade_simulator.get_all_positions()
        
        position_value = 0.0
        if positions and date:
            position_value = self._calculate_position_value(positions, date)
        
        total_equity = cash + position_value
        
        self.equity_curve.append({
            'date': date,
            'equity': total_equity,
            'cash': cash,
            'position_value': position_value
        })
        
        self.positions_history.append({
            'date': date,
            'positions': positions.copy()
        })
        
        self.daily_results.append({
            'date': date,
            'cash': cash,
            'position_value': position_value,
            'total_equity': total_equity,
            'position_count': len(positions)
        })
        
        logger.debug(f"记录权益 {date}: 总权益={total_equity:.2f}, 现金={cash:.2f}, 持仓={position_value:.2f}")

    def calculate_metrics(self):
        """
        计算回测指标
        
        使用MetricsCalculator计算所有绩效指标
        """
        logger.info("开始计算绩效指标...")
        
        if not self.trades:
            logger.warning("没有交易记录，无法计算指标")
            self.metrics = {
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': 0.0,
                'profit_loss_ratio': 0.0,
                'average_return': 0.0,
                'total_return': 0.0,
                'annual_return': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
                'max_drawdown_value': 0.0,
                'volatility': 0.0,
                'calmar_ratio': 0.0,
                'profit_factor': 0.0
            }
            return
        
        # 准备交易数据
        sell_trades = [t for t in self.trades if t['action'] == 'sell']
        
        # 准备权益曲线数据
        equity_curve_for_metrics = [
            {'date': point['date'], 'value': point['equity']} 
            for point in self.equity_curve
        ]
        
        # 计算总交易天数
        total_days = len(self.equity_curve) if self.equity_curve else 0
        
        # 使用MetricsCalculator计算指标
        self.metrics = self.metrics_calculator.calculate_all_metrics(
            trades=sell_trades,
            equity_curve=equity_curve_for_metrics,
            total_days=total_days
        )
        
        logger.info("绩效指标计算完成")
        
        # 输出关键指标
        logger.info(f"总交易次数: {self.metrics['total_trades']}")
        logger.info(f"胜率: {self.metrics['win_rate']*100:.2f}%")
        logger.info(f"总收益率: {self.metrics['total_return']*100:.2f}%")
        logger.info(f"最大回撤: {self.metrics['max_drawdown']*100:.2f}%")
        logger.info(f"夏普比率: {self.metrics['sharpe_ratio']:.2f}")

    def generate_report(self) -> Dict[str, Any]:
        """
        生成回测报告
        
        Returns:
            包含所有回测结果的字典
        """
        logger.info("生成回测报告...")
        
        report = self.get_results()
        
        # 添加额外信息
        report['generated_at'] = datetime.now().isoformat()
        report['config'] = {
            'initial_capital': self.initial_capital,
            'commission_rate': self.commission_rate,
            'slippage': self.slippage,
            'position_size': self.position_size,
            'max_positions': self.max_positions,
            'top_n_candidates': self.top_n_candidates
        }
        
        logger.info("回测报告生成完成")
        
        return report

    def get_results(self) -> Dict[str, Any]:
        """
        获取回测结果
        
        Returns:
            完整的回测结果字典
        """
        return {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'initial_capital': self.initial_capital,
            'final_capital': self.final_capital,
            'total_return': (self.final_capital - self.initial_capital) / self.initial_capital 
                          if self.initial_capital > 0 else 0,
            'trades': self.trades.copy(),
            'equity_curve': self.equity_curve.copy(),
            'metrics': self.metrics.copy() if self.metrics else {},
            'positions_history': self.positions_history.copy(),
            'daily_results': self.daily_results.copy(),
            'backtest_completed': self.backtest_completed
        }
