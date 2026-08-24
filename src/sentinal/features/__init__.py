"""
Module 2 — Feature Engineering
Responsibilities: Convert validated transactions into numeric feature vectors
expected by downstream ML models (XGBoost) without train/serve skew.
"""

from .config import FEATURE_COLUMNS, CATEGORICAL_CATEGORIES
from .pipeline import FeaturePipeline

__all__ = [
    "FEATURE_COLUMNS",
    "CATEGORICAL_CATEGORIES",
    "FeaturePipeline",
]
