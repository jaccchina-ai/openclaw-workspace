#!/usr/bin/env python3
"""
Neural Factor Extractor Module - 神经因子提取器
使用自编码器架构从基础因子中提取新的非线性因子

功能：
1. 数据预处理（标准化、缺失值处理、序列创建）
2. 自编码器模型构建和训练
3. 从瓶颈层提取特征作为新因子
4. 计算IC值并筛选有效因子
5. 支持横截面和时间序列两种提取模式

集成点：
- 与factor_mining.py的Factor类兼容
- 使用pandas DataFrame处理因子数据
- 返回ExtractedFactor对象列表
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from dataclasses import dataclass, field
from datetime import datetime
import logging
import warnings

warnings.filterwarnings('ignore')
logger = logging.getLogger(__name__)


@dataclass
class ExtractedFactor:
    """
    提取的因子数据类
    
    Attributes:
        name: 因子名称
        code: 因子代码
        values: 因子值数组
        ic_value: IC值（与次日收益的相关系数）
        is_valid: 是否有效（|IC| >= threshold）
        description: 因子描述
        category: 因子类别
        extraction_method: 提取方法
    """
    name: str
    code: str
    values: np.ndarray
    ic_value: float = 0.0
    is_valid: bool = False
    description: str = ""
    category: str = "neural"
    extraction_method: str = "autoencoder"
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            'name': self.name,
            'code': self.code,
            'values': self.values.tolist() if isinstance(self.values, np.ndarray) else self.values,
            'ic_value': self.ic_value,
            'is_valid': self.is_valid,
            'description': self.description,
            'category': self.category,
            'extraction_method': self.extraction_method
        }


class NeuralFactorExtractor:
    """
    神经因子提取器
    
    使用自编码器（Autoencoder）架构从基础因子中提取新的非线性组合因子。
    自编码器通过编码器将输入压缩到低维瓶颈层，再通过解码器重建输入。
    瓶颈层的输出作为新的因子特征。
    
    Attributes:
        bottleneck_size: 瓶颈层大小（提取的因子数量）
        epochs: 训练轮数
        learning_rate: 学习率
        ic_threshold: IC值阈值
        batch_size: 批次大小
        validation_split: 验证集比例
        random_state: 随机种子
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化神经因子提取器
        
        Args:
            config: 配置字典，包含以下可选参数：
                - bottleneck_size: 瓶颈层大小（默认5）
                - epochs: 训练轮数（默认50）
                - learning_rate: 学习率（默认0.001）
                - ic_threshold: IC阈值（默认0.03）
                - batch_size: 批次大小（默认32）
                - validation_split: 验证集比例（默认0.2）
                - random_state: 随机种子（默认42）
        """
        self.config = config or {}
        
        # 模型参数
        self.bottleneck_size = self.config.get('bottleneck_size', 5)
        self.epochs = self.config.get('epochs', 50)
        self.learning_rate = self.config.get('learning_rate', 0.001)
        self.ic_threshold = self.config.get('ic_threshold', 0.03)
        self.batch_size = self.config.get('batch_size', 32)
        self.validation_split = self.config.get('validation_split', 0.2)
        self.random_state = self.config.get('random_state', 42)
        
        # 模型对象
        self.autoencoder = None
        self.scaler = None
        self.feature_columns = None
        self.is_fitted = False
        
        logger.info(f"NeuralFactorExtractor初始化完成: bottleneck_size={self.bottleneck_size}")
    
    def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """
        获取特征列（排除元数据列）
        
        Args:
            df: 输入DataFrame
            
        Returns:
            特征列名称列表
        """
        # 排除的元数据列
        exclude_cols = ['ts_code', 'trade_date', 'next_day_return', 'close', 'open', 'high', 'low', 'vol', 'amount']
        
        # 选择数值列且不在排除列表中的列
        feature_cols = []
        for col in df.columns:
            if col not in exclude_cols:
                # 检查是否为数值类型
                if pd.api.types.is_numeric_dtype(df[col]):
                    feature_cols.append(col)
        
        return feature_cols
    
    def _preprocess_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        数据预处理
        
        步骤：
        1. 处理缺失值（用均值填充）
        2. 标准化（Z-score标准化）
        
        Args:
            df: 原始数据
            
        Returns:
            预处理后的数据
        """
        from sklearn.preprocessing import StandardScaler
        
        df_processed = df.copy()
        
        # 获取特征列
        feature_cols = self._get_feature_columns(df_processed)
        
        if not feature_cols:
            logger.warning("未找到特征列")
            return df_processed
        
        # 处理缺失值 - 用均值填充
        for col in feature_cols:
            if df_processed[col].isnull().any():
                mean_val = df_processed[col].mean()
                df_processed[col] = df_processed[col].fillna(mean_val)
                logger.debug(f"列 {col} 用均值 {mean_val:.4f} 填充了缺失值")
        
        # 标准化
        if self.scaler is None:
            self.scaler = StandardScaler()
            df_processed[feature_cols] = self.scaler.fit_transform(df_processed[feature_cols])
        else:
            df_processed[feature_cols] = self.scaler.transform(df_processed[feature_cols])
        
        return df_processed
    
    def _create_sequences(self, df: pd.DataFrame, sequence_length: int = 10) -> List[np.ndarray]:
        """
        创建时间序列数据
        
        将数据转换为序列形式，用于时间序列因子提取。
        例如，sequence_length=10表示用过去10天的数据预测。
        
        Args:
            df: 输入数据（已按时间排序）
            sequence_length: 序列长度
            
        Returns:
            序列列表
        """
        feature_cols = self._get_feature_columns(df)
        
        if not feature_cols:
            return []
        
        sequences = []
        values = df[feature_cols].values
        
        # 创建滑动窗口序列
        for i in range(len(values) - sequence_length + 1):
            seq = values[i:i + sequence_length]
            sequences.append(seq)
        
        logger.info(f"创建了 {len(sequences)} 个长度为 {sequence_length} 的序列")
        return sequences
    
    def _flatten_sequences(self, sequences: List[np.ndarray]) -> np.ndarray:
        """
        将序列展平为2D数组
        
        Args:
            sequences: 序列列表
            
        Returns:
            展平后的数组
        """
        if not sequences:
            return np.array([])
        
        # 每个序列展平为一行
        flattened = np.array([seq.flatten() for seq in sequences])
        return flattened
    
    def _build_autoencoder(self, n_features: int) -> None:
        """
        构建自编码器模型
        
        使用MLPRegressor构建自编码器：
        - 输入层: n_features
        - 编码器层: 逐渐减小维度
        - 瓶颈层: bottleneck_size（特征提取层）
        - 解码器层: 逐渐恢复维度
        - 输出层: n_features
        
        Args:
            n_features: 输入特征数量
        """
        from sklearn.neural_network import MLPRegressor
        
        # 计算隐藏层结构
        # 编码器: n_features -> hidden1 -> hidden2 -> bottleneck
        # 解码器: bottleneck -> hidden2 -> hidden1 -> n_features
        
        if n_features <= self.bottleneck_size:
            logger.warning(f"特征数 {n_features} 小于等于瓶颈层大小 {self.bottleneck_size}，调整瓶颈层")
            self.bottleneck_size = max(2, n_features // 2)
        
        # 构建对称的隐藏层
        hidden1 = max(self.bottleneck_size * 2, n_features // 2)
        hidden2 = max(self.bottleneck_size, n_features // 4)
        
        hidden_layers = [hidden1, hidden2, self.bottleneck_size, hidden2, hidden1]
        
        logger.info(f"构建自编码器: 输入={n_features}, 隐藏层={hidden_layers}, 瓶颈层={self.bottleneck_size}")
        
        # 创建MLPRegressor作为自编码器
        self.autoencoder = MLPRegressor(
            hidden_layer_sizes=tuple(hidden_layers),
            activation='relu',
            solver='adam',
            learning_rate_init=self.learning_rate,
            max_iter=self.epochs,
            batch_size=self.batch_size,
            validation_fraction=self.validation_split,
            random_state=self.random_state,
            early_stopping=True,
            n_iter_no_change=10,
            verbose=False
        )
        
        self.input_size = n_features
    
    def _extract_bottleneck_features(self, X: np.ndarray) -> np.ndarray:
        """
        从瓶颈层提取特征
        
        通过前向传播到瓶颈层获取压缩表示。
        
        Args:
            X: 输入数据
            
        Returns:
            瓶颈层特征
        """
        if self.autoencoder is None:
            raise ValueError("自编码器未构建，请先调用_fit_autoencoder")
        
        # 使用MLP的中间层输出
        # 我们需要手动实现前向传播到瓶颈层
        
        # 获取权重
        coefs = self.autoencoder.coefs_
        intercepts = self.autoencoder.intercepts_
        
        # 前向传播到瓶颈层
        # 输入层 -> 隐藏层1
        hidden1_input = np.dot(X, coefs[0]) + intercepts[0]
        hidden1_output = np.maximum(hidden1_input, 0)  # ReLU
        
        # 隐藏层1 -> 隐藏层2
        hidden2_input = np.dot(hidden1_output, coefs[1]) + intercepts[1]
        hidden2_output = np.maximum(hidden2_input, 0)  # ReLU
        
        # 隐藏层2 -> 瓶颈层（这是我们要提取的特征）
        bottleneck_input = np.dot(hidden2_output, coefs[2]) + intercepts[2]
        bottleneck_output = np.maximum(bottleneck_input, 0)  # ReLU
        
        return bottleneck_output
    
    def _fit_autoencoder(self, X: np.ndarray) -> None:
        """
        训练自编码器
        
        Args:
            X: 输入数据（目标也是X，因为是自编码器）
        """
        if self.autoencoder is None:
            self._build_autoencoder(X.shape[1])
        
        logger.info(f"开始训练自编码器: 样本数={X.shape[0]}, 特征数={X.shape[1]}")
        
        # 训练自编码器（输入=输出）
        self.autoencoder.fit(X, X)
        
        # 计算重建误差
        X_reconstructed = self.autoencoder.predict(X)
        mse = np.mean((X - X_reconstructed) ** 2)
        logger.info(f"自编码器训练完成，重建MSE: {mse:.6f}")
        
        self.is_fitted = True
    
    def _calculate_ic(self, factor_values: pd.Series, returns: pd.Series, 
                     method: str = 'spearman') -> float:
        """
        计算IC值（信息系数）
        
        IC值衡量因子值与未来收益的相关性。
        
        Args:
            factor_values: 因子值序列
            returns: 收益序列
            method: 相关系数方法 ('spearman' 或 'pearson')
            
        Returns:
            IC值
        """
        try:
            # 去除NaN
            mask = factor_values.notna() & returns.notna()
            f = factor_values[mask]
            r = returns[mask]
            
            if len(f) < 10:
                return 0.0
            
            if method == 'spearman':
                return f.corr(r, method='spearman')
            else:
                return f.corr(r, method='pearson')
        except Exception as e:
            logger.error(f"计算IC失败: {e}")
            return 0.0
    
    def _filter_factors_by_ic(self, factors: List[ExtractedFactor], 
                             threshold: Optional[float] = None) -> List[ExtractedFactor]:
        """
        按IC值筛选因子
        
        Args:
            factors: 因子列表
            threshold: IC阈值（默认使用self.ic_threshold）
            
        Returns:
            筛选后的因子列表
        """
        threshold = threshold or self.ic_threshold
        
        filtered = []
        for factor in factors:
            if abs(factor.ic_value) >= threshold:
                factor.is_valid = True
                filtered.append(factor)
            else:
                factor.is_valid = False
        
        logger.info(f"IC筛选: {len(factors)} 个因子 -> {len(filtered)} 个有效因子 (阈值={threshold})")
        return filtered
    
    def extract_factors(self, df: pd.DataFrame, 
                       extraction_mode: str = 'cross_sectional',
                       sequence_length: int = 10,
                       target_col: str = 'next_day_return') -> List[ExtractedFactor]:
        """
        提取神经因子
        
        主入口方法，支持横截面和时间序列两种提取模式。
        
        Args:
            df: 输入数据DataFrame
            extraction_mode: 提取模式 ('cross_sectional' 或 'time_series')
            sequence_length: 时间序列长度（仅time_series模式使用）
            target_col: 目标收益列名
            
        Returns:
            ExtractedFactor对象列表
        """
        if df.empty:
            logger.warning("输入数据为空")
            return []
        
        logger.info(f"开始提取神经因子: 模式={extraction_mode}, 数据形状={df.shape}")
        
        if extraction_mode == 'cross_sectional':
            return self._extract_cross_sectional(df, target_col)
        elif extraction_mode == 'time_series':
            return self._extract_time_series(df, sequence_length, target_col)
        else:
            raise ValueError(f"不支持的提取模式: {extraction_mode}. 支持 'cross_sectional' 或 'time_series'")
    
    def _extract_cross_sectional(self, df: pd.DataFrame, 
                                target_col: str) -> List[ExtractedFactor]:
        """
        横截面因子提取
        
        在单个时间截面上，跨股票提取因子。
        
        Args:
            df: 输入数据
            target_col: 目标收益列名
            
        Returns:
            提取的因子列表
        """
        # 数据预处理
        df_processed = self._preprocess_data(df)
        
        # 获取特征列
        feature_cols = self._get_feature_columns(df_processed)
        
        if not feature_cols:
            logger.warning("未找到特征列")
            return []
        
        X = df_processed[feature_cols].values
        
        # 构建和训练自编码器
        self._build_autoencoder(X.shape[1])
        self._fit_autoencoder(X)
        
        # 从瓶颈层提取特征
        bottleneck_features = self._extract_bottleneck_features(X)
        
        # 创建因子对象
        factors = []
        for i in range(self.bottleneck_size):
            factor_values = bottleneck_features[:, i]
            
            # 计算IC值
            ic_value = 0.0
            if target_col in df.columns:
                ic_value = self._calculate_ic(
                    pd.Series(factor_values),
                    df[target_col]
                )
            
            factor = ExtractedFactor(
                name=f"neural_factor_{i+1}",
                code=f"nf_{i+1}",
                values=factor_values,
                ic_value=ic_value,
                is_valid=abs(ic_value) >= self.ic_threshold,
                description=f"Autoencoder bottleneck feature {i+1}",
                category="neural",
                extraction_method="autoencoder_cross_sectional"
            )
            factors.append(factor)
        
        # 按IC值排序
        factors.sort(key=lambda x: abs(x.ic_value), reverse=True)
        
        # 筛选有效因子
        valid_factors = self._filter_factors_by_ic(factors)
        
        logger.info(f"横截面提取完成: {len(valid_factors)} 个有效因子")
        return valid_factors
    
    def _extract_time_series(self, df: pd.DataFrame, 
                            sequence_length: int,
                            target_col: str) -> List[ExtractedFactor]:
        """
        时间序列因子提取
        
        使用滑动窗口创建序列，提取时间序列特征。
        
        Args:
            df: 输入数据（需要按时间排序）
            sequence_length: 序列长度
            target_col: 目标收益列名
            
        Returns:
            提取的因子列表
        """
        # 确保数据按时间排序
        if 'trade_date' in df.columns:
            df = df.sort_values('trade_date')
        
        # 数据预处理
        df_processed = self._preprocess_data(df)
        
        # 创建序列
        sequences = self._create_sequences(df_processed, sequence_length)
        
        if not sequences:
            logger.warning("未创建任何序列")
            return []
        
        # 展平序列用于自编码器
        X_flat = self._flatten_sequences(sequences)
        
        # 构建和训练自编码器
        self._build_autoencoder(X_flat.shape[1])
        self._fit_autoencoder(X_flat)
        
        # 从瓶颈层提取特征
        bottleneck_features = self._extract_bottleneck_features(X_flat)
        
        # 创建因子对象
        factors = []
        for i in range(self.bottleneck_size):
            factor_values = bottleneck_features[:, i]
            
            # 对于时间序列，我们需要对齐目标值
            # 序列的起始索引对应的目标值
            ic_value = 0.0
            if target_col in df.columns:
                # 对齐：序列结束后的目标值
                target_values = df[target_col].values[sequence_length - 1:sequence_length - 1 + len(factor_values)]
                if len(target_values) == len(factor_values):
                    ic_value = self._calculate_ic(
                        pd.Series(factor_values),
                        pd.Series(target_values)
                    )
            
            factor = ExtractedFactor(
                name=f"neural_ts_factor_{i+1}",
                code=f"nf_ts_{i+1}",
                values=factor_values,
                ic_value=ic_value,
                is_valid=abs(ic_value) >= self.ic_threshold,
                description=f"Autoencoder time-series feature {i+1}",
                category="neural_time_series",
                extraction_method="autoencoder_time_series"
            )
            factors.append(factor)
        
        # 按IC值排序并筛选
        factors.sort(key=lambda x: abs(x.ic_value), reverse=True)
        valid_factors = self._filter_factors_by_ic(factors)
        
        logger.info(f"时间序列提取完成: {len(valid_factors)} 个有效因子")
        return valid_factors
    
    def get_factor_dataframe(self, factors: List[ExtractedFactor], 
                            index: Optional[pd.Index] = None) -> pd.DataFrame:
        """
        将提取的因子转换为DataFrame
        
        Args:
            factors: 提取的因子列表
            index: 索引（可选）
            
        Returns:
            因子DataFrame
        """
        if not factors:
            return pd.DataFrame()
        
        data = {}
        for factor in factors:
            data[factor.code] = factor.values
        
        df = pd.DataFrame(data)
        
        if index is not None:
            df.index = index[:len(df)]
        
        return df
    
    def get_factor_importance(self, factors: List[ExtractedFactor]) -> pd.DataFrame:
        """
        获取因子重要性排序
        
        Args:
            factors: 提取的因子列表
            
        Returns:
            因子重要性DataFrame
        """
        if not factors:
            return pd.DataFrame()
        
        importance_data = []
        for factor in factors:
            importance_data.append({
                'factor_code': factor.code,
                'factor_name': factor.name,
                'ic_value': factor.ic_value,
                'abs_ic': abs(factor.ic_value),
                'is_valid': factor.is_valid,
                'description': factor.description
            })
        
        df = pd.DataFrame(importance_data)
        df = df.sort_values('abs_ic', ascending=False)
        return df
    
    def transform(self, df: pd.DataFrame) -> np.ndarray:
        """
        使用已训练的自编码器转换新数据
        
        Args:
            df: 输入数据
            
        Returns:
            瓶颈层特征
        """
        if not self.is_fitted:
            raise ValueError("自编码器尚未训练，请先调用extract_factors")
        
        # 预处理
        df_processed = self._preprocess_data(df)
        feature_cols = self._get_feature_columns(df_processed)
        X = df_processed[feature_cols].values
        
        # 提取特征
        return self._extract_bottleneck_features(X)
    
    def save_model(self, path: str) -> None:
        """
        保存模型
        
        Args:
            path: 保存路径
        """
        import pickle
        
        model_data = {
            'autoencoder': self.autoencoder,
            'scaler': self.scaler,
            'config': {
                'bottleneck_size': self.bottleneck_size,
                'epochs': self.epochs,
                'learning_rate': self.learning_rate,
                'ic_threshold': self.ic_threshold,
                'batch_size': self.batch_size,
                'validation_split': self.validation_split,
                'random_state': self.random_state
            },
            'is_fitted': self.is_fitted,
            'input_size': getattr(self, 'input_size', None)
        }
        
        with open(path, 'wb') as f:
            pickle.dump(model_data, f)
        
        logger.info(f"模型已保存到 {path}")
    
    def load_model(self, path: str) -> None:
        """
        加载模型
        
        Args:
            path: 模型路径
        """
        import pickle
        
        with open(path, 'rb') as f:
            model_data = pickle.load(f)
        
        self.autoencoder = model_data['autoencoder']
        self.scaler = model_data['scaler']
        self.is_fitted = model_data['is_fitted']
        self.input_size = model_data.get('input_size')
        
        # 恢复配置
        config = model_data['config']
        self.bottleneck_size = config['bottleneck_size']
        self.epochs = config['epochs']
        self.learning_rate = config['learning_rate']
        self.ic_threshold = config['ic_threshold']
        self.batch_size = config['batch_size']
        self.validation_split = config['validation_split']
        self.random_state = config['random_state']
        
        logger.info(f"模型已从 {path} 加载")


# ==================== 便捷函数 ====================

def create_neural_extractor(config_path: Optional[str] = None, 
                            config_dict: Optional[Dict] = None) -> NeuralFactorExtractor:
    """
    创建神经因子提取器实例
    
    Args:
        config_path: 配置文件路径（YAML）
        config_dict: 配置字典
        
    Returns:
        NeuralFactorExtractor实例
    """
    config = config_dict or {}
    
    # 从文件加载配置
    if config_path:
        try:
            import yaml
            with open(config_path, 'r', encoding='utf-8') as f:
                file_config = yaml.safe_load(f)
                
                # 查找神经因子提取器配置
                if file_config and 'machine_learning' in file_config:
                    ml_config = file_config['machine_learning']
                    if 'neural_factor_extractor' in ml_config:
                        config.update(ml_config['neural_factor_extractor'])
        except Exception as e:
            logger.warning(f"加载配置文件失败: {e}")
    
    return NeuralFactorExtractor(config=config)


def extract_neural_factors(df: pd.DataFrame, 
                          n_factors: int = 5,
                          target_col: str = 'next_day_return',
                          mode: str = 'cross_sectional') -> Tuple[List[ExtractedFactor], pd.DataFrame]:
    """
    便捷函数：提取神经因子
    
    Args:
        df: 输入数据
        n_factors: 要提取的因子数量
        target_col: 目标收益列
        mode: 提取模式
        
    Returns:
        (因子列表, 因子DataFrame)
    """
    config = {
        'bottleneck_size': n_factors,
        'epochs': 50,
        'ic_threshold': 0.03
    }
    
    extractor = NeuralFactorExtractor(config=config)
    factors = extractor.extract_factors(df, extraction_mode=mode, target_col=target_col)
    factor_df = extractor.get_factor_dataframe(factors)
    
    return factors, factor_df


if __name__ == '__main__':
    # 简单测试
    logging.basicConfig(level=logging.INFO)
    
    # 创建测试数据
    np.random.seed(42)
    n_samples = 100
    n_features = 20
    
    test_data = pd.DataFrame(
        np.random.randn(n_samples, n_features),
        columns=[f'factor_{i}' for i in range(n_features)]
    )
    test_data['ts_code'] = [f'00000{i%10}.SZ' for i in range(n_samples)]
    test_data['trade_date'] = '20240301'
    test_data['next_day_return'] = np.random.randn(n_samples) * 0.02
    
    # 创建提取器
    extractor = NeuralFactorExtractor(config={
        'bottleneck_size': 5,
        'epochs': 20,
        'ic_threshold': 0.03
    })
    
    # 提取因子
    factors = extractor.extract_factors(
        test_data,
        extraction_mode='cross_sectional',
        target_col='next_day_return'
    )
    
    print(f"\n提取了 {len(factors)} 个神经因子:")
    for factor in factors:
        print(f"  {factor.name}: IC={factor.ic_value:.4f}, valid={factor.is_valid}")
    
    # 获取重要性
    importance = extractor.get_factor_importance(factors)
    print("\n因子重要性:")
    print(importance)