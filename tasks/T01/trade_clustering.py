#!/usr/bin/env python3
"""
Trade Clustering模块 - 交易聚类分析

功能:
1. 从交易数据中提取特征
2. 应用多种聚类算法 (K-means, DBSCAN, 层次聚类)
3. 分析聚类特征和模式
4. 识别盈利/亏损交易模式
5. 提供可执行的交易建议

集成点:
- performance_tracker.py: 获取交易数据
- factor_mining.py: 获取因子值
- market_regime_detector.py: 获取市场状态

作者: T01 Phase 3
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple, Optional, Union
from dataclasses import dataclass, field
from enum import Enum
import logging
import json
import os

# scikit-learn imports
from sklearn.cluster import KMeans, DBSCAN, AgglomerativeClustering
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.metrics import silhouette_score, calinski_harabasz_score
from sklearn.impute import SimpleImputer

logger = logging.getLogger(__name__)


class ClusterAlgorithm(Enum):
    """聚类算法枚举"""
    KMEANS = "kmeans"
    DBSCAN = "dbscan"
    HIERARCHICAL = "hierarchical"


@dataclass
class TradeFeatures:
    """交易特征数据类"""
    trade_id: str
    return_pct: float
    seal_ratio: float
    turnover_rate: float
    market_regime: str
    sector: str
    duration_days: int
    win_loss: int
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'trade_id': self.trade_id,
            'return_pct': self.return_pct,
            'seal_ratio': self.seal_ratio,
            'turnover_rate': self.turnover_rate,
            'market_regime': self.market_regime,
            'sector': self.sector,
            'duration_days': self.duration_days,
            'win_loss': self.win_loss
        }


@dataclass
class ClusterAnalysis:
    """聚类分析结果数据类"""
    cluster_id: int
    trade_count: int
    win_rate: float
    avg_return: float
    std_return: float
    factor_distributions: Dict[str, Dict[str, float]] = field(default_factory=dict)
    dominant_regime: str = ""
    dominant_sector: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'cluster_id': self.cluster_id,
            'trade_count': self.trade_count,
            'win_rate': self.win_rate,
            'avg_return': self.avg_return,
            'std_return': self.std_return,
            'factor_distributions': self.factor_distributions,
            'dominant_regime': self.dominant_regime,
            'dominant_sector': self.dominant_sector
        }


class TradeClustering:
    """
    交易聚类分析器
    
    用于对交易进行聚类分析，识别盈利和亏损模式
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化交易聚类分析器
        
        Args:
            config: 配置字典，包含:
                - n_clusters: K-means聚类数量 (默认: 3)
                - algorithm: 聚类算法 ('kmeans', 'dbscan', 'hierarchical') (默认: 'kmeans')
                - random_state: 随机种子 (默认: 42)
                - handle_missing: 缺失值处理方法 ('mean', 'median', 'drop') (默认: 'mean')
                - eps: DBSCAN的epsilon参数 (默认: 0.5)
                - min_samples: DBSCAN的最小样本数 (默认: 5)
        """
        self.config = config or {}
        
        # 聚类配置
        self.n_clusters = self.config.get('n_clusters', 3)
        self.algorithm = self._parse_algorithm(self.config.get('algorithm', 'kmeans'))
        self.random_state = self.config.get('random_state', 42)
        self.handle_missing = self.config.get('handle_missing', 'mean')
        
        # DBSCAN特定配置
        self.eps = self.config.get('eps', 0.5)
        self.min_samples = self.config.get('min_samples', 5)
        
        # 内部状态
        self.scaler = StandardScaler()
        self.imputer = self._create_imputer()
        self.label_encoders: Dict[str, LabelEncoder] = {}
        self.cluster_model = None
        self.feature_columns: List[str] = []
        self.is_fitted = False
        
        logger.info(f"交易聚类分析器初始化完成: algorithm={self.algorithm.value}, n_clusters={self.n_clusters}")
    
    def _parse_algorithm(self, algorithm: str) -> ClusterAlgorithm:
        """解析算法字符串为枚举值"""
        try:
            return ClusterAlgorithm(algorithm.lower())
        except ValueError:
            logger.warning(f"未知算法 '{algorithm}'，使用默认的 KMEANS")
            return ClusterAlgorithm.KMEANS
    
    def _create_imputer(self) -> SimpleImputer:
        """创建缺失值填充器"""
        strategy = self.handle_missing if self.handle_missing in ['mean', 'median'] else 'mean'
        return SimpleImputer(strategy=strategy)
    
    def extract_features(self, trade_data: pd.DataFrame) -> pd.DataFrame:
        """
        从交易数据中提取特征
        
        提取的特征包括:
        - return_pct: 交易收益率 (%)
        - duration_days: 持仓天数
        - seal_ratio: 涨停封单比
        - turnover_rate: 换手率
        - market_regime_encoded: 市场状态编码
        - sector_encoded: 板块编码
        
        Args:
            trade_data: 交易数据DataFrame
            
        Returns:
            特征DataFrame
        """
        if trade_data.empty:
            logger.warning("交易数据为空，返回空特征")
            return pd.DataFrame()
        
        logger.info(f"开始从 {len(trade_data)} 条交易记录中提取特征")
        
        features = pd.DataFrame()
        features['trade_id'] = trade_data['trade_id'] if 'trade_id' in trade_data.columns else trade_data.index.astype(str)
        
        # 1. 交易收益率
        if 'return_pct' in trade_data.columns:
            features['return_pct'] = trade_data['return_pct']
        elif 'buy_price' in trade_data.columns and 'sell_price' in trade_data.columns:
            features['return_pct'] = (trade_data['sell_price'] - trade_data['buy_price']) / trade_data['buy_price'] * 100
        else:
            features['return_pct'] = 0.0
            logger.warning("无法计算收益率，使用默认值0")
        
        # 2. 持仓天数
        if 'duration_days' in trade_data.columns:
            features['duration_days'] = trade_data['duration_days']
        elif 'buy_date' in trade_data.columns and 'sell_date' in trade_data.columns:
            features['duration_days'] = self._calculate_duration(trade_data['buy_date'], trade_data['sell_date'])
        else:
            features['duration_days'] = 2  # 默认2天
        
        # 3. 因子值
        factor_cols = ['seal_ratio', 'turnover_rate', 'open_change_pct', 'limit_up_time', 'break_count']
        for col in factor_cols:
            if col in trade_data.columns:
                features[col] = trade_data[col]
            else:
                features[col] = np.nan
        
        # 4. 市场状态编码
        if 'market_regime' in trade_data.columns:
            features['market_regime'] = trade_data['market_regime']
            features['market_regime_encoded'] = self._encode_categorical(trade_data['market_regime'], 'market_regime')
        else:
            features['market_regime'] = 'unknown'
            features['market_regime_encoded'] = 0
        
        # 5. 板块编码
        if 'sector' in trade_data.columns:
            features['sector'] = trade_data['sector']
            features['sector_encoded'] = self._encode_categorical(trade_data['sector'], 'sector')
        else:
            features['sector'] = 'unknown'
            features['sector_encoded'] = 0
        
        # 6. 盈亏标签
        if 'win_loss' in trade_data.columns:
            features['win_loss'] = trade_data['win_loss']
        else:
            # 根据收益率推断
            features['win_loss'] = (features['return_pct'] > 0).astype(int)
        
        # 7. 股票代码
        if 'ts_code' in trade_data.columns:
            features['ts_code'] = trade_data['ts_code']
        
        # 处理缺失值
        features = self._handle_missing_values(features)
        
        logger.info(f"特征提取完成: {len(features.columns)} 个特征")
        return features
    
    def _calculate_duration(self, buy_dates: pd.Series, sell_dates: pd.Series) -> pd.Series:
        """计算持仓天数"""
        durations = []
        for buy, sell in zip(buy_dates, sell_dates):
            try:
                buy_dt = datetime.strptime(str(buy), '%Y%m%d') if isinstance(buy, str) else buy
                sell_dt = datetime.strptime(str(sell), '%Y%m%d') if isinstance(sell, str) else sell
                duration = (sell_dt - buy_dt).days
                durations.append(max(duration, 1))  # 至少1天
            except:
                durations.append(2)  # 默认2天
        return pd.Series(durations, index=buy_dates.index)
    
    def _encode_categorical(self, series: pd.Series, name: str) -> pd.Series:
        """编码分类变量"""
        if name not in self.label_encoders:
            self.label_encoders[name] = LabelEncoder()
            encoded = self.label_encoders[name].fit_transform(series.astype(str))
        else:
            # 处理新类别
            le = self.label_encoders[name]
            values = series.astype(str)
            known_classes = set(le.classes_)
            new_values = []
            for v in values:
                if v in known_classes:
                    new_values.append(le.transform([v])[0])
                else:
                    new_values.append(-1)  # 未知类别标记为-1
            encoded = np.array(new_values)
        return pd.Series(encoded, index=series.index)
    
    def _handle_missing_values(self, features: pd.DataFrame) -> pd.DataFrame:
        """处理缺失值"""
        numeric_cols = features.select_dtypes(include=[np.number]).columns
        
        if self.handle_missing == 'drop':
            return features.dropna()
        else:
            # 使用imputer填充 - 为每列创建新的imputer避免状态问题
            for col in numeric_cols:
                if features[col].isna().any():
                    # 只对当前列进行填充
                    col_data = features[[col]].copy()
                    # 检查是否所有值都是NaN
                    if col_data.isna().all().all():
                        # 如果全为NaN，填充为0
                        features[col] = features[col].fillna(0)
                    else:
                        # 创建新的imputer
                        imputer = SimpleImputer(strategy=self.handle_missing if self.handle_missing in ['mean', 'median'] else 'mean')
                        imputed = imputer.fit_transform(col_data)
                        features[col] = imputed
            return features
    
    def _get_feature_matrix(self, features: pd.DataFrame) -> np.ndarray:
        """获取用于聚类的特征矩阵"""
        # 选择数值特征用于聚类
        exclude_cols = ['trade_id', 'ts_code', 'win_loss', 'market_regime', 'sector']
        feature_cols = [col for col in features.columns 
                       if col not in exclude_cols and features[col].dtype in ['float64', 'int64', 'float32', 'int32']]
        
        self.feature_columns = feature_cols
        X = features[feature_cols].values
        
        # 再次检查并处理任何剩余的NaN值
        if np.isnan(X).any():
            X = np.nan_to_num(X, nan=0.0)
        
        # 标准化
        if not self.is_fitted:
            X_scaled = self.scaler.fit_transform(X)
        else:
            X_scaled = self.scaler.transform(X)
        
        return X_scaled
    
    def fit_predict(self, features: pd.DataFrame) -> Dict[str, Any]:
        """
        执行聚类并返回结果
        
        Args:
            features: 特征DataFrame
            
        Returns:
            聚类结果字典，包含:
            - cluster_labels: 聚类标签数组
            - silhouette_score: 轮廓分数
            - calinski_harabasz_score: Calinski-Harabasz分数
            - cluster_centers: 聚类中心 (仅K-means和层次聚类)
            - algorithm: 使用的算法
            - n_clusters: 聚类数量
        """
        if features.empty:
            logger.warning("特征数据为空，无法聚类")
            return {
                'cluster_labels': [],
                'silhouette_score': 0,
                'calinski_harabasz_score': 0,
                'cluster_centers': [],
                'algorithm': self.algorithm.value,
                'n_clusters': 0
            }
        
        logger.info(f"开始使用 {self.algorithm.value} 算法进行聚类")
        
        # 获取特征矩阵
        X = self._get_feature_matrix(features)
        
        # 执行聚类
        if self.algorithm == ClusterAlgorithm.KMEANS:
            labels, centers = self._fit_kmeans(X)
        elif self.algorithm == ClusterAlgorithm.DBSCAN:
            labels, centers = self._fit_dbscan(X)
        elif self.algorithm == ClusterAlgorithm.HIERARCHICAL:
            labels, centers = self._fit_hierarchical(X)
        else:
            labels, centers = self._fit_kmeans(X)
        
        # 计算评估指标
        metrics = self._calculate_metrics(X, labels)
        
        self.is_fitted = True
        
        result = {
            'cluster_labels': labels.tolist(),
            'silhouette_score': metrics['silhouette_score'],
            'calinski_harabasz_score': metrics['calinski_harabasz_score'],
            'cluster_centers': centers.tolist() if centers is not None else [],
            'algorithm': self.algorithm.value,
            'n_clusters': len(set(labels)) - (1 if -1 in labels else 0)
        }
        
        logger.info(f"聚类完成: {result['n_clusters']} 个聚类, 轮廓分数: {result['silhouette_score']:.3f}")
        
        return result
    
    def _fit_kmeans(self, X: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """执行K-means聚类"""
        self.cluster_model = KMeans(
            n_clusters=self.n_clusters,
            random_state=self.random_state,
            n_init=10
        )
        labels = self.cluster_model.fit_predict(X)
        centers = self.cluster_model.cluster_centers_
        return labels, centers
    
    def _fit_dbscan(self, X: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """执行DBSCAN聚类"""
        self.cluster_model = DBSCAN(
            eps=self.eps,
            min_samples=self.min_samples
        )
        labels = self.cluster_model.fit_predict(X)
        # DBSCAN没有聚类中心
        return labels, None
    
    def _fit_hierarchical(self, X: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """执行层次聚类"""
        self.cluster_model = AgglomerativeClustering(
            n_clusters=self.n_clusters
        )
        labels = self.cluster_model.fit_predict(X)
        # 层次聚类没有显式的聚类中心，计算每个簇的均值
        centers = np.array([X[labels == i].mean(axis=0) for i in range(self.n_clusters)])
        return labels, centers
    
    def _calculate_metrics(self, X: np.ndarray, labels: np.ndarray) -> Dict[str, float]:
        """计算聚类评估指标"""
        metrics = {
            'silhouette_score': 0.0,
            'calinski_harabasz_score': 0.0
        }
        
        # 过滤噪声点 (DBSCAN中的-1)
        mask = labels != -1
        if mask.sum() > 1:
            X_filtered = X[mask]
            labels_filtered = labels[mask]
            
            n_clusters = len(set(labels_filtered))
            
            if n_clusters > 1:
                try:
                    metrics['silhouette_score'] = silhouette_score(X_filtered, labels_filtered)
                except Exception as e:
                    logger.debug(f"计算轮廓分数失败: {e}")
                
                try:
                    metrics['calinski_harabasz_score'] = calinski_harabasz_score(X_filtered, labels_filtered)
                except Exception as e:
                    logger.debug(f"计算Calinski-Harabasz分数失败: {e}")
        
        return metrics
    
    def analyze_clusters(self, clustered_data: pd.DataFrame) -> Dict[str, Any]:
        """
        分析聚类特征
        
        Args:
            clustered_data: 带聚类标签的数据，需要包含 'cluster_label' 列
            
        Returns:
            聚类分析结果字典，包含:
            - cluster_stats: 每个聚类的统计信息
            - winning_patterns: 盈利聚类ID列表
            - losing_patterns: 亏损聚类ID列表
            - overall_quality: 整体聚类质量评估
        """
        if clustered_data.empty or 'cluster_label' not in clustered_data.columns:
            logger.warning("聚类数据为空或缺少cluster_label列")
            return {
                'cluster_stats': {},
                'winning_patterns': [],
                'losing_patterns': [],
                'overall_quality': {}
            }
        
        logger.info(f"开始分析 {len(clustered_data)} 条记录的聚类特征")
        
        cluster_stats = {}
        winning_patterns = []
        losing_patterns = []
        
        # 获取所有聚类ID (排除噪声点-1)
        cluster_ids = sorted([cid for cid in clustered_data['cluster_label'].unique() if cid != -1])
        
        for cluster_id in cluster_ids:
            cluster_data = clustered_data[clustered_data['cluster_label'] == cluster_id]
            
            # 基础统计
            trade_count = len(cluster_data)
            
            # 胜率
            if 'win_loss' in cluster_data.columns:
                win_count = cluster_data['win_loss'].sum()
                win_rate = (win_count / trade_count * 100) if trade_count > 0 else 0
            else:
                win_rate = 50.0  # 默认50%
            
            # 收益率统计
            if 'return_pct' in cluster_data.columns:
                avg_return = cluster_data['return_pct'].mean()
                std_return = cluster_data['return_pct'].std()
                median_return = cluster_data['return_pct'].median()
                max_return = cluster_data['return_pct'].max()
                min_return = cluster_data['return_pct'].min()
            else:
                avg_return = std_return = median_return = max_return = min_return = 0
            
            # 因子分布
            factor_distributions = {}
            factor_cols = ['seal_ratio', 'turnover_rate', 'duration_days', 'open_change_pct']
            for col in factor_cols:
                if col in cluster_data.columns:
                    factor_distributions[col] = {
                        'mean': float(cluster_data[col].mean()),
                        'std': float(cluster_data[col].std()),
                        'median': float(cluster_data[col].median()),
                        'min': float(cluster_data[col].min()),
                        'max': float(cluster_data[col].max())
                    }
            
            # 主导市场状态
            if 'market_regime' in cluster_data.columns:
                dominant_regime = cluster_data['market_regime'].mode()
                dominant_regime = dominant_regime.iloc[0] if not dominant_regime.empty else 'unknown'
            else:
                dominant_regime = 'unknown'
            
            # 主导板块
            if 'sector' in cluster_data.columns:
                dominant_sector = cluster_data['sector'].mode()
                dominant_sector = dominant_sector.iloc[0] if not dominant_sector.empty else 'unknown'
            else:
                dominant_sector = 'unknown'
            
            # 创建聚类分析对象
            analysis = ClusterAnalysis(
                cluster_id=cluster_id,
                trade_count=trade_count,
                win_rate=win_rate,
                avg_return=avg_return,
                std_return=std_return,
                factor_distributions=factor_distributions,
                dominant_regime=dominant_regime,
                dominant_sector=dominant_sector
            )
            
            cluster_stats[cluster_id] = analysis.to_dict()
            
            # 识别盈利/亏损模式
            # 胜率 > 60% 且平均收益 > 3% 视为盈利聚类
            if win_rate > 60 and avg_return > 3:
                winning_patterns.append(cluster_id)
            # 胜率 < 40% 或平均收益 < -2% 视为亏损聚类
            elif win_rate < 40 or avg_return < -2:
                losing_patterns.append(cluster_id)
        
        # 整体质量评估
        overall_quality = self._assess_overall_quality(clustered_data, cluster_stats)
        
        result = {
            'cluster_stats': cluster_stats,
            'winning_patterns': winning_patterns,
            'losing_patterns': losing_patterns,
            'overall_quality': overall_quality
        }
        
        logger.info(f"聚类分析完成: {len(winning_patterns)} 个盈利模式, {len(losing_patterns)} 个亏损模式")
        
        return result
    
    def _assess_overall_quality(self, clustered_data: pd.DataFrame, 
                                 cluster_stats: Dict) -> Dict[str, float]:
        """评估整体聚类质量"""
        quality = {
            'separation_score': 0.0,
            'stability_score': 0.0,
            'actionability_score': 0.0
        }
        
        if not cluster_stats:
            return quality
        
        # 分离度评分: 聚类间平均收益率差异
        returns = [stats['avg_return'] for stats in cluster_stats.values()]
        if len(returns) > 1:
            return_std = np.std(returns)
            # 标准差越大，分离度越高，满分10分
            quality['separation_score'] = min(return_std / 2, 10.0)
        
        # 稳定性评分: 聚类内标准差的倒数
        stds = [stats['std_return'] for stats in cluster_stats.values() if stats['std_return'] > 0]
        if stds:
            avg_stability = np.mean([1 / (std + 0.1) for std in stds])
            quality['stability_score'] = min(avg_stability * 2, 10.0)
        
        # 可执行性评分: 盈利和亏损聚类的清晰度
        win_rates = [stats['win_rate'] for stats in cluster_stats.values()]
        if win_rates:
            # 胜率分布越两极化，可执行性越高
            extreme_rates = [wr for wr in win_rates if wr > 65 or wr < 35]
            quality['actionability_score'] = len(extreme_rates) / len(win_rates) * 10
        
        return quality
    
    def get_trading_recommendations(self, analysis_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        基于聚类分析生成交易建议
        
        Args:
            analysis_result: analyze_clusters的返回结果
            
        Returns:
            交易建议字典，包含:
            - favorable_conditions: 有利交易条件
            - avoid_conditions: 应避免的条件
            - optimal_parameters: 最优参数建议
            - risk_factors: 风险因素
        """
        cluster_stats = analysis_result.get('cluster_stats', {})
        winning_patterns = analysis_result.get('winning_patterns', [])
        losing_patterns = analysis_result.get('losing_patterns', [])
        
        recommendations = {
            'favorable_conditions': [],
            'avoid_conditions': [],
            'optimal_parameters': {},
            'risk_factors': []
        }
        
        # 分析盈利聚类的共同特征
        if winning_patterns:
            winning_stats = [cluster_stats[cid] for cid in winning_patterns if cid in cluster_stats]
            
            if winning_stats:
                # 提取共同因子特征
                avg_seal_ratios = [s['factor_distributions'].get('seal_ratio', {}).get('mean', 0) 
                                  for s in winning_stats if 'seal_ratio' in s.get('factor_distributions', {})]
                avg_turnovers = [s['factor_distributions'].get('turnover_rate', {}).get('mean', 0) 
                                for s in winning_stats if 'turnover_rate' in s.get('factor_distributions', {})]
                
                if avg_seal_ratios:
                    avg_seal = np.mean(avg_seal_ratios)
                    recommendations['favorable_conditions'].append(
                        f"涨停封单比(seal_ratio) >= {avg_seal:.3f}"
                    )
                    recommendations['optimal_parameters']['min_seal_ratio'] = round(avg_seal * 0.9, 3)
                
                if avg_turnovers:
                    avg_turnover = np.mean(avg_turnovers)
                    recommendations['favorable_conditions'].append(
                        f"换手率(turnover_rate)在 {avg_turnover:.3f} 附近"
                    )
                    recommendations['optimal_parameters']['target_turnover_rate'] = round(avg_turnover, 3)
                
                # 市场状态
                regimes = [s['dominant_regime'] for s in winning_stats]
                if regimes:
                    from collections import Counter
                    regime_counts = Counter(regimes)
                    best_regime = regime_counts.most_common(1)[0][0]
                    recommendations['favorable_conditions'].append(
                        f"市场状态为 '{best_regime}' 时表现较好"
                    )
                
                # 板块
                sectors = [s['dominant_sector'] for s in winning_stats if s['dominant_sector'] != 'unknown']
                if sectors:
                    from collections import Counter
                    sector_counts = Counter(sectors)
                    best_sectors = [s for s, c in sector_counts.most_common(2)]
                    recommendations['favorable_conditions'].append(
                        f"推荐板块: {', '.join(best_sectors)}"
                    )
        
        # 分析亏损聚类的特征
        if losing_patterns:
            losing_stats = [cluster_stats[cid] for cid in losing_patterns if cid in cluster_stats]
            
            if losing_stats:
                avg_seal_ratios = [s['factor_distributions'].get('seal_ratio', {}).get('mean', 0) 
                                  for s in losing_stats if 'seal_ratio' in s.get('factor_distributions', {})]
                avg_turnovers = [s['factor_distributions'].get('turnover_rate', {}).get('mean', 0) 
                                for s in losing_stats if 'turnover_rate' in s.get('factor_distributions', {})]
                
                if avg_seal_ratios:
                    avg_seal = np.mean(avg_seal_ratios)
                    recommendations['avoid_conditions'].append(
                        f"避免涨停封单比(seal_ratio) < {avg_seal * 1.2:.3f} 的股票"
                    )
                
                if avg_turnovers:
                    avg_turnover = np.mean(avg_turnovers)
                    recommendations['avoid_conditions'].append(
                        f"避免换手率(turnover_rate) > {avg_turnover:.3f} 的股票"
                    )
                
                # 风险因素
                recommendations['risk_factors'].append(
                    f"低胜率聚类平均收益率: {np.mean([s['avg_return'] for s in losing_stats]):.2f}%"
                )
        
        # 添加通用建议
        if not recommendations['favorable_conditions']:
            recommendations['favorable_conditions'].append("数据不足，无法确定最优条件")
        
        if not recommendations['avoid_conditions']:
            recommendations['avoid_conditions'].append("数据不足，无法确定风险条件")
        
        return recommendations
    
    def get_cluster_summary(self, clustered_data: pd.DataFrame) -> Dict[str, Any]:
        """
        获取聚类摘要信息
        
        Args:
            clustered_data: 带聚类标签的数据
            
        Returns:
            摘要字典
        """
        if clustered_data.empty or 'cluster_label' not in clustered_data.columns:
            return {
                'total_clusters': 0,
                'total_trades': 0,
                'cluster_distribution': {}
            }
        
        cluster_counts = clustered_data['cluster_label'].value_counts().to_dict()
        
        return {
            'total_clusters': len([c for c in cluster_counts.keys() if c != -1]),
            'total_trades': len(clustered_data),
            'cluster_distribution': cluster_counts,
            'noise_points': cluster_counts.get(-1, 0)  # DBSCAN噪声点
        }
    
    def export_results(self, result: Dict[str, Any], output_path: str):
        """
        导出聚类结果到JSON文件
        
        Args:
            result: 聚类结果字典
            output_path: 输出文件路径
        """
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            logger.info(f"聚类结果已导出到: {output_path}")
        except Exception as e:
            logger.error(f"导出结果失败: {e}")
    
    def predict_cluster(self, new_features: pd.DataFrame) -> np.ndarray:
        """
        预测新数据的聚类标签
        
        Args:
            new_features: 新特征数据
            
        Returns:
            聚类标签数组
        """
        if not self.is_fitted:
            logger.error("模型尚未训练，无法预测")
            return np.array([])
        
        # 提取特征矩阵
        X = self._get_feature_matrix(new_features)
        
        if self.algorithm == ClusterAlgorithm.KMEANS:
            labels = self.cluster_model.predict(X)
        elif self.algorithm == ClusterAlgorithm.DBSCAN:
            # DBSCAN不支持predict，使用近似方法
            labels = self._approximate_dbscan_predict(X)
        elif self.algorithm == ClusterAlgorithm.HIERARCHICAL:
            # 层次聚类使用训练好的模型
            labels = self.cluster_model.fit_predict(X)
        else:
            labels = self.cluster_model.predict(X)
        
        return labels
    
    def _approximate_dbscan_predict(self, X: np.ndarray) -> np.ndarray:
        """DBSCAN的近似预测方法"""
        # 找到最近的训练样本的聚类标签
        # 这里简化处理，实际应该保存训练数据
        logger.warning("DBSCAN不支持直接预测，返回-1（未知）")
        return np.full(len(X), -1)


