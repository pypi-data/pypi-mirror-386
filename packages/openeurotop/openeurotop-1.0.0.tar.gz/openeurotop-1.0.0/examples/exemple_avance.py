"""
Exemples avancés utilisant les nouveaux modules d'OpenEurOtop v0.2.0

Couvre :
- Run-up
- Analyses probabilistes
- Cas spécifiques
- Validation
"""

import sys
sys.path.insert(0, '..')

import numpy as np
from openeurotop import (
    overtopping,
    run_up,
    probabilistic,
    special_cases,
    validation
)


def exemple_run_up():
    """Exemple 1 : Calcul du run-up"""
    print("=" * 70)
    print("EXEMPLE 1 : Calcul du run-up Ru2%")
    print("=" * 70)
    
    # Paramètres
    Hm0 = 2.5
    Tm_10 = 6.0
    alpha = 35.0
    
    print(f"\nParamètres :")
    print(f"  Hm0 = {Hm0} m")
    print(f"  Tm-1,0 = {Tm_10} s")
    print(f"  Pente = {alpha}°")
    
    # Run-up pente lisse
    Ru2_lisse = run_up.run_up_2percent_smooth_slope(Hm0, Tm_10, alpha)
    
    # Run-up pente rugueuse (enrochement)
    Ru2_rugueux = run_up.run_up_2percent_rough_slope(Hm0, Tm_10, alpha, gamma_f=0.5)
    
    # Calcul détaillé
    result = run_up.run_up_detailed(Hm0, Tm_10, alpha, type_revetement="enrochement_2couches")
    
    print(f"\nRésultats :")
    print(f"  Run-up (pente lisse) : Ru2% = {Ru2_lisse:.2f} m")
    print(f"  Run-up (enrochement) : Ru2% = {Ru2_rugueux:.2f} m")
    print(f"  Ru2%/Hm0 = {Ru2_rugueux/Hm0:.2f}")
    print(f"  Run-up moyen = {result['Ru_mean']:.2f} m")
    print(f"  Run-down Rd2% = {result['Rd2']:.2f} m")
    
    # Distribution du run-up
    dist = run_up.run_up_distribution_parameters(Hm0, Tm_10, alpha, gamma_f=0.5)
    print(f"\nDistribution du run-up :")
    print(f"  Paramètre a (Rayleigh) = {dist['a']:.2f} m")
    print(f"  Run-up max (99.9%) = {dist['Ru_max']:.2f} m")
    
    print()


def exemple_analyses_probabilistes():
    """Exemple 2 : Analyses probabilistes"""
    print("=" * 70)
    print("EXEMPLE 2 : Analyses probabilistes et incertitudes")
    print("=" * 70)
    
    # Paramètres
    Hm0 = 2.5
    Tm_10 = 6.0
    h = 10.0
    Rc = 3.0
    alpha = 35.0
    
    print(f"\nParamètres : Hm0={Hm0}m, Rc={Rc}m, α={alpha}°")
    
    # Incertitudes
    unc = probabilistic.uncertainty_overtopping(
        Hm0, Tm_10, h, Rc, alpha,
        structure_type="rough_slope"
    )
    
    print(f"\nIncertitudes (digue rugueuse) :")
    print(f"  Débit moyen : q = {unc['q_mean']*1000:.3f} l/s/m")
    print(f"  Intervalle 90% : [{unc['q_5']*1000:.3f}, {unc['q_95']*1000:.3f}] l/s/m")
    print(f"  Intervalle 95% : [{unc['q_2.5']*1000:.3f}, {unc['q_97.5']*1000:.3f}] l/s/m")
    print(f"  σ_ln(q) = {unc['sigma_ln_q']:.3f}")
    
    # Distribution de Weibull pour volumes individuels
    weibull = probabilistic.weibull_distribution_overtopping(
        Hm0, Tm_10, h, Rc, alpha,
        gamma_f=0.5, N_waves=1000
    )
    
    print(f"\nDistribution de Weibull (volumes par vagues) :")
    print(f"  Paramètres : a={weibull['a']:.4f}, b={weibull['b']:.2f}")
    print(f"  Volume moyen : {weibull['V_mean']:.4f} m³/m")
    print(f"  Volume 0.1% : {weibull['V_01']:.4f} m³/m")
    print(f"  Probabilité de franchissement : {weibull['P_ow']*100:.1f}%")
    print(f"  Vagues franchissantes : {weibull['N_ow']} / 1000")
    
    # Probabilité de défaillance
    q_critical = 0.01  # 10 l/s/m
    Pf = probabilistic.failure_probability_overtopping(
        q_critical, Hm0, Tm_10, h, Rc, alpha, gamma_f=0.5
    )
    
    print(f"\nProbabilité de défaillance :")
    print(f"  Critère : q > {q_critical*1000} l/s/m")
    print(f"  Probabilité : Pf = {Pf*100:.2f}%")
    
    print()


