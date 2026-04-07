#!/usr/bin/env python3
"""
测试sentiment_monitor.py的API重试机制和缓存机制
TDD流程: 先写测试 -> 看失败 -> 实现 -> 看通过
"""

import unittest
import sys
import os
import time
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment_monitor import MarketSentimentMonitor, safe_api_call


class TestSafeApiCall(unittest.TestCase):
    """测试API重试机制"""
    
    def test_successful_call_no_retry(self):
        """测试成功调用不重试"""
        mock_func = Mock(return_value="success")
        
        result = safe_api_call(mock_func, "arg1", kwarg1="value1")
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 1)
        mock_func.assert_called_once_with("arg1", kwarg1="value1")
    
    def test_retry_on_failure_then_success(self):
        """测试失败后重试并最终成功"""
        mock_func = Mock(side_effect=[Exception("Error 1"), Exception("Error 2"), "success"])
        
        result = safe_api_call(mock_func, max_retries=3, retry_delay=0.1)
        
        self.assertEqual(result, "success")
        self.assertEqual(mock_func.call_count, 3)
    
    def test_retry_exhausted_raises_exception(self):
        """测试重试次数用尽后抛出异常"""
        mock_func = Mock(side_effect=Exception("Persistent error"))
        
        with self.assertRaises(Exception) as context:
            safe_api_call(mock_func, max_retries=3, retry_delay=0.1)
        
        self.assertEqual(mock_func.call_count, 3)
        self.assertIn("Persistent error", str(context.exception))
    
    def test_zero_retries(self):
        """测试不重试的情况"""
        mock_func = Mock(side_effect=Exception("Error"))
        
        with self.assertRaises(Exception):
            safe_api_call(mock_func, max_retries=0, retry_delay=0.1)
        
        self.assertEqual(mock_func.call_count, 1)


class TestCacheMechanism(unittest.TestCase):
    """测试缓存机制"""
    
    def setUp(self):
        """每个测试前创建新的监控器实例"""
        self.monitor = MarketSentimentMonitor(config={})
        self.monitor.pro = Mock()  # Mock Tushare API
    
    def test_cache_initially_empty(self):
        """测试缓存初始为空"""
        self.assertEqual(len(self.monitor._cache), 0)
    
    def test_get_cache_key(self):
        """测试缓存键生成"""
        key1 = self.monitor._get_cache_key("method1", ("arg1",), {"kwarg": "value"})
        key2 = self.monitor._get_cache_key("method1", ("arg1",), {"kwarg": "value"})
        key3 = self.monitor._get_cache_key("method1", ("arg2",), {"kwarg": "value"})
        
        # 相同参数应生成相同键
        self.assertEqual(key1, key2)
        # 不同参数应生成不同键
        self.assertNotEqual(key1, key3)
    
    def test_set_and_get_cached_result(self):
        """测试设置和获取缓存"""
        key = "test_key"
        data = {"test": "data", "value": 123}
        
        # 设置缓存
        self.monitor._set_cached_result(key, data)
        
        # 获取缓存
        cached = self.monitor._get_cached_result(key)
        
        self.assertEqual(cached, data)
    
    def test_cache_expiration(self):
        """测试缓存过期"""
        key = "test_key"
        data = {"test": "data"}
        
        # 设置缓存
        self.monitor._set_cached_result(key, data)
        
        # 立即获取应存在
        self.assertIsNotNone(self.monitor._get_cached_result(key))
        
        # 修改缓存时间为过期
        self.monitor._cache[key]['timestamp'] = time.time() - 301  # 超过5分钟
        
        # 过期后应返回None
        self.assertIsNone(self.monitor._get_cached_result(key))
    
    def test_cache_ttl_parameter(self):
        """测试自定义缓存TTL"""
        key = "test_key"
        data = {"test": "data"}
        
        # 设置TTL为1秒
        self.monitor._set_cached_result(key, data, ttl=1)
        
        # 立即获取应存在
        self.assertIsNotNone(self.monitor._get_cached_result(key))
        
        # 等待过期
        time.sleep(1.1)
        
        # 过期后应返回None
        self.assertIsNone(self.monitor._get_cached_result(key))


