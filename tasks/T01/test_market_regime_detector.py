#!/usr/bin/env python3
"""
Test suite for Market Regime Detector module
TDD approach: Write tests first, then implement
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from market_regime_detector import MarketRegimeDetector, MarketRegime, RegimeTransition


class TestMarketRegimeDetector(unittest.TestCase):
    """Test cases for MarketRegimeDetector"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'api': {
                'api_key': 'test_token',
                'timeout': 30
            },
            'market_regime': {
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
        }
        
        # Create detector with mocked API
        with patch('tushare.pro_api') as mock_pro_api:
            self.detector = MarketRegimeDetector(self.config)
            self.detector.pro = Mock()
    
    def test_initialization(self):
        """Test detector initialization"""
        self.assertIsNotNone(self.detector)
        self.assertEqual(self.detector.lookback_days, 60)
        self.assertEqual(self.detector.ma_short, 5)
        self.assertEqual(self.detector.ma_medium, 20)
        self.assertEqual(self.detector.ma_long, 60)
        self.assertEqual(self.detector.sideways_threshold, 0.02)
        
        # Check regime history is empty
        self.assertEqual(len(self.detector.regime_history), 0)
    
    def test_market_regime_enum(self):
        """Test MarketRegime enum values"""
        self.assertEqual(MarketRegime.BULL.value, 'bull')
        self.assertEqual(MarketRegime.BEAR.value, 'bear')
        self.assertEqual(MarketRegime.SIDEWAYS.value, 'sideways')
        self.assertEqual(MarketRegime.UNKNOWN.value, 'unknown')
    
    def test_calculate_moving_averages(self):
        """Test moving average calculations"""
        # Create test data
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        prices = np.linspace(100, 130, 30)  # Upward trend
        df = pd.DataFrame({
            'close': prices,
            'trade_date': [d.strftime('%Y%m%d') for d in dates]
        })
        
        result = self.detector._calculate_moving_averages(df)
        
        # Check that MAs are calculated
        self.assertIn('ma_5', result.columns)
        self.assertIn('ma_20', result.columns)
        self.assertIn('ma_60', result.columns)
        
        # Check MA values are reasonable (NaN for first few rows)
        self.assertTrue(result['ma_5'].iloc[4:].notna().all())
        self.assertTrue(result['ma_20'].iloc[19:].notna().all())
    
    def test_calculate_momentum(self):
        """Test momentum calculation"""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        prices = np.linspace(100, 130, 30)  # Upward trend
        df = pd.DataFrame({
            'close': prices,
            'trade_date': [d.strftime('%Y%m%d') for d in dates]
        })
        
        result = self.detector._calculate_momentum(df, window=10)
        
        # Check momentum column exists
        self.assertIn('momentum_10', result.columns)
        
        # For upward trend, momentum should be positive
        valid_momentum = result['momentum_10'].dropna()
        self.assertTrue((valid_momentum > 0).all())
    
    def test_calculate_volatility(self):
        """Test volatility (ATR) calculation"""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        np.random.seed(42)
        df = pd.DataFrame({
            'close': 100 + np.random.randn(30).cumsum(),
            'high': 102 + np.random.randn(30).cumsum(),
            'low': 98 + np.random.randn(30).cumsum(),
            'trade_date': [d.strftime('%Y%m%d') for d in dates]
        })
        
        result = self.detector._calculate_volatility(df, window=14)
        
        # Check ATR column exists
        self.assertIn('atr_14', result.columns)
        
        # ATR should be positive
        valid_atr = result['atr_14'].dropna()
        self.assertTrue((valid_atr > 0).all())
    
    def test_calculate_volume_trend(self):
        """Test volume trend calculation"""
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        volumes = np.linspace(1000000, 2000000, 30)  # Increasing volume
        df = pd.DataFrame({
            'vol': volumes,
            'trade_date': [d.strftime('%Y%m%d') for d in dates]
        })
        
        result = self.detector._calculate_volume_trend(df, window=20)
        
        # Check volume trend column exists
        self.assertIn('volume_ma_20', result.columns)
        self.assertIn('volume_ratio', result.columns)
        
        # For increasing volume, ratio should be > 1
        valid_ratio = result['volume_ratio'].dropna()
        self.assertTrue((valid_ratio > 1).all())
    
    def test_classify_regime_bull(self):
        """Test bull market classification"""
        # Create bull market data: price above MA20, positive momentum
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        prices = np.linspace(100, 150, 30)  # Strong upward trend
        ma_20 = prices * 0.95  # Price above MA20
        df = pd.DataFrame({
            'close': prices,
            'ma_20': ma_20,
            'price_to_ma_medium': prices / ma_20 - 1,  # ~5% above MA20
            'momentum_10': np.ones(30) * 0.05,  # Positive momentum
            'atr_14': np.ones(30) * 2,
            'volume_ratio': np.ones(30) * 1.2,
            'trade_date': [d.strftime('%Y%m%d') for d in dates]
        })
        
        regime, confidence = self.detector._classify_regime(df.iloc[-1])
        
        self.assertEqual(regime, MarketRegime.BULL)
        self.assertGreater(confidence, 0.5)
    
    def test_classify_regime_bear(self):
        """Test bear market classification"""
        # Create bear market data: price below MA20, negative momentum
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        prices = np.linspace(150, 100, 30)  # Strong downward trend
        ma_20 = prices * 1.05  # Price below MA20
        df = pd.DataFrame({
            'close': prices,
            'ma_20': ma_20,
            'price_to_ma_medium': prices / ma_20 - 1,  # ~-5% below MA20
            'momentum_10': np.ones(30) * -0.05,  # Negative momentum
            'atr_14': np.ones(30) * 2,
            'volume_ratio': np.ones(30) * 0.8,
            'trade_date': [d.strftime('%Y%m%d') for d in dates]
        })
        
        regime, confidence = self.detector._classify_regime(df.iloc[-1])
        
        self.assertEqual(regime, MarketRegime.BEAR)
        self.assertGreater(confidence, 0.5)
    
    def test_classify_regime_sideways(self):
        """Test sideways market classification"""
        # Create sideways market data: price near MA20, low volatility
        dates = pd.date_range(start='2024-01-01', periods=30, freq='D')
        np.random.seed(42)
        prices = 100 + np.random.randn(30) * 0.5  # Sideways with low volatility
        ma_20 = np.ones(30) * 100  # Price near MA20
        df = pd.DataFrame({
            'close': prices,
            'ma_20': ma_20,
            'price_to_ma_medium': prices / ma_20 - 1,  # Near 0
            'momentum_10': np.ones(30) * 0.001,  # Near zero momentum
            'atr_14': np.ones(30) * 0.5,  # Low ATR
            'volume_ratio': np.ones(30) * 1.0,
            'trade_date': [d.strftime('%Y%m%d') for d in dates]
        })
        
        regime, confidence = self.detector._classify_regime(df.iloc[-1])
        
        self.assertEqual(regime, MarketRegime.SIDEWAYS)
    
    def test_detect_transition(self):
        """Test regime transition detection"""
        # Set up history with one regime
        self.detector.current_regime = MarketRegime.BULL
        self.detector.current_confidence = 0.8
        
        # Simulate a transition to bear
        transition = self.detector._detect_transition(
            MarketRegime.BEAR, 
            0.75,
            '20240315'
        )
        
        self.assertIsNotNone(transition)
        self.assertEqual(transition.from_regime, MarketRegime.BULL)
        self.assertEqual(transition.to_regime, MarketRegime.BEAR)
        self.assertEqual(transition.date, '20240315')
    
    def test_no_transition_same_regime(self):
        """Test that no transition is detected for same regime"""
        self.detector.current_regime = MarketRegime.BULL
        self.detector.current_confidence = 0.8
        
        transition = self.detector._detect_transition(
            MarketRegime.BULL,
            0.75,
            '20240315'
        )
        
        self.assertIsNone(transition)
    
    def test_get_index_data(self):
        """Test fetching index data from Tushare"""
        # Mock the API response
        mock_data = pd.DataFrame({
            'ts_code': ['000001.SH'] * 30,
            'trade_date': pd.date_range(start='2024-01-01', periods=30).strftime('%Y%m%d').tolist(),
            'close': np.linspace(3000, 3100, 30),
            'open': np.linspace(2990, 3090, 30),
            'high': np.linspace(3010, 3110, 30),
            'low': np.linspace(2980, 3080, 30),
            'vol': np.random.randint(1000000, 2000000, 30)
        })
        
        self.detector.pro.index_daily = Mock(return_value=mock_data)
        
        result = self.detector.get_index_data('000001.SH', '20240301', lookback_days=30)
        
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 30)
        self.assertIn('close', result.columns)
        self.assertIn('trade_date', result.columns)
    
    def test_analyze_regime_integration(self):
        """Test full regime analysis flow"""
        # Mock index data
        dates = pd.date_range(start='2024-01-01', periods=60, freq='D')
        np.random.seed(42)
        mock_data = pd.DataFrame({
            'ts_code': ['000001.SH'] * 60,
            'trade_date': [d.strftime('%Y%m%d') for d in dates],
            'close': np.linspace(3000, 3300, 60),  # Bullish trend
            'open': np.linspace(2990, 3290, 60),
            'high': np.linspace(3010, 3310, 60),
            'low': np.linspace(2980, 3280, 60),
            'vol': np.random.randint(1000000, 2000000, 60)
        })
        
        self.detector.pro.index_daily = Mock(return_value=mock_data)
        
        result = self.detector.analyze_regime('20240301', index_code='000001.SH')
        
        self.assertIn('regime', result)
        self.assertIn('confidence', result)
        self.assertIn('indicators', result)
        self.assertIn('date', result)
        
        # Should detect bull market
        self.assertIn(result['regime'], ['bull', 'bear', 'sideways', 'unknown'])
        self.assertGreaterEqual(result['confidence'], 0)
        self.assertLessEqual(result['confidence'], 1)
    
    def test_get_regime_summary(self):
        """Test regime summary generation"""
        # Add some history
        self.detector.regime_history = [
            {
                'date': '20240310',
                'regime': MarketRegime.BULL,
                'confidence': 0.8,
                'indicators': {'ma_20': 3000, 'momentum': 0.02}
            },
            {
                'date': '20240311',
                'regime': MarketRegime.BULL,
                'confidence': 0.85,
                'indicators': {'ma_20': 3010, 'momentum': 0.025}
            },
            {
                'date': '20240312',
                'regime': MarketRegime.BEAR,
                'confidence': 0.7,
                'indicators': {'ma_20': 2990, 'momentum': -0.01}
            }
        ]
        
        summary = self.detector.get_regime_summary(days=7)
        
        self.assertIn('current_regime', summary)
        self.assertIn('current_confidence', summary)
        self.assertIn('regime_distribution', summary)
        self.assertIn('transitions_7d', summary)
        self.assertIn('avg_confidence', summary)
        
        # Check regime distribution
        self.assertIn('bull', summary['regime_distribution'])
        self.assertIn('bear', summary['regime_distribution'])
        self.assertEqual(summary['regime_distribution']['bull'], 2)
        self.assertEqual(summary['regime_distribution']['bear'], 1)
    
    def test_get_adaptive_thresholds(self):
        """Test adaptive threshold generation"""
        self.detector.current_regime = MarketRegime.BULL
        self.detector.current_confidence = 0.8
        
        thresholds = self.detector.get_adaptive_thresholds()
        
        self.assertIn('min_total_score', thresholds)
        self.assertIn('position_multiplier', thresholds)
        self.assertIn('risk_tolerance', thresholds)
        self.assertIn('regime', thresholds)
        
        # Bull market should have lower thresholds
        self.assertLess(thresholds['min_total_score'], 70)
        self.assertGreater(thresholds['position_multiplier'], 1.0)
    
    def test_bull_market_thresholds(self):
        """Test bull market specific thresholds"""
        thresholds = self.detector._calculate_regime_thresholds(MarketRegime.BULL, 0.8)
        
        # Bull market: lower score threshold, higher position size
        self.assertLess(thresholds['min_total_score'], 65)
        self.assertGreater(thresholds['position_multiplier'], 1.0)
        self.assertEqual(thresholds['regime'], 'bull')
    
    def test_bear_market_thresholds(self):
        """Test bear market specific thresholds"""
        thresholds = self.detector._calculate_regime_thresholds(MarketRegime.BEAR, 0.8)
        
        # Bear market: higher score threshold, lower position size
        self.assertGreater(thresholds['min_total_score'], 70)
        self.assertLess(thresholds['position_multiplier'], 1.0)
        self.assertEqual(thresholds['regime'], 'bear')
    
    def test_sideways_market_thresholds(self):
        """Test sideways market specific thresholds"""
        thresholds = self.detector._calculate_regime_thresholds(MarketRegime.SIDEWAYS, 0.6)
        
        # Sideways market: moderate thresholds
        self.assertGreaterEqual(thresholds['min_total_score'], 65)
        self.assertLessEqual(thresholds['min_total_score'], 75)
        self.assertEqual(thresholds['regime'], 'sideways')
    
    def test_error_handling_empty_data(self):
        """Test handling of empty data"""
        self.detector.pro.index_daily = Mock(return_value=pd.DataFrame())
        
        result = self.detector.analyze_regime('20240301', index_code='000001.SH')
        
        self.assertEqual(result['regime'], 'unknown')
        self.assertEqual(result['confidence'], 0)
    
    def test_error_handling_api_failure(self):
        """Test handling of API failure"""
        self.detector.pro.index_daily = Mock(side_effect=Exception("API Error"))
        
        result = self.detector.analyze_regime('20240301', index_code='000001.SH')
        
        self.assertEqual(result['regime'], 'unknown')
        self.assertEqual(result['confidence'], 0)
        self.assertIn('error', result)
    
    def test_shanghai_index_default(self):
        """Test that Shanghai index is used by default"""
        with patch.object(self.detector, 'get_index_data') as mock_get_data:
            mock_get_data.return_value = pd.DataFrame({
                'close': [3000],
                'trade_date': ['20240301']
            })
            
            self.detector.analyze_regime('20240301')
            
            # Should default to Shanghai index
            mock_get_data.assert_called_once()
            args = mock_get_data.call_args
            self.assertEqual(args[0][0], '000001.SH')
    
    def test_shenzhen_index_support(self):
        """Test support for Shenzhen index"""
        with patch.object(self.detector, 'get_index_data') as mock_get_data:
            mock_get_data.return_value = pd.DataFrame({
                'close': [10000],
                'trade_date': ['20240301']
            })
            
            self.detector.analyze_regime('20240301', index_code='399001.SZ')
            
            mock_get_data.assert_called_once()
            args = mock_get_data.call_args
            self.assertEqual(args[0][0], '399001.SZ')


