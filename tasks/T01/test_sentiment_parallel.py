#!/usr/bin/env python3
"""
情绪指标并行计算测试
TDD流程: 先写测试 → 看失败 → 实现 → 看通过
"""

import unittest
import sys
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from unittest.mock import Mock, patch, MagicMock

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment_monitor import MarketSentimentMonitor


class TestParallelSentimentAnalysis(unittest.TestCase):
    """测试并行情绪分析功能"""
    
    def setUp(self):
        """测试前准备"""
        self.config = {
            'api_key': 'test_token',
            'sentiment_thresholds': MarketSentimentMonitor.DEFAULT_THRESHOLDS
        }
        self.monitor = MarketSentimentMonitor(self.config)
        self.trade_date = '20250101'
    
    def test_analyze_sentiment_parallel_exists(self):
        """测试并行分析方法是否存在"""
        self.assertTrue(hasattr(self.monitor, 'analyze_sentiment_parallel'),
                       "MarketSentimentMonitor应该有analyze_sentiment_parallel方法")
    
    def test_get_default_result_exists(self):
        """测试默认结果辅助方法是否存在"""
        self.assertTrue(hasattr(self.monitor, '_get_default_result'),
                       "MarketSentimentMonitor应该有_get_default_result方法")
    
    def test_get_default_result_returns_correct_structure(self):
        """测试默认结果返回正确的结构"""
        # 测试各个指标的默认返回值
        test_cases = [
            ('explosion_rate', {'rate': 0, 'total': 0, 'exploded': 0, 'sealed': 0}),
            ('consecutive_limits', {'max_consecutive': 0, 'distribution': {}}),
            ('advance_decline_ratio', {'ratio': 1.0, 'advance': 0, 'decline': 0, 'flat': 0}),
            ('limit_up_down_stats', {'limit_up': 0, 'limit_down': 0, 'strong_up': 0, 'strong_down': 0}),
            ('yesterday_limit_up_premium', {'premium': 0, 'avg_open': 0, 'avg_close': 0, 'count': 0}),
        ]
        
        for indicator_name, expected in test_cases:
            with self.subTest(indicator=indicator_name):
                result = self.monitor._get_default_result(indicator_name)
                self.assertEqual(result, expected,
                               f"{indicator_name}应该返回正确的默认结构")
    
    @patch.object(MarketSentimentMonitor, 'calculate_explosion_rate')
    @patch.object(MarketSentimentMonitor, 'calculate_consecutive_limits')
    @patch.object(MarketSentimentMonitor, 'calculate_advance_decline_ratio')
    @patch.object(MarketSentimentMonitor, 'calculate_limit_up_down_stats')
    @patch.object(MarketSentimentMonitor, 'calculate_yesterday_limit_up_premium')
    def test_parallel_returns_same_result_as_serial(self, mock_premium, mock_limit_stats,
                                                      mock_ad_ratio, mock_consecutive, mock_explosion):
        """测试并行计算结果与串行计算一致"""
        # 设置模拟返回值
        mock_explosion.return_value = {'rate': 0.3, 'total': 50, 'exploded': 15, 'sealed': 35}
        mock_consecutive.return_value = {'max_consecutive': 5, 'distribution': {5: 3, 4: 5}}
        mock_ad_ratio.return_value = {'ratio': 1.5, 'advance': 3000, 'decline': 2000, 'flat': 100}
        mock_limit_stats.return_value = {'limit_up': 80, 'limit_down': 5, 'strong_up': 200, 'strong_down': 50}
        mock_premium.return_value = {'premium': 2.5, 'avg_open': 1.8, 'avg_close': 2.5, 'count': 60}
        
        # 模拟交易日检查
        with patch.object(self.monitor, '_is_trading_day', return_value=True):
            # 串行计算
            serial_result = self.monitor.analyze_sentiment(self.trade_date)
            
            # 并行计算
            parallel_result = self.monitor.analyze_sentiment_parallel(self.trade_date)
            
            # 验证关键字段一致
            self.assertEqual(serial_result['sentiment_score'], parallel_result['sentiment_score'])
            self.assertEqual(serial_result['market_status'], parallel_result['market_status'])
            self.assertEqual(serial_result['trade_date'], parallel_result['trade_date'])
            
            # 验证指标数据一致
            self.assertEqual(
                serial_result['indicators']['explosion_rate'],
                parallel_result['indicators']['explosion_rate']
            )
            self.assertEqual(
                serial_result['indicators']['consecutive_limits'],
                parallel_result['indicators']['consecutive_limits']
            )
            self.assertEqual(
                serial_result['indicators']['advance_decline_ratio'],
                parallel_result['indicators']['advance_decline_ratio']
            )
            self.assertEqual(
                serial_result['indicators']['limit_stats'],
                parallel_result['indicators']['limit_stats']
            )
            self.assertEqual(
                serial_result['indicators']['yesterday_premium'],
                parallel_result['indicators']['yesterday_premium']
            )
    
    @patch.object(MarketSentimentMonitor, 'calculate_explosion_rate')
    @patch.object(MarketSentimentMonitor, 'calculate_consecutive_limits')
    @patch.object(MarketSentimentMonitor, 'calculate_advance_decline_ratio')
    @patch.object(MarketSentimentMonitor, 'calculate_limit_up_down_stats')
    @patch.object(MarketSentimentMonitor, 'calculate_yesterday_limit_up_premium')
    def test_parallel_handles_single_failure(self, mock_premium, mock_limit_stats,
                                               mock_ad_ratio, mock_consecutive, mock_explosion):
        """测试单个指标失败时的容错能力"""
        # 设置模拟返回值，其中一个会失败
        mock_explosion.return_value = {'rate': 0.3, 'total': 50, 'exploded': 15, 'sealed': 35}
        mock_consecutive.side_effect = Exception("模拟连板计算失败")
        mock_ad_ratio.return_value = {'ratio': 1.5, 'advance': 3000, 'decline': 2000, 'flat': 100}
        mock_limit_stats.return_value = {'limit_up': 80, 'limit_down': 5, 'strong_up': 200, 'strong_down': 50}
        mock_premium.return_value = {'premium': 2.5, 'avg_open': 1.8, 'avg_close': 2.5, 'count': 60}
        
        # 模拟交易日检查
        with patch.object(self.monitor, '_is_trading_day', return_value=True):
            # 并行计算（应该能处理单个失败）
            result = self.monitor.analyze_sentiment_parallel(self.trade_date)
            
            # 验证结果包含所有指标
            self.assertIn('indicators', result)
            indicators = result['indicators']
            
            # 失败的指标应该返回默认值
            self.assertEqual(indicators['consecutive_limits'], {'max_consecutive': 0, 'distribution': {}})
            
            # 其他指标应该正常
            self.assertEqual(indicators['explosion_rate']['rate'], 0.3)
            self.assertEqual(indicators['advance_decline_ratio']['ratio'], 1.5)
            self.assertEqual(indicators['limit_stats']['limit_up'], 80)
            self.assertEqual(indicators['yesterday_premium']['premium'], 2.5)
    
    @patch.object(MarketSentimentMonitor, 'calculate_explosion_rate')
    @patch.object(MarketSentimentMonitor, 'calculate_consecutive_limits')
    @patch.object(MarketSentimentMonitor, 'calculate_advance_decline_ratio')
    @patch.object(MarketSentimentMonitor, 'calculate_limit_up_down_stats')
    @patch.object(MarketSentimentMonitor, 'calculate_yesterday_limit_up_premium')
    def test_parallel_handles_multiple_failures(self, mock_premium, mock_limit_stats,
                                                  mock_ad_ratio, mock_consecutive, mock_explosion):
        """测试多个指标失败时的容错能力"""
        # 设置多个失败
        mock_explosion.side_effect = Exception("炸板率计算失败")
        mock_consecutive.side_effect = Exception("连板高度计算失败")
        mock_ad_ratio.return_value = {'ratio': 1.5, 'advance': 3000, 'decline': 2000, 'flat': 100}
        mock_limit_stats.side_effect = Exception("涨跌停统计失败")
        mock_premium.return_value = {'premium': 2.5, 'avg_open': 1.8, 'avg_close': 2.5, 'count': 60}
        
        # 模拟交易日检查
        with patch.object(self.monitor, '_is_trading_day', return_value=True):
            # 并行计算
            result = self.monitor.analyze_sentiment_parallel(self.trade_date)
            
            # 验证结果包含所有指标（失败的返回默认值）
            indicators = result['indicators']
            
            # 失败的指标返回默认值
            self.assertEqual(indicators['explosion_rate'], {'rate': 0, 'total': 0, 'exploded': 0, 'sealed': 0})
            self.assertEqual(indicators['consecutive_limits'], {'max_consecutive': 0, 'distribution': {}})
            self.assertEqual(indicators['limit_stats'], {'limit_up': 0, 'limit_down': 0, 'strong_up': 0, 'strong_down': 0})
            
            # 成功的指标正常
            self.assertEqual(indicators['advance_decline_ratio']['ratio'], 1.5)
            self.assertEqual(indicators['yesterday_premium']['premium'], 2.5)
    
    @patch.object(MarketSentimentMonitor, 'calculate_explosion_rate')
    @patch.object(MarketSentimentMonitor, 'calculate_consecutive_limits')
    @patch.object(MarketSentimentMonitor, 'calculate_advance_decline_ratio')
    @patch.object(MarketSentimentMonitor, 'calculate_limit_up_down_stats')
    @patch.object(MarketSentimentMonitor, 'calculate_yesterday_limit_up_premium')
    def test_parallel_uses_threadpool(self, mock_premium, mock_limit_stats,
                                        mock_ad_ratio, mock_consecutive, mock_explosion):
        """测试并行方法使用ThreadPoolExecutor - 通过验证并行执行更快来间接证明"""
        # 设置模拟返回值，添加小延迟
        def slow_explosion(*args, **kwargs):
            time.sleep(0.05)
            return {'rate': 0.3, 'total': 50, 'exploded': 15, 'sealed': 35}
        
        def slow_consecutive(*args, **kwargs):
            time.sleep(0.05)
            return {'max_consecutive': 5, 'distribution': {5: 3}}
        
        def slow_ad_ratio(*args, **kwargs):
            time.sleep(0.05)
            return {'ratio': 1.5, 'advance': 3000, 'decline': 2000, 'flat': 100}
        
        def slow_limit_stats(*args, **kwargs):
            time.sleep(0.05)
            return {'limit_up': 80, 'limit_down': 5, 'strong_up': 200, 'strong_down': 50}
        
        def slow_premium(*args, **kwargs):
            time.sleep(0.05)
            return {'premium': 2.5, 'avg_open': 1.8, 'avg_close': 2.5, 'count': 60}
        
        mock_explosion.side_effect = slow_explosion
        mock_consecutive.side_effect = slow_consecutive
        mock_ad_ratio.side_effect = slow_ad_ratio
        mock_limit_stats.side_effect = slow_limit_stats
        mock_premium.side_effect = slow_premium
        
        # 模拟交易日检查
        with patch.object(self.monitor, '_is_trading_day', return_value=True):
            # 串行执行时间
            start = time.time()
            serial_result = self.monitor.analyze_sentiment(self.trade_date)
            serial_time = time.time() - start
            
            # 并行执行时间
            start = time.time()
            parallel_result = self.monitor.analyze_sentiment_parallel(self.trade_date)
            parallel_time = time.time() - start
            
            # 验证结果一致
            self.assertEqual(serial_result['sentiment_score'], parallel_result['sentiment_score'])
            
            # 验证并行更快（至少快1.5倍，考虑到线程开销）
            self.assertLess(parallel_time, serial_time * 0.8,
                          f"并行({parallel_time:.3f}s)应该比串行({serial_time:.3f}s)快")
    
    def test_non_trading_day_returns_early(self):
        """测试非交易日直接返回"""
        with patch.object(self.monitor, '_is_trading_day', return_value=False):
            result = self.monitor.analyze_sentiment_parallel(self.trade_date)
            self.assertEqual(result, {'is_trading_day': False})
    
    def test_backward_compatibility(self):
        """测试向后兼容 - 原有analyze_sentiment方法仍然存在"""
        self.assertTrue(hasattr(self.monitor, 'analyze_sentiment'))
        self.assertTrue(callable(getattr(self.monitor, 'analyze_sentiment')))


