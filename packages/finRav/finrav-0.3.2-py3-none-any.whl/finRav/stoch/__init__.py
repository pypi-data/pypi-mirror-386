"""
finRav.stoch — Simulation submodule
Contains stochastic process simulators such as FBM.
"""

from .fractional_brownian_motion import fBM

__all__ = ["fBM"]
