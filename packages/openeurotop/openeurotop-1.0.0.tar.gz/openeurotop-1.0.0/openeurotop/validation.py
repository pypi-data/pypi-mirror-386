"""
Module de validation et vérifications selon EurOtop (2018)

Vérifie les domaines de validité, signale les warnings et propose des recommandations
"""

import numpy as np
from openeurotop import wave_parameters
from openeurotop.constants import (
    MIN_SLOPE_ANGLE, MAX_SLOPE_ANGLE,
    MAX_RC_HM0, MIN_RC_HM0
)


class ValidationResult:
    """Classe pour stocker les résultats de validation"""
    
    def __init__(self):
        self.is_valid = True
        self.warnings = []
        self.errors = []
        self.recommendations = []
        self.parameters = {}
    
    def add_warning(self, message):
        """Ajoute un avertissement"""
        self.warnings.append(message)
    
    def add_error(self, message):
        """Ajoute une erreur (invalidité)"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_recommendation(self, message):
        """Ajoute une recommandation"""
        self.recommendations.append(message)
    
    def __str__(self):
        """Affichage formaté des résultats"""
        lines = []
        lines.append("="*70)
        lines.append("RÉSULTATS DE VALIDATION")
        lines.append("="*70)
        
        if self.is_valid:
            lines.append("✓ VALIDITÉ : OK")
        else:
            lines.append("✗ VALIDITÉ : HORS DOMAINE")
        
        if self.errors:
            lines.append("\n❌ ERREURS :")
            for err in self.errors:
                lines.append(f"   • {err}")
        
        if self.warnings:
            lines.append("\n⚠️  AVERTISSEMENTS :")
            for warn in self.warnings:
                lines.append(f"   • {warn}")
        
        if self.recommendations:
            lines.append("\n💡 RECOMMANDATIONS :")
            for rec in self.recommendations:
                lines.append(f"   • {rec}")
        
        if self.parameters:
            lines.append("\n📊 PARAMÈTRES CALCULÉS :")
            for key, value in self.parameters.items():
                if isinstance(value, float):
                    lines.append(f"   • {key} = {value:.3f}")
                else:
                    lines.append(f"   • {key} = {value}")
        
        lines.append("="*70)
        return "\n".join(lines)


def validate_slope_structure(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=1.0, gamma_beta=1.0):
    """
    Valide les paramètres pour une structure à talus
    
    Vérifie les domaines de validité selon EurOtop 2018
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc, alpha_deg : float
        Paramètres de la structure
    gamma_f, gamma_beta : float
        Facteurs de réduction
    
    Returns
    -------
    ValidationResult
        Objet contenant les résultats de validation
    
    Examples
    --------
    >>> result = validate_slope_structure(2.5, 6.0, 10.0, 3.0, 35.0)
    >>> print(result)
    >>> if result.is_valid:
    ...     print("OK pour calcul")
    """
    result = ValidationResult()
    
    # 1. Vérifier la revanche relative
    Rc_Hm0 = Rc / Hm0
    result.parameters['Rc/Hm0'] = Rc_Hm0
    
    if Rc_Hm0 < MIN_RC_HM0:
        result.add_error(
            f"Rc/Hm0 = {Rc_Hm0:.2f} < {MIN_RC_HM0} : Hors domaine de validité. "
            f"La structure est submergée ou quasi-submergée."
        )
        result.add_recommendation(
            "Pour Rc/Hm0 < 0.5, les formules de franchissement sont très incertaines. "
            "Considérer une conception différente ou des essais physiques."
        )
    elif Rc_Hm0 > MAX_RC_HM0:
        result.add_warning(
            f"Rc/Hm0 = {Rc_Hm0:.2f} > {MAX_RC_HM0} : Extrapolation au-delà du domaine validé. "
            f"Les incertitudes sont plus élevées."
        )
        result.add_recommendation(
            "Pour Rc/Hm0 > 3.5, le franchissement est généralement très faible. "
            "Les formules restent conservatrices."
        )
    
    # 2. Vérifier l'angle de pente
    result.parameters['alpha (deg)'] = alpha_deg
    
    if alpha_deg < MIN_SLOPE_ANGLE:
        result.add_warning(
            f"Pente α = {alpha_deg}° < {MIN_SLOPE_ANGLE}° : Pente très douce. "
            f"Les formules standards sont moins fiables."
        )
        result.add_recommendation(
            "Pour α < 10°, utiliser openeurotop.special_cases.very_gentle_slope() "
            "qui applique une correction empirique."
        )
    elif alpha_deg > 60:
        result.add_warning(
            f"Pente α = {alpha_deg}° > 60° : Pente très raide. "
            f"Le comportement se rapproche d'un mur vertical."
        )
        result.add_recommendation(
            "Pour α > 60°, utiliser openeurotop.special_cases.very_steep_slope() "
            "qui interpole vers un mur vertical."
        )
    
    # 3. Vérifier le nombre d'Iribarren
    xi = wave_parameters.iribarren_number(alpha_deg, Hm0, Tm_10)
    result.parameters['xi (Iribarren)'] = xi
    
    if xi < 0.5:
        result.add_warning(
            f"Nombre d'Iribarren ξ = {xi:.2f} < 0.5 : Vagues très fortement déferlantes. "
            f"Cas rare en pratique."
        )
    elif xi > 7.0:
        result.add_warning(
            f"Nombre d'Iribarren ξ = {xi:.2f} > 7.0 : Vagues très non-déferlantes. "
            f"Configuration peu courante."
        )
    
    # 4. Vérifier la profondeur relative
    h_Hm0 = h / Hm0
    result.parameters['h/Hm0'] = h_Hm0
    
    if h_Hm0 < 2.0:
        result.add_warning(
            f"Profondeur relative h/Hm0 = {h_Hm0:.2f} < 2.0 : Eau peu profonde. "
            f"Déferlement probable avant la structure."
        )
        result.add_recommendation(
            "En eau peu profonde, considérer la correction avec "
            "openeurotop.special_cases.shallow_water_correction()"
        )
    
    # 5. Vérifier la cambrure
    s0 = wave_parameters.wave_steepness(Hm0, Tm_10)
    result.parameters['s0 (steepness)'] = s0
    
    if s0 < 0.005:
        result.add_warning(
            f"Cambrure s0 = {s0:.4f} < 0.005 : Vagues très plates (houle longue). "
            f"Configuration inhabituelle."
        )
    elif s0 > 0.07:
        result.add_warning(
            f"Cambrure s0 = {s0:.4f} > 0.07 : Vagues très cambrées (mer du vent). "
            f"Vagues potentiellement déferlantes."
        )
    
    # 6. Vérifier les facteurs de réduction
    if gamma_f < 0.3 or gamma_f > 1.0:
        result.add_warning(
            f"Facteur de rugosité γf = {gamma_f:.2f} hors plage typique [0.3, 1.0]"
        )
    
    if gamma_beta < 0.5 or gamma_beta > 1.0:
        result.add_warning(
            f"Facteur d'obliquité γβ = {gamma_beta:.2f} hors plage typique [0.5, 1.0]"
        )
    
    # 7. Recommandations générales
    if result.is_valid and len(result.warnings) == 0:
        result.add_recommendation(
            "Tous les paramètres sont dans le domaine de validité standard. "
            "Les formules EurOtop peuvent être appliquées avec confiance."
        )
    
    return result


def validate_vertical_wall(Hm0, Tm_10, h, Rc):
    """
    Valide les paramètres pour un mur vertical
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc : float
        Paramètres de la structure
    
    Returns
    -------
    ValidationResult
        Résultats de validation
    """
    result = ValidationResult()
    
    # 1. Revanche relative
    Rc_Hm0 = Rc / Hm0
    result.parameters['Rc/Hm0'] = Rc_Hm0
    
    if Rc_Hm0 < 0.1:
        result.add_error(
            f"Rc/Hm0 = {Rc_Hm0:.2f} < 0.1 : Hors domaine de validité pour mur vertical. "
            f"La structure est submergée."
        )
    elif Rc_Hm0 > 3.5:
        result.add_warning(
            f"Rc/Hm0 = {Rc_Hm0:.2f} > 3.5 : Extrapolation. "
            f"Le franchissement devrait être très faible."
        )
    
    # 2. Profondeur relative
    d_star = h / Hm0
    result.parameters['h/Hm0'] = d_star
    
    if d_star < 0.2:
        result.add_warning(
            f"h/Hm0 = {d_star:.2f} < 0.2 : Très peu profond. "
            f"Conditions potentiellement impulsives."
        )
        result.add_recommendation(
            "Pour h/Hm0 < 0.3, les impacts peuvent être impulsifs. "
            "Vérifier avec impulsive=True dans mur_vertical()"
        )
    elif d_star > 5.0:
        result.add_warning(
            f"h/Hm0 = {d_star:.2f} > 5.0 : Eau très profonde. "
            f"Configuration inhabituelle pour un mur de protection."
        )
    
    # 3. Période et longueur d'onde
    L0 = wave_parameters.wave_length_deep_water(Tm_10)
    result.parameters['L0 (m)'] = L0
    
    h_L0 = h / L0
    result.parameters['h/L0'] = h_L0
    
    if h_L0 < 0.1:
        result.add_warning(
            f"h/L0 = {h_L0:.2f} < 0.1 : Eau peu profonde par rapport à la longueur d'onde. "
            f"Les vagues peuvent avoir déferlé."
        )
    
    return result


def validate_composite_structure(Hm0, Tm_10, h, Rc, alpha_lower_deg, h_transition):
    """
    Valide les paramètres pour une structure composite
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc : float
        Paramètres de vague
    alpha_lower_deg : float
        Angle de pente inférieure
    h_transition : float
        Hauteur de transition
    
    Returns
    -------
    ValidationResult
        Résultats de validation
    """
    result = ValidationResult()
    
    # 1. Valider la partie talus
    result_slope = validate_slope_structure(Hm0, Tm_10, h, h_transition, alpha_lower_deg)
    result.warnings.extend(result_slope.warnings)
    result.errors.extend(result_slope.errors)
    
    # 2. Vérifier la cohérence de la transition
    if h_transition <= 0:
        result.add_error(
            f"Hauteur de transition h_transition = {h_transition:.2f} m <= 0. "
            f"La transition doit être au-dessus du SWL."
        )
    elif h_transition >= Rc:
        result.add_warning(
            f"Hauteur de transition {h_transition:.2f} m >= Revanche {Rc:.2f} m. "
            f"Le mur vertical n'a pas d'effet."
        )
        result.add_recommendation(
            "Si h_transition >= Rc, utiliser simplement une formule pour talus simple."
        )
    
    # 3. Estimer le run-up
    from openeurotop.run_up import run_up_2percent_smooth_slope
    Ru2_estimate = run_up_2percent_smooth_slope(Hm0, Tm_10, alpha_lower_deg)
    result.parameters['Ru2% estimé (m)'] = Ru2_estimate
    
    if h_transition > Ru2_estimate:
        result.add_warning(
            f"La transition ({h_transition:.2f} m) est au-dessus du run-up estimé "
            f"({Ru2_estimate:.2f} m). Le mur vertical sera peu sollicité."
        )
    
    return result


def check_design_requirements(q, q_limit, safety_factor=1.0):
    """
    Vérifie si le débit respecte les critères de conception
    
    Parameters
    ----------
    q : float
        Débit calculé (m³/s/m)
    q_limit : float
        Débit limite acceptable (m³/s/m)
    safety_factor : float, optional
        Facteur de sécurité à appliquer
    
    Returns
    -------
    dict
        Résultats de vérification
    
    Examples
    --------
    >>> # Vérifier si q < 1 l/s/m avec facteur de sécurité 1.5
    >>> check = check_design_requirements(0.0008, 0.001, safety_factor=1.5)
    >>> if check['acceptable']:
    ...     print("Conception acceptable")
    """
    q_design = q * safety_factor
    
    acceptable = q_design <= q_limit
    
    margin = (q_limit - q_design) / q_limit * 100 if acceptable else None
    exceedance = (q_design - q_limit) / q_limit * 100 if not acceptable else None
    
    return {
        'q_calculated': q,
        'q_design': q_design,
        'q_limit': q_limit,
        'safety_factor': safety_factor,
        'acceptable': acceptable,
        'margin_percent': margin,
        'exceedance_percent': exceedance,
        'status': 'OK' if acceptable else 'DÉPASSEMENT'
    }


def validate_all_parameters(structure_type, **params):
    """
    Validation globale pour tous types de structures
    
    Parameters
    ----------
    structure_type : str
        Type de structure : "slope", "vertical_wall", "composite"
    **params : dict
        Paramètres de la structure
    
    Returns
    -------
    ValidationResult
        Résultats complets de validation
    
    Examples
    --------
    >>> result = validate_all_parameters(
    ...     "slope",
    ...     Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0
    ... )
    >>> print(result)
    """
    if structure_type == "slope":
        required = ['Hm0', 'Tm_10', 'h', 'Rc', 'alpha_deg']
        for param in required:
            if param not in params:
                raise ValueError(f"Paramètre manquant : {param}")
        return validate_slope_structure(
            params['Hm0'], params['Tm_10'], params['h'],
            params['Rc'], params['alpha_deg'],
            params.get('gamma_f', 1.0), params.get('gamma_beta', 1.0)
        )
    
    elif structure_type == "vertical_wall":
        required = ['Hm0', 'Tm_10', 'h', 'Rc']
        for param in required:
            if param not in params:
                raise ValueError(f"Paramètre manquant : {param}")
        return validate_vertical_wall(
            params['Hm0'], params['Tm_10'], params['h'], params['Rc']
        )
    
    elif structure_type == "composite":
        required = ['Hm0', 'Tm_10', 'h', 'Rc', 'alpha_lower_deg', 'h_transition']
        for param in required:
            if param not in params:
                raise ValueError(f"Paramètre manquant : {param}")
        return validate_composite_structure(
            params['Hm0'], params['Tm_10'], params['h'], params['Rc'],
            params['alpha_lower_deg'], params['h_transition']
        )
    
    else:
        raise ValueError(f"Type de structure inconnu : {structure_type}")


def generate_validation_report(structure_type, calculation_results, **params):
    """
    Génère un rapport de validation complet
    
    Parameters
    ----------
    structure_type : str
        Type de structure
    calculation_results : dict
        Résultats de calcul (débit, etc.)
    **params : dict
        Paramètres de la structure
    
    Returns
    -------
    str
        Rapport formaté
    
    Examples
    --------
    >>> from openeurotop import overtopping
    >>> q = overtopping.digue_talus(2.5, 6.0, 10.0, 3.0, 35.0)
    >>> report = generate_validation_report(
    ...     "slope",
    ...     {'q': q},
    ...     Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0
    ... )
    >>> print(report)
    """
    # Validation des paramètres
    validation = validate_all_parameters(structure_type, **params)
    
    # Construction du rapport
    lines = []
    lines.append("="*80)
    lines.append("RAPPORT DE VALIDATION - OPENEUROTOP")
    lines.append("="*80)
    lines.append(f"\nType de structure : {structure_type}")
    lines.append(f"\nDate : {np.datetime64('today')}")
    
    lines.append("\n" + "-"*80)
    lines.append("PARAMÈTRES D'ENTRÉE")
    lines.append("-"*80)
    for key, value in sorted(params.items()):
        if isinstance(value, float):
            lines.append(f"  {key:<20} = {value:>10.3f}")
        else:
            lines.append(f"  {key:<20} = {value:>10}")
    
    lines.append("\n" + "-"*80)
    lines.append("RÉSULTATS DE CALCUL")
    lines.append("-"*80)
    for key, value in sorted(calculation_results.items()):
        if isinstance(value, float):
            if 'q' in key.lower():
                lines.append(f"  {key:<20} = {value:>10.6f} m³/s/m = {value*1000:>10.3f} l/s/m")
            else:
                lines.append(f"  {key:<20} = {value:>10.3f}")
        else:
            lines.append(f"  {key:<20} = {value}")
    
    lines.append("\n" + str(validation))
    
    lines.append("\n" + "="*80)
    lines.append("FIN DU RAPPORT")
    lines.append("="*80)
    
    return "\n".join(lines)

