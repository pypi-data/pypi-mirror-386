"""
Tests for validation module
"""

import warnings

import pytest

from opensection.geometry.section import CircularSection, RectangularSection
from opensection.materials.concrete import ConcreteEC2
from opensection.materials.steel import SteelEC2
from opensection.reinforcement.rebar import RebarGroup
from opensection.validation import (
    GeometryValidationError,
    GeometryValidator,
    LoadValidationError,
    LoadValidator,
    MaterialValidationError,
    MaterialValidator,
    RebarValidationError,
    RebarValidator,
    SectionValidator,
)


class TestGeometryValidator:
    """Tests for GeometryValidator"""

    def test_validate_positive_ok(self):
        """Test validation of positive value"""
        GeometryValidator.validate_positive(1.0, "test")  # Should not raise

    def test_validate_positive_fail(self):
        """Test validation fails for negative value"""
        with pytest.raises(GeometryValidationError):
            GeometryValidator.validate_positive(-1.0, "test")

    def test_validate_positive_zero(self):
        """Test validation fails for zero"""
        with pytest.raises(GeometryValidationError):
            GeometryValidator.validate_positive(0.0, "test")

    def test_validate_dimension_ok(self):
        """Test validation of normal dimension"""
        GeometryValidator.validate_dimension(0.5, "largeur")  # Should not raise

    def test_validate_dimension_too_small(self):
        """Test validation fails for too small dimension"""
        with pytest.raises(GeometryValidationError):
            GeometryValidator.validate_dimension(0.005, "largeur")  # 0.5 cm

    def test_validate_dimension_too_large(self):
        """Test validation fails for too large dimension"""
        with pytest.raises(GeometryValidationError):
            GeometryValidator.validate_dimension(15.0, "hauteur")  # 15 m

    def test_validate_rectangular_section_ok(self):
        """Test validation of normal rectangular section"""
        GeometryValidator.validate_rectangular_section(0.3, 0.5)  # Should not raise

    def test_validate_rectangular_section_high_ratio(self):
        """Test warning for high aspect ratio"""
        with pytest.warns(UserWarning):
            GeometryValidator.validate_rectangular_section(0.1, 1.5)  # ratio = 15

    def test_validate_point_in_rectangle_inside(self):
        """Test point is inside rectangle"""
        assert GeometryValidator.validate_point_in_rectangle(0.1, 0.05, 0.3, 0.5)

    def test_validate_point_in_rectangle_outside(self):
        """Test point is outside rectangle"""
        assert not GeometryValidator.validate_point_in_rectangle(0.3, 0.0, 0.3, 0.5)

    def test_validate_point_in_circle_inside(self):
        """Test point is inside circle"""
        assert GeometryValidator.validate_point_in_circle(0.1, 0.1, 0.5)

    def test_validate_point_in_circle_outside(self):
        """Test point is outside circle"""
        assert not GeometryValidator.validate_point_in_circle(0.3, 0.3, 0.5)


class TestMaterialValidator:
    """Tests for MaterialValidator"""

    def test_validate_concrete_strength_ok(self):
        """Test validation of normal concrete strength"""
        MaterialValidator.validate_concrete_strength(30)  # C30/37

    def test_validate_concrete_strength_too_low(self):
        """Test validation fails for too low strength"""
        with pytest.raises(MaterialValidationError):
            MaterialValidator.validate_concrete_strength(10)  # < C12/15

    def test_validate_concrete_strength_too_high(self):
        """Test validation fails for too high strength"""
        with pytest.raises(MaterialValidationError):
            MaterialValidator.validate_concrete_strength(100)  # > C90/105

    def test_validate_concrete_strength_non_standard(self):
        """Test warning for non-standard strength"""
        with pytest.warns(UserWarning):
            MaterialValidator.validate_concrete_strength(33)  # Not standard

    def test_validate_steel_strength_ok(self):
        """Test validation of normal steel strength"""
        MaterialValidator.validate_steel_strength(500)  # B500

    def test_validate_steel_strength_too_low(self):
        """Test validation fails for too low strength"""
        with pytest.raises(MaterialValidationError):
            MaterialValidator.validate_steel_strength(300)

    def test_validate_steel_strength_non_standard(self):
        """Test warning for non-standard strength"""
        with pytest.warns(UserWarning):
            MaterialValidator.validate_steel_strength(450)  # Not standard

    def test_validate_safety_factor_ok(self):
        """Test validation of normal safety factor"""
        MaterialValidator.validate_safety_factor(1.5, "gamma_c")

    def test_validate_safety_factor_too_low(self):
        """Test validation fails for too low safety factor"""
        with pytest.raises(MaterialValidationError):
            MaterialValidator.validate_safety_factor(0.9, "gamma_c")


