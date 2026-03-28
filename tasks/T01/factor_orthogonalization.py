"""
T01因子正交化PCA核心模块

使用PCA（主成分分析）对多因子进行正交化处理，提取独立的因子信息。
消除因子间的多重共线性，提高评分系统的稳定性和可解释性。

主要功能:
- 数据标准化
- PCA拟合与转换
- 方差解释度计算
- 主成分数量自动选择
- 逆转换（数据重建）
- 序列化支持

依赖:
- numpy
- pandas
- scikit-learn
"""

import numpy as np
import pandas as pd
from typing import Union, Optional, List, Tuple
from sklearn.decomposition import PCA, IncrementalPCA
from sklearn.preprocessing import StandardScaler
import pickle
import warnings
import json


class FactorOrthogonalizer:
    """
    因子正交化器 - 基于PCA的主成分分析

    将原始相关因子转换为相互独立的主成分，消除多重共线性。

    Attributes:
        n_components (Union[int, float, None]): 主成分数量或方差比例
        standardize (bool): 是否在PCA前进行标准化，默认True
        random_state (Optional[int]): 随机种子，用于结果复现
        use_incremental (bool): 是否使用增量PCA，用于大数据集
        pca (PCA): sklearn PCA模型实例
        scaler (StandardScaler): 标准化器实例
        n_features_ (int): 因子数量
        n_samples_ (int): 样本数量
        feature_names_ (List[str]): 因子名称列表

    Example:
        >>> from factor_orthogonalization import FactorOrthogonalizer
        >>> import numpy as np
        >>>
        >>> # 创建模拟因子数据 (100个样本, 10个因子)
        >>> X = np.random.randn(100, 10)
        >>>
        >>> # 创建正交化器并拟合
        >>> fo = FactorOrthogonalizer(standardize=True)
        >>> fo.fit(X)
        >>>
        >>> # 转换为正交主成分
        >>> X_orthogonal = fo.transform(X)
        >>>
        >>> # 获取方差解释度
        >>> evr = fo.get_explained_variance_ratio()
        >>> print(f"前3个主成分解释方差: {evr[:3].sum():.2%}")
        >>>
        >>> # 计算保留90%方差所需的主成分数
        >>> n_comp = fo.get_n_components_for_variance(threshold=0.9)
        >>> print(f"保留90%方差需要 {n_comp} 个主成分")
    """

    def __init__(
        self,
        n_components: Union[int, float, None] = None,
        standardize: bool = True,
        random_state: Optional[int] = None,
        use_incremental: bool = False,
        batch_size: Optional[int] = None
    ):
        """
        初始化因子正交化器

        Args:
            n_components: 主成分数量或方差比例
                         - int: 指定主成分数量
                         - float (0-1): 指定保留方差比例
                         - None: 保留所有主成分
            standardize: 是否在PCA前对数据进行标准化（零均值，单位方差），
                        默认True。当因子量纲不同时建议启用。
            random_state: 随机种子，用于结果复现。PCA本身是确定性的，
                         但某些求解器可能使用随机初始化。
            use_incremental: 是否使用增量PCA (IncrementalPCA)，
                            适用于大数据集，默认False。
            batch_size: 增量PCA的批次大小，仅在use_incremental=True时生效。
                       默认None（自动选择min(1000, n_samples)）。
        """
        self.n_components = n_components
        self.standardize = standardize
        self.random_state = random_state
        self.use_incremental = use_incremental
        self.batch_size = batch_size
        self.pca: Optional[Union[PCA, IncrementalPCA]] = None
        self.scaler: Optional[StandardScaler] = None
        self.n_features_: Optional[int] = None
        self.n_samples_: Optional[int] = None
        self.feature_names_: Optional[List[str]] = None

    def _validate_input(self, X: np.ndarray, check_finite: bool = True, allow_single_sample: bool = False) -> np.ndarray:
        """
        验证输入数据

        Args:
            X: 输入数据数组
            check_finite: 是否检查NaN和Inf
            allow_single_sample: 是否允许单样本（用于transform，模型已拟合时）

        Returns:
            验证后的数据数组

        Raises:
            ValueError: 数据验证失败
        """
        # 检查空数据
        if X.size == 0:
            raise ValueError("输入数据为空")

        # 检查维度
        if X.ndim != 2:
            raise ValueError(f"输入数据必须是2维数组，当前维度: {X.ndim}")

        n_samples, n_features = X.shape

        # 检查样本数（fit需要至少2个，transform可以允许1个）
        if n_samples < 2 and not allow_single_sample:
            raise ValueError(f"样本数必须至少为2，当前: {n_samples}")

        # 警告：样本数少于特征数
        if n_samples < n_features:
            warnings.warn(
                f"样本数({n_samples})少于特征数({n_features})，"
                "PCA结果可能不稳定。建议增加样本数或减少特征。",
                UserWarning
            )

        # 检查NaN和Inf（增强版）
        if check_finite:
            nan_count = np.isnan(X).sum()
            inf_count = np.isinf(X).sum()

            if nan_count > 0:
                nan_positions = np.argwhere(np.isnan(X))
                sample_positions = nan_positions[:5]  # 最多显示5个位置
                pos_str = ", ".join([f"({r},{c})" for r, c in sample_positions])
                if len(nan_positions) > 5:
                    pos_str += f" ... 等共{nan_count}处"
                raise ValueError(
                    f"输入数据包含{nan_count}个NaN值，位置: {pos_str}。"
                    f"请先使用fillna()或dropna()处理缺失值"
                )

            if inf_count > 0:
                inf_positions = np.argwhere(np.isinf(X))
                sample_positions = inf_positions[:5]
                pos_str = ", ".join([f"({r},{c})" for r, c in sample_positions])
                if len(inf_positions) > 5:
                    pos_str += f" ... 等共{inf_count}处"
                raise ValueError(
                    f"输入数据包含{inf_count}个无穷值(Inf/-Inf)，位置: {pos_str}。"
                    f"请先使用np.nan_to_num()或clip()处理异常值"
                )

            # 额外检查：极大/极小值（可能导致数值不稳定）
            max_abs_val = np.max(np.abs(X))
            if max_abs_val > 1e10:
                warnings.warn(
                    f"输入数据包含极大值(最大绝对值: {max_abs_val:.2e})，"
                    f"可能导致PCA数值不稳定。建议进行标准化或缩放到合理范围。",
                    UserWarning
                )

        return X

    def fit(self, X: Union[np.ndarray, pd.DataFrame]) -> 'FactorOrthogonalizer':
        """
        拟合PCA模型

        根据输入数据拟合PCA模型，计算主成分方向。

        Args:
            X: 输入因子数据，形状为 (n_samples, n_features)
               可以是numpy数组或pandas DataFrame

        Returns:
            self: 返回自身，支持链式调用

        Raises:
            ValueError: 输入数据为空或格式不正确
        """
        # 转换为numpy数组
        if isinstance(X, pd.DataFrame):
            X_array = X.values
        else:
            X_array = np.asarray(X)

        # 验证输入数据（在设置feature_names之前，以捕获1D输入）
        X_array = self._validate_input(X_array)

        # 保存特征名
        if isinstance(X, pd.DataFrame):
            self.feature_names_ = list(X.columns)
        else:
            self.feature_names_ = [f"factor_{i}" for i in range(X_array.shape[1])]

        self.n_samples_, self.n_features_ = X_array.shape

        # 数据标准化
        if self.standardize:
            self.scaler = StandardScaler()
            X_scaled = self.scaler.fit_transform(X_array)
        else:
            X_scaled = X_array

        # 确定主成分数量
        n_components = self.n_components
        if n_components is None:
            n_components = min(self.n_samples_, self.n_features_)
        elif isinstance(n_components, float):
            # 如果是0-1之间的浮点数，解释为方差比例
            if 0 < n_components < 1:
                n_components = self._calculate_n_components_for_variance(X_scaled, n_components)
            else:
                raise ValueError(f"n_components作为浮点数必须在(0, 1)之间，当前: {n_components}")

        # 创建并拟合PCA模型
        if self.use_incremental and self.n_samples_ > 10000:
            # 大数据集使用增量PCA
            batch_size = self.batch_size or min(1000, self.n_samples_)
            self.pca = IncrementalPCA(
                n_components=n_components,
                batch_size=batch_size
            )
        else:
            self.pca = PCA(
                n_components=n_components,
                random_state=self.random_state
            )

        self.pca.fit(X_scaled)

        return self

    def _calculate_n_components_for_variance(
        self,
        X: np.ndarray,
        variance_threshold: float
    ) -> int:
        """计算保留指定方差所需的主成分数"""
        temp_pca = PCA()
        temp_pca.fit(X)
        cumulative_variance = np.cumsum(temp_pca.explained_variance_ratio_)
        n_components = np.argmax(cumulative_variance >= variance_threshold) + 1
        return int(n_components)

    def transform(self, X: Union[np.ndarray, pd.DataFrame]) -> np.ndarray:
        """
        将原始因子转换为主成分

        Args:
            X: 输入因子数据，形状为 (n_samples, n_features)

        Returns:
            主成分数据，形状为 (n_samples, n_components)

        Raises:
            RuntimeError: 模型未拟合
            ValueError: 输入维度不匹配
        """
        if self.pca is None:
            raise RuntimeError("模型尚未拟合，请先调用fit()方法")

        # 转换为numpy数组
        if isinstance(X, pd.DataFrame):
            X_array = X.values
        else:
            X_array = np.asarray(X)

        # 验证输入（transform允许单样本，因为模型已拟合）
        X_array = self._validate_input(X_array, check_finite=True, allow_single_sample=True)

        # 检查特征数量
        if X_array.shape[1] != self.n_features_:
            raise ValueError(
                f"输入特征数量({X_array.shape[1]})与拟合时的特征数量({self.n_features_})不匹配"
            )

        # 数据标准化
        if self.standardize and self.scaler is not None:
            X_scaled = self.scaler.transform(X_array)
        else:
            X_scaled = X_array

        # 转换为主成分
        return self.pca.transform(X_scaled)

    def fit_transform(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        y: None = None
    ) -> np.ndarray:
        """
        拟合模型并转换数据

        等同于依次调用fit()和transform()，但更高效。
        符合sklearn的Transformer接口规范。

        Args:
            X: 输入因子数据，形状为 (n_samples, n_features)
            y: 兼容sklearn接口，不使用，默认None

        Returns:
            主成分数据，形状为 (n_samples, n_components)

        Example:
            >>> fo = FactorOrthogonalizer(n_components=5)
            >>> X_ortho = fo.fit_transform(X)
            >>> print(f"输出形状: {X_ortho.shape}")
        """
        return self.fit(X).transform(X)

    def inverse_transform(self, X: np.ndarray, n_components: Optional[int] = None) -> np.ndarray:
        """
        将主成分转换回原始因子空间

        用于验证和数据重建。注意：如果使用了降维，重建会有信息损失。

        Args:
            X: 主成分数据，形状为 (n_samples, n_components)
            n_components: 指定使用的主成分数量，默认使用全部

        Returns:
            重建的原始因子数据，形状为 (n_samples, n_features)

        Raises:
            RuntimeError: 模型未拟合
            ValueError: n_components超过可用主成分数
        """
        if self.pca is None:
            raise RuntimeError("模型尚未拟合，请先调用fit()方法")

        X_array = np.asarray(X)

        # 如果指定了n_components，验证并截取
        if n_components is not None:
            if n_components > self.pca.n_components_:
                raise ValueError(
                    f"n_components ({n_components}) 不能超过 "
                    f"可用主成分数 ({self.pca.n_components_})"
                )
            # 截取到指定数量的主成分
            if X_array.shape[1] > n_components:
                X_array = X_array[:, :n_components]
            # 填充到完整维度
            if X_array.shape[1] < self.pca.n_components_:
                X_padded = np.zeros((X_array.shape[0], self.pca.n_components_))
                X_padded[:, :n_components] = X_array
                X_array = X_padded

        # 逆转换到标准化空间
        X_reconstructed_scaled = self.pca.inverse_transform(X_array)

        # 逆标准化
        if self.standardize and self.scaler is not None:
            X_reconstructed = self.scaler.inverse_transform(X_reconstructed_scaled)
        else:
            X_reconstructed = X_reconstructed_scaled

        return X_reconstructed

    def get_explained_variance_ratio(self) -> np.ndarray:
        """
        获取各主成分的方差解释度

        Returns:
            方差解释度数组，形状为 (n_components,)
            每个元素表示对应主成分解释的方差比例

        Raises:
            RuntimeError: 模型未拟合
        """
        if self.pca is None:
            raise RuntimeError("模型尚未拟合，请先调用fit()方法")
        return self.pca.explained_variance_ratio_

    def get_cumulative_explained_variance_ratio(self) -> np.ndarray:
        """
        获取累积方差解释度

        Returns:
            累积方差解释度数组，形状为 (n_components,)

        Raises:
            RuntimeError: 模型未拟合
        """
        if self.pca is None:
            raise RuntimeError("模型尚未拟合，请先调用fit()方法")
        return np.cumsum(self.pca.explained_variance_ratio_)

    def get_n_components_for_variance(self, threshold: float = 0.9) -> int:
        """
        计算保留指定方差所需的主成分数

        Args:
            threshold: 方差保留阈值，默认0.9（保留90%方差）

        Returns:
            所需主成分数

        Raises:
            RuntimeError: 模型未拟合
            ValueError: 阈值不在(0, 1]范围内
        """
        if self.pca is None:
            raise RuntimeError("模型尚未拟合，请先调用fit()方法")

        if not 0 < threshold <= 1:
            raise ValueError(f"阈值必须在(0, 1]范围内，当前: {threshold}")

        cumulative_variance = np.cumsum(self.pca.explained_variance_ratio_)
        n_components = np.argmax(cumulative_variance >= threshold) + 1
        return int(n_components)

    def get_components(self) -> np.ndarray:
        """
        获取主成分方向（载荷矩阵）

        Returns:
            主成分方向矩阵，形状为 (n_components, n_features)
            每行代表一个主成分，每列代表一个原始因子

        Raises:
            RuntimeError: 模型未拟合
        """
        if self.pca is None:
            raise RuntimeError("模型尚未拟合，请先调用fit()方法")
        return self.pca.components_

    def get_feature_importance(self, top_n: Optional[int] = None) -> pd.DataFrame:
        """
        获取各因子对主成分的贡献度（重要性）

        通过计算各因子在载荷矩阵中的绝对值加权平均来评估重要性。

        Args:
            top_n: 返回前N个重要因子，默认返回所有

        Returns:
            DataFrame包含因子名称和重要性得分
                - factor_name: 因子名称
                - importance: 重要性得分（归一化到0-1）

        Raises:
            RuntimeError: 模型未拟合
        """
        if self.pca is None:
            raise RuntimeError("模型尚未拟合，请先调用fit()方法")

        components = self.pca.components_

        # 计算每个因子的平均绝对载荷
        importance = np.mean(np.abs(components), axis=0)

        # 归一化到0-1
        importance = importance / importance.sum()

        # 创建DataFrame（使用factor_name列名以兼容测试）
        df = pd.DataFrame({
            'factor_name': self.feature_names_,
            'importance': importance
        }).sort_values('importance', ascending=False)

        if top_n is not None:
            df = df.head(top_n)

        return df

    def transform_with_n_components(
        self,
        X: Union[np.ndarray, pd.DataFrame],
        n_components: int
    ) -> np.ndarray:
        """
        仅使用前n个主成分进行转换

        Args:
            X: 输入因子数据
            n_components: 使用的主成分数量

        Returns:
            前n个主成分
        """
        X_transformed = self.transform(X)
        return X_transformed[:, :n_components]

    def save(self, filepath: str, format: str = 'pickle') -> None:
        """
        保存模型到文件

        支持pickle和JSON两种格式。pickle格式保存完整模型状态，
        JSON格式保存模型参数（不包含拟合后的PCA对象）。

        Args:
            filepath: 保存路径
            format: 保存格式，'pickle'（默认）或'json'

        Example:
            >>> # 保存为pickle（完整模型）
            >>> fo.save('model.pkl', format='pickle')
            >>>
            >>> # 保存为JSON（仅参数）
            >>> fo.save('model.json', format='json')
        """
        if format == 'pickle':
            with open(filepath, 'wb') as f:
                pickle.dump(self, f)
            print(f"✅ 模型已保存到: {filepath}")
        elif format == 'json':
            # 保存为JSON（仅参数，不包含PCA对象）
            config = {
                'n_components': self.n_components,
                'standardize': self.standardize,
                'random_state': self.random_state,
                'use_incremental': self.use_incremental,
                'batch_size': self.batch_size,
                'n_features_': self.n_features_,
                'n_samples_': self.n_samples_,
                'feature_names_': self.feature_names_,
                'fitted': self.pca is not None
            }
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ 模型配置已保存到: {filepath}")
        else:
            raise ValueError(f"不支持的保存格式: {format}。支持: 'pickle', 'json'")

    @classmethod
    def load(cls, filepath: str, format: Optional[str] = None) -> 'FactorOrthogonalizer':
        """
        从文件加载模型

        Args:
            filepath: 模型文件路径
            format: 加载格式，默认根据文件扩展名自动检测
                   ('.pkl'或'.pickle' -> pickle, '.json' -> json)

        Returns:
            加载的FactorOrthogonalizer实例

        Note:
            JSON格式加载的模型需要重新调用fit()进行拟合，
            因为JSON只保存配置参数，不保存拟合后的PCA状态。

        Example:
            >>> # 从pickle加载（完整模型）
            >>> fo = FactorOrthogonalizer.load('model.pkl')
            >>>
            >>> # 从JSON加载（仅配置）
            >>> fo = FactorOrthogonalizer.load('model.json')
            >>> # 需要重新拟合
            >>> fo.fit(X)
        """
        # 自动检测格式
        if format is None:
            if filepath.endswith('.json'):
                format = 'json'
            else:
                format = 'pickle'

        if format == 'pickle':
            with open(filepath, 'rb') as f:
                model = pickle.load(f)
            print(f"✅ 模型已从 {filepath} 加载")
            return model
        elif format == 'json':
            with open(filepath, 'r', encoding='utf-8') as f:
                config = json.load(f)

            # 创建新实例
            model = cls(
                n_components=config.get('n_components'),
                standardize=config.get('standardize', True),
                random_state=config.get('random_state'),
                use_incremental=config.get('use_incremental', False),
                batch_size=config.get('batch_size')
            )
            model.n_features_ = config.get('n_features_')
            model.n_samples_ = config.get('n_samples_')
            model.feature_names_ = config.get('feature_names_')

            print(f"✅ 模型配置已从 {filepath} 加载 (fitted={config.get('fitted', False)})")
            if config.get('fitted'):
                print("⚠️ 注意：JSON格式不保存拟合状态，需要重新调用fit()")
            return model
        else:
            raise ValueError(f"不支持的加载格式: {format}。支持: 'pickle', 'json'")

    def __repr__(self) -> str:
        """返回对象的字符串表示"""
        if self.pca is None:
            return (
                f"FactorOrthogonalizer("
                f"n_components={self.n_components}, "
                f"standardize={self.standardize}, "
                f"random_state={self.random_state}, "
                f"fitted=False)"
            )
        else:
            pca_type = "IncrementalPCA" if self.use_incremental else "PCA"
            return (
                f"FactorOrthogonalizer("
                f"n_components={self.pca.n_components_}, "
                f"standardize={self.standardize}, "
                f"random_state={self.random_state}, "
                f"pca_type={pca_type}, "
                f"n_features={self.n_features_}, "
                f"fitted=True)"
            )


