"""机器学习相关模块

本模块包含机器学习相关的工具，如统计分析、标签编码等。
"""

from .stats import calculate_classification_metrics
from .label_encoder import LabelEncoder

__all__ = [
    "calculate_classification_metrics",
    "LabelEncoder",
]