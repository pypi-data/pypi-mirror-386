"""
Validators for opensection data integrity
"""

from typing import Optional

import numpy as np

from opensection.validation.exceptions import (
    GeometryValidationError,
    LoadValidationError,
    MaterialValidationError,
    RebarValidationError,
)


class GeometryValidator:
    """Validates geometry parameters"""

    MIN_DIMENSION = 0.01  # 1 cm minimum
    MAX_DIMENSION = 10.0  # 10 m maximum

    @staticmethod
    def validate_positive(value: float, name: str) -> None:
        """
        Validate that a value is positive

        Args:
            value: Value to check
            name: Name of the parameter (for error message)

        Raises:
            GeometryValidationError: If value is not positive
        """
        if not isinstance(value, (int, float)):
            raise GeometryValidationError(
                f"{name} doit être un nombre numérique",
                parameter_name=name,
                parameter_value=value,
                context="Vérification type de donnée",
            )

        if np.isnan(value) or np.isinf(value):
            raise GeometryValidationError(
                f"{name} doit être un nombre valide (pas NaN ou infini)",
                parameter_name=name,
                parameter_value=value,
                context="Vérification valeur numérique",
            )

        if value <= 0:
            raise GeometryValidationError(
                f"{name} doit être positif",
                parameter_name=name,
                parameter_value=value,
                context="Vérification positivité",
            )

    @staticmethod
    def validate_dimension(value: float, name: str) -> None:
        """
        Validate that a dimension is within reasonable bounds

        Args:
            value: Dimension value in meters
            name: Name of the dimension

        Raises:
            GeometryValidationError: If dimension is out of bounds
        """
        if value < GeometryValidator.MIN_DIMENSION:
            raise GeometryValidationError(
                f"{name} trop petit : {value*100:.2f} cm "
                f"(minimum : {GeometryValidator.MIN_DIMENSION*100} cm)"
            )

        if value > GeometryValidator.MAX_DIMENSION:
            raise GeometryValidationError(
                f"{name} trop grand : {value:.2f} m "
                f"(maximum : {GeometryValidator.MAX_DIMENSION} m)"
            )

    @staticmethod
    def validate_rectangular_section(width: float, height: float) -> None:
        """
        Validate rectangular section dimensions

        Args:
            width: Section width in meters
            height: Section height in meters

        Raises:
            GeometryValidationError: If dimensions are invalid
        """
        GeometryValidator.validate_dimension(width, "Largeur")
        GeometryValidator.validate_dimension(height, "Hauteur")

        # Vérifier le ratio hauteur/largeur (avertissement si > 10)
        ratio = max(height, width) / min(height, width)
        if ratio > 10:
            import warnings

            warnings.warn(
                f"Ratio hauteur/largeur très élevé : {ratio:.1f}. " f"Vérifiez les dimensions.",
                UserWarning,
            )

    @staticmethod
    def validate_circular_section(diameter: float) -> None:
        """
        Validate circular section diameter

        Args:
            diameter: Section diameter in meters

        Raises:
            GeometryValidationError: If diameter is invalid
        """
        GeometryValidator.validate_dimension(diameter, "Diamètre")

    @staticmethod
    def validate_point_in_rectangle(
        y: float, z: float, width: float, height: float, margin: float = 0.01
    ) -> bool:
        """
        Check if a point is inside a rectangular section

        Args:
            y: Y coordinate (vertical)
            z: Z coordinate (horizontal)
            width: Section width
            height: Section height
            margin: Safety margin (default 1 cm)

        Returns:
            True if point is inside (with margin)
        """
        half_height = height / 2 - margin
        half_width = width / 2 - margin

        return abs(y) <= half_height and abs(z) <= half_width

    @staticmethod
    def validate_point_in_circle(y: float, z: float, diameter: float, margin: float = 0.01) -> bool:
        """
        Check if a point is inside a circular section

        Args:
            y: Y coordinate
            z: Z coordinate
            diameter: Section diameter
            margin: Safety margin (default 1 cm)

        Returns:
            True if point is inside (with margin)
        """
        radius = diameter / 2 - margin
        distance = np.sqrt(y**2 + z**2)

        return distance <= radius