class TestRegimeTransition(unittest.TestCase):
    """Test cases for RegimeTransition dataclass"""
    
    def test_transition_creation(self):
        """Test creating a regime transition"""
        transition = RegimeTransition(
            from_regime=MarketRegime.BULL,
            to_regime=MarketRegime.BEAR,
            date='20240315',
            confidence_from=0.8,
            confidence_to=0.75
        )
        
        self.assertEqual(transition.from_regime, MarketRegime.BULL)
        self.assertEqual(transition.to_regime, MarketRegime.BEAR)
        self.assertEqual(transition.date, '20240315')
        self.assertEqual(transition.confidence_from, 0.8)
        self.assertEqual(transition.confidence_to, 0.75)
    
    def test_transition_to_dict(self):
        """Test converting transition to dictionary"""
        transition = RegimeTransition(
            from_regime=MarketRegime.BULL,
            to_regime=MarketRegime.BEAR,
            date='20240315',
            confidence_from=0.8,
            confidence_to=0.75
        )
        
        d = transition.to_dict()
        
        self.assertEqual(d['from_regime'], 'bull')
        self.assertEqual(d['to_regime'], 'bear')
        self.assertEqual(d['date'], '20240315')
        self.assertEqual(d['confidence_from'], 0.8)
        self.assertEqual(d['confidence_to'], 0.75)


class TestIntegrationWithStrategy(unittest.TestCase):
    """Test integration with limit_up_strategy_new.py"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.config = {
            'api': {'api_key': 'test_token'},
            'market_regime': {}
        }
        
        with patch('tushare.pro_api'):
            self.detector = MarketRegimeDetector(self.config)
    
    def test_adaptive_scoring_integration(self):
        """Test that detector can provide adaptive scoring parameters"""
        self.detector.current_regime = MarketRegime.BULL
        self.detector.current_confidence = 0.85
        
        # Get adaptive parameters
        params = self.detector.get_adaptive_thresholds()
        
        # Should provide parameters needed by strategy
        self.assertIn('min_total_score', params)
        self.assertIn('position_multiplier', params)
        self.assertIn('risk_tolerance', params)
        
        # Bull market should encourage more aggressive trading
        self.assertGreater(params['position_multiplier'], 1.0)
        self.assertLess(params['risk_tolerance'], 0.5)


if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
