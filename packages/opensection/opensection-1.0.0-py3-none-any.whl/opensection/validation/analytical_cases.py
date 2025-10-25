"""
Analytical validation cases for concrete sections
Based on Eurocode 2 formulas and simplified assumptions
"""

from dataclasses import dataclass
from typing import Any, Dict


@dataclass
class AnalyticalSolution:
    """Analytical solution for a test case"""

    N: float  # Axial load (kN)
    M: float  # Bending moment (kN·m)
    epsilon_0: float  # Axial strain
    chi: float  # Curvature (rad/m)
    x_n: float  # Neutral axis depth (m)
    sigma_c_max: float  # Max concrete stress (MPa)
    sigma_s_tension: float  # Steel tension stress (MPa)
    sigma_s_compression: float  # Steel compression stress (MPa)
    method: str  # Calculation method


class RectangularBeamCase:
    """
    Analytical solutions for rectangular reinforced concrete beams
    Based on simplified EC2 assumptions
    """

    @staticmethod
    def pure_bending_balanced(
        width: float = 0.3,
        height: float = 0.5,
        d: float = 0.45,  # Effective depth
        d_prime: float = 0.05,  # Compression steel depth
        As_tension: float = 0.001,  # m²
        As_compression: float = 0.0004,  # m²
        fck: float = 30.0,  # MPa
        fyk: float = 500.0,  # MPa
    ) -> AnalyticalSolution:
        """
        Case 1: Balanced failure (pivot B)
        Section rectangulaire en flexion simple avec armatures tendues et comprimées

        Hypothèses simplifiées:
        - Diagramme rectangulaire pour le béton (EC2 3.1.7)
        - epsilon_cu = 3.5‰
        - fcd = alpha_cc * fck / gamma_c
        - fyd = fyk / gamma_s

        Returns:
            AnalyticalSolution with all calculated values
        """
        # Material properties EC2
        gamma_c = 1.5
        gamma_s = 1.15
        alpha_cc = 0.85

        fcd = alpha_cc * fck / gamma_c  # 17.0 MPa pour C30
        fyd = fyk / gamma_s  # 434.78 MPa pour B500

        # EC2 pivot B: epsilon_cu = 3.5‰, epsilon_s = fyd/Es
        epsilon_cu = 0.0035
        Es = 200000  # MPa
        epsilon_yd = fyd / Es  # ~2.17‰

        # Hauteur utile
        d_eff = d  # Distance de la fibre comprimée aux aciers tendus

        # Position de l'axe neutre pour équilibre (pivot B)
        # epsilon_cu / x_n = (epsilon_cu + epsilon_yd) / d
        # x_n = epsilon_cu * d / (epsilon_cu + epsilon_yd)
        x_n = epsilon_cu * d_eff / (epsilon_cu + epsilon_yd)

        # Hauteur du bloc de béton comprimé (EC2)
        # Pour diagramme rectangulaire: lambda = 0.8, eta = 1.0 pour fck ≤ 50 MPa
        lambda_factor = 0.8
        eta = 1.0
        y_compressed = lambda_factor * x_n  # Hauteur du rectangle de contraintes

        # Forces dans le béton
        Fc = eta * fcd * width * y_compressed  # Force de compression béton

        # Déformation dans l'acier comprimé
        epsilon_s_comp = epsilon_cu * (x_n - d_prime) / x_n
        sigma_s_comp = min(epsilon_s_comp * Es, fyd)
        Fs_comp = As_compression * sigma_s_comp

        # Déformation dans l'acier tendu
        epsilon_s_tens = epsilon_cu * (d_eff - x_n) / x_n
        sigma_s_tens = min(epsilon_s_tens * Es, fyd)
        Fs_tens = As_tension * sigma_s_tens

        # Effort normal (flexion simple)
        N = (Fc + Fs_comp - Fs_tens) * 1000  # kN

        # Moment autour du centre géométrique
        z_c = height / 2  # Centre de la section

        # Bras de levier des forces par rapport au centre
        arm_concrete = z_c - y_compressed / 2  # Béton comprimé
        arm_s_comp = z_c - d_prime  # Acier comprimé
        arm_s_tens = d_eff - z_c  # Acier tendu

        M = (Fc * arm_concrete + Fs_comp * arm_s_comp + Fs_tens * arm_s_tens) * 1000  # kN·m

        # Courbure
        chi = epsilon_cu / x_n

        # Déformation moyenne en fibre supérieure
        epsilon_0 = epsilon_cu - chi * z_c

        return AnalyticalSolution(
            N=N,
            M=M,
            epsilon_0=epsilon_0,
            chi=chi,
            x_n=x_n,
            sigma_c_max=fcd,
            sigma_s_tension=sigma_s_tens,
            sigma_s_compression=sigma_s_comp,
            method="EC2 Pivot B - Balanced Failure",
        )

    @staticmethod
    def pure_compression(
        width: float = 0.3,
        height: float = 0.5,
        As_total: float = 0.001,  # m² (aire totale d'armatures)
        fck: float = 30.0,
        fyk: float = 500.0,
    ) -> AnalyticalSolution:
        """
        Case 2: Pure compression (N only, M=0)

        Formule simplifiée EC2 pour compression centrée:
        N_Rd = Ac * fcd + As * fyd

        Returns:
            AnalyticalSolution
        """
        gamma_c = 1.5
        gamma_s = 1.15
        alpha_cc = 0.85

        fcd = alpha_cc * fck / gamma_c
        fyd = fyk / gamma_s

        Ac = width * height
        As = As_total

        # Capacité en compression pure
        N_max = (Ac * fcd + As * fyd) * 1000  # kN

        # Pour un niveau de chargement à 30% (cas test)
        N = 0.3 * N_max

        # Déformation uniforme
        Es = 200000
        E_equiv = (Ac * fcd / 0.002 + As * Es) / (Ac + As)  # Module équivalent
        epsilon_0 = (N / 1000) / (E_equiv * (Ac + As))

        # Contraintes
        sigma_c = min(epsilon_0 * fcd / 0.002, fcd)  # Simplifié
        sigma_s = min(epsilon_0 * Es, fyd)

        return AnalyticalSolution(
            N=N,
            M=0.0,
            epsilon_0=epsilon_0,
            chi=0.0,
            x_n=height,  # Toute la section comprimée
            sigma_c_max=sigma_c,
            sigma_s_tension=sigma_s,
            sigma_s_compression=sigma_s,
            method="EC2 Pure Compression",
        )

    @staticmethod
    def elastic_linear(
        width: float = 0.3,
        height: float = 0.5,
        d: float = 0.45,
        As_tension: float = 0.001,
        N: float = 100,  # kN
        M: float = 50,  # kN·m
        fck: float = 30.0,
        fyk: float = 500.0,
    ) -> AnalyticalSolution:
        """
        Case 3: Elastic linear analysis (small loads)

        Hypothèses:
        - Comportement linéaire élastique
        - Section homogénéisée
        - Navier-Bernoulli

        Returns:
            AnalyticalSolution
        """
        # Modules élastiques
        Ecm = 22000 * ((fck + 8) / 10) ** 0.3  # EC2
        Es = 200000
        n = Es / Ecm  # Coefficient d'équivalence

        # Section homogénéisée
        Ac = width * height
        I_c = width * height**3 / 12

        # Aire d'acier équivalente en béton
        As_equiv = As_tension * n

        # Position du centre de gravité (simplifié, armatures en bas)
        y_cg = height / 2  # Approximation

        # Aire totale homogénéisée
        A_total = Ac + As_equiv

        # Inertie homogénéisée (approximation)
        I_total = I_c + As_equiv * (d - y_cg) ** 2

        # Contraintes et déformations (Navier)
        epsilon_0 = (N * 1000) / (Ecm * A_total)
        chi = (M * 1000 * 1000) / (Ecm * I_total)  # M en N·mm

        # Position de l'axe neutre
        x_n = epsilon_0 / chi if chi > 1e-10 else height

        # Contraintes
        sigma_c_top = Ecm * (epsilon_0 + chi * height / 2)
        sigma_c_max = abs(sigma_c_top) / 1000  # MPa

        sigma_s = Es * (epsilon_0 + chi * (d - height / 2))
        sigma_s_tens = sigma_s / 1000  # MPa

        return AnalyticalSolution(
            N=N,
            M=M,
            epsilon_0=epsilon_0,
            chi=chi,
            x_n=x_n,
            sigma_c_max=sigma_c_max,
            sigma_s_tension=sigma_s_tens,
            sigma_s_compression=0.0,
            method="Elastic Linear (Navier-Bernoulli)",
        )


