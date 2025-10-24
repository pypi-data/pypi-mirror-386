import numpy as np
from typing import Any, List

"""
dfa.py
------

Detrended Fluctuation Analysis (DFA-1) implementation for estimating
the Hurst exponent (H) from a time series of stock prices or simulated data.
"""

class DFA:
    """
    Detrended Fluctuation Analysis (DFA-1) implementation for estimating
    the Hurst exponent (H) from a time series of stock prices.

    The algorithm performs the following steps:
    1. Converts the price series to log-prices and builds the cumulative profile.
    2. Divides the series into windows (scales) of increasing sizes.
    3. Detrends each segment by removing a linear fit (local trend).
    4. Computes the root-mean-square fluctuation F(s) for each scale s.
    5. Estimates H from the slope of log(F(s)) vs. log(s).
    """

    def __init__(self, S_t: np.ndarray, min_window: int=4, num_scales=20):
        """
        Initialize the DFA class.

        Parameters
        ----------
        S_t : np.ndarray
            1D array of stock prices (e.g., closing prices).
        min_window : int, default=4
            Minimum window size (s_min) used for computing F(s).
        num_scales : int, default=20
            Number of scales (log-spaced window sizes) between s_min and s_max.
        """
        self.S_t: np.ndarray = S_t
        self.min_window: int = min_window
        self.num_scales: int = num_scales

    @property
    def S_t(self) -> np.ndarray:
        """Return the validated price series."""
        return self._S_t

    @property
    def min_window(self) -> int:
        """Return the minimum window size used for DFA."""
        return self._min_window

    @property
    def num_scales(self) -> int:
        """Return the number of log-spaced scales used for DFA."""
        return self._num_scales

    @S_t.setter
    def S_t(self, value:Any):
        """
        Validate and assign the stock price series.

        Parameters
        ----------
        value : array-like
            Input price series. Must be 1D, finite, and sufficiently long.
        """
        value: np.ndarray = np.asarray(value[np.isfinite(value)], dtype=np.float64)
        if value.ndim != 1:
            raise ValueError("S_t must be a 1D array.")
        if len(value) < 200:
            raise ValueError("S_t must contain at least ~200 samples for a stable DFA estimate.")
        self._S_t = value

    @min_window.setter
    def min_window(self, value):
        """Validate and assign the minimum window size."""
        if not isinstance(value, int):
            raise ValueError("min_window must be an integer (int class).")
        self._min_window = value

    @num_scales.setter
    def num_scales(self, value):
        """Validate and assign the number of scales."""
        if not isinstance(value, int):
            raise ValueError("min_window must be an integer (int class).")
        self._num_scales = value

    @staticmethod
    def linear_regression_fit(A: np.ndarray, y: np.ndarray) -> List:
        """
        Solve a linear least-squares regression Aβ ≈ y.

        Parameters
        ----------
        A : np.ndarray
            Design matrix (e.g., [t, 1] for linear fit).
        y : np.ndarray
            Dependent variable (data segment).

        Returns
        -------
        list
            [coefficients, estimated solution]
        """
        coef, *_ = np.linalg.lstsq(A, y, rcond=None)
        return  coef, A @ coef

    def calculate_fluctuations(self, Y_t: np.ndarray, window: int) -> float:
        """
        Compute the root-mean-square fluctuation F(s) for a given window size s.

        Parameters
        ----------
        Y_t : np.ndarray
            Integrated (profile) signal obtained from log-prices.
        window : int
            Current window size (scale).

        Returns
        -------
        float
            The mean fluctuation F(s) for this scale.
        """
        m: int = len(Y_t) // window
        if m < 2:
            return None

        segments: np.ndarray = Y_t[:m * window].reshape(m, window)
        F_values: List[float] = []

        for segment in segments:

            t: np.ndarray = np.arange(window)
            A: np.ndarray = np.vstack([t, np.ones_like(t)]).T
            _, fit= self.linear_regression_fit(A=A, y=segment)
            resid = segment - fit
            F_values.append(np.sqrt(np.mean(resid**2)))

        return np.sqrt(np.mean(np.asarray(F_values)**2))

    def compute_hurst_H(self) -> float:
        """
        Estimate the Hurst exponent H using DFA.

        Steps
        -----
        1. Convert prices to log-prices and build cumulative profile.
        2. Compute F(s) for multiple scales.
        3. Fit log(F(s)) vs. log(s) with a linear regression.
        4. Return H = slope - 1 (for fBm case).

        Returns
        -------
        float
            Estimated Hurst exponent H.
        """
        log_S_t: np.ndarray = np.log(self.S_t)
        Y_t = np.cumsum(log_S_t - np.mean(log_S_t))

        windows: np.ndarray = np.logspace(np.log10(self.min_window),
                                          np.log10(self.S_t.shape[0] // self.min_window),
                                          self.num_scales).astype(np.int32)

        F_s: List[float] = []

        for window in windows:
            F_s.append(self.calculate_fluctuations(Y_t=Y_t, window=window))

        A: np.ndarray = np.vstack([np.log(windows), np.ones_like(windows)]).T
        return self.linear_regression_fit(A=A, y=np.asarray(np.log(F_s)))[0][0] - 1
