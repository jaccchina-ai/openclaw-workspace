#!/usr/bin/env python3
"""
Volatility Adjuster Module for T01 Phase 3

This module calculates market volatility metrics and provides threshold scaling
based on volatility regimes. It implements the adaptive threshold component
of the T01 Phase 3 evolution.

Features:
- ATR (Average True Range) calculation
- Realized volatility (standard deviation of returns)
- Historical volatility percentiles
- Threshold scaling based on volatility regimes
- Thread-safe adjustment history tracking

Integration Points:
- Used by adaptive_threshold_manager.py
- Integrates with limit_up_strategy_new.py
- Uses Tushare API for market data (000001.SH)

Author: T01 Phase 3 Evolution System
Date: 2026-03-30
"""

import pandas as pd
import numpy as np
import tushare as ts
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import logging
import threading

logger = logging.getLogger(__name__)


class VolatilityRegime(Enum):
    """
    Volatility regime enumeration
    
    LOW: < 30th percentile - Lower thresholds (less selective)
    NORMAL: 30th - 70th percentile - No adjustment
    HIGH: > 70th percentile - Higher thresholds (more selective)
    """
    LOW = 'low'
    NORMAL = 'normal'
    HIGH = 'high'


@dataclass
class VolatilityMetrics:
    """
    Container for volatility metrics
    
    Attributes:
        atr: Average True Range (absolute value)
        atr_pct: ATR as percentage of price
        realized_volatility: Standard deviation of returns (annualized)
        historical_percentile: Percentile rank in historical context (0-1)
        lookback_days: Number of days used for calculation
    """
    atr: float
    atr_pct: float
    realized_volatility: float
    historical_percentile: float
    lookback_days: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'atr': self.atr,
            'atr_pct': self.atr_pct,
            'realized_volatility': self.realized_volatility,
            'historical_percentile': self.historical_percentile,
            'lookback_days': self.lookback_days
        }


