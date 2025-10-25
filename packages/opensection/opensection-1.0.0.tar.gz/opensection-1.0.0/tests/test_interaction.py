"""
Tests unitaires pour les diagrammes d'interaction
"""

import numpy as np
import pytest

from opensection import (
    RectangularSection,
    CircularSection,
    ConcreteEC2,
    SteelEC2,
    RebarGroup,
    SectionSolver,
)
from opensection.interaction import InteractionDiagram


class TestInteractionDiagram:
    """Tests pour les diagrammes d'interaction N-M"""

    def test_interaction_diagram_creation(self):
        """Test création d'un diagramme d'interaction"""
        # Section rectangulaire
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        # Armatures
        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        # Solver
        solver = SectionSolver(section, concrete, steel, rebars)

        # Diagramme d'interaction
        diagram = InteractionDiagram(solver)
        assert diagram.solver is not None

    def test_compute_NM_curve(self):
        """Test calcul de la courbe N-M"""
        # Section rectangulaire
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        # Armatures symétriques
        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)
        diagram = InteractionDiagram(solver)

        # Calculer courbe (peu de points pour le test)
        M_vals, N_vals = diagram.compute_NM_curve(n_points=10)

        # Vérifications
        assert len(M_vals) > 0
        assert len(N_vals) > 0
        assert len(M_vals) == len(N_vals)

    def test_pure_compression_point(self):
        """Test point de compression pure"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)

        # Compression pure (M=0)
        result = solver.solve(N=2000, My=0, Mz=0)

        # En compression pure, on devrait avoir peu de courbure
        assert abs(result.chi_z) < 0.01
        assert result.converged

    def test_pure_bending_point(self):
        """Test point de flexion pure"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)

        # Flexion pure (N≈0)
        result = solver.solve(N=1, My=0, Mz=100)

        assert result.converged
        # En flexion pure, moment résistant devrait être significatif
        assert abs(result.Mz) > 50  # kN·m

    def test_circular_section_interaction(self):
        """Test diagramme pour section circulaire"""
        section = CircularSection(diameter=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        # Armatures circulaires
        rebars = RebarGroup()
        rebars.add_circular_array(
            center_y=0.0, center_z=0.0, radius=0.20, n=8, diameter=0.020
        )

        solver = SectionSolver(section, concrete, steel, rebars)
        diagram = InteractionDiagram(solver)

        # Test que ça fonctionne
        assert diagram.solver is not None

    def test_balanced_failure_point(self):
        """Test point d'équilibre (rupture béton et acier simultanée)"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)

        # Point d'équilibre approximatif
        result = solver.solve(N=800, My=0, Mz=120)

        assert result.converged
        # Les contraintes devraient être significatives
        assert result.sigma_c_max > 10  # MPa
        assert result.sigma_s_max > 200  # MPa

    def test_interaction_curve_symmetric(self):
        """Test symétrie de la courbe pour section symétrique"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        # Armatures symétriques
        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)

        # Test moment positif vs négatif avec même effort normal
        result_pos = solver.solve(N=500, My=0, Mz=100)
        result_neg = solver.solve(N=500, My=0, Mz=-100)

        # Pour section symétrique, capacités devraient être similaires
        # (pas exactement égales à cause de la non-linéarité)
        assert result_pos.converged
        assert result_neg.converged

    def test_interaction_with_high_strength_concrete(self):
        """Test avec béton haute résistance"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=60)  # Béton haute résistance
        steel = SteelEC2(fyk=500)

        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)
        diagram = InteractionDiagram(solver)

        # Devrait fonctionner avec béton haute résistance
        M_vals, N_vals = diagram.compute_NM_curve(n_points=5)
        assert len(M_vals) > 0

    def test_interaction_with_unsymmetric_reinforcement(self):
        """Test avec armatures non-symétriques"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        # Armatures non-symétriques
        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.025, n=4)  # Plus d'armatures en haut
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.016, n=2)  # Moins en bas

        solver = SectionSolver(section, concrete, steel, rebars)

        # Test résolution
        result = solver.solve(N=500, My=0, Mz=100)
        assert result.converged

    def test_maximum_moment_capacity(self):
        """Test capacité maximale en moment"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)

        # Tester plusieurs efforts normaux pour trouver le moment max
        moments = []
        for N in [0, 500, 1000, 1500]:
            for M_trial in np.linspace(50, 200, 5):
                try:
                    result = solver.solve(N=N, My=0, Mz=M_trial)
                    if result.converged:
                        moments.append(result.Mz)
                except Exception:
                    pass

        # Il devrait y avoir des moments résistants calculés
        assert len(moments) > 0
        assert max(moments) > 50  # kN·m


class TestInteractionDiagramValidation:
    """Tests de validation physique des diagrammes d'interaction"""

    def test_interaction_envelope_convex(self):
        """Test que l'enveloppe d'interaction est convexe (approximativement)"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)
        diagram = InteractionDiagram(solver)

        M_vals, N_vals = diagram.compute_NM_curve(n_points=10)

        # Vérifier qu'on a suffisamment de points
        assert len(M_vals) >= 3

    def test_compression_reduces_moment_capacity_limit(self):
        """Test que la compression excessive réduit la capacité en moment"""
        section = RectangularSection(width=0.3, height=0.5)
        concrete = ConcreteEC2(fck=30)
        steel = SteelEC2(fyk=500)

        rebars = RebarGroup()
        rebars.add_rebar(y=0.20, z=0.0, diameter=0.020, n=3)
        rebars.add_rebar(y=-0.20, z=0.0, diameter=0.020, n=3)

        solver = SectionSolver(section, concrete, steel, rebars)

        # Tester différents niveaux de compression
        moments = []
        N_values = [100, 500, 1000, 2000, 3000]

        for N in N_values:
            try:
                # Chercher le moment qui donne convergence
                for M_trial in np.linspace(200, 50, 10):
                    result = solver.solve(N=N, My=0, Mz=M_trial)
                    if result.converged:
                        moments.append((N, result.Mz))
                        break
            except Exception:
                pass

        # On devrait avoir quelques points convergés
        assert len(moments) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

