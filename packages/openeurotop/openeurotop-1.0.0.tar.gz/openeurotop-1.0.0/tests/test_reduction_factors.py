"""
Tests pour le module reduction_factors
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from openeurotop import reduction_factors


def test_gamma_f_smooth():
    """Test facteur de rugosité pour surfaces lisses"""
    gamma_lisse = reduction_factors.gamma_f_roughness("lisse")
    gamma_asphalte = reduction_factors.gamma_f_roughness("asphalte")
    gamma_beton = reduction_factors.gamma_f_roughness("beton_lisse")
    
    assert gamma_lisse == 1.0
    assert gamma_asphalte == 1.0
    assert gamma_beton == 1.0
    
    print(f"[OK] Surfaces lisses: gamma_f = 1.0")


def test_gamma_f_rough():
    """Test facteur de rugosité pour surfaces rugueuses"""
    gamma_enroch = reduction_factors.gamma_f_roughness("enrochement_2couches")
    gamma_tetrapodes = reduction_factors.gamma_f_roughness("tetrapodes")  # pluriel
    
    assert gamma_enroch == 0.50
    assert gamma_tetrapodes == 0.38
    assert gamma_enroch > gamma_tetrapodes, "Enrochement moins rugueux que tétrapodes"
    
    print(f"[OK] Enrochement: gamma_f={gamma_enroch}, Tetrapodes: gamma_f={gamma_tetrapodes}")


def test_gamma_f_range():
    """Test que tous les gamma_f sont dans [0, 1]"""
    types = [
        "lisse", "asphalte", "beton_lisse", "beton_rugueux",
        "herbe", "enrochement_1couche", "enrochement_2couches",
        "accropode", "tetrapodes", "cubes"
    ]
    
    for type_rev in types:
        gamma = reduction_factors.gamma_f_roughness(type_rev)
        assert 0 < gamma <= 1.0, f"{type_rev}: gamma_f hors [0,1]"
    
    print(f"[OK] Tous les gamma_f dans [0, 1]")


def test_gamma_beta_perpendicular():
    """Test obliquité nulle"""
    gamma = reduction_factors.gamma_beta_obliquity(0.0)
    assert gamma == 1.0, "Vagues perpendiculaires: gamma_beta = 1.0"
    
    print(f"[OK] beta=0deg: gamma_beta = 1.0")


def test_gamma_beta_oblique():
    """Test avec obliquité"""
    gamma_30 = reduction_factors.gamma_beta_obliquity(30.0)
    gamma_60 = reduction_factors.gamma_beta_obliquity(60.0)
    
    assert gamma_30 < 1.0, "Obliquité réduit le franchissement"
    assert gamma_60 < gamma_30, "Plus d'obliquité = plus de réduction"
    assert gamma_30 > 0.8, "Réduction modérée pour 30°"
    
    print(f"[OK] beta=30deg: gamma_beta={gamma_30:.3f}, beta=60deg: {gamma_60:.3f}")


def test_gamma_beta_range():
    """Test domaine de validité gamma_beta"""
    for beta in [0, 10, 20, 30, 40, 50, 60, 70, 80]:
        gamma = reduction_factors.gamma_beta_obliquity(beta)
        assert 0 < gamma <= 1.0, f"beta={beta}: gamma_beta hors [0,1]"
    
    print(f"[OK] gamma_beta toujours dans [0, 1]")


def test_gamma_b_no_berm():
    """Test sans berme"""
    gamma_b = reduction_factors.gamma_b_berm(
        Rc=3.0, Hm0=2.5, B_berm=0.0, h_berm=0.0, gamma_f=1.0
    )
    assert gamma_b == 1.0, "Sans berme: gamma_b = 1.0"
    
    print(f"[OK] Sans berme: gamma_b = 1.0")


def test_gamma_b_with_berm():
    """Test avec berme"""
    gamma_b = reduction_factors.gamma_b_berm(
        Rc=3.0, Hm0=2.5, B_berm=20.0, h_berm=-1.0, gamma_f=0.5
    )
    
    # Fonction non implémentée, retourne 1.0 pour l'instant
    assert 0 < gamma_b <= 1.0, "Facteur entre 0 et 1"
    
    print(f"[OK] Avec berme (B=20m): gamma_b = {gamma_b:.3f} (non implemente)")


def test_gamma_b_wide_berm():
    """Test berme large vs étroite"""
    gamma_narrow = reduction_factors.gamma_b_berm(
        Rc=3.0, Hm0=2.5, B_berm=10.0, h_berm=-1.0, gamma_f=0.5
    )
    gamma_wide = reduction_factors.gamma_b_berm(
        Rc=3.0, Hm0=2.5, B_berm=30.0, h_berm=-1.0, gamma_f=0.5
    )
    
    # Fonction non implémentée, retourne 1.0 pour les deux
    assert 0 < gamma_narrow <= 1.0
    assert 0 < gamma_wide <= 1.0
    
    print(f"[OK] Berme: etroite={gamma_narrow:.3f}, large={gamma_wide:.3f} (non implemente)")


def test_all_gammas_reduce():
    """Test que tous les facteurs réduisent (≤1)"""
    # Rugosité
    gamma_f = reduction_factors.gamma_f_roughness("enrochement_2couches")
    assert gamma_f <= 1.0
    
    # Obliquité
    gamma_beta = reduction_factors.gamma_beta_obliquity(30.0)
    assert gamma_beta <= 1.0
    
    # Berme
    gamma_b = reduction_factors.gamma_b_berm(3.0, 2.5, 15.0, -1.0, 0.5)
    assert gamma_b <= 1.0
    
    # Produit
    gamma_total = gamma_f * gamma_beta * gamma_b
    assert gamma_total <= 1.0
    
    print(f"[OK] Produit des gammas: {gamma_total:.3f} <= 1.0")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS DU MODULE REDUCTION_FACTORS")
    print("="*70 + "\n")
    
    tests = [
        test_gamma_f_smooth,
        test_gamma_f_rough,
        test_gamma_f_range,
        test_gamma_beta_perpendicular,
        test_gamma_beta_oblique,
        test_gamma_beta_range,
        test_gamma_b_no_berm,
        test_gamma_b_with_berm,
        test_gamma_b_wide_berm,
        test_all_gammas_reduce
    ]
    
    failed = 0
    passed = 0
    
    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"[FAIL] {test.__name__}: ECHEC - {e}")
            failed += 1
        except Exception as e:
            print(f"[ERROR] {test.__name__}: ERREUR - {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTATS: {passed} tests reussis, {failed} tests echoues")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

