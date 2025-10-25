"""
Tests for cover helper functions
"""

import numpy as np
import pytest

from opensection.reinforcement.helpers import CoverHelper


class TestCoverHelper:
    """Tests for automatic cover calculation"""

    def test_rectangular_position_top(self):
        """Test top position with cover"""
        y, z = CoverHelper.rectangular_position_with_cover(
            "top", width=0.3, height=0.5, diameter=0.016, cover=0.03
        )

        # Top position: y = height/2 - cover - diameter/2
        expected_y = 0.5 / 2 - 0.03 - 0.016 / 2
        assert np.isclose(y, expected_y)
        assert np.isclose(z, 0.0)

    def test_rectangular_position_bottom(self):
        """Test bottom position with cover"""
        y, z = CoverHelper.rectangular_position_with_cover(
            "bottom", width=0.3, height=0.5, diameter=0.016, cover=0.03
        )

        expected_y = -(0.5 / 2 - 0.03 - 0.016 / 2)
        assert np.isclose(y, expected_y)
        assert np.isclose(z, 0.0)

    def test_rectangular_position_left(self):
        """Test left position with cover"""
        y, z = CoverHelper.rectangular_position_with_cover(
            "left", width=0.3, height=0.5, diameter=0.016, cover=0.03
        )

        expected_z = -(0.3 / 2 - 0.03 - 0.016 / 2)
        assert np.isclose(y, 0.0)
        assert np.isclose(z, expected_z)

    def test_rectangular_position_top_left(self):
        """Test corner position"""
        y, z = CoverHelper.rectangular_position_with_cover(
            "top-left", width=0.3, height=0.5, diameter=0.016, cover=0.03
        )

        expected_y = 0.5 / 2 - 0.03 - 0.016 / 2
        expected_z = -(0.3 / 2 - 0.03 - 0.016 / 2)
        assert np.isclose(y, expected_y)
        assert np.isclose(z, expected_z)

    def test_circular_position_top(self):
        """Test circular position at top (90°)"""
        y, z = CoverHelper.circular_position_with_cover(
            angle_degrees=90, diameter_section=0.5, diameter_rebar=0.016, cover=0.03
        )

        # Radius to rebar center
        radius = 0.5 / 2 - 0.03 - 0.016 / 2

        # At 90°: z=0, y=radius
        assert np.isclose(y, radius, rtol=1e-10)
        assert np.isclose(z, 0.0, atol=1e-10)

    def test_circular_position_right(self):
        """Test circular position at right (0°)"""
        y, z = CoverHelper.circular_position_with_cover(
            angle_degrees=0, diameter_section=0.5, diameter_rebar=0.016, cover=0.03
        )

        radius = 0.5 / 2 - 0.03 - 0.016 / 2

        # At 0°: y=0, z=radius
        assert np.isclose(y, 0.0, atol=1e-10)
        assert np.isclose(z, radius, rtol=1e-10)

    def test_circular_array(self):
        """Test circular array generation"""
        positions = CoverHelper.circular_array_with_cover(
            n_bars=8, diameter_section=0.5, diameter_rebar=0.016, cover=0.03
        )

        # Should have 8 positions
        assert len(positions) == 8

        # All positions should be at same radius
        radius_expected = 0.5 / 2 - 0.03 - 0.016 / 2
        for y, z in positions:
            radius_actual = np.sqrt(y**2 + z**2)
            assert np.isclose(radius_actual, radius_expected)

        # First position at 0° (right)
        y0, z0 = positions[0]
        assert np.isclose(y0, 0.0, atol=1e-10)
        assert np.isclose(z0, radius_expected, rtol=1e-10)

    def test_layer_positions_single(self):
        """Test layer with single bar"""
        positions = CoverHelper.layer_positions_with_cover(
            "top", width=0.3, height=0.5, n_bars=1, diameter=0.016, cover=0.03
        )

        assert len(positions) == 1
        y, z = positions[0]

        expected_y = 0.5 / 2 - 0.03 - 0.016 / 2
        assert np.isclose(y, expected_y)
        assert np.isclose(z, 0.0)

    def test_layer_positions_two_bars(self):
        """Test layer with two bars"""
        positions = CoverHelper.layer_positions_with_cover(
            "bottom", width=0.3, height=0.5, n_bars=2, diameter=0.016, cover=0.03
        )

        assert len(positions) == 2

        # Should be at edges
        y1, z1 = positions[0]
        y2, z2 = positions[1]

        expected_y = -(0.5 / 2 - 0.03 - 0.016 / 2)
        expected_z_left = -(0.3 / 2 - 0.03 - 0.016 / 2)
        expected_z_right = 0.3 / 2 - 0.03 - 0.016 / 2

        assert np.isclose(y1, expected_y)
        assert np.isclose(y2, expected_y)
        assert np.isclose(z1, expected_z_left)
        assert np.isclose(z2, expected_z_right)

    def test_layer_positions_three_bars(self):
        """Test layer with three bars"""
        positions = CoverHelper.layer_positions_with_cover(
            "top", width=0.3, height=0.5, n_bars=3, diameter=0.016, cover=0.03
        )

        assert len(positions) == 3

        # All should have same y
        ys = [y for y, z in positions]
        assert all(np.isclose(y, ys[0]) for y in ys)

        # Middle one should be at center
        y_mid, z_mid = positions[1]
        assert np.isclose(z_mid, 0.0)


class TestRebarGroupWithCover:
    """Test RebarGroup methods with automatic cover"""

    def test_add_rebar_with_cover(self):
        """Test adding rebar with automatic cover"""
        from opensection.reinforcement.rebar import RebarGroup

        rebars = RebarGroup()
        rebars.add_rebar_with_cover(
            "top", diameter=0.016, n=3, section_width=0.3, section_height=0.5, cover=0.03
        )

        assert rebars.n_rebars == 3
        assert len(rebars.rebars) == 1

        rebar = rebars.rebars[0]
        expected_y = 0.5 / 2 - 0.03 - 0.016 / 2
        assert np.isclose(rebar.y, expected_y)
        assert np.isclose(rebar.z, 0.0)

    def test_add_layer_with_cover(self):
        """Test adding a layer with automatic cover"""
        from opensection.reinforcement.rebar import RebarGroup

        rebars = RebarGroup()
        rebars.add_layer_with_cover(
            "bottom", n_bars=3, diameter=0.016, section_width=0.3, section_height=0.5, cover=0.03
        )

        assert rebars.n_rebars == 3
        assert len(rebars.rebars) == 3

        # All should have same y (bottom)
        ys = [r.y for r in rebars.rebars]
        expected_y = -(0.5 / 2 - 0.03 - 0.016 / 2)
        assert all(np.isclose(y, expected_y) for y in ys)

    def test_add_circular_array_with_cover(self):
        """Test adding circular array with automatic cover"""
        from opensection.reinforcement.rebar import RebarGroup

        rebars = RebarGroup()
        rebars.add_circular_array_with_cover(
            n_bars=8, diameter_rebar=0.016, diameter_section=0.5, cover=0.04
        )

        assert rebars.n_rebars == 8
        assert len(rebars.rebars) == 8

        # All should be at same radius
        radius_expected = 0.5 / 2 - 0.04 - 0.016 / 2
        for rebar in rebars.rebars:
            radius_actual = np.sqrt(rebar.y**2 + rebar.z**2)
            assert np.isclose(radius_actual, radius_expected)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
