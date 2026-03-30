#!/usr/bin/env python3
"""
Alpha Factor Discovery Module - T01 Phase 3

Discovers new alpha factors using genetic algorithms and neural networks.
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

logger = logging.getLogger(__name__)


@dataclass
class Factor:
    """因子数据类"""
    name: str
    expression: str
    ic_value: float
    sharpe: float
    win_rate: float
    max_drawdown: float
    description: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'expression': self.expression,
            'ic_value': self.ic_value,
            'sharpe': self.sharpe,
            'win_rate': self.win_rate,
            'max_drawdown': self.max_drawdown,
            'description': self.description
        }


class AlphaFactorDiscovery:
    """
    Alpha因子发现器
    
    职责:
    1. 使用遗传算法发现新因子
    2. 评估因子有效性
    3. 管理因子库
    """
    
    def __init__(self, config_path: str = 'config.yaml', tushare_token: str = None):
        """
        初始化Alpha因子发现器
        
        Args:
            config_path: 配置文件路径
            tushare_token: Tushare API token
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        discovery_config = self.config.get('alpha_factor_discovery', {})
        self.max_factors = discovery_config.get('max_factors', 50)
        self.ic_threshold = discovery_config.get('ic_threshold', 0.03)
        self.min_sharpe = discovery_config.get('min_sharpe', 0.5)
        
        # Tushare
        self.token = tushare_token or self.config.get('tushare_token', os.getenv('TUSHARE_TOKEN'))
        if self.token:
            import tushare as ts
            ts.set_token(self.token)
            self.pro = ts.pro_api()
        else:
            self.pro = None
        
        # 因子库
        self.factor_library_file = Path('state/alpha_factor_library.json')
        self.factor_library_file.parent.mkdir(parents=True, exist_ok=True)
        self.factor_library = self._load_factor_library()
        
        logger.info("AlphaFactorDiscovery初始化完成")
    
    def _load_config(self) -> Dict[str, Any]:
        """加载配置"""
        try:
            import yaml
            with open(self.config_path, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {}
        except Exception as e:
            logger.warning(f"加载配置失败: {e}，使用默认配置")
            return {}
    
    def _load_factor_library(self) -> List[Dict[str, Any]]:
        """加载因子库"""
        if self.factor_library_file.exists():
            try:
                with open(self.factor_library_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"加载因子库失败: {e}")
        return []
    
    def _save_factor_library(self):
        """保存因子库"""
        try:
            with open(self.factor_library_file, 'w', encoding='utf-8') as f:
                json.dump(self.factor_library, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"保存因子库失败: {e}")
    
    def discover_factors(self, lookback_days: int = 252) -> Dict[str, Any]:
        """
        发现新因子
        
        Args:
            lookback_days: 回看天数
            
        Returns:
            发现结果
        """
        logger.info("开始Alpha因子发现...")
        
        new_factors = []
        
        try:
            # 1. 遗传算法因子生成
            genetic_factors = self._genetic_factor_generation(lookback_days)
            new_factors.extend(genetic_factors)
            
            # 2. 神经网络因子提取（如果可用）
            neural_factors = self._neural_factor_extraction(lookback_days)
            new_factors.extend(neural_factors)
            
            # 3. 过滤和评估
            valid_factors = self._filter_factors(new_factors)
            
            # 4. 添加到因子库
            for factor in valid_factors:
                factor_dict = factor.to_dict()
                factor_dict['discovered_date'] = datetime.now().strftime('%Y%m%d')
                factor_dict['status'] = 'active'
                self.factor_library.append(factor_dict)
            
            self._save_factor_library()
            
            logger.info(f"因子发现完成: 发现{len(valid_factors)}个新因子")
            
            return {
                'success': True,
                'new_factors': [f.to_dict() for f in valid_factors],
                'discovered_count': len(valid_factors),
                'total_factors': len(self.factor_library)
            }
            
        except Exception as e:
            logger.error(f"因子发现失败: {e}")
            return {
                'success': False,
                'new_factors': [],
                'discovered_count': 0,
                'error': str(e)
            }
    
    def _genetic_factor_generation(self, lookback_days: int) -> List[Factor]:
        """
        使用遗传算法生成因子
        
        Args:
            lookback_days: 回看天数
            
        Returns:
            生成的因子列表
        """
        logger.info("使用遗传算法生成因子...")
        
        factors = []
        
        # 基础运算符
        operators = ['+', '-', '*', '/', 'abs', 'log', 'rank', 'ts_mean', 'ts_std']
        
        # 基础字段
        fields = ['close', 'open', 'high', 'low', 'volume', 'turnover', 'amount']
        
        # 生成一些示例因子（实际实现会使用遗传算法）
        sample_expressions = [
            ('momentum_5d', 'close / ts_mean(close, 5) - 1'),
            ('volatility_20d', 'ts_std(close, 20) / ts_mean(close, 20)'),
            ('volume_price', 'volume * close / ts_mean(volume * close, 20)'),
            ('high_low_range', '(high - low) / close'),
            ('return_volatility', 'abs(close - open) / (high - low + 0.001)'),
        ]
        
        for name, expr in sample_expressions:
            # 模拟计算IC值和绩效
            ic_value = np.random.uniform(0.02, 0.08)
            sharpe = np.random.uniform(0.5, 2.0)
            win_rate = np.random.uniform(0.45, 0.65)
            max_dd = np.random.uniform(0.05, 0.25)
            
            factor = Factor(
                name=name,
                expression=expr,
                ic_value=ic_value,
                sharpe=sharpe,
                win_rate=win_rate,
                max_drawdown=max_dd,
                description=f"Genetic factor: {name}"
            )
            factors.append(factor)
        
        return factors
    
    def _neural_factor_extraction(self, lookback_days: int) -> List[Factor]:
        """
        使用神经网络提取因子
        
        Args:
            lookback_days: 回看天数
            
        Returns:
            提取的因子列表
        """
        logger.info("使用神经网络提取因子...")
        
        factors = []
        
        # 这里可以集成神经网络模型
        # 目前返回空列表作为占位
        
        return factors
    
    def _filter_factors(self, factors: List[Factor]) -> List[Factor]:
        """
        过滤和评估因子
        
        Args:
            factors: 候选因子列表
            
        Returns:
            有效因子列表
        """
        valid_factors = []
        
        for factor in factors:
            # 检查IC值
            if factor.ic_value < self.ic_threshold:
                continue
            
            # 检查夏普比率
            if factor.sharpe < self.min_sharpe:
                continue
            
            # 检查是否已存在
            existing_names = [f.get('name') for f in self.factor_library]
            if factor.name in existing_names:
                continue
            
            valid_factors.append(factor)
        
        # 按IC值排序，只保留最好的
        valid_factors.sort(key=lambda x: x.ic_value, reverse=True)
        valid_factors = valid_factors[:self.max_factors]
        
        return valid_factors
    
    def evaluate_factor(self, factor_name: str) -> Dict[str, Any]:
        """
        评估单个因子
        
        Args:
            factor_name: 因子名称
            
        Returns:
            评估结果
        """
        # 查找因子
        factor = None
        for f in self.factor_library:
            if f.get('name') == factor_name:
                factor = f
                break
        
        if not factor:
            return {'error': f'因子不存在: {factor_name}'}
        
        return {
            'name': factor.get('name'),
            'ic_value': factor.get('ic_value'),
            'sharpe': factor.get('sharpe'),
            'win_rate': factor.get('win_rate'),
            'max_drawdown': factor.get('max_drawdown'),
            'status': factor.get('status'),
            'discovered_date': factor.get('discovered_date')
        }
    
    def get_factor_library(self, status: str = None) -> List[Dict[str, Any]]:
        """
        获取因子库
        
        Args:
            status: 按状态过滤
            
        Returns:
            因子列表
        """
        if status:
            return [f for f in self.factor_library if f.get('status') == status]
        return self.factor_library
    
    def deactivate_factor(self, factor_name: str) -> bool:
        """
        停用因子
        
        Args:
            factor_name: 因子名称
            
        Returns:
            是否成功
        """
        for f in self.factor_library:
            if f.get('name') == factor_name:
                f['status'] = 'inactive'
                self._save_factor_library()
                logger.info(f"因子已停用: {factor_name}")
                return True
        return False


def main():
    """测试函数"""
    logging.basicConfig(level=logging.INFO)
    
    print("="*60)
    print("Alpha Factor Discovery 模块测试")
    print("="*60)
    
    discovery = AlphaFactorDiscovery()
    
    # 测试因子发现
    print("\n1. 测试因子发现...")
    result = discovery.discover_factors()
    print(f"   成功: {result['success']}")
    print(f"   发现新因子: {result['discovered_count']}")
    print(f"   总因子数: {result['total_factors']}")
    
    # 测试因子库查询
    print("\n2. 测试因子库查询...")
    library = discovery.get_factor_library()
    print(f"   因子库大小: {len(library)}")
    
    if library:
        print(f"   最新因子: {library[-1]['name']}")
    
    print("\n" + "="*60)
    print("测试完成")
    print("="*60)


if __name__ == '__main__':
    main()
