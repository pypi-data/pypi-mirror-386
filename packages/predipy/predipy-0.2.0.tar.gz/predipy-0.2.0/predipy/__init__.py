"""
Predipy: Lightweight ML Pipeline with Python-Go Hybrid
Version 0.2.0
"""

from .config import Config
from .predipy import PredipyRegressor, PredipyClassifier, preprocess_data
from .utils.io_helpers import load_dataset
from .preprocess.text import clean_text

# Export utama buat user
__all__ = [
    "Config",
    "PredipyRegressor",
    "PredipyClassifier",
    "preprocess_data",
    "load_dataset",
    "clean_text",
    # opsional: fungsi top-level
    "train_regression",
    "predict_regression",
    "train_classification",
    "predict_classification"
]

__version__ = "0.2.0"
