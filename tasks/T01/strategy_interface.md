# Strategy 基类接口文档

## 概述

`strategy_base.py` 提供了T01多策略框架的基础架构，使用**策略模式(Strategy Pattern)**设计，支持多种选股策略变体的统一接口。

## 核心组件

### 1. StrategyConfig - 策略配置类

用于存储和管理策略的参数配置。

#### 属性

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `name` | str | 必填 | 配置名称 |
| `params` | Dict[str, Any] | {} | 策略参数字典 |
| `enabled` | bool | True | 是否启用 |
| `description` | str | "" | 配置描述 |

#### 方法

```python
# 创建配置
config = StrategyConfig(
    name="trend_config",
    params={"threshold": 0.5, "window": 20},
    enabled=True,
    description="趋势跟踪配置"
)

# 转换为字典
data = config.to_dict()

# 从字典创建
config = StrategyConfig.from_dict(data)

# 深拷贝
config_copy = config.copy()
```

---

### 2. StrategyMetadata - 策略元数据类

存储策略的基本信息，用于策略管理和展示。

#### 属性

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `name` | str | 必填 | 策略名称 |
| `description` | str | "" | 策略描述 |
| `version` | str | "1.0.0" | 版本号 |
| `author` | str | "" | 作者 |
| `strategy_type` | str | "unknown" | 策略类型 |
| `tags` | List[str] | [] | 标签列表 |
| `created_at` | Optional[str] | None | 创建时间 |
| `updated_at` | Optional[str] | None | 更新时间 |

#### 方法

```python
# 创建元数据
metadata = StrategyMetadata(
    name="TrendFollowingStrategy",
    description="基于趋势跟踪的选股策略",
    version="1.0.0",
    author="T01 Team",
    strategy_type=StrategyType.TREND_FOLLOWING,
    tags=["trend", "momentum"]
)

# 序列化
data = metadata.to_dict()

# 反序列化
metadata = StrategyMetadata.from_dict(data)
```

---

### 3. StrategyResult - 策略结果类

封装策略选股和评分的结果。

#### 属性

| 属性名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `selected_stocks` | List[str] | [] | 选中的股票代码列表 |
| `scores` | Dict[str, float] | {} | 股票评分字典 |
| `metadata` | Dict[str, Any] | {} | 额外元数据 |
| `success` | bool | True | 是否执行成功 |
| `error_message` | Optional[str] | None | 错误信息 |
| `execution_time_ms` | Optional[float] | None | 执行时间(毫秒) |

#### 方法

```python
# 验证结果有效性
is_valid = result.is_valid()
# 检查：1) 所有选中股票都有分数 2) 分数在0-100范围内

# 获取评分最高的N只股票
top_stocks = result.get_top_stocks(n=10)

# 序列化
data = result.to_dict()

# 反序列化
result = StrategyResult.from_dict(data)
```

---

### 4. Strategy - 抽象基类

所有选股策略必须继承的抽象基类，定义了策略的通用接口。

#### 抽象方法（必须实现）

##### `select(stock_data, market_data) -> List[str]`

选股逻辑，根据股票数据和市场数据筛选符合条件的股票。

**参数：**
- `stock_data` (Dict[str, Any]): 股票数据字典
  ```python
  {
      "stocks": ["000001.SZ", "000002.SZ"],
      "fundamentals": {...},
      "technical": {...}
  }
  ```
- `market_data` (Dict[str, Any]): 市场数据字典
  ```python
  {
      "index": {"close": 3000, "change_pct": 1.5},
      "sectors": {...}
  }
  ```

**返回：**
- `List[str]`: 选中的股票代码列表

**异常：**
- `ValueError`: 输入数据格式不正确

---

##### `score(stock_data) -> Dict[str, float]`

评分逻辑，对股票进行评分（0-100）。

**参数：**
- `stock_data` (Dict[str, Any]): 股票数据字典
  ```python
  {
      "000001.SZ": {"close": 10.5, "volume": 1000000},
      "000002.SZ": {"close": 20.0, "volume": 2000000}
  }
  ```

**返回：**
- `Dict[str, float]`: 股票评分字典 {股票代码: 分数}
- 分数范围：0-100，越高表示越符合策略

**异常：**
- `ValueError`: 输入数据格式不正确

---

##### `validate() -> bool`

验证策略配置是否有效。

**返回：**
- `bool`: 配置是否有效

**验证项：**
- 必需参数是否存在
- 参数值是否在有效范围内
- 配置是否完整

---

##### `get_name() -> str`

获取策略名称。

**返回：**
- `str`: 策略的唯一标识名称

---

##### `get_description() -> str`

获取策略描述。

**返回：**
- `str`: 策略的详细描述，包括适用场景和逻辑说明

---

#### 具体方法（可继承或覆盖）

##### `execute(stock_data, market_data) -> StrategyResult`

执行完整的策略流程。