# ==================== 便捷函数 ====================

def create_trade_clustering(config_path: Optional[str] = None) -> TradeClustering:
    """
    创建交易聚类分析器实例（使用配置文件）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        TradeClustering实例
    """
    config = {
        'n_clusters': 3,
        'algorithm': 'kmeans',
        'random_state': 42,
        'handle_missing': 'mean'
    }
    
    # 加载配置文件
    if config_path and os.path.exists(config_path):
        import yaml
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config and 'trade_clustering' in file_config:
                    tc_config = file_config['trade_clustering']
                    config.update(tc_config)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}")
    
    return TradeClustering(config)


def analyze_trade_patterns(trade_data: pd.DataFrame, 
                           algorithm: str = 'kmeans',
                           n_clusters: int = 3) -> Dict[str, Any]:
    """
    便捷函数：分析交易模式
    
    Args:
        trade_data: 交易数据
        algorithm: 聚类算法
        n_clusters: 聚类数量
        
    Returns:
        完整的分析结果
    """
    config = {
        'algorithm': algorithm,
        'n_clusters': n_clusters,
        'random_state': 42
    }
    
    clustering = TradeClustering(config)
    
    # 特征提取
    features = clustering.extract_features(trade_data)
    
    # 聚类
    cluster_result = clustering.fit_predict(features)
    
    # 添加聚类标签
    features['cluster_label'] = cluster_result['cluster_labels']
    
    # 聚类分析
    analysis = clustering.analyze_clusters(features)
    
    # 交易建议
    recommendations = clustering.get_trading_recommendations(analysis)
    
    return {
        'features': features,
        'cluster_result': cluster_result,
        'analysis': analysis,
        'recommendations': recommendations
    }


