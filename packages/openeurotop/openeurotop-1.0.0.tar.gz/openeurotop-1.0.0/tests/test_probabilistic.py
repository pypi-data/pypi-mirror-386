"""
Tests pour le module probabilistic
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
import numpy as np
from openeurotop import probabilistic


def test_uncertainty_basic():
    """Test calcul d'incertitudes basique"""
    unc = probabilistic.uncertainty_overtopping(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0,
        structure_type='smooth_slope'
    )
    
    assert 'q_mean' in unc
    assert 'q_5' in unc
    assert 'q_95' in unc
    assert unc['q_5'] < unc['q_mean'] < unc['q_95']
    
    print(f"[OK] Incertitudes: q5={unc['q_5']*1000:.1f}, q95={unc['q_95']*1000:.1f} l/s/m")


def test_weibull_distribution():
    """Test distribution de Weibull"""
    result = probabilistic.weibull_distribution_overtopping(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0
    )
    
    assert 'a' in result
    assert 'b' in result
    assert 'V_mean' in result
    assert result['a'] >= 0
    assert result['b'] > 0
    
    print(f"[OK] Weibull: a={result['a']:.3f}, b={result['b']:.3f}")


def test_volume_exceedance():
    """Test probabilité de dépassement de volume"""
    # Paramètres Weibull typiques
    a = 0.1
    b = 0.75
    
    # Plusieurs volumes
    volumes = [0.01, 0.05, 0.1, 0.2]
    probs = [probabilistic.volume_exceedance_weibull(v, a, b) for v in volumes]
    
    # Probabilités doivent décroître
    assert all(probs[i] >= probs[i+1] for i in range(len(probs)-1))
    
    print(f"[OK] Probabilites decroissantes: {[f'{p:.3f}' for p in probs]}")


def test_monte_carlo_basic():
    """Test simulation Monte Carlo basique"""
    results = probabilistic.monte_carlo_overtopping(
        Hm0_mean=2.5,
        Hm0_std=0.3,
        Tm_10_mean=6.0,
        Tm_10_std=0.5,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0,
        n_simulations=50  # Petit nombre pour rapidité
    )
    
    assert 'samples' in results
    assert 'q_mean' in results
    assert 'q_std' in results
    assert len(results['samples']) == 50
    
    print(f"[OK] Monte Carlo: mean={results['q_mean']*1000:.3f} l/s/m, std={results['q_std']*1000:.3f}")


def test_design_overtopping_rate():
    """Test débit de dimensionnement sur période de retour"""
    result = probabilistic.design_overtopping_rate(
        return_period_years=100,
        acceptable_rate_per_year=0.1
    )
    
    # Vérifie que le résultat est un dict
    assert isinstance(result, dict)
    assert 'return_period_years' in result
    assert 'annual_exceedance_probability' in result
    
    print(f"[OK] Design T=100 ans, P={result['annual_exceedance_probability']:.3f}")


def test_overtopping_probability():
    """Test probabilité de franchissement"""
    result = probabilistic.weibull_distribution_overtopping(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0,
        N_waves=1000
    )
    
    assert 'P_ow' in result
    assert 'N_ow' in result
    assert 0 <= result['P_ow'] <= 1.0
    assert result['N_ow'] <= 1000
    
    print(f"[OK] Vagues franchissantes: P_ow={result['P_ow']:.2%}, N_ow={result['N_ow']}")


def test_individual_wave_volumes():
    """Test volumes par vagues individuelles"""
    result = probabilistic.weibull_distribution_overtopping(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0,
        N_waves=100
    )
    
    assert 'V_mean' in result
    assert 'V_01' in result
    assert result['V_01'] >= result['V_mean']
    
    print(f"[OK] Volumes vagues: V_mean={result['V_mean']:.4f}, V_01={result['V_01']:.4f} m3/m")


def test_uncertainty_different_conditions():
    """Test incertitudes pour différentes conditions"""
    # Revanche faible
    unc_low = probabilistic.uncertainty_overtopping(
        2.5, 6.0, 10.0, 1.0, 35.0, 'smooth_slope'
    )
    
    # Revanche élevée
    unc_high = probabilistic.uncertainty_overtopping(
        2.5, 6.0, 10.0, 5.0, 35.0, 'smooth_slope'
    )
    
    # Revanche élevée -> débit plus faible
    assert unc_high['q_mean'] < unc_low['q_mean']
    
    print(f"[OK] Rc eleve reduit franchissement")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS DU MODULE PROBABILISTIC")
    print("="*70 + "\n")
    
    tests = [
        test_uncertainty_basic,
        test_weibull_distribution,
        test_volume_exceedance,
        test_monte_carlo_basic,
        test_design_overtopping_rate,
        test_overtopping_probability,
        test_individual_wave_volumes,
        test_uncertainty_different_conditions
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
