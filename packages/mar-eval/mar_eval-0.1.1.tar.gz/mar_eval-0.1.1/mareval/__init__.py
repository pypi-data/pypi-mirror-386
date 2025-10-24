"""
mar-eval: Annex GG toolkit for MAR performance evaluation
Implements CHO analysis, AUC computation, and bias assessment utilities.
"""

from .cho import cho_decision_values
from .stats import compute_auc
from . import utils

__all__ = ["cho_decision_values", "compute_auc", "utils"]
__version__ = "0.1.0"
