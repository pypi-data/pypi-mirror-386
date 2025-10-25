"""
Propriétés géométriques
"""

from typing import Tuple

import numpy as np


class GeometricProperties:
    """Propriétés géométriques d'une section"""

    def __init__(
        self, area: float, centroid: Tuple[float, float], I_yy: float, I_zz: float, I_yz: float
    ):
        self.area = area
        self.centroid = centroid
        self.I_yy = I_yy
        self.I_zz = I_zz
        self.I_yz = I_yz

    @property
    def principal_inertias(self) -> Tuple[float, float, float]:
        """Calcule I1, I2 et a"""
        I_yy, I_zz, I_yz = self.I_yy, self.I_zz, self.I_yz

        if abs(I_yy - I_zz) < 1e-12:
            alpha = 0.0
        else:
            alpha = 0.5 * np.arctan2(2 * I_yz, I_yy - I_zz)

        I_mean = (I_yy + I_zz) / 2
        I_diff = np.sqrt(((I_yy - I_zz) / 2) ** 2 + I_yz**2)

        I_1 = I_mean + I_diff
        I_2 = I_mean - I_diff

        return (I_1, I_2, alpha)
