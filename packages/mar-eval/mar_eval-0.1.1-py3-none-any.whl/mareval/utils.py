import numpy as np
from scipy.stats import norm

def phi(x):
    """Standard normal CDF. """
    return norm.cdf(x)

def print_summary(auc_baseline, auc_mar, p_value, bias):
    print("\n--- MAR-EVAL Summary ---")
    print(f"Baseline AUC: {np.mean(auc_baseline):.3f}")
    print(f"MAR AUC:      {np.mean(auc_mar):.3f}")
    print(f"ΔAUC:         {np.mean(np.array(auc_mar) - np.array(auc_baseline)):.3f}")
    print(f"p-value:      {p_value:.4f}")
    print(f"Bias:         {bias:.4f}")