# ==================== 主函数 ====================



# ==================== 便捷函数 ====================

def create_trade_clustering(config_path: Optional[str] = None) -> TradeClustering:
    """
    创建交易聚类分析器实例（使用配置文件）
    
    Args:
        config_path: 配置文件路径
        
    Returns:
        TradeClustering实例
    """
    config = {
        'n_clusters': 3,
        'algorithm': 'kmeans',
        'random_state': 42,
        'handle_missing': 'mean'
    }
    
    # 加载配置文件
    if config_path and os.path.exists(config_path):
        import yaml
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                if file_config and 'trade_clustering' in file_config:
                    tc_config = file_config['trade_clustering']
                    config.update(tc_config)
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}")
    
    return TradeClustering(config)


def analyze_trade_patterns(trade_data: pd.DataFrame, 
                           algorithm: str = 'kmeans',
                           n_clusters: int = 3) -> Dict[str, Any]:
    """
    便捷函数：分析交易模式
    
    Args:
        trade_data: 交易数据
        algorithm: 聚类算法
        n_clusters: 聚类数量
        
    Returns:
        完整的分析结果
    """
    config = {
        'algorithm': algorithm,
        'n_clusters': n_clusters,
        'random_state': 42
    }
    
    clustering = TradeClustering(config)
    
    # 特征提取
    features = clustering.extract_features(trade_data)
    
    # 聚类
    cluster_result = clustering.fit_predict(features)
    
    # 添加聚类标签
    features['cluster_label'] = cluster_result['cluster_labels']
    
    # 聚类分析
    analysis = clustering.analyze_clusters(features)
    
    # 交易建议
    recommendations = clustering.get_trading_recommendations(analysis)
    
    return {
        'features': features,
        'cluster_result': cluster_result,
        'analysis': analysis,
        'recommendations': recommendations
    }


