"""
趋势跟踪型策略实现

基于移动平均线和动量指标的趋势跟踪策略。
识别趋势向上的强势股票，进行跟踪买入。

核心逻辑：
1. 使用MA5、MA10、MA20判断趋势方向
2. 短期均线上穿长期均线视为上升趋势
3. 计算趋势强度和动量得分
4. 考虑成交量确认趋势有效性
5. 结合大盘趋势进行过滤
"""

from typing import Dict, Any, List, Optional
from datetime import datetime

import numpy as np

from strategy_base import Strategy, StrategyConfig, StrategyMetadata, StrategyType


class TrendFollowingStrategy(Strategy):
    """
    趋势跟踪型策略
    
    通过移动平均线识别上升趋势，跟踪强势股票。
    适用于牛市和震荡向上的市场环境。
    
    Attributes:
        _config: 策略配置
        _metadata: 策略元数据
    
    配置参数:
        ma_short: 短期均线周期（默认5）
        ma_medium: 中期均线周期（默认10）
        ma_long: 长期均线周期（默认20）
        momentum_threshold: 动量阈值（默认0.05，即5%）
        volume_threshold: 成交量倍数（默认1.0，即大于20日均量）
        trend_strength_threshold: 趋势强度阈值（默认0.3）
    """
    
    # 默认配置参数
    DEFAULT_PARAMS = {
        'ma_short': 5,
        'ma_medium': 10,
        'ma_long': 20,
        'momentum_threshold': 0.05,
        'volume_threshold': 1.0,
        'trend_strength_threshold': 0.3
    }
    
    def __init__(self):
        """初始化趋势跟踪策略"""
        super().__init__()
        
        # 设置默认配置
        self._config = StrategyConfig(
            name="TrendFollowingStrategy",
            params=self.DEFAULT_PARAMS.copy(),
            enabled=True,
            description="趋势跟踪型策略默认配置"
        )
        
        # 设置元数据
        self._metadata = StrategyMetadata(
            name="TrendFollowingStrategy",
            description="基于移动平均线的趋势跟踪策略，识别上升趋势中的强势股票",
            version="1.0.0",
            author="T01 System",
            strategy_type=StrategyType.TREND_FOLLOWING,
            tags=["trend", "momentum", "moving_average"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def get_name(self) -> str:
        """
        获取策略名称
        
        Returns:
            str: "TrendFollowingStrategy"
        """
        return "TrendFollowingStrategy"
    
    def get_description(self) -> str:
        """
        获取策略描述
        
        Returns:
            str: 策略详细描述
        """
        return (
            "趋势跟踪型策略：基于移动平均线(MA5/MA10/MA20)识别上升趋势，"
            "通过多头排列、动量指标和成交量确认，选出强势股票进行跟踪。"
            "适用于牛市和震荡向上的市场环境。"
        )
    
    def validate(self) -> bool:
        """
        验证策略配置
        
        检查项：
        1. 均线周期必须为正整数
        2. 短期 < 中期 < 长期均线周期
        3. 阈值参数必须在合理范围内
        
        Returns:
            bool: 配置是否有效
        """
        params = self._config.params
        
        # 检查均线周期
        ma_short = params.get('ma_short', self.DEFAULT_PARAMS['ma_short'])
        ma_medium = params.get('ma_medium', self.DEFAULT_PARAMS['ma_medium'])
        ma_long = params.get('ma_long', self.DEFAULT_PARAMS['ma_long'])
        
        # 必须是正整数
        if not (isinstance(ma_short, int) and ma_short > 0):
            return False
        if not (isinstance(ma_medium, int) and ma_medium > 0):
            return False
        if not (isinstance(ma_long, int) and ma_long > 0):
            return False
        
        # 必须满足短期 < 中期 < 长期
        if not (ma_short < ma_medium < ma_long):
            return False
        
        # 检查动量阈值
        momentum_threshold = params.get('momentum_threshold', self.DEFAULT_PARAMS['momentum_threshold'])
        if not isinstance(momentum_threshold, (int, float)):
            return False
        if momentum_threshold < 0 or momentum_threshold > 1:
            return False
        
        # 检查成交量阈值
        volume_threshold = params.get('volume_threshold', self.DEFAULT_PARAMS['volume_threshold'])
        if not isinstance(volume_threshold, (int, float)):
            return False
        if volume_threshold <= 0:
            return False
        
        # 检查趋势强度阈值
        trend_strength_threshold = params.get('trend_strength_threshold', self.DEFAULT_PARAMS['trend_strength_threshold'])
        if not isinstance(trend_strength_threshold, (int, float)):
            return False
        if trend_strength_threshold < 0 or trend_strength_threshold > 1:
            return False
        
        return True
    
    def select(self, stock_data: Dict[str, Any], market_data: Dict[str, Any]) -> List[str]:
        """
        选股逻辑
        
        根据趋势跟踪规则筛选符合条件的股票：
        1. 股价 > MA20（中期趋势向上）
        2. MA5 > MA10 > MA20（多头排列）
        3. 成交量 > 20日均量 * volume_threshold（放量确认）
        4. 动量指标 > momentum_threshold
        5. 大盘趋势不过于悲观（可选过滤）
        
        Args:
            stock_data: 股票数据字典
                格式: {
                    "股票代码": {
                        "prices": [历史价格列表],
                        "volumes": [历史成交量列表],
                        "close": 最新收盘价,
                        "name": 股票名称
                    }
                }
            market_data: 市场数据字典
                格式: {
                    "index": {
                        "close": 收盘指数,
                        "change_pct": 涨跌幅,
                        "prices": [历史指数列表]
                    }
                }
        
        Returns:
            List[str]: 符合条件的股票代码列表
        """
        selected = []
        
        # 获取配置参数
        params = self._config.params
        ma_short = params.get('ma_short', self.DEFAULT_PARAMS['ma_short'])
        ma_medium = params.get('ma_medium', self.DEFAULT_PARAMS['ma_medium'])
        ma_long = params.get('ma_long', self.DEFAULT_PARAMS['ma_long'])
        momentum_threshold = params.get('momentum_threshold', self.DEFAULT_PARAMS['momentum_threshold'])
        volume_threshold = params.get('volume_threshold', self.DEFAULT_PARAMS['volume_threshold'])
        
        # 检查大盘趋势（如果数据可用）
        market_bearish = False
        if market_data and 'index' in market_data:
            index_data = market_data['index']
            if 'prices' in index_data and len(index_data['prices']) >= ma_long:
                market_trend = self._identify_trend(index_data['prices'], [1000000] * len(index_data['prices']))
                # 如果大盘处于强烈下跌趋势，减少选股
                if market_trend['trend_strength'] < -0.5:
                    market_bearish = True
        
        for stock_code, data in stock_data.items():
            # 检查必要字段
            if not self._has_required_fields(data):
                continue
            
            prices = data.get('prices', [])
            volumes = data.get('volumes', [])
            close = data.get('close', 0)
            
            # 数据长度检查
            if len(prices) < ma_long or len(volumes) < ma_long:
                continue
            
            # 计算移动平均线
            ma_s = self._calculate_ma(prices, ma_short)
            ma_m = self._calculate_ma(prices, ma_medium)
            ma_l = self._calculate_ma(prices, ma_long)
            
            if ma_s is None or ma_m is None or ma_l is None:
                continue
            
            # 条件1: 股价 > MA20
            if close <= ma_l:
                continue
            
            # 条件2: MA5 > MA10 > MA20（多头排列）
            if not (ma_s > ma_m > ma_l):
                continue
            
            # 条件3: 成交量 > 20日均量 * threshold
            avg_volume = np.mean(volumes[-ma_long:])
            current_volume = volumes[-1] if volumes else 0
            if avg_volume > 0 and current_volume < avg_volume * volume_threshold:
                continue
            
            # 条件4: 动量 > 阈值
            momentum = self._calculate_momentum(prices)
            if momentum < momentum_threshold:
                continue
            
            # 条件5: 趋势强度检查
            trend_info = self._identify_trend(prices, volumes)
            if not trend_info['is_uptrend']:
                continue
            
            # 熊市中更严格
            if market_bearish and trend_info['trend_strength'] < 0.5:
                continue
            
            selected.append(stock_code)
        
        return selected
    
    def score(self, stock_data: Dict[str, Any]) -> Dict[str, float]:
        """
        评分逻辑
        
        对每只股票进行综合评分（0-100）：
        - 趋势强度（40%权重）
        - 动量得分（30%权重）
        - 成交量配合（20%权重）
        - 大盘相关性（10%权重）
        
        Args:
            stock_data: 股票数据字典
        
        Returns:
            Dict[str, float]: 股票评分字典 {股票代码: 分数}
        """
        scores = {}
        
        for stock_code, data in stock_data.items():
            # 检查必要字段
            if not self._has_required_fields(data):
                scores[stock_code] = 0
                continue
            
            prices = data.get('prices', [])
            volumes = data.get('volumes', [])
            
            if len(prices) < 5 or len(volumes) < 5:
                scores[stock_code] = 0
                continue
            
            # 计算各项得分
            trend_score = self._calculate_trend_score(prices, volumes)
            momentum_score = self._calculate_momentum_score(prices)
            volume_score = self._calculate_volume_score(volumes)
            correlation_score = 50  # 默认中等相关性
            
            # 综合评分（加权平均）
            total_score = (
                trend_score * 0.4 +
                momentum_score * 0.3 +
                volume_score * 0.2 +
                correlation_score * 0.1
            )
            
            # 确保在0-100范围内
            scores[stock_code] = max(0, min(100, total_score))
        
        return scores
    
    @staticmethod
    def _has_required_fields(data: Dict[str, Any]) -> bool:
        """
        检查数据是否包含必要字段
        
        Args:
            data: 股票数据字典
        
        Returns:
            bool: 是否包含必要字段
        """
        required_fields = ['prices', 'volumes', 'close']
        return all(field in data for field in required_fields)
    
    @staticmethod
    def _calculate_ma(prices: List[float], period: int) -> Optional[float]:
        """
        计算移动平均线
        
        Args:
            prices: 价格列表
            period: 均线周期
        
        Returns:
            Optional[float]: 移动平均值，数据不足时返回None
        """
        if len(prices) < period:
            return None
        
        return float(np.mean(prices[-period:]))
    
    @staticmethod
    def _calculate_momentum(prices: List[float], period: int = 5) -> float:
        """
        计算动量指标（价格变化率）
        
        Args:
            prices: 价格列表
            period: 计算周期（默认5天）
        
        Returns:
            float: 动量值（价格变化百分比）
        """
        if len(prices) < period:
            return 0.0
        
        current = prices[-1]
        previous = prices[-period]
        
        if previous == 0:
            return 0.0
        
        return (current - previous) / previous
    
    def _identify_trend(self, prices: List[float], volumes: List[float]) -> Dict[str, Any]:
        """
        识别趋势方向和强度
        
        Args:
            prices: 价格列表
            volumes: 成交量列表
        
        Returns:
            Dict[str, Any]: 趋势信息字典
                - is_uptrend: 是否上升趋势
                - trend_strength: 趋势强度（-1到1）
                - ma_bullish_alignment: 是否多头排列
                - slope: 价格斜率
        """
        result = {
            'is_uptrend': False,
            'trend_strength': 0.0,
            'ma_bullish_alignment': False,
            'slope': 0.0
        }
        
        if len(prices) < 20:
            return result
        
        # 计算各周期均线
        ma5 = self._calculate_ma(prices, 5)
        ma10 = self._calculate_ma(prices, 10)
        ma20 = self._calculate_ma(prices, 20)
        
        if ma5 is None or ma10 is None or ma20 is None:
            return result
        
        # 判断多头排列
        result['ma_bullish_alignment'] = ma5 > ma10 > ma20
        
        # 计算价格斜率（线性回归）
        x = np.arange(len(prices[-20:]))
        y = np.array(prices[-20:])
        
        if len(x) > 1 and np.std(y) > 0:
            slope = np.polyfit(x, y, 1)[0]
            result['slope'] = slope
            
            # 标准化斜率到-1到1范围
            price_mean = np.mean(y)
            if price_mean > 0:
                normalized_slope = slope / price_mean * 20  # 20天周期标准化
                result['trend_strength'] = max(-1, min(1, normalized_slope))
        
        # 判断趋势方向
        result['is_uptrend'] = (
            result['ma_bullish_alignment'] and 
            result['trend_strength'] > 0.05
        )
        
        return result
    
    def _analyze_volume(self, volumes: List[float], threshold: float = 1.0) -> Dict[str, Any]:
        """
        分析成交量
        
        Args:
            volumes: 成交量列表
            threshold: 成交量倍数阈值
        
        Returns:
            Dict[str, Any]: 成交量分析结果
                - above_average: 是否高于平均
                - volume_ratio: 当前成交量/平均成交量
                - trend: 成交量趋势（"increasing", "decreasing", "stable"）
        """
        result = {
            'above_average': False,
            'volume_ratio': 1.0,
            'trend': 'stable'
        }
        
        if len(volumes) < 20:
            return result
        
        avg_volume = np.mean(volumes[-20:])
        current_volume = volumes[-1]
        
        if avg_volume > 0:
            result['volume_ratio'] = current_volume / avg_volume
            result['above_average'] = result['volume_ratio'] >= threshold
        
        # 判断成交量趋势
        if len(volumes) >= 5:
            recent_avg = np.mean(volumes[-5:])
            previous_avg = np.mean(volumes[-10:-5]) if len(volumes) >= 10 else avg_volume
            
            if previous_avg > 0:
                change = (recent_avg - previous_avg) / previous_avg
                if change > 0.1:
                    result['trend'] = 'increasing'
                elif change < -0.1:
                    result['trend'] = 'decreasing'
        
        return result
    
    def _calculate_trend_score(self, prices: List[float], volumes: List[float]) -> float:
        """
        计算趋势强度得分（0-100）
        
        Args:
            prices: 价格列表
            volumes: 成交量列表
        
        Returns:
            float: 趋势强度得分
        """
        trend_info = self._identify_trend(prices, volumes)
        
        # 基础分
        base_score = 50
        
        # 根据趋势强度调整
        strength = trend_info['trend_strength']
        base_score += strength * 30  # 趋势强度贡献±30分
        
        # 多头排列加分
        if trend_info['ma_bullish_alignment']:
            base_score += 15
        
        # 确保在0-100范围内
        return max(0, min(100, base_score))
    
    def _calculate_momentum_score(self, prices: List[float]) -> float:
        """
        计算动量得分（0-100）
        
        Args:
            prices: 价格列表
        
        Returns:
            float: 动量得分
        """
        if len(prices) < 6:
            return 50
        
        # 计算不同周期的动量
        momentum_5d = self._calculate_momentum(prices, 5)
        momentum_10d = self._calculate_momentum(prices, 10) if len(prices) >= 11 else momentum_5d
        
        # 加权平均动量
        momentum = momentum_5d * 0.6 + momentum_10d * 0.4
        
        # 转换动量到得分（假设合理动量范围-20%到+20%）
        score = 50 + momentum * 250  # 10%动量 = 75分
        
        return max(0, min(100, score))
    
    def _calculate_volume_score(self, volumes: List[float]) -> float:
        """
        计算成交量得分（0-100）
        
        Args:
            volumes: 成交量列表
        
        Returns:
            float: 成交量得分
        """
        if len(volumes) < 20:
            return 50
        
        volume_info = self._analyze_volume(volumes)
        
        # 基础分
        base_score = 50
        
        # 成交量比例调整
        ratio = volume_info['volume_ratio']
        if ratio > 1.0:
            # 放量加分
            base_score += min(30, (ratio - 1.0) * 30)
        else:
            # 缩量减分
            base_score -= min(30, (1.0 - ratio) * 30)
        
        # 成交量趋势调整
        if volume_info['trend'] == 'increasing':
            base_score += 10
        elif volume_info['trend'] == 'decreasing':
            base_score -= 10
        
        return max(0, min(100, base_score))


if __name__ == "__main__":
    # 简单的使用示例
    print("Trend Following Strategy")
    print("=" * 50)
    
    strategy = TrendFollowingStrategy()
    
    print(f"Name: {strategy.get_name()}")
    print(f"Description: {strategy.get_description()}")
    print(f"Config: {strategy.get_config().to_dict()}")
    print(f"Validation: {strategy.validate()}")
    
    # 示例数据测试
    stock_data = {
        '000001.SZ': {
            'prices': [10, 10.2, 10.5, 10.8, 11, 11.3, 11.6, 11.9, 12.2, 12.5,
                      12.8, 13.1, 13.4, 13.7, 14, 14.3, 14.6, 14.9, 15.2, 15.5],
            'volumes': [1000000] * 19 + [1500000],
            'close': 15.5,
            'name': '平安银行'
        },
        '000002.SZ': {
            'prices': [20, 19.8, 19.5, 19.3, 19, 18.8, 18.5, 18.3, 18, 17.8,
                      17.5, 17.3, 17, 16.8, 16.5, 16.3, 16, 15.8, 15.5, 15.3],
            'volumes': [800000] * 20,
            'close': 15.3,
            'name': '万科A'
        }
    }
    
    market_data = {
        'index': {
            'close': 3000,
            'change_pct': 1.5,
            'prices': list(range(2950, 2970))
        }
    }
    
    print("\n示例执行:")
    result = strategy.execute(stock_data, market_data)
    print(f"Success: {result.success}")
    print(f"Selected: {result.selected_stocks}")
    print(f"Scores: {result.scores}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")
