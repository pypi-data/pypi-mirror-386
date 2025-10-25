"""
Unit conversion utilities for opensection

Handles conversions between different unit systems commonly used in structural engineering.

Base units used internally:
- Length: m (meters)
- Force: kN (kilonewtons)
- Stress: MPa (megapascals)
- Moment: kN·m (kilonewton-meters)
"""

from typing import Union

import numpy as np

Number = Union[float, np.ndarray]


class Length:
    """Length unit conversions"""

    @staticmethod
    def mm_to_m(value: Number) -> Number:
        """Convert millimeters to meters"""
        return value / 1000.0

    @staticmethod
    def m_to_mm(value: Number) -> Number:
        """Convert meters to millimeters"""
        return value * 1000.0

    @staticmethod
    def cm_to_m(value: Number) -> Number:
        """Convert centimeters to meters"""
        return value / 100.0

    @staticmethod
    def m_to_cm(value: Number) -> Number:
        """Convert meters to centimeters"""
        return value * 100.0


class Force:
    """Force unit conversions"""

    @staticmethod
    def N_to_kN(value: Number) -> Number:
        """Convert newtons to kilonewtons"""
        return value / 1000.0

    @staticmethod
    def kN_to_N(value: Number) -> Number:
        """Convert kilonewtons to newtons"""
        return value * 1000.0

    @staticmethod
    def MN_to_kN(value: Number) -> Number:
        """Convert meganewtons to kilonewtons"""
        return value * 1000.0

    @staticmethod
    def kN_to_MN(value: Number) -> Number:
        """Convert kilonewtons to meganewtons"""
        return value / 1000.0


class Stress:
    """Stress unit conversions"""

    @staticmethod
    def MPa_to_kPa(value: Number) -> Number:
        """Convert megapascals to kilopascals"""
        return value * 1000.0

    @staticmethod
    def kPa_to_MPa(value: Number) -> Number:
        """Convert kilopascals to megapascals"""
        return value / 1000.0

    @staticmethod
    def Pa_to_MPa(value: Number) -> Number:
        """Convert pascals to megapascals"""
        return value / 1e6

    @staticmethod
    def MPa_to_Pa(value: Number) -> Number:
        """Convert megapascals to pascals"""
        return value * 1e6


class Area:
    """Area unit conversions"""

    @staticmethod
    def mm2_to_m2(value: Number) -> Number:
        """Convert square millimeters to square meters"""
        return value / 1e6

    @staticmethod
    def m2_to_mm2(value: Number) -> Number:
        """Convert square meters to square millimeters"""
        return value * 1e6

    @staticmethod
    def cm2_to_m2(value: Number) -> Number:
        """Convert square centimeters to square meters"""
        return value / 1e4

    @staticmethod
    def m2_to_cm2(value: Number) -> Number:
        """Convert square meters to square centimeters"""
        return value * 1e4


class Moment:
    """Moment unit conversions"""

    @staticmethod
    def Nm_to_kNm(value: Number) -> Number:
        """Convert newton-meters to kilonewton-meters"""
        return value / 1000.0

    @staticmethod
    def kNm_to_Nm(value: Number) -> Number:
        """Convert kilonewton-meters to newton-meters"""
        return value * 1000.0

    @staticmethod
    def MNm_to_kNm(value: Number) -> Number:
        """Convert meganewton-meters to kilonewton-meters"""
        return value * 1000.0


class UnitConverter:
    """
    Main unit converter with common structural engineering conversions

    Internal units (SI):
    - Length: m
    - Force: kN
    - Stress: MPa (= N/mm² = kN/m²*1000)
    - Moment: kN·m

    Key conversion for stress calculations:
    MPa * m² = (N/mm²) * m² = (N/mm²) * (1000mm)² = N * 1e6 = MN
    Therefore: sigma(MPa) * A(m²) = F(MN) -> multiply by 1000 to get kN
    """

    @staticmethod
    def stress_area_to_force(stress_MPa: Number, area_m2: Number) -> Number:
        """
        Convert stress (MPa) and area (m²) to force (kN)

        sigma(MPa) * A(m²) = (N/mm²) * m² = (N/mm²) * 1e6 mm² = N * 1e6 = MN
        MN * 1000 = kN

        Args:
            stress_MPa: Stress in MPa
            area_m2: Area in m²

        Returns:
            Force in kN
        """
        return stress_MPa * area_m2 * 1000.0

    @staticmethod
    def stress_area_moment_to_moment(stress_MPa: Number, area_m2: Number, arm_m: Number) -> Number:
        """
        Convert stress, area and moment arm to moment (kN·m)

        Args:
            stress_MPa: Stress in MPa
            area_m2: Area in m²
            arm_m: Moment arm in m

        Returns:
            Moment in kN·m
        """
        force_kN = UnitConverter.stress_area_to_force(stress_MPa, area_m2)
        return force_kN * arm_m

    @staticmethod
    def modulus_area_to_stiffness(modulus_MPa: Number, area_m2: Number) -> Number:
        """
        Convert elastic modulus (MPa) and area (m²) to axial stiffness (kN)

        E(MPa) * A(m²) = EA in MN -> multiply by 1000 to get kN

        Args:
            modulus_MPa: Elastic modulus in MPa
            area_m2: Area in m²

        Returns:
            Axial stiffness EA in kN (for use with epsilon)
        """
        return modulus_MPa * area_m2 * 1000.0

    @staticmethod
    def modulus_inertia_to_flexural_stiffness(modulus_MPa: Number, inertia_m4: Number) -> Number:
        """
        Convert elastic modulus (MPa) and moment of inertia (m⁴) to flexural stiffness (kN·m²)

        E(MPa) * I(m⁴) = EI in MN·m² -> multiply by 1000 to get kN·m²

        Args:
            modulus_MPa: Elastic modulus in MPa
            inertia_m4: Moment of inertia in m⁴

        Returns:
            Flexural stiffness EI in kN·m² (for use with curvature)
        """
        return modulus_MPa * inertia_m4 * 1000.0


# Convenience instances
length = Length()
force = Force()
stress = Stress()
area = Area()
moment = Moment()
units = UnitConverter()
