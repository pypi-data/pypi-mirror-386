"""
Gestion des armatures
"""

from dataclasses import dataclass
from typing import List, Tuple

import numpy as np

try:
    from opensection.reinforcement.helpers import CoverHelper
except ImportError:
    # Si helpers n'est pas encore chargé, on l'importera plus tard
    CoverHelper = None


@dataclass
class Rebar:
    """
    Représente une armature ou un groupe d'armatures identiques

    Attributes:
        y: Coordonnée y (m)
        z: Coordonnée z (m)
        diameter: Diamètre (m)
        n: Nombre de barres
        area: Aire totale (m²)
    """

    y: float
    z: float
    diameter: float
    n: int = 1

    @property
    def area(self) -> float:
        """Aire totale des barres"""
        return self.n * np.pi * (self.diameter / 2) ** 2

    @property
    def position(self) -> Tuple[float, float]:
        """Position (y, z)"""
        return (self.y, self.z)


class RebarGroup:
    """Groupe d'armatures"""

    def __init__(self):
        self.rebars: List[Rebar] = []

    def add_rebar(self, y: float, z: float, diameter: float, n: int = 1):
        """Ajoute une armature à une position donnée"""
        self.rebars.append(Rebar(y, z, diameter, n))

    def add_rebar_with_cover(
        self,
        position: str,
        diameter: float,
        n: int = 1,
        cover: float = 0.03,
        section_width: float = None,
        section_height: float = None,
    ):
        """
        Ajoute une armature avec gestion automatique de l'enrobage

        Args:
            position: "top", "bottom", "left", "right", "top-left", etc.
            diameter: Diamètre de l'armature (m)
            n: Nombre de barres
            cover: Enrobage béton (m), défaut 3 cm
            section_width: Largeur de la section (m)
            section_height: Hauteur de la section (m)

        Examples:
            >>> rebars = RebarGroup()
            >>> # Section rectangulaire 30x50 cm
            >>> rebars.add_rebar_with_cover(
            ...     "top", diameter=0.016, n=3,
            ...     cover=0.03, section_width=0.3, section_height=0.5
            ... )
            >>> # Position calculée automatiquement avec enrobage
        """
        if section_width is None or section_height is None:
            raise ValueError("section_width et section_height requis pour add_rebar_with_cover()")

        y, z = CoverHelper.rectangular_position_with_cover(
            position, section_width, section_height, diameter, cover
        )

        self.add_rebar(y, z, diameter, n)

    def add_layer_with_cover(
        self,
        position: str,
        n_bars: int,
        diameter: float,
        section_width: float,
        section_height: float,
        cover: float = 0.03,
        spacing: float = None,
    ):
        """
        Ajoute une nappe d'armatures avec enrobage automatique

        Args:
            position: "top" ou "bottom"
            n_bars: Nombre de barres dans la nappe
            diameter: Diamètre (m)
            section_width: Largeur section (m)
            section_height: Hauteur section (m)
            cover: Enrobage (m)
            spacing: Espacement entre barres (si None, auto-calculé)

        Examples:
            >>> rebars = RebarGroup()
            >>> rebars.add_layer_with_cover(
            ...     "top", n_bars=3, diameter=0.016,
            ...     section_width=0.3, section_height=0.5, cover=0.03
            ... )
        """
        positions = CoverHelper.layer_positions_with_cover(
            position, section_width, section_height, n_bars, diameter, cover, spacing
        )

        for y, z in positions:
            self.add_rebar(y, z, diameter, 1)

    def add_circular_array_with_cover(
        self,
        n_bars: int,
        diameter_rebar: float,
        diameter_section: float,
        cover: float = 0.03,
        start_angle: float = 0.0,
    ):
        """
        Ajoute un ferraillage circulaire avec enrobage automatique

        Args:
            n_bars: Nombre de barres
            diameter_rebar: Diamètre des armatures (m)
            diameter_section: Diamètre de la section circulaire (m)
            cover: Enrobage (m)
            start_angle: Angle de départ en degrés (0° = droite)

        Examples:
            >>> rebars = RebarGroup()
            >>> # Poteau circulaire D=50cm avec 8HA16
            >>> rebars.add_circular_array_with_cover(
            ...     n_bars=8, diameter_rebar=0.016,
            ...     diameter_section=0.5, cover=0.03
            ... )
        """
        positions = CoverHelper.circular_array_with_cover(
            n_bars, diameter_section, diameter_rebar, cover, start_angle
        )

        for y, z in positions:
            self.add_rebar(y, z, diameter_rebar, 1)

    def add_linear_array(self, y1: float, z1: float, y2: float, z2: float, n: int, diameter: float):
        """
        Ajoute une nappe linéaire d'armatures

        Args:
            y1, z1: Position première barre
            y2, z2: Position dernière barre
            n: Nombre de barres
            diameter: Diamètre
        """
        for i in range(n):
            t = i / (n - 1) if n > 1 else 0
            y = y1 + t * (y2 - y1)
            z = z1 + t * (z2 - z1)
            self.add_rebar(y, z, diameter, 1)

    def add_circular_array(
        self,
        center_y: float,
        center_z: float,
        radius: float,
        n: int,
        diameter: float,
        start_angle: float = 0,
    ):
        """
        Ajoute une nappe circulaire d'armatures

        Args:
            center_y, center_z: Centre
            radius: Rayon
            n: Nombre de barres
            diameter: Diamètre
            start_angle: Angle de départ (radians)
        """
        for i in range(n):
            theta = start_angle + 2 * np.pi * i / n
            y = center_y + radius * np.cos(theta)
            z = center_z + radius * np.sin(theta)
            self.add_rebar(y, z, diameter, 1)

    @property
    def total_area(self) -> float:
        """Aire totale d'armatures"""
        return sum(r.area for r in self.rebars)

    @property
    def n_rebars(self) -> int:
        """Nombre total de barres"""
        return sum(r.n for r in self.rebars)

    def to_array(self) -> np.ndarray:
        """Convertit en array numpy (n_rebars, 3) -> [y, z, area]"""
        data = []
        for rebar in self.rebars:
            for _ in range(rebar.n):
                data.append([rebar.y, rebar.z, rebar.area / rebar.n])
        return np.array(data)
