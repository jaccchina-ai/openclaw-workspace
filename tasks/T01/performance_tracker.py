#!/usr/bin/env python3
"""
T01系统绩效跟踪模块
统计胜率，计算绩效指标，为机器学习提供训练数据
胜率标准: T+1日开盘价买入，T+2日收盘价卖出
成功判定: 卖出价/买入价 >= success_threshold (默认1.03, 即3%收益)
统计范围: T+1日竞价阶段最终推荐的top_n股票 (默认前3名)
"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import tushare as ts
import yaml

from data_storage import T01DataStorage

logger = logging.getLogger(__name__)


class PerformanceTracker:
    """绩效跟踪器"""
    
    def __init__(self, config_path='config.yaml'):
        """初始化绩效跟踪器"""
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # 绩效跟踪配置
        perf_config = self.config.get('performance_tracking', {})
        self.buy_time = perf_config.get('buy_time', 'T+1日09:30')
        self.sell_time = perf_config.get('sell_time', 'T+2日15:00')
        self.buy_price = perf_config.get('buy_price', '开盘价')
        self.sell_price = perf_config.get('sell_price', '收盘价')
        self.min_trades = perf_config.get('min_trades_for_statistics', 20)
        self.confidence_interval = perf_config.get('confidence_interval', 0.95)
        # 成功阈值: 卖出价/买入价 >= success_threshold 算成功 (默认3%收益)
        self.success_threshold = perf_config.get('success_threshold', 1.03)
        
        # 数据存储
        self.storage = T01DataStorage(config_path)
        
        # tushare配置
        api_key = self.config['api']['api_key']
        ts.set_token(api_key)
        self.pro = ts.pro_api()
        
        logger.info("绩效跟踪器初始化完成")
    
    def calculate_trade_performance(self, recommendation_id: str) -> Optional[Dict[str, Any]]:
        """
        计算单个推荐的交易表现
        
        Args:
            recommendation_id: 推荐记录ID
            
        Returns:
            表现数据字典，如果无法计算返回None
        """
        try:
            # 获取推荐记录
            recommendation = self.storage.get_recommendation(recommendation_id)
            if not recommendation:
                logger.warning(f"推荐记录不存在: {recommendation_id}")
                return None
            
            # 获取交易记录
            trades = self.storage.get_trades_by_recommendation(recommendation_id)
            
            # 查找买入和卖出交易
            buy_trade = None
            sell_trade = None
            
            for trade in trades:
                if trade['trade_type'] == 'buy' and trade['status'] == 'completed':
                    buy_trade = trade
                elif trade['trade_type'] == 'sell' and trade['status'] == 'completed':
                    sell_trade = trade
            
            # 如果数据库中没有完整的交易记录，尝试根据规则计算
            if not buy_trade:
                # 根据规则计算买入数据
                trade_date = recommendation['trade_date']  # T日
                t1_date = recommendation['t1_date']        # T+1日
                ts_code = recommendation['ts_code']
                
                # 获取T+1日开盘价作为买入价
                buy_price = self._get_stock_price(ts_code, t1_date, price_type='open')
                if buy_price is None:
                    logger.warning(f"无法获取股票 {ts_code} 在 {t1_date} 的开盘价")
                    return None
                
                buy_trade = {
                    'trade_type': 'buy',
                    'trade_date': t1_date,
                    'trade_time': '09:30',
                    'price': buy_price,
                    'quantity': 1000,  # 默认1000股
                    'amount': buy_price * 1000,
                    'status': 'simulated'
                }
                
                # 保存到数据库
                buy_trade_id = self.storage.record_trade(recommendation_id, buy_trade)
                buy_trade['trade_id'] = buy_trade_id
            
            # 计算卖出数据
            if not sell_trade:
                # 计算T+2日
                buy_date = buy_trade['trade_date']
                t2_date = self._get_next_trading_day(buy_date)
                
                if not t2_date:
                    logger.warning(f"无法计算 {buy_date} 的T+2日")
                    return None
                
                # 获取T+2日收盘价作为卖出价
                sell_price = self._get_stock_price(recommendation['ts_code'], t2_date, price_type='close')
                if sell_price is None:
                    logger.warning(f"无法获取股票 {recommendation['ts_code']} 在 {t2_date} 的收盘价")
                    return None
                
                sell_trade = {
                    'trade_type': 'sell',
                    'trade_date': t2_date,
                    'trade_time': '15:00',
                    'price': sell_price,
                    'quantity': buy_trade['quantity'],
                    'amount': sell_price * buy_trade['quantity'],
                    'status': 'simulated'
                }
                
                # 保存到数据库
                sell_trade_id = self.storage.record_trade(recommendation_id, sell_trade)
                sell_trade['trade_id'] = sell_trade_id
            
            # 计算持有天数
            buy_date = datetime.strptime(buy_trade['trade_date'], '%Y%m%d')
            sell_date = datetime.strptime(sell_trade['trade_date'], '%Y%m%d')
            holding_days = (sell_date - buy_date).days
            
            # 计算收益率
            buy_price = buy_trade['price']
            sell_price = sell_trade['price']
            return_pct = (sell_price - buy_price) / buy_price * 100 if buy_price > 0 else 0
            
            # 判断盈亏 (使用成功阈值: 卖出价/买入价 >= success_threshold)
            price_ratio = sell_price / buy_price if buy_price > 0 else 0
            win_loss = 1 if price_ratio >= self.success_threshold else 0
            
            # 计算最大回撤（简化版：使用期间最低价）
            # 实际应该计算每日回撤，这里简化处理
            max_drawdown = self._calculate_max_drawdown(
                recommendation['ts_code'],
                buy_trade['trade_date'],
                sell_trade['trade_date']
            )
            
            # 计算夏普比率（简化版，假设无风险利率为0）
            sharpe_ratio = return_pct / (abs(max_drawdown) + 0.01) if abs(max_drawdown) > 0.01 else 0
            
            # 组装表现数据
            performance_data = {
                'buy_date': buy_trade['trade_date'],
                'buy_price': buy_price,
                'sell_date': sell_trade['trade_date'],
                'sell_price': sell_price,
                'holding_days': holding_days,
                'return_pct': return_pct,
                'win_loss': win_loss,
                'max_drawdown': max_drawdown,
                'sharpe_ratio': sharpe_ratio,
                'buy_trade_id': buy_trade.get('trade_id'),
                'sell_trade_id': sell_trade.get('trade_id')
            }
            
            # 保存表现数据
            perf_id = self.storage.record_performance(recommendation_id, performance_data)
            performance_data['performance_id'] = perf_id
            
            logger.debug(f"计算表现完成: {recommendation_id} - 收益率: {return_pct:.2f}%, 胜败: {'盈利' if win_loss == 1 else '亏损'}")
            
            return performance_data
            
        except Exception as e:
            logger.error(f"计算交易表现失败: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _get_stock_price(self, ts_code: str, trade_date: str, price_type: str = 'open') -> Optional[float]:
        """获取股票价格"""
        try:
            if price_type == 'open':
                fields = 'open'
            elif price_type == 'close':
                fields = 'close'
            elif price_type == 'high':
                fields = 'high'
            elif price_type == 'low':
                fields = 'low'
            else:
                fields = 'close'
            
            # 尝试获取日线数据
            df = self.pro.daily(
                ts_code=ts_code,
                trade_date=trade_date,
                fields=fields
            )
            
            if not df.empty:
                return float(df.iloc[0][fields])
            
            # 如果日线数据失败，尝试竞价数据
            if price_type == 'open':
                df = self.pro.stk_auction_o(
                    trade_date=trade_date,
                    ts_code=ts_code,
                    fields='open'
                )
                if not df.empty:
                    return float(df.iloc[0]['open'])
            
            return None
            
        except Exception as e:
            logger.debug(f"获取股票价格失败: {ts_code} {trade_date} {price_type} - {e}")
            return None
    
    def _get_next_trading_day(self, trade_date: str) -> Optional[str]:
        """获取下一个交易日"""
        try:
            from datetime import datetime, timedelta
            
            current_dt = datetime.strptime(trade_date, '%Y%m%d')
            # 查询未来30天
            start_date = trade_date
            end_date = (current_dt + timedelta(days=30)).strftime('%Y%m%d')
            
            cal_df = self.pro.trade_cal(
                exchange='SSE',
                start_date=start_date,
                end_date=end_date,
                fields='cal_date,is_open'
            )
            
            if cal_df.empty:
                return None
            
            cal_df = cal_df.sort_values('cal_date', ascending=True)
            
            # 找到当前日期
            current_idx = -1
            for i, row in cal_df.iterrows():
                if row['cal_date'] == trade_date:
                    current_idx = i
                    break
            
            if current_idx == -1:
                return None
            
            # 向后查找下一个交易日
            for i in range(current_idx + 1, len(cal_df)):
                if cal_df.iloc[i]['is_open'] == 1:
                    return cal_df.iloc[i]['cal_date']
            
            return None
            
        except Exception as e:
            logger.debug(f"获取下一个交易日失败: {trade_date} - {e}")
            return None
    
    def _calculate_max_drawdown(self, ts_code: str, start_date: str, end_date: str) -> float:
        """计算最大回撤（简化版）"""
        try:
            # 获取期间日线数据
            df = self.pro.daily(
                ts_code=ts_code,
                start_date=start_date,
                end_date=end_date,
                fields='trade_date,high,low,close'
            )
            
            if df.empty or len(df) < 2:
                return 0.0
            
            # 计算每日回撤
            df = df.sort_values('trade_date')
            peak = df.iloc[0]['close']
            max_drawdown = 0.0
            
            for i in range(1, len(df)):
                current_close = df.iloc[i]['close']
                if current_close > peak:
                    peak = current_close
                else:
                    drawdown = (peak - current_close) / peak * 100
                    max_drawdown = max(max_drawdown, drawdown)
            
            return max_drawdown
            
        except Exception as e:
            logger.debug(f"计算最大回撤失败: {ts_code} {start_date}-{end_date} - {e}")
            return 0.0
    
    def calculate_portfolio_performance(self, start_date: str = None, end_date: str = None, top_n: int = 3) -> Dict[str, Any]:
        """
        计算组合表现
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            top_n: 只统计每天前N名推荐 (默认3名，对应T+1竞价阶段最终推荐)
            
        Returns:
            组合表现统计
        """
        try:
            # 获取策略配置中的final_recommendation_count
            strategy_config = self.config.get('strategy', {})
            output_config = strategy_config.get('output', {})
            final_count = output_config.get('final_recommendation_count', 3)
            # 使用配置值或传入值
            top_n = top_n or final_count
            
            # 获取所有已完成的表现记录
            conditions = []
            params = []
            
            if start_date:
                conditions.append("p.buy_date >= ?")
                params.append(start_date)
            
            if end_date:
                conditions.append("p.buy_date <= ?")
                params.append(end_date)
            
            where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""
            
            query = f'''
            SELECT p.*, r.ts_code, r.name, r.total_score, r.t_day_score, r.auction_score,
                   ROW_NUMBER() OVER (PARTITION BY p.buy_date ORDER BY r.total_score DESC) as rank
            FROM {self.storage.table_performance} p
            JOIN {self.storage.table_recommendations} r ON p.recommendation_id = r.recommendation_id
            {where_clause}
            AND p.win_loss IN (0, 1)
            ORDER BY p.buy_date, rank
            '''
            
            self.storage.cursor.execute(query, params)
            rows = self.storage.cursor.fetchall()
            
            if not rows:
                return {
                    'total_trades': 0,
                    'win_rate': 0,
                    'message': '暂无完成交易的记录'
                }
            
            # 转换为DataFrame
            df = pd.DataFrame([dict(row) for row in rows])
            
            # 只统计每天前top_n名推荐 (T+1竞价阶段最终推荐)
            original_count = len(df)
            df = df[df['rank'] <= top_n]
            filtered_count = len(df)
            
            if original_count != filtered_count:
                logger.info(f"胜率统计范围过滤: 原始{original_count}条记录 -> 过滤后{filtered_count}条 (每天前{top_n}名)")
            
            # 计算基本统计
            total_trades = len(df)
            winning_trades = len(df[df['win_loss'] == 1])
            losing_trades = len(df[df['win_loss'] == 0])
            
            win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
            
            # 计算收益率统计
            avg_return = df['return_pct'].mean()
            median_return = df['return_pct'].median()
            std_return = df['return_pct'].std()
            max_return = df['return_pct'].max()
            min_return = df['return_pct'].min()
            
            # 计算夏普比率（年化，假设252个交易日）
            if std_return > 0:
                sharpe_ratio = (avg_return * np.sqrt(252)) / (std_return * 100)
            else:
                sharpe_ratio = 0
            
            # 计算最大回撤（组合层面）
            cumulative_returns = (1 + df['return_pct'] / 100).cumprod()
            running_max = cumulative_returns.expanding().max()
            drawdowns = (cumulative_returns - running_max) / running_max * 100
            max_drawdown = drawdowns.min()
            
            # 计算盈亏因子
            total_profit = df[df['return_pct'] > 0]['return_pct'].sum()
            total_loss = abs(df[df['return_pct'] < 0]['return_pct'].sum())
            profit_factor = total_profit / total_loss if total_loss > 0 else float('inf')
            
            # 按股票分析
            stock_stats = df.groupby('ts_code').agg({
                'return_pct': ['count', 'mean', 'std'],
                'win_loss': 'sum'
            }).round(2)
            
            stock_stats.columns = ['trades_count', 'avg_return', 'std_return', 'win_count']
            stock_stats['win_rate'] = (stock_stats['win_count'] / stock_stats['trades_count'] * 100).round(1)
            
            # 按评分区间分析
            df['score_bin'] = pd.cut(df['total_score'], bins=[0, 50, 70, 85, 100, 200], 
                                      labels=['<50', '50-70', '70-85', '85-100', '>100'])
            score_stats = df.groupby('score_bin').agg({
                'return_pct': ['count', 'mean', 'std'],
                'win_loss': 'sum'
            }).round(2)
            
            if not score_stats.empty:
                score_stats.columns = ['trades_count', 'avg_return', 'std_return', 'win_count']
                score_stats['win_rate'] = (score_stats['win_count'] / score_stats['trades_count'] * 100).round(1)
            
            # 置信区间计算
            if total_trades >= self.min_trades:
                # 胜率的置信区间（二项分布近似为正态分布）
                from scipy import stats
                z = stats.norm.ppf((1 + self.confidence_interval) / 2)
                se = np.sqrt(win_rate * (100 - win_rate) / total_trades) / 100
                ci_lower = win_rate - z * se * 100
                ci_upper = win_rate + z * se * 100
            else:
                ci_lower = ci_upper = None
            
            # 组装结果
            result = {
                'summary': {
                    'total_trades': int(total_trades),
                    'winning_trades': int(winning_trades),
                    'losing_trades': int(losing_trades),
                    'win_rate_pct': round(win_rate, 2),
                    'avg_return_pct': round(avg_return, 2),
                    'median_return_pct': round(median_return, 2),
                    'std_return_pct': round(std_return, 2),
                    'max_return_pct': round(max_return, 2),
                    'min_return_pct': round(min_return, 2),
                    'sharpe_ratio': round(sharpe_ratio, 3),
                    'max_drawdown_pct': round(max_drawdown, 2),
                    'profit_factor': round(profit_factor, 2) if profit_factor != float('inf') else 'inf'
                },
                'confidence_interval': {
                    'level': self.confidence_interval,
                    'win_rate_lower': round(ci_lower, 2) if ci_lower is not None else None,
                    'win_rate_upper': round(ci_upper, 2) if ci_upper is not None else None,
                    'sufficient_data': total_trades >= self.min_trades,
                    'min_trades_required': self.min_trades
                },
                'by_stock': stock_stats.to_dict('index') if not stock_stats.empty else {},
                'by_score': score_stats.to_dict('index') if not score_stats.empty else {},
                'time_period': {
                    'start_date': start_date,
                    'end_date': end_date,
                    'trades_count': int(total_trades)
                }
            }
            
            logger.info(f"组合表现计算完成: {total_trades}笔交易，胜率: {win_rate:.1f}%")
            
            return result
            
        except Exception as e:
            logger.error(f"计算组合表现失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'error': str(e),
                'total_trades': 0,
                'win_rate': 0
            }
    
    def generate_performance_report(self, start_date: str = None, end_date: str = None, top_n: int = 3) -> str:
        """生成绩效报告文本
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            top_n: 只统计每天前N名推荐 (默认3名)
        """
        try:
            performance = self.calculate_portfolio_performance(start_date, end_date, top_n)
            
            if 'error' in performance:
                return f"❌ 生成绩效报告失败: {performance['error']}"
            
            summary = performance.get('summary', {})
            ci = performance.get('confidence_interval', {})
            time_period = performance.get('time_period', {})
            
            report_parts = []
            
            # 标题
            report_parts.append("="*60)
            report_parts.append("📊 T01策略绩效报告")
            report_parts.append("="*60)
            
            # 统计规则说明
            report_parts.append(f"📋 统计规则:")
            report_parts.append(f"  - 买入: T+1日09:30开盘价")
            report_parts.append(f"  - 卖出: T+2日15:00收盘价")
            report_parts.append(f"  - 成功标准: 收益率 >= {(self.success_threshold - 1) * 100:.1f}%")
            report_parts.append(f"  - 统计范围: 每天前{top_n}名推荐")
            report_parts.append("")
            
            # 时间范围
            if time_period.get('start_date') or time_period.get('end_date'):
                start = time_period.get('start_date', '最早')
                end = time_period.get('end_date', '最新')
                report_parts.append(f"统计期间: {start} 至 {end}")
                report_parts.append(f"交易笔数: {time_period.get('trades_count', 0)}")
            
            report_parts.append("")
            
            # 核心指标
            report_parts.append("🎯 核心绩效指标")
            report_parts.append("-"*40)
            report_parts.append(f"胜率: {summary.get('win_rate_pct', 0):.1f}%")
            report_parts.append(f"平均收益率: {summary.get('avg_return_pct', 0):.2f}%")
            report_parts.append(f"盈亏因子: {summary.get('profit_factor', 0):.2f}")
            report_parts.append(f"夏普比率: {summary.get('sharpe_ratio', 0):.3f}")
            report_parts.append(f"最大回撤: {summary.get('max_drawdown_pct', 0):.2f}%")
            
            # 置信区间
            if ci.get('sufficient_data'):
                report_parts.append("")
                report_parts.append("📈 统计置信度")
                report_parts.append(f"置信区间 ({ci.get('level', 0.95)*100:.0f}%): [{ci.get('win_rate_lower', 0):.1f}%, {ci.get('win_rate_upper', 0):.1f}%]")
            else:
                report_parts.append("")
                report_parts.append(f"⚠️  数据不足，需要至少 {ci.get('min_trades_required', 20)} 笔交易进行统计")
            
            # 按股票分析
            by_stock = performance.get('by_stock', {})
            if by_stock:
                report_parts.append("")
                report_parts.append("📋 股票表现分析")
                report_parts.append("-"*40)
                
                for ts_code, stats in list(by_stock.items())[:10]:  # 显示前10只
                    trades = stats.get('trades_count', 0)
                    win_rate = stats.get('win_rate', 0)
                    avg_return = stats.get('avg_return', 0)
                    report_parts.append(f"{ts_code}: {trades}次，胜率{win_rate:.1f}%，均收益{avg_return:.2f}%")
            
            # 按评分分析
            by_score = performance.get('by_score', {})
            if by_score:
                report_parts.append("")
                report_parts.append("🏆 评分区间表现")
                report_parts.append("-"*40)
                
                for score_bin, stats in by_score.items():
                    trades = stats.get('trades_count', 0)
                    win_rate = stats.get('win_rate', 0)
                    avg_return = stats.get('avg_return', 0)
                    report_parts.append(f"{score_bin}分: {trades}次，胜率{win_rate:.1f}%，均收益{avg_return:.2f}%")
            
            # 建议
            report_parts.append("")
            report_parts.append("💡 改进建议")
            report_parts.append("-"*40)
            
            win_rate = summary.get('win_rate_pct', 0)
            if win_rate > 60:
                report_parts.append("✅ 策略表现优秀，继续保持")
            elif win_rate > 50:
                report_parts.append("📈 策略表现良好，有优化空间")
            elif win_rate > 40:
                report_parts.append("⚠️  策略表现一般，建议优化")
            else:
                report_parts.append("❌ 策略表现不佳，需要重大调整")
            
            if summary.get('max_drawdown_pct', 0) > 20:
                report_parts.append("📉 回撤过大，需要加强风险控制")
            
            report_parts.append("")
            report_parts.append("生成时间: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            
            return "\n".join(report_parts)
            
        except Exception as e:
            return f"❌ 生成绩效报告失败: {e}"
    
    def get_training_data_for_ml(self) -> pd.DataFrame:
        """
        获取机器学习训练数据
        
        Returns:
            包含特征和标签的DataFrame
        """
        try:
            # 获取所有已完成的表现记录及其推荐数据
            query = f'''
            SELECT 
                p.*,
                r.trade_date, r.ts_code, r.name,
                r.total_score, r.t_day_score, r.auction_score,
                r.open_change_pct,
                json_extract(r.recommendation_json, '$.seal_ratio') as seal_ratio,
                json_extract(r.recommendation_json, '$.seal_to_mv') as seal_to_mv,
                json_extract(r.recommendation_json, '$.turnover_ratio') as turnover_ratio,
                json_extract(r.recommendation_json, '$.is_hot_sector') as is_hot_sector,
                json_extract(r.recommendation_json, '$.pct_chg') as pct_chg
            FROM {self.storage.table_performance} p
            JOIN {self.storage.table_recommendations} r ON p.recommendation_id = r.recommendation_id
            WHERE p.win_loss IN (0, 1)
            '''
            
            self.storage.cursor.execute(query)
            rows = self.storage.cursor.fetchall()
            
            if not rows:
                logger.warning("暂无训练数据")
                return pd.DataFrame()
            
            # 转换为DataFrame
            df = pd.DataFrame([dict(row) for row in rows])
            
            # 数据清洗和特征工程
            # 转换数据类型
            numeric_cols = ['total_score', 't_day_score', 'auction_score', 'open_change_pct',
                           'seal_ratio', 'seal_to_mv', 'turnover_ratio', 'pct_chg']
            
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            # 处理布尔值
            if 'is_hot_sector' in df.columns:
                df['is_hot_sector'] = df['is_hot_sector'].map({'true': 1, 'false': 0, True: 1, False: 0})
                df['is_hot_sector'] = df['is_hot_sector'].fillna(0).astype(int)
            
            # 标签：win_loss (0:亏损, 1:盈利)
            df['label'] = df['win_loss']
            
            # 添加衍生特征
            df['score_ratio'] = df['auction_score'] / (df['t_day_score'] + 0.01)
            df['total_to_open_ratio'] = df['total_score'] / (abs(df['open_change_pct']) + 1)
            
            logger.info(f"获取训练数据: {len(df)} 条记录，{len(df.columns)} 个特征")
            
            return df
            
        except Exception as e:
            logger.error(f"获取训练数据失败: {e}")
            return pd.DataFrame()


def main():
    """测试函数"""
    logging.basicConfig(level=logging.INFO)
    
    tracker = PerformanceTracker()
    
    try:
        # 测试组合表现计算
        print("🔍 计算组合表现...")
        performance = tracker.calculate_portfolio_performance()
        
        if performance.get('total_trades', 0) > 0:
            summary = performance['summary']
            print(f"\n📊 组合表现统计:")
            print(f"  总交易: {summary['total_trades']}")
            print(f"  胜率: {summary['win_rate_pct']:.1f}%")
            print(f"  平均收益率: {summary['avg_return_pct']:.2f}%")
            print(f"  盈亏因子: {summary['profit_factor']:.2f}")
            
            # 生成报告
            report = tracker.generate_performance_report()
            print(f"\n{report}")
        else:
            print("⚠️  暂无完成交易的记录")
        
        # 测试训练数据获取
        print("\n🔍 获取训练数据...")
        train_df = tracker.get_training_data_for_ml()
        if not train_df.empty:
            print(f"✅ 获取到 {len(train_df)} 条训练数据")
            print(f"   特征数量: {len(train_df.columns) - 1}")  # 减去标签列
            print(f"   正样本(盈利): {len(train_df[train_df['label'] == 1])}")
            print(f"   负样本(亏损): {len(train_df[train_df['label'] == 0])}")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()