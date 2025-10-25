"""
Geometry module for opensection

This module provides classes for representing cross-section geometry,
computing geometric properties, and creating fiber meshes for analysis.
"""

from opensection.geometry.contour import Contour, Point
from opensection.geometry.properties import GeometricProperties
from opensection.geometry.section import CircularSection, RectangularSection, Section, TSection

__all__ = [
    "Point",
    "Contour",
    "GeometricProperties",
    "Section",
    "RectangularSection",
    "CircularSection",
    "TSection",
]
