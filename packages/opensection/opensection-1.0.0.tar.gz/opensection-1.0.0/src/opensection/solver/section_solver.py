"""
Solveur de section en flexion composée déviée
Méthode de Newton-Raphson avec discrétisation par fibres
"""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np

from opensection.geometry.section import Section
from opensection.materials.concrete import ConcreteEC2
from opensection.materials.steel import SteelEC2
from opensection.reinforcement.rebar import RebarGroup
from opensection.utils import NumericalConstants, UnitConverter, clamp, is_converged, safe_divide


@dataclass
class SolverResult:
    """Résultat de la résolution"""

    epsilon_0: float  # Déformation axiale au CG
    chi_y: float  # Courbure autour de y
    chi_z: float  # Courbure autour de z
    N: float  # Effort normal (kN)
    My: float  # Moment autour de y (kN·m)
    Mz: float  # Moment autour de z (kN·m)
    sigma_c_max: float  # Contrainte béton max (MPa)
    sigma_s_max: float  # Contrainte acier max (MPa)
    converged: bool  # Convergence
    n_iter: int  # Nombre d'itérations
    # Diagnostics de convergence
    residual_norm_history: Optional[List[float]] = None
    step_norm_history: Optional[List[float]] = None
    reason: Optional[str] = None  # 'converged' | 'singular' | 'max_iter'

    @property
    def neutral_axis_depth(self) -> float:
        """Distance de l'axe neutre au CG"""
        if abs(self.chi_y) < 1e-12 and abs(self.chi_z) < 1e-12:
            return float("inf")
        return abs(self.epsilon_0) / np.sqrt(self.chi_y**2 + self.chi_z**2)


