#!/usr/bin/env python3
"""
PCA集成端到端验证脚本

验证PCA因子正交化是否正确集成到T01评分系统。
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import yaml
import pandas as pd
import numpy as np
from unittest.mock import Mock, patch, MagicMock


def test_pca_disabled_flow():
    """测试PCA关闭时的流程"""
    print("\n" + "=" * 60)
    print("测试1: PCA关闭时的正常流程")
    print("=" * 60)
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 确保PCA关闭
    config['pca']['enabled'] = False
    
    with patch('tushare.pro_api') as mock_pro_api:
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro
        
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        strategy = LimitUpScoringStrategyV2(config)
        
        # 验证PCA配置
        assert strategy.pca_config['enabled'] == False, "PCA应被禁用"
        assert strategy.pca_enabled == False, "pca_enabled应为False"
        
        print("✓ PCA配置正确: 已禁用")
        print(f"✓ pca_config: {strategy.pca_config}")


def test_pca_enabled_flow():
    """测试PCA开启时的流程"""
    print("\n" + "=" * 60)
    print("测试2: PCA开启时的流程")
    print("=" * 60)
    
    # 加载配置
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 启用PCA
    config['pca']['enabled'] = True
    config['pca']['variance_threshold'] = 0.9
    config['pca']['standardize'] = True
    
    with patch('tushare.pro_api') as mock_pro_api:
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro
        
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        strategy = LimitUpScoringStrategyV2(config)
        
        # 验证PCA配置
        assert strategy.pca_config['enabled'] == True, "PCA应被启用"
        assert strategy.pca_enabled == True, "pca_enabled应为True"
        assert strategy.factor_transformer is not None, "factor_transformer应被初始化"
        
        print("✓ PCA配置正确: 已启用")
        print(f"✓ pca_config: {strategy.pca_config}")
        print(f"✓ factor_transformer: {strategy.factor_transformer}")


def test_apply_pca_transform():
    """测试_apply_pca_transform方法"""
    print("\n" + "=" * 60)
    print("测试3: _apply_pca_transform方法")
    print("=" * 60)
    
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    config['pca']['enabled'] = True
    
    with patch('tushare.pro_api') as mock_pro_api:
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro
        
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        strategy = LimitUpScoringStrategyV2(config)
        
        # 测试有效数据
        factor_data = pd.DataFrame({
            'factor1': [10, 20, 30, 40, 50],
            'factor2': [5, 15, 25, 35, 45],
            'factor3': [2, 8, 14, 20, 26]
        }, index=['000001.SZ', '000002.SZ', '600000.SH', '600001.SH', '000003.SZ'])
        
        result = strategy._apply_pca_transform(factor_data)
        
        assert 'scores' in result, "结果应包含scores"
        assert 'pca_info' in result, "结果应包含pca_info"
        assert len(result['scores']) == 5, "应有5个评分"
        
        pca_info = result['pca_info']
        assert 'n_components' in pca_info, "pca_info应包含n_components"
        assert 'explained_variance_ratio' in pca_info, "pca_info应包含explained_variance_ratio"
        
        print("✓ PCA转换成功")
        print(f"✓ 原始因子数: {pca_info['n_original_features']}")
        print(f"✓ 主成分数: {pca_info['n_components']}")
        print(f"✓ 保留方差: {pca_info['total_explained_variance']:.1%}")
        print(f"✓ 评分范围: [{result['scores'].min():.2f}, {result['scores'].max():.2f}]")


def test_empty_data_handling():
    """测试空数据处理"""
    print("\n" + "=" * 60)
    print("测试4: 空数据处理")
    print("=" * 60)
    
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    config['pca']['enabled'] = True
    
    with patch('tushare.pro_api') as mock_pro_api:
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro
        
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        strategy = LimitUpScoringStrategyV2(config)
        
        # 测试空数据
        empty_df = pd.DataFrame()
        result = strategy._apply_pca_transform(empty_df)
        
        assert 'scores' in result, "结果应包含scores"
        assert 'pca_info' in result, "结果应包含pca_info"
        assert 'error' in result['pca_info'], "应记录错误信息"
        
        print("✓ 空数据处理正确")
        print(f"✓ 错误信息: {result['pca_info']['error']}")


def test_single_stock_handling():
    """测试单只股票处理"""
    print("\n" + "=" * 60)
    print("测试5: 单只股票处理")
    print("=" * 60)
    
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    config['pca']['enabled'] = True
    
    with patch('tushare.pro_api') as mock_pro_api:
        mock_pro = MagicMock()
        mock_pro_api.return_value = mock_pro
        
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        strategy = LimitUpScoringStrategyV2(config)
        
        # 测试单只股票
        single_stock = pd.DataFrame({
            'factor1': [10.0],
            'factor2': [20.0],
            'factor3': [30.0]
        }, index=['000001.SZ'])
        
        result = strategy._apply_pca_transform(single_stock)
        
        assert 'scores' in result, "结果应包含scores"
        assert 'pca_info' in result, "结果应包含pca_info"
        assert len(result['scores']) == 1, "应有1个评分"
        
        print("✓ 单只股票处理正确")
        print(f"✓ 评分: {result['scores'].iloc[0]:.2f}")


def test_config_yaml_consistency():
    """测试config.yaml配置一致性"""
    print("\n" + "=" * 60)
    print("测试6: config.yaml配置一致性")
    print("=" * 60)
    
    with open('config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 验证PCA配置节存在
    assert 'pca' in config, "配置文件中缺少pca配置节"
    
    pca_config = config['pca']
    
    # 验证必要字段
    assert 'enabled' in pca_config, "PCA配置缺少enabled字段"
    assert 'variance_threshold' in pca_config, "PCA配置缺少variance_threshold字段"
    assert 'standardize' in pca_config, "PCA配置缺少standardize字段"
    
    # 验证默认值
    assert pca_config['enabled'] == False, "PCA默认应为关闭"
    assert pca_config['variance_threshold'] == 0.9, "方差阈值默认应为0.9"
    assert pca_config['standardize'] == True, "标准化默认应为True"
    
    print("✓ config.yaml配置正确")
    print(f"✓ enabled: {pca_config['enabled']}")
    print(f"✓ variance_threshold: {pca_config['variance_threshold']}")
    print(f"✓ standardize: {pca_config['standardize']}")


def main():
    """运行所有验证测试"""
    print("\n" + "=" * 60)
    print("PCA集成端到端验证")
    print("=" * 60)
    
    try:
        test_pca_disabled_flow()
        test_pca_enabled_flow()
        test_apply_pca_transform()
        test_empty_data_handling()
        test_single_stock_handling()
        test_config_yaml_consistency()
        
        print("\n" + "=" * 60)
        print("✓ 所有验证测试通过!")
        print("=" * 60)
        return 0
        
    except AssertionError as e:
        print(f"\n✗ 验证失败: {e}")
        return 1
    except Exception as e:
        print(f"\n✗ 验证异常: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
