#!/usr/bin/env python3
"""
测试报告格式化功能 - 情绪指标整合到选股报告
TDD流程: 先写测试 → 看失败 → 实现功能 → 看通过
"""

import unittest
import sys
import os
from datetime import datetime
from pathlib import Path

# 添加父目录到Python路径
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

# 模拟数据用于测试
class MockSentimentData:
    """模拟情绪数据"""
    
    @staticmethod
    def get_extreme_bear_data():
        """极端熊市场景"""
        return {
            'score': 15,
            'status': 'extreme_bear',
            'factor_value': 0.15,
            'should_filter': True,
            'reason': '情绪评分极低(15)，建议停止选股',
            'indicators': {
                'explosion_rate': {'rate': 0.75, 'total': 20, 'exploded': 15, 'sealed': 5},
                'consecutive_limits': {'max_consecutive': 2, 'distribution': {1: 15, 2: 5}},
                'advance_decline_ratio': {'ratio': 0.25, 'advance': 500, 'decline': 2000, 'flat': 100},
                'limit_stats': {'limit_up': 20, 'limit_down': 80, 'strong_up': 100, 'strong_down': 500},
                'yesterday_premium': {'premium': -3.5, 'avg_open': -2.0, 'avg_close': -3.5, 'count': 30},
                'seal_rate': {'rate': 0.25, 'sealed': 5, 'total': 20}
            }
        }
    
    @staticmethod
    def get_bull_data():
        """普通牛市场景"""
        return {
            'score': 75,
            'status': 'bull',
            'factor_value': 0.75,
            'should_filter': False,
            'reason': '牛市状态(75分)，可积极选股',
            'indicators': {
                'explosion_rate': {'rate': 0.20, 'total': 100, 'exploded': 20, 'sealed': 80},
                'consecutive_limits': {'max_consecutive': 7, 'distribution': {1: 50, 2: 30, 3: 15, 4: 5}},
                'advance_decline_ratio': {'ratio': 2.5, 'advance': 2500, 'decline': 1000, 'flat': 100},
                'limit_stats': {'limit_up': 100, 'limit_down': 5, 'strong_up': 800, 'strong_down': 50},
                'yesterday_premium': {'premium': 4.5, 'avg_open': 3.0, 'avg_close': 4.5, 'count': 80},
                'seal_rate': {'rate': 0.80, 'sealed': 80, 'total': 100}
            }
        }
    
    @staticmethod
    def get_neutral_data():
        """中性市场场景"""
        return {
            'score': 50,
            'status': 'neutral',
            'factor_value': 0.50,
            'should_filter': False,
            'reason': '中性状态(50分)，正常选股',
            'indicators': {
                'explosion_rate': {'rate': 0.35, 'total': 60, 'exploded': 21, 'sealed': 39},
                'consecutive_limits': {'max_consecutive': 4, 'distribution': {1: 30, 2: 20, 3: 8, 4: 2}},
                'advance_decline_ratio': {'ratio': 1.2, 'advance': 1500, 'decline': 1250, 'flat': 100},
                'limit_stats': {'limit_up': 60, 'limit_down': 15, 'strong_up': 300, 'strong_down': 150},
                'yesterday_premium': {'premium': 1.5, 'avg_open': 0.8, 'avg_close': 1.5, 'count': 50},
                'seal_rate': {'rate': 0.65, 'sealed': 39, 'total': 60}
            }
        }