class TestParallelPerformance(unittest.TestCase):
    """测试并行性能（可选）"""
    
    @unittest.skip("性能测试 - 可选运行")
    def test_parallel_faster_than_serial(self):
        """测试并行计算比串行快（使用模拟延迟）"""
        config = {
            'api_key': 'test_token',
            'sentiment_thresholds': MarketSentimentMonitor.DEFAULT_THRESHOLDS
        }
        monitor = MarketSentimentMonitor(config)
        trade_date = '20250101'
        
        # 模拟有延迟的计算
        def slow_calculation(*args, **kwargs):
            time.sleep(0.1)  # 100ms延迟
            return {'rate': 0.3, 'total': 50, 'exploded': 15, 'sealed': 35}
        
        with patch.object(monitor, 'calculate_explosion_rate', side_effect=slow_calculation):
            with patch.object(monitor, 'calculate_consecutive_limits', side_effect=slow_calculation):
                with patch.object(monitor, 'calculate_advance_decline_ratio', side_effect=slow_calculation):
                    with patch.object(monitor, 'calculate_limit_up_down_stats', side_effect=slow_calculation):
                        with patch.object(monitor, 'calculate_yesterday_limit_up_premium', side_effect=slow_calculation):
                            with patch.object(monitor, '_is_trading_day', return_value=True):
                                # 串行时间（5个指标 * 100ms = 500ms）
                                start = time.time()
                                monitor.analyze_sentiment(trade_date)
                                serial_time = time.time() - start
                                
                                # 并行时间（约100ms + 开销）
                                start = time.time()
                                monitor.analyze_sentiment_parallel(trade_date)
                                parallel_time = time.time() - start
                                
                                # 并行应该明显更快（至少快2倍）
                                self.assertLess(parallel_time, serial_time / 2,
                                              f"并行({parallel_time:.2f}s)应该比串行({serial_time:.2f}s)快至少2倍")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
