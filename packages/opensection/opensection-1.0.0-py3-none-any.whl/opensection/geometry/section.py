"""
Classes de sections géométriques
"""

from typing import List

import numpy as np

from opensection.geometry.contour import Contour, Point
from opensection.geometry.properties import GeometricProperties


class Section:
    """Classe de base pour les sections"""

    def __init__(self, contours: List[Contour]):
        self.contours = contours
        self._properties = None

    def compute_properties(self) -> GeometricProperties:
        """Calcule les propriétés géométriques"""
        total_area = 0.0
        moment_y = 0.0
        moment_z = 0.0

        for contour in self.contours:
            sign = -1.0 if contour.is_hole else 1.0
            area = contour.area()
            cy, cz = contour.centroid()

            total_area += sign * area
            moment_y += sign * area * cy
            moment_z += sign * area * cz

        if total_area < 1e-12:
            raise ValueError("Aire totale nulle ou négative")

        centroid_y = moment_y / total_area
        centroid_z = moment_z / total_area

        I_yy_total = 0.0
        I_zz_total = 0.0
        I_yz_total = 0.0

        for contour in self.contours:
            sign = -1.0 if contour.is_hole else 1.0
            area = contour.area()
            cy, cz = contour.centroid()

            I_yy, I_zz, I_yz = contour.second_moment(cy, cz)

            dy = cy - centroid_y
            dz = cz - centroid_z

            I_yy_total += sign * (I_yy + area * dz**2)
            I_zz_total += sign * (I_zz + area * dy**2)
            I_yz_total += sign * (I_yz + area * dy * dz)

        self._properties = GeometricProperties(
            total_area, (centroid_y, centroid_z), I_yy_total, I_zz_total, I_yz_total
        )

        return self._properties

    @property
    def properties(self) -> GeometricProperties:
        if self._properties is None:
            self._properties = self.compute_properties()
        return self._properties

    def create_fiber_mesh(self, target_fiber_area: float = 0.0001) -> np.ndarray:
        """Crée un maillage de fibres"""
        all_points = []
        for contour in self.contours:
            all_points.extend(contour.to_array())
        points = np.array(all_points)

        y_min, z_min = points.min(axis=0)
        y_max, z_max = points.max(axis=0)

        n_y = max(10, int(np.ceil((y_max - y_min) / np.sqrt(target_fiber_area))))
        n_z = max(10, int(np.ceil((z_max - z_min) / np.sqrt(target_fiber_area))))

        y_grid = np.linspace(y_min, y_max, n_y)
        z_grid = np.linspace(z_min, z_max, n_z)

        fibers = []
        dy = (y_max - y_min) / n_y if n_y > 1 else 0.01
        dz = (z_max - z_min) / n_z if n_z > 1 else 0.01
        fiber_area = dy * dz

        for yi in y_grid:
            for zi in z_grid:
                is_inside = False
                for contour in self.contours:
                    in_contour = contour.contains_point(yi, zi)
                    if not contour.is_hole and in_contour:
                        is_inside = True
                    elif contour.is_hole and in_contour:
                        is_inside = False

                if is_inside:
                    fibers.append([yi, zi, fiber_area])

        return np.array(fibers) if fibers else np.zeros((0, 3))


class RectangularSection(Section):
    """Section rectangulaire"""

    def __init__(self, width: float, height: float):
        self.width = width
        self.height = height
        contour = Contour.rectangle(width, height)
        super().__init__([contour])


class CircularSection(Section):
    """Section circulaire"""

    def __init__(self, diameter: float, n_points: int = 36):
        self.diameter = diameter
        self.radius = diameter / 2
        contour = Contour.circle(self.radius, n_points)
        super().__init__([contour])


class TSection(Section):
    """Section en T"""

    def __init__(
        self, flange_width: float, flange_thickness: float, web_width: float, web_height: float
    ):
        self.flange_width = flange_width
        self.flange_thickness = flange_thickness
        self.web_width = web_width
        self.web_height = web_height

        points = [
            Point(-web_width / 2, -web_height),
            Point(web_width / 2, -web_height),
            Point(web_width / 2, 0),
            Point(flange_width / 2, 0),
            Point(flange_width / 2, flange_thickness),
            Point(-flange_width / 2, flange_thickness),
            Point(-flange_width / 2, 0),
            Point(-web_width / 2, 0),
        ]

        contour = Contour(points)
        super().__init__([contour])
