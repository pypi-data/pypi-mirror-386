"""
Tests unitaires pour le module géométrie
"""

import numpy as np
import pytest

from opensection.geometry import CircularSection, Contour, Point, RectangularSection


def test_point_creation():
    p = Point(1.0, 2.0)
    assert p.y == 1.0
    assert p.z == 2.0


def test_rectangular_contour():
    contour = Contour.rectangle(width=0.3, height=0.5)
    area = contour.area()
    assert abs(area - 0.15) < 1e-6

    cy, cz = contour.centroid()
    assert abs(cy) < 1e-6
    assert abs(cz) < 1e-6


def test_rectangular_section():
    section = RectangularSection(width=0.3, height=0.5)
    props = section.properties

    # Vérifier l'aire
    assert abs(props.area - 0.15) < 1e-6

    # Vérifier les inerties
    I_yy_expected = 0.3 * 0.5**3 / 12
    assert abs(props.I_yy - I_yy_expected) < 1e-9


def test_circular_section():
    diameter = 0.5
    section = CircularSection(diameter=diameter)
    props = section.properties

    # Aire
    area_expected = np.pi * (diameter / 2) ** 2
    assert abs(props.area - area_expected) / area_expected < 0.01

    # Inertie (tolérance 2% car approximation du maillage)
    I_expected = np.pi * diameter**4 / 64
    assert abs(props.I_yy - I_expected) / I_expected < 0.02


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
