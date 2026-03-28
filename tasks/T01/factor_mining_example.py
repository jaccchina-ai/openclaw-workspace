#!/usr/bin/env python3
"""
T01深度因子挖掘模块使用示例
展示如何在T01系统中集成和使用factor_mining模块
"""

import sys
import os
import logging
from datetime import datetime, timedelta

# 设置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def example_1_basic_usage():
    """示例1: 基本使用 - 创建因子挖掘器并查看因子库"""
    print("\n" + "=" * 70)
    print("示例1: 基本使用 - 创建因子挖掘器")
    print("=" * 70)
    
    from factor_mining import FactorMiner, FactorCategory
    
    # 创建因子挖掘器
    token = '870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab'
    miner = FactorMiner(token)
    
    # 获取因子库信息
    library = miner.get_factor_library()
    
    print(f"\n因子库统计:")
    print(f"  总因子数: {library['total_count']}")
    print(f"  技术指标: {library['technical_count']}")
    print(f"  基本面: {library['fundamental_count']}")
    print(f"  资金流: {library['money_flow_count']}")
    print(f"  情绪: {library['sentiment_count']}")
    
    # 按类别查看因子
    print("\n技术指标因子列表:")
    for factor in miner.get_factor_by_category(FactorCategory.TECHNICAL)[:5]:
        print(f"  - {factor.code}: {factor.name} ({factor.description})")


def example_2_calculate_factors():
    """示例2: 计算单只股票的所有因子"""
    print("\n" + "=" * 70)
    print("示例2: 计算单只股票的所有因子")
    print("=" * 70)
    
    from factor_mining import FactorMiner
    
    # 创建因子挖掘器
    token = '870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab'
    miner = FactorMiner(token)
    
    # 计算单只股票因子
    trade_date = '20240325'
    ts_code = '000001.SZ'  # 平安银行
    
    print(f"\n正在计算 {ts_code} 在 {trade_date} 的因子...")
    
    try:
        factors = miner.mine_factors_for_stock(ts_code, trade_date, lookback_days=60)
        
        if factors:
            print(f"\n成功计算 {len(factors)} 个因子:")
            
            # 按类别分组显示
            tech_factors = {k: v for k, v in factors.items() if k.startswith(('macd', 'kdj', 'rsi', 'bb', 'ma'))}
            print(f"\n技术指标因子 ({len(tech_factors)}个):")
            for k, v in list(tech_factors.items())[:5]:
                print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
            
            fund_factors = {k: v for k, v in factors.items() if k in ['pe_ttm', 'pb', 'roe', 'roa']}
            if fund_factors:
                print(f"\n基本面因子 ({len(fund_factors)}个):")
                for k, v in fund_factors.items():
                    print(f"  {k}: {v:.4f}" if isinstance(v, float) else f"  {k}: {v}")
        else:
            print("未能获取因子数据")
            
    except Exception as e:
        print(f"计算失败: {e}")


