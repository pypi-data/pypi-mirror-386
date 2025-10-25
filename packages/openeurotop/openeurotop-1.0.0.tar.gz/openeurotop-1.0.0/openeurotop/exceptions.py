"""
Exceptions personnalisées pour OpenEurOtop

Ce module définit les exceptions spécifiques utilisées dans le package
pour une meilleure gestion des erreurs et des messages informatifs.
"""


class OpenEurOtopError(Exception):
    """
    Classe de base pour toutes les exceptions OpenEurOtop.
    
    Toutes les exceptions personnalisées du package héritent de cette classe.
    """
    pass


class ValidationError(OpenEurOtopError):
    """
    Erreur de validation des paramètres d'entrée.
    
    Levée lorsqu'un paramètre fourni n'est pas valide (type incorrect,
    valeur négative quand positive requise, etc.).
    
    Examples
    --------
    >>> raise ValidationError("Hm0 doit être positif, reçu -2.5")
    """
    pass


class DomainError(OpenEurOtopError):
    """
    Paramètres hors du domaine de validité d'EurOtop.
    
    Levée lorsque les paramètres sont en dehors du domaine pour lequel
    les formules EurOtop sont validées. Le calcul peut continuer mais
    les résultats peuvent être imprécis.
    
    Examples
    --------
    >>> raise DomainError(
    ...     "Nombre d'Iribarren ξ=12.5 hors domaine [1, 10]. "
    ...     "Résultats non fiables."
    ... )
    """
    pass


class CalculationError(OpenEurOtopError):
    """
    Erreur lors du calcul.
    
    Levée lorsqu'un calcul ne peut pas être effectué (division par zéro,
    convergence impossible, etc.).
    
    Examples
    --------
    >>> raise CalculationError("Impossible de calculer la longueur d'onde")
    """
    pass


class ConfigurationError(OpenEurOtopError):
    """
    Erreur de configuration.
    
    Levée lorsque la configuration du calcul est invalide ou incohérente.
    
    Examples
    --------
    >>> raise ConfigurationError(
    ...     "Type de revêtement 'xyz' non reconnu"
    ... )
    """
    pass


class DataError(OpenEurOtopError):
    """
    Erreur liée aux données.
    
    Levée lorsque les données fournies sont incohérentes ou manquantes.
    
    Examples
    --------
    >>> raise DataError("Données de vagues manquantes")
    """
    pass


def validate_positive(value: float, name: str) -> None:
    """
    Valide qu'une valeur est strictement positive.
    
    Parameters
    ----------
    value : float
        Valeur à valider
    name : str
        Nom du paramètre (pour message d'erreur)
    
    Raises
    ------
    ValidationError
        Si la valeur n'est pas strictement positive
    
    Examples
    --------
    >>> validate_positive(2.5, "Hm0")  # OK
    >>> validate_positive(-1.0, "Hm0")  # Lève ValidationError
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{name} doit être un nombre, reçu {type(value).__name__}"
        )
    if value <= 0:
        raise ValidationError(
            f"{name} doit être strictement positif, reçu {value}"
        )


def validate_non_negative(value: float, name: str) -> None:
    """
    Valide qu'une valeur est non-négative.
    
    Parameters
    ----------
    value : float
        Valeur à valider
    name : str
        Nom du paramètre (pour message d'erreur)
    
    Raises
    ------
    ValidationError
        Si la valeur est négative
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{name} doit être un nombre, reçu {type(value).__name__}"
        )
    if value < 0:
        raise ValidationError(
            f"{name} doit être non-négatif, reçu {value}"
        )


def validate_range(value: float, name: str, min_val: float, max_val: float, 
                   inclusive: bool = True) -> None:
    """
    Valide qu'une valeur est dans un intervalle donné.
    
    Parameters
    ----------
    value : float
        Valeur à valider
    name : str
        Nom du paramètre
    min_val : float
        Valeur minimale
    max_val : float
        Valeur maximale
    inclusive : bool, optional
        Si True, les bornes sont incluses, par défaut True
    
    Raises
    ------
    ValidationError
        Si la valeur est hors de l'intervalle
    """
    if not isinstance(value, (int, float)):
        raise ValidationError(
            f"{name} doit être un nombre, reçu {type(value).__name__}"
        )
    
    if inclusive:
        if value < min_val or value > max_val:
            raise ValidationError(
                f"{name} doit être dans [{min_val}, {max_val}], reçu {value}"
            )
    else:
        if value <= min_val or value >= max_val:
            raise ValidationError(
                f"{name} doit être dans ]{min_val}, {max_val}[, reçu {value}"
            )


def warn_domain(message: str) -> None:
    """
    Émet un avertissement pour domaine de validité.
    
    Parameters
    ----------
    message : str
        Message d'avertissement
    """
    import warnings
    warnings.warn(message, DomainError, stacklevel=2)

