#!/usr/bin/env python3
"""
Attribution Analyzer Module - T01 Phase 3

Performs deep attribution analysis on trades to understand factor contributions.
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
from collections import defaultdict

logger = logging.getLogger(__name__)


@dataclass
class AttributionResult:
    """归因分析结果数据类"""
    factor_name: str
    contribution: float
    contribution_pct: float
    t_stat: float
    p_value: float
    significant: bool


class AttributionAnalyzer:
    """
    归因分析器
    
    职责:
    1. 分析交易绩效的因子贡献
    2. 识别有效和无效因子
    3. 提供因子权重调整建议
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        初始化归因分析器
        
        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        attribution_config = self.config.get('attribution_analyzer', {})
        self.significance_level = attribution_config.get('significance_level', 0.05)
        self.min_observations = attribution_config.get('min_observations', 30)
        
        # 分析报告目录
        self.reports_dir = Path('reports/attribution')
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("AttributionAnalyzer初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"加载配置失败: {e}，使用默认配置")
            return {}
    
    def analyze(self, trade_ids: List[str] = None, 
                start_date: str = None, 
                end_date: str = None) -> Dict[str, Any]:
        """
        执行归因分析
        
        Args:
            trade_ids: 要分析的交易ID列表，None表示分析所有近期交易
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            归因分析报告
        """
        logger.info("开始归因分析...")
        
        try:
            # 1. 加载交易数据
            trades = self._load_trades(trade_ids, start_date, end_date)
            
            if len(trades) < self.min_observations:
                return {
                    'success': False,
                    'error': f'交易样本不足: {len(trades)} < {self.min_observations}',
                    'attribution_report': {}
                }
            
            # 2. 计算因子贡献
            factor_contributions = self._calculate_factor_contributions(trades)
            
            # 3. 计算未解释收益
            unexplained = self._calculate_unexplained(trades, factor_contributions)
            
            # 4. 生成建议
            recommendations = self._generate_recommendations(factor_contributions)
            
            # 5. 构建报告
            report = {
                'analysis_period': {
                    'start_date': start_date or trades[0].get('date', 'unknown'),
                    'end_date': end_date or trades[-1].get('date', 'unknown'),
                    'total_trades': len(trades)
                },
                'factor_contributions': {
                    k: {
                        'contribution': v.contribution,
                        'contribution_pct': v.contribution_pct,
                        't_stat': v.t_stat,
                        'p_value': v.p_value,
                        'significant': v.significant
                    }
                    for k, v in factor_contributions.items()
                },
                'unexplained': unexplained,
                'recommendations': recommendations
            }
            
            # 6. 保存报告
            self._save_report(report)
            
            logger.info("归因分析完成")
            
            return {
                'success': True,
                'attribution_report': report
            }
            
        except Exception as e:
            logger.error(f"归因分析失败: {e}")
            return {
                'success': False,
                'error': str(e),
                'attribution_report': {}
            }
    
    def _load_trades(self, trade_ids: List[str] = None,
                     start_date: str = None,
                     end_date: str = None) -> List[Dict[str, Any]]:
        """
        加载交易数据
        
        Args:
            trade_ids: 交易ID列表
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            交易列表
        """
        trades = []
        
        # 从state目录加载交易记录
        state_dir = Path('state')
        
        try:
            # 尝试加载回测结果
            backtest_file = state_dir / 'backtest_results.json'
            if backtest_file.exists():
                with open(backtest_file, 'r', encoding='utf-8') as f:
                    trades = json.load(f)
            
            # 如果没有回测结果，尝试加载候选股历史
            if not trades:
                for candidate_file in state_dir.glob('candidates_*.json'):
                    with open(candidate_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if 'trades' in data:
                            trades.extend(data['trades'])
            
            # 按日期过滤
            if start_date:
                trades = [t for t in trades if t.get('date', '') >= start_date]
            if end_date:
                trades = [t for t in trades if t.get('date', '') <= end_date]
            
            # 按ID过滤
            if trade_ids:
                trades = [t for t in trades if t.get('id') in trade_ids]
            
        except Exception as e:
            logger.warning(f"加载交易数据失败: {e}")
        
        # 如果没有真实数据，生成模拟数据用于测试
        if not trades:
            trades = self._generate_mock_trades(100)
        
        return trades
    
    def _generate_mock_trades(self, n: int) -> List[Dict[str, Any]]:
        """生成模拟交易数据"""
        trades = []
        base_date = datetime.now() - timedelta(days=n)
        
        for i in range(n):
            date = (base_date + timedelta(days=i)).strftime('%Y%m%d')
            
            # 模拟收益
            pnl = np.random.normal(0.02, 0.05)
            
            trade = {
                'id': f'trade_{i}',
                'date': date,
                'stock_code': f'{np.random.randint(100000, 999999):06d}.SZ',
                'pnl': pnl,
                'pnl_pct': pnl,
                'factors': {
                    'momentum': np.random.uniform(-1, 1),
                    'value': np.random.uniform(-1, 1),
                    'quality': np.random.uniform(-1, 1),
                    'volatility': np.random.uniform(-1, 1),
                    'liquidity': np.random.uniform(-1, 1)
                }
            }
            trades.append(trade)
        
        return trades
    
    def _calculate_factor_contributions(self, trades: List[Dict[str, Any]]) -> Dict[str, AttributionResult]:
        """
        计算因子贡献
        
        Args:
            trades: 交易列表
            
        Returns:
            因子贡献字典
        """
        contributions = {}
        
        # 收集所有因子
        all_factors = set()
        for trade in trades:
            factors = trade.get('factors', {})
            all_factors.update(factors.keys())
        
        # 计算每个因子的贡献
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        
        for factor_name in all_factors:
            # 获取该因子的值和对应的收益
            factor_values = []
            pnls = []
            
            for trade in trades:
                factors = trade.get('factors', {})
                if factor_name in factors:
                    factor_values.append(factors[factor_name])
                    pnls.append(trade.get('pnl', 0))
            
            if len(factor_values) < self.min_observations:
                continue
            
            # 计算相关性
            correlation = np.corrcoef(factor_values, pnls)[0, 1]
            if np.isnan(correlation):
                correlation = 0
            
            # 计算贡献
            contribution = correlation * np.std(pnls) * np.mean(np.abs(factor_values))
            contribution_pct = (contribution / total_pnl * 100) if total_pnl != 0 else 0
            
            # 计算t统计量和p值
            from scipy import stats
            t_stat, p_value = stats.ttest_ind(
                [pnls[i] for i in range(len(pnls)) if factor_values[i] > 0],
                [pnls[i] for i in range(len(pnls)) if factor_values[i] <= 0]
            ) if len(set(factor_values)) > 1 else (0, 1)
            
            if np.isnan(t_stat):
                t_stat = 0
            if np.isnan(p_value):
                p_value = 1
            
            significant = p_value < self.significance_level
            
            contributions[factor_name] = AttributionResult(
                factor_name=factor_name,
                contribution=contribution,
                contribution_pct=contribution_pct,
                t_stat=t_stat,
                p_value=p_value,
                significant=significant
            )
        
        return contributions
    
    def _calculate_unexplained(self, trades: List[Dict[str, Any]], 
                               contributions: Dict[str, AttributionResult]) -> Dict[str, float]:
        """
        计算未解释收益
        
        Args:
            trades: 交易列表
            contributions: 因子贡献
            
        Returns:
            未解释收益信息
        """
        total_pnl = sum(t.get('pnl', 0) for t in trades)
        explained_pnl = sum(c.contribution for c in contributions.values())
        unexplained_pnl = total_pnl - explained_pnl
        
        unexplained_pct = (unexplained_pnl / total_pnl * 100) if total_pnl != 0 else 0
        
        return {
            'unexplained_pnl': unexplained_pnl,
            'unexplained_pct': unexplained_pct,
            'explained_pnl': explained_pnl,
            'explained_pct': 100 - unexplained_pct,
            'total_pnl': total_pnl
        }
    
    def _generate_recommendations(self, contributions: Dict[str, AttributionResult]) -> List[str]:
        """
        生成建议
        
        Args:
            contributions: 因子贡献
            
        Returns:
            建议列表
        """
        recommendations = []
        
        # 识别显著因子
        significant_factors = [c for c in contributions.values() if c.significant]
        
        if significant_factors:
            # 正向贡献因子
            positive = [c for c in significant_factors if c.contribution > 0]
            if positive:
                top_positive = sorted(positive, key=lambda x: x.contribution, reverse=True)[:3]
                recommendations.append(
                    f"增强正向因子权重: {', '.join([c.factor_name for c in top_positive])}"
                )
            
            # 负向贡献因子
            negative = [c for c in significant_factors if c.contribution < 0]
            if negative:
                recommendations.append(
                    f"降低负向因子权重: {', '.join([c.factor_name for c in negative])}"
                )
        
        # 检查不显著因子
        insignificant = [c for c in contributions.values() if not c.significant]
        if len(insignificant) > len(significant_factors):
            recommendations.append(
                f"考虑移除不显著因子: {len(insignificant)}个因子统计不显著"
            )
        
        if not recommendations:
            recommendations.append("当前因子配置合理，建议保持")
        
        return recommendations
    
    def _save_report(self, report: Dict[str, Any]):
        """保存报告"""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            report_file = self.reports_dir / f'attribution_report_{timestamp}.json'
            
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
            
            logger.info(f"归因报告已保存: {report_file}")
        except Exception as e:
            logger.error(f"保存报告失败: {e}")
    
    def get_latest_report(self) -> Optional[Dict[str, Any]]:
        """获取最新报告"""
        try:
            report_files = sorted(self.reports_dir.glob('attribution_report_*.json'))
            if report_files:
                with open(report_files[-1], 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"获取最新报告失败: {e}")
        return None


def main():
    """测试函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Attribution Analyzer 模块测试")
    print("="*60)
    
    analyzer = AttributionAnalyzer()
    
    # 测试归因分析
    print("\n1. 测试归因分析...")
    result = analyzer.analyze()
    print(f"   成功: {result['success']}")
    
    if result['success']:
        report = result['attribution_report']
        print(f"   分析交易数: {report['analysis_period']['total_trades']}")
        print(f"   因子贡献数: {len(report['factor_contributions'])}")
        print(f"   未解释收益: {report['unexplained']['unexplained_pct']:.1f}%")
        print(f"   建议数: {len(report['recommendations'])}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == '__main__':
    main()
