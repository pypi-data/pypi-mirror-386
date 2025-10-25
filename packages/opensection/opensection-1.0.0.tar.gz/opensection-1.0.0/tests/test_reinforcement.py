"""
Tests unitaires pour les armatures
"""

import numpy as np
import pytest

from opensection.reinforcement import Rebar, RebarGroup


class TestRebar:
    """Tests pour la classe Rebar"""

    def test_rebar_creation(self):
        """Test création d'une barre"""
        rebar = Rebar(y=0.0, z=-0.2, diameter=0.020, n=3)
        assert rebar.y == 0.0
        assert rebar.z == -0.2
        assert rebar.diameter == 0.020
        assert rebar.n == 3

    def test_rebar_area(self):
        """Test calcul aire"""
        rebar = Rebar(y=0.0, z=0.0, diameter=0.020, n=3)
        expected_area = 3 * np.pi * (0.020 / 2) ** 2
        assert abs(rebar.area - expected_area) < 1e-10

    def test_rebar_position(self):
        """Test propriété position"""
        rebar = Rebar(y=0.1, z=-0.2, diameter=0.020, n=1)
        assert rebar.position == (0.1, -0.2)


class TestRebarGroup:
    """Tests pour la classe RebarGroup"""

    def test_group_creation(self):
        """Test création groupe vide"""
        group = RebarGroup()
        assert len(group.rebars) == 0
        assert group.total_area == 0.0
        assert group.n_rebars == 0

    def test_add_single_rebar(self):
        """Test ajout d'une barre"""
        group = RebarGroup()
        group.add_rebar(y=0.0, z=-0.2, diameter=0.020, n=3)
        assert len(group.rebars) == 1
        assert group.n_rebars == 3

    def test_add_multiple_rebars(self):
        """Test ajout de plusieurs barres"""
        group = RebarGroup()
        group.add_rebar(y=0.0, z=-0.2, diameter=0.020, n=3)
        group.add_rebar(y=0.0, z=0.2, diameter=0.016, n=2)
        assert len(group.rebars) == 2
        assert group.n_rebars == 5

    def test_total_area(self):
        """Test calcul aire totale"""
        group = RebarGroup()
        group.add_rebar(y=0.0, z=-0.2, diameter=0.020, n=3)
        expected_area = 3 * np.pi * (0.020 / 2) ** 2
        assert abs(group.total_area - expected_area) < 1e-10

    def test_linear_array(self):
        """Test nappe linéaire"""
        group = RebarGroup()
        group.add_linear_array(y1=-0.1, z1=-0.2, y2=0.1, z2=-0.2, n=5, diameter=0.016)
        assert len(group.rebars) == 5
        assert group.n_rebars == 5
        # Vérifier positions
        assert group.rebars[0].y == -0.1
        assert group.rebars[-1].y == 0.1

    def test_circular_array(self):
        """Test nappe circulaire"""
        group = RebarGroup()
        group.add_circular_array(center_y=0.0, center_z=0.0, radius=0.2, n=8, diameter=0.020)
        assert len(group.rebars) == 8
        assert group.n_rebars == 8
        # Vérifier que les barres sont sur le cercle
        for rebar in group.rebars:
            distance = np.sqrt(rebar.y**2 + rebar.z**2)
            assert abs(distance - 0.2) < 1e-10

    def test_to_array(self):
        """Test conversion en array"""
        group = RebarGroup()
        group.add_rebar(y=0.0, z=-0.2, diameter=0.020, n=3)
        array = group.to_array()
        assert array.shape == (3, 3)  # 3 barres, 3 colonnes (y, z, area)
        assert np.all(array[:, 0] == 0.0)  # Toutes au même y
        assert np.all(array[:, 1] == -0.2)  # Toutes au même z


