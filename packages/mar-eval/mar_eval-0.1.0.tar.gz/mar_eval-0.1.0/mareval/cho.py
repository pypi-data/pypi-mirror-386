import numpy as np
from scipy.stats import norm

class CHOModel:
    """
    Channelized Hotelling Observer (CHO) implementation for task-based
    detectability analysis of CT MAR algorithms.
    """

    def __init__(self, channel_matrix):
        self.U = channel_matrix

    def project(self, image):
        """Project image into channel space. """
        return self.U.T @ image.flatten()

    def compute_test_statistic(self, g_signal, g_noise):
        """Compute CHO template and test statistic values. """
        mu_s = np.mean(g_signal, axis=1)
        mu_n = np.mean(g_noise, axis=1)
        cov = np.cov(np.hstack((g_signal, g_noise)))
        w = np.linalg.pinv(cov) @ (mu_s - mu_n)
        t_s = w @ g_signal
        t_n = w @ g_noise
        return t_s, t_n, w

def compute_auc(t_signal, t_noise):
    """Compute AUC from CHO test statistic distributions. """
    mu_s, mu_n = np.mean(t_signal), np.mean(t_noise)
    std = np.sqrt(0.5 * (np.var(t_signal) + np.var(t_noise)))
    d_prime = (mu_s - mu_n) / std
    return norm.cdf(d_prime / np.sqrt(2))
