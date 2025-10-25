"""
Tests complets pour reduction_factors.py - Viser 100% coverage
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import numpy as np
from openeurotop import reduction_factors


class TestGammaFRoughness:
    """Tests complets pour gamma_f_roughness"""
    
    def test_all_coating_types(self):
        """Test tous les types de revêtement"""
        coatings = {
            "lisse": 1.0,
            "beton_lisse": 1.0,
            "asphalte": 1.0,
            "herbe": 1.0,
            "gazon": 1.0,
            "beton_rugueux": 0.9,
            "beton_colonne": 0.85,
            "enrochement_1couche": 0.55,
            "enrochement_2couches": 0.50,
            "enrochement_impermeable": 0.45,
            "cubes": 0.47,
            "antifer": 0.47,
            "tetrapodes": 0.38,
            "accropode": 0.46,
            "xbloc": 0.45,
            "core_loc": 0.44,
        }
        
        for coating, expected in coatings.items():
            gamma = reduction_factors.gamma_f_roughness(coating)
            assert gamma == expected, f"Erreur pour {coating}"
            print(f"[OK] {coating:25s} : gamma_f = {gamma:.2f}")
    
    def test_case_insensitive(self):
        """Test insensibilité à la casse"""
        assert reduction_factors.gamma_f_roughness("LISSE") == 1.0
        assert reduction_factors.gamma_f_roughness("Asphalte") == 1.0
        assert reduction_factors.gamma_f_roughness("ENROCHEMENT_2COUCHES") == 0.50
        print("[OK] Case insensitive")
    
    def test_with_spaces(self):
        """Test avec espaces"""
        assert reduction_factors.gamma_f_roughness("beton lisse") == 1.0
        assert reduction_factors.gamma_f_roughness("core loc") == 0.44
        print("[OK] Gestion espaces")
    
    def test_numeric_value(self):
        """Test valeur numérique directe"""
        assert reduction_factors.gamma_f_roughness(0.75) == 0.75
        assert reduction_factors.gamma_f_roughness(1.0) == 1.0
        print("[OK] Valeur numérique")
    
    def test_unknown_coating(self):
        """Test revêtement inconnu"""
        with pytest.raises(ValueError) as exc_info:
            reduction_factors.gamma_f_roughness("inconnu")
        assert "non reconnu" in str(exc_info.value)
        print("[OK] Erreur pour revêtement inconnu")


class TestGammaBetaObliquity:
    """Tests complets pour gamma_beta_obliquity"""
    
    def test_perpendicular(self):
        """Test vagues perpendiculaires"""
        assert reduction_factors.gamma_beta_obliquity(0) == 1.0
        assert reduction_factors.gamma_beta_obliquity(5) == 1.0
        print("[OK] Perpendiculaire")
    
    def test_moderate_obliquity(self):
        """Test obliquité modérée"""
        gamma_30 = reduction_factors.gamma_beta_obliquity(30)
        gamma_60 = reduction_factors.gamma_beta_obliquity(60)
        
        assert gamma_30 > gamma_60
        assert 0.8 < gamma_30 < 1.0
        assert 0.7 < gamma_60 < 0.9
        print(f"[OK] Obliquité: 30°={gamma_30:.3f}, 60°={gamma_60:.3f}")
    
    def test_extreme_obliquity(self):
        """Test obliquité extrême"""
        gamma_80 = reduction_factors.gamma_beta_obliquity(80)
        gamma_90 = reduction_factors.gamma_beta_obliquity(90)
        
        # Au-delà de 80°, plafonné
        assert gamma_80 == gamma_90
        print(f"[OK] Obliquité extrême: 80°={gamma_80:.3f}")
    
    def test_negative_angle(self):
        """Test angle négatif (valeur absolue)"""
        gamma_pos = reduction_factors.gamma_beta_obliquity(45)
        gamma_neg = reduction_factors.gamma_beta_obliquity(-45)
        assert gamma_pos == gamma_neg
        print("[OK] Angle négatif")


class TestGammaBBermComplete:
    """Tests complets pour gamma_b_berm (nouvelle implémentation)"""
    
    def test_no_berm(self):
        """Test sans berme"""
        gamma_b = reduction_factors.gamma_b_berm(3.0, 2.5, 0, 0, 1.0)
        assert gamma_b == 1.0
        print("[OK] Sans berme")
    
    def test_submerged_berm_narrow(self):
        """Test berme submergée étroite"""
        gamma_b = reduction_factors.gamma_b_berm(3.0, 2.5, 3.0, -0.5, 0.5)
        assert gamma_b == 1.0  # Trop étroite
        print(f"[OK] Berme submergée étroite: {gamma_b:.3f}")
    
    def test_submerged_berm_wide(self):
        """Test berme submergée large"""
        gamma_b = reduction_factors.gamma_b_berm(3.0, 2.5, 20.0, -0.5, 0.5)
        assert gamma_b < 1.0
        assert gamma_b >= 0.6
        print(f"[OK] Berme submergée large: {gamma_b:.3f}")
    
    def test_submerged_berm_deep(self):
        """Test berme profondément submergée"""
        gamma_b_shallow = reduction_factors.gamma_b_berm(3.0, 2.5, 20.0, -0.5, 0.5)
        gamma_b_deep = reduction_factors.gamma_b_berm(3.0, 2.5, 20.0, -4.0, 0.5)
        assert gamma_b_deep > gamma_b_shallow  # Moins d'effet en profondeur
        print(f"[OK] Profondeur: peu profond={gamma_b_shallow:.3f}, profond={gamma_b_deep:.3f}")
    
    def test_emerged_berm_low(self):
        """Test berme émergée basse"""
        gamma_b = reduction_factors.gamma_b_berm(3.0, 2.5, 20.0, 0.3, 0.5)
        assert gamma_b < 1.0
        assert gamma_b >= 0.6
        print(f"[OK] Berme émergée basse: {gamma_b:.3f}")
    
    def test_emerged_berm_high(self):
        """Test berme émergée haute"""
        gamma_b = reduction_factors.gamma_b_berm(3.0, 2.5, 20.0, 2.0, 0.5)
        assert gamma_b > 0.8  # Moins d'effet si haute
        print(f"[OK] Berme émergée haute: {gamma_b:.3f}")
    
    def test_berm_too_high(self):
        """Test berme au-dessus de la zone active"""
        gamma_b = reduction_factors.gamma_b_berm(3.0, 2.5, 20.0, 2.5, 0.5)
        assert gamma_b == 1.0  # Pas d'effet
        print("[OK] Berme trop haute")
    
    def test_roughness_effect(self):
        """Test effet de la rugosité"""
        gamma_smooth = reduction_factors.gamma_b_berm(3.0, 2.5, 20.0, 0.3, 1.0)
        gamma_rough = reduction_factors.gamma_b_berm(3.0, 2.5, 20.0, 0.3, 0.5)
        assert gamma_rough < gamma_smooth  # Rugosité améliore l'effet
        print(f"[OK] Rugosité: lisse={gamma_smooth:.3f}, rugueux={gamma_rough:.3f}")
    
    def test_width_effect(self):
        """Test effet de la largeur"""
        widths = [1, 5, 10, 20, 30]
        gammas = [reduction_factors.gamma_b_berm(3.0, 2.5, w, -0.5, 0.5) for w in widths]
        
        # Gammas doivent décroître avec largeur
        assert all(gammas[i] >= gammas[i+1] for i in range(len(gammas)-1))
        print(f"[OK] Largeur: {widths} -> gammas décroissants")
    
    def test_all_berm_positions(self):
        """Test toutes les positions de berme"""
        positions = [-3.0, -1.5, -0.8, -0.3, 0.0, 0.5, 1.0, 1.5, 2.0, 2.5]
        gammas = [reduction_factors.gamma_b_berm(3.0, 2.5, 15.0, h, 0.5) for h in positions]
        
        assert all(0.6 <= g <= 1.0 for g in gammas)
        print(f"[OK] Toutes positions testées: {len(positions)} positions")


class TestOtherFactors:
    """Tests pour autres facteurs"""
    
    def test_gamma_v_parapet(self):
        """Test facteur parapet"""
        gamma_none = reduction_factors.gamma_v_vertical_wall(0, 2.5)
        gamma_small = reduction_factors.gamma_v_vertical_wall(0.5, 2.5)
        gamma_large = reduction_factors.gamma_v_vertical_wall(2.0, 2.5)
        
        assert gamma_none == 1.0
        assert gamma_small < gamma_none
        assert gamma_large < gamma_small
        assert gamma_large >= 0.5  # Limite inférieure
        print(f"[OK] Parapet: sans={gamma_none:.2f}, petit={gamma_small:.2f}, grand={gamma_large:.2f}")
    
    def test_gamma_star_composite(self):
        """Test facteur composite"""
        gamma_deep = reduction_factors.gamma_star_composite(8.0, 10.0, 2.5)
        gamma_shallow = reduction_factors.gamma_star_composite(1.0, 10.0, 2.5)
        
        assert gamma_deep == 1.0
        assert gamma_shallow < 1.0
        print(f"[OK] Composite: profond={gamma_deep:.2f}, peu profond={gamma_shallow:.2f}")
    
    def test_gamma_h_water_depth(self):
        """Test facteur profondeur"""
        gamma_deep = reduction_factors.gamma_h_water_depth(50.0, 2.5, 6.0)
        gamma_shallow = reduction_factors.gamma_h_water_depth(5.0, 2.5, 6.0)
        
        assert gamma_deep == 1.0
        assert gamma_shallow < 1.0
        print(f"[OK] Profondeur: profond={gamma_deep:.2f}, peu profond={gamma_shallow:.2f}")
    
    def test_gamma_cf_wind(self):
        """Test facteur vent"""
        gamma_calm = reduction_factors.gamma_cf_wind(5.0, 2.5, 6.0)
        gamma_strong = reduction_factors.gamma_cf_wind(20.0, 2.5, 6.0)
        
        assert gamma_calm >= 1.0  # Peut être légèrement > 1.0
        assert gamma_strong > 1.0
        assert gamma_strong <= 1.5  # Limite supérieure
        print(f"[OK] Vent: calme={gamma_calm:.3f}, fort={gamma_strong:.2f}")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS COMPLETS REDUCTION_FACTORS")
    print("="*70 + "\n")
    
    test_classes = [
        TestGammaFRoughness(),
        TestGammaBetaObliquity(),
        TestGammaBBermComplete(),
        TestOtherFactors()
    ]
    
    failed = 0
    passed = 0
    
    for test_class in test_classes:
        print(f"\n>>> {test_class.__class__.__name__}")
        for method_name in dir(test_class):
            if method_name.startswith('test_'):
                try:
                    method = getattr(test_class, method_name)
                    method()
                    passed += 1
                except AssertionError as e:
                    print(f"[FAIL] {method_name}: {e}")
                    failed += 1
                except Exception as e:
                    print(f"[ERROR] {method_name}: {e}")
                    failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTATS: {passed} tests reussis, {failed} tests echoues")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