@dataclass
class AdjustmentRecord:
    """
    Record of a threshold adjustment event
    
    Attributes:
        date: Date string (YYYYMMDD)
        base_threshold: Original threshold value
        adjusted_threshold: Adjusted threshold value
        volatility_factor: Applied volatility factor
        regime: Volatility regime at time of adjustment
        metrics: Volatility metrics used for adjustment
    """
    date: str
    base_threshold: float
    adjusted_threshold: float
    volatility_factor: float
    regime: VolatilityRegime
    metrics: VolatilityMetrics
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert record to dictionary"""
        return {
            'date': self.date,
            'base_threshold': self.base_threshold,
            'adjusted_threshold': self.adjusted_threshold,
            'volatility_factor': self.volatility_factor,
            'regime': self.regime.value,
            'metrics': self.metrics.to_dict()
        }


class VolatilityAdjuster:
    """
    Volatility Adjuster for T01 Strategy
    
    Calculates market volatility metrics and adjusts scoring thresholds
    based on current volatility regime:
    
    - High volatility -> Lower thresholds (more selective)
    - Low volatility -> Higher thresholds (less selective)
    
    Uses Shanghai Composite Index (000001.SH) as market proxy.
    
    Thread-safe for concurrent access.
    """
    
    # Default configuration
    DEFAULT_CONFIG = {
        'lookback_days': 20,
        'atr_window': 14,
        'percentile_window': 252,  # 1 year of trading days
        'low_percentile': 0.30,    # 30th percentile
        'high_percentile': 0.70,   # 70th percentile
        'high_vol_factor': -0.15,  # -15% adjustment for high vol
        'low_vol_factor': 0.10,    # +10% adjustment for low vol
    }
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the Volatility Adjuster
        
        Args:
            config: Configuration dictionary containing API settings and parameters
        """
        self.config = config
        self.api_config = config.get('api', {})
        
        # Load volatility-specific config or use defaults
        vol_config = config.get('volatility', {})
        self.lookback_days = vol_config.get('lookback_days', self.DEFAULT_CONFIG['lookback_days'])
        self.atr_window = vol_config.get('atr_window', self.DEFAULT_CONFIG['atr_window'])
        self.percentile_window = vol_config.get('percentile_window', self.DEFAULT_CONFIG['percentile_window'])
        self.low_percentile = vol_config.get('low_percentile', self.DEFAULT_CONFIG['low_percentile'])
        self.high_percentile = vol_config.get('high_percentile', self.DEFAULT_CONFIG['high_percentile'])
        self.high_vol_factor = vol_config.get('high_vol_factor', self.DEFAULT_CONFIG['high_vol_factor'])
        self.low_vol_factor = vol_config.get('low_vol_factor', self.DEFAULT_CONFIG['low_vol_factor'])
        
        # Initialize Tushare API
        self.token = self.api_config.get('api_key', '')
        if self.token:
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        else:
            logger.error("Tushare token not configured")
            self.pro = None
        
        # State tracking
        self.current_regime: VolatilityRegime = VolatilityRegime.NORMAL
        self.current_volatility_factor: float = 0.0
        self.current_metrics: Optional[VolatilityMetrics] = None
        self.adjustment_history: List[AdjustmentRecord] = []
        
        # Thread safety
        self._lock = threading.Lock()
        
        logger.info(f"VolatilityAdjuster initialized (lookback={self.lookback_days} days, "
                   f"low_pct={self.low_percentile}, high_pct={self.high_percentile})")
    
    def get_index_data(self, index_code: str = '000001.SH', 
                       end_date: Optional[str] = None,
                       lookback_days: int = None) -> pd.DataFrame:
        """
        Fetch index data from Tushare
        
        Args:
            index_code: Index code (default: '000001.SH' for Shanghai Composite)
            end_date: End date (YYYYMMDD format, default: today)
            lookback_days: Number of days to look back (defaults to self.lookback_days + buffer)
            
        Returns:
            DataFrame with index data (open, high, low, close, vol, amount)
        """
        if self.pro is None:
            logger.error("Tushare API not initialized")
            return pd.DataFrame()
        
        if lookback_days is None:
            lookback_days = self.lookback_days + self.percentile_window
        
        if end_date is None:
            end_date = datetime.now().strftime('%Y%m%d')
        
        try:
            # Calculate start date
            end_dt = datetime.strptime(end_date, '%Y%m%d')
            start_dt = end_dt - timedelta(days=lookback_days + 20)  # Extra for weekends/holidays
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
    
    def _calculate_atr(self, df: pd.DataFrame, window: int = None) -> float:
        """
        Calculate Average True Range (ATR)
        
        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            window: ATR window (defaults to self.atr_window)
            
        Returns:
            ATR value (absolute)
        """
        if window is None:
            window = self.atr_window
        
        if len(df) < window + 1:
            logger.warning(f"Insufficient data for ATR calculation: {len(df)} < {window + 1}")
            return 0.0
        
        # Calculate True Range
        df = df.copy()
        df['prev_close'] = df['close'].shift(1)
        df['tr1'] = df['high'] - df['low']
        df['tr2'] = abs(df['high'] - df['prev_close'])
        df['tr3'] = abs(df['low'] - df['prev_close'])
        df['true_range'] = df[['tr1', 'tr2', 'tr3']].max(axis=1)
        
        # Calculate ATR using Wilder's smoothing
        atr_series = df['true_range'].ewm(alpha=1/window, min_periods=window).mean()
        
        return float(atr_series.iloc[-1])
    
    def _calculate_realized_volatility(self, df: pd.DataFrame, 
                                       window: int = None) -> float:
        """
        Calculate realized volatility (standard deviation of returns)
        
        Args:
            df: DataFrame with 'close' column
            window: Volatility window (defaults to self.lookback_days)
            
        Returns:
            Realized volatility (annualized)
        """
        if window is None:
            window = self.lookback_days
        
        if len(df) < window + 1:
            logger.warning(f"Insufficient data for volatility calculation: {len(df)} < {window + 1}")
            return 0.0
        
        # Calculate daily returns
        returns = df['close'].pct_change().dropna()
        
        if len(returns) < window:
            logger.warning(f"Insufficient returns data: {len(returns)} < {window}")
            return 0.0
        
        # Calculate standard deviation of returns
        daily_vol = returns.tail(window).std()
        
        # Annualize (252 trading days)
        annualized_vol = daily_vol * np.sqrt(252)
        
        return float(annualized_vol)
    
    def _calculate_historical_percentile(self, current_vol: float,
                                          vol_history: np.ndarray) -> float:
        """
        Calculate percentile rank of current volatility in historical context
        
        Args:
            current_vol: Current volatility value
            vol_history: Array of historical volatility values
            
        Returns:
            Percentile rank (0-1)
        """
        if len(vol_history) == 0:
            return 0.5  # Default to middle
        
        # Calculate percentile
        percentile = np.sum(vol_history <= current_vol) / len(vol_history)
        
        return float(percentile)
    
    def _map_regime(self, percentile: float) -> VolatilityRegime:
        """
        Map volatility percentile to regime
        
        Args:
            percentile: Volatility percentile (0-1)
            
        Returns:
            VolatilityRegime enum value
        """
        if percentile < self.low_percentile:
            return VolatilityRegime.LOW
        elif percentile > self.high_percentile:
            return VolatilityRegime.HIGH
        else:
            return VolatilityRegime.NORMAL
    
    def _calculate_volatility_factor(self, regime: VolatilityRegime) -> float:
        """
        Calculate volatility adjustment factor based on regime
        
        Args:
            regime: Current volatility regime
            
        Returns:
            Volatility factor for threshold adjustment
        """
        if regime == VolatilityRegime.HIGH:
            return self.high_vol_factor  # Negative: lower thresholds
        elif regime == VolatilityRegime.LOW:
            return self.low_vol_factor   # Positive: raise thresholds
        else:
            return 0.0  # No adjustment for normal regime
    
    def _adjust_threshold(self, base_threshold: float, 
                          volatility_factor: float) -> float:
        """
        Adjust threshold based on volatility factor
        
        Formula: new_threshold = base_threshold * (1 + volatility_factor)
        
        Args:
            base_threshold: Original threshold value
            volatility_factor: Volatility adjustment factor
            
        Returns:
            Adjusted threshold value
        """
        return base_threshold * (1 + volatility_factor)
    
    def _calculate_volatility_metrics(self, df: pd.DataFrame) -> VolatilityMetrics:
        """
        Calculate all volatility metrics from price data
        
        Args:
            df: DataFrame with OHLC data
            
        Returns:
            VolatilityMetrics object
        """
        # Calculate ATR
        atr = self._calculate_atr(df, window=self.atr_window)
        
        # Calculate ATR as percentage of current price
        current_price = df['close'].iloc[-1]
        atr_pct = atr / current_price if current_price > 0 else 0
        
        # Calculate realized volatility
        realized_vol = self._calculate_realized_volatility(df, window=self.lookback_days)
        
        # Calculate historical volatility for percentile
        if len(df) >= self.percentile_window + self.lookback_days:
            # Calculate rolling volatility history
            returns = df['close'].pct_change().dropna()
            rolling_vol = returns.rolling(window=self.lookback_days).std() * np.sqrt(252)
            vol_history = rolling_vol.dropna().values
            
            # Calculate percentile
            historical_percentile = self._calculate_historical_percentile(
                realized_vol, vol_history
            )
        else:
            # Insufficient history, use default
            historical_percentile = 0.5
            logger.warning(f"Insufficient data for historical percentile: {len(df)} days")
        
        return VolatilityMetrics(
            atr=atr,
            atr_pct=atr_pct,
            realized_volatility=realized_vol,
            historical_percentile=historical_percentile,
            lookback_days=self.lookback_days
        )
    
    def calculate_volatility(self, trade_date: str, 
                            index_code: str = '000001.SH') -> VolatilityMetrics:
        """
        Calculate current volatility metrics for a given date
        
        Args:
            trade_date: Trade date (YYYYMMDD format)
            index_code: Index code (default: Shanghai Composite)
            
        Returns:
            VolatilityMetrics object
        """
        # Fetch index data
        df = self.get_index_data(index_code, end_date=trade_date)
        
        if df.empty:
            logger.warning(f"No data available for {index_code} on {trade_date}")
            return VolatilityMetrics(
                atr=0.0,
                atr_pct=0.0,
                realized_volatility=0.0,
                historical_percentile=0.5,
                lookback_days=self.lookback_days
            )
        
        # Calculate metrics
        metrics = self._calculate_volatility_metrics(df)
        
        with self._lock:
            self.current_metrics = metrics
        
        logger.info(f"Volatility metrics for {trade_date}: "
                   f"ATR={metrics.atr:.2f} ({metrics.atr_pct*100:.2f}%), "
                   f"RealizedVol={metrics.realized_volatility*100:.2f}%, "
                   f"Percentile={metrics.historical_percentile*100:.1f}%")
        
        return metrics
    
    def get_adjusted_thresholds(self, base_thresholds: Dict[str, float],
                                market_data: pd.DataFrame = None,
                                trade_date: str = None,
                                index_code: str = '000001.SH') -> Dict[str, Any]:
        """
        Get volatility-adjusted thresholds
        
        Args:
            base_thresholds: Dictionary of base threshold values
            market_data: Optional pre-fetched market data DataFrame
            trade_date: Trade date (YYYYMMDD, default: today)
            index_code: Index code for market data
            
        Returns:
            Dictionary with adjusted thresholds and metadata
        """
        if trade_date is None:
            trade_date = datetime.now().strftime('%Y%m%d')
        
        # Get market data if not provided
        if market_data is None or market_data.empty:
            market_data = self.get_index_data(index_code, end_date=trade_date)
        
        if market_data.empty:
            logger.warning("No market data available, using base thresholds")
            return {
                'date': trade_date,
                'base_thresholds': base_thresholds,
                'adjusted_thresholds': base_thresholds.copy(),
                'volatility_metrics': None,
                'regime': VolatilityRegime.NORMAL.value,
                'volatility_factor': 0.0,
                'error': 'No market data available'
            }
        
        # Calculate volatility metrics
        metrics = self._calculate_volatility_metrics(market_data)
        
        # Determine regime
        regime = self._map_regime(metrics.historical_percentile)
        
        # Calculate volatility factor
        volatility_factor = self._calculate_volatility_factor(regime)
        
        # Adjust thresholds
        adjusted_thresholds = {}
        for key, value in base_thresholds.items():
            if isinstance(value, (int, float)):
                adjusted_thresholds[key] = self._adjust_threshold(value, volatility_factor)
            else:
                adjusted_thresholds[key] = value
        
        # Record adjustment
        record = AdjustmentRecord(
            date=trade_date,
            base_threshold=base_thresholds.get('min_total_score', 0),
            adjusted_threshold=adjusted_thresholds.get('min_total_score', 0),
            volatility_factor=volatility_factor,
            regime=regime,
            metrics=metrics
        )
        
        with self._lock:
            self.adjustment_history.append(record)
            self.current_regime = regime
            self.current_volatility_factor = volatility_factor
            self.current_metrics = metrics
        
        logger.info(f"Threshold adjustment for {trade_date}: "
                   f"regime={regime.value}, factor={volatility_factor:.2%}")
        
        return {
            'date': trade_date,
            'base_thresholds': base_thresholds,
            'adjusted_thresholds': adjusted_thresholds,
            'volatility_metrics': metrics,
            'regime': regime.value,
            'volatility_factor': volatility_factor
        }
    
    def get_adjustment_history_df(self) -> pd.DataFrame:
        """
        Get adjustment history as DataFrame
        
        Returns:
            DataFrame with adjustment history
        """
        with self._lock:
            if not self.adjustment_history:
                return pd.DataFrame()
            
            records = [r.to_dict() for r in self.adjustment_history]
            df = pd.DataFrame(records)
            
            # Expand metrics columns
            if 'metrics' in df.columns:
                metrics_df = pd.json_normalize(df['metrics'])
                metrics_df.columns = [f'metrics_{c}' for c in metrics_df.columns]
                df = pd.concat([df.drop('metrics', axis=1), metrics_df], axis=1)
            
            return df
    
    def get_volatility_summary(self, days: int = 30) -> Dict[str, Any]:
        """
        Get summary of volatility history
        
        Args:
            days: Number of days to summarize
            
        Returns:
            Dictionary with volatility summary statistics
        """
        with self._lock:
            if not self.adjustment_history:
                return {
                    'current_regime': self.current_regime.value,
                    'current_volatility_factor': self.current_volatility_factor,
                    'regime_distribution': {},
                    'adjustment_count': 0,
                    'avg_adjustment_magnitude': 0.0
                }
            
            # Get recent history
            recent_history = self.adjustment_history[-days:] if len(self.adjustment_history) > days else self.adjustment_history
            
            # Calculate regime distribution
            regime_counts = {}
            for record in recent_history:
                regime_val = record.regime.value
                regime_counts[regime_val] = regime_counts.get(regime_val, 0) + 1
            
            # Calculate average adjustment magnitude
            avg_magnitude = sum(abs(r.volatility_factor) for r in recent_history) / len(recent_history)
            
            return {
                'current_regime': self.current_regime.value,
                'current_volatility_factor': self.current_volatility_factor,
                'regime_distribution': regime_counts,
                'adjustment_count': len(recent_history),
                'avg_adjustment_magnitude': round(avg_magnitude, 4)
            }
    
    def clear_history(self):
        """Clear adjustment history"""
        with self._lock:
            self.adjustment_history = []
            self.current_regime = VolatilityRegime.NORMAL
            self.current_volatility_factor = 0.0
            self.current_metrics = None
        logger.info("Adjustment history cleared")


