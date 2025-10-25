"""
Utils module for opensection

This module provides utility functions for:
- Unit conversions
- Mathematical helpers
- Physical constants
- Numerical tools
"""

from opensection.utils.constants import (
    CodeConstants,
    GeometricConstants,
    MaterialConstants,
    NumericalConstants,
)
from opensection.utils.math_helpers import (
    angle_between_vectors,
    check_positive_definite,
    clamp,
    interpolate_linear,
    is_converged,
    normalize_vector,
    rotation_matrix_2d,
    safe_divide,
    sign_with_zero,
    smooth_max,
    smooth_min,
)
from opensection.utils.units import Area, Force, Length, Moment, Stress, UnitConverter

__all__ = [
    "UnitConverter",
    "Force",
    "Length",
    "Stress",
    "Area",
    "Moment",
    "MaterialConstants",
    "NumericalConstants",
    "GeometricConstants",
    "CodeConstants",
    "safe_divide",
    "normalize_vector",
    "is_converged",
    "clamp",
    "interpolate_linear",
    "angle_between_vectors",
    "sign_with_zero",
    "smooth_min",
    "smooth_max",
    "rotation_matrix_2d",
    "check_positive_definite",
]
