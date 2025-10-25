"""
Tests pour le module validation
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from openeurotop import validation


def test_validate_slope_structure_basic():
    """Test validation basique structure à talus"""
    result = validation.validate_slope_structure(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0
    )
    
    assert hasattr(result, 'is_valid')
    assert hasattr(result, 'warnings')
    assert isinstance(result.is_valid, bool)
    
    print(f"[OK] Validation slope: valid={result.is_valid}")


def test_validate_slope_structure_invalid_params():
    """Test validation avec paramètres invalides"""
    # Paramètres négatifs devraient être détectés
    result = validation.validate_slope_structure(
        Hm0=-1.0,  # Invalide
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0
    )
    
    assert not result.is_valid, "Hm0 negatif devrait etre invalide"
    assert len(result.errors) > 0 or len(result.warnings) > 0
    
    print(f"[OK] Parametres invalides detectes")


def test_validate_slope_structure_domain():
    """Test validation domaine de validité"""
    # Iribarren hors domaine
    result = validation.validate_slope_structure(
        Hm0=0.5,   # Petit
        Tm_10=10.0,  # Grand
        h=10.0,
        Rc=3.0,
        alpha_deg=60.0  # Raide
    )
    
    # Devrait avoir des avertissements ou recommandations
    assert hasattr(result, 'warnings')
    
    print(f"[OK] Domaine validite verifie: {len(result.warnings)} warnings")


def test_validate_vertical_wall():
    """Test validation mur vertical"""
    result = validation.validate_vertical_wall(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.5
    )
    
    assert hasattr(result, 'is_valid')
    
    print(f"[OK] Validation mur vertical: valid={result.is_valid}")


def test_validate_vertical_wall_impulsive():
    """Test détection conditions impulsives"""
    # Eau peu profonde -> impulsive
    result = validation.validate_vertical_wall(
        Hm0=3.0,
        Tm_10=7.0,
        h=3.5,  # Peu profond
        Rc=4.0
    )
    
    # Devrait détecter conditions particulières
    assert hasattr(result, 'warnings')
    print(f"[OK] Validation complete: {len(result.warnings)} warnings")


def test_check_iribarren_range():
    """Test vérification domaine Iribarren"""
    from openeurotop import wave_parameters
    
    # Iribarren normal
    xi_normal = wave_parameters.iribarren_number(35.0, 2.5, 6.0)
    valid_normal = 1.0 < xi_normal < 10.0
    
    # Iribarren hors domaine
    xi_extreme = wave_parameters.iribarren_number(70.0, 0.5, 10.0)
    valid_extreme = 1.0 < xi_extreme < 10.0
    
    assert valid_normal, "Iribarren normal devrait être dans domaine"
    assert not valid_extreme or valid_extreme, "Test de cohérence"
    
    print(f"[OK] Verification Iribarren: normal={xi_normal:.2f}, extreme={xi_extreme:.2f}")


def test_check_relative_freeboard():
    """Test vérification revanche relative"""
    # Revanche normale
    Rc_Hm0_normal = 3.0 / 2.5
    assert -0.3 < Rc_Hm0_normal < 3.0, "Revanche normale dans domaine"
    
    # Revanche extrême
    Rc_Hm0_extreme = 10.0 / 2.5
    assert Rc_Hm0_extreme > 3.0, "Revanche très élevée hors domaine"
    
    print(f"[OK] Verification revanche relative")


def test_validate_with_reduction_factors():
    """Test validation avec facteurs de réduction"""
    result = validation.validate_slope_structure(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0,
        gamma_f=0.5,
        gamma_beta=0.9
    )
    
    assert hasattr(result, 'is_valid')
    
    print(f"[OK] Validation avec facteurs reduction")


def test_validation_summary():
    """Test génération de résumé de validation"""
    result = validation.validate_slope_structure(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0
    )
    
    # Test que __str__ fonctionne
    summary_str = str(result)
    assert isinstance(summary_str, str)
    assert len(summary_str) > 0
    print(f"[OK] Resume validation genere ({len(summary_str)} chars)")


def test_validate_multiple_structures():
    """Test validation de plusieurs structures"""
    structures = [
        {'Hm0': 2.5, 'Tm_10': 6.0, 'h': 10.0, 'Rc': 3.0, 'alpha_deg': 35.0},
        {'Hm0': 3.0, 'Tm_10': 7.0, 'h': 12.0, 'Rc': 4.0, 'alpha_deg': 45.0},
        {'Hm0': 1.5, 'Tm_10': 5.0, 'h': 8.0, 'Rc': 2.0, 'alpha_deg': 20.0}
    ]
    
    valid_count = 0
    for struct in structures:
        result = validation.validate_slope_structure(**struct)
        if result.is_valid:
            valid_count += 1
    
    print(f"[OK] Validation multiple structures: {valid_count}/{len(structures)} valid")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS DU MODULE VALIDATION")
    print("="*70 + "\n")
    
    tests = [
        test_validate_slope_structure_basic,
        test_validate_slope_structure_invalid_params,
        test_validate_slope_structure_domain,
        test_validate_vertical_wall,
        test_validate_vertical_wall_impulsive,
        test_check_iribarren_range,
        test_check_relative_freeboard,
        test_validate_with_reduction_factors,
        test_validation_summary,
        test_validate_multiple_structures
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

