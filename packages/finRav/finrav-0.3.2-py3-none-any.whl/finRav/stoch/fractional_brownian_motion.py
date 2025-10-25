import numpy as np
from abc import ABC
from typing import List
from finRav.stoch._fbm_base import fBMBase
from finRav.stoch._hosking_method import Hosking
from finRav.stoch._davies_harte_method import DaviesHarte

"""
fBM.py
------

Wrapper class that provides a unified interface for generating
fractional Brownian motion using different algorithms (Hosking or Davies–Harte).
"""

class fBM(fBMBase, ABC):
    """
    Fractional Brownian Motion simulator (Hosking or Davies–Harte).

    Parameters
    ----------
    N : int
        Number of samples.
    dt : float
        Time increment.
    H : float
        Hurst exponent.
    method : str, default='Hosking'
        Simulation method ('Hosking' or 'DaviesHarte').
    """
    def __init__(self, N: int, dt: float, H: float, method: str='Hosking'):
        super().__init__(N=N, dt=dt, H=H, method=method)

    def simulate(self) -> List[np.ndarray]:
        """
        Generate fractional Brownian motion using the chosen method.

        Returns
        -------
        (t, B) : tuple[np.ndarray, np.ndarray]
            t : time grid (N points)
            B : fBM path simulated using the chosen method.
        """
        t = np.arange(self.N) * self.dt

        if self.method == 'Hosking':
            B = Hosking(N=self.N, dt=self.dt, H=self.H).simulate()

        elif self.method == 'DaviesHarte':
            B = DaviesHarte(N=self.N, dt=self.dt, H=self.H).simulate()

        else:
            B = t
        return t, B


if __name__ == "__main__":

    fbm = fBM(N=10, H=.7, dt=1, method='DaviesHarte')
    fbm.simulate()
