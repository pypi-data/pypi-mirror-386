"""
Exemples d'utilisation du package OpenEurOtop
"""

import sys
sys.path.insert(0, '..')

from openeurotop import overtopping, wave_parameters, reduction_factors


def exemple_digue_lisse():
    """Exemple 1 : Digue à talus lisse"""
    print("=" * 70)
    print("EXEMPLE 1 : Digue à talus lisse")
    print("=" * 70)
    
    # Paramètres
    Hm0 = 2.5      # Hauteur significative (m)
    Tm_10 = 6.0    # Période moyenne (s)
    h = 10.0       # Profondeur d'eau (m)
    Rc = 3.0       # Revanche (m)
    alpha = 35.0   # Pente du talus (degrés)
    
    print(f"\nParamètres :")
    print(f"  Hm0 = {Hm0} m")
    print(f"  Tm-1,0 = {Tm_10} s")
    print(f"  h = {h} m")
    print(f"  Rc = {Rc} m")
    print(f"  α = {alpha}°")
    
    # Calcul du franchissement
    q = overtopping.digue_talus(
        Hm0=Hm0,
        Tm_10=Tm_10,
        h=h,
        Rc=Rc,
        alpha_deg=alpha,
        gamma_b=1.0,
        gamma_f=1.0,
        gamma_beta=1.0
    )
    
    # Calcul du nombre d'Iribarren
    xi = wave_parameters.iribarren_number(alpha, Hm0, Tm_10)
    
    print(f"\nRésultats :")
    print(f"  Nombre d'Iribarren ξ = {xi:.3f}")
    print(f"  Débit de franchissement q = {q:.6f} m³/s/m")
    print(f"  Débit de franchissement q = {q*1000:.3f} l/s/m")
    
    # Volume sur 3 heures de tempête
    volumes = overtopping.calcul_volumes_franchissement(q, 3.0)
    print(f"\nVolumes de franchissement (3 heures de tempête) :")
    print(f"  Volume total = {volumes['volume_total_m3_per_m']:.2f} m³/m")
    print(f"  Volume total = {volumes['volume_liters_per_m']:.0f} litres/m")
    
    print()


def exemple_digue_enrochement():
    """Exemple 2 : Digue en enrochement"""
    print("=" * 70)
    print("EXEMPLE 2 : Digue en enrochement (2 couches)")
    print("=" * 70)
    
    # Paramètres
    Hm0 = 3.0
    Tm_10 = 7.0
    h = 12.0
    Rc = 4.0
    alpha = 33.7  # 1:1.5 (tan(α) = 2/3)
    
    print(f"\nParamètres :")
    print(f"  Hm0 = {Hm0} m")
    print(f"  Tm-1,0 = {Tm_10} s")
    print(f"  h = {h} m")
    print(f"  Rc = {Rc} m")
    print(f"  α = {alpha}° (pente 1:1.5)")
    print(f"  Revêtement : enrochement 2 couches")
    
    # Méthode 1 : Calcul détaillé avec type de revêtement
    result = overtopping.digue_talus_detailed(
        Hm0=Hm0,
        Tm_10=Tm_10,
        h=h,
        Rc=Rc,
        alpha_deg=alpha,
        type_revetement="enrochement_2couches"
    )
    
    print(f"\nRésultats :")
    print(f"  Nombre d'Iribarren ξ = {result['xi']:.3f}")
    print(f"  Facteur de rugosité γf = {result['gamma_f']:.2f}")
    print(f"  Facteur total γ = {result['gamma_total']:.2f}")
    print(f"  Débit de franchissement q = {result['q']:.6f} m³/s/m")
    print(f"  Débit de franchissement q = {result['q']*1000:.3f} l/s/m")
    
    # Méthode 2 : Fonction spécialisée
    q2 = overtopping.digue_en_enrochement(
        Hm0=Hm0,
        Tm_10=Tm_10,
        h=h,
        Rc=Rc,
        alpha_deg=alpha,
        Dn50=1.5,  # Diamètre nominal des enrochements
        n_layers=2,
        permeability="permeable"
    )
    
    print(f"\nVérification (méthode spécialisée) :")
    print(f"  q = {q2:.6f} m³/s/m")
    
    print()


