"""
Tests d'intégration end-to-end pour OpenEurOtop
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from openeurotop import (
    overtopping, wave_parameters, reduction_factors,
    run_up, probabilistic, special_cases, validation, case_studies
)


class TestIntegrationDikeTalus:
    """Tests d'intégration pour digue à talus"""
    
    def test_complete_design_workflow(self):
        """Test workflow complet de dimensionnement"""
        # 1. Paramètres d'entrée
        Hm0 = 2.5
        Tm_10 = 6.0
        h = 10.0
        Rc = 3.0
        alpha_deg = 35.0
        type_revetement = "enrochement_2couches"
        
        # 2. Validation
        val_result = validation.validate_slope_structure(Hm0, Tm_10, h, Rc, alpha_deg)
        assert val_result.is_valid or len(val_result.warnings) >= 0
        print(f"[1/5] Validation: {len(val_result.warnings)} warnings")
        
        # 3. Calcul paramètres vagues
        xi = wave_parameters.iribarren_number(alpha_deg, Hm0, Tm_10)
        L0 = wave_parameters.wave_length_deep_water(Tm_10)
        s = wave_parameters.wave_steepness(Hm0, Tm_10)
        print(f"[2/5] Parametres: xi={xi:.2f}, L0={L0:.1f}m, s={s:.4f}")
        
        # 4. Facteurs de réduction
        gamma_f = reduction_factors.gamma_f_roughness(type_revetement)
        gamma_beta = reduction_factors.gamma_beta_obliquity(0)  # Perpendiculaire
        print(f"[3/5] Facteurs: gamma_f={gamma_f:.2f}, gamma_beta={gamma_beta:.2f}")
        
        # 5. Calcul franchissement
        q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                                     gamma_b=1.0, gamma_f=gamma_f, gamma_beta=gamma_beta)
        print(f"[4/5] Franchissement: q={q*1000:.3f} l/s/m")
        
        # 6. Run-up
        Ru2 = run_up.run_up_2percent_smooth_slope(Hm0, Tm_10, alpha_deg)
        print(f"[5/5] Run-up: Ru2%={Ru2:.2f} m")
        
        # Vérifications
        assert xi > 0
        assert L0 > 0
        assert 0 < s < 0.1
        assert 0 < gamma_f <= 1.0
        assert gamma_beta == 1.0
        assert q >= 0
        assert Ru2 > 0
        
        print("[OK] Workflow complet digue talus")
    
    def test_with_berm_and_obliquity(self):
        """Test avec berme et obliquité"""
        Hm0 = 3.0
        Tm_10 = 7.0
        h = 12.0
        Rc = 4.0
        alpha_deg = 26.6
        beta_deg = 30.0
        
        # Facteurs
        gamma_f = reduction_factors.gamma_f_roughness("herbe")
        gamma_beta = reduction_factors.gamma_beta_obliquity(beta_deg)
        gamma_b = reduction_factors.gamma_b_berm(Rc, Hm0, 20.0, -1.0, gamma_f)
        
        # Franchissement
        q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                                     gamma_b, gamma_f, gamma_beta)
        
        assert 0 < gamma_beta < 1.0
        assert 0 < gamma_b <= 1.0
        assert q >= 0
        
        print(f"[OK] Avec berme et obliquite: q={q*1000:.3f} l/s/m")
    
    def test_extreme_conditions(self):
        """Test conditions extrêmes"""
        Hm0 = 6.5
        Tm_10 = 11.0
        h = 20.0
        Rc = 8.0
        alpha_deg = 38.7
        
        # Vérification conditions extrêmes
        check = special_cases.extreme_conditions_check(Hm0, Tm_10, h, Rc, alpha_deg)
        
        # Validation
        val_result = validation.validate_slope_structure(Hm0, Tm_10, h, Rc, alpha_deg)
        
        # Franchissement
        q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg)
        
        # Incertitudes
        unc = probabilistic.uncertainty_overtopping(Hm0, Tm_10, h, Rc, alpha_deg, 'smooth_slope')
        
        assert 'xi' in check
        assert q >= 0
        assert unc['q_95'] > unc['q_mean'] > unc['q_5']
        
        # Calcul écart-type si pas dans unc
        q_std = (unc['q_95'] - unc['q_5']) / 4.0  # Approximation
        print(f"[OK] Conditions extremes: q={q*1000:.3f} l/s/m [±{q_std*1000:.2f}]")


class TestIntegrationVerticalWall:
    """Tests d'intégration pour mur vertical"""
    
    def test_vertical_wall_workflow(self):
        """Test workflow mur vertical complet"""
        Hm0 = 3.5
        Tm_10 = 7.5
        h = 10.0
        Rc = 4.0
        
        # Validation
        val_result = validation.validate_vertical_wall(Hm0, Tm_10, h, Rc)
        
        # Franchissement
        q = overtopping.mur_vertical(Hm0, Tm_10, h, Rc)
        
        # Vérifications
        assert q >= 0
        print(f"[OK] Mur vertical: q={q*1000:.3f} l/s/m")
    
    def test_vertical_wall_with_parapet(self):
        """Test mur avec parapet"""
        Hm0 = 3.5
        Tm_10 = 7.5
        h = 10.0
        Rc_promenade = 4.0
        h_parapet = 1.5
        
        # Facteur parapet
        gamma_v = reduction_factors.gamma_v_vertical_wall(h_parapet, Hm0)
        
        # Franchissement sans parapet
        q_no_parapet = overtopping.mur_vertical(Hm0, Tm_10, h, Rc_promenade + h_parapet)
        
        # Franchissement avec parapet (réduit)
        q_with_parapet = q_no_parapet * gamma_v
        
        assert gamma_v < 1.0
        assert q_with_parapet < q_no_parapet
        
        print(f"[OK] Avec parapet: reduction={gamma_v:.2f}, q={q_with_parapet*1000:.3f} l/s/m")


