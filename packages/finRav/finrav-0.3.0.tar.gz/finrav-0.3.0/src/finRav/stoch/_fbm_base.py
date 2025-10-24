import numpy as np
from abc import ABC, abstractmethod

"""
_fbm_base.py
-----------

Abstract base class for fractional Brownian motion (fBM) and fractional Gaussian noise (fGn)
simulation methods.

Defines common parameters, validation logic, and interface for simulation classes.
"""


class fBMBase(ABC):
    """
    Abstract base class for fractional Brownian motion and fGn simulation algorithms.

    Parameters
    ----------
    N : int
        Number of samples.
    dt : float
        Time step between observations.
    H : float
        Hurst exponent, must be in range (0, 1).
    method : str
        Name of the simulation method ('Hosking' or 'DaviesHarte').
    """
    def __init__(self, N: int, dt: float, H: float, method: str):

        self.N: int  = N
        self.dt: float = dt
        self.H: float = H
        self.method: str = method
        self.gamma: np.ndarray = np.empty(self.N)

    @property
    def N(self) -> int:
        """Number of samples."""
        return self._N

    @property
    def H(self) -> float:
        """Hurst exponent."""
        return self._H

    @property
    def dt(self) -> int:
        """Time increment between samples."""
        return self._dt

    @property
    def method(self) -> str:
        """Simulation method name."""
        return self._method

    @property
    def gamma(self) -> np.ndarray:
        """Autocovariance sequence of the fGn."""
        return self._gamma

    @N.setter
    def N(self, value: int) -> None:
        """Validate and set N (must be a positive integer)."""
        if not isinstance(value, int):
            value = int(value)
        self._N = value

    @H.setter
    def H(self, value: float) -> None:
        """Validate and set H (must be in range (0,1))."""
        if not (0 <= value <= 1):
            raise ValueError("Hurst exponent must be in range (0, 1)")
        self._H = value

    @dt.setter
    def dt(self, value: float) -> None:
        """Set time step value (no restriction)."""
        self._dt = value

    @method.setter
    def method(self, value: str) -> None:
        """Validate and set simulation method."""
        if value not in ['Hosking', 'DaviesHarte'] or not isinstance(value, str):
            value = 'Hosking'
        self._method = value

    @gamma.setter
    def gamma(self, value: np.ndarray) -> None:
        """Set autocovariance array."""
        self._gamma = value

    @abstractmethod
    def simulate(self):
        """Run the simulation and return the resulting fBM or fGn path."""