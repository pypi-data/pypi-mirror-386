"""
Cas spécifiques et configurations complexes selon EurOtop (2018)

Pentes multiples, structures en escalier, conditions extrêmes, etc.
"""

import numpy as np
from openeurotop.constants import G, DEG_TO_RAD
from openeurotop import overtopping, wave_parameters, reduction_factors


def multi_slope_structure(Hm0, Tm_10, h, Rc, slopes_config, 
                          gamma_f_sections=None, gamma_beta=1.0, g=G):
    """
    Calcul du franchissement pour une structure à pentes multiples
    
    EurOtop 2018 - Annexe B.3
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    h : float
        Profondeur d'eau (m)
    Rc : float
        Revanche totale (m)
    slopes_config : list of dict
        Configuration des pentes, chaque dict contient:
        - 'alpha_deg': angle de pente (degrés)
        - 'h_start': hauteur de début (m au-dessus SWL)
        - 'h_end': hauteur de fin (m au-dessus SWL)
    gamma_f_sections : list of float, optional
        Facteurs de rugosité pour chaque section
    gamma_beta : float, optional
        Facteur d'obliquité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Résultats avec débit et pente équivalente
    
    Examples
    --------
    >>> # Structure avec 3 pentes : 1:3 jusqu'à 0m, 1:2 de 0 à 2m, 1:1.5 au-dessus
    >>> slopes = [
    ...     {'alpha_deg': 18.4, 'h_start': -5, 'h_end': 0},
    ...     {'alpha_deg': 26.6, 'h_start': 0, 'h_end': 2},
    ...     {'alpha_deg': 33.7, 'h_start': 2, 'h_end': 5}
    ... ]
    >>> result = multi_slope_structure(2.5, 6.0, 10.0, 4.0, slopes)
    
    References
    ----------
    EurOtop (2018) - Annexe B.3.1
    """
    # Si gamma_f non fourni, utiliser 1.0 pour toutes les sections
    if gamma_f_sections is None:
        gamma_f_sections = [1.0] * len(slopes_config)
    
    # Calcul de la pente équivalente
    # Méthode : pondération par la longueur de run-up attendue
    
    # Estimation du run-up sans revanche (pour avoir une idée de la zone active)
    from openeurotop.run_up import run_up_2percent_smooth_slope
    Ru_estimate = run_up_2percent_smooth_slope(Hm0, Tm_10, np.mean([s['alpha_deg'] for s in slopes_config]), h, g)
    
    # Identifier les sections actives (entre SWL et Ru_estimate)
    total_length = 0
    weighted_tan_alpha = 0
    weighted_gamma_f = 0
    
    for i, slope in enumerate(slopes_config):
        h_start = max(slope['h_start'], 0)  # Commence au SWL minimum
        h_end = min(slope['h_end'], Ru_estimate)  # Se termine au run-up max
        
        if h_end > h_start:
            # Cette section est active
            delta_h = h_end - h_start
            alpha_rad = slope['alpha_deg'] * DEG_TO_RAD
            length_section = delta_h / np.sin(alpha_rad)  # Longueur le long de la pente
            
            total_length += length_section
            weighted_tan_alpha += np.tan(alpha_rad) * length_section
            weighted_gamma_f += gamma_f_sections[i] * length_section
    
    if total_length > 0:
        # Pente équivalente
        tan_alpha_eq = weighted_tan_alpha / total_length
        alpha_eq_deg = np.arctan(tan_alpha_eq) / DEG_TO_RAD
        
        # Rugosité équivalente
        gamma_f_eq = weighted_gamma_f / total_length
    else:
        # Cas dégénéré : utiliser la dernière pente
        alpha_eq_deg = slopes_config[-1]['alpha_deg']
        gamma_f_eq = gamma_f_sections[-1]
    
    # Calcul du franchissement avec paramètres équivalents
    q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_eq_deg,
                                gamma_f=gamma_f_eq, gamma_beta=gamma_beta, g=g)
    
    return {
        'q': q,
        'alpha_equivalent_deg': alpha_eq_deg,
        'gamma_f_equivalent': gamma_f_eq,
        'active_length': total_length,
        'Ru_estimate': Ru_estimate
    }


