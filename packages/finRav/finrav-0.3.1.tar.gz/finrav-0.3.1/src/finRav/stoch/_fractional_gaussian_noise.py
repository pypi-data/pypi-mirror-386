import numpy as np
from finRav.stoch._fbm_base import fBMBase

"""
_fractional_gaussian_noise.py
----------------------------

Generates the autocovariance sequence of fractional Gaussian noise (fGn)
for a given Hurst exponent H and time step dt.
"""

class fGN(fBMBase):
    """
    Fractional Gaussian noise (fGn) generator.

    Parameters
    ----------
    N : int
        Number of samples.
    dt : float
        Time increment.
    H : float
        Hurst exponent, in range (0,1).
    """
    def __init__(self, N: int, dt: float, H: float):
        super().__init__(N, dt, H, method='fGN')

    def simulate(self) -> np.ndarray:
        """
        Compute and store the autocovariance sequence γ(k) for fractional Gaussian noise.

        The theoretical definition is:
            γ(k) = 0.5 * (|k-1|^{2H} - 2|k|^{2H} + |k+1|^{2H})
        scaled by dt^{2H}.

        Returns
        -------
        np.ndarray
            Autocovariance sequence γ(k) of length N.
        """
        k: np.ndarray = np.arange(self.N, dtype=np.float64)
        gamma: np.ndarray = .5 * (
                    (np.abs(k - 1) ** (2 * self.H)) - (2 * np.abs(k) ** (2 * self.H)) + (np.abs(k + 1) ** (2 * self.H)))
        gamma[0] = 1
        self.gamma = (self.dt ** (2 * self.H)) * gamma