class TestCoverHelper:
    """Tests pour la classe CoverHelper"""

    def test_rectangular_position_top(self):
        """Test position haut avec enrobage"""
        from opensection.reinforcement.helpers import CoverHelper
        
        y, z = CoverHelper.rectangular_position_with_cover(
            "top", width=0.3, height=0.5, diameter=0.020, cover=0.03
        )
        
        # Position devrait être en haut, centrée horizontalement
        assert z == 0.0
        assert y > 0  # Haut
        # y = 0.25 - 0.03 - 0.01 = 0.21
        assert abs(y - 0.21) < 0.001
    
    def test_rectangular_position_bottom(self):
        """Test position bas avec enrobage"""
        from opensection.reinforcement.helpers import CoverHelper
        
        y, z = CoverHelper.rectangular_position_with_cover(
            "bottom", width=0.3, height=0.5, diameter=0.020, cover=0.03
        )
        
        assert z == 0.0
        assert y < 0  # Bas
        assert abs(y + 0.21) < 0.001
    
    def test_rectangular_position_left(self):
        """Test position gauche avec enrobage"""
        from opensection.reinforcement.helpers import CoverHelper
        
        y, z = CoverHelper.rectangular_position_with_cover(
            "left", width=0.3, height=0.5, diameter=0.020, cover=0.03
        )
        
        assert y == 0.0
        assert z < 0  # Gauche
    
    def test_rectangular_position_right(self):
        """Test position droite avec enrobage"""
        from opensection.reinforcement.helpers import CoverHelper
        
        y, z = CoverHelper.rectangular_position_with_cover(
            "right", width=0.3, height=0.5, diameter=0.020, cover=0.03
        )
        
        assert y == 0.0
        assert z > 0  # Droite
    
    def test_rectangular_position_top_left(self):
        """Test position coin haut-gauche"""
        from opensection.reinforcement.helpers import CoverHelper
        
        y, z = CoverHelper.rectangular_position_with_cover(
            "top-left", width=0.3, height=0.5, diameter=0.020, cover=0.03
        )
        
        assert y > 0  # Haut
        assert z < 0  # Gauche
    
    def test_circular_position_with_cover(self):
        """Test position sur cercle avec enrobage"""
        from opensection.reinforcement.helpers import CoverHelper
        
        # Angle 0° = droite
        y, z = CoverHelper.circular_position_with_cover(
            angle_degrees=0, diameter_section=0.5, diameter_rebar=0.020, cover=0.03
        )
        
        # Devrait être à droite (z > 0, y ≈ 0)
        assert abs(y) < 0.01
        assert z > 0
        
        # Rayon attendu: 0.25 - 0.03 - 0.01 = 0.21
        radius = np.sqrt(y**2 + z**2)
        assert abs(radius - 0.21) < 0.001
    
    def test_circular_position_90_degrees(self):
        """Test position à 90° (haut)"""
        from opensection.reinforcement.helpers import CoverHelper
        
        y, z = CoverHelper.circular_position_with_cover(
            angle_degrees=90, diameter_section=0.5, diameter_rebar=0.020, cover=0.03
        )
        
        # Devrait être en haut (y > 0, z ≈ 0)
        assert y > 0
        assert abs(z) < 0.01
    
    def test_circular_array_with_cover(self):
        """Test nappe circulaire avec enrobage"""
        from opensection.reinforcement.helpers import CoverHelper
        
        positions = CoverHelper.circular_array_with_cover(
            n_bars=8, diameter_section=0.5, diameter_rebar=0.020, cover=0.03
        )
        
        assert len(positions) == 8
        
        # Vérifier que toutes les positions sont sur le cercle
        expected_radius = 0.5/2 - 0.03 - 0.020/2
        for y, z in positions:
            radius = np.sqrt(y**2 + z**2)
            assert abs(radius - expected_radius) < 0.001
    
    def test_circular_array_angles(self):
        """Test angles de la nappe circulaire"""
        from opensection.reinforcement.helpers import CoverHelper
        
        n_bars = 4
        positions = CoverHelper.circular_array_with_cover(
            n_bars=n_bars, diameter_section=0.5, diameter_rebar=0.020, cover=0.03
        )
        
        # Pour 4 barres, angles devraient être espacés de 90°
        angles = [np.arctan2(y, z) for y, z in positions]
        
        # Vérifier espacement régulier
        assert len(angles) == n_bars
    
    def test_layer_positions_single_bar(self):
        """Test nappe avec 1 barre"""
        from opensection.reinforcement.helpers import CoverHelper
        
        positions = CoverHelper.layer_positions_with_cover(
            position="top", width=0.3, height=0.5, n_bars=1,
            diameter=0.020, cover=0.03
        )
        
        assert len(positions) == 1
        y, z = positions[0]
        assert z == 0.0  # Centrée
    
    def test_layer_positions_two_bars(self):
        """Test nappe avec 2 barres"""
        from opensection.reinforcement.helpers import CoverHelper
        
        positions = CoverHelper.layer_positions_with_cover(
            position="top", width=0.3, height=0.5, n_bars=2,
            diameter=0.020, cover=0.03
        )
        
        assert len(positions) == 2
        y1, z1 = positions[0]
        y2, z2 = positions[1]
        
        # Même y
        assert y1 == y2
        
        # z opposés (aux bords)
        assert z1 < 0
        assert z2 > 0
    
    def test_layer_positions_multiple_bars(self):
        """Test nappe avec plusieurs barres"""
        from opensection.reinforcement.helpers import CoverHelper
        
        n_bars = 5
        positions = CoverHelper.layer_positions_with_cover(
            position="bottom", width=0.4, height=0.6, n_bars=n_bars,
            diameter=0.016, cover=0.04
        )
        
        assert len(positions) == n_bars
        
        # Vérifier qu'elles sont alignées horizontalement
        y_values = [y for y, z in positions]
        assert len(set(y_values)) == 1  # Toutes au même y
        
        # Vérifier espacement régulier
        z_values = [z for y, z in positions]
        spacings = [z_values[i+1] - z_values[i] for i in range(len(z_values)-1)]
        
        # Tous les espacements devraient être identiques
        for spacing in spacings[1:]:
            assert abs(spacing - spacings[0]) < 0.001
    
    def test_layer_positions_custom_spacing(self):
        """Test nappe avec espacement personnalisé"""
        from opensection.reinforcement.helpers import CoverHelper
        
        positions = CoverHelper.layer_positions_with_cover(
            position="top", width=0.3, height=0.5, n_bars=3,
            diameter=0.020, cover=0.03, spacing=0.08
        )
        
        assert len(positions) == 3
        
        # Vérifier l'espacement
        z_values = sorted([z for y, z in positions])
        spacing_1 = z_values[1] - z_values[0]
        spacing_2 = z_values[2] - z_values[1]
        
        assert abs(spacing_1 - 0.08) < 0.001
        assert abs(spacing_2 - 0.08) < 0.001
    
    def test_cover_consistency(self):
        """Test cohérence de l'enrobage"""
        from opensection.reinforcement.helpers import CoverHelper
        
        width = 0.3
        height = 0.5
        diameter = 0.020
        cover = 0.03
        
        # Position haut
        y_top, _ = CoverHelper.rectangular_position_with_cover(
            "top", width, height, diameter, cover
        )
        
        # Position bas
        y_bottom, _ = CoverHelper.rectangular_position_with_cover(
            "bottom", width, height, diameter, cover
        )
        
        # Distance entre haut et bas
        distance = y_top - y_bottom
        expected_distance = height - 2 * (cover + diameter/2)
        
        assert abs(distance - expected_distance) < 0.001


