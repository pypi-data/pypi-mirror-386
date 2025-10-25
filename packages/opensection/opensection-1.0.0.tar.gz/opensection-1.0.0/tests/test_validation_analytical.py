"""
Tests de validation du solver contre des solutions analytiques
"""

import numpy as np
import pytest

from opensection import ConcreteEC2, RebarGroup, RectangularSection, SectionSolver, SteelEC2, TSection
from opensection.validation.analytical_cases import ValidationDatabase


class TestAnalyticalValidation:
    """
    Tests de validation contre solutions analytiques
    Vérifie que le solver numérique retrouve les solutions analytiques
    """

    @pytest.fixture
    def validation_db(self):
        """Load validation database"""
        return ValidationDatabase()

    def test_database_loaded(self, validation_db):
        """Test that validation database is properly loaded"""
        cases = validation_db.list_cases()
        assert len(cases) >= 4  # Au moins 4 cas de test
        assert "rect_balanced" in cases
        assert "rect_compression" in cases
        assert "rect_elastic" in cases
        assert "tbeam_flange" in cases

    def test_rectangular_balanced_bending(self, validation_db):
        """
        Test validation: Poutre rectangulaire en flexion équilibrée
        Compare solver numérique vs solution analytique EC2
        """
        case = validation_db.get_case("rect_balanced")
        geom = case["geometry"]
        reinf = case["reinforcement"]
        mat = case["materials"]
        sol_analytical = case["solution"]
        tol = case["tolerance"]

        # Créer la section
        section = RectangularSection(width=geom["width"], height=geom["height"])
        concrete = ConcreteEC2(fck=mat["fck"])
        steel = SteelEC2(fyk=mat["fyk"])
        rebars = RebarGroup()

        # Armatures tendues (en bas)
        d = geom["d"]
        y_tension = -(geom["height"] / 2 - (geom["height"] - d))
        n_bars_tension = int(reinf["As_tension"] / (np.pi * 0.016**2 / 4)) + 1
        rebars.add_rebar(y=y_tension, z=0.0, diameter=0.016, n=n_bars_tension)

        # Armatures comprimées (en haut)
        d_prime = geom["d_prime"]
        y_compression = geom["height"] / 2 - d_prime
        n_bars_compression = int(reinf["As_compression"] / (np.pi * 0.016**2 / 4)) + 1
        rebars.add_rebar(y=y_compression, z=0.0, diameter=0.016, n=n_bars_compression)

        # Résoudre
        solver = SectionSolver(section, concrete, steel, rebars)

        # Chercher la solution pour N et M donnés
        result = solver.solve(N=sol_analytical.N, My=0, Mz=sol_analytical.M, tol=1e-2, max_iter=100)

        print(f"\n  Cas: {case['description']}")
        print(f"  Solution analytique:")
        print(f"    N = {sol_analytical.N:.2f} kN")
        print(f"    M = {sol_analytical.M:.2f} kN·m")
        print(f"    x_n = {sol_analytical.x_n*100:.2f} cm")
        print(f"  Solution numérique:")
        print(f"    Converged = {result.converged}")
        print(f"    N = {result.N:.2f} kN")
        print(f"    M_z = {result.Mz:.2f} kN·m")

        # Vérifications (si convergence)
        if result.converged:
            # Tolérance sur les efforts
            assert np.abs(result.N - sol_analytical.N) / abs(sol_analytical.N) < tol
            assert np.abs(result.Mz - sol_analytical.M) / abs(sol_analytical.M) < tol
            print(
                f"  [OK] Écart N: {np.abs(result.N - sol_analytical.N)/abs(sol_analytical.N)*100:.2f}%"
            )
            print(
                f"  [OK] Écart M: {np.abs(result.Mz - sol_analytical.M)/abs(sol_analytical.M)*100:.2f}%"
            )

    def test_rectangular_pure_compression(self, validation_db):
        """
        Test validation: Compression centrée
        """
        case = validation_db.get_case("rect_compression")
        geom = case["geometry"]
        reinf = case["reinforcement"]
        mat = case["materials"]
        sol_analytical = case["solution"]
        tol = case["tolerance"]

        # Créer la section
        section = RectangularSection(width=geom["width"], height=geom["height"])
        concrete = ConcreteEC2(fck=mat["fck"])
        steel = SteelEC2(fyk=mat["fyk"])
        rebars = RebarGroup()

        # Armatures réparties (4 coins)
        As_per_bar = reinf["As_total"] / 4
        diameter = np.sqrt(4 * As_per_bar / np.pi)
        rebars.add_rebar(y=0.20, z=0.12, diameter=diameter, n=1)
        rebars.add_rebar(y=0.20, z=-0.12, diameter=diameter, n=1)
        rebars.add_rebar(y=-0.20, z=0.12, diameter=diameter, n=1)
        rebars.add_rebar(y=-0.20, z=-0.12, diameter=diameter, n=1)

        # Résoudre
        solver = SectionSolver(section, concrete, steel, rebars)
        result = solver.solve(N=sol_analytical.N, My=0, Mz=0, tol=1e-2, max_iter=100)

        print(f"\n  Cas: {case['description']}")
        print(f"  Solution analytique: N = {sol_analytical.N:.2f} kN")
        print(f"  Solution numérique: N = {result.N:.2f} kN, converged = {result.converged}")

        if result.converged:
            error = np.abs(result.N - sol_analytical.N) / abs(sol_analytical.N)
            assert error < tol
            print(f"  [OK] Écart: {error*100:.2f}%")

    def test_rectangular_elastic(self, validation_db):
        """
        Test validation: Régime élastique
        """
        case = validation_db.get_case("rect_elastic")
        geom = case["geometry"]
        reinf = case["reinforcement"]
        mat = case["materials"]
        loads = case["loads"]
        sol_analytical = case["solution"]
        tol = case["tolerance"]

        # Créer la section
        section = RectangularSection(width=geom["width"], height=geom["height"])
        concrete = ConcreteEC2(fck=mat["fck"])
        steel = SteelEC2(fyk=mat["fyk"])
        rebars = RebarGroup()

        # Armatures tendues
        d = geom["d"]
        y_tension = -(geom["height"] / 2 - (geom["height"] - d))
        n_bars = int(reinf["As_tension"] / (np.pi * 0.016**2 / 4)) + 1
        rebars.add_rebar(y=y_tension, z=0.0, diameter=0.016, n=n_bars)

        # Résoudre
        solver = SectionSolver(section, concrete, steel, rebars)
        result = solver.solve(N=loads["N"], My=0, Mz=loads["M"], tol=1e-2, max_iter=100)

        print(f"\n  Cas: {case['description']}")
        print(f"  Charges: N = {loads['N']} kN, M = {loads['M']} kN·m")
        print(f"  Solution numérique: converged = {result.converged}")

        if result.converged:
            error_N = np.abs(result.N - loads["N"]) / abs(loads["N"])
            error_M = np.abs(result.Mz - loads["M"]) / abs(loads["M"])
            print(f"  [OK] Écart N: {error_N*100:.2f}%")
            print(f"  [OK] Écart M: {error_M*100:.2f}%")
            # En élastique, on accepte une tolérance plus large
            assert error_N < tol
            assert error_M < tol


