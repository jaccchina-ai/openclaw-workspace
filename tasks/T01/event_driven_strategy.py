"""
事件驱动型策略实现

基于事件信号识别和快速响应的事件驱动策略。
识别价格跳空、成交量异常、波动率突变等事件信号，
快速响应市场异动，捕捉事件驱动的交易机会。
"""

from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

import numpy as np

from strategy_base import Strategy, StrategyConfig, StrategyMetadata, StrategyType


class EventType(Enum):
    """事件类型枚举"""
    NONE = "none"
    GAP_UP_VOLUME = "gap_up_volume"
    GAP_DOWN_REBOUND = "gap_down_rebound"
    BREAKOUT = "breakout"
    VOLUME_SURGE = "volume_surge"
    VOLATILITY_SPIKE = "volatility_spike"
    SECTOR_ANOMALY = "sector_anomaly"
    FUND_FLOW = "fund_flow"


@dataclass
class EventSignal:
    """事件信号数据类"""
    event_type: EventType
    strength: float
    confidence: float
    timestamp: Optional[str] = None
    details: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.details is None:
            self.details = {}


class EventDrivenStrategy(Strategy):
    """事件驱动型策略"""
    
    DEFAULT_PARAMS = {
        'price_gap_threshold': 0.02,
        'volume_surge_threshold': 2.0,
        'volatility_threshold': 1.5,
        'sector_correlation_threshold': 0.6,
        'event_window': 5
    }
    
    SCORE_WEIGHTS = {
        'event_strength': 0.40,
        'volume_confirmation': 0.30,
        'price_position': 0.20,
        'sustainability': 0.10
    }
    
    def __init__(self):
        super().__init__()
        self._config = StrategyConfig(
            name="EventDrivenStrategy",
            params=self.DEFAULT_PARAMS.copy(),
            enabled=True,
            description="事件驱动型策略默认配置"
        )
        self._metadata = StrategyMetadata(
            name="EventDrivenStrategy",
            description="基于事件信号识别和快速响应的事件驱动策略",
            version="1.0.0",
            author="T01 System",
            strategy_type=StrategyType.EVENT_DRIVEN,
            tags=["event", "gap", "volume", "breakout", "momentum"],
            created_at=datetime.now().isoformat(),
            updated_at=datetime.now().isoformat()
        )
    
    def get_name(self) -> str:
        return "EventDrivenStrategy"
    
    def get_description(self) -> str:
        return (
            "事件驱动型策略：通过识别价格跳空、成交量异常、波动率突变等事件信号，"
            "快速响应市场异动，捕捉事件驱动的交易机会。"
        )
    
    def validate(self) -> bool:
        params = self._config.params
        
        price_gap = params.get('price_gap_threshold', self.DEFAULT_PARAMS['price_gap_threshold'])
        if not isinstance(price_gap, (int, float)) or price_gap <= 0 or price_gap > 0.5:
            return False
        
        volume_threshold = params.get('volume_surge_threshold', self.DEFAULT_PARAMS['volume_surge_threshold'])
        if not isinstance(volume_threshold, (int, float)) or volume_threshold <= 1:
            return False
        
        volatility_threshold = params.get('volatility_threshold', self.DEFAULT_PARAMS['volatility_threshold'])
        if not isinstance(volatility_threshold, (int, float)) or volatility_threshold <= 0:
            return False
        
        sector_threshold = params.get('sector_correlation_threshold', self.DEFAULT_PARAMS['sector_correlation_threshold'])
        if not isinstance(sector_threshold, (int, float)) or sector_threshold <= 0 or sector_threshold > 1:
            return False
        
        event_window = params.get('event_window', self.DEFAULT_PARAMS['event_window'])
        if not isinstance(event_window, int) or event_window <= 0 or event_window > 30:
            return False
        
        return True
    
    def select(self, stock_data: Dict[str, Any], market_data: Dict[str, Any]) -> List[str]:
        selected = []
        
        params = self._config.params
        price_gap_threshold = params.get('price_gap_threshold', self.DEFAULT_PARAMS['price_gap_threshold'])
        volume_surge_threshold = params.get('volume_surge_threshold', self.DEFAULT_PARAMS['volume_surge_threshold'])
        volatility_threshold = params.get('volatility_threshold', self.DEFAULT_PARAMS['volatility_threshold'])
        
        sectors_data = market_data.get('sectors', {}) if market_data else {}
        
        for stock_code, data in stock_data.items():
            if not self._has_required_fields(data):
                continue
            
            prices = data.get('prices', [])
            volumes = data.get('volumes', [])
            opens = data.get('opens', [])
            highs = data.get('highs', [])
            lows = data.get('lows', [])
            closes = data.get('closes', [])
            prev_close = data.get('prev_close', 0)
            sector = data.get('sector', '')
            
            if len(prices) < 10 or len(volumes) < 10:
                continue
            
            if len(volumes) > 0 and volumes[-1] == 0:
                continue
            
            has_gap = False
            if prev_close > 0 and len(opens) > 0:
                gap = self._calculate_price_gap(prev_close, opens[-1])
                if abs(gap) >= price_gap_threshold:
                    has_gap = True
            
            has_volume_anomaly = False
            is_volume_surge, _ = self._detect_volume_surge(volumes, volume_surge_threshold)
            if is_volume_surge:
                has_volume_anomaly = True

            # 条件3: 波动率突变检测
            has_volatility_spike = False
            if len(highs) >= len(prices) and len(lows) >= len(prices):
                is_spike, _ = self._detect_volatility_spike(highs, lows, closes or prices, volatility_threshold)
                if is_spike:
                    has_volatility_spike = True
            
            has_sector_anomaly = False
            if sector and sector in sectors_data:
                sector_info = sectors_data[sector]
                if stock_code in sector_info:
                    is_anomaly, _ = self._detect_sector_anomaly(sector_info, min_anomaly_stocks=3)
                    if is_anomaly:
                        has_sector_anomaly = True
            
            conditions_met = sum([has_gap, has_volume_anomaly, has_volatility_spike, has_sector_anomaly])
            if conditions_met >= 2:
                selected.append(stock_code)
            elif has_gap and has_volume_anomaly:
                selected.append(stock_code)
            elif self._is_breakout(prices, volumes, volume_surge_threshold):
                selected.append(stock_code)
        
        return selected
    
    def score(self, stock_data: Dict[str, Any]) -> Dict[str, float]:
        scores = {}
        
        for stock_code, data in stock_data.items():
            if not self._has_required_fields(data):
                scores[stock_code] = 0
                continue
            
            prices = data.get('prices', [])
            volumes = data.get('volumes', [])
            
            if len(prices) < 10 or len(volumes) < 10:
                scores[stock_code] = 0
                continue
            
            event_strength_score = self._calculate_event_strength_score(data)
            volume_score = self._calculate_volume_score(volumes)
            price_position_score = self._calculate_price_position_score(prices)
            sustainability_score = self._calculate_sustainability_score(prices, volumes)
            
            total_score = (
                event_strength_score * self.SCORE_WEIGHTS['event_strength'] +
                volume_score * self.SCORE_WEIGHTS['volume_confirmation'] +
                price_position_score * self.SCORE_WEIGHTS['price_position'] +
                sustainability_score * self.SCORE_WEIGHTS['sustainability']
            )
            
            scores[stock_code] = max(0, min(100, total_score))
        
        return scores
    
    @staticmethod
    def _has_required_fields(data: Dict[str, Any]) -> bool:
        required_fields = ['prices', 'volumes', 'close']
        return all(field in data for field in required_fields)
    
    @staticmethod
    def _calculate_price_gap(prev_close: float, curr_open: float) -> float:
        if prev_close == 0:
            return 0.0
        return (curr_open - prev_close) / prev_close
    
    def _detect_volume_surge(self, volumes: List[float], threshold: float = 2.0) -> Tuple[bool, float]:
        if len(volumes) < 10:
            return False, 1.0
        
        avg_volume = np.mean(volumes[-10:-1]) if len(volumes) >= 10 else np.mean(volumes[:-1])
        current_volume = volumes[-1]
        
        if avg_volume == 0:
            return False, 1.0
        
        ratio = current_volume / avg_volume
        return ratio >= threshold, ratio
    
    def _detect_volume_contraction(self, volumes: List[float], threshold: float = 0.5) -> Tuple[bool, float]:
        if len(volumes) < 10:
            return False, 1.0
        
        avg_volume = np.mean(volumes[-10:-1]) if len(volumes) >= 10 else np.mean(volumes[:-1])
        current_volume = volumes[-1]
        
        if avg_volume == 0:
            return False, 1.0
        
        ratio = current_volume / avg_volume
        return ratio <= threshold, ratio
    
    def _calculate_atr(self, highs: List[float], lows: List[float], closes: List[float], period: int = 14) -> Optional[float]:
        if len(highs) < period + 1 or len(lows) < period + 1 or len(closes) < period + 1:
            return None
        
        tr_values = []
        for i in range(1, min(len(highs), len(lows), len(closes))):
            tr1 = highs[i] - lows[i]
            tr2 = abs(highs[i] - closes[i-1])
            tr3 = abs(lows[i] - closes[i-1])
            tr = max(tr1, tr2, tr3)
            tr_values.append(tr)
        
        if len(tr_values) < period:
            return None
        
        return float(np.mean(tr_values[-period:]))
    
    def _detect_volatility_spike(self, highs: List[float], lows: List[float], closes: List[float], threshold: float = 1.5) -> Tuple[bool, float]:
        if len(highs) < 20 or len(lows) < 20 or len(closes) < 20:
            return False, 1.0
        
        prev_atr = self._calculate_atr(highs[:-5], lows[:-5], closes[:-5], period=10)
        recent_atr = self._calculate_atr(highs[-5:], lows[-5:], closes[-5:], period=3)
        
        if prev_atr is None or recent_atr is None or prev_atr == 0:
            return False, 1.0
        
        ratio = recent_atr / prev_atr
        return ratio >= threshold, ratio
    
    def _calculate_sector_correlation(self, sector_stocks: Dict[str, Dict[str, Any]]) -> float:
        if len(sector_stocks) < 2:
            return 0.0
        
        changes = []
        for stock_data in sector_stocks.values():
            if isinstance(stock_data, dict) and 'change_pct' in stock_data:
                changes.append(stock_data['change_pct'])
        
        if len(changes) < 2:
            return 0.0
        
        positive_changes = sum(1 for c in changes if c > 0)
        negative_changes = sum(1 for c in changes if c < 0)
        
        max_consistent = max(positive_changes, negative_changes)
        consistency = max_consistent / len(changes)
        
        change_std = np.std(changes) if len(changes) > 1 else 0
        change_mean = abs(np.mean(changes))
        
        if change_mean > 0:
            cv = change_std / change_mean
            consistency *= max(0, 1 - cv / 2)
        
        return min(1.0, max(0.0, consistency))
    
    def _detect_sector_anomaly(self, sector_stocks: Dict[str, Dict[str, Any]], threshold: float = 0.6, min_anomaly_stocks: int = 3) -> Tuple[bool, int]:
        anomaly_count = 0
        
        for stock_data in sector_stocks.values():
            if isinstance(stock_data, dict):
                change_pct = stock_data.get('change_pct', 0)
                volume_ratio = stock_data.get('volume_ratio', 1.0)
                
                if abs(change_pct) >= threshold * 100 and volume_ratio >= 1.5:
                    anomaly_count += 1
        
        return anomaly_count >= min_anomaly_stocks, anomaly_count
    
    def _identify_gap_event(self, prev_close: float, curr_open: float, volumes: List[float], prices: Optional[List[float]] = None) -> EventType:
        gap = self._calculate_price_gap(prev_close, curr_open)
        threshold = self._config.params.get('price_gap_threshold', self.DEFAULT_PARAMS['price_gap_threshold'])
        volume_threshold = self._config.params.get('volume_surge_threshold', self.DEFAULT_PARAMS['volume_surge_threshold'])
        
        is_volume_surge, _ = self._detect_volume_surge(volumes, volume_threshold)
        
        if gap >= threshold:
            if is_volume_surge:
                return EventType.GAP_UP_VOLUME
        elif gap <= -threshold:
            if is_volume_surge and prices and len(prices) >= 2:
                if prices[-1] > curr_open:
                    return EventType.GAP_DOWN_REBOUND
        
        return EventType.NONE
    
    def _identify_breakout_event(self, prices: List[float], volumes: List[float]) -> EventType:
        if len(prices) < 20 or len(volumes) < 20:
            return EventType.NONE
        
        volume_threshold = self._config.params.get('volume_surge_threshold', self.DEFAULT_PARAMS['volume_surge_threshold'])
        is_volume_surge, _ = self._detect_volume_surge(volumes, volume_threshold)
        
        if not is_volume_surge:
            return EventType.NONE
        
        recent_high = max(prices[-20:-5]) if len(prices) >= 20 else max(prices[:-5])
        current_price = prices[-1]
        
        if current_price > recent_high * 1.03:
            return EventType.BREAKOUT
        
        return EventType.NONE
    
    def _is_breakout(self, prices: List[float], volumes: List[float], volume_threshold: float = 2.0) -> bool:
        if len(prices) < 20 or len(volumes) < 20:
            return False
        
        is_volume_surge, _ = self._detect_volume_surge(volumes, volume_threshold)
        if not is_volume_surge:
            return False
        
        recent_high = max(prices[-20:-5]) if len(prices) >= 20 else max(prices[:-5])
        current_price = prices[-1]
        
        return current_price > recent_high * 1.02
    
    def _calculate_event_strength_score(self, data: Dict[str, Any]) -> float:
        scores = []
        
        prices = data.get('prices', [])
        volumes = data.get('volumes', [])
        opens = data.get('opens', [])
        prev_close = data.get('prev_close', 0)
        
        if prev_close > 0 and opens:
            gap = abs(self._calculate_price_gap(prev_close, opens[-1]))
            gap_score = min(100, gap * 2000)
            scores.append(gap_score)
        
        if volumes:
            _, volume_ratio = self._detect_volume_surge(volumes, threshold=1.0)
            volume_score = min(100, (volume_ratio - 1) * 50)
            scores.append(volume_score)
        
        if len(prices) >= 2:
            price_change = abs(prices[-1] - prices[-2]) / prices[-2] if prices[-2] != 0 else 0
            price_score = min(100, price_change * 2000)
            scores.append(price_score)
        
        return np.mean(scores) if scores else 50
    
    def _calculate_volume_score(self, volumes: List[float]) -> float:
        if len(volumes) < 10:
            return 50
        
        _, ratio = self._detect_volume_surge(volumes, threshold=1.0)
        
        base_score = 50
        
        if ratio > 1.0:
            base_score += min(50, (ratio - 1) * 33)
        else:
            base_score -= min(50, (1 - ratio) * 50)
        
        return max(0, min(100, base_score))
    
    def _calculate_price_position_score(self, prices: List[float]) -> float:
        if len(prices) < 20:
            return 50
        
        current_price = prices[-1]
        recent_high = max(prices[-20:])
        recent_low = min(prices[-20:])
        
        if recent_high == recent_low:
            return 50
        
        position = (current_price - recent_low) / (recent_high - recent_low)
        
        return max(0, min(100, position * 100))
    
    def _calculate_sustainability_score(self, prices: List[float], volumes: List[float]) -> float:
        if len(prices) < 10 or len(volumes) < 10:
            return 50
        
        score = 50
        
        if len(prices) >= 5:
            recent_trend = (prices[-1] - prices[-5]) / prices[-5] if prices[-5] != 0 else 0
            if recent_trend > 0.05:
                score += 20
            elif recent_trend < -0.05:
                score -= 20
        
        if len(volumes) >= 5:
            recent_volume_trend = np.mean(volumes[-3:]) / np.mean(volumes[-6:-3]) if np.mean(volumes[-6:-3]) > 0 else 1
            if recent_volume_trend > 1.2:
                score += 15
            elif recent_volume_trend < 0.8:
                score -= 15
        
        return max(0, min(100, score))


