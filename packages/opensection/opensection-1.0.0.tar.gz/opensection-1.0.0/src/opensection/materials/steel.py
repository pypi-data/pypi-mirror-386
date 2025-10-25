"""
Lois de comportement des aciers selon Eurocodes

Convention de signe pour l'acier (mécanique classique) :
- Déformation positive : traction
- Déformation négative : compression
- Contrainte positive : traction
- Contrainte négative : compression

Cette convention suit les standards de la mécanique des solides où l'acier
travaille principalement en traction.
"""

import numpy as np


class SteelEC2:
    """
    Acier d'armature passive selon EC2
    Loi bilinéaire avec écrouissage optionnel
    """

    def __init__(
        self,
        fyk: float,
        gamma_s: float = 1.15,
        Es: float = 200000,
        include_hardening: bool = False,
        k: float = 0.01,
    ):
        """
        Args:
            fyk: Limite d'élasticité caractéristique (MPa)
            gamma_s: Coefficient partiel de sécurité
            Es: Module d'Young (MPa)
            include_hardening: Inclure l'écrouissage
            k: Coefficient d'écrouissage (pente = k*Es)
        """
        self.fyk = fyk
        self.gamma_s = gamma_s
        self.Es = Es
        self.include_hardening = include_hardening
        self.k = k

        # Limite d'élasticité de calcul
        self.fyd = fyk / gamma_s

        # Déformation élastique
        self.epsilon_yk = self.fyd / Es

        # Déformation ultime (approximation)
        self.epsilon_uk = 0.05  # 5% pour classe B
        self.epsilon_ud = 0.9 * self.epsilon_uk

    def stress(self, epsilon: float) -> float:
        """
        Calcule la contrainte

        s = Es·e                           pour |e| ≤ e_yk
        s = sign(e)·fyd                    pour e_yk < |e| ≤ e_ud (sans écrouissage)
        s = sign(e)·[fyd + Es^h·(|e|-e_yk)] pour e_yk < |e| ≤ e_ud (avec écrouissage)

        Args:
            epsilon: Déformation (positive en traction)

        Returns:
            Contrainte en MPa (positive en traction)
        """
        abs_epsilon = abs(epsilon)
        sign = np.sign(epsilon) if epsilon != 0 else 0

        if abs_epsilon <= self.epsilon_yk:
            # Branche élastique
            return self.Es * epsilon
        elif abs_epsilon <= self.epsilon_ud:
            # Branche plastique
            if self.include_hardening:
                Esh = self.k * self.Es
                return sign * (self.fyd + Esh * (abs_epsilon - self.epsilon_yk))
            else:
                return sign * self.fyd
        else:
            # Rupture
            return 0.0

    def tangent_modulus(self, epsilon: float) -> float:
        """Module tangent"""
        abs_epsilon = abs(epsilon)

        if abs_epsilon <= self.epsilon_yk:
            return self.Es
        elif abs_epsilon <= self.epsilon_ud:
            if self.include_hardening:
                return self.k * self.Es
            else:
                return 0.0
        else:
            return 0.0

    def stress_vectorized(self, epsilon: np.ndarray) -> np.ndarray:
        """Version vectorisée"""
        sigma = np.zeros_like(epsilon)
        abs_eps = np.abs(epsilon)
        sign = np.sign(epsilon)

        # Élastique
        mask1 = abs_eps <= self.epsilon_yk
        sigma[mask1] = self.Es * epsilon[mask1]

        # Plastique
        mask2 = (abs_eps > self.epsilon_yk) & (abs_eps <= self.epsilon_ud)
        if self.include_hardening:
            Esh = self.k * self.Es
            sigma[mask2] = sign[mask2] * (self.fyd + Esh * (abs_eps[mask2] - self.epsilon_yk))
        else:
            sigma[mask2] = sign[mask2] * self.fyd

        return sigma

    def tangent_modulus_vectorized(self, epsilon: np.ndarray) -> np.ndarray:
        """Version vectorisée du module tangent"""
        Et = np.zeros_like(epsilon)
        abs_eps = np.abs(epsilon)

        mask1 = abs_eps <= self.epsilon_yk
        Et[mask1] = self.Es

        if self.include_hardening:
            mask2 = (abs_eps > self.epsilon_yk) & (abs_eps <= self.epsilon_ud)
            Et[mask2] = self.k * self.Es

        return Et


class PrestressingSteelEC2:
    """Acier de précontrainte selon EC2"""

    def __init__(self, fp01k: float, Ep: float = 195000):
        """
        Args:
            fp01k: Résistance à 0.1% (MPa)
            Ep: Module d'Young (MPa)
        """
        self.fp01k = fp01k
        self.Ep = Ep
        self.epsilon_p01 = fp01k / Ep
        self.epsilon_pu = 0.02
        self.m = 2.0

    def stress(self, epsilon: float) -> float:
        """Loi contrainte-déformation pour précontrainte"""
        if epsilon < 0:
            return 0.0
        elif epsilon <= self.epsilon_pu:
            ratio = epsilon / self.epsilon_pu
            return (self.fp01k / self.epsilon_p01) * epsilon * (1 - ratio**self.m)
        else:
            return 0.0


class StructuralSteelEC3:
    """Acier de charpente selon EC3"""

    def __init__(self, fy: float, gamma_M0: float = 1.0, Ea: float = 210000):
        """
        Args:
            fy: Limite d'élasticité (MPa)
            gamma_M0: Coefficient partiel
            Ea: Module d'Young (MPa)
        """
        self.fy = fy
        self.gamma_M0 = gamma_M0
        self.Ea = Ea
        self.fyd = fy / gamma_M0
        self.epsilon_y = self.fyd / Ea

    def stress(self, epsilon: float) -> float:
        """Loi élasto-plastique parfaite"""
        abs_epsilon = abs(epsilon)
        sign = np.sign(epsilon) if epsilon != 0 else 0

        if abs_epsilon <= self.epsilon_y:
            return self.Ea * epsilon
        else:
            return sign * self.fyd

    def tangent_modulus(self, epsilon: float) -> float:
        if abs(epsilon) <= self.epsilon_y:
            return self.Ea
        else:
            return 0.0
