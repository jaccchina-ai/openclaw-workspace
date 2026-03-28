"""
交易模拟模块

模拟真实交易环境，处理订单执行、滑点、手续费等
"""

from typing import Dict, Any, Optional, List
from datetime import datetime


class TradeSimulator:
    """
    交易模拟器

    模拟真实交易环境，包括：
    - 订单执行（市价单、限价单）
    - 滑点模拟
    - 手续费和印花税计算
    - 持仓管理
    - 资金账户管理

    Attributes:
        initial_capital: 初始资金
        commission_rate: 手续费率
        slippage: 滑点设置
    """

    def __init__(self, initial_capital: float = 1000000, 
                 commission_rate: float = 0.0003, 
                 slippage: float = 0.005):
        """
        初始化交易模拟器
        
        Args:
            initial_capital: 初始资金，默认1000000
            commission_rate: 手续费率，默认0.0003 (0.03%)
            slippage: 滑点比例，默认0.005 (0.5%)
        """
        self.initial_capital = initial_capital
        self.commission_rate = commission_rate
        self.slippage = slippage
        
        # 账户状态
        self._cash = initial_capital
        self._positions: Dict[str, Dict[str, Any]] = {}  # 持仓字典，key为ts_code
        self._trade_history: List[Dict[str, Any]] = []  # 交易历史
        self._equity_curve: List[Dict[str, Any]] = []  # 权益曲线

    def execute_buy(self, ts_code: str, name: str, price: float, 
                    amount: int, trade_date: str) -> Dict[str, Any]:
        """
        执行买入操作
        
        Args:
            ts_code: 股票代码 (格式: 000001.SZ)
            name: 股票名称
            price: 目标买入价格
            amount: 买入数量
            trade_date: 交易日期 (格式: YYYYMMDD)
            
        Returns:
            交易记录字典
        """
        # 计算实际成交价格（含滑点）
        # 买入时滑点使价格上升
        actual_price = price * (1 + self.slippage)
        
        # 计算成交金额
        trade_amount = actual_price * amount
        
        # 计算手续费
        commission = trade_amount * self.commission_rate
        
        # 计算总成本
        total_cost = trade_amount + commission
        
        # 检查资金是否足够
        if total_cost > self._cash:
            raise ValueError(f"资金不足: 需要 {total_cost:.2f}, 可用 {self._cash:.2f}")
        
        # 更新现金
        self._cash -= total_cost
        
        # 更新持仓
        if ts_code in self._positions:
            # 已有持仓，更新成本价
            position = self._positions[ts_code]
            old_amount = position['amount']
            old_cost = position['cost_price'] * old_amount
            new_cost = actual_price * amount + commission
            total_amount = old_amount + amount
            
            position['amount'] = total_amount
            position['cost_price'] = (old_cost + new_cost) / total_amount
            position['current_price'] = actual_price
            position['market_value'] = actual_price * total_amount
        else:
            # 新建持仓
            cost_price = (trade_amount + commission) / amount
            self._positions[ts_code] = {
                'ts_code': ts_code,
                'name': name,
                'cost_price': cost_price,
                'current_price': actual_price,
                'amount': amount,
                'market_value': actual_price * amount,
                'profit': 0.0,
                'profit_pct': 0.0
            }
        
        # 创建交易记录
        trade_record = {
            'ts_code': ts_code,
            'name': name,
            'action': 'buy',
            'price': price,
            'actual_price': actual_price,
            'amount': amount,
            'commission': commission,
            'trade_date': trade_date,
            'profit': 0.0,
            'profit_pct': 0.0
        }
        
        # 添加到交易历史
        self._trade_history.append(trade_record)
        
        return trade_record

    def execute_sell(self, ts_code: str, price: float, 
                     trade_date: str) -> Optional[Dict[str, Any]]:
        """
        执行卖出操作
        
        Args:
            ts_code: 股票代码 (格式: 000001.SZ)
            price: 目标卖出价格
            trade_date: 交易日期 (格式: YYYYMMDD)
            
        Returns:
            交易记录字典，如果没有持仓则返回None
        """
        # 检查是否有持仓
        if ts_code not in self._positions:
            return None
        
        position = self._positions[ts_code]
        amount = position['amount']
        name = position['name']
        cost_price = position['cost_price']
        
        # 计算实际成交价格（含滑点）
        # 卖出时滑点使价格下降
        actual_price = price * (1 - self.slippage)
        
        # 计算成交金额
        trade_amount = actual_price * amount
        
        # 计算手续费
        commission = trade_amount * self.commission_rate
        
        # 计算净收入
        net_proceeds = trade_amount - commission
        
        # 计算盈亏
        # 买入总成本 = 成本价 * 数量
        buy_cost = cost_price * amount
        profit = net_proceeds - buy_cost
        profit_pct = profit / buy_cost if buy_cost > 0 else 0
        
        # 更新现金
        self._cash += net_proceeds
        
        # 移除持仓
        del self._positions[ts_code]
        
        # 创建交易记录
        trade_record = {
            'ts_code': ts_code,
            'name': name,
            'action': 'sell',
            'price': price,
            'actual_price': actual_price,
            'amount': amount,
            'commission': commission,
            'trade_date': trade_date,
            'profit': profit,
            'profit_pct': profit_pct
        }
        
        # 添加到交易历史
        self._trade_history.append(trade_record)
        
        return trade_record

    def get_position(self, ts_code: str) -> Optional[Dict[str, Any]]:
        """
        获取指定股票的持仓信息
        
        Args:
            ts_code: 股票代码
            
        Returns:
            持仓记录字典，如果没有持仓则返回None
        """
        return self._positions.get(ts_code)

    def get_all_positions(self) -> List[Dict[str, Any]]:
        """
        获取所有持仓
        
        Returns:
            持仓记录列表
        """
        return list(self._positions.values())

    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """
        获取投资组合总价值
        
        Args:
            current_prices: 当前价格字典，key为ts_code，value为价格
            
        Returns:
            投资组合总价值（现金 + 持仓市值）
        """
        position_value = 0.0
        
        for ts_code, position in self._positions.items():
            if ts_code in current_prices:
                position_value += current_prices[ts_code] * position['amount']
            else:
                # 如果没有提供当前价格，使用持仓中的当前价格
                position_value += position['market_value']
        
        return self._cash + position_value

    def get_cash(self) -> float:
        """
        获取当前现金余额
        
        Returns:
            现金余额
        """
        return self._cash

    def get_equity_curve(self) -> List[Dict[str, Any]]:
        """
        获取权益曲线
        
        Returns:
            权益曲线列表，每个元素包含date和equity
        """
        return self._equity_curve.copy()

    def record_equity(self, date: str, equity: Optional[float] = None):
        """
        记录权益
        
        Args:
            date: 日期 (格式: YYYYMMDD)
            equity: 权益值，如果为None则使用当前现金
        """
        if equity is None:
            equity = self._cash
        
        self._equity_curve.append({
            'date': date,
            'equity': equity
        })

    def reset(self):
        """
        重置模拟器状态
        
        清空所有持仓、交易历史和权益曲线，恢复初始资金
        """
        self._cash = self.initial_capital
        self._positions.clear()
        self._trade_history.clear()
        self._equity_curve.clear()

    def _update_position_value(self, ts_code: str, current_price: float):
        """
        更新持仓市值和盈亏
        
        Args:
            ts_code: 股票代码
            current_price: 当前价格
        """
        if ts_code not in self._positions:
            return
        
        position = self._positions[ts_code]
        position['current_price'] = current_price
        position['market_value'] = current_price * position['amount']
        
        # 计算未实现盈亏
        cost_value = position['cost_price'] * position['amount']
        position['profit'] = position['market_value'] - cost_value
        position['profit_pct'] = position['profit'] / cost_value if cost_value > 0 else 0

    def get_trade_history(self) -> List[Dict[str, Any]]:
        """
        获取交易历史
        
        Returns:
            交易记录列表
        """
        return self._trade_history.copy()

    def get_statistics(self) -> Dict[str, Any]:
        """
        获取交易统计信息
        
        Returns:
            统计信息字典
        """
        if not self._trade_history:
            return {
                'total_trades': 0,
                'win_trades': 0,
                'loss_trades': 0,
                'win_rate': 0.0,
                'total_profit': 0.0,
                'avg_profit_per_trade': 0.0
            }
        
        sell_trades = [t for t in self._trade_history if t['action'] == 'sell']
        
        if not sell_trades:
            return {
                'total_trades': len(self._trade_history),
                'sell_trades': 0,
                'win_trades': 0,
                'loss_trades': 0,
                'win_rate': 0.0,
                'total_profit': 0.0,
                'avg_profit_per_trade': 0.0
            }
        
        win_trades = [t for t in sell_trades if t['profit'] > 0]
        loss_trades = [t for t in sell_trades if t['profit'] <= 0]
        
        total_profit = sum(t['profit'] for t in sell_trades)
        
        return {
            'total_trades': len(self._trade_history),
            'sell_trades': len(sell_trades),
            'win_trades': len(win_trades),
            'loss_trades': len(loss_trades),
            'win_rate': len(win_trades) / len(sell_trades) if sell_trades else 0.0,
            'total_profit': total_profit,
            'avg_profit_per_trade': total_profit / len(sell_trades) if sell_trades else 0.0
        }
