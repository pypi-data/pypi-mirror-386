# -*- coding: utf-8 -*-
"""
Matrix2MPO Plus - A Python package for Matrix Product Operator (MPO) decomposition.

This package provides tools for converting matrices to MPO format
and various canonical forms for efficient tensor network representations.
"""

from .Matrix2MPO_plus import MPO, power_iteration_svd, compute_svd

__version__ = "1.0.0"
__author__ = "Matrix2MPO Plus Team"
__email__ = "matrix2mpo@example.com"

__all__ = ["MPO", "power_iteration_svd", "compute_svd"]
