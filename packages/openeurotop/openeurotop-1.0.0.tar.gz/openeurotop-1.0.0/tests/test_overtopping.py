"""
Tests unitaires pour le module overtopping
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import numpy as np
from openeurotop import overtopping, wave_parameters, reduction_factors


def test_digue_talus_basic():
    """Test basique pour digue à talus"""
    q = overtopping.digue_talus(
        Hm0=2.5,
        Tm_10=6.0,
        h=10.0,
        Rc=3.0,
        alpha_deg=35.0
    )
    
    # Le débit doit être positif et raisonnable
    assert q > 0, "Le débit doit être positif"
    assert q < 1.0, "Le débit semble trop élevé"
    
    print(f"[OK] test_digue_talus_basic: q = {q:.6f} m3/s/m")


def test_digue_talus_revanche_elevee():
    """Test avec revanche élevée (franchissement faible)"""
    q_high_rc = overtopping.digue_talus(
        Hm0=2.0,
        Tm_10=6.0,
        h=10.0,
        Rc=5.0,  # Revanche élevée
        alpha_deg=35.0
    )
    
    q_low_rc = overtopping.digue_talus(
        Hm0=2.0,
        Tm_10=6.0,
        h=10.0,
        Rc=1.0,  # Revanche faible
        alpha_deg=35.0
    )
    
    # Revanche élevée doit donner moins de franchissement
    assert q_high_rc < q_low_rc, "Revanche élevée devrait réduire le franchissement"
    
    print(f"[OK] test_digue_talus_revanche_elevee:")
    print(f"    Rc=5m: q = {q_high_rc:.6f} m3/s/m")
    print(f"    Rc=1m: q = {q_low_rc:.6f} m3/s/m")


def test_effet_rugosite():
    """Test de l'effet de la rugosité"""
    # Digue lisse
    q_lisse = overtopping.digue_talus(
        Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0,
        gamma_f=1.0
    )
    
    # Digue rugueuse (enrochement)
    q_rugueux = overtopping.digue_talus(
        Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0,
        gamma_f=0.5
    )
    
    # La rugosité doit réduire le franchissement
    assert q_rugueux < q_lisse, "La rugosité devrait réduire le franchissement"
    
    print(f"[OK] test_effet_rugosite:")
    print(f"    Lisse (gamma_f=1.0): q = {q_lisse:.6f} m3/s/m")
    print(f"    Rugueux (gamma_f=0.5): q = {q_rugueux:.6f} m3/s/m")
    print(f"    Reduction: {(1-q_rugueux/q_lisse)*100:.1f}%")


def test_mur_vertical():
    """Test pour mur vertical"""
    q = overtopping.mur_vertical(
        Hm0=2.0,
        Tm_10=5.5,
        h=8.0,
        Rc=2.5
    )
    
    assert q > 0, "Le débit doit être positif"
    assert q < 1.0, "Le débit semble trop élevé"
    
    print(f"[OK] test_mur_vertical: q = {q:.6f} m3/s/m")


def test_structure_composite():
    """Test pour structure composite"""
    q = overtopping.structure_composite(
        Hm0=2.8,
        Tm_10=6.5,
        h=10.0,
        Rc=5.0,
        alpha_lower_deg=30.0,
        h_transition=2.0
    )
    
    assert q > 0, "Le débit doit être positif"
    
    print(f"[OK] test_structure_composite: q = {q:.6f} m3/s/m")


def test_iribarren_number():
    """Test du calcul du nombre d'Iribarren"""
    xi = wave_parameters.iribarren_number(
        alpha_deg=35.0,
        Hm0=2.5,
        Tm_10=6.0
    )
    
    assert xi > 0, "Le nombre d'Iribarren doit être positif"
    assert 1.0 < xi < 10.0, "Le nombre d'Iribarren semble hors limites normales"
    
    print(f"[OK] test_iribarren_number: xi = {xi:.3f}")


def test_gamma_f_roughness():
    """Test des facteurs de rugosité"""
    gamma_lisse = reduction_factors.gamma_f_roughness("lisse")
    gamma_enrochement = reduction_factors.gamma_f_roughness("enrochement_2couches")
    
    assert gamma_lisse == 1.0, "Revêtement lisse devrait avoir γf = 1.0"
    assert gamma_enrochement < 1.0, "Enrochement devrait avoir γf < 1.0"
    
    print(f"[OK] test_gamma_f_roughness:")
    print(f"    Lisse: gamma_f = {gamma_lisse}")
    print(f"    Enrochement 2 couches: gamma_f = {gamma_enrochement}")