# ==================== 主函数 ====================

if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试数据
    np.random.seed(42)
    n_samples = 60
    
    test_data = pd.DataFrame({
        'trade_id': [f'trade_{i:03d}' for i in range(n_samples)],
        'ts_code': [f'{600000+i:06d}.SZ' for i in range(n_samples)],
        'buy_price': np.random.uniform(10, 50, n_samples),
        'sell_price': np.random.uniform(10, 55, n_samples),
        'buy_date': ['20240101'] * n_samples,
        'sell_date': ['20240103'] * n_samples,
        'seal_ratio': np.concatenate([
            np.random.uniform(0.15, 0.25, 20),
            np.random.uniform(0.05, 0.10, 20),
            np.random.uniform(0.10, 0.15, 20)
        ]),
        'turnover_rate': np.concatenate([
            np.random.uniform(0.05, 0.10, 20),
            np.random.uniform(0.12, 0.18, 20),
            np.random.uniform(0.08, 0.12, 20)
        ]),
        'market_regime': np.random.choice(['bull', 'bear', 'sideways'], n_samples),
        'sector': np.random.choice(['tech', 'finance', 'healthcare', 'energy'], n_samples),
        'win_loss': np.concatenate([
            np.random.choice([0, 1], 20, p=[0.2, 0.8]),
            np.random.choice([0, 1], 20, p=[0.8, 0.2]),
            np.random.choice([0, 1], 20, p=[0.5, 0.5])
        ])
    })
    
    # 调整sell_price使其与win_loss一致
    for i in range(n_samples):
        if test_data.loc[i, 'win_loss'] == 1:
            test_data.loc[i, 'sell_price'] = test_data.loc[i, 'buy_price'] * 1.05
        else:
            test_data.loc[i, 'sell_price'] = test_data.loc[i, 'buy_price'] * 0.97
    
    # 测试聚类分析
    print("\n=== 测试交易聚类分析 ===")
    clustering = TradeClustering({'n_clusters': 3})
    
    # 特征提取
    features = clustering.extract_features(test_data)
    print(f"特征提取完成: {len(features)} 条记录")
    
    # 聚类
    result = clustering.fit_predict(features)
    print(f"聚类完成: {result['n_clusters']} 个聚类")
    print(f"轮廓分数: {result['silhouette_score']:.3f}")
    
    # 添加聚类标签
    features['cluster_label'] = result['cluster_labels']
    
    # 聚类分析
    analysis = clustering.analyze_clusters(features)
    print(f"\n盈利模式: {analysis['winning_patterns']}")
    print(f"亏损模式: {analysis['losing_patterns']}")
    
    # 交易建议
    recommendations = clustering.get_trading_recommendations(analysis)
    print(f"\n有利条件: {recommendations['favorable_conditions']}")
    print(f"避免条件: {recommendations['avoid_conditions']}")
    
    print("\n✅ 测试完成!")
