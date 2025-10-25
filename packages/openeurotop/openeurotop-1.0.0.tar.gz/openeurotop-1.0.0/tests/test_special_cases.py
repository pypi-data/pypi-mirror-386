"""
Tests pour le module special_cases
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from openeurotop import special_cases


def test_multi_slope_basic():
    """Test structure multi-pentes basique"""
    slopes = [
        {'alpha_deg': 20, 'h_start': -5, 'h_end': 0},
        {'alpha_deg': 30, 'h_start': 0, 'h_end': 2},
        {'alpha_deg': 45, 'h_start': 2, 'h_end': 5}
    ]
    
    result = special_cases.multi_slope_structure(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=4.0,
        slopes_config=slopes
    )
    
    assert 'q' in result
    assert result['q'] >= 0
    assert 'alpha_equivalent_deg' in result
    
    print(f"[OK] Multi-pentes: q={result['q']*1000:.3f} l/s/m, alpha_eq={result['alpha_equivalent_deg']:.1f}deg")


def test_very_gentle_slope():
    """Test pente très douce (<10°)"""
    q = special_cases.very_gentle_slope(
        Hm0=2.0,
        Tm_10=5.5,
        h=8.0,
        Rc=2.0,
        alpha_deg=8.0
    )
    
    assert q >= 0
    
    print(f"[OK] Pente tres douce (8deg): q={q*1000:.3f} l/s/m")


def test_very_steep_slope():
    """Test pente très raide (>60°)"""
    q = special_cases.very_steep_slope(
        Hm0=3.0,
        Tm_10=7.0,
        h=12.0,
        Rc=5.0,
        alpha_deg=70.0
    )
    
    assert q >= 0
    
    print(f"[OK] Pente tres raide (70deg): q={q*1000:.3f} l/s/m")


def test_stepped_revetment():
    """Test revêtement en escalier"""
    result = special_cases.stepped_revetment(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_avg_deg=35.0,
        step_height=0.3,
        step_width=0.5,
        n_steps=10
    )
    
    assert 'q' in result
    assert result['q'] >= 0
    
    print(f"[OK] Revetement escalier: q={result['q']*1000:.3f} l/s/m")


def test_overhanging_wall():
    """Test mur avec surplomb"""
    result = special_cases.overhanging_wall(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.5,
        overhang_length=0.5
    )
    
    # Résultat peut être dict ou nombre
    if isinstance(result, dict):
        assert 'q' in result
        q = result['q']
    else:
        q = result
    
    assert q >= 0
    
    print(f"[OK] Mur surplomb: q={q*1000:.3f} l/s/m")


def test_shallow_water_check():
    """Test vérification condition eau peu profonde"""
    from openeurotop import overtopping
    
    # Eau peu profonde
    Hm0 = 3.0
    h = 4.0
    h_Hm0 = h / Hm0
    
    # Calcul franchissement
    q = overtopping.digue_talus(Hm0, 7.0, h, 3.0, 30.0)
    
    assert q >= 0
    assert h_Hm0 < 2.0  # Condition peu profonde
    
    print(f"[OK] Eau peu profonde: h/Hm0={h_Hm0:.2f}, q={q*1000:.3f} l/s/m")


def test_extreme_conditions_check():
    """Test vérification conditions extrêmes"""
    check = special_cases.extreme_conditions_check(
        Hm0=6.5,
        Tm_10=11.0,
        h=20.0,
        Rc=8.0,
        alpha_deg=38.7
    )
    
    assert 'xi' in check
    assert 'warnings' in check
    
    print(f"[OK] Verification extreme: xi={check['xi']:.2f}, {len(check['warnings'])} warnings")


def test_multi_slope_two_sections():
    """Test multi-pentes simple (2 sections)"""
    slopes = [
        {'alpha_deg': 25, 'h_start': -3, 'h_end': 1},
        {'alpha_deg': 35, 'h_start': 1, 'h_end': 4}
    ]
    result = special_cases.multi_slope_structure(
        2.5, 6.0, 10.0, 3.0, slopes
    )
    
    assert result['q'] >= 0
    assert 20 < result['alpha_equivalent_deg'] < 40
    
    print(f"[OK] 2 pentes: alpha_eq={result['alpha_equivalent_deg']:.1f}deg")


def test_slope_limits():
    """Test limites de pentes"""
    # Pente minimale
    q_min = special_cases.very_gentle_slope(2.0, 5.5, 8.0, 2.0, 5.0)
    
    # Pente maximale
    q_max = special_cases.very_steep_slope(3.0, 7.0, 12.0, 5.0, 85.0)
    
    assert q_min >= 0
    assert q_max >= 0
    
    print(f"[OK] Limites pentes: min={q_min*1000:.3f}, max={q_max*1000:.3f} l/s/m")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS DU MODULE SPECIAL_CASES")
    print("="*70 + "\n")
    
    tests = [
        test_multi_slope_basic,
        test_very_gentle_slope,
        test_very_steep_slope,
        test_stepped_revetment,
        test_overhanging_wall,
        test_shallow_water_check,
        test_extreme_conditions_check,
        test_multi_slope_two_sections,
        test_slope_limits
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
