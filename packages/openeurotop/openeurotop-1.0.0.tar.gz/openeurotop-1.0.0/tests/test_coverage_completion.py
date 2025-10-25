"""
Tests pour compléter le coverage des lignes manquantes

Ce fichier cible spécifiquement les lignes non couvertes dans :
- wave_parameters.py
- run_up.py
- probabilistic.py
- special_cases.py
- validation.py
- overtopping.py
"""

import numpy as np
import pytest
import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from openeurotop import wave_parameters, run_up, probabilistic, special_cases, validation, overtopping


class TestWaveParametersCompletion:
    """Tests pour compléter wave_parameters.py (54.17% -> 80%+)"""
    
    def test_wave_length_shallow_water_extreme(self):
        """Test longueur d'onde en eau très peu profonde"""
        # Ligne 65, 185-200
        L = wave_parameters.wave_length(T=8.0, h=0.5)  # h très faible
        assert L > 0
        assert L < 8.0 * 9.81 * 8.0 / (2 * np.pi)  # < L0
    
    def test_wave_length_deep_water(self):
        """Test longueur d'onde en eau profonde"""
        T = 10.0
        h = 500.0  # Très profond
        L = wave_parameters.wave_length(T, h)
        
        # En eau profonde: L ≈ g*T²/(2π)
        L0 = 9.81 * T**2 / (2 * np.pi)
        assert abs(L - L0) / L0 < 0.01  # Moins de 1% de différence
    
    def test_wave_steepness_various(self):
        """Test wave steepness diverses conditions"""
        # Lignes 137-141
        s1 = wave_parameters.wave_steepness(Hm0=2.0, Tm_10=6.0)
        s2 = wave_parameters.wave_steepness(Hm0=4.0, Tm_10=8.0)
        s3 = wave_parameters.wave_steepness(Hm0=1.0, Tm_10=4.0)
        
        assert all(s > 0 for s in [s1, s2, s3])
        # Les valeurs doivent être positives et dans des ordres de grandeur raisonnables
        assert 0.01 < s1 < 0.1
        assert 0.01 < s2 < 0.1
        assert 0.01 < s3 < 0.1
    
    def test_breaking_parameter(self):
        """Test paramètre de déferlement"""
        # Ligne 160
        result = wave_parameters.surf_similarity_parameter(
            alpha_deg=30.0, Hm0=2.0, Lm_10=50.0
        )
        assert result > 0
    
    def test_wave_length_iteration_convergence(self):
        """Test convergence itération longueur d'onde"""
        # Lignes 185-200, 221-222
        for h in [1.0, 5.0, 10.0, 20.0, 50.0]:
            for T in [3.0, 6.0, 10.0]:
                L = wave_parameters.wave_length(T, h)
                assert L > 0
                assert not np.isnan(L)
                assert not np.isinf(L)


class TestRunUpCompletion:
    """Tests pour compléter run_up.py (57.50% -> 75%+)"""
    
    def test_run_up_extreme_slope(self):
        """Test run-up pente extrême"""
        # Lignes 214-220
        # Pente très raide
        Ru = run_up.run_up_2percent_smooth_slope(
            Hm0=2.0, Tm_10=6.0, h=10.0, alpha_deg=60.0
        )
        assert Ru > 0
        
        # Pente très douce
        Ru2 = run_up.run_up_2percent_smooth_slope(
            Hm0=2.0, Tm_10=6.0, h=10.0, alpha_deg=10.0
        )
        assert Ru2 > 0
    
    def test_run_up_with_roughness_extreme(self):
        """Test run-up avec rugosité extrême"""
        # Lignes 261-288
        # Très rugueux
        Ru1 = run_up.run_up_2percent_rough_slope(
            Hm0=2.0, Tm_10=6.0, h=10.0, alpha_deg=35.0, gamma_f=0.3
        )
        
        # Lisse
        Ru2 = run_up.run_up_2percent_rough_slope(
            Hm0=2.0, Tm_10=6.0, h=10.0, alpha_deg=35.0, gamma_f=1.0
        )
        
        assert Ru1 < Ru2  # Plus rugueux => moins de run-up
    
    def test_run_up_detailed_all_params(self):
        """Test run-up détaillé avec tous les paramètres"""
        # Lignes 320-338
        result = run_up.run_up_detailed(
            Hm0=2.5, Tm_10=6.5, h=10.0, alpha_deg=35.0,
            gamma_f=0.7, gamma_beta=0.9
        )
        
        assert 'Ru_2percent' in result
        assert 'xi_m_10' in result
        assert 'regime' in result
        assert result['Ru_2percent'] > 0
    
    def test_run_down_various_conditions(self):
        """Test run-down diverses conditions"""
        # Lignes 375-391, 481
        for alpha in [20.0, 30.0, 45.0]:
            for Hm0 in [1.0, 2.0, 3.0]:
                Rd = run_up.run_down(
                    Hm0=Hm0, Tm_10=6.0, h=10.0, alpha_deg=alpha
                )
                assert Rd < 0  # Run-down est négatif
                assert abs(Rd) > 0


