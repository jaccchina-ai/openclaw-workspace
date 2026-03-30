#!/usr/bin/env python3
"""
Adaptive Threshold Manager Module - T01 Phase 3

Manages adaptive thresholds based on market regime and historical performance.
"""

import os
import sys
import json
import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """市场状态枚举"""
    BULL = "bull"
    BEAR = "bear"
    SIDEWAYS = "sideways"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    UNKNOWN = "unknown"


@dataclass
class ThresholdConfiguration:
    """阈值配置数据类"""
    entry_threshold: float
    exit_threshold: float
    stop_loss: float
    take_profit: float
    position_size: float
    regime: MarketRegime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entry_threshold': self.entry_threshold,
            'exit_threshold': self.exit_threshold,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'position_size': self.position_size,
            'regime': self.regime.value
        }


@dataclass
class TradeRecord:
    """交易记录数据类"""
    date: str
    stock_code: str
    entry_score: float
    exit_score: float
    pnl_pct: float
    win: bool
    regime: str
    threshold_used: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'date': self.date,
            'stock_code': self.stock_code,
            'entry_score': self.entry_score,
            'exit_score': self.exit_score,
            'pnl_pct': self.pnl_pct,
            'win': self.win,
            'regime': self.regime,
            'threshold_used': self.threshold_used
        }


@dataclass
class PerformanceMetrics:
    """绩效指标数据类"""
    win_rate: float
    profit_factor: float
    max_drawdown: float
    sharpe_ratio: float
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    lookback_days: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'max_drawdown': self.max_drawdown,
            'sharpe_ratio': self.sharpe_ratio,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'lookback_days': self.lookback_days
        }