class TBeamCase:
    """
    Analytical solutions for T-beam sections
    """

    @staticmethod
    def flange_in_compression(
        flange_width: float = 0.8,
        flange_thickness: float = 0.15,
        web_width: float = 0.25,
        web_height: float = 0.45,
        d: float = 0.55,
        As_tension: float = 0.002,
        fck: float = 30.0,
        fyk: float = 500.0,
    ) -> AnalyticalSolution:
        """
        Case: T-beam with full flange in compression

        Hypothèses:
        - Axe neutre dans la table (x_n < h_f)
        - Table entièrement comprimée
        - Diagramme rectangulaire EC2

        Returns:
            AnalyticalSolution
        """
        gamma_c = 1.5
        gamma_s = 1.15
        alpha_cc = 0.85

        fcd = alpha_cc * fck / gamma_c
        fyd = fyk / gamma_s

        # Hypothèse: axe neutre dans la table
        # Équilibre: Fc = Fs
        # fcd * b_eff * lambda * x_n = As * fyd

        lambda_factor = 0.8
        eta = 1.0

        # Position de l'axe neutre
        x_n = (As_tension * fyd) / (eta * fcd * flange_width * lambda_factor)

        if x_n > flange_thickness:
            # Axe neutre dans l'âme, calcul plus complexe
            # Simplifié pour ce cas
            x_n = flange_thickness * 0.9

        # Force de compression (table uniquement)
        y_comp = lambda_factor * x_n
        Fc = eta * fcd * flange_width * y_comp

        # Force de traction
        epsilon_cu = 0.0035
        epsilon_s = epsilon_cu * (d - x_n) / x_n
        Es = 200000
        sigma_s = min(epsilon_s * Es, fyd)
        Fs = As_tension * sigma_s

        # Effort normal
        N = (Fc - Fs) * 1000  # kN

        # Moment (par rapport au centre de gravité)
        z_cg = (
            flange_width * flange_thickness * flange_thickness / 2
            + web_width * web_height * (flange_thickness + web_height / 2)
        ) / (flange_width * flange_thickness + web_width * web_height)

        arm_c = z_cg - y_comp / 2
        arm_s = d - z_cg

        M = (Fc * arm_c + Fs * arm_s) * 1000  # kN·m

        # Courbure
        chi = epsilon_cu / x_n
        epsilon_0 = epsilon_cu - chi * z_cg

        return AnalyticalSolution(
            N=N,
            M=M,
            epsilon_0=epsilon_0,
            chi=chi,
            x_n=x_n,
            sigma_c_max=fcd,
            sigma_s_tension=sigma_s,
            sigma_s_compression=0.0,
            method="T-Beam with flange in compression",
        )


