"""Convenience module for post-processing.

This module provides all post-processing parsers and data structures in one place.

Example:
    >>> from pydust_utils import postpro
    >>> data = postpro.SectionalData.from_file('sectional_loads.dat')
    >>> print(data.sec.shape)
"""

from .parse_postpro_files import (
    SectionalData,
    ProbesData,
    ChordwiseData,
    IntegralData,
    HingeData,
)

__all__ = [
    "SectionalData",
    "ProbesData",
    "ChordwiseData",
    "IntegralData",
    "HingeData",
]
