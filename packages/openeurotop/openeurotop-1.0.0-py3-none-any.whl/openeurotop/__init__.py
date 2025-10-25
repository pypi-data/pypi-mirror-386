"""
OpenEurOtop - Implémentation Python du guide EurOtop
pour le calcul du franchissement de vagues
"""

__version__ = "0.3.0-beta"
__author__ = "OpenEurOtop Contributors"

from openeurotop import (
    overtopping,
    wave_parameters,
    reduction_factors,
    constants,
    run_up,
    probabilistic,
    special_cases,
    neural_network,
    xgboost_model,
    validation,
    case_studies,
    exceptions
)

# Exceptions principales exposées au niveau du package
from openeurotop.exceptions import (
    OpenEurOtopError,
    ValidationError,
    DomainError,
    CalculationError,
    ConfigurationError,
    DataError
)

__all__ = [
    "overtopping",
    "wave_parameters",
    "reduction_factors",
    "constants",
    "run_up",
    "probabilistic",
    "special_cases",
    "neural_network",
    "xgboost_model",
    "validation",
    "case_studies",
    "exceptions",
    # Exceptions
    "OpenEurOtopError",
    "ValidationError",
    "DomainError",
    "CalculationError",
    "ConfigurationError",
    "DataError"
]