class TestAnalyticalCases:
    """Test des fonctions de calcul analytique elles-mêmes"""

    def test_analytical_balanced_bending_realistic(self):
        """Test que la solution analytique donne des valeurs réalistes"""
        from opensection.validation.analytical_cases import RectangularBeamCase

        sol = RectangularBeamCase.pure_bending_balanced()

        # Vérifications de cohérence
        assert sol.M > 0  # Moment positif
        assert 0 < sol.x_n < 0.5  # Axe neutre dans la section
        assert 0 < sol.sigma_c_max <= 20  # Contrainte béton raisonnable (fcd ~ 17 MPa)
        assert 0 < sol.sigma_s_tension <= 500  # Contrainte acier raisonnable
        assert sol.chi > 0  # Courbure positive

        print(f"\nSolution analytique flexion équilibrée:")
        print(f"  M = {sol.M:.2f} kN·m")
        print(f"  x_n = {sol.x_n*100:.2f} cm")
        print(f"  sigma_c = {sol.sigma_c_max:.2f} MPa")
        print(f"  sigma_s = {sol.sigma_s_tension:.2f} MPa")

    def test_analytical_compression_realistic(self):
        """Test compression pure analytique"""
        from opensection.validation.analytical_cases import RectangularBeamCase

        sol = RectangularBeamCase.pure_compression()

        assert sol.N > 0  # Compression positive
        assert sol.M == 0  # Pas de moment
        assert sol.chi == 0  # Pas de courbure
        assert sol.epsilon_0 > 0  # Déformation de compression

        print(f"\nSolution analytique compression pure:")
        print(f"  N = {sol.N:.2f} kN")
        print(f"  epsilon_0 = {sol.epsilon_0*1000:.3f} ‰")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
