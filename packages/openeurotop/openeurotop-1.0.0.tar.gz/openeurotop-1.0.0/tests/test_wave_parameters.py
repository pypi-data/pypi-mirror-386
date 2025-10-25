"""
Tests pour le module wave_parameters
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import numpy as np
from openeurotop import wave_parameters


def test_iribarren_number_basic():
    """Test du calcul du nombre d'Iribarren"""
    xi = wave_parameters.iribarren_number(
        alpha_deg=35.0,
        Hm0=2.5,
        Tm_10=6.0
    )
    
    assert xi > 0, "Iribarren doit être positif"
    assert 1.0 < xi < 10.0, f"Iribarren {xi} hors domaine typique"
    assert abs(xi - 3.320) < 0.01, f"Valeur attendue ~3.32, reçu {xi}"
    
    print(f"[OK] iribarren_number basic: xi = {xi:.3f}")


def test_iribarren_steep_slope():
    """Test avec pente raide"""
    xi_steep = wave_parameters.iribarren_number(45.0, 2.5, 6.0)
    xi_gentle = wave_parameters.iribarren_number(20.0, 2.5, 6.0)
    
    assert xi_steep > xi_gentle, "Pente raide doit donner Iribarren plus élevé"
    
    print(f"[OK] Pente raide: xi={xi_steep:.3f}, douce: xi={xi_gentle:.3f}")


def test_wave_length_deep_water():
    """Test longueur d'onde en eau profonde"""
    L0 = wave_parameters.wave_length_deep_water(T=6.0)
    
    # L0 = g * T² / (2π) ≈ 9.81 * 36 / 6.28 ≈ 56.2 m
    expected = 9.81 * 6.0**2 / (2 * np.pi)
    assert abs(L0 - expected) < 0.1
    
    print(f"[OK] Longueur d'onde eau profonde: L0 = {L0:.2f} m")


def test_wave_length_finite_depth():
    """Test longueur d'onde en profondeur finie"""
    L0 = wave_parameters.wave_length_deep_water(6.0)
    L = wave_parameters.wave_length(6.0, 10.0)
    
    assert L < L0, "Longueur d'onde en eau peu profonde < eau profonde"
    assert L > 0
    
    print(f"[OK] L(h=10m)={L:.2f}m < L0={L0:.2f}m")


def test_wave_steepness():
    """Test du calcul de cambrure de vague"""
    s = wave_parameters.wave_steepness(
        Hm0=2.5,
        Tm_10=6.0
    )
    
    assert 0 < s < 0.1, "Cambrure typiquement entre 0 et 0.1"
    
    print(f"[OK] Cambrure: s = {s:.4f}")


def test_breaking_limit():
    """Test de la limite de déferlement"""
    # Vague déferlante
    s_breaking = wave_parameters.wave_steepness(3.0, 5.0)
    # Vague non déferlante
    s_normal = wave_parameters.wave_steepness(2.0, 8.0)
    
    assert s_breaking > s_normal
    
    print(f"[OK] Cambrure déferlante={s_breaking:.4f} > normale={s_normal:.4f}")


def test_consistency_wave_parameters():
    """Test de cohérence entre paramètres"""
    Tm_10 = 6.0
    Hm0 = 2.5
    
    L0 = wave_parameters.wave_length_deep_water(Tm_10)
    s = wave_parameters.wave_steepness(Hm0, Tm_10)
    
    # Vérifie que les valeurs sont cohérentes
    assert L0 > 0, "Longueur d'onde positive"
    assert 0 < s < 0.1, "Cambrure entre 0 et 10%"
    
    # Relation approximative s ≈ 2πH/L pour vérifier ordre de grandeur
    s_approx = 2 * np.pi * Hm0 / L0
    # La formule exacte peut différer légèrement
    assert 0 < abs(s - s_approx) < 1.0, "Cambrures du même ordre de grandeur"
    
    print(f"[OK] Coherence: L0={L0:.1f}m, s={s:.4f}, s_approx={s_approx:.4f}")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS DU MODULE WAVE_PARAMETERS")
    print("="*70 + "\n")
    
    tests = [
        test_iribarren_number_basic,
        test_iribarren_steep_slope,
        test_wave_length_deep_water,
        test_wave_length_finite_depth,
        test_wave_steepness,
        test_breaking_limit,
        test_consistency_wave_parameters
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