class MaterialValidator:
    """Validates material properties"""

    # Eurocode 2 limits
    MIN_CONCRETE_STRENGTH = 12.0  # MPa (C12/15)
    MAX_CONCRETE_STRENGTH = 90.0  # MPa (C90/105)
    MIN_STEEL_STRENGTH = 400.0  # MPa
    MAX_STEEL_STRENGTH = 600.0  # MPa

    @staticmethod
    def validate_concrete_strength(fck: float) -> None:
        """
        Validate concrete characteristic strength

        Args:
            fck: Characteristic compressive strength in MPa

        Raises:
            MaterialValidationError: If strength is invalid
        """
        if fck < MaterialValidator.MIN_CONCRETE_STRENGTH:
            raise MaterialValidationError(
                f"Résistance béton trop faible : {fck} MPa "
                f"(minimum EC2 : {MaterialValidator.MIN_CONCRETE_STRENGTH} MPa)"
            )

        if fck > MaterialValidator.MAX_CONCRETE_STRENGTH:
            raise MaterialValidationError(
                f"Résistance béton trop élevée : {fck} MPa "
                f"(maximum EC2 : {MaterialValidator.MAX_CONCRETE_STRENGTH} MPa)"
            )

        # Vérifier les classes de béton standard
        standard_classes = [12, 16, 20, 25, 30, 35, 40, 45, 50, 55, 60, 70, 80, 90]
        if fck not in standard_classes:
            import warnings

            warnings.warn(
                f"fck = {fck} MPa n'est pas une classe EC2 standard. "
                f"Classes standard : C12/15 à C90/105",
                UserWarning,
            )

    @staticmethod
    def validate_steel_strength(fyk: float) -> None:
        """
        Validate steel characteristic strength

        Args:
            fyk: Characteristic yield strength in MPa

        Raises:
            MaterialValidationError: If strength is invalid
        """
        if fyk < MaterialValidator.MIN_STEEL_STRENGTH:
            raise MaterialValidationError(
                f"Limite élastique acier trop faible : {fyk} MPa "
                f"(minimum : {MaterialValidator.MIN_STEEL_STRENGTH} MPa)"
            )

        if fyk > MaterialValidator.MAX_STEEL_STRENGTH:
            raise MaterialValidationError(
                f"Limite élastique acier trop élevée : {fyk} MPa "
                f"(maximum : {MaterialValidator.MAX_STEEL_STRENGTH} MPa)"
            )

        # Vérifier les nuances standard
        standard_grades = [400, 500, 600]
        if fyk not in standard_grades:
            import warnings

            warnings.warn(
                f"fyk = {fyk} MPa n'est pas une nuance EC2 standard. "
                f"Nuances standard : B400, B500, B600",
                UserWarning,
            )

    @staticmethod
    def validate_safety_factor(gamma: float, name: str) -> None:
        """
        Validate partial safety factor

        Args:
            gamma: Safety factor
            name: Name of the factor

        Raises:
            MaterialValidationError: If factor is invalid
        """
        if gamma < 1.0:
            raise MaterialValidationError(
                f"Coefficient de sécurité {name} doit être >= 1.0, reçu : {gamma}"
            )

        if gamma > 2.0:
            import warnings

            warnings.warn(f"Coefficient de sécurité {name} très élevé : {gamma}", UserWarning)

    @staticmethod
    def validate_elastic_modulus(E: float, material: str) -> None:
        """
        Validate elastic modulus

        Args:
            E: Elastic modulus in MPa
            material: Material name

        Raises:
            MaterialValidationError: If modulus is invalid
        """
        if E <= 0:
            raise MaterialValidationError(
                f"Module élastique {material} doit être positif, reçu : {E} MPa"
            )

        # Vérifier plages raisonnables
        if material.lower() == "concrete":
            if E < 20000 or E > 50000:
                import warnings

                warnings.warn(
                    f"Module élastique béton inhabituel : {E} MPa " f"(plage typique : 20-50 GPa)",
                    UserWarning,
                )
        elif material.lower() == "steel":
            if abs(E - 200000) > 50000:
                import warnings

                warnings.warn(
                    f"Module élastique acier inhabituel : {E} MPa " f"(valeur typique : 200 GPa)",
                    UserWarning,
                )