def very_steep_slope(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=1.0, g=G):
    """
    Franchissement pour pentes très raides (α > 60°)
    
    Pour les pentes très raides, le comportement se rapproche d'un mur vertical
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc : float
        Paramètres standard
    alpha_deg : float
        Angle de pente (degrés), devrait être > 60°
    gamma_f : float, optional
        Facteur de rugosité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Débit de franchissement q (m³/s/m)
    
    References
    ----------
    EurOtop (2018) - Section 5.4.3
    """
    if alpha_deg < 60:
        # Utiliser formule standard pour talus
        return overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=gamma_f, g=g)
    
    # Pour α > 60°, interpolation entre talus et mur vertical
    # Calculer les deux valeurs
    q_slope = overtopping.digue_talus(Hm0, Tm_10, h, Rc, 60.0, gamma_f=gamma_f, g=g)
    q_wall = overtopping.mur_vertical(Hm0, Tm_10, h, Rc, g=g)
    
    # Interpolation linéaire entre 60° et 90°
    if alpha_deg >= 90:
        return q_wall
    else:
        weight = (alpha_deg - 60) / 30  # 0 à 60°, 1 à 90°
        q = (1 - weight) * q_slope + weight * q_wall
        return q


def very_gentle_slope(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=1.0, g=G):
    """
    Franchissement pour pentes très douces (α < 10°)
    
    Pour les pentes très douces, les formules standards deviennent moins fiables.
    Utilisation d'une correction empirique.
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc : float
        Paramètres standard
    alpha_deg : float
        Angle de pente (degrés), devrait être < 10°
    gamma_f : float, optional
        Facteur de rugosité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Débit de franchissement q (m³/s/m)
    
    References
    ----------
    EurOtop (2018) - Section 5.4.4
    """
    if alpha_deg >= 10:
        # Utiliser formule standard
        return overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=gamma_f, g=g)
    
    # Pour α < 10°, correction
    # Formule standard peut surestimer
    q_standard = overtopping.digue_talus(Hm0, Tm_10, h, Rc, 10.0, gamma_f=gamma_f, g=g)
    
    # Facteur de correction empirique pour pentes douces
    correction_factor = (alpha_deg / 10.0)**0.5  # Réduction pour pentes plus douces
    
    q = q_standard * correction_factor
    
    return q


def stepped_revetment(Hm0, Tm_10, h, Rc, alpha_avg_deg, step_height, 
                     step_width, n_steps, gamma_f_base=1.0, g=G):
    """
    Franchissement pour revêtement en escalier
    
    Les marches créent une rugosité supplémentaire
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc : float
        Paramètres standard
    alpha_avg_deg : float
        Angle de pente moyen (degrés)
    step_height : float
        Hauteur de chaque marche (m)
    step_width : float
        Largeur de chaque marche (m)
    n_steps : int
        Nombre de marches
    gamma_f_base : float, optional
        Rugosité de base du matériau
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Résultats avec gamma_f équivalent
    
    References
    ----------
    EurOtop (2018) - Annexe B.4
    """
    # Rugosité supplémentaire due aux marches
    # Dépend du rapport hauteur/longueur d'onde
    L0 = wave_parameters.wave_length_deep_water(Tm_10, g)
    
    # Rugosité relative des marches
    roughness_ratio = step_height / Hm0
    
    if roughness_ratio < 0.01:
        # Marches négligeables
        gamma_f_steps = 1.0
    elif roughness_ratio < 0.1:
        # Marches modérées
        gamma_f_steps = 1.0 - 0.2 * (roughness_ratio / 0.1)
    else:
        # Marches importantes
        gamma_f_steps = 0.8
    
    # Rugosité totale
    gamma_f_total = gamma_f_base * gamma_f_steps
    
    # Calcul du franchissement
    q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_avg_deg, 
                                gamma_f=gamma_f_total, g=g)
    
    return {
        'q': q,
        'gamma_f_steps': gamma_f_steps,
        'gamma_f_total': gamma_f_total,
        'roughness_ratio': roughness_ratio
    }


