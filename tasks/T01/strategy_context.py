"""
策略上下文管理模块

提供策略的注册、管理和生命周期控制。
支持策略的激活切换和资源管理。
"""

import logging
from typing import Dict, Any, Optional, List

from strategy_base import Strategy


# 配置日志
logger = logging.getLogger(__name__)


class StrategyError(Exception):
    """策略相关错误"""


class StrategyContext:
    """
    策略上下文类
    
    管理策略的注册、激活和生命周期。
    提供策略的集中管理和访问接口。
    
    Attributes:
        _strategies: 策略字典 {策略名称: 策略实例}
        _active_strategy: 当前激活的策略名称
    
    使用示例:
        context = StrategyContext()
        
        # 注册策略
        context.register_strategy(my_strategy)
        
        # 设置激活策略
        context.set_active_strategy("MyStrategy")
        
        # 获取策略
        strategy = context.get_strategy("MyStrategy")
        
        # 使用上下文管理器
        with context:
            # 执行策略操作
            pass
        # 退出后自动清理
    """
    
    def __init__(self):
        """初始化策略上下文"""
        self._strategies: Dict[str, Strategy] = {}
        self._active_strategy: Optional[str] = None
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def register_strategy(
        self, 
        strategy: Strategy, 
        validate_config: bool = False
    ) -> None:
        """
        注册策略
        
        Args:
            strategy: 策略实例
            validate_config: 是否验证策略配置
        
        Raises:
            StrategyError: 策略无效或验证失败
        
        示例:
            strategy = MyStrategy()
            context.register_strategy(strategy, validate_config=True)
        """
        # 验证策略类型
        if not isinstance(strategy, Strategy):
            raise StrategyError(
                f"Strategy must be a Strategy instance, got {type(strategy).__name__}"
            )
        
        # 验证策略配置
        if validate_config:
            if not self._validate_strategy_config(strategy):
                raise StrategyError(
                    f"Strategy '{strategy.get_name()}' validation failed"
                )
        
        name = strategy.get_name()
        self._strategies[name] = strategy
        self._logger.debug(f"Registered strategy: {name}")
    
    def unregister_strategy(self, name: str) -> None:
        """
        注销策略
        
        Args:
            name: 策略名称
        
        说明:
            - 如果注销的是当前激活策略，会自动清除激活状态
            - 如果策略不存在，静默返回
        
        示例:
            context.unregister_strategy("MyStrategy")
        """
        if name not in self._strategies:
            self._logger.warning(f"Attempted to unregister non-existent strategy: {name}")
            return
        
        # 如果是当前激活策略，清除激活状态
        if self._active_strategy == name:
            self._active_strategy = None
            self._logger.debug(f"Cleared active strategy: {name}")
        
        del self._strategies[name]
        self._logger.debug(f"Unregistered strategy: {name}")
    
    def get_strategy(self, name: str) -> Optional[Strategy]:
        """
        获取策略实例
        
        Args:
            name: 策略名称
        
        Returns:
            Strategy: 策略实例，如果不存在则返回None
        
        示例:
            strategy = context.get_strategy("MyStrategy")
            if strategy:
                result = strategy.execute(stock_data, market_data)
        """
        return self._strategies.get(name)
    
    def list_strategies(self) -> List[str]:
        """
        列出所有已注册的策略名称
        
        Returns:
            List[str]: 策略名称列表
        
        示例:
            strategies = context.list_strategies()
            print(f"Available strategies: {strategies}")
        """
        return list(self._strategies.keys())
    
    def get_active_strategy(self) -> Optional[Strategy]:
        """
        获取当前激活的策略
        
        Returns:
            Strategy: 当前激活的策略实例，如果没有则返回None
        
        示例:
            active = context.get_active_strategy()
            if active:
                print(f"Active strategy: {active.get_name()}")
        """
        if self._active_strategy is None:
            return None
        return self._strategies.get(self._active_strategy)
    
    def set_active_strategy(
        self, 
        name: str, 
        strategy: Optional[Strategy] = None
    ) -> None:
        """
        设置激活的策略
        
        Args:
            name: 策略名称
            strategy: 策略实例（如果未注册，会自动注册）
        
        Raises:
            StrategyError: 策略不存在且未提供实例
        
        示例:
            # 设置已注册的策略为激活
            context.set_active_strategy("MyStrategy")
            
            # 直接设置并注册策略
            context.set_active_strategy("NewStrategy", strategy_instance)
        """
        # 如果提供了策略实例，先注册
        if strategy is not None:
            self.register_strategy(strategy)
        
        # 检查策略是否存在
        if name not in self._strategies:
            raise StrategyError(f"Strategy '{name}' not found")
        
        self._active_strategy = name
        self._logger.debug(f"Set active strategy: {name}")
    
    def clear(self) -> None:
        """
        清空所有策略
        
        清除所有已注册的策略和激活状态。
        
        示例:
            context.clear()
            assert context.list_strategies() == []
        """
        self._strategies.clear()
        self._active_strategy = None
        self._logger.debug("Cleared all strategies")
    
    def has_strategy(self, name: str) -> bool:
        """
        检查策略是否存在
        
        Args:
            name: 策略名称
        
        Returns:
            bool: 策略是否存在
        """
        return name in self._strategies
    
    def strategy_count(self) -> int:
        """
        获取策略数量
        
        Returns:
            int: 已注册的策略数量
        """
        return len(self._strategies)
    
    def get_all_strategies(self) -> List[Strategy]:
        """
        获取所有策略实例
        
        Returns:
            List[Strategy]: 所有策略实例列表
        """
        return list(self._strategies.values())
    
    def get_strategy_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取策略信息
        
        Args:
            name: 策略名称
        
        Returns:
            Dict[str, Any]: 策略信息字典，如果不存在则返回None
        """
        strategy = self.get_strategy(name)
        if strategy is None:
            return None
        return strategy.get_info()
    
    def _validate_strategy_config(self, strategy: Strategy) -> bool:
        """
        验证策略配置
        
        Args:
            strategy: 策略实例
        
        Returns:
            bool: 配置是否有效
        """
        try:
            return strategy.validate()
        except Exception as e:
            self._logger.warning(f"Strategy validation error: {e}")
            return False
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.clear()
        # 不抑制异常
        return False
    
    def __repr__(self) -> str:
        """字符串表示"""
        return (
            f"<{self.__class__.__name__}("
            f"strategies={self.strategy_count()}, "
            f"active={self._active_strategy})>"
        )
    
    def __len__(self) -> int:
        """策略数量"""
        return self.strategy_count()
    
    def __contains__(self, name: str) -> bool:
        """检查是否包含策略"""
        return self.has_strategy(name)
