"""
finRav – Advanced quantitative finance & stochastic simulation toolkit.
"""

from . import stoch, stats

__all__ = ["stoch", "stats", "__version__"]

# גרסה מתוך מטא-דאטה של ההתקנה (case-insensitive)
try:
    from importlib.metadata import version, PackageNotFoundError
    try:
        __version__ = version("finRav")
    except PackageNotFoundError:
        __version__ = version("finrav")
except Exception:
    __version__ = "0.0.0"