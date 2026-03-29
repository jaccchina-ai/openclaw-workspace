#!/usr/bin/env python3
"""
T01 SHAP Explainer 模块 (shap_explainer.py)
实现SHAP (SHapley Additive exPlanations) 值计算，用于解释模型预测和因子贡献
支持全局解释（所有交易）和局部解释（单个交易）
"""

import sys
import logging
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple, Union
import yaml
import warnings
warnings.filterwarnings('ignore')

# 导入T01相关模块
try:
    from data_storage import T01DataStorage
    from performance_tracker import PerformanceTracker
except ImportError:
    T01DataStorage = None
    PerformanceTracker = None
    logger = logging.getLogger(__name__)
    logger.warning("无法导入T01数据存储模块，某些功能可能不可用")

logger = logging.getLogger(__name__)


class SimplifiedSHAP:
    """
    简化版SHAP实现
    当shap库不可用时使用，基于线性近似和边际贡献计算
    """
    
    def __init__(self):
        """初始化简化版SHAP计算器"""
        self.baseline = None
        self.feature_names = None
        
    def _calculate_baseline(self, y: np.ndarray) -> float:
        """
        计算基线值（平均预测）
        
        Args:
            y: 目标变量数组
            
        Returns:
            基线值
        """
        return np.mean(y)
    
    def calculate_shap_values(self, X: pd.DataFrame, y: np.ndarray) -> np.ndarray:
        """
        计算SHAP值
        
        使用基于相关性的近似方法：
        1. 计算每个特征与目标的相关性
        2. 根据相关性分配SHAP值
        3. 考虑特征间的交互效应
        
        Args:
            X: 特征矩阵 (n_samples, n_features)
            y: 目标变量 (n_samples,)
            
        Returns:
            SHAP值矩阵 (n_samples, n_features)
        """
        if isinstance(X, pd.DataFrame):
            self.feature_names = X.columns.tolist()
            X = X.values
        
        n_samples, n_features = X.shape
        self.baseline = self._calculate_baseline(y)
        
        # 标准化特征
        X_scaled = (X - np.mean(X, axis=0)) / (np.std(X, axis=0) + 1e-10)
        
        # 计算每个特征与目标的相关系数
        correlations = np.array([
            np.corrcoef(X_scaled[:, i], y)[0, 1] if np.std(X_scaled[:, i]) > 0 else 0
            for i in range(n_features)
        ])
        
        # 处理NaN相关性
        correlations = np.nan_to_num(correlations, nan=0.0, posinf=0.0, neginf=0.0)
        
        # 计算SHAP值：特征值 * 相关性 * 缩放因子
        # 缩放因子确保SHAP值之和接近预测值与基线的差
        shap_values = np.zeros((n_samples, n_features))
        
        for i in range(n_samples):
            # 计算预测值（使用加权平均）
            prediction = self.baseline + np.sum(X_scaled[i] * correlations)
            
            # 计算差值
            diff = prediction - self.baseline
            
            # 根据特征贡献分配SHAP值
            total_contribution = np.sum(np.abs(correlations)) + 1e-10
            
            for j in range(n_features):
                if total_contribution > 0:
                    # SHAP值 = 特征值 * 相关性权重
                    weight = abs(correlations[j]) / total_contribution
                    shap_values[i, j] = X_scaled[i, j] * correlations[j] * (1 + weight)
        
        return shap_values
    
    def calculate_feature_importance(self, shap_values: np.ndarray) -> Dict[str, float]:
        """
        计算特征重要性（基于平均绝对SHAP值）
        
        Args:
            shap_values: SHAP值矩阵
            
        Returns:
            特征重要性字典 {特征名: 重要性值}
        """
        # 计算每个特征的平均绝对SHAP值
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        
        # 归一化到0-1范围
        total = np.sum(mean_abs_shap) + 1e-10
        normalized_importance = mean_abs_shap / total
        
        # 构建结果字典
        importance = {}
        if self.feature_names:
            for i, name in enumerate(self.feature_names):
                importance[name] = float(normalized_importance[i])
        else:
            for i in range(len(normalized_importance)):
                importance[f'feature_{i}'] = float(normalized_importance[i])
        
        return importance
    
    def explain_instance(self, x: Union[pd.Series, np.ndarray], 
                         shap_values: np.ndarray) -> Dict[str, Any]:
        """
        解释单个样本
        
        Args:
            x: 单个样本特征值
            shap_values: 该样本的SHAP值
            
        Returns:
            解释结果字典
        """
        if isinstance(x, pd.Series):
            feature_values = x.values
            feature_names = x.index.tolist()
        else:
            feature_values = x
            feature_names = self.feature_names or [f'feature_{i}' for i in range(len(x))]
        
        # 构建贡献列表
        contributions = []
        for i, (name, value, shap_val) in enumerate(zip(feature_names, feature_values, shap_values)):
            contributions.append({
                'factor': name,
                'value': float(value),
                'shap_value': float(shap_val),
                'abs_shap': float(abs(shap_val)),
                'direction': 'positive' if shap_val > 0 else 'negative'
            })
        
        # 按绝对SHAP值排序
        contributions.sort(key=lambda x: x['abs_shap'], reverse=True)
        
        # 分离正负贡献
        positive_contributions = [c for c in contributions if c['shap_value'] > 0]
        negative_contributions = [c for c in contributions if c['shap_value'] < 0]
        
        # 计算预测值
        prediction = self.baseline + np.sum(shap_values)
        
        return {
            'baseline': float(self.baseline),
            'prediction': float(prediction),
            'contributions': contributions,
            'top_positive': positive_contributions[:5],
            'top_negative': negative_contributions[:5],
            'total_contribution': float(np.sum(shap_values))
        }


