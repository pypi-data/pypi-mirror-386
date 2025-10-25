"""
Mathematical helper functions for opensection
"""

from typing import Optional, Tuple, Union

import numpy as np

Number = Union[float, np.ndarray]


def safe_divide(
    numerator: Number, denominator: Number, default: float = 0.0, epsilon: float = 1e-12
) -> Number:
    """
    Safe division that handles division by zero

    Args:
        numerator: Numerator value(s)
        denominator: Denominator value(s)
        default: Default value to return if denominator is zero
        epsilon: Threshold for considering denominator as zero

    Returns:
        Result of division or default value

    Examples:
        >>> safe_divide(10, 2)
        5.0
        >>> safe_divide(10, 0)
        0.0
        >>> safe_divide(10, 0, default=float('inf'))
        inf
    """
    if isinstance(denominator, np.ndarray):
        result = np.where(np.abs(denominator) > epsilon, numerator / denominator, default)
        return result
    else:
        if abs(denominator) > epsilon:
            return numerator / denominator
        else:
            return default


def normalize_vector(vector: np.ndarray, epsilon: float = 1e-12) -> Tuple[np.ndarray, float]:
    """
    Normalize a vector and return both the normalized vector and its original norm

    Args:
        vector: Vector to normalize
        epsilon: Threshold for zero norm

    Returns:
        Tuple of (normalized_vector, original_norm)

    Examples:
        >>> v = np.array([3, 4])
        >>> normalized, norm = normalize_vector(v)
        >>> norm
        5.0
        >>> np.allclose(normalized, [0.6, 0.8])
        True
    """
    norm = np.linalg.norm(vector)
    if norm > epsilon:
        return vector / norm, norm
    else:
        return np.zeros_like(vector), 0.0


def is_converged(
    residual: np.ndarray,
    tolerance: float = 1e-6,
    relative: bool = False,
    reference: Optional[np.ndarray] = None,
) -> bool:
    """
    Check if residual is below tolerance

    Args:
        residual: Residual vector or value
        tolerance: Convergence tolerance
        relative: If True, use relative tolerance
        reference: Reference value for relative tolerance

    Returns:
        True if converged, False otherwise

    Examples:
        >>> is_converged(np.array([1e-7, 1e-8]), 1e-6)
        True
        >>> is_converged(np.array([1e-5, 1e-6]), 1e-6)
        False
    """
    norm = np.linalg.norm(residual) if isinstance(residual, np.ndarray) else abs(residual)

    if relative and reference is not None:
        ref_norm = (
            np.linalg.norm(reference) if isinstance(reference, np.ndarray) else abs(reference)
        )
        if ref_norm > 1e-12:
            return norm / ref_norm < tolerance

    return norm < tolerance


def clamp(value: Number, min_val: Number, max_val: Number) -> Number:
    """
    Clamp value between min and max

    Args:
        value: Value to clamp
        min_val: Minimum value
        max_val: Maximum value

    Returns:
        Clamped value

    Examples:
        >>> clamp(5, 0, 10)
        5
        >>> clamp(-1, 0, 10)
        0
        >>> clamp(15, 0, 10)
        10
    """
    if isinstance(value, np.ndarray):
        return np.clip(value, min_val, max_val)
    else:
        return max(min_val, min(value, max_val))


def interpolate_linear(x: Number, x1: float, y1: float, x2: float, y2: float) -> Number:
    """
    Linear interpolation between two points

    Args:
        x: Value to interpolate at
        x1, y1: First point
        x2, y2: Second point

    Returns:
        Interpolated value

    Examples:
        >>> interpolate_linear(0.5, 0, 0, 1, 10)
        5.0
    """
    if abs(x2 - x1) < 1e-12:
        return y1
    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)


def angle_between_vectors(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Calculate angle between two vectors in radians

    Args:
        v1: First vector
        v2: Second vector

    Returns:
        Angle in radians [0, π]

    Examples:
        >>> v1 = np.array([1, 0])
        >>> v2 = np.array([0, 1])
        >>> angle = angle_between_vectors(v1, v2)
        >>> np.isclose(angle, np.pi/2)
        True
    """
    v1_norm, norm1 = normalize_vector(v1)
    v2_norm, norm2 = normalize_vector(v2)

    if norm1 < 1e-12 or norm2 < 1e-12:
        return 0.0

    cos_angle = np.clip(np.dot(v1_norm, v2_norm), -1.0, 1.0)
    return np.arccos(cos_angle)


def sign_with_zero(value: Number, epsilon: float = 1e-12) -> Number:
    """
    Sign function that returns 0 for values close to zero

    Args:
        value: Input value(s)
        epsilon: Threshold for zero

    Returns:
        -1, 0, or 1
    """
    if isinstance(value, np.ndarray):
        result = np.sign(value)
        result[np.abs(value) < epsilon] = 0
        return result
    else:
        if abs(value) < epsilon:
            return 0
        return 1 if value > 0 else -1


def smooth_min(a: Number, b: Number, k: float = 0.1) -> Number:
    """
    Smooth approximation of minimum function
    Useful for making discontinuous functions differentiable

    Args:
        a: First value
        b: Second value
        k: Smoothing parameter (smaller = closer to true min)

    Returns:
        Smooth minimum
    """
    h = np.maximum(k - np.abs(a - b), 0.0) / k
    return np.minimum(a, b) - h * h * k * 0.25


def smooth_max(a: Number, b: Number, k: float = 0.1) -> Number:
    """
    Smooth approximation of maximum function

    Args:
        a: First value
        b: Second value
        k: Smoothing parameter (smaller = closer to true max)

    Returns:
        Smooth maximum
    """
    return -smooth_min(-a, -b, k)


def rotation_matrix_2d(angle: float) -> np.ndarray:
    """
    Create 2D rotation matrix

    Args:
        angle: Rotation angle in radians

    Returns:
        2x2 rotation matrix

    Examples:
        >>> R = rotation_matrix_2d(np.pi/2)
        >>> v = np.array([1, 0])
        >>> rotated = R @ v
        >>> np.allclose(rotated, [0, 1])
        True
    """
    c = np.cos(angle)
    s = np.sin(angle)
    return np.array([[c, -s], [s, c]])


def check_positive_definite(matrix: np.ndarray, epsilon: float = 1e-12) -> bool:
    """
    Check if a matrix is positive definite

    Args:
        matrix: Square matrix to check
        epsilon: Tolerance for eigenvalue positivity

    Returns:
        True if positive definite
    """
    try:
        eigenvalues = np.linalg.eigvals(matrix)
        return np.all(eigenvalues > epsilon)
    except Exception:
        return False