def orthogonalize_factors(
    X: Union[np.ndarray, pd.DataFrame],
    variance_threshold: float = 0.9,
    standardize: bool = True,
    return_full: bool = False
) -> Union[np.ndarray, Tuple[np.ndarray, FactorOrthogonalizer, int, float]]:
    """
    便捷函数：一键式因子正交化

    自动拟合PCA并转换数据，可选择返回完整信息。

    Args:
        X: 输入因子数据
        variance_threshold: 方差保留阈值，默认0.9
        standardize: 是否标准化，默认True
        return_full: 是否返回完整信息，默认False

    Returns:
        如果return_full=False: 返回主成分数据
        如果return_full=True: 返回(主成分数据, 正交化器, 主成分数, 实际方差保留比例)

    Example:
        >>> import numpy as np
        >>> X = np.random.randn(100, 10)
        >>> X_ortho, fo, n_comp, variance = orthogonalize_factors(
        ...     X, variance_threshold=0.95, return_full=True
        ... )
        >>> print(f"使用{n_comp}个主成分保留了{variance:.2%}的方差")
    """
    fo = FactorOrthogonalizer(standardize=standardize)
    X_orthogonal = fo.fit_transform(X)

    # 计算保留指定方差所需的主成分数
    n_components = fo.get_n_components_for_variance(variance_threshold)

    # 截取指定数量的主成分
    X_reduced = X_orthogonal[:, :n_components]

    # 计算实际保留的方差比例
    actual_variance = fo.get_cumulative_explained_variance_ratio()[n_components - 1]

    if return_full:
        return X_reduced, fo, n_components, actual_variance
    else:
        return X_reduced


