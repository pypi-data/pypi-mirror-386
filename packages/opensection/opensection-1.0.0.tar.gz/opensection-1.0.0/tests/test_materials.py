"""
Tests unitaires pour les matériaux
"""

import numpy as np
import pytest

import opensection as ops
from opensection.materials import ConcreteEC2, SteelEC2, StructuralSteelEC3


class TestConcreteEC2:
    """Tests pour le béton EC2"""

    def test_concrete_creation(self):
        """Test création béton C30/37"""
        concrete = ConcreteEC2(fck=30)
        assert concrete.fck == 30
        assert concrete.fcd > 0
        assert concrete.Ecm > 0

    def test_concrete_stress_compression(self):
        """Test contrainte en compression"""
        concrete = ConcreteEC2(fck=30)

        # Compression faible
        epsilon = 0.001  # 1 permil
        sigma = concrete.stress(epsilon)
        assert sigma > 0
        assert sigma < concrete.fcd

    def test_concrete_stress_tension(self):
        """Test contrainte en traction (négligée)"""
        concrete = ConcreteEC2(fck=30)
        epsilon = -0.001  # Traction
        sigma = concrete.stress(epsilon)
        assert sigma == 0.0  # Béton en traction négligé

    def test_concrete_stress_plateau(self):
        """Test plateau plastique"""
        concrete = ConcreteEC2(fck=30)
        epsilon = 0.003  # Sur le plateau
        sigma = concrete.stress(epsilon)
        assert abs(sigma - concrete.fcd) < 0.01

    def test_concrete_stress_rupture(self):
        """Test après rupture"""
        concrete = ConcreteEC2(fck=30)
        epsilon = 0.005  # Au-delà de epsilon_cu2
        sigma = concrete.stress(epsilon)
        assert sigma == 0.0

    def test_concrete_high_strength(self):
        """Test béton haute résistance"""
        concrete = ConcreteEC2(fck=60)
        assert concrete.fck == 60
        assert concrete.epsilon_c2 > 0.002  # Différent du béton normal


class TestSteelEC2:
    """Tests pour l'acier d'armature EC2"""

    def test_steel_creation(self):
        """Test création acier B500B"""
        steel = SteelEC2(fyk=500)
        assert steel.fyk == 500
        assert steel.fyd > 0
        assert steel.Es == 200000

    def test_steel_elastic_tension(self):
        """Test branche élastique en traction"""
        steel = SteelEC2(fyk=500)
        epsilon = 0.001
        sigma = steel.stress(epsilon)
        assert abs(sigma - steel.Es * epsilon) < 1.0

    def test_steel_plastic_tension(self):
        """Test plateau plastique en traction"""
        steel = SteelEC2(fyk=500)
        epsilon = 0.01  # Bien au-delà de epsilon_yk
        sigma = steel.stress(epsilon)
        assert abs(sigma - steel.fyd) < 1.0

    def test_steel_elastic_compression(self):
        """Test branche élastique en compression"""
        steel = SteelEC2(fyk=500)
        epsilon = -0.001
        sigma = steel.stress(epsilon)
        assert abs(sigma + steel.Es * 0.001) < 1.0

    def test_steel_plastic_compression(self):
        """Test plateau plastique en compression"""
        steel = SteelEC2(fyk=500)
        epsilon = -0.01
        sigma = steel.stress(epsilon)
        assert abs(sigma + steel.fyd) < 1.0

    def test_steel_with_hardening(self):
        """Test avec écrouissage"""
        steel = SteelEC2(fyk=500, include_hardening=True, k=0.01)
        epsilon = 0.01
        sigma = steel.stress(epsilon)
        assert sigma > steel.fyd  # Avec écrouissage

    def test_steel_vectorized(self):
        """Test calcul vectorisé"""
        steel = SteelEC2(fyk=500)
        epsilons = np.array([0.0, 0.001, 0.01, -0.001, -0.01])
        sigmas = steel.stress_vectorized(epsilons)
        assert len(sigmas) == len(epsilons)
        assert sigmas[0] == 0.0  # Epsilon = 0