def overhanging_wall(Hm0, Tm_10, h, Rc, overhang_length, gamma_f=1.0, g=G):
    """
    Franchissement pour mur avec surplomb (angle > 90°)
    
    Le surplomb réduit significativement le franchissement
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc : float
        Paramètres standard
    overhang_length : float
        Longueur du surplomb horizontal (m)
    gamma_f : float, optional
        Facteur de rugosité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Résultats avec facteur de réduction du surplomb
    
    References
    ----------
    EurOtop (2018) - Section 5.4.5
    """
    # Franchissement sans surplomb
    q_no_overhang = overtopping.mur_vertical(Hm0, Tm_10, h, Rc, g=g)
    
    # Réduction due au surplomb
    overhang_ratio = overhang_length / Hm0
    
    if overhang_ratio < 0.1:
        gamma_overhang = 1.0
    elif overhang_ratio < 0.5:
        gamma_overhang = 1.0 - 0.5 * ((overhang_ratio - 0.1) / 0.4)
    else:
        gamma_overhang = 0.5  # Réduction de 50% pour surplomb important
    
    q = q_no_overhang * gamma_overhang
    
    return {
        'q': q,
        'gamma_overhang': gamma_overhang,
        'overhang_ratio': overhang_ratio,
        'q_no_overhang': q_no_overhang
    }


def shallow_water_correction(Hm0, Tm_10, h, Rc, alpha_deg, breaking_index=0.5, g=G):
    """
    Correction pour eau très peu profonde avec déferlement
    
    En eau peu profonde, les vagues déferlent avant d'atteindre la structure,
    réduisant le franchissement.
    
    Parameters
    ----------
    Hm0, Tm_10, h : float
        Paramètres de vague et profondeur
    Rc : float
        Revanche (m)
    alpha_deg : float
        Angle de pente (degrés)
    breaking_index : float, optional
        Indice de déferlement γ = H/h (typiquement 0.4-0.6)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Résultats avec hauteur de vague corrigée
    
    References
    ----------
    EurOtop (2018) - Section 5.4.6
    """
    # Critère de déferlement : Hm0 > γ * h
    H_breaking = breaking_index * h
    
    if Hm0 <= H_breaking:
        # Pas de déferlement, utiliser Hm0 directement
        Hm0_corrected = Hm0
        correction_applied = False
    else:
        # Déferlement : réduire la hauteur de vague
        Hm0_corrected = H_breaking
        correction_applied = True
    
    # Calcul avec hauteur corrigée
    q = overtopping.digue_talus(Hm0_corrected, Tm_10, h, Rc, alpha_deg, g=g)
    
    return {
        'q': q,
        'Hm0_original': Hm0,
        'Hm0_corrected': Hm0_corrected,
        'H_breaking': H_breaking,
        'correction_applied': correction_applied,
        'depth_ratio': h / Hm0
    }