class SectionSolver:
    """
    Solveur pour section en flexion composée déviée
    Résout le système : F(d) = S
    où d = (e0, χ_y, χ_z) et S = (N, M_y, M_z)
    """

    def __init__(
        self,
        section: Section,
        concrete: ConcreteEC2,
        steel: SteelEC2,
        rebars: RebarGroup,
        fiber_area: float = 0.0001,
    ):
        """
        Args:
            section: Section géométrique
            concrete: Matériau béton
            steel: Matériau acier
            rebars: Groupe d'armatures
            fiber_area: Aire cible des fibres (m²)
        """
        self.section = section
        self.concrete = concrete
        self.steel = steel
        self.rebars = rebars

        # Créer le maillage de fibres
        self.fibers = section.create_fiber_mesh(fiber_area)
        self.rebar_array = rebars.to_array()

        # Centre de gravité de la section
        props = section.properties
        self.yc, self.zc = props.centroid

    def compute_strain(self, y: float, z: float, d: np.ndarray) -> float:
        """
        Calcule la déformation en un point
        e(y,z) = e0 + χ_y·y + χ_z·z

        Args:
            y, z: Coordonnées du point
            d: Vecteur [e0, χ_y, χ_z]

        Returns:
            Déformation
        """
        epsilon_0, chi_y, chi_z = d
        return epsilon_0 + chi_y * (y - self.yc) + chi_z * (z - self.zc)

    def compute_internal_forces(self, d: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Calcule les efforts internes F(d) et la matrice tangente K

        Args:
            d: Vecteur [e0, χ_y, χ_z]

        Returns:
            F: Vecteur [N, M_y, M_z]
            K: Matrice tangente 3x3
        """
        epsilon_0, chi_y, chi_z = d

        # Initialiser
        F = np.zeros(3)
        K = np.zeros((3, 3))

        # Contribution du béton (fibres)
        if len(self.fibers) > 0:
            y_fibers = self.fibers[:, 0] - self.yc
            z_fibers = self.fibers[:, 1] - self.zc
            A_fibers = self.fibers[:, 2]

            # Déformations des fibres
            eps_fibers = epsilon_0 + chi_y * y_fibers + chi_z * z_fibers

            # Contraintes et modules tangents
            sigma_c = self.concrete.stress_vectorized(eps_fibers)
            Et_c = self.concrete.tangent_modulus_vectorized(eps_fibers)

            # Efforts internes
            F[0] += np.sum(sigma_c * A_fibers)
            F[1] += np.sum(sigma_c * A_fibers * z_fibers)
            F[2] += np.sum(sigma_c * A_fibers * y_fibers)

            # Matrice tangente
            K[0, 0] += np.sum(Et_c * A_fibers)
            K[0, 1] += np.sum(Et_c * A_fibers * y_fibers)
            K[0, 2] += np.sum(Et_c * A_fibers * z_fibers)
            K[1, 0] += np.sum(Et_c * A_fibers * z_fibers)
            K[1, 1] += np.sum(Et_c * A_fibers * z_fibers * y_fibers)
            K[1, 2] += np.sum(Et_c * A_fibers * z_fibers**2)
            K[2, 0] += np.sum(Et_c * A_fibers * y_fibers)
            K[2, 1] += np.sum(Et_c * A_fibers * y_fibers**2)
            K[2, 2] += np.sum(Et_c * A_fibers * y_fibers * z_fibers)

        # Contribution des aciers
        if len(self.rebar_array) > 0:
            y_rebars = self.rebar_array[:, 0] - self.yc
            z_rebars = self.rebar_array[:, 1] - self.zc
            A_rebars = self.rebar_array[:, 2]

            # Déformations des aciers
            eps_rebars = epsilon_0 + chi_y * y_rebars + chi_z * z_rebars

            # Contraintes et modules tangents
            sigma_s = self.steel.stress_vectorized(eps_rebars)
            Et_s = self.steel.tangent_modulus_vectorized(eps_rebars)

            # Efforts internes
            F[0] += np.sum(sigma_s * A_rebars)
            F[1] += np.sum(sigma_s * A_rebars * z_rebars)
            F[2] += np.sum(sigma_s * A_rebars * y_rebars)

            # Matrice tangente
            K[0, 0] += np.sum(Et_s * A_rebars)
            K[0, 1] += np.sum(Et_s * A_rebars * y_rebars)
            K[0, 2] += np.sum(Et_s * A_rebars * z_rebars)
            K[1, 0] += np.sum(Et_s * A_rebars * z_rebars)
            K[1, 1] += np.sum(Et_s * A_rebars * z_rebars * y_rebars)
            K[1, 2] += np.sum(Et_s * A_rebars * z_rebars**2)
            K[2, 0] += np.sum(Et_s * A_rebars * y_rebars)
            K[2, 1] += np.sum(Et_s * A_rebars * y_rebars**2)
            K[2, 2] += np.sum(Et_s * A_rebars * y_rebars * z_rebars)

        # Conversion: sigma (MPa) * A (m²) -> Force (kN)
        # Utilisation de UnitConverter pour garantir la cohérence
        # Note: Les efforts sont déjà calculés en "unités brutes" (MPa·m²)
        # et doivent être convertis en kN et kN·m
        F *= 1000.0  # MPa·m² = MN -> kN
        K *= 1000.0  # Ajuster la matrice tangente

        return F, K

    def solve(
        self,
        N: float,
        My: float = 0,
        Mz: float = 0,
        tol: float = None,
        max_iter: int = None,
        use_relative_tol: bool = False,
    ) -> SolverResult:
        """
        Résout F(d) = S par Newton-Raphson

        Args:
            N: Effort normal (kN, positif en compression)
            My: Moment autour de y (kN·m)
            Mz: Moment autour de z (kN·m)
            tol: Tolérance de convergence (défaut: NumericalConstants.TOL_FORCE_DEFAULT)
            max_iter: Nombre max d'itérations (défaut: NumericalConstants.MAX_ITER_DEFAULT)

        Returns:
            SolverResult avec les résultats
        """
        # Utiliser les constantes par défaut si non spécifiées
        if tol is None:
            tol = (
                NumericalConstants.TOL_FORCE_DEFAULT
                if not use_relative_tol
                else NumericalConstants.TOL_RESIDUAL_REL_DEFAULT
            )
        if max_iter is None:
            max_iter = NumericalConstants.MAX_ITER_DEFAULT

        S = np.array([N, My, Mz])

        # Initialisation basée sur estimation linéaire élastique
        props = self.section.properties

        # Calculer la rigidité axiale totale (kN)
        EA_concrete = UnitConverter.modulus_area_to_stiffness(self.concrete.Ecm, props.area)
        EA_steel = UnitConverter.modulus_area_to_stiffness(self.steel.Es, self.rebars.total_area)
        EA_total = EA_concrete + EA_steel

        # Estimation initiale de epsilon_0 basée sur effort axial
        # epsilon_0 = N / EA (avec limitation)
        if EA_total > NumericalConstants.EPSILON_ZERO:
            eps0_guess = safe_divide(N, EA_total, default=0.0)
            eps0_guess = clamp(eps0_guess, -0.002, 0.002)  # Limiter à ±2‰
        else:
            eps0_guess = 0.0

        d = np.array(
            [
                eps0_guess,  # e0 initial
                0.0,  # χ_y initial
                0.0,  # χ_z initial
            ]
        )

        converged = False
        reason = "max_iter"
        residual_norm_history: List[float] = []
        step_norm_history: List[float] = []

        for iter in range(max_iter):
            # Calculer F(d) et K(d)
            F, K = self.compute_internal_forces(d)

            # Résidu
            R = F - S
            residual_norm = float(np.linalg.norm(R))
            residual_norm_history.append(residual_norm)

            # Test de convergence (utilisation de la fonction is_converged)
            if is_converged(R, tol, relative=use_relative_tol, reference=S):
                converged = True
                reason = "converged"
                break

            # Résoudre K·Δd = -R
            try:
                delta_d = np.linalg.solve(K, -R)
            except np.linalg.LinAlgError:
                # Matrice singulière
                reason = "singular"
                break

            # Line search avec backtracking
            alpha = NumericalConstants.ALPHA_INITIAL
            norm_R = np.linalg.norm(R)

            for _ in range(NumericalConstants.MAX_ITER_LINE_SEARCH):
                d_trial = d + alpha * delta_d
                F_trial, _ = self.compute_internal_forces(d_trial)
                R_trial = F_trial - S
                norm_R_trial = np.linalg.norm(R_trial)

                if norm_R_trial < norm_R:
                    # Amélioration trouvée
                    d = d_trial
                    break
                else:
                    # Réduire le pas
                    alpha *= NumericalConstants.ALPHA_REDUCTION
                    if alpha < NumericalConstants.ALPHA_MIN:
                        # Pas trop petit, accepter quand même
                        d = d_trial
                        break
            else:
                # Aucune amélioration trouvée, prendre le dernier essai
                d = d_trial

            # Stocker la norme du pas
            step_norm_history.append(float(np.linalg.norm(delta_d)))

        # Calculer les contraintes max
        epsilon_0, chi_y, chi_z = d

        sigma_c_max = 0.0
        if len(self.fibers) > 0:
            y_fibers = self.fibers[:, 0] - self.yc
            z_fibers = self.fibers[:, 1] - self.zc
            eps_fibers = epsilon_0 + chi_y * y_fibers + chi_z * z_fibers
            sigma_c = self.concrete.stress_vectorized(eps_fibers)
            sigma_c_max = np.max(np.abs(sigma_c))

        sigma_s_max = 0.0
        if len(self.rebar_array) > 0:
            y_rebars = self.rebar_array[:, 0] - self.yc
            z_rebars = self.rebar_array[:, 1] - self.zc
            eps_rebars = epsilon_0 + chi_y * y_rebars + chi_z * z_rebars
            sigma_s = self.steel.stress_vectorized(eps_rebars)
            sigma_s_max = np.max(np.abs(sigma_s))

        return SolverResult(
            epsilon_0=epsilon_0,
            chi_y=chi_y,
            chi_z=chi_z,
            N=F[0],
            My=F[1],
            Mz=F[2],
            sigma_c_max=sigma_c_max,
            sigma_s_max=sigma_s_max,
            converged=converged,
            n_iter=iter + 1,
            residual_norm_history=residual_norm_history,
            step_norm_history=step_norm_history,
            reason=reason,
        )
