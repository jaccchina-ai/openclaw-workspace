"""
Enhanced Risk Control Module

风险控制增强模块，提供完善的个股止损、组合风险敞口控制和最大回撤保护。

功能:
1. 个股止损逻辑（固定比例、移动止损、时间止损、波动率止损）
2. 组合风险敞口控制（总仓位、个股仓位、行业集中度、VaR）
3. 最大回撤保护（跟踪历史最高值、计算回撤、触发保护）
4. 风险限制验证和风险报告生成

Author: T01 System
Date: 2026-03-28
"""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from copy import deepcopy


@dataclass
class Position:
    """
    持仓数据结构
    
    Attributes:
        stock_code: 股票代码
        stock_name: 股票名称
        entry_price: 入场价格
        current_price: 当前价格
        quantity: 持仓数量
        entry_date: 入场日期
        sector: 所属行业
        highest_price: 历史最高价（用于移动止损）
        atr: 平均真实波幅（用于波动率止损）
    """
    stock_code: str
    stock_name: str = ""
    entry_price: float = 0.0
    current_price: float = 0.0
    quantity: int = 0
    entry_date: Optional[datetime] = None
    sector: str = ""
    highest_price: Optional[float] = None
    atr: Optional[float] = None
    
    def get_current_value(self) -> float:
        """获取当前持仓市值"""
        return self.current_price * self.quantity
    
    def get_cost_value(self) -> float:
        """获取持仓成本"""
        return self.entry_price * self.quantity
    
    def get_pnl_pct(self) -> float:
        """获取盈亏比例"""
        if self.entry_price <= 0:
            return 0.0
        return (self.current_price - self.entry_price) / self.entry_price
    
    def get_pnl_amount(self) -> float:
        """获取盈亏金额"""
        return (self.current_price - self.entry_price) * self.quantity
    
    def get_holding_days(self, current_date: Optional[datetime] = None) -> int:
        """获取持仓天数"""
        if self.entry_date is None:
            return 0
        if current_date is None:
            current_date = datetime.now()
        return (current_date - self.entry_date).days
    
    def update_highest_price(self, price: float) -> None:
        """更新历史最高价"""
        if self.highest_price is None or price > self.highest_price:
            self.highest_price = price
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.entry_date:
            data['entry_date'] = self.entry_date.isoformat()
        return data


@dataclass
class RiskMetrics:
    """
    风险指标数据结构
    
    Attributes:
        total_exposure: 总敞口比例
        max_position_pct: 最大个股仓位
        max_sector_pct: 最大行业仓位
        var_95: 95%置信度VaR
        concentration_risk: 集中度风险评分
        sector_concentration: 行业集中度
        timestamp: 计算时间戳
    """
    total_exposure: float = 0.0
    max_position_pct: float = 0.0
    max_sector_pct: float = 0.0
    var_95: float = 0.0
    concentration_risk: float = 0.0
    sector_concentration: float = 0.0
    timestamp: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        data = asdict(self)
        if self.timestamp:
            data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class StopLossSignal:
    """
    止损信号数据结构
    
    Attributes:
        triggered: 是否触发止损
        stock_code: 股票代码
        stop_type: 止损类型（fixed/trailing/time/volatility）
        current_pnl_pct: 当前盈亏比例
        threshold_pct: 触发阈值
        recommendation: 建议操作（sell/hold/reduce）
        reason: 触发原因描述
    """
    triggered: bool = False
    stock_code: str = ""
    stop_type: str = ""
    current_pnl_pct: float = 0.0
    threshold_pct: float = 0.0
    recommendation: str = "hold"
    reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class DrawdownSignal:
    """
    回撤信号数据结构
    
    Attributes:
        triggered: 是否触发回撤保护
        current_drawdown: 当前回撤比例
        max_drawdown_limit: 最大回撤限制
        peak_value: 历史最高净值
        current_value: 当前净值
        action: 建议操作（reduce/clear/pause）
        severity: 严重程度（low/medium/high/critical）
    """
    triggered: bool = False
    current_drawdown: float = 0.0
    max_drawdown_limit: float = -0.10
    peak_value: float = 0.0
    current_value: float = 0.0
    action: str = "hold"
    severity: str = "low"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class RiskWarning:
    """
    风险警告数据结构
    
    Attributes:
        level: 警告级别（info/warning/critical）
        type: 警告类型
        message: 警告信息
        metric_name: 指标名称
        current_value: 当前值
        threshold: 阈值
    """
    level: str = "info"
    type: str = ""
    message: str = ""
    metric_name: str = ""
    current_value: float = 0.0
    threshold: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)