**执行流程：**
1. 调用 `validate()` 验证配置
2. 如果验证失败，返回失败结果
3. 调用 `select()` 选股
4. 调用 `score()` 评分
5. 封装结果返回

**参数：**
- `stock_data` (Dict[str, Any]): 股票数据
- `market_data` (Dict[str, Any]): 市场数据

**返回：**
- `StrategyResult`: 策略执行结果

---

##### `set_config(config) -> None`

设置策略配置。

**参数：**
- `config` (Optional[StrategyConfig]): 策略配置对象，None则使用默认配置

---

##### `get_config() -> StrategyConfig`

获取策略配置的深拷贝。

**返回：**
- `StrategyConfig`: 配置的深拷贝，防止外部修改

---

##### `set_metadata(metadata) -> None`

设置策略元数据。

**参数：**
- `metadata` (StrategyMetadata): 策略元数据对象

---

##### `get_metadata() -> StrategyMetadata`

获取策略元数据。

**返回：**
- `StrategyMetadata`: 策略元数据

---

##### `get_info() -> Dict[str, Any]`

获取策略完整信息。

**返回：**
```python
{
    "name": str,
    "description": str,
    "config": Dict[str, Any],
    "metadata": Dict[str, Any]
}
```

---

## 使用示例

### 创建自定义策略

```python
from strategy_base import Strategy, StrategyConfig, StrategyMetadata, StrategyType

class TrendFollowingStrategy(Strategy):
    """趋势跟踪策略示例"""
    
    def __init__(self):
        super().__init__()
        self._metadata = StrategyMetadata(
            name="TrendFollowingStrategy",
            description="基于均线突破的趋势跟踪策略",
            version="1.0.0",
            strategy_type=StrategyType.TREND_FOLLOWING
        )
    
    def select(self, stock_data, market_data):
        """选择突破均线的股票"""
        selected = []
        for code, data in stock_data.items():
            if data.get("close", 0) > data.get("ma20", float('inf')):
                selected.append(code)
        return selected
    
    def score(self, stock_data):
        """根据突破强度评分"""
        scores = {}
        for code, data in stock_data.items():
            close = data.get("close", 0)
            ma20 = data.get("ma20", 1)
            strength = (close - ma20) / ma20 * 100
            scores[code] = min(100, max(0, 50 + strength * 10))
        return scores
    
    def validate(self):
        """验证配置"""
        params = self._config.params
        return "threshold" in params and 0 <= params["threshold"] <= 1
    
    def get_name(self):
        return "TrendFollowingStrategy"
    
    def get_description(self):
        return "基于均线突破的趋势跟踪策略，适用于牛市环境"


# 使用策略
strategy = TrendFollowingStrategy()

# 配置策略
config = StrategyConfig(
    name="trend_config",
    params={"threshold": 0.5, "ma_period": 20},
    description="趋势跟踪配置"
)
strategy.set_config(config)

# 执行策略
stock_data = {
    "000001.SZ": {"close": 15.5, "ma20": 14.8, "volume": 1000000},
    "000002.SZ": {"close": 25.0, "ma20": 26.0, "volume": 2000000}
}
market_data = {
    "index": {"close": 3000, "change_pct": 1.5}
}

result = strategy.execute(stock_data, market_data)
print(f"选中股票: {result.selected_stocks}")
print(f"评分: {result.scores}")
```

---

## 策略类型常量

```python
from strategy_base import StrategyType

StrategyType.TREND_FOLLOWING  # "trend_following" - 趋势跟踪型
StrategyType.REVERSAL         # "reversal" - 反转抄底型
StrategyType.EVENT_DRIVEN     # "event_driven" - 事件驱动型
StrategyType.VALUE            # "value" - 价值型
StrategyType.GROWTH           # "growth" - 成长型
StrategyType.MOMENTUM         # "momentum" - 动量型
StrategyType.CUSTOM           # "custom" - 自定义类型
```

---

## 向后兼容

为了兼容现有代码，提供了别名：

```python
from strategy_base import BaseStrategy  # 等同于 Strategy
```

---

## 测试

运行测试：

```bash
cd /root/.openclaw/workspace/tasks/T01
python3 -m pytest test_strategy_base.py -v
```

测试覆盖率目标：> 90%

---

## 设计原则

1. **单一职责**：每个策略只负责一种选股逻辑
2. **开闭原则**：通过继承扩展新策略，不修改现有代码
3. **依赖倒置**：高层模块依赖Strategy抽象，不依赖具体策略
4. **接口隔离**：策略只暴露必要的方法

---

## 注意事项

1. **抽象方法必须实现**：子类必须实现所有`@abstractmethod`装饰的方法
2. **配置线程安全**：`get_config()`返回深拷贝，防止外部修改影响策略
3. **结果验证**：使用`StrategyResult.is_valid()`验证结果完整性
4. **异常处理**：`execute()`方法会捕获异常并返回失败结果
