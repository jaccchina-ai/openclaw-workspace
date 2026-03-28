"""
Strategy基类与接口定义

提供多策略框架的基础抽象类和数据结构。
支持策略模式(Strategy Pattern)架构，允许不同的选股策略变体
（趋势跟踪型、反转抄底型、事件驱动型）共享相同的接口。
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List, Union
from copy import deepcopy
import json


@dataclass
class StrategyConfig:
    """
    策略配置类
    
    用于存储策略的参数配置，支持序列化和反序列化。
    
    Attributes:
        name: 策略配置名称
        params: 策略参数字典
        enabled: 是否启用该配置
        description: 配置描述
    """
    name: str
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyConfig':
        """从字典创建配置"""
        return cls(
            name=data.get("name", ""),
            params=data.get("params", {}),
            enabled=data.get("enabled", True),
            description=data.get("description", "")
        )
    
    def copy(self) -> 'StrategyConfig':
        """创建配置的深拷贝"""
        return StrategyConfig(
            name=self.name,
            params=deepcopy(self.params),
            enabled=self.enabled,
            description=self.description
        )


@dataclass
class StrategyMetadata:
    """
    策略元数据类
    
    存储策略的基本信息，用于策略管理和展示。
    
    Attributes:
        name: 策略名称
        description: 策略描述
        version: 策略版本号
        author: 策略作者
        strategy_type: 策略类型（如trend_following, reversal, event_driven）
        tags: 策略标签列表
        created_at: 创建时间
        updated_at: 更新时间
    """
    name: str
    description: str = ""
    version: str = "1.0.0"
    author: str = ""
    strategy_type: str = "unknown"
    tags: List[str] = field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """将元数据转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyMetadata':
        """从字典创建元数据"""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            version=data.get("version", "1.0.0"),
            author=data.get("author", ""),
            strategy_type=data.get("strategy_type", "unknown"),
            tags=data.get("tags", []),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at")
        )


