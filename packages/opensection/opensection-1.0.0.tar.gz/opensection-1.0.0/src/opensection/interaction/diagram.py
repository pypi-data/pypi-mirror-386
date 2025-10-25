"""
Diagrammes d'interaction N-M
"""

from typing import Tuple

import numpy as np

from opensection.solver.section_solver import SectionSolver


class InteractionDiagram:
    """Génère des diagrammes d'interaction"""

    def __init__(self, solver: SectionSolver):
        self.solver = solver

    def compute_NM_curve(self, n_points: int = 50) -> Tuple[np.ndarray, np.ndarray]:
        """Calcule la courbe N-M"""
        M_vals = []
        N_vals = []

        # Compression pure à traction pure
        props = self.solver.section.properties
        area_total = props.area

        # Estimer Nmax et Nmin
        N_max = (
            self.solver.concrete.fcd * area_total
            + self.solver.rebars.total_area * self.solver.steel.fyd
        )
        N_min = -self.solver.rebars.total_area * self.solver.steel.fyd

        N_range = np.linspace(N_max / 1000, N_min / 1000, n_points)  # kN

        for N in N_range:
            # Résoudre pour différentes courbures
            for chi in np.linspace(0, 0.01, 20):
                try:
                    result = self.solver.solve(N=N, My=0, Mz=chi * 1000)
                    if result.converged:
                        M_vals.append(result.Mz)
                        N_vals.append(result.N)
                        break
                except Exception:
                    continue

        return np.array(M_vals), np.array(N_vals)