class TestProbabilisticCompletion:
    """Tests pour compléter probabilistic.py (60.81% -> 75%+)"""
    
    def test_weibull_extreme_params(self):
        """Test Weibull avec paramètres extrêmes"""
        # Lignes 112, 149-150
        # q très faible
        result1 = probabilistic.weibull_distribution_overtopping(
            q_mean=1e-8, N_waves=1000
        )
        assert 'Pr' in result1
        assert 'a' in result1
        assert 'b' in result1
        
        # q très élevé
        result2 = probabilistic.weibull_distribution_overtopping(
            q_mean=1.0, N_waves=500
        )
        assert result2['Pr'] >= 0
    
    def test_volume_exceedance_various(self):
        """Test volume exceedance diverses conditions"""
        # Lignes 212-232
        for V_limit in [0.01, 0.1, 1.0]:
            for q_mean in [1e-5, 1e-3, 1e-1]:
                result = probabilistic.volume_exceedance_weibull(
                    q_mean=q_mean, N_waves=1000, V_limit=V_limit, storm_duration=3600
                )
                assert 0 <= result['Pv'] <= 1
    
    def test_monte_carlo_large_sample(self):
        """Test Monte Carlo avec grand échantillon"""
        # Lignes 341-355
        result = probabilistic.monte_carlo_overtopping(
            Hm0_mean=2.5, Hm0_std=0.3,
            Tm_10_mean=6.0, Tm_10_std=0.5,
            h=10.0, Rc=3.0, alpha_deg=35.0,
            n_simulations=100  # Réduit pour rapidité
        )
        
        assert 'q_mean' in result
        assert 'q_std' in result
        assert 'q_p50' in result
        assert result['q_mean'] > 0
    
    def test_design_overtopping_extreme(self):
        """Test design overtopping conditions extrêmes"""
        # Lignes 393-406
        result = probabilistic.design_overtopping_rate(
            Hm0=4.0, Tm_10=8.0, h=15.0, Rc=1.0, alpha_deg=25.0,
            target_prob=0.01, N_waves=3000
        )
        
        assert 'q_design' in result
        assert 'q_mean' in result
        assert result['q_design'] > result['q_mean']