class AdaptiveThresholdManager:
    """
    自适应阈值管理器
    
    职责:
    1. 根据市场状态调整阈值
    2. 基于历史绩效反馈优化阈值
    3. 管理多目标优化
    """
    
    DEFAULT_THRESHOLDS = {
        MarketRegime.BULL: {
            'entry': 65.0,
            'exit': 70.0,
            'stop_loss': 0.05,
            'take_profit': 0.15,
            'position_size': 0.25
        },
        MarketRegime.BEAR: {
            'entry': 75.0,
            'exit': 80.0,
            'stop_loss': 0.03,
            'take_profit': 0.08,
            'position_size': 0.15
        },
        MarketRegime.SIDEWAYS: {
            'entry': 70.0,
            'exit': 75.0,
            'stop_loss': 0.04,
            'take_profit': 0.10,
            'position_size': 0.20
        },
        MarketRegime.HIGH_VOLATILITY: {
            'entry': 72.0,
            'exit': 78.0,
            'stop_loss': 0.06,
            'take_profit': 0.12,
            'position_size': 0.15
        },
        MarketRegime.LOW_VOLATILITY: {
            'entry': 68.0,
            'exit': 72.0,
            'stop_loss': 0.03,
            'take_profit': 0.08,
            'position_size': 0.25
        },
        MarketRegime.UNKNOWN: {
            'entry': 70.0,
            'exit': 75.0,
            'stop_loss': 0.04,
            'take_profit': 0.10,
            'position_size': 0.20
        }
    }
    
    def __init__(self, config_path: str = 'config.yaml',
                 market_regime_detector=None):
        """
        初始化自适应阈值管理器
        
        Args:
            config_path: 配置文件路径
            market_regime_detector: 市场状态检测器
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        threshold_config = self.config.get('adaptive_thresholds', {})
        self.base_entry = threshold_config.get('base_entry', 70.0)
        self.base_exit = threshold_config.get('base_exit', 75.0)
        self.adjustment_step = threshold_config.get('adjustment_step', 2.0)
        self.max_adjustment = threshold_config.get('max_adjustment', 10.0)
        
        self.market_regime_detector = market_regime_detector
        
        # 当前阈值
        self.current_thresholds = self._load_current_thresholds()
        
        # 交易历史
        self.trade_history_file = Path('state/adaptive_trade_history.json')
        self.trade_history_file.parent.mkdir(parents=True, exist_ok=True)
        self.trade_history = self._load_trade_history()
        
        logger.info("AdaptiveThresholdManager初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"加载配置失败: {e}，使用默认配置")
            return {}
    
    def _load_current_thresholds(self) -> Dict[str, float]:
        """加载当前阈值"""
        threshold_file = Path('state/current_thresholds.json')
        if threshold_file.exists():
            try:
                with open(threshold_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载阈值失败: {e}")
        
        return {
            'entry': self.base_entry,
            'exit': self.base_exit,
            'stop_loss': 0.04,
            'take_profit': 0.10,
            'position_size': 0.20
        }
    
    def _save_current_thresholds(self):
        """保存当前阈值"""
        try:
            threshold_file = Path('state/current_thresholds.json')
            with open(threshold_file, 'w', encoding='utf-8') as f:
                json.dump(self.current_thresholds, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存阈值失败: {e}")
    
    def _load_trade_history(self) -> List[Dict[str, Any]]:
        """加载交易历史"""
        if self.trade_history_file.exists():
            try:
                with open(self.trade_history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载交易历史失败: {e}")
        return []
    
    def _save_trade_history(self):
        """保存交易历史"""
        try:
            with open(self.trade_history_file, 'w', encoding='utf-8') as f:
                json.dump(self.trade_history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存交易历史失败: {e}")
    
    def detect_market_regime(self) -> MarketRegime:
        """
        检测当前市场状态
        
        Returns:
            市场状态
        """
        if self.market_regime_detector:
            try:
                regime = self.market_regime_detector.detect()
                return MarketRegime(regime)
            except Exception as e:
                logger.warning(f"市场状态检测失败: {e}")
        
        # 默认返回未知状态
        return MarketRegime.UNKNOWN
    
    def update_thresholds(self, force: bool = False) -> Dict[str, Any]:
        """
        更新阈值
        
        Args:
            force: 是否强制更新
            
        Returns:
            更新结果
        """
        logger.info("开始更新自适应阈值...")
        
        try:
            # 1. 检测市场状态
            regime = self.detect_market_regime()
            
            # 2. 获取基准阈值
            base_thresholds = self.DEFAULT_THRESHOLDS.get(regime, self.DEFAULT_THRESHOLDS[MarketRegime.UNKNOWN])
            
            # 3. 基于历史绩效调整
            performance_adjustments = self._calculate_performance_adjustments()
            
            # 4. 应用调整
            new_thresholds = {
                'entry': base_thresholds['entry'] + performance_adjustments.get('entry', 0),
                'exit': base_thresholds['exit'] + performance_adjustments.get('exit', 0),
                'stop_loss': base_thresholds['stop_loss'] + performance_adjustments.get('stop_loss', 0),
                'take_profit': base_thresholds['take_profit'] + performance_adjustments.get('take_profit', 0),
                'position_size': base_thresholds['position_size'] + performance_adjustments.get('position_size', 0)
            }
            
            # 5. 限制调整范围
            new_thresholds['entry'] = np.clip(new_thresholds['entry'], 50, 90)
            new_thresholds['exit'] = np.clip(new_thresholds['exit'], 55, 95)
            new_thresholds['stop_loss'] = np.clip(new_thresholds['stop_loss'], 0.01, 0.10)
            new_thresholds['take_profit'] = np.clip(new_thresholds['take_profit'], 0.05, 0.20)
            new_thresholds['position_size'] = np.clip(new_thresholds['position_size'], 0.10, 0.30)
            
            # 6. 保存新阈值
            old_thresholds = self.current_thresholds.copy()
            self.current_thresholds = new_thresholds
            self._save_current_thresholds()
            
            logger.info(f"阈值已更新: 入场 {old_thresholds['entry']:.1f} -> {new_thresholds['entry']:.1f}")
            
            return {
                'success': True,
                'adjusted': True,
                'regime': regime.value,
                'old_thresholds': old_thresholds,
                'new_thresholds': new_thresholds,
                'adjustments': performance_adjustments
            }
            
        except Exception as e:
            logger.error(f"更新阈值失败: {e}")
            return {
                'success': False,
                'adjusted': False,
                'error': str(e)
            }
    
    def _calculate_performance_adjustments(self) -> Dict[str, float]:
        """
        基于绩效计算调整
        
        Returns:
            调整值字典
        """
        adjustments = {
            'entry': 0,
            'exit': 0,
            'stop_loss': 0,
            'take_profit': 0,
            'position_size': 0
        }
        
        if len(self.trade_history) < 20:
            return adjustments
        
        # 计算近期绩效
        recent_trades = self.trade_history[-50:]
        wins = [t for t in recent_trades if t.get('win', False)]
        win_rate = len(wins) / len(recent_trades) if recent_trades else 0
        
        # 根据胜率调整入场阈值
        if win_rate < 0.40:
            adjustments['entry'] = self.adjustment_step  # 提高入场标准
        elif win_rate > 0.60:
            adjustments['entry'] = -self.adjustment_step  # 降低入场标准
        
        # 根据盈亏调整仓位
        total_pnl = sum(t.get('pnl_pct', 0) for t in recent_trades)
        if total_pnl < 0:
            adjustments['position_size'] = -0.05  # 减少仓位
        elif total_pnl > 0.10:
            adjustments['position_size'] = 0.02  # 增加仓位
        
        return adjustments
    
    def get_current_thresholds(self, regime: MarketRegime = None) -> Dict[str, float]:
        """
        获取当前阈值
        
        Args:
            regime: 市场状态，None表示使用当前检测的状态
            
        Returns:
            当前阈值
        """
        if regime:
            base = self.DEFAULT_THRESHOLDS.get(regime, self.DEFAULT_THRESHOLDS[MarketRegime.UNKNOWN])
            return {
                'entry': base['entry'],
                'exit': base['exit'],
                'stop_loss': base['stop_loss'],
                'take_profit': base['take_profit'],
                'position_size': base['position_size']
            }
        
        return self.current_thresholds.copy()
    
    def record_trade(self, trade: TradeRecord):
        """
        记录交易
        
        Args:
            trade: 交易记录
        """
        self.trade_history.append(trade.to_dict())
        
        # 只保留最近500条
        if len(self.trade_history) > 500:
            self.trade_history = self.trade_history[-500:]
        
        self._save_trade_history()
    
    def calculate_performance_metrics(self, lookback_days: int = 30) -> PerformanceMetrics:
        """
        计算绩效指标
        
        Args:
            lookback_days: 回看天数
            
        Returns:
            绩效指标
        """
        cutoff_date = (datetime.now() - timedelta(days=lookback_days)).strftime('%Y%m%d')
        recent_trades = [t for t in self.trade_history if t.get('date', '') >= cutoff_date]
        
        if not recent_trades:
            return PerformanceMetrics(
                win_rate=0, profit_factor=0, max_drawdown=0, sharpe_ratio=0,
                total_trades=0, winning_trades=0, losing_trades=0,
                avg_win=0, avg_loss=0, lookback_days=lookback_days
            )
        
        wins = [t for t in recent_trades if t.get('win', False)]
        losses = [t for t in recent_trades if not t.get('win', False)]
        
        win_rate = len(wins) / len(recent_trades)
        
        total_win = sum(t.get('pnl_pct', 0) for t in wins)
        total_loss = abs(sum(t.get('pnl_pct', 0) for t in losses))
        profit_factor = total_win / total_loss if total_loss > 0 else float('inf')
        
        avg_win = total_win / len(wins) if wins else 0
        avg_loss = total_loss / len(losses) if losses else 0
        
        # 简化夏普比率计算
        pnls = [t.get('pnl_pct', 0) for t in recent_trades]
        sharpe = np.mean(pnls) / np.std(pnls) if np.std(pnls) > 0 else 0
        
        # 简化最大回撤计算
        cumulative = np.cumsum(pnls)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / (running_max + 1e-10)
        max_dd = abs(np.min(drawdown)) if len(drawdown) > 0 else 0
        
        return PerformanceMetrics(
            win_rate=win_rate,
            profit_factor=profit_factor,
            max_drawdown=max_dd,
            sharpe_ratio=sharpe,
            total_trades=len(recent_trades),
            winning_trades=len(wins),
            losing_trades=len(losses),
            avg_win=avg_win,
            avg_loss=avg_loss,
            lookback_days=lookback_days
        )


def main():
    """测试函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Adaptive Threshold Manager 模块测试")
    print("="*60)
    
    manager = AdaptiveThresholdManager()
    
    # 测试获取当前阈值
    print("\n1. 测试获取当前阈值...")
    thresholds = manager.get_current_thresholds()
    print(f"   入场阈值: {thresholds['entry']}")
    print(f"   出场阈值: {thresholds['exit']}")
    print(f"   仓位大小: {thresholds['position_size']}")
    
    # 测试更新阈值
    print("\n2. 测试更新阈值...")
    result = manager.update_thresholds()
    print(f"   成功: {result['success']}")
    print(f"   市场状态: {result.get('regime', 'unknown')}")
    
    # 测试绩效计算
    print("\n3. 测试绩效计算...")
    metrics = manager.calculate_performance_metrics()
    print(f"   胜率: {metrics.win_rate:.2%}")
    print(f"   盈亏比: {metrics.profit_factor:.2f}")
    print(f"   夏普比率: {metrics.sharpe_ratio:.2f}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == '__main__':
    main()
