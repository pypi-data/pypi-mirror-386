"""
Tests for circular sections with reinforcement
"""

import numpy as np
import pytest

from opensection.geometry.section import CircularSection
from opensection.materials.concrete import ConcreteEC2
from opensection.materials.steel import SteelEC2
from opensection.reinforcement.rebar import RebarGroup
from opensection.solver.section_solver import SectionSolver


class TestCircularSection:
    """Tests for circular section geometry"""

    def test_circular_section_creation(self):
        """Test circular section can be created"""
        section = CircularSection(diameter=0.5)
        assert section.diameter == 0.5
        assert section.radius == 0.25

    def test_circular_section_properties(self):
        """Test circular section properties"""
        diameter = 0.5
        section = CircularSection(diameter=diameter)
        props = section.properties

        # Area
        area_expected = np.pi * (diameter / 2) ** 2
        assert abs(props.area - area_expected) / area_expected < 0.01

        # Inertia (allow larger tolerance due to mesh approximation)
        I_expected = np.pi * diameter**4 / 64
        assert abs(props.I_yy - I_expected) / I_expected < 0.02  # 2% tolerance
        assert abs(props.I_zz - I_expected) / I_expected < 0.02

    def test_circular_section_fibers(self):
        """Test fiber generation for circular section"""
        section = CircularSection(diameter=0.5)
        fibers = section.create_fiber_mesh(target_fiber_area=0.0001)

        # Should have many fibers
        assert len(fibers) > 1000

        # All fibers should be inside circle
        for fiber in fibers:
            y, z, area = fiber
            distance = np.sqrt(y**2 + z**2)
            assert distance <= 0.25  # radius


class TestCircularSectionWithRebars:
    """Tests for circular sections with reinforcement"""

    def test_circular_array_8_bars(self):
        """Test 8 bars in circular pattern"""
        rebars = RebarGroup()
        rebars.add_circular_array_with_cover(
            n_bars=8, diameter_rebar=0.016, diameter_section=0.5, cover=0.03
        )

        assert rebars.n_rebars == 8

        # Check total area
        single_bar_area = np.pi * (0.016 / 2) ** 2
        expected_total = 8 * single_bar_area
        assert np.isclose(rebars.total_area, expected_total)

    def test_circular_array_angles(self):
        """Test bars are at correct angles"""
        rebars = RebarGroup()
        rebars.add_circular_array_with_cover(
            n_bars=4, diameter_rebar=0.016, diameter_section=0.5, cover=0.03  # 4 bars = 90° apart
        )

        # Calculate angles (normalize to 0-360°)
        angles = []
        for rebar in rebars.rebars:
            angle = np.arctan2(rebar.y, rebar.z)
            angle_deg = np.degrees(angle)
            # Normalize to 0-360
            if angle_deg < 0:
                angle_deg += 360
            angles.append(angle_deg)

        # Should be 0°, 90°, 180°, 270° (or close)
        angles_sorted = sorted(angles)
        expected_angles = [0, 90, 180, 270]

        for expected in expected_angles:
            # Find closest angle
            closest = min(
                angles_sorted, key=lambda x: min(abs(x - expected), abs(x - expected - 360))
            )
            diff = min(abs(closest - expected), abs(closest - expected - 360))
            assert diff < 5  # Within 5°


class TestCircularSectionSolver:
    """Tests for solver with circular sections"""

    @pytest.fixture
    def circular_column(self):
        """Create a standard circular column"""
        section = CircularSection(diameter=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)
        rebars = RebarGroup()
        rebars.add_circular_array_with_cover(
            n_bars=8, diameter_rebar=0.016, diameter_section=0.5, cover=0.04
        )
        return section, concrete, steel, rebars

    def test_solver_circular_compression(self, circular_column):
        """Test solver with circular section - pure compression"""
        section, concrete, steel, rebars = circular_column
        solver = SectionSolver(section, concrete, steel, rebars)

        N = 1000  # kN
        result = solver.solve(N=N, My=0, Mz=0, tol=1e-3, max_iter=100)

        print(f"\nCircular compression: N={N} kN")
        print(f"  Converged: {result.converged} in {result.n_iter} iterations")
        print(f"  epsilon_0 = {result.epsilon_0*1000:.3f} ‰")
        print(f"  sigma_c_max = {result.sigma_c_max:.2f} MPa")

        assert result.converged
        assert result.n_iter < 20
        assert np.isclose(result.N, N, rtol=0.01)

    def test_solver_circular_bending(self, circular_column):
        """Test solver with circular section - bending"""
        section, concrete, steel, rebars = circular_column
        solver = SectionSolver(section, concrete, steel, rebars)

        N = 1000  # kN
        M = 150  # kN·m
        result = solver.solve(N=N, My=0, Mz=M, tol=1e-3, max_iter=100)

        print(f"\nCircular bending: N={N} kN, M={M} kN·m")
        print(f"  Converged: {result.converged} in {result.n_iter} iterations")
        print(f"  epsilon_0 = {result.epsilon_0*1000:.3f} ‰")
        print(f"  chi_z = {result.chi_z:.6e}")
        print(f"  sigma_c_max = {result.sigma_c_max:.2f} MPa")
        print(f"  sigma_s_max = {result.sigma_s_max:.2f} MPa")

        assert result.converged
        assert result.n_iter < 20

    def test_solver_circular_pure_bending(self, circular_column):
        """Test solver with circular section - pure bending"""
        section, concrete, steel, rebars = circular_column
        solver = SectionSolver(section, concrete, steel, rebars)

        M = 50  # kN·m
        result = solver.solve(N=0, My=0, Mz=M, tol=1e-3, max_iter=100)

        print(f"\nCircular pure bending: M={M} kN·m")
        print(f"  Converged: {result.converged} in {result.n_iter} iterations")

        assert result.converged
        assert np.isclose(result.N, 0, atol=10)  # N should be near zero


class TestCoverImpact:
    """Test impact of cover on capacity"""

    def test_cover_impact_on_capacity(self):
        """Test that larger cover reduces capacity"""
        section = CircularSection(diameter=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        # With small cover
        rebars_small = RebarGroup()
        rebars_small.add_circular_array_with_cover(
            n_bars=8, diameter_rebar=0.016, diameter_section=0.5, cover=0.03
        )

        # With large cover
        rebars_large = RebarGroup()
        rebars_large.add_circular_array_with_cover(
            n_bars=8, diameter_rebar=0.016, diameter_section=0.5, cover=0.06
        )

        # Calculate effective radius for each
        radius_small = []
        for rebar in rebars_small.rebars:
            radius_small.append(np.sqrt(rebar.y**2 + rebar.z**2))

        radius_large = []
        for rebar in rebars_large.rebars:
            radius_large.append(np.sqrt(rebar.y**2 + rebar.z**2))

        # Small cover should have larger effective radius
        assert np.mean(radius_small) > np.mean(radius_large)

        print(f"\nCover impact:")
        print(f"  Cover 3cm: radius = {np.mean(radius_small)*100:.2f} cm")
        print(f"  Cover 6cm: radius = {np.mean(radius_large)*100:.2f} cm")
        print(f"  Reduction: {(np.mean(radius_small) - np.mean(radius_large))*100:.2f} cm")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
