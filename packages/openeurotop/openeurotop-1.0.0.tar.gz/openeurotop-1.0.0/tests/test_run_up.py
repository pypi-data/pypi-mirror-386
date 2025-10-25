"""
Tests pour le module run_up
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from openeurotop import run_up, wave_parameters


def test_run_up_2percent_smooth_basic():
    """Test run-up sur pente lisse"""
    Ru2 = run_up.run_up_2percent_smooth_slope(
        Hm0=2.5,
        Tm_10=6.0,
        alpha_deg=35.0
    )
    
    assert Ru2 > 0, "Run-up doit être positif"
    assert Ru2 > 2.5, "Run-up doit être > Hm0 pour pentes raides"
    assert Ru2 < 10.0, "Run-up semble trop élevé"
    
    print(f"[OK] Run-up lisse: Ru2% = {Ru2:.2f} m")


def test_run_up_2percent_rough():
    """Test run-up sur pente rugueuse"""
    Ru2_smooth = run_up.run_up_2percent_smooth_slope(2.5, 6.0, 35.0)
    Ru2_rough = run_up.run_up_2percent_rough_slope(2.5, 6.0, 35.0, gamma_f=0.5)
    
    assert Ru2_rough < Ru2_smooth, "Rugosité réduit le run-up"
    assert Ru2_rough > 0
    
    print(f"[OK] Ru lisse={Ru2_smooth:.2f}m > rugueux={Ru2_rough:.2f}m")


def test_run_up_steep_vs_gentle():
    """Test run-up pente raide vs douce"""
    Ru_steep = run_up.run_up_2percent_smooth_slope(2.5, 6.0, 45.0)
    Ru_gentle = run_up.run_up_2percent_smooth_slope(2.5, 6.0, 20.0)
    
    # Pente raide donne run-up plus élevé
    assert Ru_steep > Ru_gentle
    
    print(f"[OK] Ru pente raide={Ru_steep:.2f}m > douce={Ru_gentle:.2f}m")


def test_run_up_detailed():
    """Test calcul détaillé du run-up"""
    result = run_up.run_up_detailed(
        Hm0=2.5,
        Tm_10=6.0,
        alpha_deg=35.0,
        type_revetement="enrochement_2couches"
    )
    
    assert 'Ru2' in result
    assert 'Ru_mean' in result
    assert result['Ru2'] > result['Ru_mean'], "Ru2% > Ru_mean"
    
    print(f"[OK] Run-up detaille: Ru2%={result['Ru2']:.2f}m, Ru_mean={result['Ru_mean']:.2f}m")


def test_run_down():
    """Test calcul du run-down"""
    Rd2 = run_up.run_down_2percent(
        Hm0=2.5,
        Tm_10=6.0,
        alpha_deg=35.0
    )
    
    assert Rd2 < 0, "Run-down doit être négatif"
    
    print(f"[OK] Run-down: Rd2% = {Rd2:.2f} m")


def test_run_up_with_wave_params():
    """Test avec différents paramètres de vague"""
    results = []
    for Hm0 in [1.5, 2.5, 3.5]:
        Ru = run_up.run_up_2percent_smooth_slope(Hm0, 6.0, 30.0)
        results.append(Ru)
    
    # Run-up croît avec Hm0
    assert all(results[i] < results[i+1] for i in range(len(results)-1))
    
    print(f"[OK] Run-up croissant avec Hm0: {results}")


def test_run_up_different_periods():
    """Test avec différentes périodes"""
    Ru_short = run_up.run_up_2percent_smooth_slope(2.5, 5.0, 30.0)
    Ru_long = run_up.run_up_2percent_smooth_slope(2.5, 8.0, 30.0)
    
    # Période longue -> run-up plus élevé
    assert Ru_long > Ru_short
    
    print(f"[OK] Ru periode longue={Ru_long:.2f}m > courte={Ru_short:.2f}m")


def test_run_up_mean_from_detailed():
    """Test calcul du run-up moyen"""
    result = run_up.run_up_detailed(2.5, 6.0, 35.0, "lisse")
    Ru_mean = result['Ru_mean']
    Ru2 = result['Ru2']
    
    # Ru_mean doit être plus petit que Ru2%
    assert Ru_mean < Ru2
    
    print(f"[OK] Ru_mean={Ru_mean:.2f}m < Ru2%={Ru2:.2f}m")


def test_run_up_iribarren_regimes():
    """Test différents régimes d'Iribarren"""
    # Petit xi (déferlant)
    Ru_breaking = run_up.run_up_2percent_smooth_slope(3.0, 6.0, 20.0)
    
    # Grand xi (non-déferlant)
    Ru_surging = run_up.run_up_2percent_smooth_slope(1.5, 6.0, 50.0)
    
    assert Ru_breaking > 0
    assert Ru_surging > 0
    
    print(f"[OK] Ru deferlant={Ru_breaking:.2f}m, surging={Ru_surging:.2f}m")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS DU MODULE RUN_UP")
    print("="*70 + "\n")
    
    tests = [
        test_run_up_2percent_smooth_basic,
        test_run_up_2percent_rough,
        test_run_up_steep_vs_gentle,
        test_run_up_detailed,
        test_run_down,
        test_run_up_with_wave_params,
        test_run_up_different_periods,
        test_run_up_mean_from_detailed,
        test_run_up_iribarren_regimes
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
