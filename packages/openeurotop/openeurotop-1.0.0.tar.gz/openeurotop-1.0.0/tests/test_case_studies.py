"""
Tests pour les case studies EurOtop
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from openeurotop import case_studies


def test_all_case_studies_run():
    """Vérifie que tous les case studies s'exécutent sans erreur"""
    print("Test : Execution de tous les case studies...")
    
    all_cases = case_studies.run_all_case_studies()
    
    assert len(all_cases) == 12, f"Devrait y avoir 12 case studies, trouvé {len(all_cases)}"
    
    for cs_id, cs in all_cases.items():
        assert cs is not None, f"{cs_id} est None"
        assert hasattr(cs, 'name'), f"{cs_id} n'a pas de nom"
        assert hasattr(cs, 'parameters'), f"{cs_id} n'a pas de paramètres"
        assert hasattr(cs, 'results'), f"{cs_id} n'a pas de résultats"
        assert len(cs.results) > 0, f"{cs_id} n'a pas de résultats calculés"
    
    print(f"[OK] Tous les {len(all_cases)} case studies s'executent correctement")


def test_case_study_1():
    """Test spécifique du Case Study 1 (Zeebrugge)"""
    print("\nTest : Case Study 1 (Zeebrugge)...")
    
    cs = case_studies.case_study_1_zeebrugge()
    
    assert cs.name == "Case Study 1: Zeebrugge Breakwater"
    assert cs.location == "Zeebrugge, Belgium"
    assert cs.parameters['Hm0'] == 4.5
    assert 'q_calculated' in cs.results
    assert cs.results['q_calculated'] > 0
    
    print(f"[OK] Case Study 1 OK")
    print(f"    q_calculated = {cs.results['q_calculated']*1000:.3f} l/s/m")
    if 'q_measured' in cs.results:
        print(f"    q_measured = {cs.results['q_measured']*1000:.3f} l/s/m")


def test_case_study_with_validation():
    """Test des case studies avec validation par mesures"""
    print("\nTest : Case studies avec validation...")
    
    all_cases = case_studies.run_all_case_studies()
    
    validated_cases = []
    for cs_id, cs in all_cases.items():
        comp = case_studies.compare_with_measurements(cs)
        if comp['comparison_available']:
            validated_cases.append(cs_id)
            print(f"  {cs_id}: Erreur = {comp['relative_error_percent']:.1f}%")
    
    print(f"[OK] {len(validated_cases)} case studies avec mesures disponibles")


def test_report_generation():
    """Test de génération du rapport"""
    print("\nTest : Generation du rapport...")
    
    report = case_studies.generate_case_studies_report()
    
    assert isinstance(report, str)
    assert len(report) > 1000, "Le rapport semble trop court"
    assert "CASE STUDY" in report
    assert "EUROTOP" in report.upper()
    
    print(f"[OK] Rapport genere : {len(report)} caracteres")


def test_all_structure_types():
    """Vérifie que tous les types de structures sont couverts"""
    print("\nTest : Couverture des types de structures...")
    
    all_cases = case_studies.run_all_case_studies()
    
    structure_types = set()
    for cs in all_cases.values():
        desc = cs.description.lower()
        if 'rubble' in desc or 'rock' in desc or 'enrochement' in desc:
            structure_types.add('rubble_mound')
        if 'vertical' in desc or 'wall' in desc or 'mur' in desc:
            structure_types.add('vertical_wall')
        if 'composite' in desc:
            structure_types.add('composite')
        if 'berm' in desc or 'berme' in desc:
            structure_types.add('with_berm')
        if 'multi' in desc or 'pente' in desc:
            structure_types.add('multi_slope')
    
    print(f"  Types de structures trouvés : {structure_types}")
    assert len(structure_types) >= 4, "Devrait couvrir au moins 4 types de structures"
    
    print(f"[OK] {len(structure_types)} types de structures couverts")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS DES CASE STUDIES EUROTOP")
    print("="*70 + "\n")
    
    tests = [
        test_all_case_studies_run,
        test_case_study_1,
        test_case_study_with_validation,
        test_report_generation,
        test_all_structure_types
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

