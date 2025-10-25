#!/usr/bin/env python
"""
Script de vérification de l'installation du package OpenEurOtop
"""

import sys

def check_import():
    """Vérifie que le package peut être importé"""
    try:
        import openeurotop
        print("[OK] Package 'openeurotop' importe avec succes")
        print(f"  Version: {openeurotop.__version__}")
        return True
    except ImportError as e:
        print(f"[FAIL] Erreur d'importation: {e}")
        return False


def check_dependencies():
    """Vérifie les dépendances"""
    deps_ok = True
    
    try:
        import numpy
        print(f"[OK] numpy {numpy.__version__}")
    except ImportError:
        print("[FAIL] numpy non trouve")
        deps_ok = False
    
    try:
        import scipy
        print(f"[OK] scipy {scipy.__version__}")
    except ImportError:
        print("[FAIL] scipy non trouve")
        deps_ok = False
    
    return deps_ok


def check_modules():
    """Vérifie que tous les modules sont accessibles"""
    modules_ok = True
    
    try:
        from openeurotop import overtopping
        print("[OK] Module 'overtopping' accessible")
    except ImportError:
        print("[FAIL] Module 'overtopping' non accessible")
        modules_ok = False
    
    try:
        from openeurotop import wave_parameters
        print("[OK] Module 'wave_parameters' accessible")
    except ImportError:
        print("[FAIL] Module 'wave_parameters' non accessible")
        modules_ok = False
    
    try:
        from openeurotop import reduction_factors
        print("[OK] Module 'reduction_factors' accessible")
    except ImportError:
        print("[FAIL] Module 'reduction_factors' non accessible")
        modules_ok = False
    
    try:
        from openeurotop import constants
        print("[OK] Module 'constants' accessible")
    except ImportError:
        print("[FAIL] Module 'constants' non accessible")
        modules_ok = False
    
    return modules_ok


def run_basic_test():
    """Exécute un test de calcul simple"""
    try:
        from openeurotop import overtopping
        
        # Calcul simple
        q = overtopping.digue_talus(
            Hm0=2.5,
            Tm_10=6.0,
            h=10.0,
            Rc=3.0,
            alpha_deg=35.0
        )
        
        if q > 0 and q < 1.0:
            print(f"[OK] Calcul de base reussi (q = {q:.6f} m3/s/m)")
            return True
        else:
            print(f"[FAIL] Calcul de base a donne un resultat suspect: q = {q}")
            return False
            
    except Exception as e:
        print(f"[FAIL] Erreur lors du calcul de base: {e}")
        return False


def run_detailed_test():
    """Exécute un test plus détaillé"""
    try:
        from openeurotop import overtopping, wave_parameters, reduction_factors
        
        # Test du nombre d'Iribarren
        xi = wave_parameters.iribarren_number(35.0, 2.5, 6.0)
        
        # Test du facteur de rugosité
        gamma_f = reduction_factors.gamma_f_roughness("enrochement_2couches")
        
        # Test du calcul détaillé
        result = overtopping.digue_talus_detailed(
            Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0,
            type_revetement="enrochement_2couches"
        )
        
        checks = [
            (xi > 0, f"Iribarren: xi = {xi:.3f}"),
            (gamma_f == 0.5, f"Rugosite: gamma_f = {gamma_f}"),
            (result['q'] > 0, f"Debit: q = {result['q']:.6f} m3/s/m"),
        ]
        
        all_ok = True
        for check, msg in checks:
            if check:
                print(f"[OK] {msg}")
            else:
                print(f"[FAIL] {msg}")
                all_ok = False
        
        return all_ok
        
    except Exception as e:
        print(f"[FAIL] Erreur lors des tests detailles: {e}")
        return False


def main():
    """Fonction principale de vérification"""
    print("=" * 70)
    print("VÉRIFICATION DE L'INSTALLATION - OPENEUROTOP")
    print("=" * 70)
    print()
    
    print("1. Vérification des importations")
    print("-" * 70)
    import_ok = check_import()
    print()
    
    print("2. Vérification des dépendances")
    print("-" * 70)
    deps_ok = check_dependencies()
    print()
    
    print("3. Vérification des modules")
    print("-" * 70)
    modules_ok = check_modules()
    print()
    
    print("4. Test de calcul de base")
    print("-" * 70)
    basic_test_ok = run_basic_test()
    print()
    
    print("5. Tests détaillés")
    print("-" * 70)
    detailed_test_ok = run_detailed_test()
    print()
    
    # Résumé
    print("=" * 70)
    print("RÉSUMÉ")
    print("=" * 70)
    
    all_ok = import_ok and deps_ok and modules_ok and basic_test_ok and detailed_test_ok
    
    if all_ok:
        print("[OK] Tous les tests ont reussi !")
        print("\nLe package OpenEurOtop est correctement installé et fonctionnel.")
        print("\nPour commencer :")
        print("  - Consultez QUICKSTART.md pour un démarrage rapide")
        print("  - Exécutez 'python examples/exemple_basic.py' pour voir des exemples")
        print("  - Exécutez 'python tests/test_overtopping.py' pour les tests unitaires")
        return 0
    else:
        print("[FAIL] Certains tests ont echoue.")
        print("\nVeuillez vérifier :")
        print("  1. Que les dépendances sont installées: pip install -r requirements.txt")
        print("  2. Que le package est installé: pip install -e .")
        print("  3. Que vous êtes dans le bon répertoire")
        return 1


if __name__ == "__main__":
    sys.exit(main())