class TestReportFormatWithSentiment(unittest.TestCase):
    """测试带情绪指标的报告格式化"""
    
    def setUp(self):
        """测试前准备"""
        # 模拟策略配置
        self.config = {
            'api': {'api_key': 'test_token'},
            'strategy': {
                'output': {'final_recommendation_count': 3},
                'risk_control': {'max_position_per_stock': 0.2}
            }
        }
        
        # 模拟候选股票数据
        self.mock_candidates = [
            {
                'ts_code': '000001.SZ',
                'name': '平安银行',
                'total_score': 85.5,
                'basic_score': 80.0,
                'sentiment_score': 5.5,
                'industry': '银行',
                'pct_chg': 10.02,
                'seal_ratio': 0.35,
                'turnover_rate': 5.2
            },
            {
                'ts_code': '000002.SZ', 
                'name': '万科A',
                'total_score': 78.3,
                'basic_score': 75.0,
                'sentiment_score': 3.3,
                'industry': '房地产',
                'pct_chg': 9.98,
                'seal_ratio': 0.28,
                'turnover_rate': 4.8
            }
        ]
        
        # 模拟T+1推荐数据
        self.mock_t1_results = [
            {
                'ts_code': '000001.SZ',
                'name': '平安银行',
                't_day_score': 85.5,
                'auction_score': 82.0,
                'final_score': 84.5,
                'recommendation': {
                    'action': '买入',
                    'position': 0.2,
                    'confidence': '高',
                    'reasons': ['竞价高开(3-5%)', '竞价量比放大(2-3)', '竞价成交量强(15-20%，热度延续)']
                },
                'auction_data': {
                    'open_change_pct': 3.5,
                    'auction_volume_ratio': 2.5,
                    'auction_volume_to_t_volume': 0.18
                }
            }
        ]
    
    def test_format_report_with_sentiment_exists(self):
        """测试 format_report_with_sentiment 方法是否存在"""
        try:
            from limit_up_strategy_new import LimitUpScoringStrategyV2
            strategy = LimitUpScoringStrategyV2(self.config)
            self.assertTrue(hasattr(strategy, 'format_report_with_sentiment'),
                          "LimitUpScoringStrategyV2 应该有 format_report_with_sentiment 方法")
        except ImportError as e:
            self.fail(f"导入 LimitUpScoringStrategyV2 失败: {e}")
        except Exception as e:
            self.fail(f"测试失败: {e}")
    
    def test_extreme_bear_report_format(self):
        """测试极端熊市场景报告格式"""
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        strategy = LimitUpScoringStrategyV2(self.config)
        sentiment_data = MockSentimentData.get_extreme_bear_data()
        
        # 生成报告
        report = strategy.format_report_with_sentiment(
            candidates=self.mock_candidates,
            t1_results=self.mock_t1_results,
            sentiment_data=sentiment_data,
            trade_date='20250407'
        )
        
        # 验证报告结构
        self.assertIsInstance(report, str)
        self.assertIn('情绪指标', report)
        self.assertIn('情绪评分', report)
        self.assertIn('15/100', report)  # 极端熊市评分
        self.assertIn('extreme_bear', report)  # 市场状态
        self.assertIn('炸板率', report)
        self.assertIn('连板高度', report)
        self.assertIn('涨跌比', report)
        self.assertIn('涨停家数', report)
        self.assertIn('跌停家数', report)
        
        # 极端熊市应该有警告信息
        self.assertIn('警告', report)
        self.assertIn('停止选股', report)
        
        print("\n=== 极端熊市报告 ===")
        print(report)
    
    def test_bull_market_report_format(self):
        """测试普通牛市场景报告格式"""
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        strategy = LimitUpScoringStrategyV2(self.config)
        sentiment_data = MockSentimentData.get_bull_data()
        
        # 生成报告
        report = strategy.format_report_with_sentiment(
            candidates=self.mock_candidates,
            t1_results=self.mock_t1_results,
            sentiment_data=sentiment_data,
            trade_date='20250407'
        )
        
        # 验证报告结构
        self.assertIsInstance(report, str)
        self.assertIn('情绪评分', report)
        self.assertIn('75/100', report)  # 牛市评分
        self.assertIn('bull', report)  # 市场状态
        
        # 牛市不应该有停止选股警告
        self.assertNotIn('停止选股', report)
        
        print("\n=== 牛市报告 ===")
        print(report)
    
    def test_sentiment_data_structure(self):
        """测试情绪数据结构完整性"""
        sentiment_data = MockSentimentData.get_bull_data()
        
        # 验证必要字段
        required_fields = ['score', 'status', 'factor_value', 'should_filter', 'reason', 'indicators']
        for field in required_fields:
            self.assertIn(field, sentiment_data, f"情绪数据应包含 {field} 字段")
        
        # 验证指标字段
        indicators = sentiment_data['indicators']
        required_indicators = ['explosion_rate', 'consecutive_limits', 'advance_decline_ratio', 
                               'limit_stats', 'yesterday_premium', 'seal_rate']
        for indicator in required_indicators:
            self.assertIn(indicator, indicators, f"情绪指标应包含 {indicator}")
    
    def test_report_contains_all_sentiment_indicators(self):
        """测试报告包含所有情绪指标"""
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        strategy = LimitUpScoringStrategyV2(self.config)
        sentiment_data = MockSentimentData.get_neutral_data()
        
        report = strategy.format_report_with_sentiment(
            candidates=self.mock_candidates,
            t1_results=self.mock_t1_results,
            sentiment_data=sentiment_data,
            trade_date='20250407'
        )
        
        # 验证所有指标都在报告中
        self.assertIn('炸板率', report)
        self.assertIn('连板高度', report)
        self.assertIn('涨跌比', report)
        self.assertIn('涨停家数', report)
        self.assertIn('跌停家数', report)
        self.assertIn('封板率', report)
        self.assertIn('操作建议', report)
    
    def test_filter_warning_display(self):
        """测试过滤警告显示逻辑"""
        from limit_up_strategy_new import LimitUpScoringStrategyV2
        
        strategy = LimitUpScoringStrategyV2(self.config)
        
        # 测试 should_filter=True 时显示警告
        bear_data = MockSentimentData.get_extreme_bear_data()
        report_bear = strategy.format_report_with_sentiment(
            candidates=self.mock_candidates,
            t1_results=self.mock_t1_results,
            sentiment_data=bear_data,
            trade_date='20250407'
        )
        self.assertIn('⚠️', report_bear)  # 应该有警告符号
        
        # 测试 should_filter=False 时不显示警告
        bull_data = MockSentimentData.get_bull_data()
        report_bull = strategy.format_report_with_sentiment(
            candidates=self.mock_candidates,
            t1_results=self.mock_t1_results,
            sentiment_data=bull_data,
            trade_date='20250407'
        )
        # 牛市报告不应该有极端警告
        self.assertNotIn('⚠️ 警告', report_bull)


class TestSentimentIntegration(unittest.TestCase):
    """测试情绪指标与选股报告的集成"""
    
    def test_sentiment_factor_score_range(self):
        """测试情绪因子得分范围"""
        # 情绪评分应该在0-100之间
        bear_data = MockSentimentData.get_extreme_bear_data()
        self.assertGreaterEqual(bear_data['score'], 0)
        self.assertLessEqual(bear_data['score'], 100)
        
        bull_data = MockSentimentData.get_bull_data()
        self.assertGreaterEqual(bull_data['score'], 0)
        self.assertLessEqual(bull_data['score'], 100)
    
    def test_market_status_values(self):
        """测试市场状态值"""
        valid_statuses = ['extreme_bear', 'bear', 'caution', 'neutral', 'bull']
        
        bear_data = MockSentimentData.get_extreme_bear_data()
        self.assertIn(bear_data['status'], valid_statuses)
        
        bull_data = MockSentimentData.get_bull_data()
        self.assertIn(bull_data['status'], valid_statuses)


if __name__ == '__main__':
    # 运行测试
    unittest.main(verbosity=2)
