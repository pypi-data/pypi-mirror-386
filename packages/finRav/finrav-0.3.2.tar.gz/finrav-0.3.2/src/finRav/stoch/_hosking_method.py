import numpy as np
from finRav.stoch._fbm_base import fBMBase
from finRav.stoch._fractional_gaussian_noise import fGN

"""
_hosking_method.py
-----------------

Implements the Hosking algorithm for simulating fractional Gaussian noise (fGn)
and fractional Brownian motion (fBM).
"""

class Hosking(fBMBase):
    """
    Simulate fractional Brownian motion using the Hosking algorithm.

    Parameters
    ----------
    N : int
        Number of samples.
    dt : float
        Time increment.
    H : float
        Hurst exponent.
    """
    def __init__(self, N: int, dt: float, H: float):
        super().__init__(N=N, dt=dt, H=H, method='Hosking')

    def simulate(self):
        """
        Simulate an fBM path using the Hosking algorithm.

        Steps
        -----
        1. Compute fGn autocovariance γ(k).
        2. Sequentially generate fGn values using recursive relations.
        3. Return cumulative sum as fBM.

        Returns
        -------
        np.ndarray
            Simulated fractional Brownian motion path.
        """
        fgn = fGN(N=self.N, dt=self.dt, H=self.H)
        fgn.simulate()

        self.gamma = fgn.gamma

        X = np.empty(self.N, dtype=float)
        phi = np.zeros(self.N, dtype=float)  # holds φ_{k,·} at each step
        phi_temp = np.zeros(self.N, dtype=float)

        # init
        v = float(self.gamma[0])  # v0 = dt^{2H}
        X[0] = np.random.normal(scale=np.sqrt(v))

        for k in range(1, self.N):

            kappa_k = self.gamma[k]
            for j in range(k - 1):
                kappa_k -= phi[j] * self.gamma[k-j-1]
            kappa_k /= v

            for j in range(k - 1):
                # φ_{k,j} = φ_{k-1,j} - κ_k * φ_{k-1,k-j}
                phi_temp[j] = phi[j] - kappa_k * phi[k - j - 2]
            phi_temp[k - 1] = kappa_k  # φ_{k,k} = κ_k
            phi[:k] = phi_temp[:k]

            v = v * (1.0 - kappa_k ** 2)

            prediction = float(np.dot(phi[:k], X[k - 1::-1][:k]))
            X[k] = prediction + np.random.normal(scale=np.sqrt(v))

        return np.cumsum(X)