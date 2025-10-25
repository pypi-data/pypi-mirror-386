"""
Classes pour la représentation de contours géométriques
"""

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np


@dataclass
class Point:
    """Représente un point 2D dans le plan (y, z)"""

    y: float
    z: float

    def to_array(self) -> np.ndarray:
        """Convertit en array numpy"""
        return np.array([self.y, self.z])


class Contour:
    """
    Représente un contour fermé défini par une liste de points

    Attributes:
        points: Liste de points définissant le contour
        is_hole: True si le contour représente un trou
    """

    def __init__(self, points: List[Point], is_hole: bool = False):
        """
        Args:
            points: Liste de points (sens trigonométrique pour contour extérieur)
            is_hole: True si c'est un trou (sens horaire)
        """
        self.points = points
        self.is_hole = is_hole

    def to_array(self) -> np.ndarray:
        """Convertit en array numpy (n_points, 2)"""
        return np.array([[p.y, p.z] for p in self.points])

    def area(self) -> float:
        """
        Calcule l'aire du contour par la formule de Shoelace

        Returns:
            Aire du contour (positive)
        """
        coords = self.to_array()
        n = len(coords)
        if n < 3:
            return 0.0

        # Formule de Shoelace
        area = 0.0
        for i in range(n):
            j = (i + 1) % n
            area += coords[i, 0] * coords[j, 1]
            area -= coords[j, 0] * coords[i, 1]

        return abs(area) / 2.0

    def centroid(self) -> Tuple[float, float]:
        """
        Calcule le centroïde du contour

        Returns:
            Tuple (y_c, z_c) du centroïde
        """
        coords = self.to_array()
        n = len(coords)
        if n < 3:
            return (0.0, 0.0)

        area = self.area()
        if area < 1e-12:
            return (0.0, 0.0)

        cy = 0.0
        cz = 0.0

        for i in range(n):
            j = (i + 1) % n
            cross = coords[i, 0] * coords[j, 1] - coords[j, 0] * coords[i, 1]
            cy += (coords[i, 0] + coords[j, 0]) * cross
            cz += (coords[i, 1] + coords[j, 1]) * cross

        factor = 1.0 / (6.0 * area)
        cy *= factor
        cz *= factor

        return (cy, cz)

    def second_moment(self, cy: float, cz: float) -> Tuple[float, float, float]:
        """
        Calcule les moments quadratiques par rapport à un point de référence

        Args:
            cy, cz: Coordonnées du point de référence

        Returns:
            Tuple (I_yy, I_zz, I_yz)
        """
        coords = self.to_array()
        n = len(coords)

        I_yy = 0.0
        I_zz = 0.0
        I_yz = 0.0

        for i in range(n):
            j = (i + 1) % n

            y1, z1 = coords[i] - np.array([cy, cz])
            y2, z2 = coords[j] - np.array([cy, cz])

            cross = y1 * z2 - y2 * z1

            # Moments quadratiques
            I_yy += (z1**2 + z1 * z2 + z2**2) * cross
            I_zz += (y1**2 + y1 * y2 + y2**2) * cross
            I_yz += (y1 * z2 + 2 * y1 * z1 + 2 * y2 * z2 + y2 * z1) * cross

        I_yy /= 12.0
        I_zz /= 12.0
        I_yz /= 24.0

        return (abs(I_yy), abs(I_zz), abs(I_yz))

    def contains_point(self, y: float, z: float) -> bool:
        """
        Teste si un point est à l'intérieur du contour (ray casting algorithm)

        Args:
            y, z: Coordonnées du point à tester

        Returns:
            True si le point est à l'intérieur
        """
        coords = self.to_array()
        n = len(coords)
        inside = False

        p1y, p1z = coords[0]
        for i in range(1, n + 1):
            p2y, p2z = coords[i % n]

            if z > min(p1z, p2z):
                if z <= max(p1z, p2z):
                    if y <= max(p1y, p2y):
                        if p1z != p2z:
                            xinters = (z - p1z) * (p2y - p1y) / (p2z - p1z) + p1y
                        if p1y == p2y or y <= xinters:
                            inside = not inside

            p1y, p1z = p2y, p2z

        return inside

    @classmethod
    def rectangle(
        cls, width: float, height: float, center_y: float = 0.0, center_z: float = 0.0
    ) -> "Contour":
        """
        Crée un contour rectangulaire

        Args:
            width: Largeur (direction y)
            height: Hauteur (direction z)
            center_y: Coordonnée y du centre
            center_z: Coordonnée z du centre

        Returns:
            Contour rectangulaire
        """
        half_w = width / 2.0
        half_h = height / 2.0

        points = [
            Point(center_y - half_w, center_z - half_h),
            Point(center_y + half_w, center_z - half_h),
            Point(center_y + half_w, center_z + half_h),
            Point(center_y - half_w, center_z + half_h),
        ]

        return cls(points)

    @classmethod
    def circle(
        cls, radius: float, n_points: int = 36, center_y: float = 0.0, center_z: float = 0.0
    ) -> "Contour":
        """
        Crée un contour circulaire

        Args:
            radius: Rayon du cercle
            n_points: Nombre de points pour approximer le cercle
            center_y: Coordonnée y du centre
            center_z: Coordonnée z du centre

        Returns:
            Contour circulaire
        """
        points = []
        for i in range(n_points):
            theta = 2 * np.pi * i / n_points
            y = center_y + radius * np.cos(theta)
            z = center_z + radius * np.sin(theta)
            points.append(Point(y, z))

        return cls(points)

    @classmethod
    def polygon(cls, vertices: List[Tuple[float, float]]) -> "Contour":
        """
        Crée un contour polygonal à partir d'une liste de vertices

        Args:
            vertices: Liste de tuples (y, z)

        Returns:
            Contour polygonal
        """
        points = [Point(y, z) for y, z in vertices]
        return cls(points)
