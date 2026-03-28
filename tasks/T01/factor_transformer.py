"""
因子映射与转换模块

提供因子到主成分的映射转换功能，以及主成分到评分的转换。
支持因子贡献度分析和转换精度验证。

主要功能:
- 原始因子→主成分映射
- 主成分→评分转换
- 因子贡献度计算
- 转换精度验证

依赖:
- numpy
- pandas
- scikit-learn
- factor_orthogonalization (任务1.1)
"""

import numpy as np
import pandas as pd
from typing import Union, Optional, List, Dict, Any
from sklearn.metrics import mean_squared_error

from factor_orthogonalization import FactorOrthogonalizer


class FactorTransformer:
    """
    因子转换器 - 实现因子到主成分的映射与转换
    
    将原始相关因子转换为相互独立的主成分，并进一步转换为股票评分。
    支持因子贡献度分析和转换精度验证。
    
    Attributes:
        orthogonalizer (FactorOrthogonalizer): 正交化器实例
        variance_threshold (float): 方差保留阈值
        feature_names (List[str]): 因子名称列表
        n_components (int): 主成分数量
        component_weights (np.ndarray): 主成分权重
    
    Example:
        >>> from factor_transformer import FactorTransformer
        >>> import pandas as pd
        >>> import numpy as np
        >>> 
        >>> # 创建模拟因子数据
        >>> np.random.seed(42)
        >>> factor_data = pd.DataFrame({
        ...     'momentum': np.random.randn(100),
        ...     'volume': np.random.randn(100),
        ...     'volatility': np.random.randn(100),
        ... })
        >>> 
        >>> # 创建转换器并映射
        >>> transformer = FactorTransformer(variance_threshold=0.9)
        >>> result = transformer.map_factors_to_components(factor_data)
        >>> 
        >>> # 转换为评分
        >>> scores = transformer.components_to_scores()
        >>> print(f"评分范围: [{scores.min():.2f}, {scores.max():.2f}]")
        >>> 
        >>> # 查看因子贡献度
        >>> contribution = transformer.get_factor_contribution(0)
        >>> print(contribution)
        >>> 
        >>> # 验证转换精度
        >>> validation = transformer.validate_transformation(factor_data)
        >>> print(f"重构误差: {validation['reconstruction_error']:.4f}")
    """
    
    def __init__(
        self,
        orthogonalizer: Optional[FactorOrthogonalizer] = None,
        variance_threshold: float = 0.9
    ):
        """
        初始化因子转换器
        
        Args:
            orthogonalizer: 已拟合的正交化器实例，如果为None则会在首次映射时创建
            variance_threshold: 方差保留阈值，范围 (0, 1]，默认0.9
                               用于自动选择保留多少主成分
        """
        self.orthogonalizer = orthogonalizer
        self.variance_threshold = variance_threshold
        self.feature_names: Optional[List[str]] = None
        self.n_components: Optional[int] = None
        self.component_weights: Optional[np.ndarray] = None
        self._components_df: Optional[pd.DataFrame] = None
        self._index: Optional[pd.Index] = None
        
        # 如果提供了已拟合的正交化器，提取其信息
        if orthogonalizer is not None and orthogonalizer.pca is not None:
            self.feature_names = orthogonalizer.feature_names_
            self.n_components = orthogonalizer.n_features_
    
    def map_factors_to_components(
        self,
        factor_df: pd.DataFrame,
        n_components: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        将原始因子映射到主成分
        
        使用PCA将原始相关因子转换为相互独立的主成分，
        并保留映射关系以便后续追溯。
        
        Args:
            factor_df: 原始因子DataFrame，形状为 (n_samples, n_features)
                      行索引通常为股票代码，列名为因子名称
            n_components: 指定保留的主成分数量，默认根据variance_threshold自动选择
        
        Returns:
            Dict包含:
                - 'components': 主成分DataFrame，形状为 (n_samples, n_components)
                - 'mapping_info': 映射信息字典，包含:
                    - 'feature_names': 原始因子名称列表
                    - 'n_original_features': 原始因子数量
                    - 'n_components': 主成分数量
                    - 'explained_variance_ratio': 各主成分方差解释度
                    - 'cumulative_variance_ratio': 累积方差解释度
                    - 'variance_threshold': 使用的方差阈值
                - 'orthogonalizer': 拟合后的正交化器实例
        
        Raises:
            ValueError: 输入数据为空、样本数量不足或格式不正确
        
        Example:
            >>> transformer = FactorTransformer()
            >>> result = transformer.map_factors_to_components(factor_data)
            >>> components_df = result['components']
            >>> mapping_info = result['mapping_info']
        """
        # 验证输入
        if factor_df.empty:
            raise ValueError("输入数据不能为空")
        
        if len(factor_df) < 2:
            raise ValueError(f"样本数量必须至少为2，当前: {len(factor_df)}")
        
        # 保存原始索引和因子名称
        self._index = factor_df.index
        self.feature_names = list(factor_df.columns)
        
        # 创建或复用正交化器
        if self.orthogonalizer is None:
            self.orthogonalizer = FactorOrthogonalizer(standardize=True)
            components_array = self.orthogonalizer.fit_transform(factor_df)
        else:
            components_array = self.orthogonalizer.transform(factor_df)
        
        # 确定主成分数量
        if n_components is None:
            self.n_components = self.orthogonalizer.get_n_components_for_variance(
                self.variance_threshold
            )
        else:
            self.n_components = min(n_components, components_array.shape[1])
        
        # 截取指定数量的主成分
        components_reduced = components_array[:, :self.n_components]
        
        # 创建主成分DataFrame
        component_names = [f'PC{i+1}' for i in range(self.n_components)]
        self._components_df = pd.DataFrame(
            components_reduced,
            index=self._index,
            columns=component_names
        )
        
        # 计算默认权重（基于方差解释度）
        evr = self.orthogonalizer.get_explained_variance_ratio()
        self.component_weights = evr[:self.n_components]
        self.component_weights = self.component_weights / self.component_weights.sum()
        
        # 构建映射信息
        cumulative_evr = np.cumsum(evr)
        mapping_info = {
            'feature_names': self.feature_names,
            'n_original_features': len(self.feature_names),
            'n_components': self.n_components,
            'explained_variance_ratio': evr[:self.n_components],
            'cumulative_variance_ratio': cumulative_evr[:self.n_components],
            'variance_threshold': self.variance_threshold,
            'total_explained_variance': cumulative_evr[self.n_components - 1]
        }
        
        return {
            'components': self._components_df,
            'mapping_info': mapping_info,
            'orthogonalizer': self.orthogonalizer
        }
    
    def components_to_scores(
        self,
        components_df: Optional[pd.DataFrame] = None,
        weights: Optional[np.ndarray] = None,
        equal_weights: bool = False,
        use_variance_weights: bool = False
    ) -> pd.Series:
        """
        将主成分转换为股票评分
        
        使用加权平均方法将主成分转换为综合评分。
        支持多种权重策略：自定义权重、等权重、基于方差的权重。
        
        Args:
            components_df: 主成分DataFrame，默认使用map_factors_to_components的结果
            weights: 自定义权重数组，长度应等于主成分数量
            equal_weights: 是否使用等权重，默认False
            use_variance_weights: 是否使用基于方差解释度的权重，默认False
                                如果weights和equal_weights都未指定，则默认使用此方法
        
        Returns:
            scores: 股票评分Series，索引与输入数据相同
        
        Raises:
            RuntimeError: 在调用map_factors_to_components之前调用此方法
            ValueError: 权重长度与主成分数量不匹配
        
        Example:
            >>> # 使用默认方差权重
            >>> scores = transformer.components_to_scores()
            >>> 
            >>> # 使用等权重
            >>> scores = transformer.components_to_scores(equal_weights=True)
            >>> 
            >>> # 使用自定义权重
            >>> custom_weights = np.array([0.5, 0.3, 0.2])
            >>> scores = transformer.components_to_scores(weights=custom_weights)
        """
        self._check_fitted()
        
        # 使用提供的主成分数据或内部存储的数据
        if components_df is not None:
            comp_array = components_df.values
            index = components_df.index
        else:
            if self._components_df is None:
                raise RuntimeError("没有可用的主成分数据")
            comp_array = self._components_df.values
            index = self._index
        
        n_comp = comp_array.shape[1]
        
        # 确定权重
        if weights is not None:
            weights_array = np.asarray(weights)
            if len(weights_array) != n_comp:
                raise ValueError(
                    f"权重长度 ({len(weights_array)}) 与主成分数量 ({n_comp}) 不匹配"
                )
        elif equal_weights:
            weights_array = np.ones(n_comp) / n_comp
        elif use_variance_weights or self.component_weights is None:
            # 使用方差解释度作为权重
            evr = self.orthogonalizer.get_explained_variance_ratio()[:n_comp]
            weights_array = evr / evr.sum()
        else:
            weights_array = self.component_weights[:n_comp]
            if len(weights_array) != n_comp:
                # 重新计算权重
                evr = self.orthogonalizer.get_explained_variance_ratio()[:n_comp]
                weights_array = evr / evr.sum()
        
        # 计算加权评分
        scores_array = np.dot(comp_array, weights_array)
        
        # 创建Series
        scores = pd.Series(scores_array, index=index, name='score')
        
        return scores
    
    def get_factor_contribution(
        self,
        component_idx: Union[int, List[int], str] = 0
    ) -> pd.DataFrame:
        """
        获取各原始因子对主成分的贡献度
        
        计算每个原始因子对指定主成分的贡献程度，
        贡献度基于PCA载荷矩阵的绝对值。
        
        Args:
            component_idx: 主成分索引，可以是:
                          - int: 单个主成分索引（0-based）
                          - List[int]: 多个主成分索引
                          - 'all': 所有主成分
        
        Returns:
            contribution_df: 贡献度DataFrame
                如果查询单个主成分:
                    - factor_name: 因子名称
                    - contribution: 贡献度（归一化到0-1）
                如果查询多个主成分:
                    - factor_name: 因子名称
                    - PC1, PC2, ...: 各主成分的贡献度
                    - average: 平均贡献度
        
        Raises:
            RuntimeError: 在调用map_factors_to_components之前调用此方法
            ValueError: 主成分索引无效
        
        Example:
            >>> # 查看第一个主成分的因子贡献
            >>> contribution = transformer.get_factor_contribution(0)
            >>> 
            >>> # 查看前两个主成分的因子贡献
            >>> contribution = transformer.get_factor_contribution([0, 1])
            >>> 
            >>> # 查看所有主成分的因子贡献
            >>> contribution = transformer.get_factor_contribution('all')
        """
        self._check_fitted()
        
        # 获取载荷矩阵
        components_matrix = self.orthogonalizer.get_components()
        
        # 处理component_idx参数
        if component_idx == 'all':
            indices = list(range(self.n_components))
        elif isinstance(component_idx, int):
            if component_idx < 0 or component_idx >= self.n_components:
                raise ValueError(
                    f"无效的主成分索引: {component_idx}，有效范围: [0, {self.n_components-1}]"
                )
            indices = [component_idx]
        elif isinstance(component_idx, (list, tuple)):
            for idx in component_idx:
                if idx < 0 or idx >= self.n_components:
                    raise ValueError(
                        f"无效的主成分索引: {idx}，有效范围: [0, {self.n_components-1}]"
                    )
            indices = component_idx
        else:
            raise ValueError(f"无效的component_idx类型: {type(component_idx)}")
        
        if len(indices) == 1:
            # 单个主成分
            idx = indices[0]
            loadings = np.abs(components_matrix[idx, :])
            # 归一化
            loadings = loadings / loadings.sum()
            
            contribution_df = pd.DataFrame({
                'factor_name': self.feature_names,
                'contribution': loadings
            }).sort_values('contribution', ascending=False)
        else:
            # 多个主成分
            data = {'factor_name': self.feature_names}
            
            for idx in indices:
                loadings = np.abs(components_matrix[idx, :])
                data[f'PC{idx+1}'] = loadings
            
            contribution_df = pd.DataFrame(data)
            # 计算平均贡献度
            pc_columns = [c for c in contribution_df.columns if c.startswith('PC')]
            contribution_df['average'] = contribution_df[pc_columns].mean(axis=1)
            contribution_df = contribution_df.sort_values('average', ascending=False)
        
        return contribution_df
    
    def validate_transformation(
        self,
        original_data: pd.DataFrame,
        n_components: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        验证转换精度并计算重构误差
        
        通过将主成分逆转换回原始因子空间，计算重构误差，
        验证PCA转换的精度和信息保留程度。
        
        Args:
            original_data: 原始因子数据，用于计算重构误差
            n_components: 用于重建的主成分数量，默认使用全部
        
        Returns:
            validation_result: 验证结果字典，包含:
                - 'reconstruction_error': 相对重构误差（相对于数据标准差）
                - 'max_absolute_error': 最大绝对误差
                - 'mean_squared_error': 均方误差
                - 'explained_variance': 解释的方差比例
                - 'n_components_used': 使用的主成分数量
                - 'is_valid': 是否通过验证（误差<1%）
        
        Raises:
            RuntimeError: 在调用map_factors_to_components之前调用此方法
            ValueError: 输入数据特征数量与拟合时不一致
        
        Example:
            >>> validation = transformer.validate_transformation(original_data)
            >>> print(f"重构误差: {validation['reconstruction_error']:.4f}")
            >>> print(f"验证通过: {validation['is_valid']}")
            >>> 
            >>> # 使用部分主成分验证
            >>> validation = transformer.validate_transformation(original_data, n_components=3)
        """
        self._check_fitted()
        
        # 验证特征数量
        if list(original_data.columns) != self.feature_names:
            raise ValueError(
                "输入数据的特征与拟合时不一致"
            )
        
        original_array = original_data.values
        
        # 转换到主成分空间
        components_full = self.orthogonalizer.transform(original_data)
        
        # 确定使用的主成分数量
        if n_components is None:
            n_comp = self.n_components
        else:
            n_comp = min(n_components, components_full.shape[1])
        
        # 使用指定数量的主成分进行重建
        components_subset = components_full[:, :n_comp]
        
        # 填充到完整维度（如果需要）
        if n_comp < components_full.shape[1]:
            components_padded = np.zeros_like(components_full)
            components_padded[:, :n_comp] = components_subset
        else:
            components_padded = components_subset
        
        # 逆转换重建原始数据
        reconstructed = self.orthogonalizer.inverse_transform(components_padded)
        
        # 计算误差
        diff = original_array - reconstructed
        mse = np.mean(diff ** 2)
        max_abs_error = np.max(np.abs(diff))
        
        # 计算相对重构误差（相对于数据标准差）
        data_std = np.std(original_array)
        if data_std > 0:
            reconstruction_error = np.sqrt(mse) / data_std
        else:
            reconstruction_error = 0.0
        
        # 计算解释的方差
        evr = self.orthogonalizer.get_explained_variance_ratio()
        explained_variance = np.sum(evr[:n_comp])
        
        # 验证是否通过（误差<1%）
        is_valid = reconstruction_error < 0.01
        
        return {
            'reconstruction_error': reconstruction_error,
            'max_absolute_error': max_abs_error,
            'mean_squared_error': mse,
            'explained_variance': explained_variance,
            'n_components_used': n_comp,
            'is_valid': is_valid
        }
    
    def get_component_weights(self) -> pd.DataFrame:
        """
        获取主成分权重信息
        
        Returns:
            weights_df: 权重信息DataFrame，包含:
                - component: 主成分名称
                - explained_variance_ratio: 方差解释度
                - weight: 归一化权重
        
        Raises:
            RuntimeError: 在调用map_factors_to_components之前调用此方法
        """
        self._check_fitted()
        
        evr = self.orthogonalizer.get_explained_variance_ratio()[:self.n_components]
        weights = self.component_weights if self.component_weights is not None else evr / evr.sum()
        
        weights_df = pd.DataFrame({
            'component': [f'PC{i+1}' for i in range(self.n_components)],
            'explained_variance_ratio': evr,
            'weight': weights
        })
        
        return weights_df
    
    def _check_fitted(self) -> None:
        """
        检查是否已进行因子映射
        
        Raises:
            RuntimeError: 尚未调用map_factors_to_components
        """
        if self.orthogonalizer is None:
            raise RuntimeError(
                "尚未进行因子映射。请先调用map_factors_to_components()。"
            )
    
    def __repr__(self) -> str:
        """返回对象字符串表示"""
        if self.orthogonalizer is None:
            return (
                f"FactorTransformer("
                f"variance_threshold={self.variance_threshold}, "
                f"fitted=False)"
            )
        else:
            return (
                f"FactorTransformer("
                f"variance_threshold={self.variance_threshold}, "
                f"n_features={len(self.feature_names) if self.feature_names else 0}, "
                f"n_components={self.n_components}, "
                f"fitted=True)"
            )


def transform_factors_to_scores(
    factor_df: pd.DataFrame,
    variance_threshold: float = 0.9,
    weights: Optional[np.ndarray] = None
) -> pd.Series:
    """
    便捷函数：将因子直接转换为评分
    
    一键完成因子→主成分→评分的完整转换流程。
    
    Args:
        factor_df: 原始因子DataFrame
        variance_threshold: 方差保留阈值，默认0.9
        weights: 主成分权重，默认使用基于方差的权重
    
    Returns:
        scores: 股票评分Series
    
    Example:
        >>> scores = transform_factors_to_scores(factor_data, variance_threshold=0.95)
    """
    transformer = FactorTransformer(variance_threshold=variance_threshold)
    transformer.map_factors_to_components(factor_df)
    scores = transformer.components_to_scores(weights=weights)
    return scores


if __name__ == '__main__':
    # 简单示例
    print("FactorTransformer 示例")
    print("=" * 50)
    
    # 生成模拟数据
    np.random.seed(42)
    n_samples = 100
    
    factor_data = pd.DataFrame({
        'momentum': np.random.randn(n_samples),
        'volume': np.random.randn(n_samples),
        'volatility': np.random.randn(n_samples),
        'liquidity': np.random.randn(n_samples),
        'value': np.random.randn(n_samples),
    })
    factor_data.index = [f'STOCK_{i:04d}' for i in range(n_samples)]
    
    # 创建转换器
    transformer = FactorTransformer(variance_threshold=0.9)
    
    # 因子映射到主成分
    print("\n1. 因子映射到主成分")
    result = transformer.map_factors_to_components(factor_data)
    print(f"   原始因子数: {result['mapping_info']['n_original_features']}")
    print(f"   主成分数: {result['mapping_info']['n_components']}")
    print(f"   累积方差解释度: {result['mapping_info']['total_explained_variance']:.2%}")
    
    # 主成分转换为评分
    print("\n2. 主成分转换为评分")
    scores = transformer.components_to_scores()
    print(f"   评分数量: {len(scores)}")
    print(f"   评分范围: [{scores.min():.2f}, {scores.max():.2f}]")
    print(f"   评分均值: {scores.mean():.2f}")
    print(f"   评分标准差: {scores.std():.2f}")
    
    # 查看因子贡献度
    print("\n3. 第一个主成分的因子贡献度")
    contribution = transformer.get_factor_contribution(0)
    for _, row in contribution.head(3).iterrows():
        print(f"   {row['factor_name']}: {row['contribution']:.3f}")
    
    # 验证转换精度
    print("\n4. 转换精度验证")
    validation = transformer.validate_transformation(factor_data)
    print(f"   重构误差: {validation['reconstruction_error']:.4f}")
    print(f"   验证通过: {validation['is_valid']}")
    
    print("\n" + "=" * 50)
    print("示例完成!")