class TestStructuralSteelEC3:
    """Tests pour l'acier de charpente EC3"""

    def test_structural_steel_creation(self):
        """Test création acier S235"""
        steel = StructuralSteelEC3(fy=235)
        assert steel.fy == 235
        assert steel.Ea == 210000

    def test_structural_steel_elastic(self):
        """Test branche élastique"""
        steel = StructuralSteelEC3(fy=235)
        epsilon = 0.0005
        sigma = steel.stress(epsilon)
        assert abs(sigma - steel.Ea * epsilon) < 1.0

    def test_structural_steel_plastic(self):
        """Test plateau plastique"""
        steel = StructuralSteelEC3(fy=235)
        epsilon = 0.01
        sigma = steel.stress(epsilon)
        assert abs(sigma - steel.fyd) < 1.0


class TestConcreteEC2Advanced:
    """Tests avancés pour le béton EC2"""

    def test_concrete_tangent_modulus(self):
        """Test module tangent"""
        concrete = ConcreteEC2(fck=30)
        
        # Dans la zone élastique
        epsilon = 0.0005
        Et = concrete.tangent_modulus(epsilon)
        assert Et > 0
        assert Et < concrete.Ecm * 2  # Ordre de grandeur
    
    def test_concrete_tangent_modulus_plateau(self):
        """Test module tangent sur plateau"""
        concrete = ConcreteEC2(fck=30)
        
        # Sur le plateau
        epsilon = 0.003
        Et = concrete.tangent_modulus(epsilon)
        assert Et == 0.0  # Plateau plastique
    
    def test_concrete_stress_curve_monotonic(self):
        """Test que la courbe est monotone croissante jusqu'au pic"""
        concrete = ConcreteEC2(fck=30)
        
        epsilons = np.linspace(0, concrete.epsilon_c2, 10)
        sigmas = [concrete.stress(e) for e in epsilons]
        
        # Vérifier croissance monotone
        for i in range(len(sigmas) - 1):
            assert sigmas[i+1] >= sigmas[i]
    
    def test_concrete_multiple_strengths(self):
        """Test plusieurs classes de béton"""
        strengths = [20, 25, 30, 35, 40, 50, 60, 70, 80, 90]
        
        for fck in strengths:
            concrete = ConcreteEC2(fck=fck)
            assert concrete.fck == fck
            assert concrete.fcd > 0
            assert concrete.fcd < concrete.fck  # Avec sécurité
            assert concrete.epsilon_c2 > 0
            # Pour béton haute résistance, epsilon_cu2 peut être très proche de epsilon_c2
            assert concrete.epsilon_cu2 >= concrete.epsilon_c2 * 0.95
    
    def test_concrete_vectorized_vs_scalar(self):
        """Test cohérence vectorisé vs scalaire"""
        concrete = ConcreteEC2(fck=30)
        
        epsilons = np.array([0.0, 0.001, 0.002, 0.0035])
        
        # Vectorisé
        sigmas_vec = concrete.stress_vectorized(epsilons)
        
        # Scalaire
        sigmas_scalar = np.array([concrete.stress(e) for e in epsilons])
        
        np.testing.assert_allclose(sigmas_vec, sigmas_scalar, rtol=1e-10)
    
    def test_concrete_negative_strains(self):
        """Test déformations négatives (traction)"""
        concrete = ConcreteEC2(fck=30)
        
        epsilons_tension = np.array([-0.001, -0.01, -0.1])
        sigmas = concrete.stress_vectorized(epsilons_tension)
        
        # Béton en traction négligé
        assert np.all(sigmas == 0.0)
    
    def test_concrete_custom_gamma_c(self):
        """Test coefficient de sécurité personnalisé"""
        concrete1 = ConcreteEC2(fck=30, gamma_c=1.5)
        concrete2 = ConcreteEC2(fck=30, gamma_c=1.2)
        
        # Avec gamma_c plus faible, fcd plus élevé
        assert concrete2.fcd > concrete1.fcd
    
    def test_concrete_alpha_cc(self):
        """Test coefficient alpha_cc"""
        concrete1 = ConcreteEC2(fck=30, alpha_cc=0.85)
        concrete2 = ConcreteEC2(fck=30, alpha_cc=1.0)
        
        # Avec alpha_cc plus élevé, fcd plus élevé
        assert concrete2.fcd > concrete1.fcd