# Convenience functions for integration with limit_up_strategy_new.py

def get_volatility_adjusted_thresholds(config: Dict[str, Any],
                                       base_thresholds: Dict[str, float],
                                       trade_date: str,
                                       index_code: str = '000001.SH') -> Dict[str, Any]:
    """
    Convenience function to get volatility-adjusted thresholds
    
    Args:
        config: Configuration dictionary
        base_thresholds: Base threshold values
        trade_date: Trade date (YYYYMMDD)
        index_code: Index code (default: Shanghai)
        
    Returns:
        Dictionary with adjusted thresholds and metadata
    """
    adjuster = VolatilityAdjuster(config)
    return adjuster.get_adjusted_thresholds(base_thresholds, trade_date=trade_date, index_code=index_code)


def get_current_volatility_regime(config: Dict[str, Any],
                                  trade_date: str,
                                  index_code: str = '000001.SH') -> Dict[str, Any]:
    """
    Convenience function to get current volatility regime
    
    Args:
        config: Configuration dictionary
        trade_date: Trade date (YYYYMMDD)
        index_code: Index code (default: Shanghai)
        
    Returns:
        Dictionary with regime information
    """
    adjuster = VolatilityAdjuster(config)
    metrics = adjuster.calculate_volatility(trade_date, index_code)
    regime = adjuster._map_regime(metrics.historical_percentile)
    factor = adjuster._calculate_volatility_factor(regime)
    
    return {
        'regime': regime.value,
        'volatility_factor': factor,
        'metrics': metrics.to_dict(),
        'date': trade_date
    }


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
            'volatility': {}
        }
    
    # Create adjuster
    adjuster = VolatilityAdjuster(config)
    
    # Test with a date
    test_date = '20240301'
    metrics = adjuster.calculate_volatility(test_date)
    
    print(f"\nVolatility Analysis for {test_date}:")
    print(f"ATR: {metrics.atr:.2f} ({metrics.atr_pct*100:.2f}%)")
    print(f"Realized Volatility: {metrics.realized_volatility*100:.2f}%")
    print(f"Historical Percentile: {metrics.historical_percentile*100:.1f}%")
    
    # Test threshold adjustment
    base_thresholds = {
        'min_total_score': 65.0,
        'position_multiplier': 1.0,
        'risk_tolerance': 0.5
    }
    
    result = adjuster.get_adjusted_thresholds(base_thresholds, trade_date=test_date)
    
    print(f"\nThreshold Adjustment:")
    print(f"Regime: {result['regime']}")
    print(f"Volatility Factor: {result['volatility_factor']:.2%}")
    print(f"Base Min Score: {result['base_thresholds']['min_total_score']}")
    print(f"Adjusted Min Score: {result['adjusted_thresholds']['min_total_score']:.1f}")