class ValidationDatabase:
    """
    Database of validation cases with analytical solutions
    """

    def __init__(self):
        self.cases = {}
        self._build_database()

    def _build_database(self):
        """Build the complete validation database"""

        # RECTANGULAR BEAMS
        self.cases["rect_balanced"] = {
            "description": "Poutre rectangulaire 30x50cm en flexion équilibrée (pivot B)",
            "geometry": {
                "width": 0.3,
                "height": 0.5,
                "d": 0.45,
                "d_prime": 0.05,
            },
            "reinforcement": {
                "As_tension": 0.001,  # 10 cm² (environ 5HA16)
                "As_compression": 0.0004,  # 4 cm² (environ 2HA16)
            },
            "materials": {
                "fck": 30.0,
                "fyk": 500.0,
            },
            "solution": RectangularBeamCase.pure_bending_balanced(),
            "tolerance": 0.05,  # 5%
        }

        self.cases["rect_compression"] = {
            "description": "Poteau rectangulaire 30x50cm en compression centrée",
            "geometry": {
                "width": 0.3,
                "height": 0.5,
            },
            "reinforcement": {
                "As_total": 0.001,  # 10 cm²
            },
            "materials": {
                "fck": 30.0,
                "fyk": 500.0,
            },
            "solution": RectangularBeamCase.pure_compression(),
            "tolerance": 0.03,  # 3%
        }

        self.cases["rect_elastic"] = {
            "description": "Poutre rectangulaire en régime élastique",
            "geometry": {
                "width": 0.3,
                "height": 0.5,
                "d": 0.45,
            },
            "reinforcement": {
                "As_tension": 0.001,
            },
            "materials": {
                "fck": 30.0,
                "fyk": 500.0,
            },
            "loads": {
                "N": 100,  # kN
                "M": 50,  # kN·m
            },
            "solution": RectangularBeamCase.elastic_linear(N=100, M=50),
            "tolerance": 0.10,  # 10% (élastique moins précis)
        }

        # T-BEAMS
        self.cases["tbeam_flange"] = {
            "description": "Poutre en T avec table comprimée",
            "geometry": {
                "flange_width": 0.8,
                "flange_thickness": 0.15,
                "web_width": 0.25,
                "web_height": 0.45,
                "d": 0.55,
            },
            "reinforcement": {
                "As_tension": 0.002,  # 20 cm²
            },
            "materials": {
                "fck": 30.0,
                "fyk": 500.0,
            },
            "solution": TBeamCase.flange_in_compression(),
            "tolerance": 0.08,  # 8%
        }

    def get_case(self, case_name: str) -> Dict[str, Any]:
        """Get a validation case by name"""
        return self.cases.get(case_name)

    def list_cases(self) -> list:
        """List all available validation cases"""
        return list(self.cases.keys())

    def get_summary(self) -> str:
        """Get a summary of all validation cases"""
        summary = "=== BASE DE VALIDATION opensection ===\n\n"
        summary += f"Nombre de cas : {len(self.cases)}\n\n"

        for name, case in self.cases.items():
            summary += f"{name}:\n"
            summary += f"  {case['description']}\n"
            sol = case["solution"]
            summary += f"  N = {sol.N:.2f} kN, M = {sol.M:.2f} kN·m\n"
            summary += f"  Méthode : {sol.method}\n"
            summary += f"  Tolérance : {case['tolerance']*100:.0f}%\n\n"

        return summary


if __name__ == "__main__":
    # Test de la base de validation
    db = ValidationDatabase()
    print(db.get_summary())

    # Exemple d'utilisation
    case = db.get_case("rect_balanced")
    if case:
        sol = case["solution"]
        print("\nDétails cas 'rect_balanced':")
        print(f"  N = {sol.N:.3f} kN")
        print(f"  M = {sol.M:.3f} kN·m")
        print(f"  epsilon_0 = {sol.epsilon_0*1000:.3f} ‰")
        print(f"  chi = {sol.chi:.6f} rad/m")
        print(f"  x_n = {sol.x_n*100:.2f} cm")
        print(f"  sigma_c_max = {sol.sigma_c_max:.2f} MPa")
        print(f"  sigma_s_tension = {sol.sigma_s_tension:.2f} MPa")