class RebarValidator:
    """Validates reinforcement parameters"""

    MIN_DIAMETER = 0.006  # 6 mm
    MAX_DIAMETER = 0.050  # 50 mm
    STANDARD_DIAMETERS = [
        0.006,
        0.008,
        0.010,
        0.012,
        0.014,
        0.016,
        0.020,
        0.025,
        0.032,
        0.040,
        0.050,
    ]  # in meters

    @staticmethod
    def validate_diameter(diameter: float) -> None:
        """
        Validate rebar diameter

        Args:
            diameter: Rebar diameter in meters

        Raises:
            RebarValidationError: If diameter is invalid
        """
        if diameter < RebarValidator.MIN_DIAMETER:
            raise RebarValidationError(
                f"Diamètre armature trop petit : {diameter*1000:.0f} mm "
                f"(minimum : {RebarValidator.MIN_DIAMETER*1000:.0f} mm)"
            )

        if diameter > RebarValidator.MAX_DIAMETER:
            raise RebarValidationError(
                f"Diamètre armature trop grand : {diameter*1000:.0f} mm "
                f"(maximum : {RebarValidator.MAX_DIAMETER*1000:.0f} mm)"
            )

        # Vérifier si c'est un diamètre standard
        is_standard = any(abs(diameter - d) < 0.0001 for d in RebarValidator.STANDARD_DIAMETERS)
        if not is_standard:
            import warnings

            warnings.warn(
                f"Diamètre {diameter*1000:.0f} mm n'est pas standard. "
                f"Diamètres standards : 6, 8, 10, 12, 14, 16, 20, 25, 32, 40, 50 mm",
                UserWarning,
            )

    @staticmethod
    def validate_number_of_bars(n: int) -> None:
        """
        Validate number of bars

        Args:
            n: Number of bars

        Raises:
            RebarValidationError: If number is invalid
        """
        if n < 1:
            raise RebarValidationError(f"Nombre de barres doit être >= 1, reçu : {n}")

        if n > 100:
            import warnings

            warnings.warn(f"Nombre de barres très élevé : {n}", UserWarning)

    @staticmethod
    def validate_rebar_position(
        y: float,
        z: float,
        diameter: float,
        section_width: float,
        section_height: float,
        cover: float = 0.03,
    ) -> None:
        """
        Validate that rebar is inside section with proper cover

        Args:
            y: Y coordinate (vertical)
            z: Z coordinate (horizontal)
            diameter: Rebar diameter
            section_width: Section width
            section_height: Section height
            cover: Concrete cover (default 3 cm)

        Raises:
            RebarValidationError: If rebar is outside section or cover is insufficient
        """
        # Position du centre de la barre
        half_height = section_height / 2
        half_width = section_width / 2
        radius = diameter / 2

        # Vérifier que la barre est dans la section
        if abs(y) > half_height:
            raise RebarValidationError(
                f"Armature hors section (y = {y*100:.1f} cm, "
                f"hauteur section = {section_height*100:.1f} cm)"
            )

        if abs(z) > half_width:
            raise RebarValidationError(
                f"Armature hors section (z = {z*100:.1f} cm, "
                f"largeur section = {section_width*100:.1f} cm)"
            )

        # Vérifier l'enrobage
        distance_top = half_height - abs(y) - radius
        distance_side = half_width - abs(z) - radius
        min_distance = min(distance_top, distance_side)

        if min_distance < cover:
            import warnings

            warnings.warn(
                f"Enrobage insuffisant : {min_distance*100:.1f} cm "
                f"(minimum recommandé : {cover*100:.1f} cm)",
                UserWarning,
            )

    @staticmethod
    def required_cover_exposure(exposure_class: str, diameter: float) -> float:
        """
        Approximate EC2 c_min for exposure classes (simplified mapping).
        Returns c_nom (c_min + Δc_dev), in meters.
        """
        # Simplified baseline (m) for demonstration; adjust per national annex
        base = {
            "XC1": 0.025,
            "XC2": 0.030,
            "XC3": 0.035,
            "XC4": 0.040,
            "XD1": 0.035,
            "XD2": 0.040,
            "XD3": 0.045,
            "XS1": 0.035,
            "XS2": 0.040,
            "XS3": 0.045,
        }
        c_min = base.get(exposure_class.upper(), 0.030)
        delta_dev = 0.010  # allowance for deviations (10 mm)
        c_nom = c_min + delta_dev
        # Diameter rule: c_nom >= diameter
        return max(c_nom, diameter)

    @staticmethod
    def validate_cover_by_exposure(
        y: float,
        z: float,
        diameter: float,
        section_width: float,
        section_height: float,
        exposure_class: str,
    ) -> None:
        c_nom = RebarValidator.required_cover_exposure(exposure_class, diameter)
        RebarValidator.validate_rebar_position(
            y=y,
            z=z,
            diameter=diameter,
            section_width=section_width,
            section_height=section_height,
            cover=c_nom,
        )

    @staticmethod
    def validate_minimum_reinforcement(As: float, Ac: float) -> None:
        """
        Validate minimum reinforcement ratio (EC2 9.2.1.1)

        Args:
            As: Steel area
            Ac: Concrete area

        Raises:
            RebarValidationError: If reinforcement ratio is too low
        """
        if As <= 0:
            raise RebarValidationError("Section non armée : au moins une armature requise")

        ratio = As / Ac
        min_ratio = 0.002  # 0.2% minimum pour EC2

        if ratio < min_ratio:
            import warnings

            warnings.warn(
                f"Taux d'armature faible : {ratio*100:.2f}% " f"(minimum EC2 : {min_ratio*100}%)",
                UserWarning,
            )

    @staticmethod
    def validate_maximum_reinforcement(As: float, Ac: float) -> None:
        """
        Validate maximum reinforcement ratio (EC2 9.2.1.1)

        Args:
            As: Steel area
            Ac: Concrete area

        Raises:
            RebarValidationError: If reinforcement ratio is too high
        """
        ratio = As / Ac
        max_ratio = 0.08  # 8% maximum pour EC2

        if ratio > max_ratio:
            raise RebarValidationError(
                f"Taux d'armature trop élevé : {ratio*100:.2f}% "
                f"(maximum EC2 : {max_ratio*100}%)"
            )

        # Avertissement si > 4% (congestion probable)
        if ratio > 0.04:
            import warnings

            warnings.warn(
                f"Taux d'armature élevé : {ratio*100:.2f}% " f"(risque de congestion)", UserWarning
            )


