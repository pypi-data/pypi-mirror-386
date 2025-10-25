"""
Vérifications Eurocode 2
"""

from opensection.solver.section_solver import SolverResult
from opensection.utils import CodeConstants


class EC2Verification:
    """Vérifications selon EC2"""

    @staticmethod
    def check_ULS(result: SolverResult, fcd: float, fyd: float) -> dict:
        """Vérification ELU"""
        checks = {}

        # Contrainte béton
        checks["concrete_stress"] = {
            "value": result.sigma_c_max,
            "limit": fcd,
            "ratio": result.sigma_c_max / fcd if fcd > 0 else 0,
            "ok": result.sigma_c_max <= fcd,
        }

        # Contrainte acier
        checks["steel_stress"] = {
            "value": result.sigma_s_max,
            "limit": fyd,
            "ratio": result.sigma_s_max / fyd if fyd > 0 else 0,
            "ok": result.sigma_s_max <= fyd,
        }

        return checks

    @staticmethod
    def check_SLS(result: SolverResult, fck: float, fyk: float) -> dict:
        """Vérification ELS"""
        checks = {}

        # Contraintes limitées
        sigma_c_lim = CodeConstants.EC2.K_SLS_CONCRETE * fck
        sigma_s_lim = CodeConstants.EC2.K_SLS_STEEL * fyk

        checks["concrete_stress_SLS"] = {
            "value": result.sigma_c_max,
            "limit": sigma_c_lim,
            "ok": result.sigma_c_max <= sigma_c_lim,
        }

        checks["steel_stress_SLS"] = {
            "value": result.sigma_s_max,
            "limit": sigma_s_lim,
            "ok": result.sigma_s_max <= sigma_s_lim,
        }

        return checks

    @staticmethod
    def check_rebar_ratios(As: float, Ac: float) -> dict:
        """Contrôles simplifiés des taux d'armature min/max (EC2 9.2.1.1)."""
        ratio = As / Ac if Ac > 0 else 0.0
        min_ratio = 0.002
        max_ratio = 0.08
        checks = {
            "rho": ratio,
            "min_ok": ratio >= min_ratio,
            "max_ok": ratio <= max_ratio,
            "min_required": min_ratio,
            "max_allowed": max_ratio,
        }
        return checks