def exemple_mur_vertical():
    """Exemple 3 : Mur vertical"""
    print("=" * 70)
    print("EXEMPLE 3 : Mur vertical")
    print("=" * 70)
    
    # Paramètres
    Hm0 = 2.0
    Tm_10 = 5.5
    h = 8.0
    Rc = 2.5
    
    print(f"\nParamètres :")
    print(f"  Hm0 = {Hm0} m")
    print(f"  Tm-1,0 = {Tm_10} s")
    print(f"  h = {h} m")
    print(f"  Rc = {Rc} m")
    
    # Calcul du franchissement
    q = overtopping.mur_vertical(
        Hm0=Hm0,
        Tm_10=Tm_10,
        h=h,
        Rc=Rc
    )
    
    print(f"\nRésultats :")
    print(f"  Débit de franchissement q = {q:.6f} m³/s/m")
    print(f"  Débit de franchissement q = {q*1000:.3f} l/s/m")
    
    print()


def exemple_structure_composite():
    """Exemple 4 : Structure composite (talus + mur)"""
    print("=" * 70)
    print("EXEMPLE 4 : Structure composite (talus + mur vertical)")
    print("=" * 70)
    
    # Paramètres
    Hm0 = 2.8
    Tm_10 = 6.5
    h = 10.0
    Rc = 5.0
    alpha_lower = 30.0
    h_transition = 2.0  # Transition à +2m SWL
    
    print(f"\nParamètres :")
    print(f"  Hm0 = {Hm0} m")
    print(f"  Tm-1,0 = {Tm_10} s")
    print(f"  h = {h} m")
    print(f"  Rc = {Rc} m")
    print(f"  Pente partie basse = {alpha_lower}°")
    print(f"  Hauteur de transition = {h_transition} m")
    
    # Calcul
    q = overtopping.structure_composite(
        Hm0=Hm0,
        Tm_10=Tm_10,
        h=h,
        Rc=Rc,
        alpha_lower_deg=alpha_lower,
        h_transition=h_transition,
        gamma_f_lower=0.9,  # Béton rugueux
        gamma_f_upper=1.0,  # Mur lisse
    )
    
    print(f"\nRésultats :")
    print(f"  Débit de franchissement q = {q:.6f} m³/s/m")
    print(f"  Débit de franchissement q = {q*1000:.3f} l/s/m")
    
    print()


def exemple_avec_obliquite():
    """Exemple 5 : Effet de l'obliquité des vagues"""
    print("=" * 70)
    print("EXEMPLE 5 : Effet de l'obliquité des vagues")
    print("=" * 70)
    
    # Paramètres de base
    Hm0 = 2.5
    Tm_10 = 6.0
    h = 10.0
    Rc = 3.0
    alpha = 35.0
    
    print(f"\nParamètres :")
    print(f"  Hm0 = {Hm0} m, Tm-1,0 = {Tm_10} s, h = {h} m")
    print(f"  Rc = {Rc} m, α = {alpha}°")
    
    # Test différents angles d'obliquité
    angles = [0, 15, 30, 45, 60]
    
    print(f"\nEffet de l'angle d'obliquité β :")
    print(f"  {'β (°)':<8} {'γβ':<8} {'q (l/s/m)':<12} {'Réduction (%)':<15}")
    print(f"  {'-'*50}")
    
    q_reference = None
    for beta in angles:
        gamma_beta = reduction_factors.gamma_beta_obliquity(beta)
        q = overtopping.digue_talus(
            Hm0, Tm_10, h, Rc, alpha,
            gamma_beta=gamma_beta
        )
        
        if q_reference is None:
            q_reference = q
            reduction = 0
        else:
            reduction = (1 - q/q_reference) * 100
        
        print(f"  {beta:<8} {gamma_beta:<8.3f} {q*1000:<12.3f} {reduction:<15.1f}")
    
    print()


def exemple_avec_berme():
    """Exemple 6 : Effet d'une berme"""
    print("=" * 70)
    print("EXEMPLE 6 : Effet d'une berme")
    print("=" * 70)
    
    # Paramètres de base
    Hm0 = 3.0
    Tm_10 = 7.0
    h = 12.0
    Rc = 4.0
    alpha = 35.0
    
    print(f"\nParamètres :")
    print(f"  Hm0 = {Hm0} m, Tm-1,0 = {Tm_10} s")
    print(f"  Rc = {Rc} m, α = {alpha}°")
    
    # Sans berme
    q_sans_berme = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha)
    
    # Avec berme
    B_berm = 8.0  # Largeur de berme 8m
    h_berm = 0.5  # Berme à +0.5m au-dessus du SWL
    
    gamma_b = reduction_factors.gamma_b_berm(Rc, Hm0, B_berm, h_berm)
    q_avec_berme = overtopping.digue_talus(
        Hm0, Tm_10, h, Rc, alpha,
        gamma_b=gamma_b
    )
    
    print(f"\nRésultats :")
    print(f"  Sans berme :")
    print(f"    q = {q_sans_berme*1000:.3f} l/s/m")
    print(f"\n  Avec berme (B = {B_berm} m, h = {h_berm} m) :")
    print(f"    γb = {gamma_b:.3f}")
    print(f"    q = {q_avec_berme*1000:.3f} l/s/m")
    print(f"    Réduction = {(1-q_avec_berme/q_sans_berme)*100:.1f}%")
    
    print()


