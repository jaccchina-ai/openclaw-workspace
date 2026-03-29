#!/usr/bin/env python3
"""
Tests for Volatility Adjuster Module

TDD Approach:
1. Write tests first (they should fail)
2. Implement the module
3. Run tests (they should pass)
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, Any
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from volatility_adjuster import (
    VolatilityAdjuster,
    VolatilityRegime,
    VolatilityMetrics,
    AdjustmentRecord
)


class TestVolatilityMetrics(unittest.TestCase):
    """Test VolatilityMetrics dataclass"""
    
    def test_metrics_creation(self):
        """Test creating VolatilityMetrics instance"""
        metrics = VolatilityMetrics(
            atr=1.5,
            atr_pct=0.02,
            realized_volatility=0.025,
            historical_percentile=0.65,
            lookback_days=20
        )
        self.assertEqual(metrics.atr, 1.5)
        self.assertEqual(metrics.atr_pct, 0.02)
        self.assertEqual(metrics.realized_volatility, 0.025)
        self.assertEqual(metrics.historical_percentile, 0.65)
        self.assertEqual(metrics.lookback_days, 20)
    
    def test_metrics_to_dict(self):
        """Test conversion to dictionary"""
        metrics = VolatilityMetrics(
            atr=1.5,
            atr_pct=0.02,
            realized_volatility=0.025,
            historical_percentile=0.65,
            lookback_days=20
        )
        d = metrics.to_dict()
        self.assertEqual(d['atr'], 1.5)
        self.assertEqual(d['atr_pct'], 0.02)
        self.assertEqual(d['realized_volatility'], 0.025)
        self.assertEqual(d['historical_percentile'], 0.65)


class TestAdjustmentRecord(unittest.TestCase):
    """Test AdjustmentRecord dataclass"""
    
    def test_record_creation(self):
        """Test creating AdjustmentRecord instance"""
        record = AdjustmentRecord(
            date='20240301',
            base_threshold=65.0,
            adjusted_threshold=58.5,
            volatility_factor=-0.1,
            regime=VolatilityRegime.HIGH,
            metrics=VolatilityMetrics(
                atr=2.0,
                atr_pct=0.03,
                realized_volatility=0.035,
                historical_percentile=0.85,
                lookback_days=20
            )
        )
        self.assertEqual(record.date, '20240301')
        self.assertEqual(record.base_threshold, 65.0)
        self.assertEqual(record.adjusted_threshold, 58.5)
        self.assertEqual(record.volatility_factor, -0.1)
        self.assertEqual(record.regime, VolatilityRegime.HIGH)
    
    def test_record_to_dict(self):
        """Test conversion to dictionary"""
        record = AdjustmentRecord(
            date='20240301',
            base_threshold=65.0,
            adjusted_threshold=58.5,
            volatility_factor=-0.1,
            regime=VolatilityRegime.HIGH,
            metrics=VolatilityMetrics(
                atr=2.0,
                atr_pct=0.03,
                realized_volatility=0.035,
                historical_percentile=0.85,
                lookback_days=20
            )
        )
        d = record.to_dict()
        self.assertEqual(d['date'], '20240301')
        self.assertEqual(d['base_threshold'], 65.0)
        self.assertEqual(d['adjusted_threshold'], 58.5)
        self.assertEqual(d['volatility_factor'], -0.1)
        self.assertEqual(d['regime'], 'high')


class TestVolatilityRegime(unittest.TestCase):
    """Test VolatilityRegime enum"""
    
    def test_regime_values(self):
        """Test regime enum values"""
        self.assertEqual(VolatilityRegime.LOW.value, 'low')
        self.assertEqual(VolatilityRegime.NORMAL.value, 'normal')
        self.assertEqual(VolatilityRegime.HIGH.value, 'high')


class TestVolatilityAdjuster(unittest.TestCase):
    """Test VolatilityAdjuster class"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'api': {
                'api_key': 'test_token',
                'timeout': 30
            },
            'volatility': {
                'lookback_days': 20,
                'atr_window': 14,
                'percentile_window': 252,
                'low_percentile': 0.30,
                'high_percentile': 0.70,
                'high_vol_factor': -0.15,
                'low_vol_factor': 0.10
            }
        }
        self.adjuster = VolatilityAdjuster(self.config)
    
    def test_initialization(self):
        """Test adjuster initialization"""
        self.assertEqual(self.adjuster.lookback_days, 20)
        self.assertEqual(self.adjuster.atr_window, 14)
        self.assertEqual(self.adjuster.percentile_window, 252)
        self.assertEqual(self.adjuster.low_percentile, 0.30)
        self.assertEqual(self.adjuster.high_percentile, 0.70)
        self.assertEqual(self.adjuster.high_vol_factor, -0.15)
        self.assertEqual(self.adjuster.low_vol_factor, 0.10)
        self.assertEqual(len(self.adjuster.adjustment_history), 0)
    
    def test_initialization_with_defaults(self):
        """Test adjuster initialization with default config"""
        config = {'api': {'api_key': 'test'}}
        adjuster = VolatilityAdjuster(config)
        self.assertEqual(adjuster.lookback_days, 20)
        self.assertEqual(adjuster.atr_window, 14)
        self.assertEqual(adjuster.percentile_window, 252)
    
    def test_calculate_atr(self):
        """Test ATR calculation"""
        # Create sample OHLC data
        data = pd.DataFrame({
            'high': [102, 103, 101, 104, 105, 103, 106, 107, 105, 108],
            'low': [98, 99, 97, 100, 101, 99, 102, 103, 101, 104],
            'close': [100, 101, 99, 102, 103, 101, 104, 105, 103, 106]
        })
        
        atr = self.adjuster._calculate_atr(data, window=5)
        
        # ATR should be positive
        self.assertGreater(atr, 0)
        # ATR should be reasonable (based on price range)
        self.assertLess(atr, 10)
    
    def test_calculate_realized_volatility(self):
        """Test realized volatility calculation"""
        # Create sample price data with known volatility
        np.random.seed(42)
        returns = np.random.normal(0, 0.02, 100)  # 2% daily volatility
        prices = 100 * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({'close': prices})
        vol = self.adjuster._calculate_realized_volatility(data, window=20)
        
        # Volatility should be positive
        self.assertGreater(vol, 0)
        # Annualized volatility should be reasonable (between 10% and 50% for typical markets)
        self.assertGreater(vol, 0.10)
        self.assertLess(vol, 0.60)
    
    def test_calculate_historical_percentile(self):
        """Test historical percentile calculation"""
        # Create sample volatility history
        np.random.seed(42)
        vol_history = np.random.normal(0.025, 0.005, 252)
        current_vol = 0.03
        
        percentile = self.adjuster._calculate_historical_percentile(
            current_vol, vol_history
        )
        
        # Percentile should be between 0 and 1
        self.assertGreaterEqual(percentile, 0)
        self.assertLessEqual(percentile, 1)
    
    def test_map_regime_low(self):
        """Test regime mapping for low volatility"""
        regime = self.adjuster._map_regime(0.25)  # Below 30th percentile
        self.assertEqual(regime, VolatilityRegime.LOW)
    
    def test_map_regime_normal(self):
        """Test regime mapping for normal volatility"""
        regime = self.adjuster._map_regime(0.50)  # Between 30th and 70th
        self.assertEqual(regime, VolatilityRegime.NORMAL)
    
    def test_map_regime_high(self):
        """Test regime mapping for high volatility"""
        regime = self.adjuster._map_regime(0.75)  # Above 70th percentile
        self.assertEqual(regime, VolatilityRegime.HIGH)
    
    def test_map_regime_boundary_low(self):
        """Test regime mapping at low boundary (30%)"""
        regime = self.adjuster._map_regime(0.30)
        self.assertEqual(regime, VolatilityRegime.NORMAL)
    
    def test_map_regime_boundary_high(self):
        """Test regime mapping at high boundary (70%)"""
        regime = self.adjuster._map_regime(0.70)
        self.assertEqual(regime, VolatilityRegime.NORMAL)
    
    def test_calculate_volatility_factor_low(self):
        """Test volatility factor for low volatility"""
        factor = self.adjuster._calculate_volatility_factor(VolatilityRegime.LOW)
        self.assertEqual(factor, 0.10)  # Lower thresholds
    
    def test_calculate_volatility_factor_normal(self):
        """Test volatility factor for normal volatility"""
        factor = self.adjuster._calculate_volatility_factor(VolatilityRegime.NORMAL)
        self.assertEqual(factor, 0.0)  # No change
    
    def test_calculate_volatility_factor_high(self):
        """Test volatility factor for high volatility"""
        factor = self.adjuster._calculate_volatility_factor(VolatilityRegime.HIGH)
        self.assertEqual(factor, -0.15)  # Raise thresholds
    
    def test_adjust_threshold_low_volatility(self):
        """Test threshold adjustment for low volatility"""
        base_threshold = 65.0
        adjusted = self.adjuster._adjust_threshold(base_threshold, 0.10)
        expected = base_threshold * (1 + 0.10)  # 71.5
        self.assertAlmostEqual(adjusted, expected, places=2)
    
    def test_adjust_threshold_high_volatility(self):
        """Test threshold adjustment for high volatility"""
        base_threshold = 65.0
        adjusted = self.adjuster._adjust_threshold(base_threshold, -0.15)
        expected = base_threshold * (1 - 0.15)  # 55.25
        self.assertAlmostEqual(adjusted, expected, places=2)
    
    def test_adjust_threshold_normal(self):
        """Test threshold adjustment for normal volatility"""
        base_threshold = 65.0
        adjusted = self.adjuster._adjust_threshold(base_threshold, 0.0)
        self.assertEqual(adjusted, base_threshold)
    
    def test_calculate_volatility_metrics(self):
        """Test calculation of all volatility metrics"""
        # Create sample OHLC data
        np.random.seed(42)
        n = 100
        returns = np.random.normal(0.001, 0.02, n)
        closes = 100 * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({
            'close': closes,
            'high': closes * (1 + np.abs(np.random.normal(0, 0.01, n))),
            'low': closes * (1 - np.abs(np.random.normal(0, 0.01, n)))
        })
        
        metrics = self.adjuster._calculate_volatility_metrics(data)
        
        self.assertIsInstance(metrics, VolatilityMetrics)
        self.assertGreater(metrics.atr, 0)
        self.assertGreater(metrics.atr_pct, 0)
        self.assertGreater(metrics.realized_volatility, 0)
        self.assertGreaterEqual(metrics.historical_percentile, 0)
        self.assertLessEqual(metrics.historical_percentile, 1)
        self.assertEqual(metrics.lookback_days, 20)
    
    def test_get_adjusted_thresholds(self):
        """Test getting adjusted thresholds"""
        # Mock the calculate_volatility_metrics method
        self.adjuster._calculate_volatility_metrics = lambda df: VolatilityMetrics(
            atr=2.0,
            atr_pct=0.03,
            realized_volatility=0.035,
            historical_percentile=0.85,  # High volatility
            lookback_days=20
        )
        
        base_thresholds = {
            'min_total_score': 65.0,
            'position_multiplier': 1.0,
            'risk_tolerance': 0.5
        }
        
        # Create dummy data
        data = pd.DataFrame({
            'close': [100] * 30,
            'high': [102] * 30,
            'low': [98] * 30
        })
        
        result = self.adjuster.get_adjusted_thresholds(
            base_thresholds, data, '20240301'
        )
        
        self.assertIn('base_thresholds', result)
        self.assertIn('adjusted_thresholds', result)
        self.assertIn('volatility_metrics', result)
        self.assertIn('regime', result)
        self.assertIn('volatility_factor', result)
        self.assertIn('date', result)
        
        # High volatility should lower thresholds
        self.assertLess(
            result['adjusted_thresholds']['min_total_score'],
            result['base_thresholds']['min_total_score']
        )
    
    def test_history_tracking(self):
        """Test adjustment history tracking"""
        # Mock the calculate_volatility_metrics method
        self.adjuster._calculate_volatility_metrics = lambda df: VolatilityMetrics(
            atr=2.0,
            atr_pct=0.03,
            realized_volatility=0.035,
            historical_percentile=0.85,
            lookback_days=20
        )
        
        base_thresholds = {'min_total_score': 65.0}
        data = pd.DataFrame({
            'close': [100] * 30,
            'high': [102] * 30,
            'low': [98] * 30
        })
        
        # First adjustment
        self.adjuster.get_adjusted_thresholds(base_thresholds, data, '20240301')
        self.assertEqual(len(self.adjuster.adjustment_history), 1)
        
        # Second adjustment
        self.adjuster.get_adjusted_thresholds(base_thresholds, data, '20240302')
        self.assertEqual(len(self.adjuster.adjustment_history), 2)
        
        # Check history content
        record = self.adjuster.adjustment_history[0]
        self.assertEqual(record.date, '20240301')
        self.assertEqual(record.regime, VolatilityRegime.HIGH)
    
    def test_get_adjustment_history_df(self):
        """Test getting adjustment history as DataFrame"""
        # Mock and add some history
        self.adjuster._calculate_volatility_metrics = lambda df: VolatilityMetrics(
            atr=2.0,
            atr_pct=0.03,
            realized_volatility=0.035,
            historical_percentile=0.85,
            lookback_days=20
        )
        
        base_thresholds = {'min_total_score': 65.0}
        data = pd.DataFrame({
            'close': [100] * 30,
            'high': [102] * 30,
            'low': [98] * 30
        })
        
        self.adjuster.get_adjusted_thresholds(base_thresholds, data, '20240301')
        
        df = self.adjuster.get_adjustment_history_df()
        self.assertIsInstance(df, pd.DataFrame)
        self.assertEqual(len(df), 1)
        self.assertIn('date', df.columns)
        self.assertIn('regime', df.columns)
    
    def test_clear_history(self):
        """Test clearing adjustment history"""
        # Add some history
        self.adjuster._calculate_volatility_metrics = lambda df: VolatilityMetrics(
            atr=2.0,
            atr_pct=0.03,
            realized_volatility=0.035,
            historical_percentile=0.85,
            lookback_days=20
        )
        
        base_thresholds = {'min_total_score': 65.0}
        data = pd.DataFrame({
            'close': [100] * 30,
            'high': [102] * 30,
            'low': [98] * 30
        })
        
        self.adjuster.get_adjusted_thresholds(base_thresholds, data, '20240301')
        self.assertEqual(len(self.adjuster.adjustment_history), 1)
        
        self.adjuster.clear_history()
        self.assertEqual(len(self.adjuster.adjustment_history), 0)
    
    def test_thread_safety(self):
        """Test thread-safe operations"""
        import threading
        import time
        
        self.adjuster._calculate_volatility_metrics = lambda df: VolatilityMetrics(
            atr=2.0,
            atr_pct=0.03,
            realized_volatility=0.035,
            historical_percentile=0.85,
            lookback_days=20
        )
        
        base_thresholds = {'min_total_score': 65.0}
        data = pd.DataFrame({
            'close': [100] * 30,
            'high': [102] * 30,
            'low': [98] * 30
        })
        
        results = []
        
        def worker(date):
            result = self.adjuster.get_adjusted_thresholds(
                base_thresholds, data, date
            )
            results.append(result)
        
        # Run multiple threads
        threads = []
        for i in range(10):
            t = threading.Thread(target=worker, args=(f'202403{i+1:02d}',))
            threads.append(t)
            t.start()
        
        for t in threads:
            t.join()
        
        # All threads should complete successfully
        self.assertEqual(len(results), 10)
        self.assertEqual(len(self.adjuster.adjustment_history), 10)
    
    def test_get_volatility_summary(self):
        """Test getting volatility summary"""
        # Add some history
        self.adjuster._calculate_volatility_metrics = lambda df: VolatilityMetrics(
            atr=2.0,
            atr_pct=0.03,
            realized_volatility=0.035,
            historical_percentile=0.85,
            lookback_days=20
        )
        
        base_thresholds = {'min_total_score': 65.0}
        data = pd.DataFrame({
            'close': [100] * 30,
            'high': [102] * 30,
            'low': [98] * 30
        })
        
        for i in range(5):
            self.adjuster.get_adjusted_thresholds(
                base_thresholds, data, f'202403{i+1:02d}'
            )
        
        summary = self.adjuster.get_volatility_summary(days=7)
        
        self.assertIn('current_regime', summary)
        self.assertIn('current_volatility_factor', summary)
        self.assertIn('regime_distribution', summary)
        self.assertIn('adjustment_count', summary)
        self.assertIn('avg_adjustment_magnitude', summary)
        self.assertEqual(summary['adjustment_count'], 5)