class TestSpecialCasesCompletion:
    """Tests pour compléter special_cases.py (65.25% -> 80%+)"""
    
    def test_multi_slope_edge_cases(self):
        """Test multi-slope cas limites"""
        # Lignes 99-100, 143, 152
        # Deux sections identiques
        result1 = special_cases.multi_slope_structure(
            Hm0=2.0, Tm_10=6.0, h=10.0,
            sections=[
                {'alpha_deg': 30.0, 'length': 20.0, 'gamma_f': 1.0},
                {'alpha_deg': 30.0, 'length': 20.0, 'gamma_f': 1.0}
            ],
            Rc=3.0
        )
        assert 'q' in result1
        
        # Pentes très différentes
        result2 = special_cases.multi_slope_structure(
            Hm0=2.0, Tm_10=6.0, h=10.0,
            sections=[
                {'alpha_deg': 10.0, 'length': 30.0, 'gamma_f': 1.0},
                {'alpha_deg': 60.0, 'length': 10.0, 'gamma_f': 0.5}
            ],
            Rc=2.0
        )
        assert result2['q'] > 0
    
    def test_very_gentle_slope_extreme(self):
        """Test pente très douce extrême"""
        # Lignes 188, 244, 247
        result = special_cases.very_gentle_slope(
            Hm0=3.0, Tm_10=7.0, h=12.0, Rc=2.0, alpha_deg=5.0
        )
        
        assert result['q'] > 0
        assert 'warning' in result
    
    def test_very_steep_slope_extreme(self):
        """Test pente très raide extrême"""
        # Lignes 300, 304
        result = special_cases.very_steep_slope(
            Hm0=2.0, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=75.0
        )
        
        assert result['q'] > 0
    
    def test_stepped_revetment_various(self):
        """Test stepped revetment variations"""
        # Lignes 346-360
        for n_steps in [2, 5, 10]:
            for step_height in [0.2, 0.5, 1.0]:
                result = special_cases.stepped_revetment(
                    Hm0=2.0, Tm_10=6.0, h=10.0, Rc=3.0,
                    alpha_deg=35.0, n_steps=n_steps, step_height=step_height
                )
                assert result['q'] > 0
    
    def test_overhanging_wall_extreme(self):
        """Test overhanging wall conditions extrêmes"""
        # Lignes 401-438
        # Surplomb important
        result1 = special_cases.overhanging_wall(
            Hm0=3.0, Tm_10=7.0, h=12.0, Rc=2.0,
            overhang_length=2.0, overhang_angle_deg=45.0
        )
        assert result1['q'] > 0
        
        # Surplomb faible
        result2 = special_cases.overhanging_wall(
            Hm0=2.0, Tm_10=6.0, h=10.0, Rc=3.0,
            overhang_length=0.5, overhang_angle_deg=30.0
        )
        assert result2['q'] > 0
    
    def test_shallow_water_various_depths(self):
        """Test shallow water check diverses profondeurs"""
        # Lignes 469-470, 472, 476, 478, 483, 485, 490, 495, 497
        for h in [1.0, 2.0, 5.0, 10.0, 20.0]:
            for Hm0 in [0.5, 1.0, 2.0, 3.0]:
                if Hm0 < h:  # Condition physique
                    result = special_cases.shallow_water_check(Hm0=Hm0, h=h)
                    assert 'is_shallow' in result
                    assert 'h_Hm0' in result
    
    def test_extreme_conditions_various(self):
        """Test extreme conditions check"""
        for Hm0 in [0.5, 3.0, 6.0]:
            for Rc in [-2.0, 0.0, 5.0]:
                result = special_cases.extreme_conditions_check(
                    Hm0=Hm0, Rc=Rc, alpha_deg=30.0
                )
                assert 'is_extreme' in result


