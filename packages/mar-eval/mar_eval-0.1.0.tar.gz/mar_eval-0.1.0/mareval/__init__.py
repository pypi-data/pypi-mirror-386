"""
mar-eval: Metal Artifact Reduction Evaluation Toolkit
Implements quantitative analysis routines consistent with Annex GG
of IEC 60601-2-44 Ed. 4 for task-based MAR performance evaluation.
"""

from .cho import CHOModel, compute_auc
from .stats import delta_auc_test, bias_assessment
from .utils import phi

__all__ = ["CHOModel", "compute_auc", "delta_auc_test", "bias_assessment", "phi"]
