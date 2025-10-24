import numpy as np
from scipy.stats import ttest_rel

def delta_auc_test(auc_baseline, auc_mar):
    """
    One-tailed paired t-test comparing baseline and MAR AUC values.
    Returns p-value and mean delta AUC.
    """
    delta = np.array(auc_mar) - np.array(auc_baseline)
    _, p_value = ttest_rel(auc_mar, auc_baseline, alternative="greater")
    return p_value, np.mean(delta)

def bias_assessment(auc_resub, auc_holdout):
    """
    Quantify bias between resubstitution and hold-out validation results.
    Positive bias indicates potential overfitting.
    """
    bias = np.mean(auc_resub) - np.mean(auc_holdout)
    return bias
