"""
反转抄底型策略实现

基于RSI指标、价格偏离度和支撑位的反转抄底策略。
识别超跌股票，预测反弹机会。

核心逻辑：
1. 使用RSI指标识别超卖区域（RSI < 30）
2. 计算价格偏离度判断超跌程度
3. 检测近期支撑位
4. 识别反转K线形态
5. 分析成交量萎缩后放量（底部确认）
6. 综合评分选出最佳反弹标的
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

import numpy as np

from strategy_base import Strategy, StrategyConfig, StrategyMetadata, StrategyType


@dataclass
class ReversalConfig:
    """
    反转策略专用配置类

    Attributes:
        rsi_period: RSI计算周期（默认14）
        rsi_oversold: RSI超卖阈值（默认30）
        price_deviation_threshold: 价格偏离阈值（默认-0.15，即低于MA20 15%）
        volume_contraction_threshold: 成交量萎缩阈值（默认0.7）
        support_lookback: 支撑位回看周期（默认20）
    """
    rsi_period: int = 14
    rsi_oversold: float = 30
    price_deviation_threshold: float = -0.15
    volume_contraction_threshold: float = 0.7
    support_lookback: int = 20

    def to_dict(self) -> Dict[str, Any]:
        """将配置转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ReversalConfig':
        """从字典创建配置"""
        return cls(
            rsi_period=data.get('rsi_period', 14),
            rsi_oversold=data.get('rsi_oversold', 30),
            price_deviation_threshold=data.get('price_deviation_threshold', -0.15),
            volume_contraction_threshold=data.get('volume_contraction_threshold', 0.7),
            support_lookback=data.get('support_lookback', 20)
        )


