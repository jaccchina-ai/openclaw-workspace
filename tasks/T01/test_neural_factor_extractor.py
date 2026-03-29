#!/usr/bin/env python3
"""
Neural Factor Extractor 测试模块
TDD方式实现 - 先写测试，再实现功能
"""

import unittest
import numpy as np
import pandas as pd
from datetime import datetime
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from neural_factor_extractor import NeuralFactorExtractor, ExtractedFactor


class TestExtractedFactor(unittest.TestCase):
    """测试ExtractedFactor数据类"""
    
    def test_factor_creation(self):
        """测试因子对象创建"""
        factor = ExtractedFactor(
            name="neural_factor_1",
            code="nf_1",
            values=np.array([0.1, 0.2, 0.3]),
            ic_value=0.05,
            is_valid=True,
            description="Test neural factor"
        )
        
        self.assertEqual(factor.name, "neural_factor_1")
        self.assertEqual(factor.code, "nf_1")
        self.assertEqual(len(factor.values), 3)
        self.assertEqual(factor.ic_value, 0.05)
        self.assertTrue(factor.is_valid)


class TestNeuralFactorExtractor(unittest.TestCase):
    """测试NeuralFactorExtractor类"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            'bottleneck_size': 8,
            'epochs': 10,
            'learning_rate': 0.001,
            'ic_threshold': 0.03,
            'batch_size': 32,
            'validation_split': 0.2
        }
        self.extractor = NeuralFactorExtractor(config=self.config)
        
        # 创建测试数据
        np.random.seed(42)
        n_samples = 100
        n_features = 20
        
        self.test_data = pd.DataFrame(
            np.random.randn(n_samples, n_features),
            columns=[f'factor_{i}' for i in range(n_features)]
        )
        self.test_data['ts_code'] = [f'00000{i%10}.SZ' for i in range(n_samples)]
        self.test_data['trade_date'] = '20240301'
        self.test_data['next_day_return'] = np.random.randn(n_samples) * 0.02
    
    def test_initialization(self):
        """测试初始化"""
        self.assertEqual(self.extractor.bottleneck_size, 8)
        self.assertEqual(self.extractor.epochs, 10)
        self.assertEqual(self.extractor.learning_rate, 0.001)
        self.assertEqual(self.extractor.ic_threshold, 0.03)
        self.assertIsNone(self.extractor.autoencoder)
        self.assertIsNone(self.extractor.scaler)
    
    def test_default_config(self):
        """测试默认配置"""
        extractor = NeuralFactorExtractor()
        self.assertEqual(extractor.bottleneck_size, 5)
        self.assertEqual(extractor.epochs, 50)
        self.assertEqual(extractor.learning_rate, 0.001)
        self.assertEqual(extractor.ic_threshold, 0.03)
    
    def test_data_preprocessing(self):
        """测试数据预处理"""
        # 添加一些缺失值
        data_with_na = self.test_data.copy()
        data_with_na.loc[0, 'factor_0'] = np.nan
        data_with_na.loc[1, 'factor_1'] = np.nan
        
        processed = self.extractor._preprocess_data(data_with_na)
        
        # 检查没有缺失值
        self.assertFalse(processed.isnull().any().any())
        
        # 检查数值范围（标准化后应该在合理范围内）
        numeric_cols = [c for c in processed.columns if c.startswith('factor_')]
        self.assertTrue(all(processed[col].dtype in [np.float64, np.float32] 
                           for col in numeric_cols))
    
    def test_feature_extraction_columns(self):
        """测试特征提取列识别"""
        feature_cols = self.extractor._get_feature_columns(self.test_data)
        
        # 应该识别出factor_开头的列
        self.assertEqual(len(feature_cols), 20)
        self.assertTrue(all(col.startswith('factor_') for col in feature_cols))
        
        # 不应该包含元数据列
        self.assertNotIn('ts_code', feature_cols)
        self.assertNotIn('trade_date', feature_cols)
        self.assertNotIn('next_day_return', feature_cols)
    
    def test_build_autoencoder(self):
        """测试自编码器构建"""
        n_features = 20
        self.extractor._build_autoencoder(n_features)
        
        self.assertIsNotNone(self.extractor.autoencoder)
        # MLPRegressor应该被创建
        from sklearn.neural_network import MLPRegressor
        self.assertIsInstance(self.extractor.autoencoder, MLPRegressor)
    
    def test_extract_bottleneck_features(self):
        """测试从瓶颈层提取特征"""
        # 准备数据
        X = np.random.randn(50, 20)
        
        # 构建和训练模型
        self.extractor._build_autoencoder(20)
        self.extractor.autoencoder.fit(X, X)
        
        # 提取特征
        features = self.extractor._extract_bottleneck_features(X)
        
        # 检查特征维度
        self.assertEqual(features.shape, (50, self.extractor.bottleneck_size))
    
    def test_calculate_ic(self):
        """测试IC值计算"""
        factor_values = pd.Series(np.random.randn(100))
        returns = pd.Series(np.random.randn(100))
        
        ic = self.extractor._calculate_ic(factor_values, returns)
        
        # IC值应该在-1到1之间
        self.assertGreaterEqual(ic, -1)
        self.assertLessEqual(ic, 1)
        
        # 测试完全相关的情况
        perfect_factor = pd.Series(np.arange(100))
        perfect_returns = pd.Series(np.arange(100))
        perfect_ic = self.extractor._calculate_ic(perfect_factor, perfect_returns, method='pearson')
        self.assertAlmostEqual(perfect_ic, 1.0, places=5)
    
    def test_filter_factors_by_ic(self):
        """测试按IC值筛选因子"""
        factors = [
            ExtractedFactor("f1", "f1", np.array([0.1]), 0.05, True),
            ExtractedFactor("f2", "f2", np.array([0.2]), 0.02, True),
            ExtractedFactor("f3", "f3", np.array([0.3]), 0.01, True),
            ExtractedFactor("f4", "f4", np.array([0.4]), -0.04, True),
        ]
        
        filtered = self.extractor._filter_factors_by_ic(factors, threshold=0.03)
        
        # 应该保留|IC| >= 0.03的因子
        self.assertEqual(len(filtered), 2)
        self.assertEqual(filtered[0].code, "f1")
        self.assertEqual(filtered[1].code, "f4")
    
    def test_create_sequences(self):
        """测试时间序列数据创建"""
        # 创建时间序列测试数据
        dates = pd.date_range('2024-01-01', periods=30, freq='D')
        ts_data = pd.DataFrame({
            'ts_code': ['000001.SZ'] * 30,
            'trade_date': dates.strftime('%Y%m%d'),
            'factor_0': np.random.randn(30),
            'factor_1': np.random.randn(30),
            'next_day_return': np.random.randn(30)
        })
        
        sequences = self.extractor._create_sequences(ts_data, sequence_length=5)
        
        # 应该创建 30 - 5 + 1 = 26 个序列
        self.assertEqual(len(sequences), 26)
        
        # 每个序列应该有5个时间步
        self.assertEqual(sequences[0].shape[0], 5)
    
    def test_cross_sectional_extraction(self):
        """测试横截面因子提取"""
        # 运行提取
        factors = self.extractor.extract_factors(
            self.test_data,
            extraction_mode='cross_sectional',
            target_col='next_day_return'
        )
        
        # 应该返回因子列表
        self.assertIsInstance(factors, list)
        
        # 应该提取至少3个因子
        self.assertGreaterEqual(len(factors), 3)
        
        # 每个因子应该有正确的属性
        for factor in factors:
            self.assertIsInstance(factor, ExtractedFactor)
            self.assertTrue(hasattr(factor, 'name'))
            self.assertTrue(hasattr(factor, 'code'))
            self.assertTrue(hasattr(factor, 'values'))
            self.assertTrue(hasattr(factor, 'ic_value'))
            self.assertTrue(hasattr(factor, 'is_valid'))
    
    def test_time_series_extraction(self):
        """测试时间序列因子提取"""
        # 创建时间序列数据
        dates = pd.date_range('2024-01-01', periods=50, freq='D')
        ts_data = pd.DataFrame({
            'ts_code': ['000001.SZ'] * 50,
            'trade_date': dates.strftime('%Y%m%d'),
        })
        
        for i in range(10):
            ts_data[f'factor_{i}'] = np.random.randn(50)
        ts_data['next_day_return'] = np.random.randn(50)
        
        # 运行提取
        factors = self.extractor.extract_factors(
            ts_data,
            extraction_mode='time_series',
            sequence_length=10,
            target_col='next_day_return'
        )
        
        # 应该返回因子列表
        self.assertIsInstance(factors, list)
    
    def test_invalid_mode(self):
        """测试无效的模式"""
        with self.assertRaises(ValueError):
            self.extractor.extract_factors(
                self.test_data,
                extraction_mode='invalid_mode'
            )
    
    def test_empty_data(self):
        """测试空数据处理"""
        empty_data = pd.DataFrame()
        
        factors = self.extractor.extract_factors(empty_data)
        
        # 应该返回空列表
        self.assertEqual(factors, [])
    
    def test_factor_ic_threshold(self):
        """测试因子IC阈值筛选"""
        # 使用较低的阈值
        extractor = NeuralFactorExtractor(config={'ic_threshold': 0.01})
        
        factors = extractor.extract_factors(
            self.test_data,
            extraction_mode='cross_sectional',
            target_col='next_day_return'
        )
        
        # 所有返回的因子应该满足IC阈值
        for factor in factors:
            self.assertGreaterEqual(abs(factor.ic_value), 0.01)
            self.assertTrue(factor.is_valid)
    
    def test_get_factor_dataframe(self):
        """测试获取因子DataFrame"""
        # 先提取因子
        factors = self.extractor.extract_factors(
            self.test_data,
            extraction_mode='cross_sectional',
            target_col='next_day_return'
        )
        
        # 获取DataFrame
        df = self.extractor.get_factor_dataframe(factors)
        
        # 检查DataFrame结构
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), len(self.test_data))
        
        # 应该有神经因子列 (codes start with 'nf_')
        neural_cols = [c for c in df.columns if c.startswith('nf_')]
        self.assertGreaterEqual(len(neural_cols), 3)
    
    def test_training_time(self):
        """测试训练时间是否在合理范围内"""
        import time
        
        start_time = time.time()
        
        factors = self.extractor.extract_factors(
            self.test_data,
            extraction_mode='cross_sectional',
            target_col='next_day_return'
        )
        
        elapsed_time = time.time() - start_time
        
        # 应该在5分钟内完成
        self.assertLess(elapsed_time, 300)
    
    def test_reproducibility(self):
        """测试结果可复现性"""
        # 设置随机种子
        extractor1 = NeuralFactorExtractor(config={**self.config, 'random_state': 42})
        extractor2 = NeuralFactorExtractor(config={**self.config, 'random_state': 42})
        
        factors1 = extractor1.extract_factors(
            self.test_data,
            extraction_mode='cross_sectional',
            target_col='next_day_return'
        )
        
        factors2 = extractor2.extract_factors(
            self.test_data,
            extraction_mode='cross_sectional',
            target_col='next_day_return'
        )
        
        # 两个提取器应该返回相同数量的因子
        self.assertEqual(len(factors1), len(factors2))


class TestIntegrationWithFactorMining(unittest.TestCase):
    """测试与factor_mining模块的集成"""
    
    def test_factor_object_compatibility(self):
        """测试ExtractedFactor与Factor类的兼容性"""
        try:
            from factor_mining import Factor, FactorCategory
            
            # 创建ExtractedFactor
            extracted = ExtractedFactor(
                name="neural_test",
                code="neural_test",
                values=np.array([0.1, 0.2]),
                ic_value=0.05,
                is_valid=True,
                description="Test factor"
            )
            
            # 应该可以转换为Factor对象
            factor = Factor(
                name=extracted.name,
                code=extracted.code,
                category=FactorCategory.CUSTOM,
                description=extracted.description or "Neural extracted factor",
                formula="Autoencoder bottleneck feature",
                ic_value=extracted.ic_value,
                is_valid=extracted.is_valid
            )
            
            self.assertEqual(factor.name, extracted.name)
            self.assertEqual(factor.ic_value, extracted.ic_value)
            
        except ImportError:
            self.skipTest("factor_mining模块不可用")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)