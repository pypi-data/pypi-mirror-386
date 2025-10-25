from __future__ import annotations

from typing import List, Optional, Union

import numpy as np
import pandas as pd
from datasets import Dataset, DatasetDict, load_dataset
from iterstrat.ml_stratifiers import MultilabelStratifiedKFold
from sklearn.model_selection import train_test_split

# 配置常量
DEFAULT_TEST_SIZE = 0.2
DEFAULT_RANDOM_STATE = 42
MIN_TEST_SIZE = 0.0
MAX_TEST_SIZE = 1.0


class DataSplitError(Exception):
    """数据分割相关的基础异常类"""

    pass


class ValidationError(DataSplitError):
    """输入验证错误"""

    pass


class StratificationError(DataSplitError):
    """分层抽样错误"""

    pass


def is_multilabel(df: pd.DataFrame, column: str) -> bool:
    """判断指定列是否为多标签数据

    通过检查列中第一个有效值的类型来判断是否为多标签。
    多标签数据的特征是每个样本的标签值为list或numpy数组。

    Args:
        df: 输入数据框
        column: 要检查的标签列名

    Returns:
        bool: 如果是多标签数据返回True，否则返回False

    Examples:
        >>> df = pd.DataFrame({'labels': [['A', 'B'], ['C']]})
        >>> is_multilabel(df, 'labels')
        True

        >>> df = pd.DataFrame({'label': ['A', 'B', 'C']})
        >>> is_multilabel(df, 'label')
        False
    """
    try:
        if not len(df):
            return False
        first_valid_value = df[column].dropna().iloc[0]
        return isinstance(first_valid_value, (list, np.ndarray))
    except (KeyError, IndexError):
        return False


def _validate_inputs(dataset: Union[Dataset, pd.DataFrame], test_size: float, stratify: Optional[str]) -> pd.DataFrame:
    """验证输入参数并转换数据格式

    Args:
        dataset: 输入数据集
        test_size: 测试集比例
        stratify: 分层抽样的列名

    Returns:
        pd.DataFrame: 验证后的数据框

    Raises:
        ValidationError: 当输入参数无效时抛出
    """
    # 验证test_size
    if not MIN_TEST_SIZE < test_size < MAX_TEST_SIZE:
        raise ValidationError(f"test_size must be between {MIN_TEST_SIZE} and {MAX_TEST_SIZE}, got {test_size}")

    # 转换为DataFrame
    if isinstance(dataset, Dataset):
        df = pd.DataFrame(dataset)
    elif isinstance(dataset, pd.DataFrame):
        df = dataset.copy()
    else:
        raise ValidationError(f"dataset must be either a Dataset or DataFrame, got {type(dataset)}")

    # 检查数据是否为空
    if df.empty:
        raise ValidationError("Dataset cannot be empty")

    # 检查是否存在分层列
    if stratify and stratify not in df.columns:
        raise ValidationError(f"Column '{stratify}' not found in dataset. Available columns: {list(df.columns)}")

    return df


def get_label_matrix(labels: List, unique_labels: List) -> np.ndarray:
    """将标签列表转换为多标签二值矩阵

    用于多标签分层抽样时，将每个样本的标签列表转换为one-hot编码的二值矩阵。

    Args:
        labels: 单个样本的标签列表，如 ['A', 'C']
        unique_labels: 所有可能的标签列表，如 ['A', 'B', 'C']

    Returns:
        np.ndarray: 对应的二值向量，如 [1, 0, 1]

    Examples:
        >>> get_label_matrix(['A', 'C'], ['A', 'B', 'C'])
        array([1., 0., 1.])
    """
    matrix = np.zeros(len(unique_labels))
    label_to_index = {label: idx for idx, label in enumerate(unique_labels)}
    for label in labels:
        if label in label_to_index:
            matrix[label_to_index[label]] = 1
    return matrix


