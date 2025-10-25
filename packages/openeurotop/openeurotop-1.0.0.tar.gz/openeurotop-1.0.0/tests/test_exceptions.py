"""
Tests pour les exceptions personnalisées
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

import pytest
from openeurotop import exceptions
from openeurotop.exceptions import (
    OpenEurOtopError,
    ValidationError,
    DomainError,
    CalculationError,
    ConfigurationError,
    DataError,
    validate_positive,
    validate_non_negative,
    validate_range
)


def test_exception_hierarchy():
    """Test de la hiérarchie des exceptions"""
    # Toutes les exceptions héritent de OpenEurOtopError
    assert issubclass(ValidationError, OpenEurOtopError)
    assert issubclass(DomainError, OpenEurOtopError)
    assert issubclass(CalculationError, OpenEurOtopError)
    assert issubclass(ConfigurationError, OpenEurOtopError)
    assert issubclass(DataError, OpenEurOtopError)
    
    # OpenEurOtopError hérite de Exception
    assert issubclass(OpenEurOtopError, Exception)
    
    print("[OK] Hiérarchie des exceptions correcte")


def test_validation_error():
    """Test de ValidationError"""
    with pytest.raises(ValidationError) as exc_info:
        raise ValidationError("Paramètre invalide")
    
    assert "Paramètre invalide" in str(exc_info.value)
    print("[OK] ValidationError fonctionne")


def test_domain_error():
    """Test de DomainError"""
    with pytest.raises(DomainError) as exc_info:
        raise DomainError("Hors domaine de validité")
    
    assert "Hors domaine" in str(exc_info.value)
    print("[OK] DomainError fonctionne")


def test_validate_positive_valid():
    """Test validate_positive avec valeur valide"""
    # Ne doit pas lever d'exception
    validate_positive(1.0, "test")
    validate_positive(100.5, "test")
    validate_positive(0.001, "test")
    
    print("[OK] validate_positive accepte valeurs positives")


def test_validate_positive_invalid():
    """Test validate_positive avec valeurs invalides"""
    # Valeur nulle
    with pytest.raises(ValidationError) as exc_info:
        validate_positive(0.0, "Hm0")
    assert "Hm0" in str(exc_info.value)
    assert "strictement positif" in str(exc_info.value)
    
    # Valeur négative
    with pytest.raises(ValidationError):
        validate_positive(-1.0, "Hm0")
    
    # Type invalide
    with pytest.raises(ValidationError):
        validate_positive("abc", "Hm0")
    
    print("[OK] validate_positive rejette valeurs invalides")


def test_validate_non_negative_valid():
    """Test validate_non_negative avec valeurs valides"""
    validate_non_negative(0.0, "test")
    validate_non_negative(1.0, "test")
    validate_non_negative(100.5, "test")
    
    print("[OK] validate_non_negative accepte valeurs >= 0")


def test_validate_non_negative_invalid():
    """Test validate_non_negative avec valeurs invalides"""
    with pytest.raises(ValidationError) as exc_info:
        validate_non_negative(-1.0, "Rc")
    assert "Rc" in str(exc_info.value)
    assert "non-négatif" in str(exc_info.value)
    
    print("[OK] validate_non_negative rejette valeurs négatives")


def test_validate_range_valid():
    """Test validate_range avec valeurs valides"""
    # Inclusive
    validate_range(5.0, "test", 0.0, 10.0, inclusive=True)
    validate_range(0.0, "test", 0.0, 10.0, inclusive=True)
    validate_range(10.0, "test", 0.0, 10.0, inclusive=True)
    
    # Exclusive
    validate_range(5.0, "test", 0.0, 10.0, inclusive=False)
    
    print("[OK] validate_range accepte valeurs dans intervalle")


def test_validate_range_invalid():
    """Test validate_range avec valeurs invalides"""
    # Hors bornes (inclusive)
    with pytest.raises(ValidationError) as exc_info:
        validate_range(-0.1, "gamma_f", 0.0, 1.0, inclusive=True)
    assert "gamma_f" in str(exc_info.value)
    assert "[0.0, 1.0]" in str(exc_info.value)
    
    with pytest.raises(ValidationError):
        validate_range(1.1, "gamma_f", 0.0, 1.0, inclusive=True)
    
    # Sur bornes (exclusive)
    with pytest.raises(ValidationError):
        validate_range(0.0, "test", 0.0, 1.0, inclusive=False)
    
    with pytest.raises(ValidationError):
        validate_range(1.0, "test", 0.0, 1.0, inclusive=False)
    
    print("[OK] validate_range rejette valeurs hors intervalle")


def test_exception_can_be_caught():
    """Test qu'on peut attraper les exceptions"""
    try:
        raise ValidationError("Test")
    except OpenEurOtopError:
        # Doit pouvoir attraper avec la classe de base
        pass
    
    try:
        raise ValidationError("Test")
    except ValidationError:
        # Doit pouvoir attraper avec la classe spécifique
        pass
    
    print("[OK] Exceptions peuvent être attrapées")


def run_all_tests():
    """Exécute tous les tests"""
    print("\n" + "="*70)
    print("TESTS DES EXCEPTIONS")
    print("="*70 + "\n")
    
    tests = [
        test_exception_hierarchy,
        test_validation_error,
        test_domain_error,
        test_validate_positive_valid,
        test_validate_positive_invalid,
        test_validate_non_negative_valid,
        test_validate_non_negative_invalid,
        test_validate_range_valid,
        test_validate_range_invalid,
        test_exception_can_be_caught
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

