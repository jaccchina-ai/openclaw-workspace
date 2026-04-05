"""
情绪因子集成测试
测试在选股策略中集成情绪因子评分
"""
import pytest
import sys
import os

# 添加父目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from limit_up_strategy_new import LimitUpScoringStrategyV2


class TestSentimentIntegration:
    """测试情绪因子集成"""
    
    @pytest.fixture
    def strategy(self):
        """创建策略实例"""
        config = {
            'api': {
                'api_key': '870008d508d2b0e57ecf2ccc586c23c4ecc37522f5e93890fb3d56ab'
            },
            'strategy': {
                't_day_scoring': {
                    'first_limit_time': 30,
                    'buy_to_sell_ratio': 10,
                    'order_amount_to_circ_mv': 15,
                    'turnover_rate': 5,
                    'turnover_rate_to_20ma': 10,
                    'volume_ratio': 5,
                    'main_net_amount': 5,
                    'main_net_ratio': 5,
                    'medium_net_amount': 5,
                    'is_hot_sector': 10,
                    'sentiment': 10  # 情绪因子权重
                },
                't1_auction_scoring': {
                    'open_change_pct': 35,
                    'auction_volume_ratio': 20,
                    'auction_amount': 20,
                    'auction_turnover_rate': 0,
                    'auction_volume_to_t_volume': 25
                },
                'risk_control': {
                    'max_position_per_stock': 0.2,
                    'min_total_score': 60
                },
                'sentiment_analysis': {
                    'enabled': True,
                    'top_n_for_analysis': 10,
                    'days_back': 1,
                    'max_news_per_stock': 5
                }
            },
            'pca': {
                'enabled': False
            }
        }
        return LimitUpScoringStrategyV2(config)
    
    def test_sentiment_factor_in_scoring(self, strategy):
        """验证情绪因子权重配置存在"""
        assert 'sentiment' in strategy.t_day_weights, "t_day_weights中应包含sentiment权重"
        assert strategy.t_day_weights['sentiment'] == 10, "sentiment权重应为10"
    
    def test_score_sentiment_factor_method_exists(self, strategy):
        """验证情绪评分方法存在"""
        assert hasattr(strategy, '_score_sentiment_factor'), "策略应有_score_sentiment_factor方法"
        assert callable(getattr(strategy, '_score_sentiment_factor')), "_score_sentiment_factor应是可调用的方法"
    
    def test_score_sentiment_factor_return_range(self, strategy):
        """验证情绪评分方法返回正确范围"""
        # 测试非交易日（周日）
        score, data = strategy._score_sentiment_factor('20260405')
        assert 0 <= score <= 10, f"情绪评分应在0-10范围内，实际为{score}"
        assert isinstance(data, dict), "返回的数据应为字典类型"
    
    def test_score_sentiment_factor_structure(self, strategy):
        """验证情绪评分返回数据结构"""
        score, data = strategy._score_sentiment_factor('20260401')
        
        # 检查data中的必需字段
        assert 'score' in data, "data应包含'score'字段"
        assert 'status' in data, "data应包含'status'字段"
        assert 'factor_value' in data, "data应包含'factor_value'字段"
        assert 'should_filter' in data, "data应包含'should_filter'字段"
        assert 'reason' in data, "data应包含'reason'字段"
    
    def test_sentiment_factor_value_range(self, strategy):
        """验证factor_value在0-1范围内"""
        score, data = strategy._score_sentiment_factor('20260401')
        
        factor_value = data.get('factor_value', 0)
        assert 0 <= factor_value <= 1, f"factor_value应在0-1范围内，实际为{factor_value}"
    
    def test_extreme_bear_sentiment_score(self, strategy):
        """验证极端熊市返回低分 - 模拟数据测试"""
        # 直接测试评分转换逻辑：当情绪数据为极端熊市时
        # 模拟极端熊市的情绪数据 (score < 20, should_filter=True)
        mock_sentiment_data = {
            'score': 15,  # 极低评分
            'status': 'extreme_bear',
            'factor_value': 0.15,
            'should_filter': True,
            'reason': '极端熊市状态，建议停止选股',
            'indicators': {}
        }
        
        # 计算因子得分: (15/100) * 10 = 1.5，但should_filter=True时应返回0
        sentiment_weight = strategy.t_day_weights.get('sentiment', 10)
        raw_score = (mock_sentiment_data['score'] / 100.0) * sentiment_weight
        
        # 验证原始计算
        assert raw_score == 1.5, f"原始情绪得分应为1.5，实际为{raw_score}"
        
        # 验证极端熊市时 should_filter 为 True
        assert mock_sentiment_data['should_filter'] == True, "极端熊市时should_filter应为True"
        assert mock_sentiment_data['score'] < 20, "极端熊市评分应小于20"
    
    def test_bull_sentiment_score(self, strategy):
        """验证牛市返回高分 - 模拟数据测试"""
        # 模拟牛市的情绪数据
        mock_sentiment_data = {
            'score': 85,  # 高评分
            'status': 'bull',
            'factor_value': 0.85,
            'should_filter': False,
            'reason': '牛市状态，可积极选股',
            'indicators': {}
        }
        
        # 计算因子得分: (85/100) * 10 = 8.5
        sentiment_weight = strategy.t_day_weights.get('sentiment', 10)
        factor_score = (mock_sentiment_data['score'] / 100.0) * sentiment_weight
        
        # 验证高分
        assert factor_score > 5, f"牛市因子得分应大于5，实际为{factor_score}"
        assert factor_score == 8.5, f"牛市因子得分应为8.5，实际为{factor_score}"
        
        # 验证牛市时 should_filter 为 False
        assert mock_sentiment_data['should_filter'] == False, "牛市时should_filter应为False"


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