class ReversalStrategy(Strategy):
    """
    反转抄底型策略

    通过RSI指标、价格偏离度和支撑位识别超跌股票，
    预测反弹机会。适用于熊市末期和震荡市中的反弹机会。

    Attributes:
        _config: 策略配置
        _metadata: 策略元数据

    配置参数:
        rsi_period: RSI计算周期（默认14）
        rsi_oversold: RSI超卖阈值（默认30）
        price_deviation_threshold: 价格偏离阈值（默认-0.15）
        volume_contraction_threshold: 成交量萎缩阈值（默认0.7）
        support_lookback: 支撑位回看周期（默认20）
    """

    # 默认配置参数
    DEFAULT_PARAMS = {
        'rsi_period': 14,
        'rsi_oversold': 30,
        'price_deviation_threshold': -0.15,
        'volume_contraction_threshold': 0.7,
        'support_lookback': 20
    }

    def __init__(self):
        """初始化反转抄底策略"""
        super().__init__()

        # 设置默认配置
        self._config = StrategyConfig(
            name="ReversalStrategy",
            params=self.DEFAULT_PARAMS.copy(),
            enabled=True,
            description="反转抄底型策略默认配置"
        )

        # 设置元数据
        self._metadata = StrategyMetadata(
            name="ReversalStrategy",
            description="基于RSI指标和价格偏离度的反转抄底策略，识别超跌股票的反弹机会",
            version="1.0.0",
            author="T01 System",
            strategy_type=StrategyType.REVERSAL,
            tags=["reversal", "oversold", "rsi", "support", "bottom_fishing"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )

    def get_name(self) -> str:
        """
        获取策略名称

        Returns:
            str: "ReversalStrategy"
        """
        return "ReversalStrategy"

    def get_description(self) -> str:
        """
        获取策略描述

        Returns:
            str: 策略详细描述
        """
        return (
            "反转抄底型策略：基于RSI指标识别超卖区域，通过价格偏离度判断超跌程度，"
            "结合支撑位和成交量分析，选出具有反弹潜力的超跌股票。"
            "适用于熊市末期和震荡市中的反弹机会捕捉。"
        )

    def validate(self) -> bool:
        """
        验证策略配置

        检查项：
        1. RSI周期必须为正整数
        2. RSI超卖阈值必须在0-100范围内
        3. 价格偏离阈值必须为负数（表示下跌）
        4. 成交量萎缩阈值必须在0-1范围内
        5. 支撑位回看周期必须为正整数

        Returns:
            bool: 配置是否有效
        """
        params = self._config.params

        # 检查RSI周期
        rsi_period = params.get('rsi_period', self.DEFAULT_PARAMS['rsi_period'])
        if not (isinstance(rsi_period, int) and rsi_period > 0):
            return False

        # 检查RSI超卖阈值
        rsi_oversold = params.get('rsi_oversold', self.DEFAULT_PARAMS['rsi_oversold'])
        if not isinstance(rsi_oversold, (int, float)):
            return False
        if rsi_oversold < 0 or rsi_oversold > 100:
            return False

        # 检查价格偏离阈值（必须为负数）
        price_deviation = params.get('price_deviation_threshold',
                                     self.DEFAULT_PARAMS['price_deviation_threshold'])
        if not isinstance(price_deviation, (int, float)):
            return False
        if price_deviation > 0:  # 反转策略应该寻找下跌的股票
            return False

        # 检查成交量萎缩阈值
        volume_threshold = params.get('volume_contraction_threshold',
                                      self.DEFAULT_PARAMS['volume_contraction_threshold'])
        if not isinstance(volume_threshold, (int, float)):
            return False
        if volume_threshold <= 0 or volume_threshold > 1:
            return False

        # 检查支撑位回看周期
        support_lookback = params.get('support_lookback',
                                      self.DEFAULT_PARAMS['support_lookback'])
        if not (isinstance(support_lookback, int) and support_lookback > 0):
            return False

        return True

    def select(self, stock_data: Dict[str, Any], market_data: Dict[str, Any]) -> List[str]:
        """
        选股逻辑

        根据反转抄底规则筛选符合条件的股票：
        1. RSI < rsi_oversold（超卖区域）
        2. 价格偏离MA20超过阈值（超跌）
        3. 成交量萎缩后放量（底部确认）
        4. 近期有支撑位

        Args:
            stock_data: 股票数据字典
                格式: {
                    "股票代码": {
                        "prices": [历史价格列表],
                        "volumes": [历史成交量列表],
                        "close": 最新收盘价,
                        "open": 最新开盘价,
                        "high": 最新最高价,
                        "low": 最新最低价,
                        "name": 股票名称
                    }
                }
            market_data: 市场数据字典
                格式: {
                    "index": {
                        "close": 收盘指数,
                        "change_pct": 涨跌幅
                    }
                }

        Returns:
            List[str]: 符合条件的股票代码列表
        """
        selected = []

        # 获取配置参数
        params = self._config.params
        rsi_period = params.get('rsi_period', self.DEFAULT_PARAMS['rsi_period'])
        rsi_oversold = params.get('rsi_oversold', self.DEFAULT_PARAMS['rsi_oversold'])
        price_deviation_threshold = params.get('price_deviation_threshold',
                                               self.DEFAULT_PARAMS['price_deviation_threshold'])
        volume_threshold = params.get('volume_contraction_threshold',
                                      self.DEFAULT_PARAMS['volume_contraction_threshold'])
        support_lookback = params.get('support_lookback',
                                      self.DEFAULT_PARAMS['support_lookback'])

        for stock_code, data in stock_data.items():
            # 检查必要字段
            if not self._has_required_fields(data):
                continue

            prices = data.get('prices', [])
            volumes = data.get('volumes', [])

            # 数据长度检查
            min_length = max(rsi_period, support_lookback, 20)
            if len(prices) < min_length or len(volumes) < min_length:
                continue

            # 条件1: RSI < 超卖阈值
            rsi = self._calculate_rsi(prices, rsi_period)
            if rsi is None or rsi >= rsi_oversold:
                continue

            # 条件2: 价格偏离MA20超过阈值（超跌）
            deviation = self._calculate_price_deviation(prices, ma_period=20)
            if deviation is None or deviation > price_deviation_threshold:
                continue

            # 条件3: 成交量萎缩后放量
            if not self._is_volume_contracting(volumes, volume_threshold):
                continue

            # 检查是否有放量迹象（底部确认）
            if not self._has_volume_expansion(volumes):
                continue

            # 条件4: 近期有支撑位
            support_level = self._detect_support_level(prices, support_lookback)
            if support_level is None:
                continue

            # 当前价格应该接近支撑位（在5%范围内）
            current_price = prices[-1]
            if abs(current_price - support_level) / support_level > 0.05:
                continue

            selected.append(stock_code)

        return selected

    def score(self, stock_data: Dict[str, Any]) -> Dict[str, float]:
        """
        评分逻辑

        对每只股票进行综合评分（0-100）：
        - 超跌程度（40%权重）
        - 反转信号强度（30%权重）
        - 成交量配合（20%权重）
        - 支撑强度（10%权重）

        Args:
            stock_data: 股票数据字典

        Returns:
            Dict[str, float]: 股票评分字典 {股票代码: 分数}
        """
        scores = {}

        # 获取配置参数
        params = self._config.params
        rsi_period = params.get('rsi_period', self.DEFAULT_PARAMS['rsi_period'])
        support_lookback = params.get('support_lookback', self.DEFAULT_PARAMS['support_lookback'])

        for stock_code, data in stock_data.items():
            # 检查必要字段
            if not self._has_required_fields(data):
                scores[stock_code] = 0
                continue

            prices = data.get('prices', [])
            volumes = data.get('volumes', [])
            opens = data.get('opens', [])
            highs = data.get('highs', [])
            lows = data.get('lows', [])

            min_length = max(rsi_period, support_lookback, 5)
            if len(prices) < min_length or len(volumes) < min_length:
                scores[stock_code] = 0
                continue

            # 计算各项得分
            oversold_score = self._calculate_oversold_score(prices, rsi_period)
            reversal_score = self._calculate_reversal_score(prices, opens, highs, lows)
            volume_score = self._calculate_volume_score(volumes)
            support_score = self._calculate_support_score(prices, support_lookback)

            # 综合评分（加权平均）
            total_score = (
                oversold_score * 0.4 +
                reversal_score * 0.3 +
                volume_score * 0.2 +
                support_score * 0.1
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
    def _calculate_rsi(prices: List[float], period: int = 14) -> Optional[float]:
        """
        计算RSI指标（相对强弱指标）

        公式：RSI = 100 - (100 / (1 + RS))
        其中 RS = 平均上涨幅度 / 平均下跌幅度

        Args:
            prices: 价格列表
            period: RSI计算周期

        Returns:
            Optional[float]: RSI值（0-100），数据不足时返回None
        """
        if len(prices) < period + 1:
            return None

        # 计算价格变化
        deltas = np.diff(prices)

        # 分离上涨和下跌
        gains = np.where(deltas > 0, deltas, 0)
        losses = np.where(deltas < 0, -deltas, 0)

        # 计算平均上涨和下跌（使用简单移动平均）
        avg_gain = np.mean(gains[-period:])
        avg_loss = np.mean(losses[-period:])

        if avg_loss == 0:
            return 100.0 if avg_gain > 0 else 50.0

        rs = avg_gain / avg_loss
        rsi = 100 - (100 / (1 + rs))

        return float(rsi)

    @staticmethod
    def _calculate_price_deviation(prices: List[float], ma_period: int = 20) -> Optional[float]:
        """
        计算价格偏离度

        公式：(当前价格 - MA) / MA

        Args:
            prices: 价格列表
            ma_period: 均线周期

        Returns:
            Optional[float]: 价格偏离度，数据不足时返回None
        """
        if len(prices) < ma_period:
            return None

        ma = np.mean(prices[-ma_period:])
        current_price = prices[-1]

        if ma == 0:
            return None

        return (current_price - ma) / ma

    @staticmethod
    def _detect_support_level(prices: List[float], lookback: int = 20) -> Optional[float]:
        """
        检测支撑位

        通过寻找近期价格的局部最低点来识别支撑位

        Args:
            prices: 价格列表
            lookback: 回看周期

        Returns:
            Optional[float]: 支撑位价格，数据不足时返回None
        """
        if len(prices) < lookback:
            return None

        recent_prices = prices[-lookback:]

        # 找出近期最低点
        min_price = min(recent_prices)

        # 检查该低点是否多次被测试（形成支撑）
        support_tests = sum(1 for p in recent_prices if abs(p - min_price) / min_price < 0.02)

        # 如果至少有2次测试，认为是有效支撑
        if support_tests >= 2:
            return min_price

        # 否则返回近期低点作为潜在支撑
        return min_price

    def _is_volume_contracting(self, volumes: List[float], threshold: float = 0.7) -> bool:
        """
        检查成交量是否萎缩

        检查近期是否存在成交量相对于前期平均水平出现萎缩的阶段

        Args:
            volumes: 成交量列表
            threshold: 萎缩阈值（萎缩期成交量/前期平均成交量 < threshold）

        Returns:
            bool: 是否出现过萎缩
        """
        if len(volumes) < 10:
            return False

        # 计算前1/3的平均成交量（作为基准）
        early_end = len(volumes) // 3
        early_volumes = volumes[:early_end]

        # 计算中间1/3的成交量（检查是否萎缩）
        mid_start = early_end
        mid_end = 2 * len(volumes) // 3
        mid_volumes = volumes[mid_start:mid_end]

        if len(early_volumes) == 0 or len(mid_volumes) == 0:
            return False

        early_avg = np.mean(early_volumes)
        mid_avg = np.mean(mid_volumes)

        if early_avg == 0:
            return False

        # 检查中间阶段是否出现萎缩
        return mid_avg / early_avg < threshold

    def _has_volume_expansion(self, volumes: List[float]) -> bool:
        """
        检查是否有放量迹象（底部确认）

        Args:
            volumes: 成交量列表

        Returns:
            bool: 是否有放量
        """
        if len(volumes) < 5:
            return False

        # 最近一天的成交量是否大于前几天平均
        recent_volume = volumes[-1]
        prev_avg = np.mean(volumes[-5:-1])

        if prev_avg == 0:
            return False

        # 放量10%以上视为底部确认信号
        return recent_volume / prev_avg > 1.1

    def _detect_reversal_pattern(self, opens: List[float], highs: List[float],
                                  lows: List[float], closes: List[float]) -> float:
        """
        检测反转K线形态

        识别的形态：
        - 锤子线：小实体，长下影线
        - 看涨吞没：第二天阳线包含第一天阴线
        - 早晨之星：三天形态

        Args:
            opens: 开盘价列表
            highs: 最高价列表
            lows: 最低价列表
            closes: 收盘价列表

        Returns:
            float: 反转信号强度（0-100）
        """
        if len(closes) < 3:
            return 0.0

        strength = 0.0
        n = len(closes)

        # 检查最近3天的K线
        for i in range(max(1, n-3), n):
            o, h, l, c = opens[i], highs[i], lows[i], closes[i]

            # 实体大小
            body = abs(c - o)
            total_range = h - l

            if total_range == 0:
                continue

            # 锤子线形态：下影线是实体的2倍以上
            if c > o:  # 阳线
                lower_shadow = o - l
                upper_shadow = h - c
            else:  # 阴线
                lower_shadow = c - l
                upper_shadow = h - o

            # 锤子线：下影线长，实体小，上影线短
            if body > 0.001 and lower_shadow / body > 1.5 and upper_shadow / body < 0.3:
                strength += 30
            elif total_range > 0 and body / total_range < 0.3 and lower_shadow / total_range > 0.6:
                # 另一种锤子线判断：小实体，长下影线占比
                strength += 30

            # 看涨吞没
            if i > 0:
                prev_o, prev_c = opens[i-1], closes[i-1]
                # 前一天阴线，第二天阳线，且第二天包含第一天
                if prev_c < prev_o and c > o and o <= prev_c <= c:
                    strength += 40

        return min(100, strength)

    def _calculate_oversold_score(self, prices: List[float], rsi_period: int) -> float:
        """
        计算超跌程度得分（0-100）

        基于RSI和价格偏离度

        Args:
            prices: 价格列表
            rsi_period: RSI周期

        Returns:
            float: 超跌程度得分
        """
        rsi = self._calculate_rsi(prices, rsi_period)
        deviation = self._calculate_price_deviation(prices, ma_period=20)

        if rsi is None or deviation is None:
            return 50

        # RSI越低，得分越高（超卖越严重）
        rsi_score = max(0, (30 - rsi) * 2)  # RSI=30得0分，RSI=0得60分

        # 偏离度越负，得分越高
        deviation_score = max(0, min(40, abs(deviation) * 200))  # -20%偏离得40分

        return min(100, rsi_score + deviation_score)

    def _calculate_reversal_score(self, prices: List[float], opens: List[float],
                                   highs: List[float], lows: List[float]) -> float:
        """
        计算反转信号强度得分（0-100）

        Args:
            prices: 价格列表
            opens: 开盘价列表
            highs: 最高价列表
            lows: 最低价列表

        Returns:
            float: 反转信号强度得分
        """
        # 如果没有OHLC数据，使用价格数据估算
        if not opens or not highs or not lows or len(opens) < len(prices):
            opens = prices[:-1] + [prices[-1]]
            highs = [p * 1.01 for p in prices]
            lows = [p * 0.99 for p in prices]

        # 检测K线形态
        pattern_strength = self._detect_reversal_pattern(opens, highs, lows, prices)

        # 价格动量（近期是否止跌）
        momentum_score = 0
        if len(prices) >= 5:
            recent_change = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] != 0 else 0
            if recent_change > 0:  # 近期上涨
                momentum_score = min(30, recent_change * 500)

        return min(100, pattern_strength + momentum_score)

    def _calculate_volume_score(self, volumes: List[float]) -> float:
        """
        计算成交量配合得分（0-100）

        Args:
            volumes: 成交量列表

        Returns:
            float: 成交量配合得分
        """
        if len(volumes) < 10:
            return 50

        score = 50

        # 成交量萎缩后放量是底部信号
        if self._is_volume_contracting(volumes):
            score += 20

        if self._has_volume_expansion(volumes):
            score += 30

        # 成交量趋势
        recent_avg = np.mean(volumes[-5:])
        prev_avg = np.mean(volumes[-10:-5]) if len(volumes) >= 10 else np.mean(volumes)

        if prev_avg > 0:
            change = (recent_avg - prev_avg) / prev_avg
            if change > 0:
                score += min(20, change * 100)
            else:
                score -= min(20, abs(change) * 100)

        return max(0, min(100, score))

    def _calculate_support_score(self, prices: List[float], lookback: int) -> float:
        """
        计算支撑强度得分（0-100）

        Args:
            prices: 价格列表
            lookback: 回看周期

        Returns:
            float: 支撑强度得分
        """
        support_level = self._detect_support_level(prices, lookback)

        if support_level is None:
            return 30  # 无明确支撑，中等得分

        current_price = prices[-1]

        # 当前价格接近支撑位的程度
        distance = abs(current_price - support_level) / support_level

        # 越接近支撑，得分越高
        if distance < 0.01:
            return 100
        if distance < 0.03:
            return 80
        if distance < 0.05:
            return 60
        return 40


if __name__ == "__main__":
    # 简单的使用示例
    print("Reversal Strategy")
    print("=" * 50)

    strategy = ReversalStrategy()

    print(f"Name: {strategy.get_name()}")
    print(f"Description: {strategy.get_description()}")
    print(f"Config: {strategy.get_config().to_dict()}")
    print(f"Validation: {strategy.validate()}")

    # 示例数据测试 - 超跌股票（符合所有选股条件）
    # 连续下跌，RSI超卖，价格偏离MA20超过15%，成交量萎缩后放量
    stock_data = {
        '000001.SZ': {
            'prices': [20, 19.5, 19, 18.5, 18, 17.5, 17, 16.5, 16, 15.5,
                      15, 14.5, 14, 13.5, 13, 12.5, 12, 11.5, 11, 10.5],
            'volumes': [1000000] * 8 + [500000] * 8 + [900000, 1000000, 1100000, 1200000],
            'close': 10.5,
            'open': 10.3,
            'high': 10.8,
            'low': 10.1,
            'name': '超跌股A'
        },
        '000002.SZ': {
            'prices': [10 + i * 0.1 for i in range(20)],  # 上涨趋势，不应被选中
            'volumes': [1000000] * 20,
            'close': 11.9,
            'open': 11.8,
            'high': 12.0,
            'low': 11.7,
            'name': '上涨股B'
        }
    }

    market_data = {
        'index': {
            'close': 3000,
            'change_pct': -1.5
        }
    }

    print("\n示例执行:")
    result = strategy.execute(stock_data, market_data)
    print(f"Success: {result.success}")
    print(f"Selected: {result.selected_stocks}")
    print(f"Scores: {result.scores}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")

    if result.selected_stocks:
        print("\n选中股票详情:")
        for stock in result.selected_stocks:
            score = result.scores.get(stock, 0)
            print(f"  {stock}: 评分={score:.1f}")

    # 单独测试RSI计算
    print("\nRSI计算测试:")
    prices = [20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10]
    rsi = strategy._calculate_rsi(prices, period=5)
    print(f"下跌序列RSI: {rsi:.2f}")

    prices = [10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20]
    rsi = strategy._calculate_rsi(prices, period=5)
    print(f"上涨序列RSI: {rsi:.2f}")