class TestAnalyzeSentimentWithCache(unittest.TestCase):
    """测试analyze_sentiment方法使用缓存"""
    
    def setUp(self):
        """设置测试环境"""
        self.config = {'api_key': 'test_token'}
        self.monitor = MarketSentimentMonitor(config=self.config)
        self.monitor.pro = Mock()
    
    @patch.object(MarketSentimentMonitor, '_is_trading_day')
    @patch.object(MarketSentimentMonitor, 'calculate_explosion_rate')
    @patch.object(MarketSentimentMonitor, 'calculate_consecutive_limits')
    @patch.object(MarketSentimentMonitor, 'calculate_advance_decline_ratio')
    @patch.object(MarketSentimentMonitor, 'calculate_limit_up_down_stats')
    @patch.object(MarketSentimentMonitor, 'calculate_yesterday_limit_up_premium')
    @patch.object(MarketSentimentMonitor, 'calculate_seal_rate')
    def test_analyze_uses_cache_on_second_call(
        self, mock_seal, mock_premium, mock_limit, mock_ad, mock_consecutive, mock_explosion, mock_is_trading
    ):
        """测试第二次调用使用缓存"""
        # 设置mock返回值
        mock_is_trading.return_value = True
        mock_explosion.return_value = {'rate': 0.3, 'total': 100, 'exploded': 30, 'sealed': 70}
        mock_consecutive.return_value = {'max_consecutive': 5, 'distribution': {1: 50, 2: 30}}
        mock_ad.return_value = {'ratio': 1.5, 'advance': 2000, 'decline': 1500, 'flat': 100}
        mock_limit.return_value = {'limit_up': 80, 'limit_down': 5, 'strong_up': 200, 'strong_down': 50}
        mock_premium.return_value = {'premium': 2.5, 'avg_open': 1.5, 'avg_close': 2.5, 'count': 50}
        mock_seal.return_value = {'rate': 0.7, 'sealed': 70, 'total': 100}
        
        # 第一次调用
        result1 = self.monitor.analyze_sentiment('20250101')
        
        # 验证计算函数被调用
        self.assertTrue(mock_explosion.called)
        
        # 重置mock
        mock_explosion.reset_mock()
        
        # 第二次调用（应使用缓存）
        result2 = self.monitor.analyze_sentiment('20250101')
        
        # 验证计算函数未被调用（使用了缓存）
        self.assertFalse(mock_explosion.called)
        
        # 结果应相同
        self.assertEqual(result1['sentiment_score'], result2['sentiment_score'])
    
    @patch.object(MarketSentimentMonitor, '_is_trading_day')
    def test_cache_graceful_failure(self, mock_is_trading):
        """测试缓存失败时优雅降级"""
        mock_is_trading.return_value = True
        
        # 模拟缓存损坏
        self.monitor._cache = None  # 破坏缓存
        
        # 使用mock来避免实际API调用 - 提供完整的mock数据
        with patch.object(self.monitor, 'calculate_explosion_rate', return_value={'rate': 0.3, 'total': 100, 'exploded': 30, 'sealed': 70}):
            with patch.object(self.monitor, 'calculate_consecutive_limits', return_value={'max_consecutive': 5, 'distribution': {1: 50, 2: 30}}):
                with patch.object(self.monitor, 'calculate_advance_decline_ratio', return_value={'ratio': 1.5, 'advance': 2000, 'decline': 1500, 'flat': 100}):
                    with patch.object(self.monitor, 'calculate_limit_up_down_stats', return_value={'limit_up': 80, 'limit_down': 5, 'strong_up': 200, 'strong_down': 50}):
                        with patch.object(self.monitor, 'calculate_yesterday_limit_up_premium', return_value={'premium': 2.5, 'avg_open': 1.5, 'avg_close': 2.5, 'count': 50}):
                            with patch.object(self.monitor, 'calculate_seal_rate', return_value={'rate': 0.7, 'sealed': 70, 'total': 100}):
                                # 即使缓存损坏，也应正常工作
                                result = self.monitor.analyze_sentiment('20250101')
                                self.assertIn('sentiment_score', result)


class TestIntegration(unittest.TestCase):
    """集成测试"""
    
    def test_safe_api_call_with_real_function(self):
        """测试safe_api_call包装真实函数"""
        call_count = [0]
        
        def real_function(fail_times=0):
            call_count[0] += 1
            if call_count[0] <= fail_times:
                raise Exception(f"Failure {call_count[0]}")
            return f"Success after {call_count[0]} attempts"
        
        # 测试失败2次后成功
        result = safe_api_call(real_function, fail_times=2, max_retries=3, retry_delay=0.1)
        self.assertEqual(result, "Success after 3 attempts")
        self.assertEqual(call_count[0], 3)
    
    def test_cache_isolation_between_instances(self):
        """测试不同实例间缓存隔离"""
        monitor1 = MarketSentimentMonitor(config={})
        monitor2 = MarketSentimentMonitor(config={})
        
        # 在monitor1中设置缓存
        monitor1._set_cached_result("key1", "data1")
        
        # monitor2不应有该缓存
        self.assertIsNone(monitor2._get_cached_result("key1"))
        self.assertEqual(monitor1._get_cached_result("key1"), "data1")


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