class LoadValidator:
    """Validates applied loads"""

    @staticmethod
    def validate_axial_load(N: float, section_area: float, concrete_strength: float) -> None:
        """
        Validate axial load magnitude

        Args:
            N: Axial load in kN (positive = compression)
            section_area: Section area in m²
            concrete_strength: Concrete design strength in MPa

        Raises:
            LoadValidationError: If load seems unrealistic
        """
        # Capacité approximative de la section
        approx_capacity = concrete_strength * section_area * 1000  # kN

        if abs(N) > 2 * approx_capacity:
            raise LoadValidationError(
                f"Effort normal très élevé : {N:.0f} kN "
                f"(capacité approximative : {approx_capacity:.0f} kN). "
                f"Vérifiez les unités (kN attendus)."
            )

    @staticmethod
    def validate_moment(
        M: float, section_height: float, section_area: float, concrete_strength: float
    ) -> None:
        """
        Validate bending moment magnitude

        Args:
            M: Bending moment in kN·m
            section_height: Section height in m
            section_area: Section area in m²
            concrete_strength: Concrete design strength in MPa

        Raises:
            LoadValidationError: If moment seems unrealistic
        """
        # Capacité approximative en flexion
        lever_arm = section_height * 0.8
        approx_capacity = concrete_strength * section_area * lever_arm * 1000  # kN·m

        if abs(M) > 2 * approx_capacity:
            raise LoadValidationError(
                f"Moment très élevé : {M:.0f} kN·m "
                f"(capacité approximative : {approx_capacity:.0f} kN·m). "
                f"Vérifiez les unités (kN·m attendus)."
            )

    @staticmethod
    def validate_unit_consistency(N: float, M: float) -> None:
        """
        Validate that units seem consistent

        Args:
            N: Axial load (should be in kN)
            M: Moment (should be in kN·m)

        Raises:
            LoadValidationError: If units seem wrong
        """
        # Si N >> M, probablement erreur d'unités
        # (N en N au lieu de kN, ou M en N·m au lieu de kN·m)
        if abs(N) > 1000 * abs(M) and abs(M) > 0:
            import warnings

            warnings.warn(
                f"N = {N:.0f} kN et M = {M:.0f} kN·m : " f"ratio inhabituel. Vérifiez les unités.",
                UserWarning,
            )