@dataclass
class StrategyResult:
    """
    策略执行结果类
    
    封装策略选股和评分的结果。
    
    Attributes:
        selected_stocks: 选中的股票代码列表
        scores: 股票评分字典 {stock_code: score}
        metadata: 额外元数据
        success: 是否执行成功
        error_message: 错误信息（如果失败）
        execution_time_ms: 执行时间（毫秒）
    """
    selected_stocks: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    success: bool = True
    error_message: Optional[str] = None
    execution_time_ms: Optional[float] = None
    
    def is_valid(self) -> bool:
        """
        验证结果是否有效
        
        检查：
        1. 所有选中的股票都有对应的分数
        2. 分数在合理范围内（0-100）
        
        Returns:
            bool: 结果是否有效
        """
        # 检查所有选中的股票都有分数
        for stock in self.selected_stocks:
            if stock not in self.scores:
                return False
        
        # 检查分数范围
        for score in self.scores.values():
            if not isinstance(score, (int, float)):
                return False
            if score < 0 or score > 100:
                return False
        
        return True
    
    def get_top_stocks(self, n: int = 10) -> List[str]:
        """
        获取评分最高的N只股票
        
        Args:
            n: 返回的股票数量
            
        Returns:
            List[str]: 股票代码列表，按评分降序排列
        """
        sorted_stocks = sorted(
            self.scores.items(),
            key=lambda x: x[1],
            reverse=True
        )
        return [stock for stock, _ in sorted_stocks[:n]]
    
    def to_dict(self) -> Dict[str, Any]:
        """将结果转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'StrategyResult':
        """从字典创建结果"""
        return cls(
            selected_stocks=data.get("selected_stocks", []),
            scores=data.get("scores", {}),
            metadata=data.get("metadata", {}),
            success=data.get("success", True),
            error_message=data.get("error_message"),
            execution_time_ms=data.get("execution_time_ms")
        )


class Strategy(ABC):
    """
    策略抽象基类
    
    所有选股策略的基类，定义了策略的通用接口。
    子类必须实现所有抽象方法。
    
    使用示例:
        class MyStrategy(Strategy):
            def select(self, stock_data, market_data):
                # 实现选股逻辑
                return ["000001.SZ"]
            
            def score(self, stock_data):
                # 实现评分逻辑
                return {"000001.SZ": 85.5}
            
            def validate(self):
                # 验证配置
                return True
            
            def get_name(self):
                return "MyStrategy"
            
            def get_description(self):
                return "My custom strategy"
        
        strategy = MyStrategy()
        result = strategy.execute(stock_data, market_data)
    
    Attributes:
        _config: 策略配置
        _metadata: 策略元数据
    """
    
    def __init__(self):
        """初始化策略基类"""
        self._config: StrategyConfig = StrategyConfig(name=self.__class__.__name__)
        self._metadata: StrategyMetadata = StrategyMetadata(name=self.__class__.__name__)
    
    @abstractmethod
    def select(self, stock_data: Dict[str, Any], market_data: Dict[str, Any]) -> List[str]:
        """
        选股逻辑
        
        根据股票数据和市场数据，筛选出符合条件的股票。
        
        Args:
            stock_data: 股票数据字典，包含股票列表和基本面数据
                示例: {
                    "stocks": ["000001.SZ", "000002.SZ"],
                    "fundamentals": {...},
                    "technical": {...}
                }
            market_data: 市场数据字典，包含大盘指数和板块数据
                示例: {
                    "index": {"close": 3000, "change_pct": 1.5},
                    "sectors": {...}
                }
        
        Returns:
            List[str]: 选中的股票代码列表
        
        Raises:
            ValueError: 输入数据格式不正确
        """
        pass
    
    @abstractmethod
    def score(self, stock_data: Dict[str, Any]) -> Dict[str, float]:
        """
        评分逻辑
        
        对股票进行评分，返回每只股票的得分（0-100）。
        
        Args:
            stock_data: 股票数据字典
                示例: {
                    "000001.SZ": {"close": 10.5, "volume": 1000000, ...},
                    "000002.SZ": {"close": 20.0, "volume": 2000000, ...}
                }
        
        Returns:
            Dict[str, float]: 股票评分字典 {股票代码: 分数}
            分数范围: 0-100，越高表示越符合策略
        
        Raises:
            ValueError: 输入数据格式不正确
        """
        pass
    
    @abstractmethod
    def validate(self) -> bool:
        """
        验证策略配置
        
        检查策略配置是否有效，参数是否在合理范围内。
        
        Returns:
            bool: 配置是否有效
        
        验证项:
            - 必需参数是否存在
            - 参数值是否在有效范围内
            - 配置是否完整
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """
        获取策略名称
        
        Returns:
            str: 策略的唯一标识名称
        """
        pass
    
    @abstractmethod
    def get_description(self) -> str:
        """
        获取策略描述
        
        Returns:
            str: 策略的详细描述，包括适用场景和逻辑说明
        """
        pass
    
    def execute(self, stock_data: Dict[str, Any], market_data: Dict[str, Any]) -> StrategyResult:
        """
        执行策略
        
        执行完整的策略流程：验证配置 -> 选股 -> 评分。
        
        Args:
            stock_data: 股票数据
            market_data: 市场数据
        
        Returns:
            StrategyResult: 策略执行结果
        
        执行流程:
            1. 调用validate()验证配置
            2. 如果验证失败，返回失败结果
            3. 调用select()选股
            4. 调用score()评分
            5. 封装结果返回
        """
        import time
        start_time = time.time()
        
        # 验证配置
        if not self.validate():
            return StrategyResult(
                success=False,
                error_message="Strategy validation failed",
                metadata={"strategy_name": self.get_name()}
            )
        
        try:
            # 选股
            selected = self.select(stock_data, market_data)
            
            # 评分
            scores = self.score(stock_data)
            
            # 只保留选中股票的分数
            filtered_scores = {k: v for k, v in scores.items() if k in selected}
            
            execution_time = (time.time() - start_time) * 1000
            
            return StrategyResult(
                selected_stocks=selected,
                scores=filtered_scores,
                success=True,
                metadata={
                    "strategy_name": self.get_name(),
                    "strategy_description": self.get_description(),
                    "config_name": self._config.name
                },
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            return StrategyResult(
                success=False,
                error_message=str(e),
                metadata={"strategy_name": self.get_name()}
            )
    
    def set_config(self, config: Optional[StrategyConfig]) -> None:
        """
        设置策略配置
        
        Args:
            config: 策略配置对象，如果为None则使用默认配置
        """
        if config is None:
            self._config = StrategyConfig(name=self.__class__.__name__)
        else:
            self._config = config.copy()
    
    def get_config(self) -> StrategyConfig:
        """
        获取策略配置
        
        Returns:
            StrategyConfig: 配置的深拷贝，防止外部修改
        """
        return self._config.copy()
    
    def set_metadata(self, metadata: StrategyMetadata) -> None:
        """
        设置策略元数据
        
        Args:
            metadata: 策略元数据对象
        """
        self._metadata = metadata
    
    def get_metadata(self) -> StrategyMetadata:
        """
        获取策略元数据
        
        Returns:
            StrategyMetadata: 策略元数据
        """
        return self._metadata
    
    def get_info(self) -> Dict[str, Any]:
        """
        获取策略完整信息
        
        Returns:
            Dict[str, Any]: 包含名称、描述、配置、元数据的字典
        """
        return {
            "name": self.get_name(),
            "description": self.get_description(),
            "config": self._config.to_dict(),
            "metadata": self._metadata.to_dict()
        }
    
    def __repr__(self) -> str:
        """策略对象的字符串表示"""
        return f"<{self.__class__.__name__}(name='{self.get_name()}')>"
    
    def __str__(self) -> str:
        """策略对象的友好字符串表示"""
        return f"{self.get_name()}: {self.get_description()}"


# 策略类型常量
class StrategyType:
    """策略类型常量定义"""
    TREND_FOLLOWING = "trend_following"      # 趋势跟踪型
    REVERSAL = "reversal"                     # 反转抄底型
    EVENT_DRIVEN = "event_driven"            # 事件驱动型
    VALUE = "value"                          # 价值型
    GROWTH = "growth"                        # 成长型
    MOMENTUM = "momentum"                    # 动量型
    CUSTOM = "custom"                        # 自定义类型


# 向后兼容的别名
BaseStrategy = Strategy


if __name__ == "__main__":
    # 简单的使用示例
    print("Strategy Base Module")
    print("=" * 50)
    
    # 展示配置
    config = StrategyConfig(
        name="example_config",
        params={"threshold": 0.5, "lookback": 20},
        description="示例配置"
    )
    print(f"Config: {config.to_dict()}")
    
    # 展示元数据
    metadata = StrategyMetadata(
        name="ExampleStrategy",
        description="示例策略",
        version="1.0.0",
        strategy_type=StrategyType.TREND_FOLLOWING
    )
    print(f"Metadata: {metadata.to_dict()}")
    
    # 展示结果
    result = StrategyResult(
        selected_stocks=["000001.SZ", "000002.SZ"],
        scores={"000001.SZ": 85.5, "000002.SZ": 78.0},
        success=True
    )
    print(f"Result: {result.to_dict()}")
    print(f"Is valid: {result.is_valid()}")
    print(f"Top stocks: {result.get_top_stocks(1)}")
