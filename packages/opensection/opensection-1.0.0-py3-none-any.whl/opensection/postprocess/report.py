"""
Génération de rapports
"""

from opensection.solver.section_solver import SolverResult


class ReportGenerator:
    """Génère des rapports de calcul"""

    @staticmethod
    def generate_text_report(result: SolverResult) -> str:
        """Génère un rapport texte"""
        report = []
        report.append("=" * 60)
        report.append("RAPPORT DE CALCUL DE SECTION")
        report.append("=" * 60)
        report.append("")
        report.append("RÉSULTATS DE CONVERGENCE:")
        report.append(f"  Convergence: {'OUI' if result.converged else 'NON'}")
        report.append(f"  Itérations: {result.n_iter}")
        report.append("")
        report.append("DÉFORMATIONS:")
        report.append(f"  e0 = {result.epsilon_0:.6f} (‰: {result.epsilon_0*1000:.3f})")
        report.append(f"  χ_y = {result.chi_y:.6e} rad/m")
        report.append(f"  χ_z = {result.chi_z:.6e} rad/m")
        report.append("")
        report.append("EFFORTS:")
        report.append(f"  N = {result.N:.2f} kN")
        report.append(f"  M_y = {result.My:.2f} kN·m")
        report.append(f"  M_z = {result.Mz:.2f} kN·m")
        report.append("")
        report.append("CONTRAINTES MAXIMALES:")
        report.append(f"  s_c,max = {result.sigma_c_max:.2f} MPa")
        report.append(f"  s_s,max = {result.sigma_s_max:.2f} MPa")
        report.append("")
        report.append(f"Profondeur axe neutre: {result.neutral_axis_depth:.4f} m")
        report.append("=" * 60)

        return "\n".join(report)