class TestRebarValidator:
    """Tests for RebarValidator"""

    def test_validate_diameter_ok(self):
        """Test validation of standard diameter"""
        RebarValidator.validate_diameter(0.016)  # HA16

    def test_validate_diameter_too_small(self):
        """Test validation fails for too small diameter"""
        with pytest.raises(RebarValidationError):
            RebarValidator.validate_diameter(0.004)  # 4 mm

    def test_validate_diameter_too_large(self):
        """Test validation fails for too large diameter"""
        with pytest.raises(RebarValidationError):
            RebarValidator.validate_diameter(0.060)  # 60 mm

    def test_validate_diameter_non_standard(self):
        """Test warning for non-standard diameter"""
        with pytest.warns(UserWarning):
            RebarValidator.validate_diameter(0.018)  # 18 mm

    def test_validate_number_of_bars_ok(self):
        """Test validation of normal number of bars"""
        RebarValidator.validate_number_of_bars(4)

    def test_validate_number_of_bars_zero(self):
        """Test validation fails for zero bars"""
        with pytest.raises(RebarValidationError):
            RebarValidator.validate_number_of_bars(0)

    def test_validate_number_of_bars_high(self):
        """Test warning for high number of bars"""
        with pytest.warns(UserWarning):
            RebarValidator.validate_number_of_bars(150)

    def test_validate_rebar_position_ok(self):
        """Test validation of rebar in correct position"""
        RebarValidator.validate_rebar_position(
            y=0.20, z=0.0, diameter=0.016, section_width=0.3, section_height=0.5, cover=0.03
        )

    def test_validate_rebar_position_outside(self):
        """Test validation fails for rebar outside section"""
        with pytest.raises(RebarValidationError):
            RebarValidator.validate_rebar_position(
                y=0.30, z=0.0, diameter=0.016, section_width=0.3, section_height=0.5
            )

    def test_validate_rebar_position_insufficient_cover(self):
        """Test warning for insufficient cover"""
        with pytest.warns(UserWarning):
            RebarValidator.validate_rebar_position(
                y=0.23, z=0.0, diameter=0.020, section_width=0.3, section_height=0.5, cover=0.03
            )

    def test_validate_minimum_reinforcement_ok(self):
        """Test validation of minimum reinforcement"""
        RebarValidator.validate_minimum_reinforcement(As=0.0006, Ac=0.15)  # 0.4%

    def test_validate_minimum_reinforcement_low(self):
        """Test warning for low reinforcement ratio"""
        with pytest.warns(UserWarning):
            RebarValidator.validate_minimum_reinforcement(As=0.0001, Ac=0.15)  # 0.067%

    def test_validate_minimum_reinforcement_zero(self):
        """Test validation fails for no reinforcement"""
        with pytest.raises(RebarValidationError):
            RebarValidator.validate_minimum_reinforcement(As=0.0, Ac=0.15)

    def test_validate_maximum_reinforcement_ok(self):
        """Test validation of normal reinforcement"""
        RebarValidator.validate_maximum_reinforcement(As=0.003, Ac=0.15)  # 2%

    def test_validate_maximum_reinforcement_too_high(self):
        """Test validation fails for too high reinforcement"""
        with pytest.raises(RebarValidationError):
            RebarValidator.validate_maximum_reinforcement(As=0.015, Ac=0.15)  # 10%

    def test_validate_maximum_reinforcement_high(self):
        """Test warning for high reinforcement"""
        with pytest.warns(UserWarning):
            RebarValidator.validate_maximum_reinforcement(As=0.007, Ac=0.15)  # 4.7%


class TestLoadValidator:
    """Tests for LoadValidator"""

    def test_validate_axial_load_ok(self):
        """Test validation of reasonable axial load"""
        LoadValidator.validate_axial_load(N=500, section_area=0.15, concrete_strength=17)

    def test_validate_axial_load_too_high(self):
        """Test validation fails for unrealistic load"""
        with pytest.raises(LoadValidationError):
            LoadValidator.validate_axial_load(N=50000, section_area=0.15, concrete_strength=17)

    def test_validate_moment_ok(self):
        """Test validation of reasonable moment"""
        LoadValidator.validate_moment(
            M=100, section_height=0.5, section_area=0.15, concrete_strength=17
        )

    def test_validate_moment_too_high(self):
        """Test validation fails for unrealistic moment"""
        with pytest.raises(LoadValidationError):
            LoadValidator.validate_moment(
                M=10000, section_height=0.5, section_area=0.15, concrete_strength=17
            )

    def test_validate_unit_consistency_ok(self):
        """Test validation of consistent units"""
        LoadValidator.validate_unit_consistency(N=500, M=100)

    def test_validate_unit_consistency_warning(self):
        """Test warning for inconsistent units"""
        with pytest.warns(UserWarning):
            LoadValidator.validate_unit_consistency(N=500000, M=1)


class TestSectionValidator:
    """Tests for complete section validation"""

    def test_validate_all_ok(self):
        """Test validation of complete valid section"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)
        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.016, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.016, n=3)

        SectionValidator.validate_all(section, concrete, steel, rebars, N=500, M_y=0, M_z=100)

    def test_validate_all_rebar_outside(self):
        """Test validation fails for rebar outside section"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)
        rebars = RebarGroup()
        rebars.add_rebar(y=0.30, z=0.0, diameter=0.016, n=3)  # Outside!

        with pytest.raises(RebarValidationError):
            SectionValidator.validate_all(section, concrete, steel, rebars)

    def test_validate_all_weak_concrete(self):
        """Test validation fails for too weak concrete"""
        section = RectangularSection(width=0.3, height=0.5)
        steel = SteelEC2(fyk=500)
        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.016, n=3)

        with pytest.raises(MaterialValidationError):
            concrete = ConcreteEC2(fck=10)  # Too weak
            SectionValidator.validate_all(section, concrete, steel, rebars)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
