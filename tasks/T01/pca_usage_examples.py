"""
PCA因子正交化使用示例

本示例演示如何在T01评分系统中使用PCA因子正交化功能。

PCA（主成分分析）用于消除因子间的多重共线性，提取独立的因子信息，
提高评分系统的稳定性和可解释性。
"""

import yaml
import pandas as pd
import numpy as np
from datetime import datetime


def example_1_basic_usage():
    """
    示例1: 基本使用 - 在配置中启用PCA
    
    默认情况下PCA是关闭的，需要在config.yaml中手动启用。
    """
    print("=" * 60)
    print("示例1: 基本使用 - 启用PCA")
    print("=" * 60)
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 启用PCA
    config['pca'] = {
        'enabled': True,           # 启用PCA
        'variance_threshold': 0.9,  # 保留90%的方差
        'standardize': True         # 标准化数据
    }
    
    print("\nPCA配置:")
    print(f"  enabled: {config['pca']['enabled']}")
    print(f"  variance_threshold: {config['pca']['variance_threshold']}")
    print(f"  standardize: {config['pca']['standardize']}")
    
    # 初始化策略
    from limit_up_strategy_new import LimitUpScoringStrategyV2
    
    # 注意：实际使用时需要有效的Tushare token
    # strategy = LimitUpScoringStrategyV2(config)
    
    print("\n策略初始化后，PCA因子转换器将自动创建")
    print("当调用calculate_t_day_score时，如果PCA启用，将自动应用PCA转换")


def example_2_pca_transform_only():
    """
    示例2: 单独使用PCA转换
    
    可以直接使用FactorTransformer进行因子转换，
    不依赖于完整的评分系统。
    """
    print("\n" + "=" * 60)
    print("示例2: 单独使用PCA转换")
    print("=" * 60)
    
    from factor_transformer import FactorTransformer
    
    # 创建模拟因子数据
    np.random.seed(42)
    n_stocks = 50
    
    factor_data = pd.DataFrame({
        'first_limit_time_score': np.random.uniform(0, 30, n_stocks),
        'order_quality_score': np.random.uniform(0, 25, n_stocks),
        'liquidity_score': np.random.uniform(0, 20, n_stocks),
        'money_flow_score': np.random.uniform(0, 15, n_stocks),
        'sector_score': np.random.uniform(0, 10, n_stocks),
        'dragon_list_score': np.random.uniform(0, 10, n_stocks),
        'sentiment_score': np.random.uniform(-10, 10, n_stocks)
    }, index=[f'STOCK_{i:04d}' for i in range(n_stocks)])
    
    print(f"\n原始因子数据: {factor_data.shape[0]}只股票 × {factor_data.shape[1]}个因子")
    print(f"因子列表: {list(factor_data.columns)}")
    
    # 创建转换器并应用PCA
    transformer = FactorTransformer(variance_threshold=0.9)
    
    # 映射因子到主成分
    result = transformer.map_factors_to_components(factor_data)
    components_df = result['components']
    mapping_info = result['mapping_info']
    
    print(f"\nPCA转换结果:")
    print(f"  原始因子数: {mapping_info['n_original_features']}")
    print(f"  主成分数: {mapping_info['n_components']}")
    print(f"  累积方差解释度: {mapping_info['total_explained_variance']:.2%}")
    
    # 转换为评分
    scores = transformer.components_to_scores(use_variance_weights=True)
    
    print(f"\n评分统计:")
    print(f"  评分数量: {len(scores)}")
    print(f"  评分范围: [{scores.min():.2f}, {scores.max():.2f}]")
    print(f"  评分均值: {scores.mean():.2f}")
    
    # 查看因子贡献度
    print(f"\n第一个主成分的因子贡献度:")
    contribution = transformer.get_factor_contribution(0)
    for _, row in contribution.head(3).iterrows():
        print(f"  {row['factor_name']}: {row['contribution']:.3f}")


def example_3_compare_with_and_without_pca():
    """
    示例3: 对比使用PCA和不使用PCA的评分结果
    """
    print("\n" + "=" * 60)
    print("示例3: 对比使用PCA和不使用PCA")
    print("=" * 60)
    
    from factor_transformer import FactorTransformer
    
    # 创建相关因子数据（模拟多重共线性）
    np.random.seed(42)
    n_stocks = 30
    
    # 创建基础因子
    base_factor = np.random.randn(n_stocks)
    
    # 创建相关因子（与base_factor相关）
    factor_data = pd.DataFrame({
        'momentum': base_factor + np.random.randn(n_stocks) * 0.2,
        'trend': base_factor * 0.8 + np.random.randn(n_stocks) * 0.3,
        'strength': base_factor * 0.9 + np.random.randn(n_stocks) * 0.1,
        'volume': np.random.randn(n_stocks),
        'volatility': np.random.randn(n_stocks)
    }, index=[f'STOCK_{i:04d}' for i in range(n_stocks)])
    
    print(f"\n模拟数据: {n_stocks}只股票，5个因子（前3个高度相关）")
    
    # 不使用PCA：简单求和
    simple_scores = factor_data.sum(axis=1)
    
    # 使用PCA
    transformer = FactorTransformer(variance_threshold=0.9)
    transformer.map_factors_to_components(factor_data)
    pca_scores = transformer.components_to_scores(use_variance_weights=True)
    
    # 标准化到相同范围
    simple_scores = (simple_scores - simple_scores.min()) / (simple_scores.max() - simple_scores.min()) * 100
    pca_scores = (pca_scores - pca_scores.min()) / (pca_scores.max() - pca_scores.min()) * 100
    
    print(f"\n简单求和评分:")
    print(f"  均值: {simple_scores.mean():.2f}, 标准差: {simple_scores.std():.2f}")
    
    print(f"\nPCA评分:")
    print(f"  均值: {pca_scores.mean():.2f}, 标准差: {pca_scores.std():.2f}")
    
    # 计算排名相关性
    from scipy.stats import spearmanr
    corr, _ = spearmanr(simple_scores, pca_scores)
    print(f"\n排名相关性 (Spearman): {corr:.3f}")
    print("  注：相关性较低说明PCA消除了多重共线性的影响")


