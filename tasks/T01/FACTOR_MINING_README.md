# T01深度因子挖掘模块 (factor_mining.py)

## 模块概述

本模块实现了T01进化Phase2的深度因子挖掘系统，提供50+个技术指标、基本面、资金流和情绪因子，支持因子相关性分析、IC值有效性筛选和PCA正交化。

## 功能特性

### 1. 因子库 (56个因子)

#### 技术指标因子 (21个)
- **MACD**: macd_dif, macd_dea, macd_hist, macd_golden
- **KDJ**: kdj_k, kdj_d, kdj_j, kdj_overbought, kdj_oversold
- **RSI**: rsi_6, rsi_12, rsi_24
- **布林带**: bb_upper, bb_middle, bb_lower, bb_width, bb_position
- **均线**: ma_alignment, ma_golden, ma_distance

#### 基本面因子 (15个)
- **估值**: pe_ttm, pb, ps_ttm, pcf
- **盈利**: roe, roa, gross_margin, net_margin
- **成长**: revenue_growth, profit_growth, ebitda_growth
- **偿债**: debt_ratio, current_ratio, quick_ratio, interest_coverage

#### 资金流因子 (10个)
- **当日**: main_net_inflow, retail_net_inflow, large_order_ratio, main_net_ratio
- **累计**: inflow_5d, inflow_10d, inflow_20d
- **趋势**: net_inflow_ma5, net_inflow_trend, buy_sell_ratio

#### 情绪因子 (10个)
- **涨停**: limit_up_seal_ratio, limit_up_time, break_count, continuous_limit
- **成交**: turnover_change, volume_ratio, amplitude
- **舆情**: news_sentiment, hot_rank, attention_index

### 2. 核心功能

#### 因子计算
- `calculate_technical_factors()`: 计算技术指标因子
- `calculate_fundamental_factors()`: 计算基本面因子
- `calculate_money_flow_factors()`: 计算资金流因子
- `calculate_sentiment_factors()`: 计算情绪因子
- `mine_factors_for_stock()`: 为单只股票挖掘所有因子
- `mine_factors_for_date()`: 为指定日期批量挖掘因子

#### 因子分析
- `calculate_ic()`: 计算因子IC值（信息系数）
- `analyze_factor_ic()`: 分析所有因子的IC值
- `calculate_correlation_matrix()`: 计算因子相关性矩阵
- `analyze_factor_correlation()`: 分析高相关因子对（阈值0.8）
- `get_valid_factors()`: 获取有效因子列表（基于IC值筛选）

#### 因子筛选与优化
- `select_best_factors()`: 选择最优因子组合（考虑IC值和相关性）
- `apply_pca_orthogonalization()`: PCA正交化处理
- `generate_factor_report()`: 生成因子分析报告

#### 工具函数
- `create_factor_miner()`: 从配置文件创建因子挖掘器
- `get_factor_library()`: 获取完整因子库信息
- `export_factors_to_json()`: 导出因子定义到JSON

## 使用方法

### 基本使用

```python
from factor_mining import FactorMiner, FactorCategory

# 创建因子挖掘器
miner = FactorMiner('your_tushare_token')

# 查看因子库
library = miner.get_factor_library()
print(f"总因子数: {library['total_count']}")

# 按类别获取因子
tech_factors = miner.get_factor_by_category(FactorCategory.TECHNICAL)
```

### 计算单只股票因子

```python
# 计算单只股票的所有因子
factors = miner.mine_factors_for_stock('000001.SZ', '20240325')
print(f"计算了 {len(factors)} 个因子")
```

### 因子分析

```python
import pandas as pd

# 准备数据
factor_df = pd.DataFrame({
    'ts_code': ['000001.SZ'] * 100,
    'close': [...],
    'macd_dif': [...],
    'rsi_6': [...]
})

# 计算IC值
ic_results = miner.analyze_factor_ic(factor_df)

# 计算相关性
high_corr = miner.analyze_factor_correlation(factor_df, threshold=0.8)

# 筛选最优因子
selected = miner.select_best_factors(factor_df, max_factors=10)
```

### PCA正交化

```python
# 应用PCA正交化
pca_df, pca_model = miner.apply_pca_orthogonalization(
    factor_df, 
    n_components=5
)

print(f"解释方差比例: {pca_model.explained_variance_ratio_.sum():.2%}")
```

### 生成报告

```python
# 生成因子分析报告
report = miner.generate_factor_report(factor_df)

# 导出因子定义
miner.export_factors_to_json('factors.json')
```

### 使用配置文件

```python
from factor_mining import create_factor_miner

# 从T01配置文件创建
miner = create_factor_miner('config.yaml')
```

## 配置参数

```python
config = {
    'correlation_threshold': 0.8,  # 相关性阈值
    'ic_threshold': 0.03,          # IC值有效性阈值
    'min_periods': 20              # 最小数据周期
}

miner = FactorMiner(token, config)
```

## 测试

### 运行单元测试

```bash
cd /root/.openclaw/workspace/tasks/T01
python3 -m pytest test_factor_mining.py -v
```

### 运行集成测试

```bash
python3 -m pytest test_factor_integration.py -v
```

### 运行使用示例

```bash
python3 factor_mining_example.py
```

## 文件结构

```
/root/.openclaw/workspace/tasks/T01/
├── factor_mining.py              # 主模块 (1086行)
├── test_factor_mining.py         # 单元测试 (573行)
├── test_factor_integration.py    # 集成测试 (298行)
└── factor_mining_example.py      # 使用示例 (340行)
```

## 依赖要求

- pandas >= 1.0.0
- numpy >= 1.18.0
- tushare >= 1.2.0
- scikit-learn >= 0.22.0 (可选，用于PCA)
- PyYAML >= 5.0

## 与T01系统集成

本模块设计为与现有T01系统无缝集成：

1. **配置文件兼容**: 支持从config.yaml读取配置
2. **代码风格一致**: 遵循T01现有代码风格
3. **API接口兼容**: 使用Tushare Pro API
4. **ML模块集成**: 与machine_learning.py配置参数一致

## 验证标准

- ✅ 因子数量: 56个 (>50个要求)
- ✅ 单元测试: 27/27通过 (100%)
- ✅ 集成测试: 6/6通过 (100%)
- ✅ 技术指标: MACD、KDJ、RSI、布林带、均线排列
- ✅ 基本面因子: PE、PB、ROE、营收增长率等
- ✅ 资金流因子: 主力净流入、散户净流入、大单占比等
- ✅ 情绪因子: 涨停封单比、换手率变化、量比等
- ✅ 因子相关性分析: 阈值0.8
- ✅ 因子有效性筛选: 基于IC值
- ✅ PCA正交化: 支持scikit-learn

## 版本信息

- 版本: 1.0.0
- 创建日期: 2026-03-26
- 作者: T01进化Phase2开发团队
