#!/usr/bin/env python3
"""
Evolution Trigger模块 - 系统进化触发器

用于T01 Phase 3全自动闭环系统，监控系统绩效和因子有效性，
智能判断何时需要触发系统进化。
"""

import os
import sys
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
from enum import Enum
import numpy as np

logger = logging.getLogger(__name__)


class TriggerType(Enum):
    """触发类型枚举"""
    PERFORMANCE_DROP = "performance_drop"
    IC_DECAY = "ic_decay"
    DRAWDOWN_EXCEED = "drawdown_exceed"
    PROFIT_FACTOR_DECLINE = "profit_factor_decline"
    SCHEDULED = "scheduled"
    MANUAL = "manual"
    SUDDEN_CHANGE = "sudden_change"


@dataclass
class TriggerCondition:
    """触发条件数据类"""
    name: str
    trigger_type: TriggerType
    threshold: float
    operator: str
    weight: float = 1.0
    description: str = ""
    enabled: bool = True
    
    def evaluate(self, value: float) -> bool:
        """评估条件是否触发"""
        if not self.enabled:
            return False
        
        if self.operator == "<":
            return value < self.threshold
        elif self.operator == ">":
            return value > self.threshold
        elif self.operator == "<=":
            return value <= self.threshold
        elif self.operator == ">=":
            return value >= self.threshold
        elif self.operator == "==":
            return value == self.threshold
        else:
            logger.warning(f"未知的操作符: {self.operator}")
            return False
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'trigger_type': self.trigger_type.value,
            'threshold': self.threshold,
            'operator': self.operator,
            'weight': self.weight,
            'description': self.description,
            'enabled': self.enabled
        }


@dataclass
class TriggerResult:
    """触发结果数据类"""
    triggered: bool
    trigger_type: Optional[TriggerType]
    confidence: float
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    severity: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'triggered': self.triggered,
            'trigger_type': self.trigger_type.value.upper() if self.trigger_type else None,
            'confidence': round(self.confidence, 4),
            'message': self.message,
            'details': self.details,
            'timestamp': self.timestamp.isoformat(),
            'severity': round(self.severity, 4)
        }


@dataclass
class PerformanceMetrics:
    """绩效指标数据类"""
    date: str
    win_rate: float = 0.0
    profit_factor: float = 0.0
    max_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    total_trades: int = 0
    avg_return: float = 0.0
    
    @staticmethod
    def calculate_trend(metrics_list: List['PerformanceMetrics'], 
                       metric_name: str) -> Dict[str, Any]:
        """计算指标趋势"""
        if len(metrics_list) < 2:
            return {"direction": "stable", "days": 0, "change_pct": 0.0}
        
        values = [getattr(m, metric_name) for m in metrics_list if hasattr(m, metric_name)]
        
        if len(values) < 2:
            return {"direction": "stable", "days": 0, "change_pct": 0.0}
        
        direction = "stable"
        days = 0
        
        for i in range(len(values) - 1, 0, -1):
            if values[i] < values[i - 1]:
                if direction in ["stable", "declining"]:
                    direction = "declining"
                    days += 1
                else:
                    break
            elif values[i] > values[i - 1]:
                if direction in ["stable", "increasing"]:
                    direction = "increasing"
                    days += 1
                else:
                    break
            else:
                break
        
        if len(values) >= 2 and values[0] != 0:
            change_pct = (values[-1] - values[0]) / abs(values[0]) * 100
        else:
            change_pct = 0.0
        
        return {
            "direction": direction,
            "days": days,
            "change_pct": round(change_pct, 2)
        }


@dataclass
class ICMetrics:
    """IC指标数据类"""
    factor_name: str
    ic_value: float
    ic_window_20: Optional[float] = None
    ic_window_60: Optional[float] = None
    is_valid: bool = True
    trend: str = "stable"
    trend_days: int = 0