def test_gamma_beta_obliquity():
    """Test du facteur d'obliquité"""
    gamma_0 = reduction_factors.gamma_beta_obliquity(0)
    gamma_30 = reduction_factors.gamma_beta_obliquity(30)
    gamma_60 = reduction_factors.gamma_beta_obliquity(60)
    
    assert gamma_0 == 1.0, "Vagues perpendiculaires: γβ = 1.0"
    assert gamma_30 < 1.0, "Obliquité 30°: γβ < 1.0"
    assert gamma_60 < gamma_30, "Plus d'obliquité = plus de réduction"
    
    print(f"[OK] test_gamma_beta_obliquity:")
    print(f"    beta=0deg:  gamma_beta = {gamma_0:.3f}")
    print(f"    beta=30deg: gamma_beta = {gamma_30:.3f}")
    print(f"    beta=60deg: gamma_beta = {gamma_60:.3f}")


def test_wave_length():
    """Test du calcul de longueur d'onde"""
    T = 6.0
    h = 10.0
    
    L0 = wave_parameters.wave_length_deep_water(T)
    L = wave_parameters.wave_length(T, h)
    
    assert L0 > 0, "Longueur d'onde en eau profonde doit être positive"
    assert L > 0, "Longueur d'onde doit être positive"
    assert L < L0, "Longueur d'onde en profondeur finie < longueur d'onde profonde"
    
    print(f"[OK] test_wave_length:")
    print(f"    L0 = {L0:.2f} m")
    print(f"    L(h={h}m) = {L:.2f} m")


def test_volumes_franchissement():
    """Test du calcul de volumes"""
    q = 0.001  # m³/s/m
    duree = 3.0  # heures
    
    volumes = overtopping.calcul_volumes_franchissement(q, duree)
    
    assert volumes['volume_total_m3_per_m'] > 0
    assert volumes['duree_heures'] == duree
    
    print(f"[OK] test_volumes_franchissement:")
    print(f"    Volume (3h) = {volumes['volume_total_m3_per_m']:.2f} m³/m")
    print(f"    Volume (3h) = {volumes['volume_liters_per_m']:.0f} litres/m")


def test_digue_en_enrochement():
    """Test pour digue en enrochement"""
    q = overtopping.digue_en_enrochement(
        Hm0=3.0,
        Tm_10=7.0,
        h=12.0,
        Rc=4.0,
        alpha_deg=33.7,
        Dn50=1.5,
        n_layers=2
    )
    
    assert q > 0, "Le débit doit être positif"
    
    print(f"[OK] test_digue_en_enrochement: q = {q:.6f} m3/s/m")


def test_coherence_methodes():
    """Test de cohérence entre différentes méthodes"""
    # Paramètres
    Hm0 = 2.5
    Tm_10 = 6.0
    h = 10.0
    Rc = 3.0
    alpha = 35.0
    
    # Méthode 1 : directe
    q1 = overtopping.digue_talus(
        Hm0, Tm_10, h, Rc, alpha,
        gamma_f=0.5
    )
    
    # Méthode 2 : détaillée avec type de revêtement
    result2 = overtopping.digue_talus_detailed(
        Hm0, Tm_10, h, Rc, alpha,
        type_revetement="enrochement_2couches"
    )
    q2 = result2['q']
    
    # Les deux méthodes devraient donner des résultats similaires
    # (même gamma_f = 0.5 pour enrochement 2 couches)
    diff_relative = abs(q1 - q2) / q1
    assert diff_relative < 0.01, "Les deux méthodes devraient donner des résultats similaires"
    
    print(f"[OK] test_coherence_methodes:")
    print(f"    Méthode directe: q = {q1:.6f} m³/s/m")
    print(f"    Méthode détaillée: q = {q2:.6f} m³/s/m")
    print(f"    Différence: {diff_relative*100:.2f}%")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS UNITAIRES - OPENEUROTOP")
    print("="*70 + "\n")
    
    tests = [
        test_digue_talus_basic,
        test_digue_talus_revanche_elevee,
        test_effet_rugosite,
        test_mur_vertical,
        test_structure_composite,
        test_iribarren_number,
        test_gamma_f_roughness,
        test_gamma_beta_obliquity,
        test_wave_length,
        test_volumes_franchissement,
        test_digue_en_enrochement,
        test_coherence_methodes,
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