class SectionValidator:
    """High-level validator for complete section"""

    @staticmethod
    def validate_all(
        section,
        concrete,
        steel,
        rebars,
        N: float = None,
        M_y: float = None,
        M_z: float = None,
        exposure_class: Optional[str] = None,
    ) -> None:
        """
        Validate complete section with all parameters

        Args:
            section: Section object
            concrete: Concrete material
            steel: Steel material
            rebars: RebarGroup
            N: Axial load (optional)
            M_y: Moment around y (optional)
            M_z: Moment around z (optional)

        Raises:
            ValidationError: If any validation fails
        """
        # Validate geometry
        if hasattr(section, "width") and hasattr(section, "height"):
            GeometryValidator.validate_rectangular_section(section.width, section.height)
        elif hasattr(section, "diameter"):
            GeometryValidator.validate_circular_section(section.diameter)

        # Validate materials
        MaterialValidator.validate_concrete_strength(concrete.fck)
        MaterialValidator.validate_steel_strength(steel.fyk)

        # Validate rebars
        for rebar in rebars.rebars:
            RebarValidator.validate_diameter(rebar.diameter)
            RebarValidator.validate_number_of_bars(rebar.n)

            # Check position in section
            if hasattr(section, "width") and hasattr(section, "height"):
                if exposure_class:
                    RebarValidator.validate_cover_by_exposure(
                        rebar.y,
                        rebar.z,
                        rebar.diameter,
                        section.width,
                        section.height,
                        exposure_class,
                    )
                else:
                    RebarValidator.validate_rebar_position(
                        rebar.y, rebar.z, rebar.diameter, section.width, section.height
                    )

        # Validate reinforcement ratios
        props = section.properties
        RebarValidator.validate_minimum_reinforcement(rebars.total_area, props.area)
        RebarValidator.validate_maximum_reinforcement(rebars.total_area, props.area)

        # Validate loads if provided
        if N is not None:
            LoadValidator.validate_axial_load(N, props.area, concrete.fcd)

        if M_z is not None:
            LoadValidator.validate_moment(
                M_z,
                section.height if hasattr(section, "height") else section.diameter,
                props.area,
                concrete.fcd,
            )

        if N is not None and M_z is not None:
            LoadValidator.validate_unit_consistency(N, M_z)