class TriggerHistory:
    """触发历史管理类"""
    
    def __init__(self, history_file: str = None):
        """初始化触发历史"""
        if history_file is None:
            data_dir = Path("data/evolution_trigger")
            data_dir.mkdir(parents=True, exist_ok=True)
            self.history_file = data_dir / "trigger_history.json"
        else:
            self.history_file = Path(history_file)
            self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.records = self._load_history()
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """加载历史记录"""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载触发历史失败: {e}")
        return []
    
    def _save_history(self):
        """保存历史记录"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.records, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存触发历史失败: {e}")
    
    def add_record(self, result: TriggerResult, evolution_executed: bool = False,
                   execution_result: str = None):
        """添加触发记录"""
        record = {
            'timestamp': result.timestamp.isoformat(),
            'triggered': result.triggered,
            'trigger_type': result.trigger_type.value.upper() if result.trigger_type else None,
            'confidence': round(result.confidence, 4),
            'message': result.message,
            'details': result.details,
            'severity': round(result.severity, 4),
            'evolution_executed': evolution_executed,
            'execution_result': execution_result
        }
        
        self.records.append(record)
        
        # 只保留最近365天的记录
        cutoff_date = datetime.now() - timedelta(days=365)
        self.records = [
            r for r in self.records 
            if datetime.fromisoformat(r['timestamp']) > cutoff_date
        ]
        
        self._save_history()
    
    def get_records(self, days: int = 30, 
                   trigger_type: TriggerType = None) -> List[Dict[str, Any]]:
        """获取历史记录"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        filtered = [
            r for r in self.records
            if datetime.fromisoformat(r['timestamp']) > cutoff_date
        ]
        
        if trigger_type:
            filtered = [
                r for r in filtered 
                if r.get('trigger_type') == trigger_type.value
            ]
        
        return filtered
    
    def get_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取统计信息"""
        records = self.get_records(days)
        
        if not records:
            return {
                "total_triggers": 0,
                "evolution_executed": 0,
                "avg_confidence": 0.0,
                "by_type": {},
                "execution_rate": 0.0
            }
        
        triggered_records = [r for r in records if r.get('triggered', False)]
        executed_count = sum(1 for r in triggered_records if r.get('evolution_executed', False))
        
        by_type = {}
        for r in triggered_records:
            t_type = r.get('trigger_type', 'unknown')
            by_type[t_type] = by_type.get(t_type, 0) + 1
        
        confidences = [r.get('confidence', 0) for r in triggered_records if r.get('confidence')]
        avg_confidence = np.mean(confidences) if confidences else 0.0
        
        return {
            "total_triggers": len(triggered_records),
            "evolution_executed": executed_count,
            "avg_confidence": round(avg_confidence, 4),
            "by_type": by_type,
            "execution_rate": round(executed_count / len(triggered_records), 4) if triggered_records else 0.0
        }


class EvolutionTrigger:
    """进化触发器主类"""
    
    DEFAULT_THRESHOLDS = {
        'win_rate': 40.0,
        'ic_value': 0.03,
        'max_drawdown': 20.0,
        'profit_factor': 1.0,
    }
    
    DEFAULT_ROLLING_WINDOWS = {
        'short': 20,
        'long': 60,
    }
    
    def __init__(self, config_path: str = 'config.yaml',
                 performance_tracker=None,
                 ic_monitor=None):
        """初始化进化触发器"""
        self.config = self._load_config(config_path)
        
        trigger_config = self.config.get('evolution_trigger', {})
        self.thresholds = trigger_config.get('thresholds', self.DEFAULT_THRESHOLDS)
        self.rolling_windows = trigger_config.get('rolling_windows', self.DEFAULT_ROLLING_WINDOWS)
        
        multi_config = trigger_config.get('multi_condition', {})
        self.multi_condition_enabled = multi_config.get('enabled', True)
        self.min_conditions_for_trigger = multi_config.get('min_conditions', 2)
        self.confidence_threshold = multi_config.get('confidence_threshold', 0.7)
        
        sudden_config = trigger_config.get('sudden_change', {})
        self.sudden_change_enabled = sudden_config.get('enabled', True)
        self.win_rate_change_threshold = sudden_config.get('win_rate_change_threshold', 10.0)
        self.drawdown_change_threshold = sudden_config.get('drawdown_change_threshold', 5.0)
        
        scheduled_config = trigger_config.get('scheduled', {})
        self.weekly_trigger = scheduled_config.get('weekly', True)
        self.weekly_day = scheduled_config.get('weekly_day', 0)
        self.monthly_trigger = scheduled_config.get('monthly', True)
        self.monthly_day = scheduled_config.get('monthly_day', 1)
        
        self.performance_tracker = performance_tracker
        self.ic_monitor = ic_monitor
        
        self.performance_history: List[PerformanceMetrics] = []
        self._load_performance_history()
        
        history_file = trigger_config.get('history_file')
        self.trigger_history = TriggerHistory(history_file)
        
        self._init_trigger_conditions()
        
        logger.info("进化触发器初始化完成")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}，使用默认配置")
            return {
                'evolution_trigger': {
                    'thresholds': self.DEFAULT_THRESHOLDS,
                    'rolling_windows': self.DEFAULT_ROLLING_WINDOWS
                }
            }
    
    def _init_trigger_conditions(self):
        """初始化触发条件"""
        self.trigger_conditions = [
            TriggerCondition(
                name="win_rate_drop",
                trigger_type=TriggerType.PERFORMANCE_DROP,
                threshold=self.thresholds.get('win_rate', 40.0),
                operator="<",
                weight=1.0,
                description=f"胜率低于{self.thresholds.get('win_rate', 40.0)}%"
            ),
            TriggerCondition(
                name="ic_decay",
                trigger_type=TriggerType.IC_DECAY,
                threshold=self.thresholds.get('ic_value', 0.03),
                operator="<",
                weight=0.9,
                description=f"IC值低于{self.thresholds.get('ic_value', 0.03)}"
            ),
            TriggerCondition(
                name="drawdown_exceed",
                trigger_type=TriggerType.DRAWDOWN_EXCEED,
                threshold=self.thresholds.get('max_drawdown', 20.0),
                operator=">",
                weight=1.0,
                description=f"最大回撤超过{self.thresholds.get('max_drawdown', 20.0)}%"
            ),
            TriggerCondition(
                name="profit_factor_decline",
                trigger_type=TriggerType.PROFIT_FACTOR_DECLINE,
                threshold=self.thresholds.get('profit_factor', 1.0),
                operator="<",
                weight=0.8,
                description=f"盈亏因子低于{self.thresholds.get('profit_factor', 1.0)}"
            ),
        ]
    
    def _load_performance_history(self):
        """加载绩效历史"""
        data_dir = Path("data/evolution_trigger")
        history_file = data_dir / "performance_history.json"
        
        if history_file.exists():
            try:
                with open(history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.performance_history = [
                        PerformanceMetrics(**m) for m in data
                    ]
            except Exception as e:
                logger.warning(f"加载绩效历史失败: {e}")
    
    def _save_performance_history(self):
        """保存绩效历史"""
        data_dir = Path("data/evolution_trigger")
        data_dir.mkdir(parents=True, exist_ok=True)
        history_file = data_dir / "performance_history.json"
        
        try:
            data = [asdict(m) for m in self.performance_history]
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存绩效历史失败: {e}")
    
    def _get_current_performance(self) -> Optional[PerformanceMetrics]:
        """获取当前绩效指标"""
        if self.performance_tracker is None:
            logger.warning("绩效跟踪器未设置")
            return None
        
        try:
            perf_data = self.performance_tracker.calculate_portfolio_performance()
            
            if not perf_data or 'summary' not in perf_data:
                return None
            
            summary = perf_data['summary']
            
            metrics = PerformanceMetrics(
                date=datetime.now().strftime("%Y%m%d"),
                win_rate=summary.get('win_rate_pct', 0.0),
                profit_factor=summary.get('profit_factor', 0.0),
                max_drawdown=summary.get('max_drawdown_pct', 0.0),
                sharpe_ratio=summary.get('sharpe_ratio', 0.0),
                total_trades=summary.get('total_trades', 0),
                avg_return=summary.get('avg_return_pct', 0.0)
            )
            
            self.performance_history.append(metrics)
            if len(self.performance_history) > 90:
                self.performance_history = self.performance_history[-90:]
            self._save_performance_history()
            
            return metrics
            
        except Exception as e:
            logger.error(f"获取当前绩效失败: {e}")
            return None
    
    def _get_current_ic_metrics(self) -> List[ICMetrics]:
        """获取当前IC指标"""
        if self.ic_monitor is None:
            logger.warning("IC监控器未设置")
            return []
        
        try:
            report = self.ic_monitor.get_latest_report()
            
            if not report or not hasattr(report, 'factors'):
                return []
            
            ic_metrics = []
            for factor in report.factors:
                ic_metrics.append(ICMetrics(
                    factor_name=factor.factor_name,
                    ic_value=factor.ic_value,
                    ic_window_20=factor.ic_window_20,
                    ic_window_60=factor.ic_window_60,
                    is_valid=factor.is_valid,
                    trend=factor.trend,
                    trend_days=factor.trend_days
                ))
            
            return ic_metrics
            
        except Exception as e:
            logger.error(f"获取IC指标失败: {e}")
            return []
    
    def _check_performance_drop(self) -> TriggerResult:
        """检查绩效下降条件"""
        metrics = self._get_current_performance()
        
        if metrics is None:
            return TriggerResult(
                triggered=False,
                trigger_type=None,
                confidence=0.0,
                message="无法获取绩效数据",
                details={},
                timestamp=datetime.now()
            )
        
        condition = self.trigger_conditions[0]
        triggered = condition.evaluate(metrics.win_rate)
        
        if triggered:
            severity = min(1.0, (condition.threshold - metrics.win_rate) / condition.threshold)
            confidence = min(1.0, severity + 0.5)
            message = f"胜率下降至{metrics.win_rate:.1f}%，低于阈值{condition.threshold}%"
            
            return TriggerResult(
                triggered=True,
                trigger_type=TriggerType.PERFORMANCE_DROP,
                confidence=confidence,
                message=message,
                details={
                    'win_rate': metrics.win_rate,
                    'threshold': condition.threshold,
                    'total_trades': metrics.total_trades,
                    'profit_factor': metrics.profit_factor,
                    'max_drawdown': metrics.max_drawdown
                },
                timestamp=datetime.now(),
                severity=severity
            )
        
        return TriggerResult(
            triggered=False,
            trigger_type=None,
            confidence=0.0,
            message="绩效正常",
            details={'win_rate': metrics.win_rate},
            timestamp=datetime.now()
        )
    
    def _check_ic_decay(self) -> TriggerResult:
        """检查IC衰减条件"""
        ic_metrics = self._get_current_ic_metrics()
        
        if not ic_metrics:
            return TriggerResult(
                triggered=False,
                trigger_type=None,
                confidence=0.0,
                message="无法获取IC数据",
                details={},
                timestamp=datetime.now()
            )
        
        condition = self.trigger_conditions[1]
        invalid_factors = [ic for ic in ic_metrics if not ic.is_valid]
        invalid_ratio = len(invalid_factors) / len(ic_metrics) if ic_metrics else 0
        triggered = invalid_ratio > 0.3 or len(invalid_factors) >= 3
        
        if triggered:
            severity = min(1.0, invalid_ratio * 2)
            confidence = min(1.0, severity + 0.4)
            message = f"{len(invalid_factors)}个因子失效 ({invalid_ratio*100:.1f}%)，IC值低于阈值{condition.threshold}"
            
            return TriggerResult(
                triggered=True,
                trigger_type=TriggerType.IC_DECAY,
                confidence=confidence,
                message=message,
                details={
                    'invalid_factors': [ic.factor_name for ic in invalid_factors],
                    'invalid_ratio': invalid_ratio,
                    'threshold': condition.threshold,
                    'total_factors': len(ic_metrics)
                },
                timestamp=datetime.now(),
                severity=severity
            )
        
        return TriggerResult(
            triggered=False,
            trigger_type=None,
            confidence=0.0,
            message="IC指标正常",
            details={
                'total_factors': len(ic_metrics),
                'invalid_factors': len(invalid_factors)
            },
            timestamp=datetime.now()
        )
    
    def _check_drawdown_exceed(self) -> TriggerResult:
        """检查回撤超限条件"""
        metrics = self._get_current_performance()
        
        if metrics is None:
            return TriggerResult(
                triggered=False,
                trigger_type=None,
                confidence=0.0,
                message="无法获取绩效数据",
                details={},
                timestamp=datetime.now()
            )
        
        condition = self.trigger_conditions[2]
        triggered = condition.evaluate(metrics.max_drawdown)
        
        if triggered:
            severity = min(1.0, metrics.max_drawdown / condition.threshold - 1)
            confidence = min(1.0, severity + 0.6)
            message = f"最大回撤达到{metrics.max_drawdown:.1f}%，超过阈值{condition.threshold}%"
            
            return TriggerResult(
                triggered=True,
                trigger_type=TriggerType.DRAWDOWN_EXCEED,
                confidence=confidence,
                message=message,
                details={
                    'max_drawdown': metrics.max_drawdown,
                    'threshold': condition.threshold,
                    'win_rate': metrics.win_rate
                },
                timestamp=datetime.now(),
                severity=severity
            )
        
        return TriggerResult(
            triggered=False,
            trigger_type=None,
            confidence=0.0,
            message="回撤正常",
            details={'max_drawdown': metrics.max_drawdown},
            timestamp=datetime.now()
        )
    
    def _check_profit_factor_decline(self) -> TriggerResult:
        """检查盈亏因子下降条件"""
        metrics = self._get_current_performance()
        
        if metrics is None:
            return TriggerResult(
                triggered=False,
                trigger_type=None,
                confidence=0.0,
                message="无法获取绩效数据",
                details={},
                timestamp=datetime.now()
            )
        
        condition = self.trigger_conditions[3]
        triggered = condition.evaluate(metrics.profit_factor)
        
        if triggered:
            severity = min(1.0, 1.0 - metrics.profit_factor)
            confidence = min(1.0, severity + 0.5)
            message = f"盈亏因子下降至{metrics.profit_factor:.2f}，低于阈值{condition.threshold}"
            
            return TriggerResult(
                triggered=True,
                trigger_type=TriggerType.PROFIT_FACTOR_DECLINE,
                confidence=confidence,
                message=message,
                details={
                    'profit_factor': metrics.profit_factor,
                    'threshold': condition.threshold,
                    'win_rate': metrics.win_rate
                },
                timestamp=datetime.now(),
                severity=severity
            )
        
        return TriggerResult(
            triggered=False,
            trigger_type=None,
            confidence=0.0,
            message="盈亏因子正常",
            details={'profit_factor': metrics.profit_factor},
            timestamp=datetime.now()
        )
    
    def _check_scheduled_trigger(self) -> TriggerResult:
        """检查定时触发条件"""
        now = datetime.now()
        
        if self.weekly_trigger and now.weekday() == self.weekly_day:
            return TriggerResult(
                triggered=True,
                trigger_type=TriggerType.SCHEDULED,
                confidence=0.5,
                message=f"每周定时触发 (星期{self.weekly_day + 1})",
                details={'schedule': 'weekly', 'day': self.weekly_day},
                timestamp=now,
                severity=0.3
            )
        
        if self.monthly_trigger and now.day == self.monthly_day:
            return TriggerResult(
                triggered=True,
                trigger_type=TriggerType.SCHEDULED,
                confidence=0.5,
                message=f"每月定时触发 ({self.monthly_day}日)",
                details={'schedule': 'monthly', 'day': self.monthly_day},
                timestamp=now,
                severity=0.3
            )
        
        return TriggerResult(
            triggered=False,
            trigger_type=None,
            confidence=0.0,
            message="非定时触发时间",
            details={},
            timestamp=now
        )
    
    def _calculate_rolling_metrics(self, window: int = 20) -> Dict[str, Any]:
        """计算滚动窗口指标"""
        if len(self.performance_history) < window:
            window = len(self.performance_history)
        
        if window < 5:
            return {
                'win_rate': {'mean': 0.0, 'std': 0.0, 'trend': 'stable'},
                'profit_factor': {'mean': 0.0, 'std': 0.0, 'trend': 'stable'},
                'max_drawdown': {'mean': 0.0, 'std': 0.0, 'trend': 'stable'},
                'trend_direction': 'stable'
            }
        
        recent = self.performance_history[-window:]
        win_rates = [m.win_rate for m in recent]
        profit_factors = [m.profit_factor for m in recent]
        drawdowns = [m.max_drawdown for m in recent]
        win_rate_trend = PerformanceMetrics.calculate_trend(recent, 'win_rate')
        
        return {
            'win_rate': {
                'mean': round(np.mean(win_rates), 2),
                'std': round(np.std(win_rates), 2),
                'trend': win_rate_trend['direction'],
                'trend_days': win_rate_trend['days'],
                'change_pct': win_rate_trend['change_pct']
            },
            'profit_factor': {
                'mean': round(np.mean(profit_factors), 2),
                'std': round(np.std(profit_factors), 2)
            },
            'max_drawdown': {
                'mean': round(np.mean(drawdowns), 2),
                'std': round(np.std(drawdowns), 2)
            },
            'trend_direction': win_rate_trend['direction']
        }
    
    def _detect_sudden_change(self) -> List[Dict[str, Any]]:
        """检测绩效突变"""
        sudden_changes = []
        
        if len(self.performance_history) < 3:
            return sudden_changes
        
        recent = self.performance_history[-3:]
        
        if len(recent) >= 3:
            prev_win_rate = recent[-2].win_rate
            curr_win_rate = recent[-1].win_rate
            
            if prev_win_rate > 0:
                win_rate_change = abs(curr_win_rate - prev_win_rate)
                if win_rate_change > self.win_rate_change_threshold:
                    sudden_changes.append({
                        'metric': 'win_rate',
                        'change': round(curr_win_rate - prev_win_rate, 2),
                        'change_pct': round(win_rate_change, 2),
                        'threshold': self.win_rate_change_threshold,
                        'severity': min(1.0, win_rate_change / self.win_rate_change_threshold - 1)
                    })
        
        if len(recent) >= 3:
            prev_drawdown = recent[-2].max_drawdown
            curr_drawdown = recent[-1].max_drawdown
            drawdown_change = curr_drawdown - prev_drawdown
            
            if drawdown_change > self.drawdown_change_threshold:
                sudden_changes.append({
                    'metric': 'max_drawdown',
                    'change': round(drawdown_change, 2),
                    'threshold': self.drawdown_change_threshold,
                    'severity': min(1.0, drawdown_change / self.drawdown_change_threshold - 1)
                })
        
        return sudden_changes
    
    def _calculate_confidence_score(self, triggered_conditions: List[Dict[str, Any]]) -> float:
        """计算置信度分数"""
        if not triggered_conditions:
            return 0.0
        
        base_confidence = 0.5
        severity_sum = sum(c.get('severity', 0.5) for c in triggered_conditions)
        avg_severity = severity_sum / len(triggered_conditions)
        count_bonus = min(0.3, (len(triggered_conditions) - 1) * 0.1)
        confidence = base_confidence + avg_severity * 0.3 + count_bonus
        
        return min(1.0, confidence)
    
    def _record_trigger(self, result: TriggerResult):
        """记录触发结果"""
        self.trigger_history.add_record(result)
    
    def evaluate(self, use_multi_condition: bool = True) -> Dict[str, Any]:
        """评估是否触发进化"""
        triggered_conditions = []
        all_results = []
        
        checks = [
            ("performance_drop", self._check_performance_drop()),
            ("ic_decay", self._check_ic_decay()),
            ("drawdown_exceed", self._check_drawdown_exceed()),
            ("profit_factor_decline", self._check_profit_factor_decline()),
            ("scheduled", self._check_scheduled_trigger()),
        ]
        
        for name, result in checks:
            all_results.append((name, result))
            
            if result.triggered:
                triggered_conditions.append({
                    'name': name,
                    'type': result.trigger_type,
                    'severity': result.severity,
                    'confidence': result.confidence,
                    'message': result.message
                })
        
        sudden_changes = self._detect_sudden_change()
        if sudden_changes:
            for change in sudden_changes:
                triggered_conditions.append({
                    'name': 'sudden_change',
                    'type': TriggerType.SUDDEN_CHANGE,
                    'severity': change.get('severity', 0.5),
                    'confidence': 0.6,
                    'message': f"绩效突变: {change.get('metric')}变化{change.get('change', 0):.2f}"
                })
        
        should_evolve = False
        trigger_type = None
        confidence = 0.0
        message = ""
        
        if use_multi_condition and self.multi_condition_enabled:
            if len(triggered_conditions) >= self.min_conditions_for_trigger:
                should_evolve = True
                confidence = self._calculate_confidence_score(triggered_conditions)
                trigger_type = TriggerType.PERFORMANCE_DROP
                message = f"多条件触发: {len(triggered_conditions)}个条件满足"
        else:
            critical_triggers = [c for c in triggered_conditions 
                               if c['type'] in [TriggerType.PERFORMANCE_DROP, 
                                              TriggerType.DRAWDOWN_EXCEED]]
            if critical_triggers:
                should_evolve = True
                trigger_type = critical_triggers[0]['type']
                confidence = critical_triggers[0]['confidence']
                message = critical_triggers[0]['message']
        
        if should_evolve and confidence >= self.confidence_threshold:
            result = TriggerResult(
                triggered=True,
                trigger_type=trigger_type,
                confidence=confidence,
                message=message,
                details={
                    'triggered_conditions': triggered_conditions,
                    'rolling_metrics': self._calculate_rolling_metrics()
                },
                timestamp=datetime.now(),
                severity=max(c.get('severity', 0.5) for c in triggered_conditions) if triggered_conditions else 0.5
            )
            self._record_trigger(result)
            
            return {
                'should_evolve': True,
                'trigger_type': trigger_type,
                'confidence': confidence,
                'message': message,
                'triggered_conditions': triggered_conditions,
                'timestamp': datetime.now().isoformat()
            }
        
        return {
            'should_evolve': False,
            'trigger_type': None,
            'confidence': 0.0,
            'message': "未达到进化触发条件",
            'triggered_conditions': [],
            'timestamp': datetime.now().isoformat()
        }
    
    def manual_trigger(self, reason: str = "", triggered_by: str = "admin") -> Dict[str, Any]:
        """手动触发进化"""
        result = TriggerResult(
            triggered=True,
            trigger_type=TriggerType.MANUAL,
            confidence=1.0,
            message=f"手动触发: {reason}" if reason else "手动触发进化",
            details={
                'triggered_by': triggered_by,
                'reason': reason
            },
            timestamp=datetime.now(),
            severity=0.5
        )
        self._record_trigger(result)
        
        return {
            'should_evolve': True,
            'trigger_type': TriggerType.MANUAL,
            'confidence': 1.0,
            'message': result.message,
            'reason': reason,
            'triggered_by': triggered_by,
            'timestamp': datetime.now().isoformat()
        }
    
    def get_trigger_history(self, days: int = 30) -> List[Dict[str, Any]]:
        """获取触发历史"""
        return self.trigger_history.get_records(days)
    
    def get_trigger_statistics(self, days: int = 30) -> Dict[str, Any]:
        """获取触发统计信息"""
        return self.trigger_history.get_statistics(days)
    
    def get_rolling_metrics(self, window: int = 20) -> Dict[str, Any]:
        """获取滚动指标"""
        return self._calculate_rolling_metrics(window)


def main():
    """测试函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Evolution Trigger 模块测试")
    print("="*60)
    
    trigger = EvolutionTrigger()
    
    # 测试评估
    print("\n1. 测试评估功能...")
    result = trigger.evaluate()
    print(f"   是否触发进化: {result['should_evolve']}")
    print(f"   置信度: {result['confidence']:.2f}")
    print(f"   消息: {result['message']}")
    
    # 测试手动触发
    print("\n2. 测试手动触发...")
    manual_result = trigger.manual_trigger(reason="系统维护测试", triggered_by="test")
    print(f"   是否触发进化: {manual_result['should_evolve']}")
    print(f"   触发类型: {manual_result['trigger_type']}")
    print(f"   消息: {manual_result['message']}")
    
    # 测试历史记录
    print("\n3. 测试历史记录...")
    history = trigger.get_trigger_history(days=7)
    print(f"   最近7天触发次数: {len(history)}")
    
    stats = trigger.get_trigger_statistics(days=7)
    print(f"   统计信息: {stats}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == '__main__':
    main()
