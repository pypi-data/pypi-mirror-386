"""
Lois de comportement du béton selon Eurocode 2

Convention de signe pour le béton (génie civil) :
- Déformation positive : compression
- Déformation négative : traction
- Contrainte positive : compression
- Contrainte négative : traction

Cette convention est traditionnelle en béton armé où le béton travaille
principalement en compression.
"""

import numpy as np


class ConcreteEC2:
    """
    Béton selon Eurocode 2 (EN 1992-1-1)
    Diagramme parabole-rectangle
    """

    def __init__(self, fck: float, gamma_c: float = 1.5, alpha_cc: float = 0.85):
        """
        Args:
            fck: Résistance caractéristique en compression (MPa)
            gamma_c: Coefficient partiel de sécurité
            alpha_cc: Coefficient d'effets long terme
        """
        self.fck = fck
        self.gamma_c = gamma_c
        self.alpha_cc = alpha_cc

        # Résistance de calcul
        self.fcd = alpha_cc * fck / gamma_c

        # Paramètres de déformation
        if fck <= 50:
            self.epsilon_c2 = 2.0e-3  # 2‰
            self.epsilon_cu2 = 3.5e-3  # 3.5‰
            self.n = 2.0
        else:
            # Béton haute résistance
            self.epsilon_c2 = (2.0 + 0.085 * (fck - 50) ** 0.53) * 1e-3
            self.epsilon_cu2 = (2.6 + 35 * ((90 - fck) / 100) ** 4) * 1e-3
            self.n = 1.4 + 23.4 * ((90 - fck) / 100) ** 4

        # Module d'élasticité sécant
        self.Ecm = 22000 * ((fck + 8) / 10) ** 0.3

    def stress(self, epsilon: float) -> float:
        """
        Calcule la contrainte pour une déformation donnée

        s_c(e) = fcd [1 - (1 - e/e_c2)^n]  pour 0 ≤ e ≤ e_c2
        s_c(e) = fcd                        pour e_c2 < e ≤ e_cu2
        s_c(e) = 0                          pour e > e_cu2

        Args:
            epsilon: Déformation (positive en compression)

        Returns:
            Contrainte (positive en compression) en MPa
        """
        if epsilon < 0:
            # Béton en traction (négligé en ELU)
            return 0.0
        elif epsilon <= self.epsilon_c2:
            # Branche parabolique
            ratio = epsilon / self.epsilon_c2
            return self.fcd * (1 - (1 - ratio) ** self.n)
        elif epsilon <= self.epsilon_cu2:
            # Plateau plastique
            return self.fcd
        else:
            # Rupture
            return 0.0

    def tangent_modulus(self, epsilon: float) -> float:
        """
        Calcule le module tangent Et = ds/de

        Args:
            epsilon: Déformation

        Returns:
            Module tangent en MPa
        """
        if epsilon < 0:
            return 0.0
        elif epsilon <= self.epsilon_c2:
            # Dérivée de la parabole
            ratio = epsilon / self.epsilon_c2
            return self.fcd * self.n * (1 - ratio) ** (self.n - 1) / self.epsilon_c2
        elif epsilon <= self.epsilon_cu2:
            # Plateau plastique
            return 0.0
        else:
            return 0.0

    def stress_vectorized(self, epsilon: np.ndarray) -> np.ndarray:
        """Version vectorisée pour numpy arrays"""
        sigma = np.zeros_like(epsilon)

        # Compression
        mask1 = (epsilon >= 0) & (epsilon <= self.epsilon_c2)
        ratio = epsilon[mask1] / self.epsilon_c2
        sigma[mask1] = self.fcd * (1 - (1 - ratio) ** self.n)

        mask2 = (epsilon > self.epsilon_c2) & (epsilon <= self.epsilon_cu2)
        sigma[mask2] = self.fcd

        return sigma

    def tangent_modulus_vectorized(self, epsilon: np.ndarray) -> np.ndarray:
        """Version vectorisée du module tangent"""
        Et = np.zeros_like(epsilon)

        mask = (epsilon >= 0) & (epsilon <= self.epsilon_c2)
        ratio = epsilon[mask] / self.epsilon_c2
        Et[mask] = self.fcd * self.n * (1 - ratio) ** (self.n - 1) / self.epsilon_c2

        return Et
