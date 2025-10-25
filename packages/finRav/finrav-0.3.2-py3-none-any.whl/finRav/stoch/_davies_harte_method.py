import numpy as np
from finRav.stoch._fbm_base import fBMBase
from finRav.stoch._fractional_gaussian_noise import fGN

"""
_davies_harte_method.py
----------------------

Implements the Davies–Harte algorithm for simulating fractional Gaussian noise (fGn)
and fractional Brownian motion (fBM) using circulant embedding and FFT.
"""

class DaviesHarte(fBMBase):
    """
   Simulate fractional Brownian motion using the Davies–Harte algorithm.

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
        super().__init__(N=N, dt=dt, H=H, method='DaviesHarte')

    def simulate(self):
        """
        Simulate an fBM path using the Davies–Harte algorithm.

        Steps
        -----
        1. Compute γ(k) for k=0,...,N using fGn class.
        2. Construct circulant vector c = [γ(0..N), γ(N-1..1)].
        3. Compute eigenvalues λ_j = Re(FFT(c)).
        4. Generate complex Gaussian Z_j according to λ_j.
        5. Compute IFFT(Z) → fGn.
        6. Return cumulative sum → fBM.

        Returns
        -------
        np.ndarray
            Simulated fractional Brownian motion path.
        """
        fgn = fGN(N=self.N+1, dt=self.dt, H=self.H)
        fgn.simulate()

        self.gamma: np.ndarray = fgn.gamma

        c = np.concatenate([self.gamma, self.gamma[self.N-1:0:-1]])

        eig_values = np.fft.fft(c).real
        eig_values[eig_values < 0] = 0

        # FFT Length
        M = 2 * self.N

        # Generate standard normals
        Z = np.zeros(M, dtype=np.complex128)

        # Real parts
        Z[0] = np.sqrt(eig_values[0]) * np.random.normal()
        Z[self.N] = np.sqrt(eig_values[self.N]) * np.random.normal()

        # For 1 ≤ k < N
        X = np.random.normal(0, 1, self.N - 1)
        Y = np.random.normal(0, 1, self.N - 1)

        for k in range(1, self.N):
            Z[k] = np.sqrt(eig_values[k] / 2) * (X[k - 1] + 1j * Y[k - 1])
            Z[M - k] = np.conj(Z[k])

        # Inverse FFT to recover fGn
        fGn = np.fft.ifft(Z).real[:self.N] * np.sqrt(M) * (self.dt / self.N) ** self.H

        return np.cumsum(fGn)