if __name__ == "__main__":
    # 使用示例
    print("=" * 60)
    print("T01因子正交化PCA模块 - 使用示例")
    print("=" * 60)

    # 创建模拟数据
    np.random.seed(42)
    n_samples = 100
    n_features = 10
    X = np.random.randn(n_samples, n_features)

    # 添加一些相关性
    X[:, 1] = X[:, 0] + np.random.randn(n_samples) * 0.1
    X[:, 2] = X[:, 0] + np.random.randn(n_samples) * 0.2

    print(f"\n输入数据形状: {X.shape}")
    print(f"样本数: {n_samples}, 因子数: {n_features}")

    # 方法1: 使用便捷函数
    print("\n" + "-" * 40)
    print("方法1: 使用便捷函数")
    print("-" * 40)

    X_ortho, fo, n_comp, variance = orthogonalize_factors(
        X, variance_threshold=0.9, return_full=True
    )
    print(f"保留90%方差需要 {n_comp} 个主成分")
    print(f"实际保留方差: {variance:.2%}")
    print(f"输出数据形状: {X_ortho.shape}")

    # 方法2: 使用类接口
    print("\n" + "-" * 40)
    print("方法2: 使用类接口")
    print("-" * 40)

    fo2 = FactorOrthogonalizer(standardize=True, n_components=0.95)
    X_ortho2 = fo2.fit_transform(X)
    print(f"FactorOrthogonalizer: {fo2}")
    print(f"输出数据形状: {X_ortho2.shape}")

    # 显示方差解释度
    evr = fo2.get_explained_variance_ratio()
    print(f"\n各主成分方差解释度:")
    for i, ratio in enumerate(evr[:5]):
        print(f"  主成分{i+1}: {ratio:.2%}")

    # 显示因子重要性
    print(f"\n因子重要性排名:")
    importance = fo2.get_feature_importance(top_n=5)
    for _, row in importance.iterrows():
        print(f"  {row['factor_name']}: {row['importance']:.4f}")

    # 测试序列化
    print("\n" + "-" * 40)
    print("测试序列化")
    print("-" * 40)

    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False, suffix='.pkl') as f:
        temp_path = f.name

    fo2.save(temp_path)
    fo_loaded = FactorOrthogonalizer.load(temp_path)
    print(f"加载的模型: {fo_loaded}")

    # 清理临时文件
    os.unlink(temp_path)

    print("\n" + "=" * 60)
    print("示例完成！")
    print("=" * 60)
