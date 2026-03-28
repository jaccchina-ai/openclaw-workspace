"""市场环境检测模块

用于识别当前市场状态（牛市/熊市/震荡市），为策略选择提供依据。
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional
import numpy as np


class MarketTrend(Enum):
    """市场趋势类型"""
    BULL = "bull"           # 牛市
    BEAR = "bear"           # 熊市
    SIDEWAYS = "sideways"   # 震荡市
    UNKNOWN = "unknown"     # 未知


@dataclass
class EnvironmentConfig:
    """环境配置类

    Attributes:
        ma_short: 短期均线周期（默认20）
        ma_long: 长期均线周期（默认60）
        trend_threshold: 趋势判断阈值（默认0.05）
        volatility_threshold: 波动率阈值（默认0.02）
        confidence_threshold: 置信度阈值（默认0.7）
        lookback_period: 回看周期（默认60天）
    """
    ma_short: int = 20
    ma_long: int = 60
    trend_threshold: float = 0.05
    volatility_threshold: float = 0.02
    confidence_threshold: float = 0.7
    lookback_period: int = 60

    def __post_init__(self):
        """验证配置参数"""
        if self.ma_short <= 0 or self.ma_long <= 0:
            raise ValueError("MA periods must be positive")
        if self.ma_long < self.ma_short:
            raise ValueError("ma_long must be >= ma_short")
        if self.trend_threshold < 0:
            raise ValueError("trend_threshold must be non-negative")
        if self.volatility_threshold < 0:
            raise ValueError("volatility_threshold must be non-negative")
        if not 0 <= self.confidence_threshold <= 1:
            raise ValueError("confidence_threshold must be between 0 and 1")


@dataclass
class MarketIndicators:
    """市场指标数据类"""
    ma20: float = 0.0
    ma60: float = 0.0
    atr: float = 0.0
    trend_slope: float = 0.0
    trend_duration: int = 0
    volume_trend: float = 1.0
    volume_price_alignment: float = 0.0
    advance_decline_ratio: float = 1.0
    new_highs_lows_ratio: float = 1.0
    bollinger_width: float = 0.0
    volatility_change: float = 0.0


class MarketEnvironment:
    """市场环境检测器

    用于识别当前市场状态（牛市/熊市/震荡市），为策略选择提供依据。

    Attributes:
        config: 环境配置参数
        _current_trend: 当前检测到的市场趋势
        _confidence: 检测置信度
        _indicators: 检测指标详情
    """

    def __init__(self, config: Optional[EnvironmentConfig] = None):
        """初始化市场环境检测器

        Args:
            config: 环境配置，如果为None则使用默认配置
        """
        self._config = config if config is not None else EnvironmentConfig()
        self._current_trend = MarketTrend.UNKNOWN
        self._confidence = 0.0
        self._indicators = MarketIndicators()

    def detect(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """检测当前市场环境

        Args:
            market_data: 市场数据字典，包含：
                - index: 当前指数数据 {close, high, low, volume}
                - history: 历史数据 {close[], high[], low[], volume[]}
                - market_breadth: 市场广度数据 {advance_decline_ratio, new_highs, new_lows}

        Returns:
            Dict包含：
                - trend: 市场趋势类型 (MarketTrend)
                - confidence: 置信度 (0-1)
                - indicators: 检测指标详情
        """
        # 验证数据完整性
        if not self._validate_data(market_data):
            return {
                "trend": MarketTrend.UNKNOWN,
                "confidence": 0.0,
                "indicators": self._indicators
            }

        # 计算指标
        self._calculate_indicators(market_data)

        # 判断市场趋势
        self._determine_trend(market_data)

        return {
            "trend": self._current_trend,
            "confidence": self._confidence,
            "indicators": self._indicators
        }

    def _validate_data(self, market_data: Dict[str, Any]) -> bool:
        """验证数据完整性"""
        if not market_data or "index" not in market_data:
            return False

        index_data = market_data.get("index", {})
        required_fields = ["close", "high", "low", "volume"]
        if not all(field in index_data for field in required_fields):
            return False

        # 检查历史数据
        history = market_data.get("history", {})
        if "close" not in history or len(history["close"]) < self._config.lookback_period:
            return False

        return True

    def _calculate_indicators(self, market_data: Dict[str, Any]):
        """计算检测指标"""
        history = market_data["history"]
        closes = np.array(history["close"])
        highs = np.array(history["high"])
        lows = np.array(history["low"])
        volumes = np.array(history["volume"])

        # 计算移动平均线
        self._indicators.ma20 = np.mean(closes[-self._config.ma_short:])
        self._indicators.ma60 = np.mean(closes[-self._config.ma_long:])

        # 计算ATR (平均真实波幅)
        tr1 = highs[1:] - lows[1:]
        tr2 = np.abs(highs[1:] - closes[:-1])
        tr3 = np.abs(lows[1:] - closes[:-1])
        tr = np.maximum(np.maximum(tr1, tr2), tr3)
        self._indicators.atr = np.mean(tr[-14:]) if len(tr) >= 14 else np.mean(tr)

        # 计算趋势斜率（线性回归）
        x = np.arange(len(closes))
        slope, _ = np.polyfit(x, closes, 1)
        self._indicators.trend_slope = slope

        # 计算趋势持续时间
        self._indicators.trend_duration = self._calculate_trend_duration(closes)

        # 计算成交量趋势
        if len(volumes) >= 20:
            recent_vol = np.mean(volumes[-5:])
            past_vol = np.mean(volumes[-20:-5])
            self._indicators.volume_trend = recent_vol / past_vol if past_vol > 0 else 1.0

        # 计算布林带宽度
        ma = np.mean(closes[-20:])
        std = np.std(closes[-20:])
        self._indicators.bollinger_width = (2 * std) / ma if ma > 0 else 0

        # 市场广度数据
        market_breadth = market_data.get("market_breadth", {})
        self._indicators.advance_decline_ratio = market_breadth.get("advance_decline_ratio", 1.0)
        new_highs = market_breadth.get("new_highs", 0)
        new_lows = market_breadth.get("new_lows", 1)
        self._indicators.new_highs_lows_ratio = new_highs / new_lows if new_lows > 0 else 1.0

    def _calculate_trend_duration(self, closes: np.ndarray) -> int:
        """计算趋势持续时间"""
        if len(closes) < 2:
            return 0

        # 计算每日涨跌
        changes = np.diff(closes)

        # 确定当前趋势方向
        if changes[-1] > 0:
            trend_direction = 1  # 上升
        elif changes[-1] < 0:
            trend_direction = -1  # 下降
        else:
            return 0

        # 计算趋势持续时间
        duration = 0
        for change in reversed(changes):
            if (trend_direction == 1 and change > 0) or (trend_direction == -1 and change < 0):
                duration += 1
            else:
                break

        return duration

    def _determine_trend(self, market_data: Dict[str, Any]):
        """判断市场趋势"""
        index_data = market_data["index"]
        close = index_data["close"]

        # 牛市判断条件
        bull_signals = 0
        total_signals = 5

        # 1. 指数 > MA20 > MA60
        if close > self._indicators.ma20 > self._indicators.ma60:
            bull_signals += 1

        # 2. 趋势持续 > 20天
        if self._indicators.trend_duration > 20:
            bull_signals += 1

        # 3. 成交量温和放大
        if 1.05 <= self._indicators.volume_trend <= 1.5:
            bull_signals += 1

        # 4. 涨跌家数比 > 1.5
        if self._indicators.advance_decline_ratio > 1.5:
            bull_signals += 1

        # 5. 新高/新低比 > 2
        if self._indicators.new_highs_lows_ratio > 2:
            bull_signals += 1

        # 熊市判断条件
        bear_signals = 0

        # 1. 指数 < MA20 < MA60
        if close < self._indicators.ma20 < self._indicators.ma60:
            bear_signals += 1

        # 2. 下降趋势持续 > 20天
        if self._indicators.trend_duration > 20 and self._indicators.trend_slope < 0:
            bear_signals += 1

        # 3. 成交量萎缩或恐慌性放大
        if self._indicators.volume_trend < 0.95 or self._indicators.volume_trend > 2.0:
            bear_signals += 1

        # 4. 涨跌家数比 < 0.7
        if self._indicators.advance_decline_ratio < 0.7:
            bear_signals += 1

        # 5. 新高/新低比 < 0.5
        if self._indicators.new_highs_lows_ratio < 0.5:
            bear_signals += 1

        # 震荡市判断条件
        sideways_signals = 0

        # 1. 指数在MA20附近波动
        if abs(close - self._indicators.ma20) / self._indicators.ma20 < 0.02:
            sideways_signals += 1

        # 2. 波动率较低
        if self._indicators.atr / close < self._config.volatility_threshold:
            sideways_signals += 1

        # 3. 趋势不明确
        if abs(self._indicators.trend_slope) < 0.1:
            sideways_signals += 1

        # 4. 成交量平稳
        if 0.95 <= self._indicators.volume_trend <= 1.05:
            sideways_signals += 1

        # 5. 涨跌家数比接近1
        if 0.8 <= self._indicators.advance_decline_ratio <= 1.2:
            sideways_signals += 1

        # 确定最终趋势
        if bull_signals >= 3:
            self._current_trend = MarketTrend.BULL
            self._confidence = bull_signals / total_signals
        elif bear_signals >= 3:
            self._current_trend = MarketTrend.BEAR
            self._confidence = bear_signals / total_signals
        elif sideways_signals >= 3:
            self._current_trend = MarketTrend.SIDEWAYS
            self._confidence = sideways_signals / total_signals
        else:
            self._current_trend = MarketTrend.UNKNOWN
            self._confidence = 0.0

    def get_market_trend(self) -> MarketTrend:
        """获取当前市场趋势"""
        return self._current_trend

    def get_confidence(self) -> float:
        """获取检测置信度"""
        return self._confidence

    def get_indicators(self) -> Dict[str, Any]:
        """获取检测指标详情"""
        return {
            "ma20": self._indicators.ma20,
            "ma60": self._indicators.ma60,
            "atr": self._indicators.atr,
            "trend_slope": self._indicators.trend_slope,
            "trend_duration": self._indicators.trend_duration,
            "volume_trend": self._indicators.volume_trend,
            "volume_price_alignment": self._indicators.volume_price_alignment,
            "advance_decline_ratio": self._indicators.advance_decline_ratio,
            "new_highs_lows_ratio": self._indicators.new_highs_lows_ratio,
            "bollinger_width": self._indicators.bollinger_width,
            "volatility_change": self._indicators.volatility_change
        }

    def is_bull_market(self) -> bool:
        """判断是否牛市"""
        return self._current_trend == MarketTrend.BULL

    def is_bear_market(self) -> bool:
        """判断是否熊市"""
        return self._current_trend == MarketTrend.BEAR

    def is_sideways_market(self) -> bool:
        """判断是否震荡市"""
        return self._current_trend == MarketTrend.SIDEWAYS
