"""
Exécution des 12 Case Studies EurOtop (2018)

Ce fichier exécute et affiche les résultats des 12 études de cas
documentées dans le manuel EurOtop 2018, Chapitre 8.
"""

import sys
sys.path.insert(0, '..')

from openeurotop import case_studies


def main():
    print("\n")
    print("*" * 80)
    print("*" + " " * 78 + "*")
    print("*" + "  EUROTOP 2018 - 12 CASE STUDIES".center(78) + "*")
    print("*" + " " * 78 + "*")
    print("*" * 80)
    print("\n")
    
    # Récupérer tous les case studies
    all_cases = case_studies.run_all_case_studies()
    
    # Afficher chaque case study
    for cs_id, cs in all_cases.items():
        print(cs)
        print("\n")
        
        # Afficher la comparaison avec les mesures si disponible
        comp = case_studies.compare_with_measurements(cs)
        if comp['comparison_available']:
            print("VALIDATION AVEC MESURES:")
            print(f"  Mesure :    {comp['measured']*1000:>8.3f} l/s/m")
            print(f"  Calcule :   {comp['calculated']*1000:>8.3f} l/s/m")
            print(f"  Erreur :    {comp['relative_error_percent']:>8.1f} %")
            print(f"  Statut :    {comp['status']}")
            print("\n")
        
        input("Appuyez sur Entree pour le case study suivant...")
        print("\n")
    
    # Résumé
    print("=" * 80)
    print("RESUME DES CASE STUDIES")
    print("=" * 80)
    print(f"\nNombre total de case studies : {len(all_cases)}")
    
    # Compter combien ont des mesures
    with_measurements = sum(1 for cs in all_cases.values() 
                           if case_studies.compare_with_measurements(cs)['comparison_available'])
    print(f"Avec mesures disponibles : {with_measurements}")
    print(f"Sans mesures : {len(all_cases) - with_measurements}")
    
    # Types de structures
    print("\nTypes de structures couverts :")
    print("  - Digues en enrochement (rubble mound)")
    print("  - Murs verticaux et caissons")
    print("  - Structures composites")
    print("  - Digues lisses (asphalte, herbe)")
    print("  - Structures avec bermes")
    print("  - Structures a pentes multiples")
    print("  - Blocs artificiels (Accropode)")
    print("  - Conditions extremes")
    
    print("\n" + "=" * 80)
    print("FIN DES CASE STUDIES")
    print("=" * 80)
    print("\n")


def generate_full_report():
    """Génère et sauvegarde le rapport complet"""
    print("Generation du rapport complet...")
    
    report = case_studies.generate_case_studies_report()
    
    # Sauvegarder dans un fichier
    with open('case_studies_report.txt', 'w', encoding='utf-8') as f:
        f.write(report)
    
    print("Rapport sauvegarde dans : case_studies_report.txt")
    print(f"Taille du rapport : {len(report)} caracteres")


def show_specific_case(case_number):
    """
    Affiche un case study spécifique
    
    Parameters
    ----------
    case_number : int
        Numéro du case study (1-12)
    """
    all_cases = case_studies.run_all_case_studies()
    cs_id = f'CS{case_number}'
    
    if cs_id in all_cases:
        print(all_cases[cs_id])
        
        comp = case_studies.compare_with_measurements(all_cases[cs_id])
        if comp['comparison_available']:
            print("\nVALIDATION:")
            print(f"  Mesure :    {comp['measured']*1000:.3f} l/s/m")
            print(f"  Calcule :   {comp['calculated']*1000:.3f} l/s/m")
            print(f"  Erreur :    {comp['relative_error_percent']:.1f} %")
    else:
        print(f"Case study {case_number} non trouve.")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='EurOtop Case Studies')
    parser.add_argument('--case', type=int, help='Afficher un case study specifique (1-12)')
    parser.add_argument('--report', action='store_true', help='Generer le rapport complet')
    parser.add_argument('--all', action='store_true', help='Afficher tous les case studies')
    
    args = parser.parse_args()
    
    if args.case:
        show_specific_case(args.case)
    elif args.report:
        generate_full_report()
    elif args.all:
        main()
    else:
        # Par défaut, afficher tous
        main()