@dataclass
class RiskReport:
    """
    风险报告数据结构
    
    Attributes:
        timestamp: 报告生成时间
        portfolio_value: 组合净值
        peak_value: 历史最高净值
        current_drawdown: 当前回撤
        risk_metrics: 风险指标
        stop_loss_signals: 止损信号列表
        warnings: 风险警告列表
        summary: 报告摘要
    """
    timestamp: datetime = field(default_factory=datetime.now)
    portfolio_value: float = 0.0
    peak_value: float = 0.0
    current_drawdown: float = 0.0
    risk_metrics: RiskMetrics = field(default_factory=RiskMetrics)
    stop_loss_signals: List[StopLossSignal] = field(default_factory=list)
    warnings: List[RiskWarning] = field(default_factory=list)
    summary: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'portfolio_value': self.portfolio_value,
            'peak_value': self.peak_value,
            'current_drawdown': self.current_drawdown,
            'risk_metrics': self.risk_metrics.to_dict(),
            'stop_loss_signals': [s.to_dict() for s in self.stop_loss_signals],
            'warnings': [w.to_dict() for w in self.warnings],
            'summary': self.summary
        }


class EnhancedRiskControl:
    """
    增强风险控制类
    
    提供完善的个股止损、组合风险敞口控制和最大回撤保护。
    
    Attributes:
        config: 风控配置参数
        _peak_value: 历史最高净值
        _value_history: 净值历史记录
    
    配置参数:
        - stop_loss_pct: 固定止损比例（默认-0.07）
        - trailing_stop_pct: 移动止损比例（默认-0.05）
        - max_drawdown_pct: 最大回撤限制（默认-0.10）
        - max_position_pct: 单股最大仓位（默认0.20）
        - max_sector_pct: 单行业最大仓位（默认0.30）
        - max_total_exposure: 总仓位限制（默认0.80）
        - time_stop_days: 时间止损天数（默认20）
        - atr_multiplier: ATR倍数（默认2.0）
    """
    
    DEFAULT_CONFIG = {
        'stop_loss_pct': -0.07,
        'trailing_stop_pct': -0.05,
        'max_drawdown_pct': -0.10,
        'max_position_pct': 0.20,
        'max_sector_pct': 0.30,
        'max_total_exposure': 0.80,
        'time_stop_days': 20,
        'atr_multiplier': 2.0,
        'var_confidence': 0.95,
        'enable_fixed_stop': True,
        'enable_trailing_stop': True,
        'enable_time_stop': True,
        'enable_volatility_stop': True,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化风险控制模块
        
        Args:
            config: 风控配置字典，None则使用默认配置
        """
        self.config = deepcopy(self.DEFAULT_CONFIG)
        if config:
            self.config.update(config)
        
        self._peak_value: float = 0.0
        self._value_history: List[Tuple[datetime, float]] = []
        self._last_check_time: Optional[datetime] = None
    
    def check_stop_loss(
        self, 
        position: Position, 
        current_price: float,
        current_date: Optional[datetime] = None
    ) -> StopLossSignal:
        """
        检查个股止损
        
        支持四种止损类型:
        1. 固定比例止损
        2. 移动止损（跟踪最高价）
        3. 时间止损
        4. 波动率止损（ATR倍数）
        
        Args:
            position: 持仓数据
            current_price: 当前价格
            current_date: 当前日期，None则使用系统时间
        
        Returns:
            StopLossSignal: 止损信号
        """
        if current_date is None:
            current_date = datetime.now()
        
        # 更新持仓价格和历史最高价
        position.current_price = current_price
        position.update_highest_price(current_price)
        
        pnl_pct = position.get_pnl_pct()
        
        # 1. 检查固定比例止损
        if self.config['enable_fixed_stop']:
            if pnl_pct <= self.config['stop_loss_pct']:
                return StopLossSignal(
                    triggered=True,
                    stock_code=position.stock_code,
                    stop_type="fixed",
                    current_pnl_pct=pnl_pct,
                    threshold_pct=self.config['stop_loss_pct'],
                    recommendation="sell",
                    reason=f"Fixed stop loss triggered: {pnl_pct:.2%} <= {self.config['stop_loss_pct']:.2%}"
                )
        
        # 2. 检查移动止损
        if self.config['enable_trailing_stop'] and position.highest_price:
            if position.highest_price > position.entry_price:
                trailing_threshold = position.highest_price * (1 + self.config['trailing_stop_pct'])
                if current_price <= trailing_threshold:
                    return StopLossSignal(
                        triggered=True,
                        stock_code=position.stock_code,
                        stop_type="trailing",
                        current_pnl_pct=pnl_pct,
                        threshold_pct=self.config['trailing_stop_pct'],
                        recommendation="sell",
                        reason=f"Trailing stop triggered: price {current_price:.2f} <= threshold {trailing_threshold:.2f}"
                    )
        
        # 3. 检查时间止损
        if self.config['enable_time_stop']:
            holding_days = position.get_holding_days(current_date)
            if holding_days >= self.config['time_stop_days'] and pnl_pct < 0:
                return StopLossSignal(
                    triggered=True,
                    stock_code=position.stock_code,
                    stop_type="time",
                    current_pnl_pct=pnl_pct,
                    threshold_pct=float(self.config['time_stop_days']),
                    recommendation="sell",
                    reason=f"Time stop triggered: held for {holding_days} days with loss {pnl_pct:.2%}"
                )
        
        # 4. 检查波动率止损
        if self.config['enable_volatility_stop'] and position.atr and position.atr > 0:
            stop_price = position.entry_price - self.config['atr_multiplier'] * position.atr
            if current_price <= stop_price:
                return StopLossSignal(
                    triggered=True,
                    stock_code=position.stock_code,
                    stop_type="volatility",
                    current_pnl_pct=pnl_pct,
                    threshold_pct=-self.config['atr_multiplier'] * position.atr / position.entry_price,
                    recommendation="sell",
                    reason=f"Volatility stop triggered: price {current_price:.2f} <= stop {stop_price:.2f} (ATR={position.atr:.2f})"
                )
        
        # 未触发止损
        return StopLossSignal(
            triggered=False,
            stock_code=position.stock_code,
            stop_type="none",
            current_pnl_pct=pnl_pct,
            recommendation="hold",
            reason="No stop loss condition met"
        )
    
    def calculate_position_risk(
        self, 
        positions: List[Position],
        total_capital: float
    ) -> RiskMetrics:
        """
        计算组合风险敞口
        
        计算以下指标:
        1. 总敞口比例
        2. 最大个股仓位
        3. 最大行业仓位
        4. 风险价值(VaR)
        5. 集中度风险
        
        Args:
            positions: 持仓列表
            total_capital: 总资金
        
        Returns:
            RiskMetrics: 风险指标
        """
        if not positions or total_capital <= 0:
            return RiskMetrics(timestamp=datetime.now())
        
        # 计算总市值
        total_value = sum(p.get_current_value() for p in positions)
        
        # 1. 总敞口
        total_exposure = total_value / total_capital
        
        # 2. 个股仓位
        position_pcts = {}
        for p in positions:
            position_pcts[p.stock_code] = p.get_current_value() / total_capital
        max_position_pct = max(position_pcts.values()) if position_pcts else 0.0
        
        # 3. 行业仓位
        sector_values: Dict[str, float] = {}
        for p in positions:
            sector = p.sector or "Unknown"
            sector_values[sector] = sector_values.get(sector, 0.0) + p.get_current_value()
        
        sector_pcts = {s: v / total_capital for s, v in sector_values.items()}
        max_sector_pct = max(sector_pcts.values()) if sector_pcts else 0.0
        
        # 计算行业集中度（赫芬达尔指数）
        sector_concentration = sum(pct ** 2 for pct in sector_pcts.values())
        
        # 4. 计算VaR (简化版 - 使用历史模拟法)
        var_95 = self._calculate_var(positions, total_capital)
        
        # 5. 集中度风险评分
        concentration_risk = self._calculate_concentration_risk(
            max_position_pct, max_sector_pct, sector_concentration
        )
        
        return RiskMetrics(
            total_exposure=total_exposure,
            max_position_pct=max_position_pct,
            max_sector_pct=max_sector_pct,
            var_95=var_95,
            concentration_risk=concentration_risk,
            sector_concentration=sector_concentration,
            timestamp=datetime.now()
        )
    
    def _calculate_var(self, positions: List[Position], total_capital: float) -> float:
        """
        计算风险价值(VaR)
        
        使用简化方法计算95%置信度的VaR。
        实际应用中可以使用历史模拟法或参数法。
        
        Args:
            positions: 持仓列表
            total_capital: 总资金
        
        Returns:
            float: VaR值（负数表示损失）
        """
        if not positions or total_capital <= 0:
            return 0.0
        
        # 简化计算：基于持仓波动性的估计
        # 实际应用中应该使用历史收益率数据
        total_value = sum(p.get_current_value() for p in positions)
        
        # 假设日波动率约为2%，95%置信度对应约1.645倍标准差
        daily_volatility = 0.02
        z_score = 1.645  # 95%置信度
        
        var_pct = -z_score * daily_volatility
        var_amount = total_value * var_pct / total_capital
        
        return var_amount
    
    def _calculate_concentration_risk(
        self, 
        max_position_pct: float, 
        max_sector_pct: float,
        sector_concentration: float
    ) -> float:
        """
        计算集中度风险评分
        
        评分范围0-100，分数越高风险越大。
        
        Args:
            max_position_pct: 最大个股仓位
            max_sector_pct: 最大行业仓位
            sector_concentration: 行业集中度
        
        Returns:
            float: 集中度风险评分
        """
        # 个股集中度权重40%
        position_risk = min(max_position_pct / self.config['max_position_pct'], 1.0) * 40
        
        # 行业集中度权重40%
        sector_risk = min(max_sector_pct / self.config['max_sector_pct'], 1.0) * 40
        
        # 赫芬达尔指数权重20%
        hhi_risk = min(sector_concentration / 0.25, 1.0) * 20  # 0.25是4等分的HHI
        
        return position_risk + sector_risk + hhi_risk
    
    def check_drawdown(self, portfolio_value: float) -> DrawdownSignal:
        """
        检查回撤
        
        跟踪历史最高净值，计算当前回撤，判断是否触发回撤保护。
        
        Args:
            portfolio_value: 当前组合净值
        
        Returns:
            DrawdownSignal: 回撤信号
        """
        current_time = datetime.now()
        
        # 更新历史最高值
        if portfolio_value > self._peak_value:
            self._peak_value = portfolio_value
        
        # 记录净值历史
        self._value_history.append((current_time, portfolio_value))
        
        # 计算当前回撤
        if self._peak_value <= 0:
            current_drawdown = 0.0
        else:
            current_drawdown = (portfolio_value - self._peak_value) / self._peak_value
        
        # 判断严重程度
        max_dd = abs(self.config['max_drawdown_pct'])
        current_dd = abs(current_drawdown)
        
        if current_dd >= max_dd:
            severity = "critical"
            action = "clear"
            triggered = True
        elif current_dd >= max_dd * 0.8:
            severity = "high"
            action = "reduce"
            triggered = True
        elif current_dd >= max_dd * 0.5:
            severity = "medium"
            action = "reduce"
            triggered = False
        else:
            severity = "low"
            action = "hold"
            triggered = False
        
        self._last_check_time = current_time
        
        return DrawdownSignal(
            triggered=triggered,
            current_drawdown=current_drawdown,
            max_drawdown_limit=self.config['max_drawdown_pct'],
            peak_value=self._peak_value,
            current_value=portfolio_value,
            action=action,
            severity=severity
        )
    
    def validate_risk_limits(self, risk_metrics: RiskMetrics) -> List[RiskWarning]:
        """
        验证风险限制
        
        检查是否超过风险阈值，返回风险警告列表。
        
        Args:
            risk_metrics: 风险指标
        
        Returns:
            List[RiskWarning]: 风险警告列表
        """
        warnings: List[RiskWarning] = []
        
        # 检查总敞口
        if risk_metrics.total_exposure > self.config['max_total_exposure']:
            warnings.append(RiskWarning(
                level="critical" if risk_metrics.total_exposure > 0.95 else "warning",
                type="total_exposure",
                message=f"Total exposure {risk_metrics.total_exposure:.1%} exceeds limit {self.config['max_total_exposure']:.1%}",
                metric_name="total_exposure",
                current_value=risk_metrics.total_exposure,
                threshold=self.config['max_total_exposure']
            ))
        
        # 检查个股仓位
        if risk_metrics.max_position_pct > self.config['max_position_pct']:
            warnings.append(RiskWarning(
                level="warning",
                type="position_concentration",
                message=f"Max position {risk_metrics.max_position_pct:.1%} exceeds limit {self.config['max_position_pct']:.1%}",
                metric_name="max_position_pct",
                current_value=risk_metrics.max_position_pct,
                threshold=self.config['max_position_pct']
            ))
        
        # 检查行业仓位
        if risk_metrics.max_sector_pct > self.config['max_sector_pct']:
            warnings.append(RiskWarning(
                level="warning",
                type="sector_concentration",
                message=f"Max sector {risk_metrics.max_sector_pct:.1%} exceeds limit {self.config['max_sector_pct']:.1%}",
                metric_name="max_sector_pct",
                current_value=risk_metrics.max_sector_pct,
                threshold=self.config['max_sector_pct']
            ))
        
        # 检查集中度风险
        if risk_metrics.concentration_risk > 70:
            warnings.append(RiskWarning(
                level="critical",
                type="concentration_risk",
                message=f"Concentration risk score {risk_metrics.concentration_risk:.1f} is critically high",
                metric_name="concentration_risk",
                current_value=risk_metrics.concentration_risk,
                threshold=70.0
            ))
        elif risk_metrics.concentration_risk > 50:
            warnings.append(RiskWarning(
                level="warning",
                type="concentration_risk",
                message=f"Concentration risk score {risk_metrics.concentration_risk:.1f} is elevated",
                metric_name="concentration_risk",
                current_value=risk_metrics.concentration_risk,
                threshold=50.0
            ))
        
        return warnings
    
    def get_risk_report(
        self,
        positions: List[Position],
        portfolio_value: float,
        total_capital: float
    ) -> RiskReport:
        """
        获取风险报告
        
        汇总所有风险指标，返回完整风险报告。
        
        Args:
            positions: 持仓列表
            portfolio_value: 当前组合净值
            total_capital: 总资金
        
        Returns:
            RiskReport: 完整风险报告
        """
        # 计算风险指标
        risk_metrics = self.calculate_position_risk(positions, total_capital)
        
        # 检查回撤
        drawdown_signal = self.check_drawdown(portfolio_value)
        
        # 检查个股止损
        stop_loss_signals = []
        for position in positions:
            signal = self.check_stop_loss(position, position.current_price)
            if signal.triggered:
                stop_loss_signals.append(signal)
        
        # 验证风险限制
        warnings = self.validate_risk_limits(risk_metrics)
        
        # 添加回撤警告
        if drawdown_signal.triggered:
            warnings.append(RiskWarning(
                level="critical" if drawdown_signal.severity == "critical" else "warning",
                type="drawdown",
                message=f"Drawdown protection triggered: {drawdown_signal.current_drawdown:.2%}",
                metric_name="current_drawdown",
                current_value=drawdown_signal.current_drawdown,
                threshold=self.config['max_drawdown_pct']
            ))
        
        # 生成摘要
        summary = self._generate_summary(
            risk_metrics, drawdown_signal, stop_loss_signals, warnings
        )
        
        return RiskReport(
            timestamp=datetime.now(),
            portfolio_value=portfolio_value,
            peak_value=self._peak_value,
            current_drawdown=drawdown_signal.current_drawdown,
            risk_metrics=risk_metrics,
            stop_loss_signals=stop_loss_signals,
            warnings=warnings,
            summary=summary
        )
    
    def _generate_summary(
        self,
        risk_metrics: RiskMetrics,
        drawdown_signal: DrawdownSignal,
        stop_loss_signals: List[StopLossSignal],
        warnings: List[RiskWarning]
    ) -> str:
        """生成报告摘要"""
        parts = []
        
        # 整体风险状态
        critical_count = sum(1 for w in warnings if w.level == "critical")
        warning_count = sum(1 for w in warnings if w.level == "warning")
        
        if critical_count > 0:
            parts.append(f"CRITICAL: {critical_count} critical risk(s) detected")
        elif warning_count > 0:
            parts.append(f"WARNING: {warning_count} warning(s) present")
        else:
            parts.append("OK: Risk levels within acceptable limits")
        
        # 回撤状态
        if drawdown_signal.triggered:
            parts.append(f"Drawdown: {drawdown_signal.current_drawdown:.2%} (Action: {drawdown_signal.action})")
        
        # 止损信号
        if stop_loss_signals:
            parts.append(f"Stop Loss: {len(stop_loss_signals)} position(s) triggered")
        
        # 敞口摘要
        parts.append(f"Exposure: {risk_metrics.total_exposure:.1%} total, {risk_metrics.max_position_pct:.1%} max position")
        
        return " | ".join(parts)
    
    def reset_peak_value(self, value: Optional[float] = None) -> None:
        """
        重置历史最高值
        
        Args:
            value: 新的最高值，None则使用当前值
        """
        if value is not None:
            self._peak_value = value
        else:
            self._peak_value = 0.0
            self._value_history.clear()
    
    def get_peak_value(self) -> float:
        """获取历史最高净值"""
        return self._peak_value
    
    def get_config(self) -> Dict[str, Any]:
        """获取当前配置"""
        return deepcopy(self.config)
    
    def update_config(self, config: Dict[str, Any]) -> None:
        """
        更新配置
        
        Args:
            config: 新配置字典
        """
        self.config.update(config)


# 向后兼容的别名
RiskController = EnhancedRiskControl


if __name__ == "__main__":
    # 简单的使用示例
    print("Enhanced Risk Control Module")
    print("=" * 50)
    
    # 创建风控实例
    risk_control = EnhancedRiskControl()
    print(f"Default config: {risk_control.get_config()}")
    
    # 创建示例持仓
    position = Position(
        stock_code="000001.SZ",
        stock_name="平安银行",
        entry_price=10.0,
        current_price=9.2,
        quantity=1000,
        entry_date=datetime.now() - timedelta(days=5),
        sector="银行"
    )
    
    # 检查止损
    signal = risk_control.check_stop_loss(position, 9.2)
    print(f"\nStop loss check: {signal.to_dict()}")
    
    # 计算风险敞口
    positions = [position]
    metrics = risk_control.calculate_position_risk(positions, 100000)
    print(f"\nRisk metrics: {metrics.to_dict()}")
    
    # 检查回撤
    drawdown = risk_control.check_drawdown(95000)
    print(f"\nDrawdown check: {drawdown.to_dict()}")
    
    # 生成风险报告
    report = risk_control.get_risk_report(positions, 95000, 100000)
    print(f"\nRisk report summary: {report.summary}")