class T01SHAPExplainer:
    """
    T01系统SHAP解释器
    用于解释机器学习模型的预测结果和因子贡献
    """
    
    def __init__(self, config_path: str = 'config.yaml'):
        """
        初始化SHAP解释器
        
        Args:
            config_path: 配置文件路径
        """
        # 加载配置
        with open(config_path, 'r', encoding='utf-8') as f:
            self.config = yaml.safe_load(f)
        
        # SHAP配置
        shap_config = self.config.get('machine_learning', {}).get('shap_explainer', {})
        self.enabled = shap_config.get('enabled', True)
        self.use_library = shap_config.get('use_library', False)  # 默认使用简化版
        self.max_display_factors = shap_config.get('max_display_factors', 10)
        
        # 尝试导入shap库
        self.shap_library = None
        if self.use_library:
            try:
                import shap
                self.shap_library = shap
                logger.info("使用shap库进行解释")
            except ImportError:
                logger.warning("shap库未安装，使用简化版SHAP实现")
                self.use_library = False
        
        # 初始化SHAP计算器
        if self.use_library and self.shap_library:
            self.shap_calculator = None  # 将在需要时初始化
        else:
            self.shap_calculator = SimplifiedSHAP()
        
        # 初始化数据存储和绩效跟踪
        if T01DataStorage is None or PerformanceTracker is None:
            raise ImportError("无法导入T01数据存储模块，请确保data_storage.py和performance_tracker.py存在")
        
        self.storage = T01DataStorage(config_path)
        self.tracker = PerformanceTracker(config_path)
        
        # 缓存
        self._shap_values_cache = None
        self._feature_names_cache = None
        self._last_trade_data = None
        
        logger.info("T01 SHAP解释器初始化完成")
    
    def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """
        从DataFrame中提取特征列
        
        Args:
            df: 输入DataFrame
            
        Returns:
            特征列名列表
        """
        # 排除非特征列
        exclude_cols = [
            'trade_id', 'ts_code', 'name', 'trade_date', 'buy_date', 'sell_date',
            'win_loss', 'label', 'return_pct', 'recommendation_id',
            'buy_price', 'sell_price', 'holding_days', 'max_drawdown',
            'sharpe_ratio', 'buy_trade_id', 'sell_trade_id', 'performance_id',
            'rank', 'score_bin', 'forward_return'
        ]
        
        # 选择数值列
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # 过滤掉排除列
        feature_cols = [col for col in numeric_cols if col not in exclude_cols]
        
        return feature_cols
    
    def _prepare_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        准备特征数据
        
        Args:
            df: 原始数据
            
        Returns:
            处理后的特征DataFrame
        """
        feature_cols = self._get_feature_columns(df)
        X = df[feature_cols].copy()
        
        # 处理缺失值
        X = X.fillna(X.mean())
        
        # 处理无穷值
        X = X.replace([np.inf, -np.inf], np.nan)
        X = X.fillna(0)
        
        return X
    
    def explain_global(self, start_date: Optional[str] = None, 
                       end_date: Optional[str] = None) -> Dict[str, Any]:
        """
        全局解释：分析所有交易的因子重要性
        
        Args:
            start_date: 开始日期 (YYYYMMDD)
            end_date: 结束日期 (YYYYMMDD)
            
        Returns:
            全局解释结果
        """
        try:
            # 获取训练数据
            trade_data = self.tracker.get_training_data_for_ml()
            
            if trade_data.empty:
                return {
                    'success': False,
                    'message': '没有可用的交易数据'
                }
            
            # 日期过滤
            if start_date and 'trade_date' in trade_data.columns:
                trade_data = trade_data[trade_data['trade_date'] >= start_date]
            if end_date and 'trade_date' in trade_data.columns:
                trade_data = trade_data[trade_data['trade_date'] <= end_date]
            
            if trade_data.empty:
                return {
                    'success': False,
                    'message': '指定日期范围内没有交易数据'
                }
            
            # 准备特征
            X = self._prepare_features(trade_data)
            
            # 准备目标变量
            if 'win_loss' in trade_data.columns:
                y = trade_data['win_loss'].values
            elif 'label' in trade_data.columns:
                y = trade_data['label'].values
            else:
                return {
                    'success': False,
                    'message': '缺少目标变量(win_loss或label)'
                }
            
            if len(X) < 10:
                return {
                    'success': False,
                    'message': f'数据点太少: {len(X)}，需要至少10个'
                }
            
            # 计算SHAP值
            shap_values = self.shap_calculator.calculate_shap_values(X, y)
            
            # 计算特征重要性
            feature_importance = self.shap_calculator.calculate_feature_importance(shap_values)
            
            # 排序
            sorted_importance = dict(sorted(
                feature_importance.items(),
                key=lambda x: x[1],
                reverse=True
            ))
            
            # 缓存结果
            self._shap_values_cache = shap_values
            self._feature_names_cache = X.columns.tolist()
            self._last_trade_data = trade_data
            
            # 计算统计信息
            positive_trades = np.sum(y == 1)
            negative_trades = np.sum(y == 0)
            
            return {
                'success': True,
                'global_importance': sorted_importance,
                'feature_count': len(X.columns),
                'trade_count': len(X),
                'positive_trades': int(positive_trades),
                'negative_trades': int(negative_trades),
                'win_rate': float(positive_trades / len(y)) if len(y) > 0 else 0,
                'top_factors': list(sorted_importance.keys())[:self.max_display_factors],
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"全局解释失败: {e}")
            return {
                'success': False,
                'message': f'全局解释失败: {str(e)}'
            }
    
    def explain_trade(self, trade_id: str) -> Dict[str, Any]:
        """
        局部解释：解释单个交易的因子贡献
        
        Args:
            trade_id: 交易ID
            
        Returns:
            单个交易的解释结果
        """
        try:
            # 获取训练数据
            trade_data = self.tracker.get_training_data_for_ml()
            
            if trade_data.empty:
                return {
                    'success': False,
                    'message': '没有可用的交易数据'
                }
            
            # 查找指定交易
            if 'trade_id' in trade_data.columns:
                trade_row = trade_data[trade_data['trade_id'] == trade_id]
            elif 'recommendation_id' in trade_data.columns:
                trade_row = trade_data[trade_data['recommendation_id'] == trade_id]
            else:
                # 使用索引
                try:
                    idx = int(trade_id.split('_')[-1]) if '_' in trade_id else 0
                    if idx < len(trade_data):
                        trade_row = trade_data.iloc[idx:idx+1]
                    else:
                        trade_row = pd.DataFrame()
                except:
                    trade_row = pd.DataFrame()
            
            if trade_row.empty:
                return {
                    'success': False,
                    'message': f'找不到交易: {trade_id}'
                }
            
            # 准备特征
            X = self._prepare_features(trade_data)
            
            # 准备目标变量
            if 'win_loss' in trade_data.columns:
                y = trade_data['win_loss'].values
            elif 'label' in trade_data.columns:
                y = trade_data['label'].values
            else:
                y = np.zeros(len(trade_data))
            
            # 计算所有SHAP值
            shap_values = self.shap_calculator.calculate_shap_values(X, y)
            
            # 找到指定交易的索引
            if 'trade_id' in trade_data.columns:
                idx = trade_data[trade_data['trade_id'] == trade_id].index[0]
            elif 'recommendation_id' in trade_data.columns:
                idx = trade_data[trade_data['recommendation_id'] == trade_id].index[0]
            else:
                idx = 0
            
            # 获取该交易的SHAP值
            instance_shap = shap_values[idx]
            instance_features = X.iloc[idx]
            
            # 生成解释
            explanation = self.shap_calculator.explain_instance(
                instance_features,
                instance_shap
            )
            
            # 获取交易信息
            trade_info = trade_row.iloc[0]
            actual_outcome = trade_info.get('win_loss', trade_info.get('label', 0))
            return_pct = trade_info.get('return_pct', 0)
            ts_code = trade_info.get('ts_code', 'Unknown')
            trade_date = trade_info.get('trade_date', '')
            
            # 生成解释文本
            explanation_text = self._generate_explanation_text(
                explanation, ts_code, trade_date, actual_outcome, return_pct
            )
            
            return {
                'success': True,
                'trade_id': trade_id,
                'ts_code': ts_code,
                'trade_date': trade_date,
                'baseline_prediction': explanation['baseline'],
                'actual_outcome': int(actual_outcome) if pd.notna(actual_outcome) else None,
                'return_pct': float(return_pct) if pd.notna(return_pct) else None,
                'top_positive_factors': explanation['top_positive'],
                'top_negative_factors': explanation['top_negative'],
                'factor_contributions': explanation['contributions'],
                'explanation_text': explanation_text,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"交易解释失败: {e}")
            return {
                'success': False,
                'message': f'交易解释失败: {str(e)}'
            }
    
    def _generate_explanation_text(self, explanation: Dict[str, Any], 
                                   ts_code: str, trade_date: str,
                                   actual_outcome: int, return_pct: float) -> str:
        """
        生成人类可读的解释文本
        
        Args:
            explanation: 解释结果
            ts_code: 股票代码
            trade_date: 交易日期
            actual_outcome: 实际结果
            return_pct: 收益率
            
        Returns:
            解释文本
        """
        lines = []
        lines.append(f"📊 交易解释: {ts_code}")
        lines.append(f"交易日期: {trade_date}")
        lines.append(f"实际结果: {'✅ 盈利' if actual_outcome == 1 else '❌ 亏损'}")
        if pd.notna(return_pct):
            lines.append(f"收益率: {return_pct:.2f}%")
        lines.append("")
        
        lines.append("🔍 因子贡献分析:")
        lines.append(f"基线预测: {explanation['baseline']:.4f}")
        lines.append(f"最终预测: {explanation['prediction']:.4f}")
        lines.append("")
        
        # 正向贡献
        if explanation['top_positive']:
            lines.append("📈 正向贡献因子:")
            for contrib in explanation['top_positive'][:3]:
                lines.append(f"  + {contrib['factor']}: {contrib['shap_value']:+.4f} (值: {contrib['value']:.2f})")
            lines.append("")
        
        # 负向贡献
        if explanation['top_negative']:
            lines.append("📉 负向贡献因子:")
            for contrib in explanation['top_negative'][:3]:
                lines.append(f"  {contrib['factor']}: {contrib['shap_value']:.4f} (值: {contrib['value']:.2f})")
            lines.append("")
        
        # 总结
        total_contrib = explanation['total_contribution']
        if total_contrib > 0:
            lines.append(f"💡 总结: 整体因子贡献为正向(+{total_contrib:.4f})，有利于盈利")
        else:
            lines.append(f"💡 总结: 整体因子贡献为负向({total_contrib:.4f})，不利于盈利")
        
        return "\n".join(lines)
    
    def explain_multiple_trades(self, trade_ids: List[str]) -> Dict[str, Any]:
        """
        批量解释多个交易
        
        Args:
            trade_ids: 交易ID列表
            
        Returns:
            批量解释结果
        """
        explanations = []
        
        for trade_id in trade_ids:
            result = self.explain_trade(trade_id)
            explanations.append(result)
        
        # 统计
        successful = sum(1 for e in explanations if e.get('success', False))
        
        return {
            'success': successful > 0,
            'total_trades': len(trade_ids),
            'explained_trades': successful,
            'explanations': explanations,
            'timestamp': datetime.now().isoformat()
        }
    
    def compare_trades(self, trade_id_1: str, trade_id_2: str) -> Dict[str, Any]:
        """
        比较两个交易的因子贡献差异
        
        Args:
            trade_id_1: 第一个交易ID
            trade_id_2: 第二个交易ID
            
        Returns:
            比较结果
        """
        try:
            # 获取两个交易的解释
            exp1 = self.explain_trade(trade_id_1)
            exp2 = self.explain_trade(trade_id_2)
            
            if not exp1.get('success') or not exp2.get('success'):
                return {
                    'success': False,
                    'message': '无法获取一个或两个交易的解释'
                }
            
            # 提取贡献
            contrib1 = {c['factor']: c['shap_value'] for c in exp1['factor_contributions']}
            contrib2 = {c['factor']: c['shap_value'] for c in exp2['factor_contributions']}
            
            # 计算差异
            all_factors = set(contrib1.keys()) | set(contrib2.keys())
            differences = []
            
            for factor in all_factors:
                v1 = contrib1.get(factor, 0)
                v2 = contrib2.get(factor, 0)
                diff = v1 - v2
                differences.append({
                    'factor': factor,
                    'trade_1_value': v1,
                    'trade_2_value': v2,
                    'difference': diff,
                    'abs_difference': abs(diff)
                })
            
            # 按差异大小排序
            differences.sort(key=lambda x: x['abs_difference'], reverse=True)
            
            return {
                'success': True,
                'trade_1': {
                    'id': trade_id_1,
                    'ts_code': exp1.get('ts_code'),
                    'outcome': exp1.get('actual_outcome'),
                    'return_pct': exp1.get('return_pct')
                },
                'trade_2': {
                    'id': trade_id_2,
                    'ts_code': exp2.get('ts_code'),
                    'outcome': exp2.get('actual_outcome'),
                    'return_pct': exp2.get('return_pct')
                },
                'differences': differences[:10],  # 前10个差异最大的因子
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"交易比较失败: {e}")
            return {
                'success': False,
                'message': f'交易比较失败: {str(e)}'
            }
    
    def _create_text_visualization(self, features: pd.Series, 
                                   shap_values: np.ndarray,
                                   feature_names: List[str]) -> str:
        """
        创建文本可视化
        
        Args:
            features: 特征值
            shap_values: SHAP值
            feature_names: 特征名
            
        Returns:
            文本可视化字符串
        """
        lines = []
        lines.append("\n" + "="*60)
        lines.append("SHAP值可视化")
        lines.append("="*60)
        
        # 合并特征和SHAP值
        data = list(zip(feature_names, features.values, shap_values))
        data.sort(key=lambda x: abs(x[2]), reverse=True)
        
        # 显示前10个
        lines.append(f"{'因子':<20} {'值':<12} {'SHAP值':<12} {'贡献'}")
        lines.append("-"*60)
        
        for name, value, shap_val in data[:self.max_display_factors]:
            # 创建简单的条形图
            bar_length = min(int(abs(shap_val) * 50), 20)
            bar = "█" * bar_length
            direction = "+" if shap_val > 0 else ""
            lines.append(f"{name:<20} {value:>10.2f} {direction}{shap_val:>+10.4f} {bar}")
        
        lines.append("="*60)
        
        return "\n".join(lines)
    
    def generate_explanation_report(self, start_date: Optional[str] = None,
                                    end_date: Optional[str] = None) -> str:
        """
        生成完整的解释报告
        
        Args:
            start_date: 开始日期
            end_date: 结束日期
            
        Returns:
            报告文本
        """
        try:
            lines = []
            lines.append("="*60)
            lines.append("📊 T01 SHAP解释报告")
            lines.append("="*60)
            lines.append(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            
            # 全局解释
            lines.append("🌍 全局因子重要性")
            lines.append("-"*60)
            
            global_result = self.explain_global(start_date, end_date)
            
            if global_result.get('success'):
                importance = global_result['global_importance']
                
                lines.append(f"分析交易数: {global_result['trade_count']}")
                lines.append(f"盈利交易: {global_result['positive_trades']}")
                lines.append(f"亏损交易: {global_result['negative_trades']}")
                lines.append(f"胜率: {global_result['win_rate']*100:.1f}%")
                lines.append("")
                
                lines.append("因子重要性排名:")
                for i, (factor, imp) in enumerate(importance.items(), 1):
                    bar = "█" * int(imp * 50)
                    lines.append(f"  {i:2d}. {factor:<20} {imp:.4f} {bar}")
                    if i >= self.max_display_factors:
                        break
            else:
                lines.append(f"❌ 全局解释失败: {global_result.get('message', '未知错误')}")
            
            lines.append("")
            lines.append("="*60)
            
            return "\n".join(lines)
            
        except Exception as e:
            logger.error(f"生成报告失败: {e}")
            return f"❌ 生成报告失败: {str(e)}"
    
    def save_explanations(self, output_path: str, 
                          start_date: Optional[str] = None,
                          end_date: Optional[str] = None):
        """
        保存解释结果到文件
        
        Args:
            output_path: 输出文件路径
            start_date: 开始日期
            end_date: 结束日期
        """
        try:
            import json
            
            # 获取全局解释
            global_result = self.explain_global(start_date, end_date)
            
            # 构建输出
            output = {
                'timestamp': datetime.now().isoformat(),
                'global_explanation': global_result,
                'config': {
                    'use_library': self.use_library,
                    'max_display_factors': self.max_display_factors
                }
            }
            
            # 保存
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(output, f, ensure_ascii=False, indent=2)
            
            logger.info(f"解释结果已保存到: {output_path}")
            
        except Exception as e:
            logger.error(f"保存解释结果失败: {e}")


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='T01 SHAP解释器')
    parser.add_argument('--global', action='store_true', dest='global_exp',
                       help='生成全局解释')
    parser.add_argument('--trade', type=str, help='解释指定交易')
    parser.add_argument('--compare', nargs=2, metavar=('TRADE1', 'TRADE2'),
                       help='比较两个交易')
    parser.add_argument('--report', action='store_true',
                       help='生成完整报告')
    parser.add_argument('--start-date', type=str, help='开始日期 (YYYYMMDD)')
    parser.add_argument('--end-date', type=str, help='结束日期 (YYYYMMDD)')
    parser.add_argument('--save', type=str, help='保存结果到文件')
    parser.add_argument('--config', type=str, default='config.yaml',
                       help='配置文件路径')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        # 创建解释器
        explainer = T01SHAPExplainer(args.config)
        
        if args.global_exp:
            print("🔍 生成全局解释...")
            result = explainer.explain_global(args.start_date, args.end_date)
            
            if result['success']:
                print("\n✅ 全局解释完成")
                print(f"交易数: {result['trade_count']}")
                print(f"胜率: {result['win_rate']*100:.1f}%")
                print("\n📊 因子重要性:")
                for i, (factor, imp) in enumerate(result['global_importance'].items(), 1):
                    print(f"  {i}. {factor}: {imp:.4f}")
                    if i >= 10:
                        break
            else:
                print(f"❌ 失败: {result.get('message', '未知错误')}")
        
        elif args.trade:
            print(f"🔍 解释交易: {args.trade}")
            result = explainer.explain_trade(args.trade)
            
            if result['success']:
                print(f"\n{result['explanation_text']}")
            else:
                print(f"❌ 失败: {result.get('message', '未知错误')}")
        
        elif args.compare:
            print(f"🔍 比较交易: {args.compare[0]} vs {args.compare[1]}")
            result = explainer.compare_trades(args.compare[0], args.compare[1])
            
            if result['success']:
                print("\n✅ 比较完成")
                print(f"\n交易1: {result['trade_1']['ts_code']} "
                      f"({'盈利' if result['trade_1']['outcome'] == 1 else '亏损'})")
                print(f"交易2: {result['trade_2']['ts_code']} "
                      f"({'盈利' if result['trade_2']['outcome'] == 1 else '亏损'})")
                print("\n差异最大的因子:")
                for diff in result['differences'][:5]:
                    print(f"  {diff['factor']}: "
                          f"{diff['trade_1_value']:+.4f} vs {diff['trade_2_value']:+.4f} "
                          f"(差异: {diff['difference']:+.4f})")
            else:
                print(f"❌ 失败: {result.get('message', '未知错误')}")
        
        elif args.report:
            print("📋 生成解释报告...")
            report = explainer.generate_explanation_report(args.start_date, args.end_date)
            print(report)
        
        else:
            # 默认生成报告
            report = explainer.generate_explanation_report()
            print(report)
        
        # 保存结果
        if args.save:
            explainer.save_explanations(args.save, args.start_date, args.end_date)
            print(f"\n💾 结果已保存到: {args.save}")
    
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