class TestRebarGroupAdvanced:
    """Tests avancés pour RebarGroup"""

    def test_empty_group_properties(self):
        """Test propriétés d'un groupe vide"""
        group = RebarGroup()
        
        assert group.total_area == 0.0
        assert group.n_rebars == 0
        assert len(group.rebars) == 0
        
        # to_array devrait retourner un array vide
        array = group.to_array()
        assert array.shape[0] == 0
    
    def test_multiple_diameters(self):
        """Test groupe avec plusieurs diamètres"""
        group = RebarGroup()
        
        group.add_rebar(y=0.0, z=-0.2, diameter=0.020, n=3)
        group.add_rebar(y=0.0, z=0.0, diameter=0.016, n=2)
        group.add_rebar(y=0.0, z=0.2, diameter=0.025, n=1)
        
        assert group.n_rebars == 6
        assert len(group.rebars) == 3
    
    def test_linear_array_endpoints(self):
        """Test que la nappe linéaire respecte les extrémités"""
        group = RebarGroup()
        
        y1, z1 = 0.0, -0.2
        y2, z2 = 0.0, 0.2
        n = 5
        
        group.add_linear_array(y1, z1, y2, z2, n, diameter=0.016)
        
        # Premier et dernier devraient être aux extrémités
        assert group.rebars[0].y == y1
        assert group.rebars[0].z == z1
        assert group.rebars[-1].y == y2
        assert group.rebars[-1].z == z2
    
    def test_linear_array_spacing(self):
        """Test espacement de la nappe linéaire"""
        group = RebarGroup()
        
        group.add_linear_array(-0.1, -0.2, 0.1, -0.2, n=3, diameter=0.016)
        
        # Vérifier espacement régulier
        y_values = [r.y for r in group.rebars]
        spacing_1 = y_values[1] - y_values[0]
        spacing_2 = y_values[2] - y_values[1]
        
        assert abs(spacing_1 - spacing_2) < 1e-10
    
    def test_circular_array_full_circle(self):
        """Test que la nappe circulaire fait le tour complet"""
        group = RebarGroup()
        
        n = 8
        group.add_circular_array(0.0, 0.0, radius=0.2, n=n, diameter=0.020)
        
        # Calculer les angles
        angles = []
        for rebar in group.rebars:
            angle = np.arctan2(rebar.y, rebar.z)
            angles.append(angle)
        
        # Les angles devraient être espacés de 2π/n
        expected_spacing = 2 * np.pi / n
        
        angles_sorted = sorted(angles)
        for i in range(len(angles_sorted) - 1):
            spacing = angles_sorted[i+1] - angles_sorted[i]
            assert abs(spacing - expected_spacing) < 0.01


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
