"""
Physical and numerical constants for opensection
"""

import numpy as np


class MaterialConstants:
    """Physical constants for materials"""

    # Elastic moduli (MPa)
    E_STEEL_DEFAULT = 200000.0  # MPa (reinforcing steel)
    E_STEEL_STRUCTURAL = 210000.0  # MPa (structural steel)
    E_PRESTRESSING_STEEL = 195000.0  # MPa (prestressing steel)

    # Partial safety factors (Eurocode 2)
    GAMMA_C_DEFAULT = 1.5  # Concrete
    GAMMA_S_DEFAULT = 1.15  # Reinforcing steel
    GAMMA_M0_DEFAULT = 1.0  # Structural steel

    # Alpha coefficients (Eurocode 2)
    ALPHA_CC_DEFAULT = 0.85  # Long-term effects on concrete strength

    # Ultimate strains
    EPSILON_CU2_C50 = 0.0035  # Ultimate strain for concrete ≤ C50/60
    EPSILON_UK_STEEL = 0.05  # Ultimate strain for reinforcing steel (class B)
    EPSILON_UD_STEEL = 0.045  # Design ultimate strain for reinforcing steel

    # Minimum values
    MIN_CONCRETE_STRENGTH = 12.0  # MPa (C12/15)
    MAX_CONCRETE_STRENGTH = 90.0  # MPa (C90/105)


class NumericalConstants:
    """Numerical constants for solvers and algorithms"""

    # Convergence tolerances
    TOL_FORCE_DEFAULT = 1e-6  # kN
    TOL_MOMENT_DEFAULT = 1e-6  # kN·m
    TOL_DISPLACEMENT_DEFAULT = 1e-9  # m
    TOL_ROTATION_DEFAULT = 1e-9  # rad
    # Relative residual tolerance (dimensionless, used when relative=True)
    TOL_RESIDUAL_REL_DEFAULT = 1e-6

    # Iteration limits
    MAX_ITER_DEFAULT = 50
    MAX_ITER_LINE_SEARCH = 10

    # Line search parameters
    ALPHA_INITIAL = 1.0
    ALPHA_REDUCTION = 0.5
    ALPHA_MIN = 1e-4

    # Numerical stability
    EPSILON_ZERO = 1e-12  # Small number for zero checks
    LARGE_NUMBER = 1e10  # Large number for infinity

    # Mesh parameters
    DEFAULT_FIBER_AREA = 0.0001  # m² (1 cm²)
    MIN_FIBERS = 100
    MAX_FIBERS = 10000

    # Strain limits for numerical stability
    MAX_STRAIN_TENSION = 0.1  # 10% (for steel)
    MAX_STRAIN_COMPRESSION = 0.01  # 1% (for concrete)


class GeometricConstants:
    """Geometric constants"""

    PI = np.pi
    TWO_PI = 2 * np.pi
    SQRT_2 = np.sqrt(2)
    SQRT_3 = np.sqrt(3)

    # Default number of points for circular sections
    DEFAULT_CIRCLE_POINTS = 36
    MIN_CIRCLE_POINTS = 8
    MAX_CIRCLE_POINTS = 360


class CodeConstants:
    """Constants from design codes"""

    # Eurocode 2 (EN 1992-1-1)
    class EC2:
        """Eurocode 2 constants"""

        GAMMA_C = 1.5
        GAMMA_S = 1.15
        ALPHA_CC = 0.85

        # Stress-strain parameters for normal concrete (≤ C50/60)
        EPSILON_C2 = 0.002  # 2‰
        EPSILON_CU2 = 0.0035  # 3.5‰
        N_PARABOLA = 2.0

        # SLS limits
        K_SLS_CONCRETE = 0.6  # σc ≤ 0.6 fck
        K_SLS_STEEL = 0.8  # σs ≤ 0.8 fyk

    # ACI 318 (American code) - for future implementation
    class ACI318:
        """ACI 318 constants"""

        PHI_COMPRESSION = 0.65
        PHI_TENSION = 0.90
        EPSILON_CU = 0.003
        BETA_1 = 0.85  # For fc' ≤ 28 MPa

    # GB 50010 (Chinese code) - for future implementation
    class GB50010:
        """GB 50010 constants"""

        GAMMA_C = 1.4
        GAMMA_S = 1.1
        EPSILON_CU = 0.0033