def complex_geometry_equivalent(geometry_description, Hm0, Tm_10, h, Rc, g=G):
    """
    Approche générale pour géométries complexes via paramètres équivalents
    
    Cette fonction aide à déterminer les paramètres équivalents pour des
    géométries complexes non couvertes par les formules standard.
    
    Parameters
    ----------
    geometry_description : dict
        Description de la géométrie avec clés :
        - 'type': type de structure
        - 'slopes': liste d'angles de pente
        - 'roughness': liste de rugosités
        - 'berms': informations sur les bermes
        etc.
    Hm0, Tm_10, h, Rc : float
        Paramètres standard
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Recommandations et calculs avec paramètres équivalents
    
    Notes
    -----
    Cette fonction fournit une approche conservatrice pour les cas complexes.
    Pour des projets critiques, des essais physiques sont recommandés.
    """
    recommendations = {
        'approach': 'equivalent_parameters',
        'warnings': [],
        'q_conservative': None,
        'q_optimistic': None,
        'recommendation': None
    }
    
    # Analyser la complexité
    if 'slopes' in geometry_description and len(geometry_description['slopes']) > 2:
        recommendations['warnings'].append(
            "Géométrie à pentes multiples : utiliser multi_slope_structure()"
        )
    
    if 'berms' in geometry_description and len(geometry_description.get('berms', [])) > 1:
        recommendations['warnings'].append(
            "Plusieurs bermes : formules standard limitées, essais recommandés"
        )
    
    # Estimation conservative : utiliser paramètres les plus défavorables
    if 'slopes' in geometry_description:
        alpha_min = min(geometry_description['slopes'])
        alpha_max = max(geometry_description['slopes'])
        
        # Calcul optimiste (pente raide)
        q_opt = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_max, g=g)
        
        # Calcul conservateur (pente douce)
        q_cons = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_min, g=g)
        
        recommendations['q_optimistic'] = q_opt
        recommendations['q_conservative'] = q_cons
        recommendations['recommendation'] = (
            f"Pour conception, utiliser q = {q_cons:.6f} m³/s/m (conservateur). "
            f"Plage attendue : [{q_opt:.6f}, {q_cons:.6f}] m³/s/m"
        )
    
    return recommendations


def extreme_conditions_check(Hm0, Tm_10, h, Rc, alpha_deg):
    """
    Vérifie si les conditions sont dans le domaine de validité d'EurOtop
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc, alpha_deg : float
        Paramètres de la structure et des vagues
    
    Returns
    -------
    dict
        Résultats de validation avec warnings
    
    Examples
    --------
    >>> check = extreme_conditions_check(2.5, 6.0, 10.0, 3.0, 35.0)
    >>> if check['valid']:
    ...     print("Conditions valides")
    >>> else:
    ...     print("Warnings:", check['warnings'])
    """
    warnings = []
    valid = True
    
    # Vérifier Rc/Hm0
    Rc_Hm0 = Rc / Hm0
    if Rc_Hm0 < 0.5:
        warnings.append(f"Rc/Hm0 = {Rc_Hm0:.2f} < 0.5 : hors domaine de validité (submersion)")
        valid = False
    elif Rc_Hm0 > 3.5:
        warnings.append(f"Rc/Hm0 = {Rc_Hm0:.2f} > 3.5 : extrapolation, incertitudes élevées")
    
    # Vérifier l'angle de pente
    if alpha_deg < 10:
        warnings.append(f"Pente {alpha_deg}° < 10° : formules moins fiables, utiliser very_gentle_slope()")
    elif alpha_deg > 60 and alpha_deg < 90:
        warnings.append(f"Pente {alpha_deg}° > 60° : proche du vertical, utiliser very_steep_slope()")
    
    # Vérifier le nombre d'Iribarren
    xi = wave_parameters.iribarren_number(alpha_deg, Hm0, Tm_10)
    if xi < 1.0:
        warnings.append(f"Nombre d'Iribarren {xi:.2f} < 1.0 : vagues très déferlantes")
    elif xi > 7.0:
        warnings.append(f"Nombre d'Iribarren {xi:.2f} > 7.0 : vagues très non-déferlantes, rare")
    
    # Vérifier la profondeur relative
    h_Hm0 = h / Hm0
    if h_Hm0 < 2.0:
        warnings.append(f"h/Hm0 = {h_Hm0:.2f} < 2.0 : eau peu profonde, déferlement probable")
    
    # Vérifier la cambrure
    s0 = wave_parameters.wave_steepness(Hm0, Tm_10)
    if s0 < 0.01:
        warnings.append(f"Cambrure s0 = {s0:.4f} < 0.01 : vagues très plates, inhabituel")
    elif s0 > 0.06:
        warnings.append(f"Cambrure s0 = {s0:.4f} > 0.06 : vagues très cambrées, mer du vent")
    
    return {
        'valid': valid,
        'warnings': warnings,
        'Rc_Hm0': Rc_Hm0,
        'xi': xi,
        'h_Hm0': h_Hm0,
        's0': s0
    }

