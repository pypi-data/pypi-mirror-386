"""
DOP1 - Diabetes Osteoporosis Prediction Package

A Python package for AI-powered analysis of diabetes complicated with osteoporosis.
"""

from .predictor import DOPPredictor
from .utils import load_data, validate_data, save_results
from .exceptions import DOPError, ValidationError, APIError

__version__ = "0.1.0"
__author__ = "DOP Research Team"
__email__ = "research@dop.com"

__all__ = [
    "DOPPredictor",
    "load_data",
    "validate_data", 
    "save_results",
    "DOPError",
    "ValidationError",
    "APIError"
]