def _split_multilabel_data(
    df: pd.DataFrame, stratify_column: str, test_size: float
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """处理多标签数据的分层分割

    Args:
        df: 数据框
        stratify_column: 多标签列名
        test_size: 测试集比例

    Returns:
        tuple[pd.DataFrame, pd.DataFrame]: 训练集和测试集数据框

    Raises:
        StratificationError: 当分层分割失败时抛出
    """
    try:
        # 处理空值
        df_clean = df.dropna(subset=[stratify_column])
        if df_clean.empty:
            raise StratificationError(f"No valid data found in column '{stratify_column}' after removing null values")

        # 获取所有唯一的标签
        unique_labels = list(
            set(
                label
                for labels in df_clean[stratify_column]
                if isinstance(labels, (list, np.ndarray))
                for label in labels
            )
        )

        if not unique_labels:
            raise StratificationError(f"No valid labels found in column '{stratify_column}'")

        # 将标签列表转换为二值矩阵
        label_matrix = np.array([get_label_matrix(labels, unique_labels) for labels in df_clean[stratify_column]])

        # 使用MultilabelStratifiedKFold进行划分
        mskf = MultilabelStratifiedKFold(n_splits=int(1 / test_size), shuffle=True, random_state=DEFAULT_RANDOM_STATE)

        # 获取划分的索引
        train_idx, test_idx = next(mskf.split(df_clean, label_matrix))

        # 使用索引划分数据
        train_df = df_clean.iloc[train_idx]
        test_df = df_clean.iloc[test_idx]

        return train_df, test_df

    except StopIteration:
        raise StratificationError("Failed to split multilabel dataset with given parameters")
    except Exception as e:
        raise StratificationError(f"Error in multilabel stratification: {str(e)}")


def split_dataset(
    dataset: Union[Dataset, pd.DataFrame], test_size: float = DEFAULT_TEST_SIZE, stratify: Optional[str] = None
) -> DatasetDict:
    """将数据集分割为训练集和测试集

    支持单标签和多标签数据的分层抽样，确保训练集和测试集的标签分布保持一致。
    对于多标签数据，使用MultilabelStratifiedKFold进行分层。
    对于单标签数据，使用sklearn的stratify参数。

    Args:
        dataset: 输入数据集，支持HuggingFace Dataset或pandas DataFrame
        test_size: 测试集比例，必须在(0, 1)区间内，默认为0.2
        stratify: 用于分层抽样的列名。如果为None，则进行随机分割

    Returns:
        DatasetDict: 包含'train'和'test'键的数据集字典

    Raises:
        ValidationError: 当输入参数无效时抛出（如test_size超出范围、数据集为空等）
        StratificationError: 当分层抽样失败时抛出（如标签分布不均等）

    Examples:
        >>> # 单标签分层分割
        >>> df = pd.DataFrame({'text': ['a', 'b', 'c'], 'label': [0, 1, 0]})
        >>> result = split_dataset(df, test_size=0.33, stratify='label')
        >>> len(result['train']), len(result['test'])
        (2, 1)

        >>> # 多标签分层分割
        >>> df = pd.DataFrame({'text': ['a', 'b'], 'labels': [['A', 'B'], ['A']]})
        >>> result = split_dataset(df, stratify='labels')
    """
    # 输入验证
    df = _validate_inputs(dataset, test_size, stratify)

    # 执行数据分割
    if stratify is None:
        # 无分层的随机分割
        train_df, test_df = train_test_split(df, test_size=test_size, random_state=DEFAULT_RANDOM_STATE)
    else:
        # 分层分割
        if is_multilabel(df, stratify):
            train_df, test_df = _split_multilabel_data(df, stratify, test_size)
        else:
            # 单标签分层分割
            try:
                train_df, test_df = train_test_split(
                    df, test_size=test_size, stratify=df[stratify], random_state=DEFAULT_RANDOM_STATE
                )
            except ValueError as e:
                raise StratificationError(f"Single-label stratification failed: {str(e)}")

    # 后处理和转换
    return _create_dataset_dict(train_df, test_df)


def _create_dataset_dict(train_df: pd.DataFrame, test_df: pd.DataFrame) -> DatasetDict:
    """将训练和测试数据框转换为DatasetDict

    Args:
        train_df: 训练数据框
        test_df: 测试数据框

    Returns:
        DatasetDict: 包含训练集和测试集的数据集字典
    """
    # 重置索引并删除索引列
    train_df = train_df.reset_index(drop=True)
    test_df = test_df.reset_index(drop=True)

    # 转换为字典格式，避免产生额外的索引列
    train_dict = {col: train_df[col].tolist() for col in train_df.columns}
    test_dict = {col: test_df[col].tolist() for col in test_df.columns}

    # 创建Dataset
    train_dataset = Dataset.from_dict(train_dict)
    test_dataset = Dataset.from_dict(test_dict)

    # 构建DatasetDict
    return DatasetDict(
        {
            "train": train_dataset,
            "test": test_dataset,
        }
    )


def _run_tests() -> None:
    """运行数据分割功能的测试用例"""
    print("=" * 60)
    print("数据集分割功能测试")
    print("=" * 60)

    try:
        # 测试单标签数据
        print("\n1. 测试单标签数据分层分割...")
        single_label_dataset = load_dataset("json", data_files="./../../../testdata/data.jsonl", split="train")
        # 转换为DataFrame以避免类型问题
        single_df = pd.DataFrame(single_label_dataset)
        single_split = split_dataset(single_df, test_size=DEFAULT_TEST_SIZE, stratify="label")

        print(f"   训练集大小: {len(single_split['train'])}")
        print(f"   测试集大小: {len(single_split['test'])}")
        print(f"   总样本数: {len(single_split['train']) + len(single_split['test'])}")

    except Exception as e:
        print(f"   ❌ 单标签测试失败: {e}")

    try:
        # 测试多标签数据
        print("\n2. 测试多标签数据分层分割...")
        multi_label_dataset = load_dataset(
            "json", data_files="./../../../testdata/multilabel_data.jsonl", split="train"
        )
        # 转换为DataFrame以避免类型问题
        multi_df = pd.DataFrame(multi_label_dataset)
        multi_split = split_dataset(multi_df, test_size=DEFAULT_TEST_SIZE, stratify="labels")

        print(f"   训练集大小: {len(multi_split['train'])}")
        print(f"   测试集大小: {len(multi_split['test'])}")
        print(f"   总样本数: {len(multi_split['train']) + len(multi_split['test'])}")

    except Exception as e:
        print(f"   ❌ 多标签测试失败: {e}")

    try:
        # 测试无分层的随机分割
        print("\n3. 测试随机分割（无分层）...")
        random_df = pd.DataFrame({"text": ["a", "b", "c", "d"], "value": [1, 2, 3, 4]})
        random_split = split_dataset(random_df, test_size=0.25)

        print(f"   训练集大小: {len(random_split['train'])}")
        print(f"   测试集大小: {len(random_split['test'])}")

    except Exception as e:
        print(f"   ❌ 随机分割测试失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


if __name__ == "__main__":
    _run_tests()
