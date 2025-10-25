#!/usr/bin/env python
"""
Démonstration rapide du package OpenEurOtop
Exécutez ce script pour voir le package en action !
"""

from openeurotop import overtopping, wave_parameters, reduction_factors

def main():
    print("\n" + "="*70)
    print("DEMONSTRATION RAPIDE - OPENEUROTOP")
    print("="*70 + "\n")
    
    # Exemple 1 : Calcul simple
    print("EXEMPLE 1 : Digue a talus lisse")
    print("-" * 70)
    
    Hm0 = 2.5
    Tm_10 = 6.0
    h = 10.0
    Rc = 3.0
    alpha = 35.0
    
    q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha)
    xi = wave_parameters.iribarren_number(alpha, Hm0, Tm_10)
    
    print(f"  Hauteur de vague : {Hm0} m")
    print(f"  Periode : {Tm_10} s")
    print(f"  Revanche : {Rc} m")
    print(f"  Pente : {alpha} degres")
    print(f"\n  => Nombre d'Iribarren : {xi:.3f}")
    print(f"  => Debit de franchissement : {q*1000:.3f} l/s/m")
    
    # Volume sur 3 heures
    volumes = overtopping.calcul_volumes_franchissement(q, 3.0)
    print(f"  => Volume (3h de tempete) : {volumes['volume_total_m3_per_m']:.2f} m3/m")
    
    # Exemple 2 : Comparaison de revetements
    print("\n\nEXEMPLE 2 : Comparaison de revetements")
    print("-" * 70)
    
    revetements = ["lisse", "beton_rugueux", "enrochement_2couches", "tetrapodes"]
    
    print(f"{'Revetement':<25} {'gamma_f':<8} {'q (l/s/m)':<12} {'Reduction':<10}")
    print(f"{'-'*60}")
    
    q_ref = None
    for rev in revetements:
        gamma_f = reduction_factors.gamma_f_roughness(rev)
        q_rev = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha, gamma_f=gamma_f)
        
        if q_ref is None:
            q_ref = q_rev
            reduction = "-"
        else:
            reduction = f"-{(1-q_rev/q_ref)*100:.0f}%"
        
        print(f"{rev:<25} {gamma_f:<8.2f} {q_rev*1000:<12.3f} {reduction:<10}")
    
    # Exemple 3 : Structure composite
    print("\n\nEXEMPLE 3 : Structure composite (talus + mur)")
    print("-" * 70)
    
    q_composite = overtopping.structure_composite(
        Hm0=2.8,
        Tm_10=6.5,
        h=10.0,
        Rc=5.0,
        alpha_lower_deg=30.0,
        h_transition=2.0,
        gamma_f_lower=0.9,
        gamma_f_upper=1.0
    )
    
    print(f"  Configuration : Talus 30 degres + Mur vertical")
    print(f"  Hauteur de transition : 2.0 m")
    print(f"  Revanche totale : 5.0 m")
    print(f"\n  => Debit de franchissement : {q_composite*1000:.3f} l/s/m")
    
    # Exemple 4 : Effet de l'obliquite
    print("\n\nEXEMPLE 4 : Effet de l'obliquite des vagues")
    print("-" * 70)
    
    print(f"{'Angle b':<10} {'gamma_b':<10} {'q (l/s/m)':<12} {'Reduction':<10}")
    print(f"{'-'*45}")
    
    angles = [0, 15, 30, 45, 60]
    q_ref = None
    
    for beta in angles:
        gamma_beta = reduction_factors.gamma_beta_obliquity(beta)
        q_obl = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha, gamma_beta=gamma_beta)
        
        if q_ref is None:
            q_ref = q_obl
            reduction = "-"
        else:
            reduction = f"-{(1-q_obl/q_ref)*100:.0f}%"
        
        print(f"{beta} deg{'':<5} {gamma_beta:<10.3f} {q_obl*1000:<12.3f} {reduction:<10}")
    
    # Resume
    print("\n\n" + "="*70)
    print("Demonstration terminee avec succes !")
    print("="*70)
    
    print("\nPour aller plus loin :")
    print("  - QUICKSTART.md - Demarrage rapide")
    print("  - docs/GUIDE_UTILISATEUR.md - Guide complet")
    print("  - examples/exemple_basic.py - 8 exemples detailles")
    print("  - python verify_installation.py - Verifier l'installation")
    print("\n")


if __name__ == "__main__":
    try:
        main()
    except ImportError as e:
        print("\nErreur d'importation !")
        print(f"   {e}")
        print("\nSolution :")
        print("   pip install -e .")
        print("   ou")
        print("   pip install -r requirements.txt")
        print()