class TestValidationCompletion:
    """Tests pour compléter validation.py (65.36% -> 75%+)"""
    
    def test_validate_slope_extreme_params(self):
        """Test validation pente paramètres extrêmes"""
        # Lignes 71, 195, 200, 235
        # Hm0 très élevé
        result1 = validation.validate_slope_structure(
            Hm0=6.0, Tm_10=10.0, h=20.0, Rc=8.0, alpha_deg=35.0
        )
        assert result1.is_valid
        
        # Rc très négatif
        result2 = validation.validate_slope_structure(
            Hm0=3.0, Tm_10=7.0, h=12.0, Rc=-3.0, alpha_deg=30.0
        )
        assert result2.warnings or not result2.is_valid
        
        # Pente très raide
        result3 = validation.validate_slope_structure(
            Hm0=2.0, Tm_10=6.0, h=10.0, Rc=2.0, alpha_deg=70.0
        )
        assert len(result3.warnings) > 0
    
    def test_validate_vertical_wall_extreme(self):
        """Test validation mur vertical extrême"""
        # Lignes 250-254, 307, 312-316, 326
        # Eau très profonde
        result1 = validation.validate_vertical_wall(
            Hm0=4.0, Tm_10=8.0, h=50.0, Rc=5.0
        )
        assert result1.is_valid
        
        # Eau très peu profonde
        result2 = validation.validate_vertical_wall(
            Hm0=2.0, Tm_10=6.0, h=2.0, Rc=3.0
        )
        assert len(result2.warnings) > 0
        
        # Rc très élevé
        result3 = validation.validate_vertical_wall(
            Hm0=2.0, Tm_10=6.0, h=10.0, Rc=10.0
        )
        assert len(result3.warnings) > 0
    
    def test_check_iribarren_extreme_ranges(self):
        """Test Iribarren ranges extrêmes"""
        # Lignes 359-366
        # ξ très faible (déferlement plongeant)
        result1 = validation.check_iribarren_range(xi=0.5)
        assert result1['regime'] == 'plunging'
        
        # ξ très élevé (surging)
        result2 = validation.check_iribarren_range(xi=5.0)
        assert result2['regime'] == 'surging'
        
        # ξ intermédiaire
        result3 = validation.check_iribarren_range(xi=2.5)
        assert 'regime' in result3
    
    def test_check_relative_freeboard_extreme(self):
        """Test relative freeboard extrême"""
        # Lignes 402-433
        # Rc/Hm0 très élevé
        result1 = validation.check_relative_freeboard(Rc=10.0, Hm0=1.0)
        assert result1['Rc_Hm0'] == 10.0
        assert len(result1['warnings']) > 0
        
        # Rc/Hm0 négatif
        result2 = validation.check_relative_freeboard(Rc=-2.0, Hm0=2.0)
        assert result2['Rc_Hm0'] < 0
        
        # Rc/Hm0 proche de 0
        result3 = validation.check_relative_freeboard(Rc=0.1, Hm0=2.0)
        assert 0 < result3['Rc_Hm0'] < 1
    
    def test_validate_composite_structure_extreme(self):
        """Test validation structure composite extrême"""
        # Lignes 466-503
        from openeurotop.validation import validate_composite_structure
        
        # Pente inférieure très raide
        result1 = validate_composite_structure(
            Hm0=2.0, Tm_10=6.0, h=10.0,
            alpha_lower_deg=60.0, alpha_upper_deg=45.0,
            h_transition=5.0, Rc=3.0
        )
        assert len(result1.warnings) > 0
        
        # Transition très haute
        result2 = validate_composite_structure(
            Hm0=2.0, Tm_10=6.0, h=10.0,
            alpha_lower_deg=30.0, alpha_upper_deg=45.0,
            h_transition=9.0, Rc=3.0
        )
        assert len(result2.warnings) > 0


class TestOvertoppingCompletion:
    """Tests pour compléter overtopping.py (76% -> 85%+)"""
    
    def test_digue_talus_edge_cases(self):
        """Test digue talus cas limites"""
        # Lignes 85, 89, 91, 93
        # Tous les gamma_f différents
        for gamma_f in [0.3, 0.5, 0.7, 0.9, 1.0]:
            q = overtopping.digue_talus(
                Hm0=2.0, Tm_10=6.0, h=10.0, Rc=3.0,
                alpha_deg=35.0, gamma_f=gamma_f
            )
            assert q > 0
    
    def test_mur_vertical_edge_cases(self):
        """Test mur vertical cas limites"""
        # Lignes 224, 276, 291
        # Conditions impulsives
        q1 = overtopping.mur_vertical(
            Hm0=3.0, Tm_10=7.0, h=5.0, Rc=2.0
        )
        assert q1 > 0
        
        # Conditions non-impulsives
        q2 = overtopping.mur_vertical(
            Hm0=2.0, Tm_10=10.0, h=15.0, Rc=4.0
        )
        assert q2 > 0
    
    def test_structure_composite_edge_cases(self):
        """Test structure composite cas limites"""
        # Lignes 339, 344-346, 392, 402, 446
        q = overtopping.structure_composite(
            Hm0=2.5, Tm_10=6.5, h=12.0,
            alpha_lower_deg=25.0, alpha_upper_deg=50.0,
            h_transition=6.0, Rc=3.0,
            gamma_f_lower=1.0, gamma_f_upper=0.7
        )
        assert q > 0
    
    def test_volumes_franchissement_extreme(self):
        """Test volumes franchissement conditions extrêmes"""
        # Lignes 526-548
        result = overtopping.calcul_volumes_franchissement(
            q=0.1, N_waves=500, storm_duration=7200
        )
        
        assert 'V_total' in result
        assert 'V_mean_per_wave' in result
        assert result['V_total'] > 0


if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

