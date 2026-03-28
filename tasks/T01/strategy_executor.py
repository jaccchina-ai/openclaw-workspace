"""
策略执行器模块

提供策略的加载、执行和结果管理。
支持批量执行和异常处理。
"""

import logging
import time
from typing import Dict, Any, Optional, Type
from dataclasses import dataclass

from strategy_base import Strategy, StrategyConfig, StrategyResult
from strategy_context import StrategyContext, StrategyError


# 配置日志
logger = logging.getLogger(__name__)


@dataclass
class ExecutionResult:
    """
    执行结果封装类
    
    封装策略执行的详细结果和元数据。
    
    Attributes:
        strategy_name: 策略名称
        result: 策略执行结果
        execution_time_ms: 执行时间（毫秒）
        error: 异常对象（如果有）
    """
    strategy_name: str
    result: Optional[StrategyResult]
    execution_time_ms: float
    error: Optional[Exception] = None


class StrategyExecutor:
    """
    策略执行器类
    
    负责策略的加载、执行和结果管理。
    支持批量执行、异常处理和执行统计。
    
    Attributes:
        context: 策略上下文
        _results: 执行结果缓存
    
    使用示例:
        executor = StrategyExecutor()
        
        # 加载策略
        strategy = executor.load_strategy(MyStrategy, {"name": "MyStrategy"})
        
        # 执行策略
        result = executor.execute("MyStrategy", stock_data, market_data)
        
        # 批量执行
        results = executor.execute_all(stock_data, market_data)
        
        # 使用上下文管理器
        with executor as exec:
            exec.execute("MyStrategy", stock_data, market_data)
    """
    
    def __init__(self, context: Optional[StrategyContext] = None):
        """
        初始化策略执行器
        
        Args:
            context: 策略上下文实例，如果为None则创建新实例
        """
        self.context = context if context is not None else StrategyContext()
        self._results: Dict[str, StrategyResult] = {}
        self._execution_results: Dict[str, ExecutionResult] = {}
        self._logger = logging.getLogger(self.__class__.__name__)
    
    def load_strategy(
        self, 
        strategy_class: Type[Strategy], 
        config: Optional[Dict[str, Any]] = None
    ) -> Strategy:
        """
        加载策略
        
        创建策略实例并注册到上下文。
        
        Args:
            strategy_class: 策略类（继承自Strategy）
            config: 策略配置字典
        
        Returns:
            Strategy: 创建的策略实例
        
        Raises:
            StrategyError: 策略类无效
        
        示例:
            strategy = executor.load_strategy(
                TrendFollowingStrategy,
                {"name": "TrendStrategy", "params": {"threshold": 0.5}}
            )
        """
        # 验证策略类
        if not issubclass(strategy_class, Strategy):
            raise StrategyError(
                f"Strategy class must inherit from Strategy, got {strategy_class.__name__}"
            )
        
        # 创建策略实例
        strategy = strategy_class()
        
        # 应用配置
        if config is not None:
            if isinstance(config, dict):
                strategy_config = StrategyConfig.from_dict(config)
            else:
                strategy_config = StrategyConfig(name=strategy_class.__name__)
            strategy.set_config(strategy_config)
        
        # 注册到上下文
        self.context.register_strategy(strategy, validate_config=False)
        
        self._logger.debug(f"Loaded strategy: {strategy.get_name()}")
        return strategy
    
    def execute(
        self, 
        strategy_name: str, 
        stock_data: Dict[str, Any], 
        market_data: Dict[str, Any]
    ) -> StrategyResult:
        """
        执行指定策略
        
        Args:
            strategy_name: 策略名称
            stock_data: 股票数据
            market_data: 市场数据
        
        Returns:
            StrategyResult: 策略执行结果
        
        说明:
            - 如果策略不存在，返回失败结果
            - 如果执行异常，捕获异常并返回失败结果
            - 执行结果会被缓存
        
        示例:
            result = executor.execute("MyStrategy", stock_data, market_data)
            if result.success:
                print(f"Selected stocks: {result.selected_stocks}")
        """
        start_time = time.time()
        
        # 获取策略
        strategy = self.context.get_strategy(strategy_name)
        if strategy is None:
            error_msg = f"Strategy '{strategy_name}' not found"
            self._logger.error(error_msg)
            result = StrategyResult(
                success=False,
                error_message=error_msg,
                metadata={"strategy_name": strategy_name}
            )
            self._cache_result(strategy_name, result, start_time)
            return result
        
        # 检查策略状态
        try:
            if not strategy.validate():
                error_msg = f"Strategy '{strategy_name}' validation failed"
                self._logger.warning(error_msg)
                result = StrategyResult(
                    success=False,
                    error_message=error_msg,
                    metadata={"strategy_name": strategy_name}
                )
                self._cache_result(strategy_name, result, start_time)
                return result
        except Exception as e:
            self._logger.warning(f"Strategy validation error: {e}")
            # 继续执行，不阻止
        
        # 执行策略
        try:
            self._logger.debug(f"Executing strategy: {strategy_name}")
            result = strategy.execute(stock_data, market_data)
            self._cache_result(strategy_name, result, start_time)
            self._logger.debug(f"Strategy '{strategy_name}' executed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Strategy '{strategy_name}' execution failed: {str(e)}"
            self._logger.error(error_msg)
            
            result = StrategyResult(
                success=False,
                error_message=str(e),
                metadata={"strategy_name": strategy_name}
            )
            self._cache_result(strategy_name, result, start_time)
            return result
    
    def execute_all(
        self, 
        stock_data: Dict[str, Any], 
        market_data: Dict[str, Any]
    ) -> Dict[str, StrategyResult]:
        """
        执行所有已注册的策略
        
        Args:
            stock_data: 股票数据
            market_data: 市场数据
        
        Returns:
            Dict[str, StrategyResult]: 策略名称到执行结果的映射
        
        说明:
            - 逐个执行所有已注册的策略
            - 单个策略失败不影响其他策略执行
            - 返回所有策略的执行结果
        
        示例:
            results = executor.execute_all(stock_data, market_data)
            for name, result in results.items():
                print(f"{name}: {'✓' if result.success else '✗'}")
        """
        results = {}
        strategies = self.context.list_strategies()
        
        if not strategies:
            self._logger.warning("No strategies registered for execution")
            return results
        
        self._logger.info(f"Executing {len(strategies)} strategies")
        
        for strategy_name in strategies:
            try:
                result = self.execute(strategy_name, stock_data, market_data)
                results[strategy_name] = result
            except Exception as e:
                # 这个异常处理是双重保险，execute方法内部已经处理了大部分异常
                self._logger.error(f"Unexpected error executing '{strategy_name}': {e}")
                results[strategy_name] = StrategyResult(
                    success=False,
                    error_message=f"Unexpected error: {str(e)}",
                    metadata={"strategy_name": strategy_name}
                )
        
        return results
    
    def get_results(self) -> Dict[str, StrategyResult]:
        """
        获取所有执行结果
        
        Returns:
            Dict[str, StrategyResult]: 策略名称到执行结果的映射
        
        示例:
            results = executor.get_results()
            successful = [name for name, r in results.items() if r.success]
        """
        return self._results.copy()
    
    def clear_results(self) -> None:
        """
        清空执行结果
        
        清除所有缓存的执行结果。
        
        示例:
            executor.clear_results()
            assert executor.get_results() == {}
        """
        self._results.clear()
        self._execution_results.clear()
        self._logger.debug("Cleared all execution results")
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """
        获取执行摘要
        
        Returns:
            Dict[str, Any]: 执行统计信息
                - total: 总执行次数
                - successful: 成功次数
                - failed: 失败次数
                - success_rate: 成功率
        
        示例:
            summary = executor.get_execution_summary()
            print(f"Success rate: {summary['success_rate']:.1%}")
        """
        total = len(self._results)
        successful = sum(1 for r in self._results.values() if r.success)
        failed = total - successful
        
        success_rate = successful / total if total > 0 else 0.0
        
        return {
            "total": total,
            "successful": successful,
            "failed": failed,
            "success_rate": success_rate
        }
    
    def cleanup(self) -> None:
        """
        清理资源
        
        清理执行器和上下文中的所有资源。
        
        示例:
            executor.cleanup()
        """
        self.clear_results()
        self.context.clear()
        self._logger.debug("Executor cleanup completed")
    
    def _cache_result(
        self, 
        strategy_name: str, 
        result: StrategyResult, 
        start_time: float
    ) -> None:
        """
        缓存执行结果
        
        Args:
            strategy_name: 策略名称
            result: 执行结果
            start_time: 执行开始时间
        """
        execution_time = (time.time() - start_time) * 1000
        
        # 更新结果中的执行时间（如果未设置）
        if result.execution_time_ms is None:
            result.execution_time_ms = execution_time
        
        self._results[strategy_name] = result
        self._execution_results[strategy_name] = ExecutionResult(
            strategy_name=strategy_name,
            result=result,
            execution_time_ms=execution_time
        )
    
    def __enter__(self):
        """上下文管理器入口"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        self.cleanup()
        # 不抑制异常
        return False
    
    def __repr__(self) -> str:
        """字符串表示"""
        summary = self.get_execution_summary()
        return (
            f"<{self.__class__.__name__}("
            f"strategies={self.context.strategy_count()}, "
            f"executed={summary['total']}, "
            f"success_rate={summary['success_rate']:.1%})>"
        )