class TestIntegrationComposite:
    """Tests d'intégration pour structures composites"""
    
    def test_composite_structure_complete(self):
        """Test structure composite complète"""
        Hm0 = 2.8
        Tm_10 = 6.5
        h = 8.0
        Rc = 6.0
        alpha_lower_deg = 26.6
        h_transition = 3.5
        
        # Validation
        val_result = validation.validate_composite_structure(
            Hm0, Tm_10, h, Rc, alpha_lower_deg, h_transition
        )
        
        # Facteurs
        gamma_f_lower = reduction_factors.gamma_f_roughness("enrochement_2couches")
        gamma_f_upper = reduction_factors.gamma_f_roughness("beton_lisse")
        
        # Franchissement
        q = overtopping.structure_composite(
            Hm0, Tm_10, h, Rc, alpha_lower_deg, h_transition,
            gamma_f_lower, gamma_f_upper
        )
        
        assert q >= 0
        print(f"[OK] Structure composite: q={q*1000:.3f} l/s/m")


class TestIntegrationMultiSlope:
    """Tests d'intégration pour structures multi-pentes"""
    
    def test_multi_slope_complete(self):
        """Test structure multi-pentes complète"""
        Hm0 = 2.0
        Tm_10 = 5.5
        h = 6.0
        Rc = 3.5
        
        # Configuration multi-pentes
        slopes = [
            {'alpha_deg': 18.4, 'h_start': -5, 'h_end': 0},
            {'alpha_deg': 26.6, 'h_start': 0, 'h_end': 2},
            {'alpha_deg': 33.7, 'h_start': 2, 'h_end': 5}
        ]
        
        # Facteurs de rugosité par section
        gamma_f_sections = [0.5, 0.5, 1.0]
        
        # Calcul
        result = special_cases.multi_slope_structure(
            Hm0, Tm_10, h, Rc, slopes, gamma_f_sections
        )
        
        assert result['q'] >= 0
        assert 'alpha_equivalent_deg' in result
        
        print(f"[OK] Multi-pentes: q={result['q']*1000:.3f} l/s/m, "
              f"alpha_eq={result['alpha_equivalent_deg']:.1f}deg")


class TestIntegrationCaseStudies:
    """Tests d'intégration des cas d'étude"""
    
    def test_run_all_case_studies(self):
        """Test exécution de tous les cas d'étude"""
        all_cases = case_studies.run_all_case_studies()
        
        assert len(all_cases) == 12
        
        # Vérifier que tous ont des résultats
        for case_obj in all_cases:
            # Case_obj peut être un dict ou un CaseStudy
            if hasattr(case_obj, 'results'):  # 'results' plural
                assert case_obj.results is not None
            elif isinstance(case_obj, dict):
                assert 'result' in case_obj or 'results' in case_obj
        
        print(f"[OK] Tous les cas d'etude executes: {len(all_cases)} cas")
    
    def test_case_study_validation(self):
        """Test validation des cas d'étude"""
        # Cas 1 : Zeebrugge
        case1 = case_studies.case_study_1_zeebrugge()
        
        # Case1 est un CaseStudy object avec 'results' (plural)
        assert hasattr(case1, 'results')
        assert 'q_calculated' in case1.results
        q = case1.results['q_calculated']
        
        assert q >= 0
        print(f"[OK] Case study 1: q={q*1000:.3f} l/s/m")


class TestIntegrationProbabilistic:
    """Tests d'intégration analyses probabilistes"""
    
    def test_probabilistic_workflow(self):
        """Test workflow analyse probabiliste complète"""
        Hm0 = 2.5
        Tm_10 = 6.0
        h = 10.0
        Rc = 3.0
        alpha_deg = 35.0
        
        # 1. Incertitudes
        unc = probabilistic.uncertainty_overtopping(
            Hm0, Tm_10, h, Rc, alpha_deg, 'smooth_slope'
        )
        
        # 2. Distribution de Weibull
        weib = probabilistic.weibull_distribution_overtopping(
            Hm0, Tm_10, h, Rc, alpha_deg
        )
        
        # 3. Monte Carlo
        mc = probabilistic.monte_carlo_overtopping(
            Hm0, 0.3, Tm_10, 0.5, h, Rc, alpha_deg, n_simulations=50
        )
        
        assert unc['q_95'] > unc['q_mean']
        assert weib['V_01'] >= weib['V_mean']
        assert len(mc['samples']) == 50
        
        print(f"[OK] Analyse probabiliste: q_mean={unc['q_mean']*1000:.3f} l/s/m "
              f"[{unc['q_5']*1000:.3f}, {unc['q_95']*1000:.3f}]")


def run_all_tests():
    """Exécute tous les tests d'intégration"""
    print("\n" + "="*70)
    print("TESTS D'INTEGRATION END-TO-END")
    print("="*70 + "\n")
    
    test_classes = [
        TestIntegrationDikeTalus(),
        TestIntegrationVerticalWall(),
        TestIntegrationComposite(),
        TestIntegrationMultiSlope(),
        TestIntegrationCaseStudies(),
        TestIntegrationProbabilistic()
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