def exemple_multi_pentes():
    """Exemple 3 : Structure à pentes multiples"""
    print("=" * 70)
    print("EXEMPLE 3 : Structure à pentes multiples")
    print("=" * 70)
    
    # Configuration : 3 pentes différentes
    slopes = [
        {'alpha_deg': 20.0, 'h_start': -8, 'h_end': 0},    # Pente douce en bas
        {'alpha_deg': 30.0, 'h_start': 0, 'h_end': 2},      # Pente moyenne
        {'alpha_deg': 40.0, 'h_start': 2, 'h_end': 5}       # Pente raide en haut
    ]
    
    gamma_f_sections = [1.0, 0.9, 0.7]  # Rugosités variables
    
    print(f"\nConfiguration :")
    for i, slope in enumerate(slopes):
        print(f"  Section {i+1} : α={slope['alpha_deg']}°, "
              f"de {slope['h_start']}m à {slope['h_end']}m, γf={gamma_f_sections[i]}")
    
    # Calcul
    result = special_cases.multi_slope_structure(
        Hm0=2.5, Tm_10=6.0, h=10.0, Rc=4.0,
        slopes_config=slopes,
        gamma_f_sections=gamma_f_sections
    )
    
    print(f"\nRésultats :")
    print(f"  Pente équivalente : α_eq = {result['alpha_equivalent_deg']:.1f}°")
    print(f"  Rugosité équivalente : γf_eq = {result['gamma_f_equivalent']:.2f}")
    print(f"  Débit de franchissement : q = {result['q']*1000:.3f} l/s/m")
    print(f"  Longueur active : {result['active_length']:.2f} m")
    
    print()


def exemple_validation():
    """Exemple 4 : Validation et vérifications"""
    print("=" * 70)
    print("EXEMPLE 4 : Validation des paramètres")
    print("=" * 70)
    
    # Cas 1 : Paramètres valides
    print("\nCas 1 : Paramètres dans le domaine de validité")
    print("-" * 70)
    result1 = validation.validate_slope_structure(
        Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0
    )
    print(result1)
    
    # Cas 2 : Revanche trop faible
    print("\nCas 2 : Revanche très faible (Rc/Hm0 < 0.5)")
    print("-" * 70)
    result2 = validation.validate_slope_structure(
        Hm0=3.0, Tm_10=6.0, h=10.0, Rc=1.0, alpha_deg=35.0
    )
    print(result2)
    
    # Cas 3 : Pente très douce
    print("\nCas 3 : Pente très douce (α < 10°)")
    print("-" * 70)
    result3 = validation.validate_slope_structure(
        Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=8.0
    )
    print(result3)
    
    print()


def exemple_cas_extreme():
    """Exemple 5 : Vérification des conditions extrêmes"""
    print("=" * 70)
    print("EXEMPLE 5 : Vérification des conditions extrêmes")
    print("=" * 70)
    
    # Paramètres à vérifier
    Hm0 = 4.5
    Tm_10 = 8.0
    h = 8.0
    Rc = 1.5
    alpha = 25.0
    
    print(f"\nParamètres à vérifier :")
    print(f"  Hm0 = {Hm0} m")
    print(f"  Tm-1,0 = {Tm_10} s")
    print(f"  h = {h} m")
    print(f"  Rc = {Rc} m")
    print(f"  α = {alpha}°")
    
    # Vérification
    check = special_cases.extreme_conditions_check(Hm0, Tm_10, h, Rc, alpha)
    
    print(f"\nRésultats de vérification :")
    print(f"  Valide : {'✓ OUI' if check['valid'] else '✗ NON'}")
    print(f"  Rc/Hm0 = {check['Rc_Hm0']:.2f}")
    print(f"  ξ = {check['xi']:.2f}")
    print(f"  h/Hm0 = {check['h_Hm0']:.2f}")
    print(f"  s0 = {check['s0']:.4f}")
    
    if check['warnings']:
        print(f"\n  Avertissements :")
        for warn in check['warnings']:
            print(f"    • {warn}")
    
    print()


