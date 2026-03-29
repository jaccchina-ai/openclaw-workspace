#!/usr/bin/env python3
"""
Market Regime Detector Module for T01 Phase 3

This module detects market regimes (bull, bear, sideways) using technical indicators
and provides adaptive thresholds for the trading strategy.

Features:
- Regime classification using moving averages, momentum, volatility, and volume
- Regime transition detection
- History tracking with dates
- Adaptive threshold generation for strategy integration
"""

import pandas as pd
import numpy as np
import tushare as ts
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime enumeration"""
    BULL = 'bull'
    BEAR = 'bear'
    SIDEWAYS = 'sideways'
    UNKNOWN = 'unknown'


@dataclass
class RegimeTransition:
    """Represents a regime transition event"""
    from_regime: MarketRegime
    to_regime: MarketRegime
    date: str
    confidence_from: float
    confidence_to: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert transition to dictionary"""
        return {
            'from_regime': self.from_regime.value,
            'to_regime': self.to_regime.value,
            'date': self.date,
            'confidence_from': self.confidence_from,
            'confidence_to': self.confidence_to
        }


class MarketRegimeDetector:
    """
    Market Regime Detector for T01
    
    Detects market regimes (bull, bear, sideways) using:
    - Moving averages (5, 20, 60-day)
    - Price momentum (rate of change)
    - Volatility (ATR)
    - Volume trend
    
    Provides adaptive thresholds for strategy scoring based on current regime.
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        'lookback_days': 60,
        'ma_short': 5,
        'ma_medium': 20,
        'ma_long': 60,
        'volatility_window': 20,
        'momentum_window': 10,
        'volume_window': 20,
        'sideways_threshold': 0.02,  # 2% for sideways detection
        'confidence_threshold': 0.6
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Market Regime Detector
        
        Args:
            config: Configuration dictionary containing API settings and parameters
        """
        self.config = config
        self.api_config = config.get('api', {})
        
        # Load regime-specific config or use defaults
        regime_config = config.get('market_regime', {})
        self.lookback_days = regime_config.get('lookback_days', self.DEFAULT_CONFIG['lookback_days'])
        self.ma_short = regime_config.get('ma_short', self.DEFAULT_CONFIG['ma_short'])
        self.ma_medium = regime_config.get('ma_medium', self.DEFAULT_CONFIG['ma_medium'])
        self.ma_long = regime_config.get('ma_long', self.DEFAULT_CONFIG['ma_long'])
        self.volatility_window = regime_config.get('volatility_window', self.DEFAULT_CONFIG['volatility_window'])
        self.momentum_window = regime_config.get('momentum_window', self.DEFAULT_CONFIG['momentum_window'])
        self.volume_window = regime_config.get('volume_window', self.DEFAULT_CONFIG['volume_window'])
        self.sideways_threshold = regime_config.get('sideways_threshold', self.DEFAULT_CONFIG['sideways_threshold'])
        self.confidence_threshold = regime_config.get('confidence_threshold', self.DEFAULT_CONFIG['confidence_threshold'])
        
        # Initialize Tushare API
        self.token = self.api_config.get('api_key', '')
        if self.token:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        else:
            logger.error("Tushare token not configured")
            self.pro = None
        
        # State tracking
        self.current_regime: MarketRegime = MarketRegime.UNKNOWN
        self.current_confidence: float = 0.0
        self.regime_history: List[Dict[str, Any]] = []
        self.transitions: List[RegimeTransition] = []
        
        logger.info(f"MarketRegimeDetector initialized (lookback={self.lookback_days} days)")
    
    def get_index_data(self, index_code: str, end_date: str, lookback_days: int = None) -> pd.DataFrame:
        """
        Fetch index data from Tushare
        
        Args:
            index_code: Index code (e.g., '000001.SH' for Shanghai, '399001.SZ' for Shenzhen)
            end_date: End date (YYYYMMDD format)
            lookback_days: Number of days to look back (defaults to self.lookback_days)
            
        Returns:
            DataFrame with index data
        """
        if self.pro is None:
            logger.error("Tushare API not initialized")
            return pd.DataFrame()
        
        if lookback_days is None:
            lookback_days = self.lookback_days
        
        try:
            # Calculate start date
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            start_dt = end_dt - timedelta(days=lookback_days + 10)  # Extra days for weekends/holidays
            start_date = start_dt.strftime('%Y%m%d')
            
            # Fetch index daily data
            df = self.pro.index_daily(
                ts_code=index_code,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                logger.warning(f"No data returned for index {index_code}")
                return df
            
            # Sort by date ascending
            df = df.sort_values('trade_date', ascending=True).reset_index(drop=True)
            
            # Ensure numeric columns
            numeric_cols = ['close', 'open', 'high', 'low', 'vol', 'amount']
            for col in numeric_cols:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
            
            logger.debug(f"Fetched {len(df)} days of data for {index_code}")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching index data: {e}")
            return pd.DataFrame()
    
    def _calculate_moving_averages(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate moving averages
        
        Args:
            df: DataFrame with 'close' column
            
        Returns:
            DataFrame with added MA columns
        """
        df = df.copy()
        
        # Calculate MAs
        df[f'ma_{self.ma_short}'] = df['close'].rolling(window=self.ma_short).mean()
        df[f'ma_{self.ma_medium}'] = df['close'].rolling(window=self.ma_medium).mean()
        df[f'ma_{self.ma_long}'] = df['close'].rolling(window=self.ma_long).mean()
        
        # Calculate price relative to MAs
        df['price_to_ma_medium'] = df['close'] / df[f'ma_{self.ma_medium}'] - 1
        
        return df
    
    def _calculate_momentum(self, df: pd.DataFrame, window: int = None) -> pd.DataFrame:
        """
        Calculate price momentum (rate of change)
        
        Args:
            df: DataFrame with 'close' column
            window: Momentum window (defaults to self.momentum_window)
            
        Returns:
            DataFrame with added momentum column
        """
        df = df.copy()
        
        if window is None:
            window = self.momentum_window
        
        # Calculate momentum as rate of change
        df[f'momentum_{window}'] = df['close'].pct_change(periods=window)
        
        return df
    
    def _calculate_volatility(self, df: pd.DataFrame, window: int = 14) -> pd.DataFrame:
        """
        Calculate Average True Range (ATR) as volatility measure
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            window: ATR window
            
        Returns:
            DataFrame with added ATR column
        """
        df = df.copy()
        
        # Calculate True Range
        df['prev_close'] = df['close'].shift(1)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate ATR
        df[f'atr_{window}'] = df['true_range'].rolling(window=window).mean()
        
        # Calculate ATR as percentage of price
        df[f'atr_{window}_pct'] = df[f'atr_{window}'] / df['close']
        
        # Clean up intermediate columns
        df = df.drop(['prev_close', 'tr1', 'tr2', 'tr3', 'true_range'], axis=1)
        
        return df
    
    def _calculate_volume_trend(self, df: pd.DataFrame, window: int = None) -> pd.DataFrame:
        """
        Calculate volume trend indicators
        
        Args:
            df: DataFrame with 'vol' column
            window: Volume MA window (defaults to self.volume_window)
            
        Returns:
            DataFrame with added volume trend columns
        """
        df = df.copy()
        
        if window is None:
            window = self.volume_window
        
        if 'vol' in df.columns:
            # Calculate volume moving average
            df[f'volume_ma_{window}'] = df['vol'].rolling(window=window).mean()
            
            # Calculate volume ratio (current / average)
            df['volume_ratio'] = df['vol'] / df[f'volume_ma_{window}']
            
            # Calculate volume trend (slope of volume MA)
            df['volume_trend'] = df[f'volume_ma_{window}'].pct_change(periods=5)
        
        return df
    
    def _classify_regime(self, latest_data: pd.Series) -> Tuple[MarketRegime, float]:
        """
        Classify market regime based on latest indicators
        
        Args:
            latest_data: Series with calculated indicators for the latest date
            
        Returns:
            Tuple of (MarketRegime, confidence_score)
        """
        # Check if we have required data
        required_cols = [f'ma_{self.ma_medium}', f'momentum_{self.momentum_window}']
        for col in required_cols:
            if col not in latest_data.index or pd.isna(latest_data[col]):
                logger.warning(f"Missing required indicator: {col}")
                return MarketRegime.UNKNOWN, 0.0
        
        # Extract indicators
        price_to_ma = latest_data.get('price_to_ma_medium', 0)
        momentum = latest_data.get(f'momentum_{self.momentum_window}', 0)
        atr_pct = latest_data.get(f'atr_{self.volatility_window}_pct', 0.02)
        volume_ratio = latest_data.get('volume_ratio', 1.0)
        
        # Classification logic
        # BULL: Price above MA20, positive momentum
        # BEAR: Price below MA20, negative momentum
        # SIDEWAYS: Price near MA20, low volatility
        
        bull_score = 0
        bear_score = 0
        sideways_score = 0
        
        # Price relative to MA20
        if price_to_ma > 0.03:  # >3% above MA20
            bull_score += 3
        elif price_to_ma > 0.01:  # >1% above MA20
            bull_score += 2
        elif price_to_ma > 0:  # Above MA20
            bull_score += 1
        elif price_to_ma < -0.03:  # >3% below MA20
            bear_score += 3
        elif price_to_ma < -0.01:  # >1% below MA20
            bear_score += 2
        elif price_to_ma < 0:  # Below MA20
            bear_score += 1
        else:  # Near MA20 (exactly 0)
            sideways_score += 1
        
        # Momentum
        if momentum > 0.05:  # >5% momentum
            bull_score += 3
        elif momentum > 0.02:  # >2% momentum
            bull_score += 2
        elif momentum > 0:  # Positive momentum
            bull_score += 1
        elif momentum < -0.05:  # <-5% momentum
            bear_score += 3
        elif momentum < -0.02:  # <-2% momentum
            bear_score += 2
        elif momentum < 0:  # Negative momentum
            bear_score += 1
        else:  # Zero momentum
            sideways_score += 1
        
        # Volatility (ATR)
        if atr_pct < 0.015:  # Low volatility
            sideways_score += 1
        elif atr_pct > 0.03:  # High volatility
            # High volatility can be in bull or bear
            pass
        
        # Volume confirmation
        if volume_ratio > 1.2:  # Above average volume
            if bull_score > bear_score:
                bull_score += 1
            elif bear_score > bull_score:
                bear_score += 1
        
        # Determine regime based on scores
        max_score = max(bull_score, bear_score, sideways_score)
        total_score = bull_score + bear_score + sideways_score
        
        if total_score == 0:
            return MarketRegime.UNKNOWN, 0.0
        
        confidence = max_score / total_score
        
        # Classification with minimum score threshold
        if bull_score == max_score and bull_score >= 3:
            return MarketRegime.BULL, confidence
        elif bear_score == max_score and bear_score >= 3:
            return MarketRegime.BEAR, confidence
        elif sideways_score == max_score or max_score < 3:
            return MarketRegime.SIDEWAYS, confidence
        else:
            return MarketRegime.UNKNOWN, confidence
    
    def _detect_transition(self, new_regime: MarketRegime, new_confidence: float, 
                          date: str) -> Optional[RegimeTransition]:
        """
        Detect if a regime transition has occurred
        
        Args:
            new_regime: Newly detected regime
            new_confidence: Confidence of new regime
            date: Date string
            
        Returns:
            RegimeTransition if transition detected, None otherwise
        """
        if self.current_regime == MarketRegime.UNKNOWN:
            # First detection, no transition
            return None
        
        if new_regime != self.current_regime:
            transition = RegimeTransition(
                from_regime=self.current_regime,
                to_regime=new_regime,
                date=date,
                confidence_from=self.current_confidence,
                confidence_to=new_confidence
            )
            self.transitions.append(transition)
            logger.info(f"Regime transition detected: {self.current_regime.value} -> {new_regime.value} on {date}")
            return transition
        
        return None
    
    def analyze_regime(self, trade_date: str, index_code: str = '000001.SH') -> Dict[str, Any]:
        """
        Analyze and classify current market regime
        
        Args:
            trade_date: Trade date (YYYYMMDD format)
            index_code: Index code (default: Shanghai Composite)
            
        Returns:
            Dictionary with regime classification and indicators
        """
        try:
            # Fetch index data
            df = self.get_index_data(index_code, trade_date)
            
            if df.empty:
                logger.warning(f"No data available for {index_code} on {trade_date}")
                return {
                    'regime': MarketRegime.UNKNOWN.value,
                    'confidence': 0.0,
                    'date': trade_date,
                    'indicators': {},
                    'error': 'No data available'
                }
            
            # Calculate indicators
            df = self._calculate_moving_averages(df)
            df = self._calculate_momentum(df)
            df = self._calculate_volatility(df, window=self.volatility_window)
            df = self._calculate_volume_trend(df)
            
            # Get latest data
            latest = df.iloc[-1]
            
            # Classify regime
            regime, confidence = self._classify_regime(latest)
            
            # Detect transition
            transition = self._detect_transition(regime, confidence, trade_date)
            
            # Update current state
            self.current_regime = regime
            self.current_confidence = confidence
            
            # Build indicators dict
            indicators = {
                'close': float(latest['close']),
                f'ma_{self.ma_short}': float(latest.get(f'ma_{self.ma_short}', 0)),
                f'ma_{self.ma_medium}': float(latest.get(f'ma_{self.ma_medium}', 0)),
                f'ma_{self.ma_long}': float(latest.get(f'ma_{self.ma_long}', 0)),
                'price_to_ma_medium': float(latest.get('price_to_ma_medium', 0)),
                f'momentum_{self.momentum_window}': float(latest.get(f'momentum_{self.momentum_window}', 0)),
                f'atr_{self.volatility_window}_pct': float(latest.get(f'atr_{self.volatility_window}_pct', 0)),
                'volume_ratio': float(latest.get('volume_ratio', 1.0)),
                'volume_trend': float(latest.get('volume_trend', 0))
            }
            
            # Record in history
            history_entry = {
                'date': trade_date,
                'regime': regime,
                'confidence': confidence,
                'indicators': indicators,
                'index_code': index_code
            }
            self.regime_history.append(history_entry)
            
            # Build result
            result = {
                'regime': regime.value,
                'confidence': confidence,
                'date': trade_date,
                'indicators': indicators,
                'transition': transition.to_dict() if transition else None
            }
            
            logger.info(f"Market regime on {trade_date}: {regime.value} (confidence: {confidence:.2f})")
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing regime: {e}")
            return {
                'regime': MarketRegime.UNKNOWN.value,
                'confidence': 0.0,
                'date': trade_date,
                'indicators': {},
                'error': str(e)
            }
    
    def get_regime_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get summary of regime history
        
        Args:
            days: Number of days to summarize
            
        Returns:
            Dictionary with regime summary statistics
        """
        if not self.regime_history:
            return {
                'current_regime': self.current_regime.value,
                'current_confidence': self.current_confidence,
                'regime_distribution': {},
                'transitions_7d': 0,
                'avg_confidence': 0.0,
                'history_length': 0
            }
        
        # Get recent history
        recent_history = self.regime_history[-days:] if len(self.regime_history) > days else self.regime_history
        
        # Calculate regime distribution
        regime_counts = {}
        for entry in recent_history:
            regime_val = entry['regime'].value if isinstance(entry['regime'], MarketRegime) else entry['regime']
            regime_counts[regime_val] = regime_counts.get(regime_val, 0) + 1
        
        # Calculate average confidence
        avg_confidence = sum(entry['confidence'] for entry in recent_history) / len(recent_history)
        
        # Count recent transitions
        recent_transitions = [t for t in self.transitions if 
                             (datetime.now() - datetime.strptime(t.date, '%Y%m%d')).days <= days]
        
        return {
            'current_regime': self.current_regime.value,
            'current_confidence': self.current_confidence,
            'regime_distribution': regime_counts,
            'transitions_7d': len(recent_transitions),
            'avg_confidence': avg_confidence,
            'history_length': len(self.regime_history)
        }
    
    def _calculate_regime_thresholds(self, regime: MarketRegime, confidence: float) -> Dict[str, Any]:
        """
        Calculate adaptive thresholds based on regime
        
        Args:
            regime: Current market regime
            confidence: Regime confidence score
            
        Returns:
            Dictionary with adaptive thresholds
        """
        # Base thresholds
        base_min_score = 65
        base_position_mult = 1.0
        base_risk_tolerance = 0.5
        
        # Adjust based on regime
        if regime == MarketRegime.BULL:
            # Bull market: lower score threshold, higher position size
            min_score = base_min_score - 10  # 55
            position_mult = base_position_mult * 1.2  # 1.2x
            risk_tolerance = base_risk_tolerance * 0.8  # More strict
        elif regime == MarketRegime.BEAR:
            # Bear market: higher score threshold, lower position size
            min_score = base_min_score + 10  # 75
            position_mult = base_position_mult * 0.6  # 0.6x
            risk_tolerance = base_risk_tolerance * 1.5  # Less strict (more cautious)
        elif regime == MarketRegime.SIDEWAYS:
            # Sideways market: moderate thresholds
            min_score = base_min_score  # 65
            position_mult = base_position_mult * 0.9  # 0.9x
            risk_tolerance = base_risk_tolerance  # Unchanged
        else:
            # Unknown regime: use base thresholds
            min_score = base_min_score
            position_mult = base_position_mult
            risk_tolerance = base_risk_tolerance
        
        # Adjust based on confidence
        confidence_factor = confidence  # 0.0 to 1.0
        
        # Higher confidence = more aggressive adjustment
        if regime == MarketRegime.BULL:
            min_score = min_score - (5 * confidence_factor)
            position_mult = position_mult + (0.2 * confidence_factor)
        elif regime == MarketRegime.BEAR:
            min_score = min_score + (5 * confidence_factor)
            position_mult = position_mult - (0.2 * confidence_factor)
        
        return {
            'min_total_score': round(min_score, 1),
            'position_multiplier': round(position_mult, 2),
            'risk_tolerance': round(risk_tolerance, 2),
            'regime': regime.value,
            'confidence': confidence
        }
    
    def get_adaptive_thresholds(self) -> Dict[str, Any]:
        """
        Get adaptive thresholds for strategy scoring
        
        Returns:
            Dictionary with adaptive thresholds based on current regime
        """
        return self._calculate_regime_thresholds(self.current_regime, self.current_confidence)
    
    def get_regime_history_df(self) -> pd.DataFrame:
        """
        Get regime history as DataFrame
        
        Returns:
            DataFrame with regime history
        """
        if not self.regime_history:
            return pd.DataFrame()
        
        df = pd.DataFrame(self.regime_history)
        
        # Convert regime enum to string
        df['regime'] = df['regime'].apply(lambda x: x.value if isinstance(x, MarketRegime) else x)
        
        return df
    
    def clear_history(self):
        """Clear regime history and transitions"""
        self.regime_history = []
        self.transitions = []
        self.current_regime = MarketRegime.UNKNOWN
        self.current_confidence = 0.0
        logger.info("Regime history cleared")


# Convenience functions for integration with limit_up_strategy_new.py

def get_market_regime(config: Dict[str, Any], trade_date: str, 
                     index_code: str = '000001.SH') -> Dict[str, Any]:
    """
    Convenience function to get market regime for a given date
    
    Args:
        config: Configuration dictionary
        trade_date: Trade date (YYYYMMDD)
        index_code: Index code (default: Shanghai)
        
    Returns:
        Regime analysis result
    """
    detector = MarketRegimeDetector(config)
    return detector.analyze_regime(trade_date, index_code)


def get_adaptive_scoring_params(config: Dict[str, Any], trade_date: str,
                                index_code: str = '000001.SH') -> Dict[str, Any]:
    """
    Convenience function to get adaptive scoring parameters
    
    Args:
        config: Configuration dictionary
        trade_date: Trade date (YYYYMMDD)
        index_code: Index code (default: Shanghai)
        
    Returns:
        Adaptive thresholds for strategy scoring
    """
    detector = MarketRegimeDetector(config)
    detector.analyze_regime(trade_date, index_code)
    return detector.get_adaptive_thresholds()


if __name__ == "__main__":
    # Simple test
    import yaml
    
    # Load config
    try:
        with open('config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
    except FileNotFoundError:
        config = {
            'api': {'api_key': ''},
            'market_regime': {}
        }
    
    # Create detector
    detector = MarketRegimeDetector(config)
    
    # Test with a date
    test_date = '20240301'
    result = detector.analyze_regime(test_date)
    
    print(f"\nMarket Regime Analysis for {test_date}:")
    print(f"Regime: {result['regime']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Indicators: {result.get('indicators', {})}")
    
    # Get adaptive thresholds
    thresholds = detector.get_adaptive_thresholds()
    print(f"\nAdaptive Thresholds:")
    print(f"Min Score: {thresholds['min_total_score']}")
    print(f"Position Multiplier: {thresholds['position_multiplier']}")
    print(f"Risk Tolerance: {thresholds['risk_tolerance']}")