class TestSteelEC2Advanced:
    """Tests avancés pour l'acier EC2"""

    def test_steel_tangent_modulus_elastic(self):
        """Test module tangent élastique"""
        steel = SteelEC2(fyk=500)
        
        epsilon = 0.0005
        Et = steel.tangent_modulus(epsilon)
        assert Et == steel.Es
    
    def test_steel_tangent_modulus_plastic(self):
        """Test module tangent plastique"""
        steel = SteelEC2(fyk=500, include_hardening=False)
        
        epsilon = 0.01
        Et = steel.tangent_modulus(epsilon)
        assert Et == 0.0
    
    def test_steel_tangent_modulus_hardening(self):
        """Test module tangent avec écrouissage"""
        steel = SteelEC2(fyk=500, include_hardening=True, k=0.01)
        
        epsilon = 0.01
        Et = steel.tangent_modulus(epsilon)
        assert Et == steel.k * steel.Es
    
    def test_steel_symmetric_behavior(self):
        """Test comportement symétrique traction/compression"""
        steel = SteelEC2(fyk=500)
        
        epsilon_pos = 0.005
        epsilon_neg = -0.005
        
        sigma_pos = steel.stress(epsilon_pos)
        sigma_neg = steel.stress(epsilon_neg)
        
        # Symétrie
        assert abs(sigma_pos + sigma_neg) < 1.0
    
    def test_steel_vectorized_vs_scalar(self):
        """Test cohérence vectorisé vs scalaire"""
        steel = SteelEC2(fyk=500)
        
        epsilons = np.array([-0.01, -0.001, 0.0, 0.001, 0.01])
        
        # Vectorisé
        sigmas_vec = steel.stress_vectorized(epsilons)
        
        # Scalaire
        sigmas_scalar = np.array([steel.stress(e) for e in epsilons])
        
        np.testing.assert_allclose(sigmas_vec, sigmas_scalar, rtol=1e-10)
    
    def test_steel_rupture_limit(self):
        """Test limite de rupture"""
        steel = SteelEC2(fyk=500)
        
        # Au-delà de epsilon_ud
        epsilon_rupture = steel.epsilon_ud + 0.01
        sigma = steel.stress(epsilon_rupture)
        
        assert sigma == 0.0  # Rupture
    
    def test_steel_different_grades(self):
        """Test différentes nuances d'acier"""
        grades = [400, 500, 600]
        
        for fyk in grades:
            steel = SteelEC2(fyk=fyk)
            assert steel.fyk == fyk
            assert steel.fyd == fyk / steel.gamma_s
            assert steel.epsilon_yk == steel.fyd / steel.Es
    
    def test_steel_hardening_effect(self):
        """Test effet de l'écrouissage"""
        steel_no_hard = SteelEC2(fyk=500, include_hardening=False)
        steel_hard = SteelEC2(fyk=500, include_hardening=True, k=0.01)
        
        epsilon = 0.02
        sigma_no_hard = steel_no_hard.stress(epsilon)
        sigma_hard = steel_hard.stress(epsilon)
        
        # Avec écrouissage, contrainte plus élevée
        assert sigma_hard > sigma_no_hard
    
    def test_steel_tangent_modulus_vectorized(self):
        """Test module tangent vectorisé"""
        steel = SteelEC2(fyk=500)
        
        epsilons = np.array([0.0005, 0.005, -0.0005, -0.005])
        Et = steel.tangent_modulus_vectorized(epsilons)
        
        # Les 2 premiers élastiques, les 2 autres plastiques ou élastiques
        assert Et[0] == steel.Es
        assert Et[2] == steel.Es


class TestPrestressingSteelEC2:
    """Tests pour l'acier de précontrainte"""

    def test_prestressing_creation(self):
        """Test création acier de précontrainte"""
        steel = ops.PrestressingSteelEC2(fp01k=1500)
        assert steel.fp01k == 1500
        assert steel.Ep == 195000
    
    def test_prestressing_stress_elastic(self):
        """Test contrainte zone élastique"""
        steel = ops.PrestressingSteelEC2(fp01k=1500)
        epsilon = 0.005
        sigma = steel.stress(epsilon)
        assert sigma > 0
    
    def test_prestressing_no_compression(self):
        """Test pas de résistance en compression"""
        steel = ops.PrestressingSteelEC2(fp01k=1500)
        epsilon = -0.001
        sigma = steel.stress(epsilon)
        assert sigma == 0.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
