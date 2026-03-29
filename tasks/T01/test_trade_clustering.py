#!/usr/bin/env python3
"""
Trade Clustering模块单元测试
测试覆盖率目标: 100%

测试内容:
1. 特征提取 (Feature Extraction)
2. 聚类算法 (K-means, DBSCAN, Hierarchical)
3. 聚类分析 (Cluster Analysis)
4. 模式识别 (Pattern Recognition)
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from trade_clustering import (
    TradeClustering, ClusterAlgorithm,
    TradeFeatures, ClusterAnalysis
)


class TestClusterAlgorithm(unittest.TestCase):
    """测试聚类算法枚举"""
    
    def test_enum_values(self):
        """测试枚举值正确性"""
        self.assertEqual(ClusterAlgorithm.KMEANS.value, "kmeans")
        self.assertEqual(ClusterAlgorithm.DBSCAN.value, "dbscan")
        self.assertEqual(ClusterAlgorithm.HIERARCHICAL.value, "hierarchical")


class TestTradeFeatures(unittest.TestCase):
    """测试交易特征数据类"""
    
    def test_trade_features_creation(self):
        """测试交易特征创建"""
        features = TradeFeatures(
            trade_id="trade_001",
            return_pct=5.5,
            seal_ratio=0.15,
            turnover_rate=0.08,
            market_regime="bull",
            sector="technology",
            duration_days=2,
            win_loss=1
        )
        
        self.assertEqual(features.trade_id, "trade_001")
        self.assertEqual(features.return_pct, 5.5)
        self.assertEqual(features.seal_ratio, 0.15)
        self.assertEqual(features.turnover_rate, 0.08)
        self.assertEqual(features.market_regime, "bull")
        self.assertEqual(features.sector, "technology")
        self.assertEqual(features.duration_days, 2)
        self.assertEqual(features.win_loss, 1)


class TestTradeClusteringInitialization(unittest.TestCase):
    """测试TradeClustering初始化"""
    
    def test_init_with_config(self):
        """测试带配置的初始化"""
        config = {
            'n_clusters': 5,
            'algorithm': 'kmeans',
            'random_state': 42,
            'handle_missing': 'mean'
        }
        
        clustering = TradeClustering(config)
        
        self.assertEqual(clustering.n_clusters, 5)
        self.assertEqual(clustering.algorithm, ClusterAlgorithm.KMEANS)
        self.assertEqual(clustering.random_state, 42)
        self.assertEqual(clustering.handle_missing, 'mean')
    
    def test_init_default_config(self):
        """测试默认配置初始化"""
        clustering = TradeClustering()
        
        self.assertEqual(clustering.n_clusters, 3)
        self.assertEqual(clustering.algorithm, ClusterAlgorithm.KMEANS)
        self.assertEqual(clustering.random_state, 42)
        self.assertEqual(clustering.handle_missing, 'mean')
    
    def test_init_invalid_algorithm(self):
        """测试无效算法处理"""
        config = {'algorithm': 'invalid'}
        clustering = TradeClustering(config)
        
        # 应该回退到默认的KMEANS
        self.assertEqual(clustering.algorithm, ClusterAlgorithm.KMEANS)


class TestFeatureExtraction(unittest.TestCase):
    """测试特征提取功能"""
    
    def setUp(self):
        """设置测试数据"""
        self.clustering = TradeClustering({})
        
        # 创建模拟交易数据
        self.trade_data = pd.DataFrame({
            'trade_id': ['trade_001', 'trade_002', 'trade_003', 'trade_004', 'trade_005'],
            'ts_code': ['000001.SZ', '000002.SZ', '000003.SZ', '000004.SZ', '000005.SZ'],
            'buy_price': [10.0, 20.0, 15.0, 25.0, 30.0],
            'sell_price': [10.5, 19.0, 16.5, 26.0, 28.5],
            'buy_date': ['20240101', '20240102', '20240103', '20240104', '20240105'],
            'sell_date': ['20240103', '20240104', '20240105', '20240106', '20240107'],
            'seal_ratio': [0.15, 0.08, 0.20, 0.12, 0.05],
            'turnover_rate': [0.08, 0.12, 0.06, 0.10, 0.15],
            'market_regime': ['bull', 'bear', 'bull', 'sideways', 'bull'],
            'sector': ['technology', 'finance', 'technology', 'healthcare', 'finance'],
            'win_loss': [1, 0, 1, 1, 0]
        })
    
    def test_extract_trade_return(self):
        """测试交易收益率提取"""
        features = self.clustering.extract_features(self.trade_data)
        
        # 检查收益率计算: (sell - buy) / buy * 100
        expected_return_0 = (10.5 - 10.0) / 10.0 * 100  # 5.0%
        self.assertAlmostEqual(features.iloc[0]['return_pct'], expected_return_0, places=2)
    
    def test_extract_trade_duration(self):
        """测试交易持续时间提取"""
        features = self.clustering.extract_features(self.trade_data)
        
        # 检查持仓天数
        self.assertEqual(features.iloc[0]['duration_days'], 2)
        self.assertEqual(features.iloc[1]['duration_days'], 2)
    
    def test_extract_factor_values(self):
        """测试因子值提取"""
        features = self.clustering.extract_features(self.trade_data)
        
        # 检查因子值是否正确传递
        pd.testing.assert_series_equal(
            features['seal_ratio'],
            self.trade_data['seal_ratio']
        )
        pd.testing.assert_series_equal(
            features['turnover_rate'],
            self.trade_data['turnover_rate']
        )
    
    def test_extract_market_regime(self):
        """测试市场状态提取"""
        features = self.clustering.extract_features(self.trade_data)
        
        # 检查市场状态编码
        self.assertIn('market_regime_encoded', features.columns)
        # 检查是否有不同的编码值
        self.assertGreater(len(features['market_regime_encoded'].unique()), 1)
    
    def test_extract_sector(self):
        """测试板块分类提取"""
        features = self.clustering.extract_features(self.trade_data)
        
        # 检查板块编码
        self.assertIn('sector_encoded', features.columns)
        # 检查是否有不同的编码值
        self.assertGreater(len(features['sector_encoded'].unique()), 1)
    
    def test_extract_features_with_missing_data(self):
        """测试缺失数据处理"""
        # 创建包含缺失值的数据
        trade_data_with_na = self.trade_data.copy()
        trade_data_with_na.loc[0, 'seal_ratio'] = np.nan
        trade_data_with_na.loc[1, 'turnover_rate'] = np.nan
        
        features = self.clustering.extract_features(trade_data_with_na)
        
        # 检查缺失值是否被处理
        self.assertFalse(features['seal_ratio'].isna().any())
        self.assertFalse(features['turnover_rate'].isna().any())
    
    def test_extract_features_empty_data(self):
        """测试空数据处理"""
        empty_data = pd.DataFrame()
        features = self.clustering.extract_features(empty_data)
        
        self.assertTrue(features.empty)


class TestClusteringAlgorithms(unittest.TestCase):
    """测试聚类算法"""
    
    def setUp(self):
        """设置测试数据"""
        self.clustering = TradeClustering({'n_clusters': 3})
        
        # 创建特征数据
        np.random.seed(42)
        n_samples = 99  # 确保能被3整除
        
        # 创建3个明显的簇
        cluster_0 = np.random.multivariate_normal([0, 0], [[0.1, 0], [0, 0.1]], n_samples//3)
        cluster_1 = np.random.multivariate_normal([5, 5], [[0.1, 0], [0, 0.1]], n_samples//3)
        cluster_2 = np.random.multivariate_normal([10, 0], [[0.1, 0], [0, 0.1]], n_samples//3)
        
        X = np.vstack([cluster_0, cluster_1, cluster_2])
        
        self.features_df = pd.DataFrame(X, columns=['feature_1', 'feature_2'])
        self.features_df['trade_id'] = [f'trade_{i:03d}' for i in range(n_samples)]
        self.features_df['win_loss'] = np.random.choice([0, 1], n_samples)
        self.features_df['return_pct'] = np.random.randn(n_samples) * 5
    
    def test_kmeans_clustering(self):
        """测试K-means聚类"""
        self.clustering.algorithm = ClusterAlgorithm.KMEANS
        result = self.clustering.fit_predict(self.features_df)
        
        # 检查返回结果
        self.assertIn('cluster_labels', result)
        self.assertIn('silhouette_score', result)
        self.assertIn('cluster_centers', result)
        
        # 检查标签数量
        self.assertEqual(len(result['cluster_labels']), len(self.features_df))
        
        # 检查轮廓分数范围
        self.assertGreaterEqual(result['silhouette_score'], -1)
        self.assertLessEqual(result['silhouette_score'], 1)
    
    def test_dbscan_clustering(self):
        """测试DBSCAN聚类"""
        clustering = TradeClustering({'algorithm': 'dbscan', 'eps': 0.5, 'min_samples': 5})
        result = clustering.fit_predict(self.features_df)
        
        # 检查返回结果
        self.assertIn('cluster_labels', result)
        self.assertIn('silhouette_score', result)
        
        # DBSCAN可能有噪声点（标签为-1）
        unique_labels = set(result['cluster_labels'])
        self.assertTrue(len(unique_labels) >= 1)
    
    def test_hierarchical_clustering(self):
        """测试层次聚类"""
        clustering = TradeClustering({'algorithm': 'hierarchical', 'n_clusters': 3})
        result = clustering.fit_predict(self.features_df)
        
        # 检查返回结果
        self.assertIn('cluster_labels', result)
        self.assertIn('silhouette_score', result)
        
        # 检查标签数量
        self.assertEqual(len(result['cluster_labels']), len(self.features_df))
    
    def test_clustering_with_missing_values(self):
        """测试带缺失值的聚类"""
        # 添加一些缺失值
        features_with_na = self.features_df.copy()
        features_with_na.loc[0, 'feature_1'] = np.nan
        features_with_na.loc[1, 'feature_2'] = np.nan
        
        result = self.clustering.fit_predict(features_with_na)
        
        # 应该成功执行，缺失值被处理
        self.assertIn('cluster_labels', result)
        self.assertEqual(len(result['cluster_labels']), len(features_with_na))


class TestClusterAnalysis(unittest.TestCase):
    """测试聚类分析功能"""
    
    def setUp(self):
        """设置测试数据"""
        self.clustering = TradeClustering({'n_clusters': 3})
        
        # 创建带聚类标签的数据
        np.random.seed(42)
        n_samples = 60
        
        self.clustered_data = pd.DataFrame({
            'trade_id': [f'trade_{i:03d}' for i in range(n_samples)],
            'cluster_label': [0] * 20 + [1] * 20 + [2] * 20,
            'return_pct': np.concatenate([
                np.random.normal(5, 2, 20),   # Cluster 0: 高回报
                np.random.normal(-3, 2, 20),  # Cluster 1: 低回报
                np.random.normal(1, 1, 20)    # Cluster 2: 中等回报
            ]),
            'win_loss': np.concatenate([
                np.random.choice([0, 1], 20, p=[0.3, 0.7]),  # Cluster 0: 高胜率
                np.random.choice([0, 1], 20, p=[0.7, 0.3]),  # Cluster 1: 低胜率
                np.random.choice([0, 1], 20, p=[0.5, 0.5])   # Cluster 2: 中等胜率
            ]),
            'seal_ratio': np.random.uniform(0.05, 0.25, n_samples),
            'turnover_rate': np.random.uniform(0.05, 0.15, n_samples),
            'market_regime': np.random.choice(['bull', 'bear', 'sideways'], n_samples),
            'sector': np.random.choice(['tech', 'finance', 'healthcare'], n_samples),
            'duration_days': np.random.randint(1, 5, n_samples)
        })
    
    def test_analyze_clusters(self):
        """测试聚类分析"""
        analysis = self.clustering.analyze_clusters(self.clustered_data)
        
        # 检查返回结果
        self.assertIn('cluster_stats', analysis)
        self.assertIn('winning_patterns', analysis)
        self.assertIn('losing_patterns', analysis)
        self.assertIn('overall_quality', analysis)
        
        # 检查聚类统计
        self.assertEqual(len(analysis['cluster_stats']), 3)
    
    def test_cluster_win_rate_calculation(self):
        """测试聚类胜率计算"""
        analysis = self.clustering.analyze_clusters(self.clustered_data)
        
        # 检查每个聚类的胜率
        for cluster_id, stats in analysis['cluster_stats'].items():
            self.assertIn('win_rate', stats)
            self.assertIn('avg_return', stats)
            self.assertIn('trade_count', stats)
            
            # 胜率应该在0-100之间
            self.assertGreaterEqual(stats['win_rate'], 0)
            self.assertLessEqual(stats['win_rate'], 100)
    
    def test_cluster_factor_distributions(self):
        """测试聚类因子分布分析"""
        analysis = self.clustering.analyze_clusters(self.clustered_data)
        
        # 检查因子分布
        for cluster_id, stats in analysis['cluster_stats'].items():
            self.assertIn('factor_distributions', stats)
            
            # 检查关键因子的统计量
            if 'seal_ratio' in stats['factor_distributions']:
                dist = stats['factor_distributions']['seal_ratio']
                self.assertIn('mean', dist)
                self.assertIn('std', dist)
    
    def test_identify_winning_patterns(self):
        """测试识别盈利模式"""
        analysis = self.clustering.analyze_clusters(self.clustered_data)
        
        # 检查盈利模式
        self.assertIn('winning_patterns', analysis)
        
        # 应该有识别的盈利聚类
        self.assertGreater(len(analysis['winning_patterns']), 0)
    
    def test_identify_losing_patterns(self):
        """测试识别亏损模式"""
        analysis = self.clustering.analyze_clusters(self.clustered_data)
        
        # 检查亏损模式
        self.assertIn('losing_patterns', analysis)
        
        # 应该有识别的亏损聚类
        self.assertGreater(len(analysis['losing_patterns']), 0)
    
    def test_cluster_quality_metrics(self):
        """测试聚类质量指标"""
        analysis = self.clustering.analyze_clusters(self.clustered_data)
        
        # 检查整体质量
        self.assertIn('overall_quality', analysis)
        quality = analysis['overall_quality']
        
        self.assertIn('separation_score', quality)
        self.assertIn('stability_score', quality)
        self.assertIn('actionability_score', quality)


class TestPatternRecognition(unittest.TestCase):
    """测试模式识别功能"""
    
    def setUp(self):
        """设置测试数据"""
        self.clustering = TradeClustering({})
        
        # 创建模拟的聚类分析结果
        self.analysis_result = {
            'cluster_stats': {
                0: {
                    'win_rate': 75.0,
                    'avg_return': 8.5,
                    'trade_count': 20,
                    'factor_distributions': {
                        'seal_ratio': {'mean': 0.18, 'std': 0.03},
                        'turnover_rate': {'mean': 0.08, 'std': 0.02}
                    },
                    'dominant_regime': 'bull',
                    'dominant_sector': 'tech'
                },
                1: {
                    'win_rate': 25.0,
                    'avg_return': -5.2,
                    'trade_count': 20,
                    'factor_distributions': {
                        'seal_ratio': {'mean': 0.06, 'std': 0.02},
                        'turnover_rate': {'mean': 0.15, 'std': 0.03}
                    },
                    'dominant_regime': 'bear',
                    'dominant_sector': 'finance'
                }
            },
            'winning_patterns': [0],
            'losing_patterns': [1],
            'overall_quality': {
                'separation_score': 0.8,
                'stability_score': 0.75,
                'actionability_score': 0.85
            }
        }
    
    def test_get_trading_recommendations(self):
        """测试获取交易建议"""
        recommendations = self.clustering.get_trading_recommendations(self.analysis_result)
        
        # 检查返回结果
        self.assertIn('favorable_conditions', recommendations)
        self.assertIn('avoid_conditions', recommendations)
        self.assertIn('optimal_parameters', recommendations)
    
    def test_favorable_conditions(self):
        """测试有利条件识别"""
        recommendations = self.clustering.get_trading_recommendations(self.analysis_result)
        
        # 有利条件应该基于盈利聚类的特征
        favorable = recommendations['favorable_conditions']
        self.assertIsInstance(favorable, list)
        
        # 应该包含关于seal_ratio的建议
        has_seal_ratio = any('seal_ratio' in str(cond).lower() for cond in favorable)
        self.assertTrue(has_seal_ratio)
    
    def test_avoid_conditions(self):
        """测试避免条件识别"""
        recommendations = self.clustering.get_trading_recommendations(self.analysis_result)
        
        # 避免条件应该基于亏损聚类的特征
        avoid = recommendations['avoid_conditions']
        self.assertIsInstance(avoid, list)
        
        # 应该包含关于低seal_ratio的建议
        has_low_seal = any('seal_ratio' in str(cond).lower() for cond in avoid)
        self.assertTrue(has_low_seal)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def setUp(self):
        """设置测试数据"""
        self.clustering = TradeClustering({'n_clusters': 3})
        
        # 创建完整的交易数据
        np.random.seed(42)
        n_samples = 60
        
        self.full_trade_data = pd.DataFrame({
            'trade_id': [f'trade_{i:03d}' for i in range(n_samples)],
            'ts_code': [f'{600000+i:06d}.SZ' for i in range(n_samples)],
            'buy_price': np.random.uniform(10, 50, n_samples),
            'sell_price': np.random.uniform(10, 55, n_samples),
            'buy_date': ['20240101'] * n_samples,
            'sell_date': ['20240103'] * n_samples,
            'seal_ratio': np.concatenate([
                np.random.uniform(0.15, 0.25, 20),
                np.random.uniform(0.05, 0.10, 20),
                np.random.uniform(0.10, 0.15, 20)
            ]),
            'turnover_rate': np.concatenate([
                np.random.uniform(0.05, 0.10, 20),
                np.random.uniform(0.12, 0.18, 20),
                np.random.uniform(0.08, 0.12, 20)
            ]),
            'market_regime': np.random.choice(['bull', 'bear', 'sideways'], n_samples),
            'sector': np.random.choice(['tech', 'finance', 'healthcare', 'energy'], n_samples),
            'win_loss': np.concatenate([
                np.random.choice([0, 1], 20, p=[0.2, 0.8]),
                np.random.choice([0, 1], 20, p=[0.8, 0.2]),
                np.random.choice([0, 1], 20, p=[0.5, 0.5])
            ])
        })
        
        # 计算sell_price使其与win_loss一致
        for i in range(n_samples):
            if self.full_trade_data.loc[i, 'win_loss'] == 1:
                # 盈利交易
                self.full_trade_data.loc[i, 'sell_price'] = self.full_trade_data.loc[i, 'buy_price'] * 1.05
            else:
                # 亏损交易
                self.full_trade_data.loc[i, 'sell_price'] = self.full_trade_data.loc[i, 'buy_price'] * 0.97
    
    def test_full_pipeline(self):
        """测试完整流程"""
        # 1. 特征提取
        features = self.clustering.extract_features(self.full_trade_data)
        self.assertFalse(features.empty)
        
        # 2. 聚类
        cluster_result = self.clustering.fit_predict(features)
        self.assertIn('cluster_labels', cluster_result)
        
        # 3. 添加聚类标签到数据
        features['cluster_label'] = cluster_result['cluster_labels']
        
        # 4. 聚类分析
        analysis = self.clustering.analyze_clusters(features)
        self.assertIn('cluster_stats', analysis)
        
        # 5. 获取交易建议
        recommendations = self.clustering.get_trading_recommendations(analysis)
        self.assertIn('favorable_conditions', recommendations)
    
    def test_end_to_end_with_different_algorithms(self):
        """测试不同算法的端到端流程"""
        algorithms = ['kmeans', 'dbscan', 'hierarchical']
        
        for algo in algorithms:
            with self.subTest(algorithm=algo):
                clustering = TradeClustering({'algorithm': algo, 'n_clusters': 3})
                
                # 特征提取
                features = clustering.extract_features(self.full_trade_data)
                
                # 聚类
                result = clustering.fit_predict(features)
                
                # 验证结果
                self.assertIn('cluster_labels', result)
                self.assertEqual(len(result['cluster_labels']), len(features))


class TestEdgeCases(unittest.TestCase):
    """测试边界情况"""
    
    def setUp(self):
        """设置测试环境"""
        self.clustering = TradeClustering({})
    
    def test_single_trade(self):
        """测试单条交易数据"""
        single_trade = pd.DataFrame({
            'trade_id': ['trade_001'],
            'buy_price': [10.0],
            'sell_price': [10.5],
            'buy_date': ['20240101'],
            'sell_date': ['20240103'],
            'seal_ratio': [0.15],
            'turnover_rate': [0.08],
            'market_regime': ['bull'],
            'sector': ['tech'],
            'win_loss': [1]
        })
        
        features = self.clustering.extract_features(single_trade)
        self.assertEqual(len(features), 1)
    
    def test_all_same_cluster(self):
        """测试所有数据在同一聚类"""
        same_cluster_data = pd.DataFrame({
            'trade_id': [f'trade_{i:03d}' for i in range(10)],
            'cluster_label': [0] * 10,
            'return_pct': [5.0] * 10,
            'win_loss': [1] * 10,
            'seal_ratio': [0.15] * 10,
            'turnover_rate': [0.08] * 10
        })
        
        analysis = self.clustering.analyze_clusters(same_cluster_data)
        self.assertEqual(len(analysis['cluster_stats']), 1)
    
    def test_missing_all_features(self):
        """测试所有特征都缺失"""
        # 需要至少3个样本才能进行K-means聚类(n_clusters=3)
        empty_features = pd.DataFrame({
            'trade_id': ['trade_001', 'trade_002', 'trade_003'],
            'return_pct': [np.nan, np.nan, np.nan],
            'seal_ratio': [np.nan, np.nan, np.nan]
        })
        
        # 应该处理缺失值而不崩溃
        result = self.clustering.fit_predict(empty_features)
        # 对于全缺失数据，可能无法聚类，但至少不崩溃
        self.assertIsInstance(result, dict)


class TestUtilityMethods(unittest.TestCase):
    """测试工具方法"""
    
    def setUp(self):
        """设置测试环境"""
        self.clustering = TradeClustering({})
    
    def test_get_cluster_summary(self):
        """测试获取聚类摘要"""
        # 创建带聚类标签的数据
        data = pd.DataFrame({
            'trade_id': [f'trade_{i:03d}' for i in range(30)],
            'cluster_label': [0] * 10 + [1] * 10 + [2] * 10,
            'return_pct': np.random.randn(30) * 5,
            'win_loss': np.random.choice([0, 1], 30)
        })
        
        summary = self.clustering.get_cluster_summary(data)
        
        self.assertIn('total_clusters', summary)
        self.assertIn('total_trades', summary)
        self.assertIn('cluster_distribution', summary)
        
        self.assertEqual(summary['total_clusters'], 3)
        self.assertEqual(summary['total_trades'], 30)
    
    def test_export_results(self):
        """测试导出结果"""
        import tempfile
        import json
        
        result = {
            'cluster_labels': [0, 1, 0, 2, 1],
            'silhouette_score': 0.65,
            'cluster_centers': [[1.0, 2.0], [3.0, 4.0], [5.0, 6.0]]
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            self.clustering.export_results(result, temp_path)
            
            # 验证文件内容
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            self.assertEqual(loaded['cluster_labels'], result['cluster_labels'])
            self.assertEqual(loaded['silhouette_score'], result['silhouette_score'])
        finally:
            os.unlink(temp_path)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
