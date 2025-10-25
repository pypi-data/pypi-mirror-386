"""Convenience module for airfoil data generation.

This module provides airfoil data generation utilities.

Example:
    >>> from pydust_utils import airfoil
    >>> af = airfoil.Airfoil.generate('naca0012', 'airfoils/', reynolds=1e6)
"""

from .c81generator import Airfoil

__all__ = ["Airfoil"]
