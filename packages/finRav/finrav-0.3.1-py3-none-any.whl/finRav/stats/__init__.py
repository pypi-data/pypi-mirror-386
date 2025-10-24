"""
finRav.stats — Statistical analysis submodule
Includes DFA for estimating the Hurst exponent.
"""

from .detrended_fluctuation_analysis import DFA

__all__ = ["DFA"]