if __name__ == "__main__":
    print("Event Driven Strategy")
    print("=" * 50)
    
    strategy = EventDrivenStrategy()
    
    print(f"Name: {strategy.get_name()}")
    print(f"Description: {strategy.get_description()}")
    print(f"Config: {strategy.get_config().to_dict()}")
    print(f"Validation: {strategy.validate()}")
    
    stock_data = {
        '000001.SZ': {
            'prices': [10.0] * 19 + [10.0, 10.5],
            'opens': [10.0] * 19 + [10.5],
            'highs': [10.2] * 19 + [10.8],
            'lows': [9.8] * 19 + [10.3],
            'closes': [10.0] * 19 + [10.5],
            'volumes': [1000000] * 19 + [2500000],
            'close': 10.5,
            'prev_close': 10.0,
            'name': '跳空股A',
            'sector': 'tech'
        },
        '000002.SZ': {
            'prices': [10.0] * 20,
            'opens': [10.0] * 20,
            'highs': [10.1] * 20,
            'lows': [9.9] * 20,
            'closes': [10.0] * 20,
            'volumes': [1000000] * 20,
            'close': 10.0,
            'prev_close': 10.0,
            'name': '正常股B',
            'sector': 'tech'
        }
    }
    
    market_data = {
        'index': {
            'close': 3000,
            'change_pct': 1.5,
            'prices': list(range(2950, 2970))
        },
        'sectors': {
            'tech': {
                '000001.SZ': {'change_pct': 5.0, 'volume_ratio': 2.5},
                '000002.SZ': {'change_pct': 0.1, 'volume_ratio': 1.0}
            }
        }
    }
    
    print("\n示例执行:")
    result = strategy.execute(stock_data, market_data)
    print(f"Success: {result.success}")
    print(f"Selected: {result.selected_stocks}")
    print(f"Scores: {result.scores}")
    print(f"Execution time: {result.execution_time_ms:.2f}ms")