def exemple_rapport_complet():
    """Exemple 6 : Génération d'un rapport complet"""
    print("=" * 70)
    print("EXEMPLE 6 : Rapport de validation complet")
    print("=" * 70)
    
    # Paramètres
    params = {
        'Hm0': 2.5,
        'Tm_10': 6.0,
        'h': 10.0,
        'Rc': 3.0,
        'alpha_deg': 35.0,
        'gamma_f': 0.5
    }
    
    # Calculs
    q = overtopping.digue_talus(**params)
    Ru2 = run_up.run_up_2percent_rough_slope(
        params['Hm0'], params['Tm_10'], params['alpha_deg'], params['gamma_f']
    )
    
    results = {
        'q': q,
        'Ru2': Ru2
    }
    
    # Rapport
    report = validation.generate_validation_report(
        "slope",
        results,
        **params
    )
    
    print(report)
    
    print()


def exemple_monte_carlo():
    """Exemple 7 : Simulation Monte Carlo"""
    print("=" * 70)
    print("EXEMPLE 7 : Simulation Monte Carlo")
    print("=" * 70)
    
    # Variabilité climatique
    Hm0_mean = 2.5
    Hm0_std = 0.5
    Tm_10_mean = 6.0
    Tm_10_std = 0.8
    
    print(f"\nVariabilité des paramètres :")
    print(f"  Hm0 ~ N({Hm0_mean}, {Hm0_std}²) m")
    print(f"  Tm-1,0 ~ N({Tm_10_mean}, {Tm_10_std}²) s")
    print(f"  Nombre de simulations : 10000")
    
    # Simulation
    mc_result = probabilistic.monte_carlo_overtopping(
        Hm0_mean, Hm0_std, Tm_10_mean, Tm_10_std,
        h=10.0, Rc=3.0, alpha_deg=35.0, gamma_f=0.5,
        n_simulations=10000
    )
    
    print(f"\nRésultats Monte Carlo :")
    print(f"  Débit moyen : {mc_result['q_mean']*1000:.3f} l/s/m")
    print(f"  Débit médian : {mc_result['q_median']*1000:.3f} l/s/m")
    print(f"  Écart-type : {mc_result['q_std']*1000:.3f} l/s/m")
    print(f"  Intervalle 90% : [{mc_result['q_5']*1000:.3f}, {mc_result['q_95']*1000:.3f}] l/s/m")
    print(f"  Min/Max : [{mc_result['q_min']*1000:.3f}, {mc_result['q_max']*1000:.3f}] l/s/m")
    
    print()


def exemple_pente_tres_douce():
    """Exemple 8 : Pente très douce avec correction"""
    print("=" * 70)
    print("EXEMPLE 8 : Pente très douce (α < 10°)")
    print("=" * 70)
    
    # Paramètres
    Hm0 = 2.5
    Tm_10 = 6.0
    h = 10.0
    Rc = 3.0
    alpha = 7.0  # Pente très douce
    
    print(f"\nParamètres : α = {alpha}° (très douce)")
    
    # Calcul standard
    q_standard = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha)
    
    # Calcul avec correction
    q_corrected = special_cases.very_gentle_slope(Hm0, Tm_10, h, Rc, alpha)
    
    print(f"\nRésultats :")
    print(f"  q (formule standard) = {q_standard*1000:.3f} l/s/m")
    print(f"  q (avec correction) = {q_corrected*1000:.3f} l/s/m")
    print(f"  Différence = {(1-q_corrected/q_standard)*100:.1f}%")
    print(f"\nRecommandation : Utiliser la valeur corrigée pour pentes < 10°")
    
    print()


if __name__ == "__main__":
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  EXEMPLES AVANCÉS - OPENEUROTOP V0.2.0".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    exemple_run_up()
    exemple_analyses_probabilistes()
    exemple_multi_pentes()
    exemple_validation()
    exemple_cas_extreme()
    exemple_rapport_complet()
    exemple_monte_carlo()
    exemple_pente_tres_douce()
    
    print("=" * 70)
    print("FIN DES EXEMPLES AVANCÉS")
    print("=" * 70)

