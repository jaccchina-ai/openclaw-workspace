"""
指标计算模块

计算回测结果的各种绩效指标和风险指标
"""

import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple, Optional


class MetricsCalculator:
    """
    指标计算器

    计算策略回测的各种绩效和风险指标，包括：
    - 收益率指标（总收益率、年化收益率、超额收益）
    - 风险指标（最大回撤、波动率、夏普比率）
    - 交易指标（胜率、盈亏比、交易次数）
    - 综合评分

    Attributes:
        risk_free_rate: 无风险利率
        benchmark: 基准指数
    """

    def __init__(self):
        """初始化指标计算器"""
        self.risk_free_rate = 0.03  # 默认无风险利率3%
    
    def calculate_win_rate(self, trades: List[Dict]) -> float:
        """
        计算胜率
        
        Args:
            trades: 交易列表，每个交易包含'return'键
            
        Returns:
            胜率（0-1之间的小数）
        """
        if not trades:
            return 0.0
        
        winning_trades = sum(1 for t in trades if t.get('return', 0) > 0)
        return winning_trades / len(trades)
    
    def calculate_profit_loss_ratio(self, trades: List[Dict]) -> float:
        """
        计算盈亏比
        
        Args:
            trades: 交易列表，每个交易包含'profit'键
            
        Returns:
            盈亏比（平均盈利/平均亏损的绝对值）
            如果没有亏损交易，返回平均盈利
        """
        if not trades:
            return 0.0
        
        profits = [t.get('profit', 0) for t in trades if t.get('profit', 0) > 0]
        losses = [t.get('profit', 0) for t in trades if t.get('profit', 0) < 0]
        
        avg_profit = sum(profits) / len(profits) if profits else 0
        avg_loss = abs(sum(losses) / len(losses)) if losses else 0
        
        if avg_loss == 0:
            return avg_profit
        return avg_profit / avg_loss
    
    def calculate_average_return(self, trades: List[Dict]) -> float:
        """
        计算平均收益率
        
        Args:
            trades: 交易列表，每个交易包含'return'键
            
        Returns:
            平均每次交易的收益率
        """
        if not trades:
            return 0.0
        
        returns = [t.get('return', 0) for t in trades]
        return sum(returns) / len(returns)
    
    def calculate_sharpe_ratio(self, returns: np.ndarray, risk_free_rate: float = 0.03) -> float:
        """
        计算夏普比率
        
        夏普比率 = (年化收益率 - 无风险利率) / 年化波动率
        
        Args:
            returns: 日收益率数组
            risk_free_rate: 无风险利率（年化），默认3%
            
        Returns:
            夏普比率，如果波动率为0则返回0
        """
        if len(returns) == 0:
            return 0.0
        
        # 计算日均收益率
        daily_return = np.mean(returns)
        
        # 计算日波动率
        daily_volatility = np.std(returns, ddof=1)
        
        if daily_volatility == 0:
            return 0.0
        
        # 年化收益率 = (1 + 日均收益)^252 - 1
        annual_return = (1 + daily_return) ** 252 - 1
        
        # 年化波动率 = 日波动率 * sqrt(252)
        annual_volatility = daily_volatility * np.sqrt(252)
        
        # 夏普比率
        sharpe = (annual_return - risk_free_rate) / annual_volatility
        
        return sharpe
    
    def calculate_max_drawdown(self, equity_curve: List[Dict]) -> Tuple[float, float, Optional[datetime], Optional[datetime]]:
        """
        计算最大回撤
        
        最大回撤 = (峰值 - 谷值) / 峰值
        
        Args:
            equity_curve: 权益曲线列表，每个元素包含'date'和'value'
            
        Returns:
            (最大回撤值, 最大回撤百分比, 回撤开始日期, 回撤结束日期)
        """
        if len(equity_curve) < 2:
            return 0.0, 0.0, None, None
        
        max_drawdown = 0.0
        max_drawdown_value = 0.0
        peak_value = equity_curve[0]['value']
        peak_date = equity_curve[0]['date']
        drawdown_start = peak_date
        drawdown_end = peak_date
        
        for point in equity_curve:
            current_value = point['value']
            current_date = point['date']
            
            # 更新峰值
            if current_value > peak_value:
                peak_value = current_value
                peak_date = current_date
            
            # 计算当前回撤
            current_drawdown = (peak_value - current_value) / peak_value
            current_drawdown_value = peak_value - current_value
            
            # 更新最大回撤
            if current_drawdown > max_drawdown:
                max_drawdown = current_drawdown
                max_drawdown_value = current_drawdown_value
                drawdown_start = peak_date
                drawdown_end = current_date
        
        return max_drawdown_value, max_drawdown, drawdown_start, drawdown_end
    
    def calculate_volatility(self, returns: np.ndarray) -> float:
        """
        计算波动率
        
        年化波动率 = 日波动率 × √252
        
        Args:
            returns: 日收益率数组
            
        Returns:
            年化波动率
        """
        if len(returns) < 2:
            return 0.0
        
        # 计算日波动率（标准差）
        daily_volatility = np.std(returns, ddof=1)
        
        # 年化波动率
        annual_volatility = daily_volatility * np.sqrt(252)
        
        return annual_volatility
    
    def calculate_annual_return(self, total_return: float, days: int) -> float:
        """
        计算年化收益率
        
        年化收益率 = (1 + 总收益率)^(252/交易天数) - 1
        
        Args:
            total_return: 总收益率
            days: 交易天数
            
        Returns:
            年化收益率
        """
        if days <= 0:
            return 0.0
        
        annual_return = (1 + total_return) ** (252 / days) - 1
        return annual_return
    
    def calculate_calmar_ratio(self, annual_return: float, max_drawdown: float) -> float:
        """
        计算卡玛比率
        
        卡玛比率 = 年化收益率 / 最大回撤百分比
        
        Args:
            annual_return: 年化收益率
            max_drawdown: 最大回撤百分比（小数形式）
            
        Returns:
            卡玛比率，如果最大回撤为0则返回0
        """
        if max_drawdown == 0:
            return 0.0
        
        return annual_return / max_drawdown
    
    def calculate_all_metrics(self, trades: List[Dict], equity_curve: List[Dict], total_days: int) -> Dict:
        """
        计算所有指标
        
        Args:
            trades: 交易列表
            equity_curve: 权益曲线
            total_days: 总交易天数
            
        Returns:
            包含所有指标的字典
        """
        # 基础交易统计
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t.get('return', 0) > 0)
        losing_trades = sum(1 for t in trades if t.get('return', 0) < 0)
        
        # 计算胜率
        win_rate = self.calculate_win_rate(trades)
        
        # 计算盈亏比
        profit_loss_ratio = self.calculate_profit_loss_ratio(trades)
        
        # 计算平均收益率
        average_return = self.calculate_average_return(trades)
        
        # 计算总收益率
        total_return = sum(t.get('return', 0) for t in trades)
        
        # 计算年化收益率
        annual_return = self.calculate_annual_return(total_return, total_days)
        
        # 计算最大回撤
        max_drawdown_value, max_drawdown, _, _ = self.calculate_max_drawdown(equity_curve)
        
        # 从权益曲线计算收益率序列（用于夏普比率和波动率）
        if len(equity_curve) >= 2:
            values = [point['value'] for point in equity_curve]
            returns = np.array([(values[i] - values[i-1]) / values[i-1] for i in range(1, len(values))])
        else:
            returns = np.array([])
        
        # 计算夏普比率
        sharpe_ratio = self.calculate_sharpe_ratio(returns, self.risk_free_rate)
        
        # 计算波动率
        volatility = self.calculate_volatility(returns)
        
        # 计算卡玛比率
        calmar_ratio = self.calculate_calmar_ratio(annual_return, max_drawdown)
        
        # 计算盈利因子
        total_profit = sum(t.get('profit', 0) for t in trades if t.get('profit', 0) > 0)
        total_loss = abs(sum(t.get('profit', 0) for t in trades if t.get('profit', 0) < 0))
        profit_factor = total_profit / total_loss if total_loss > 0 else total_profit
        
        return {
            'total_trades': total_trades,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'profit_loss_ratio': profit_loss_ratio,
            'average_return': average_return,
            'total_return': total_return,
            'annual_return': annual_return,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'max_drawdown_value': max_drawdown_value,
            'volatility': volatility,
            'calmar_ratio': calmar_ratio,
            'profit_factor': profit_factor
        }