class TestIntegration(unittest.TestCase):
    """Integration tests for VolatilityAdjuster"""
    
    def test_full_workflow(self):
        """Test complete volatility adjustment workflow"""
        config = {
            'api': {'api_key': 'test'},
            'volatility': {
                'lookback_days': 20,
                'high_vol_factor': -0.15,
                'low_vol_factor': 0.10
            }
        }
        
        adjuster = VolatilityAdjuster(config)
        
        # Create realistic market data
        np.random.seed(42)
        n = 100
        
        # Simulate high volatility period
        returns = np.random.normal(0.001, 0.035, n)  # 3.5% daily vol
        closes = 100 * np.exp(np.cumsum(returns))
        
        data = pd.DataFrame({
            'close': closes,
            'high': closes * (1 + np.abs(np.random.normal(0, 0.015, n))),
            'low': closes * (1 - np.abs(np.random.normal(0, 0.015, n)))
        })
        
        base_thresholds = {
            'min_total_score': 65.0,
            'position_multiplier': 1.0,
            'risk_tolerance': 0.5
        }
        
        result = adjuster.get_adjusted_thresholds(
            base_thresholds, data, '20240301'
        )
        
        # Verify structure
        self.assertIn('adjusted_thresholds', result)
        self.assertIn('volatility_metrics', result)
        self.assertIn('regime', result)
        
        # Verify metrics
        metrics = result['volatility_metrics']
        self.assertIsInstance(metrics, VolatilityMetrics)
        self.assertGreater(metrics.atr, 0)
        self.assertGreater(metrics.realized_volatility, 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