def exemple_comparaison_revetements():
    """Exemple 7 : Comparaison de différents revêtements"""
    print("=" * 70)
    print("EXEMPLE 7 : Comparaison de différents revêtements")
    print("=" * 70)
    
    # Paramètres de base
    Hm0 = 2.5
    Tm_10 = 6.0
    h = 10.0
    Rc = 3.0
    alpha = 35.0
    
    print(f"\nParamètres :")
    print(f"  Hm0 = {Hm0} m, Tm-1,0 = {Tm_10} s")
    print(f"  Rc = {Rc} m, α = {alpha}°")
    
    # Types de revêtements à tester
    revetements = [
        "lisse",
        "beton_rugueux",
        "enrochement_1couche",
        "enrochement_2couches",
        "tetrapodes",
        "accropode"
    ]
    
    print(f"\nComparaison des revêtements :")
    print(f"  {'Revêtement':<25} {'γf':<8} {'q (l/s/m)':<12} {'Réduction (%)':<15}")
    print(f"  {'-'*65}")
    
    q_reference = None
    for rev in revetements:
        result = overtopping.digue_talus_detailed(
            Hm0, Tm_10, h, Rc, alpha,
            type_revetement=rev
        )
        
        if q_reference is None:
            q_reference = result['q']
            reduction = 0
        else:
            reduction = (1 - result['q']/q_reference) * 100
        
        print(f"  {rev:<25} {result['gamma_f']:<8.2f} "
              f"{result['q']*1000:<12.3f} {reduction:<15.1f}")
    
    print()


def exemple_statistiques_vagues():
    """Exemple 8 : Statistiques par vagues individuelles"""
    print("=" * 70)
    print("EXEMPLE 8 : Statistiques par vagues individuelles")
    print("=" * 70)
    
    # Paramètres
    Hm0 = 2.5
    Tm_10 = 6.0
    h = 10.0
    Rc = 2.0
    alpha = 35.0
    
    # Durée de tempête
    duree_heures = 4.0
    N_waves = int(duree_heures * 3600 / Tm_10)
    
    print(f"\nParamètres :")
    print(f"  Hm0 = {Hm0} m, Tm-1,0 = {Tm_10} s")
    print(f"  Rc = {Rc} m, α = {alpha}°")
    print(f"  Durée tempête = {duree_heures} heures")
    print(f"  Nombre de vagues = {N_waves}")
    
    # Calcul des statistiques
    stats = overtopping.discharge_individual_waves(
        Hm0, Tm_10, h, Rc, alpha,
        N_waves=N_waves
    )
    
    print(f"\nRésultats :")
    print(f"  Débit moyen q = {stats['q_mean']*1000:.3f} l/s/m")
    print(f"  Volume moyen par vague = {stats['V_mean_per_wave']:.4f} m³/m")
    print(f"  Proportion de vagues franchissantes = {stats['P_overtopping']*100:.1f}%")
    print(f"  Nombre de vagues franchissantes = {stats['N_overtopping_waves']}")
    print(f"  Volume moyen par vague franchissante = {stats['V_per_overtopping_wave']:.3f} m³/m")
    
    print()


if __name__ == "__main__":
    print("\n")
    print("*" * 70)
    print("*" + " " * 68 + "*")
    print("*" + "  EXEMPLES D'UTILISATION DU PACKAGE OPENEUROTOP".center(68) + "*")
    print("*" + " " * 68 + "*")
    print("*" * 70)
    print("\n")
    
    exemple_digue_lisse()
    exemple_digue_enrochement()
    exemple_mur_vertical()
    exemple_structure_composite()
    exemple_avec_obliquite()
    exemple_avec_berme()
    exemple_comparaison_revetements()
    exemple_statistiques_vagues()
    
    print("=" * 70)
    print("FIN DES EXEMPLES")
    print("=" * 70)