def example_4_different_variance_thresholds():
    """
    示例4: 不同方差阈值的影响
    """
    print("\n" + "=" * 60)
    print("示例4: 不同方差阈值的影响")
    print("=" * 60)
    
    from factor_transformer import FactorTransformer
    
    # 创建模拟数据
    np.random.seed(42)
    factor_data = pd.DataFrame(
        np.random.randn(100, 20),
        columns=[f'factor_{i}' for i in range(20)]
    )
    
    thresholds = [0.8, 0.9, 0.95, 0.99]
    
    print(f"\n数据: 100个样本，20个因子")
    print(f"\n不同方差阈值的效果:")
    print(f"{'阈值':<10} {'主成分数':<12} {'实际保留方差':<15}")
    print("-" * 40)
    
    for threshold in thresholds:
        transformer = FactorTransformer(variance_threshold=threshold)
        result = transformer.map_factors_to_components(factor_data)
        
        n_comp = result['mapping_info']['n_components']
        actual_variance = result['mapping_info']['total_explained_variance']
        
        print(f"{threshold:<10.2f} {n_comp:<12} {actual_variance:<15.2%}")


def example_5_integration_with_strategy():
    """
    示例5: 与评分系统完整集成
    
    展示如何在实际选股流程中使用PCA。
    """
    print("\n" + "=" * 60)
    print("示例5: 与评分系统完整集成")
    print("=" * 60)
    
    print("""
在实际使用中，PCA集成是自动的：

1. 在config.yaml中启用PCA:
   pca:
     enabled: true
     variance_threshold: 0.9
     standardize: true

2. 初始化策略时，PCA组件自动创建:
   strategy = LimitUpScoringStrategyV2(config)
   
3. 调用评分方法时，如果PCA启用，自动应用:
   results = strategy.calculate_t_day_score(stock_data, trade_date)
   
   内部流程:
   a. 计算各因子得分
   b. 如果PCA启用且样本数>=2:
      - 提取因子数据
      - 应用PCA转换
      - 使用主成分评分
      - 综合评分 = PCA评分 * 0.7 + 基础评分 * 0.3
   c. 返回评分结果

4. PCA信息存储在结果中:
   pca_info = results.attrs.get('pca_info', {})
   print(f"主成分数: {pca_info.get('n_components')}")
   print(f"保留方差: {pca_info.get('total_explained_variance'):.1%}")
""")


def example_6_error_handling():
    """
    示例6: 错误处理和边界情况
    """
    print("\n" + "=" * 60)
    print("示例6: 错误处理和边界情况")
    print("=" * 60)
    
    from limit_up_strategy_new import LimitUpScoringStrategyV2
    
    # 创建最小配置
    config = {
        'api': {'api_key': 'test'},
        'strategy': {
            't_day_scoring': {},
            't1_auction_scoring': {},
            'risk_control': {},
            'sentiment_analysis': {'enabled': False}
        },
        'pca': {
            'enabled': True,
            'variance_threshold': 0.9,
            'standardize': True
        }
    }
    
    print("\n边界情况处理:")
    print("  1. 空数据: 返回空结果，记录警告")
    print("  2. 单只股票: 返回原始因子之和，记录警告")
    print("  3. 缺失值: 自动填充为0")
    print("  4. PCA失败: 回退到原始评分，记录错误")
    
    print("\n代码示例:")
    print("""
    # 空数据处理
    empty_df = pd.DataFrame()
    result = strategy._apply_pca_transform(empty_df)
    # 结果: {'scores': Series(), 'pca_info': {'error': 'Empty input data'}}
    
    # 单只股票处理
    single_stock = pd.DataFrame({'factor1': [10], 'factor2': [20]}, index=['000001.SZ'])
    result = strategy._apply_pca_transform(single_stock)
    # 结果: 返回因子之和作为评分
    
    # 缺失值处理
    data_with_nan = pd.DataFrame({
        'factor1': [10, np.nan, 30],
        'factor2': [20, 25, np.nan]
    })
    result = strategy._apply_pca_transform(data_with_nan)
    # 结果: 缺失值自动填充为0
    """)


if __name__ == '__main__':
    print("\n" + "=" * 60)
    print("PCA因子正交化使用示例")
    print("=" * 60)
    
    # 运行所有示例
    example_1_basic_usage()
    example_2_pca_transform_only()
    example_3_compare_with_and_without_pca()
    example_4_different_variance_thresholds()
    example_5_integration_with_strategy()
    example_6_error_handling()
    
    print("\n" + "=" * 60)
    print("示例运行完成!")
    print("=" * 60)