def example_3_factor_analysis():
    """示例3: 因子分析 - IC值和相关性"""
    print("\n" + "=" * 70)
    print("示例3: 因子分析 - IC值和相关性")
    print("=" * 70)
    
    from factor_mining import FactorMiner
    import pandas as pd
    import numpy as np
    
    # 创建模拟数据
    np.random.seed(42)
    n_samples = 100
    
    factor_df = pd.DataFrame({
        'ts_code': ['000001.SZ'] * 50 + ['000002.SZ'] * 50,
        'trade_date': ['20240301'] * 100,
        'close': np.random.uniform(10, 20, 100),
        'macd_dif': np.random.randn(100),
        'macd_dea': np.random.randn(100),
        'rsi_6': np.random.uniform(0, 100, 100),
        'kdj_k': np.random.uniform(0, 100, 100),
        'bb_position': np.random.uniform(0, 1, 100),
        'main_net_inflow': np.random.randn(100) * 1000000,
        'turnover_change': np.random.uniform(0.5, 2, 100)
    })
    
    # 创建因子挖掘器
    token = '870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab'
    miner = FactorMiner(token)
    
    print("\n1. 计算因子IC值:")
    ic_results = miner.analyze_factor_ic(factor_df, forward_period=5)
    
    for factor, ic in sorted(ic_results.items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
        print(f"  {factor}: IC = {ic:.4f}")
    
    print("\n2. 计算因子相关性矩阵:")
    corr_matrix = miner.calculate_correlation_matrix(factor_df)
    print(f"  矩阵形状: {corr_matrix.shape}")
    
    print("\n3. 高相关性因子对 (>0.8):")
    high_corr = miner.analyze_factor_correlation(factor_df, threshold=0.8)
    if high_corr:
        for factor, related in list(high_corr.items())[:3]:
            if related:
                print(f"  {factor} 与 {related[0][0]}: {related[0][1]:.4f}")
    else:
        print("  未发现高相关性因子对")


def example_4_factor_selection():
    """示例4: 因子筛选 - 选择最优因子组合"""
    print("\n" + "=" * 70)
    print("示例4: 因子筛选 - 选择最优因子组合")
    print("=" * 70)
    
    from factor_mining import FactorMiner
    import pandas as pd
    import numpy as np
    
    # 创建模拟数据
    np.random.seed(42)
    
    factor_df = pd.DataFrame({
        'ts_code': ['000001.SZ'] * 100,
        'trade_date': pd.date_range('2024-01-01', periods=100).strftime('%Y%m%d'),
        'close': 100 + np.random.randn(100).cumsum(),
        'factor1': np.random.randn(100),
        'factor2': np.random.randn(100) * 0.8 + 0.6 * np.random.randn(100),
        'factor3': np.random.randn(100) * 0.5,
        'factor4': np.random.randn(100) * 0.3,
        'factor5': np.random.randn(100) * 0.2
    })
    
    # 创建因子挖掘器
    token = '870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab'
    miner = FactorMiner(token)
    
    print("\n从所有因子中筛选最优组合:")
    selected = miner.select_best_factors(factor_df, max_factors=3, consider_correlation=True)
    
    print(f"\n选中的因子 ({len(selected)}个):")
    for i, factor in enumerate(selected, 1):
        print(f"  {i}. {factor}")


def example_5_pca_orthogonalization():
    """示例5: PCA正交化"""
    print("\n" + "=" * 70)
    print("示例5: PCA正交化")
    print("=" * 70)
    
    from factor_mining import FactorMiner
    import pandas as pd
    import numpy as np
    
    # 创建高维因子数据
    np.random.seed(42)
    
    factor_df = pd.DataFrame({
        'ts_code': ['000001.SZ'] * 100,
        'trade_date': ['20240301'] * 100
    })
    
    # 添加10个相关因子
    base = np.random.randn(100)
    for i in range(10):
        factor_df[f'factor_{i}'] = base * (0.5 + i * 0.05) + np.random.randn(100) * 0.5
    
    # 创建因子挖掘器
    token = '870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab'
    miner = FactorMiner(token)
    
    print(f"\n原始因子维度: {len([c for c in factor_df.columns if c.startswith('factor_')])}")
    
    # 应用PCA
    pca_df, pca_model = miner.apply_pca_orthogonalization(
        factor_df, 
        n_components=5,
        variance_threshold=0.95
    )
    
    if pca_model:
        print(f"PCA后主成分维度: 5")
        print(f"解释方差比例: {pca_model.explained_variance_ratio_.sum():.2%}")
        print(f"\n各主成分解释方差:")
        for i, ratio in enumerate(pca_model.explained_variance_ratio_, 1):
            print(f"  PC{i}: {ratio:.2%}")


def example_6_generate_report():
    """示例6: 生成因子分析报告"""
    print("\n" + "=" * 70)
    print("示例6: 生成因子分析报告")
    print("=" * 70)
    
    from factor_mining import FactorMiner
    import pandas as pd
    import numpy as np
    import json
    
    # 创建模拟数据
    np.random.seed(42)
    
    factor_df = pd.DataFrame({
        'ts_code': ['000001.SZ'] * 50 + ['000002.SZ'] * 50,
        'trade_date': ['20240301'] * 100,
        'close': np.random.uniform(10, 20, 100),
        'macd_dif': np.random.randn(100),
        'rsi_6': np.random.uniform(0, 100, 100),
        'kdj_k': np.random.uniform(0, 100, 100),
        'main_net_inflow': np.random.randn(100) * 1000000,
        'pe_ttm': np.random.uniform(5, 50, 100)
    })
    
    # 创建因子挖掘器
    token = '870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab'
    miner = FactorMiner(token)
    
    print("\n生成因子分析报告...")
    report = miner.generate_factor_report(factor_df)
    
    print(f"\n报告摘要:")
    print(f"  生成时间: {report['timestamp']}")
    print(f"  总因子数: {report['total_factors']}")
    print(f"  数据点数: {report['data_points']}")
    
    print(f"\nIC分析:")
    print(f"  平均IC: {report['ic_analysis'].get('mean_ic', 0):.4f}")
    print(f"  IC标准差: {report['ic_analysis'].get('std_ic', 0):.4f}")
    print(f"  有效因子数: {report['ic_analysis'].get('valid_count', 0)}/{report['ic_analysis'].get('total_count', 0)}")
    
    print(f"\n类别分布:")
    for category, count in report['category_distribution'].items():
        print(f"  {category}: {count}个")
    
    print(f"\n顶级因子 (按IC值):")
    for i, item in enumerate(report['top_factors'][:5], 1):
        print(f"  {i}. {item['factor']}: IC = {item['ic']:.4f}")


def example_7_integration_with_t01():
    """示例7: 与T01系统集成"""
    print("\n" + "=" * 70)
    print("示例7: 与T01系统集成")
    print("=" * 70)
    
    from factor_mining import create_factor_miner
    
    # 使用T01配置文件
    config_path = os.path.join(os.path.dirname(__file__), 'config.yaml')
    
    print(f"\n从T01配置文件创建因子挖掘器: {config_path}")
    
    try:
        miner = create_factor_miner(config_path)
        
        print(f"\n配置参数:")
        print(f"  相关性阈值: {miner.correlation_threshold}")
        print(f"  IC阈值: {miner.ic_threshold}")
        print(f"  最小周期: {miner.min_periods}")
        
        print(f"\n因子库:")
        library = miner.get_factor_library()
        print(f"  总因子数: {library['total_count']}")
        
        # 导出因子定义
        output_path = '/tmp/t01_factors.json'
        miner.export_factors_to_json(output_path)
        print(f"\n因子定义已导出到: {output_path}")
        
    except Exception as e:
        print(f"集成失败: {e}")


def main():
    """主函数 - 运行所有示例"""
    print("\n" + "=" * 70)
    print("T01深度因子挖掘模块 - 使用示例")
    print("=" * 70)
    
    examples = [
        ("基本使用", example_1_basic_usage),
        ("计算单只股票因子", example_2_calculate_factors),
        ("因子分析", example_3_factor_analysis),
        ("因子筛选", example_4_factor_selection),
        ("PCA正交化", example_5_pca_orthogonalization),
        ("生成报告", example_6_generate_report),
        ("T01集成", example_7_integration_with_t01),
    ]
    
    print("\n可用示例:")
    for i, (name, _) in enumerate(examples, 1):
        print(f"  {i}. {name}")
    
    # 运行所有示例
    for name, func in examples:
        try:
            func()
        except Exception as e:
            print(f"\n示例执行失败: {name}")
            print(f"错误: {e}")
    
    print("\n" + "=" * 70)
    print("所有示例执行完成!")
    print("=" * 70)


if __name__ == '__main__':
    main()
