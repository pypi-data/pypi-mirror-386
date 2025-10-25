"""
Tests for utility functions
"""

import numpy as np
import pytest

from opensection.utils import (
    Area,
    Force,
    Length,
    MaterialConstants,
    Moment,
    NumericalConstants,
    Stress,
    UnitConverter,
    clamp,
    is_converged,
    normalize_vector,
    safe_divide,
)


class TestUnitConversions:
    """Test unit conversion functions"""

    def test_length_conversions(self):
        """Test length unit conversions"""
        assert Length.mm_to_m(1000) == 1.0
        assert Length.m_to_mm(1.0) == 1000.0
        assert Length.cm_to_m(100) == 1.0
        assert Length.m_to_cm(1.0) == 100.0

    def test_force_conversions(self):
        """Test force unit conversions"""
        assert Force.N_to_kN(1000) == 1.0
        assert Force.kN_to_N(1.0) == 1000.0
        assert Force.MN_to_kN(1.0) == 1000.0
        assert Force.kN_to_MN(1000.0) == 1.0

    def test_stress_conversions(self):
        """Test stress unit conversions"""
        assert Stress.MPa_to_kPa(1.0) == 1000.0
        assert Stress.kPa_to_MPa(1000.0) == 1.0
        assert Stress.Pa_to_MPa(1e6) == 1.0
        assert Stress.MPa_to_Pa(1.0) == 1e6

    def test_area_conversions(self):
        """Test area unit conversions"""
        assert Area.mm2_to_m2(1e6) == 1.0
        assert Area.m2_to_mm2(1.0) == 1e6
        assert Area.cm2_to_m2(1e4) == 1.0
        assert Area.m2_to_cm2(1.0) == 1e4

    def test_moment_conversions(self):
        """Test moment unit conversions"""
        assert Moment.Nm_to_kNm(1000) == 1.0
        assert Moment.kNm_to_Nm(1.0) == 1000.0
        assert Moment.MNm_to_kNm(1.0) == 1000.0


class TestUnitConverter:
    """Test main unit converter"""

    def test_stress_area_to_force(self):
        """Test stress * area = force conversion"""
        # sigma = 10 MPa, A = 0.01 m² (100 cm²)
        # F = 10 * 0.01 * 1000 = 100 kN
        force = UnitConverter.stress_area_to_force(10.0, 0.01)
        assert force == 100.0

    def test_stress_area_moment_to_moment(self):
        """Test stress * area * arm = moment conversion"""
        # sigma = 10 MPa, A = 0.01 m², arm = 0.5 m
        # F = 100 kN, M = 100 * 0.5 = 50 kN·m
        moment = UnitConverter.stress_area_moment_to_moment(10.0, 0.01, 0.5)
        assert moment == 50.0

    def test_modulus_area_to_stiffness(self):
        """Test E * A = EA conversion"""
        # E = 200000 MPa, A = 0.001 m² (10 cm²)
        # EA = 200000 * 0.001 * 1000 = 200000 kN
        ea = UnitConverter.modulus_area_to_stiffness(200000.0, 0.001)
        assert ea == 200000.0

    def test_modulus_inertia_to_flexural_stiffness(self):
        """Test E * I = EI conversion"""
        # E = 30000 MPa, I = 0.0001 m⁴
        # EI = 30000 * 0.0001 * 1000 = 3000 kN·m²
        ei = UnitConverter.modulus_inertia_to_flexural_stiffness(30000.0, 0.0001)
        assert ei == 3000.0


class TestMathHelpers:
    """Test mathematical helper functions"""

    def test_safe_divide_normal(self):
        """Test safe divide with normal values"""
        assert safe_divide(10, 2) == 5.0
        assert safe_divide(10, 5) == 2.0

    def test_safe_divide_by_zero(self):
        """Test safe divide by zero"""
        assert safe_divide(10, 0) == 0.0
        assert safe_divide(10, 0, default=float("inf")) == float("inf")

    def test_safe_divide_array(self):
        """Test safe divide with arrays"""
        numerator = np.array([10, 20, 30])
        denominator = np.array([2, 0, 5])
        result = safe_divide(numerator, denominator)
        assert np.allclose(result, [5.0, 0.0, 6.0])

    def test_normalize_vector(self):
        """Test vector normalization"""
        v = np.array([3, 4])
        normalized, norm = normalize_vector(v)
        assert norm == 5.0
        assert np.allclose(normalized, [0.6, 0.8])

    def test_normalize_zero_vector(self):
        """Test normalization of zero vector"""
        v = np.array([0, 0])
        normalized, norm = normalize_vector(v)
        assert norm == 0.0
        assert np.allclose(normalized, [0, 0])

    def test_is_converged(self):
        """Test convergence check"""
        assert is_converged(np.array([1e-7, 1e-8]), 1e-6) == True
        assert is_converged(np.array([1e-5, 1e-6]), 1e-6) == False
        assert is_converged(1e-7, 1e-6) == True

    def test_clamp(self):
        """Test value clamping"""
        assert clamp(5, 0, 10) == 5
        assert clamp(-1, 0, 10) == 0
        assert clamp(15, 0, 10) == 10

    def test_clamp_array(self):
        """Test array clamping"""
        values = np.array([-5, 0, 5, 10, 15])
        clamped = clamp(values, 0, 10)
        assert np.allclose(clamped, [0, 0, 5, 10, 10])


class TestConstants:
    """Test constants"""

    def test_material_constants(self):
        """Test material constants are defined"""
        assert MaterialConstants.E_STEEL_DEFAULT == 200000.0
        assert MaterialConstants.GAMMA_C_DEFAULT == 1.5
        assert MaterialConstants.GAMMA_S_DEFAULT == 1.15

    def test_numerical_constants(self):
        """Test numerical constants are defined"""
        assert NumericalConstants.TOL_FORCE_DEFAULT == 1e-6
        assert NumericalConstants.MAX_ITER_DEFAULT == 50
        assert NumericalConstants.ALPHA_INITIAL == 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
