"""
策略选择器模块

提供根据市场环境或配置自动选择策略的功能。
支持配置驱动和动态选择两种模式，支持默认策略回退。
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Callable
from copy import deepcopy

from strategy_base import Strategy
from strategy_context import StrategyContext, StrategyError


# 配置日志
logger = logging.getLogger(__name__)


class NoMatchingStrategyError(StrategyError):
    """没有匹配的策略错误"""


class NoDefaultStrategyError(StrategyError):
    """没有默认策略错误"""


@dataclass
class SelectionCriteria:
    """
    选择标准类
    
    用于定义策略选择的标准条件。
    
    Attributes:
        market_trend: 市场趋势（bull/bear/sideways）
        min_volume: 最小成交量
        max_volatility: 最大波动率
        custom_criteria: 自定义标准字典
    """
    market_trend: Optional[str] = None
    min_volume: Optional[float] = None
    max_volatility: Optional[float] = None
    custom_criteria: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """将选择标准转换为字典"""
        return {
            "market_trend": self.market_trend,
            "min_volume": self.min_volume,
            "max_volatility": self.max_volatility,
            "custom_criteria": self.custom_criteria
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SelectionCriteria':
        """从字典创建选择标准"""
        return cls(
            market_trend=data.get("market_trend"),
            min_volume=data.get("min_volume"),
            max_volatility=data.get("max_volatility"),
            custom_criteria=data.get("custom_criteria", {})
        )


@dataclass
class SelectionRule:
    """
    选择规则类
    
    定义策略选择的条件和目标策略。
    
    Attributes:
        name: 规则名称
        condition: 条件函数，接收市场数据返回布尔值
        target_strategy: 匹配时选择的策略名称
        priority: 规则优先级（数值越高越优先）
        description: 规则描述
    """
    name: str
    condition: Callable[[Dict[str, Any]], bool]
    target_strategy: str
    priority: int = 0
    description: str = ""
    
    def matches(self, market_data: Dict[str, Any]) -> bool:
        """
        检查规则是否匹配市场数据
        
        Args:
            market_data: 市场数据字典
            
        Returns:
            bool: 是否匹配
        """
        try:
            return self.condition(market_data)
        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.warning("Rule '%s' condition raised exception: %s", self.name, e)
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """将规则转换为字典（不包含条件函数）"""
        return {
            "name": self.name,
            "target_strategy": self.target_strategy,
            "priority": self.priority,
            "description": self.description
        }
    
    # ==================== 内置规则工厂方法 ====================
    
    @classmethod
    def create_market_trend_rule(
        cls,
        trend: str,
        target_strategy: str,
        priority: int = 10,
        description: str = ""
    ) -> 'SelectionRule':
        """
        创建市场趋势规则
        
        Args:
            trend: 市场趋势（bull/bear/sideways）
            target_strategy: 目标策略名称
            priority: 优先级
            description: 描述
            
        Returns:
            SelectionRule: 市场趋势选择规则
        """
        def condition(market_data: Dict[str, Any]) -> bool:
            market_trend = market_data.get("market_trend")
            if market_trend == trend:
                return True
            
            # 根据指数涨跌幅推断趋势
            index_data = market_data.get("index", {})
            change_pct = index_data.get("change_pct", 0)
            
            if trend == "bull" and change_pct > 1.5:
                return True
            elif trend == "bear" and change_pct < -1.5:
                return True
            elif trend == "sideways" and -1.5 <= change_pct <= 1.5:
                return True
            
            return False
        
        desc = description or f"Select {target_strategy} when market trend is {trend}"
        
        return cls(
            name=f"market_trend_{trend}",
            condition=condition,
            target_strategy=target_strategy,
            priority=priority,
            description=desc
        )
    
    @classmethod
    def create_volume_rule(
        cls,
        min_volume: float,
        target_strategy: str,
        priority: int = 5,
        description: str = ""
    ) -> 'SelectionRule':
        """
        创建成交量规则
        
        Args:
            min_volume: 最小成交量阈值
            target_strategy: 目标策略名称
            priority: 优先级
            description: 描述
            
        Returns:
            SelectionRule: 成交量选择规则
        """
        def condition(market_data: Dict[str, Any]) -> bool:
            # 检查直接提供的volume
            volume = market_data.get("volume", 0)
            if volume >= min_volume:
                return True
            
            # 检查index中的volume
            index_data = market_data.get("index", {})
            index_volume = index_data.get("volume", 0)
            if index_volume >= min_volume:
                return True
            
            return False
        
        desc = description or f"Select {target_strategy} when volume >= {min_volume}"
        
        return cls(
            name=f"volume_above_{min_volume}",
            condition=condition,
            target_strategy=target_strategy,
            priority=priority,
            description=desc
        )
    
    @classmethod
    def create_volatility_rule(
        cls,
        max_volatility: float,
        target_strategy: str,
        priority: int = 5,
        description: str = ""
    ) -> 'SelectionRule':
        """
        创建波动率规则
        
        Args:
            max_volatility: 最大波动率阈值
            target_strategy: 目标策略名称
            priority: 优先级
            description: 描述
            
        Returns:
            SelectionRule: 波动率选择规则
        """
        def condition(market_data: Dict[str, Any]) -> bool:
            volatility = market_data.get("volatility", float('inf'))
            return volatility <= max_volatility
        
        desc = description or f"Select {target_strategy} when volatility <= {max_volatility}"
        
        return cls(
            name=f"volatility_below_{max_volatility}",
            condition=condition,
            target_strategy=target_strategy,
            priority=priority,
            description=desc
        )


class StrategySelector:
    """
    策略选择器类
    
    根据市场环境或配置自动选择合适的策略。
    支持配置驱动和动态选择两种模式，支持默认策略回退。
    
    Attributes:
        context: 策略上下文
        config: 选择器配置
        _selection_rules: 选择规则列表
        _default_strategy: 默认策略名称
        _criteria: 选择标准
    
    使用示例:
        # 创建选择器
        selector = StrategySelector(context)
        
        # 设置默认策略
        selector.set_default_strategy("DefaultStrategy")
        
        # 添加选择规则
        selector.add_selection_rule(
            SelectionRule.create_market_trend_rule("bull", "BullStrategy")
        )
        
        # 根据市场数据选择策略
        market_data = {"market_trend": "bull", "index": {"change_pct": 2.0}}
        strategy = selector.select(market_data)
        
        # 执行策略
        result = strategy.execute(stock_data, market_data)
    """
    
    def __init__(
        self,
        context: Optional[StrategyContext] = None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        初始化策略选择器
        
        Args:
            context: 策略上下文，如果为None则自动创建
            config: 选择器配置字典
        """
        self._context = context if context is not None else StrategyContext()
        self._config = config or {}
        self._selection_rules: List[SelectionRule] = []
        self._default_strategy: Optional[str] = None
        self._criteria = SelectionCriteria()
        self._logger = logging.getLogger(self.__class__.__name__)
        
        # 从配置中加载设置
        self._load_from_config()
    
    def _load_from_config(self) -> None:
        """从配置加载设置"""
        if self._config:
            # 加载默认策略
            default = self._config.get("default_strategy")
            if default:
                # 验证策略存在
                if self._context.has_strategy(default):
                    self._default_strategy = default
                else:
                    self._logger.warning(
                        "Default strategy '%s' not found in context", default
                    )
            
            # 加载选择标准
            criteria_dict = self._config.get("selection_criteria")
            if criteria_dict:
                self._criteria = SelectionCriteria.from_dict(criteria_dict)
    
    @property
    def context(self) -> StrategyContext:
        """获取策略上下文"""
        return self._context
    
    def select(self, market_data: Dict[str, Any]) -> Strategy:
        """
        根据市场数据选择策略
        
        遍历所有规则，按优先级排序，执行条件函数，
        返回第一个匹配的策略。无匹配时返回默认策略。
        
        Args:
            market_data: 市场数据字典
            
        Returns:
            Strategy: 选择的策略实例
            
        Raises:
            NoDefaultStrategyError: 无匹配规则且未设置默认策略
        """
        selection_mode = self._config.get("selection_mode", "dynamic")
        
        # 配置驱动模式：返回固定策略
        if selection_mode == "config":
            fixed_strategy = self._config.get("fixed_strategy")
            if fixed_strategy:
                strategy = self._context.get_strategy(fixed_strategy)
                if strategy:
                    return strategy
                raise StrategyError(f"Fixed strategy '{fixed_strategy}' not found")
        
        # 动态模式：根据规则选择
        # 按优先级排序规则（高优先级在前）
        sorted_rules = sorted(
            self._selection_rules,
            key=lambda r: r.priority,
            reverse=True
        )
        
        # 遍历规则，返回第一个匹配的策略
        for rule in sorted_rules:
            if rule.matches(market_data):
                strategy = self._context.get_strategy(rule.target_strategy)
                if strategy:
                    self._logger.debug(
                        "Selected strategy '%s' via rule '%s'",
                        rule.target_strategy, rule.name
                    )
                    return strategy
                else:
                    self._logger.warning(
                        "Rule '%s' matched but target strategy '%s' not found",
                        rule.name, rule.target_strategy
                    )
        
        # 无匹配规则，使用默认策略
        if self._default_strategy:
            strategy = self._context.get_strategy(self._default_strategy)
            if strategy:
                self._logger.debug(
                    "Selected default strategy '%s'", self._default_strategy
                )
                return strategy
            else:
                self._logger.error(
                    "Default strategy '%s' not found", self._default_strategy
                )
                raise StrategyError(
                    f"Default strategy '{self._default_strategy}' not found"
                )
        
        # 无匹配且无默认策略
        raise NoDefaultStrategyError(
            "No matching strategy found and no default strategy set"
        )
    
    def select_by_name(self, name: str) -> Strategy:
        """
        按名称选择策略
        
        Args:
            name: 策略名称
            
        Returns:
            Strategy: 策略实例
            
        Raises:
            StrategyError: 策略不存在
        """
        strategy = self._context.get_strategy(name)
        if strategy is None:
            raise StrategyError(f"Strategy '{name}' not found")
        return strategy
    
    def select_by_type(self, strategy_type: str) -> Strategy:
        """
        按类型选择策略
        
        Args:
            strategy_type: 策略类型
            
        Returns:
            Strategy: 策略实例
            
        Raises:
            StrategyError: 该类型的策略不存在
        """
        for strategy in self._context.get_all_strategies():
            metadata = strategy.get_metadata()
            if metadata.strategy_type == strategy_type:
                return strategy
        
        raise StrategyError(f"Strategy of type '{strategy_type}' not found")
    
    def get_selection_criteria(self) -> SelectionCriteria:
        """
        获取选择标准
        
        Returns:
            SelectionCriteria: 选择标准的深拷贝
        """
        return deepcopy(self._criteria)
    
    def set_selection_criteria(self, criteria: SelectionCriteria) -> None:
        """
        设置选择标准
        
        Args:
            criteria: 选择标准
        """
        self._criteria = deepcopy(criteria)
    
    def set_default_strategy(self, name: str) -> None:
        """
        设置默认策略
        
        Args:
            name: 策略名称
            
        Raises:
            StrategyError: 策略不存在
        """
        if not self._context.has_strategy(name):
            raise StrategyError(f"Strategy '{name}' not found")
        
        self._default_strategy = name
        self._logger.debug("Set default strategy: %s", name)
    
    def get_default_strategy(self) -> Optional[str]:
        """
        获取默认策略名称
        
        Returns:
            Optional[str]: 默认策略名称，如果未设置则返回None
        """
        return self._default_strategy
    
    def add_selection_rule(self, rule: SelectionRule) -> None:
        """
        添加选择规则
        
        Args:
            rule: 选择规则
        """
        self._selection_rules.append(rule)
        self._logger.debug("Added selection rule: %s", rule.name)
    
    def remove_selection_rule(self, name: str) -> bool:
        """
        移除选择规则
        
        Args:
            name: 规则名称
            
        Returns:
            bool: 是否成功移除
        """
        for i, rule in enumerate(self._selection_rules):
            if rule.name == name:
                del self._selection_rules[i]
                self._logger.debug("Removed selection rule: %s", name)
                return True
        return False

    def clear_selection_rules(self) -> None:
        """清空所有选择规则"""
        self._selection_rules.clear()
        self._logger.debug("Cleared all selection rules")
    
    def get_selection_rules(self) -> List[SelectionRule]:
        """
        获取所有选择规则
        
        Returns:
            List[SelectionRule]: 规则列表的副本
        """
        return self._selection_rules.copy()
    
    def get_rule_count(self) -> int:
        """
        获取规则数量
        
        Returns:
            int: 规则数量
        """
        return len(self._selection_rules)
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"<{self.__class__.__name__}("
            f"rules={self.get_rule_count()}, "
            f"default={self._default_strategy})>"
        )


# 向后兼容的别名
Selector = StrategySelector
