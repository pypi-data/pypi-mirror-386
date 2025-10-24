import numpy as np
from sklearn.utils.extmath import safe_sparse_dot

def cho_decision_values(images, template, channels):
    """
    Compute Channelized Hotelling Observer (CHO) decision values for a set of images.

    Parameters
    ----------
    images : np.ndarray
        Array of shape (N, H, W) or (N, P) containing image data.
    template : np.ndarray
        CHO template (channel weights or matched filter), shape (num_channels,) or (P,).
    channels : np.ndarray
        Channel matrix, shape (num_channels, P). Transforms images into channel space.

    Returns
    -------
    decision_values : np.ndarray
        Array of length N containing CHO decision values for each image.
    """
    # Flatten image stack if 2D
    if images.ndim == 3:
        N, H, W = images.shape
        images = images.reshape(N, H * W)

    # Project images into channel space
    channel_outputs = images @ channels.T  # shape (N, num_channels)

    # Compute decision statistic for each image
    decision_values = safe_sparse_dot(channel_outputs, template)

    return np.array(decision_values)


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
