"""
Calcul du run-up selon EurOtop (2018) - Chapitre 6

Le run-up est la montée maximale de l'eau sur une structure lors du passage d'une vague.
Ru2% représente le run-up dépassé par 2% des vagues (valeur caractéristique).
"""

import numpy as np
from openeurotop.constants import G, DEG_TO_RAD
from openeurotop.wave_parameters import iribarren_number, wave_length_deep_water


def run_up_2percent_smooth_slope(Hm0, Tm_10, alpha_deg, h=None, g=G):
    """
    Calcul du run-up Ru2% pour une pente lisse
    
    EurOtop 2018 - Équations 6.1 et 6.2
    
    Pour ξm-1,0 < 1.8 (déferlant) : Ru2% / Hm0 = 1.5 · γf · γβ · ξm-1,0
    Pour ξm-1,0 ≥ 1.8 (non-déferlant) : Ru2% / Hm0 = γf · γβ · (4.0 - 1.5/ξm-1,0)
    
    avec maximum Ru2% / Hm0 ≤ γf · γβ · 4.0
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale Tm-1,0 (s)
    alpha_deg : float
        Angle de pente (degrés)
    h : float, optional
        Profondeur d'eau (m) - pour correction shallow water si besoin
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Run-up Ru2% (m)
    
    References
    ----------
    EurOtop (2018) - Section 6.2, Équations 6.1 et 6.2
    """
    # Calcul du nombre d'Iribarren
    xi = iribarren_number(alpha_deg, Hm0, Tm_10, g)
    
    # Facteurs de réduction (par défaut 1.0 pour pente lisse)
    gamma_f = 1.0
    gamma_beta = 1.0
    gamma = gamma_f * gamma_beta
    
    # Formule selon le régime de déferlement
    if xi < 1.8:
        # Vagues déferlantes
        Ru2_Hm0 = 1.5 * gamma * xi
    else:
        # Vagues non-déferlantes
        Ru2_Hm0 = gamma * (4.0 - 1.5 / xi)
    
    # Limite supérieure
    Ru2_Hm0 = min(Ru2_Hm0, 4.0 * gamma)
    
    # Ru2% absolu
    Ru2 = Ru2_Hm0 * Hm0
    
    return Ru2


def run_up_2percent_rough_slope(Hm0, Tm_10, alpha_deg, gamma_f, gamma_beta=1.0, h=None, g=G):
    """
    Calcul du run-up Ru2% pour une pente rugueuse
    
    EurOtop 2018 - Équations 6.1 et 6.2 avec facteurs de réduction
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale Tm-1,0 (s)
    alpha_deg : float
        Angle de pente (degrés)
    gamma_f : float
        Facteur de rugosité (voir reduction_factors.gamma_f_roughness)
    gamma_beta : float, optional
        Facteur d'obliquité (défaut: 1.0)
    h : float, optional
        Profondeur d'eau (m)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Run-up Ru2% (m)
    
    References
    ----------
    EurOtop (2018) - Section 6.2
    """
    # Calcul du nombre d'Iribarren
    xi = iribarren_number(alpha_deg, Hm0, Tm_10, g)
    
    # Facteur de réduction total
    gamma = gamma_f * gamma_beta
    
    # Formule selon le régime
    if xi < 1.8:
        Ru2_Hm0 = 1.5 * gamma * xi
    else:
        Ru2_Hm0 = gamma * (4.0 - 1.5 / xi)
    
    # Limite supérieure
    Ru2_Hm0 = min(Ru2_Hm0, 4.0 * gamma)
    
    return Ru2_Hm0 * Hm0


def run_up_distribution_parameters(Hm0, Tm_10, alpha_deg, gamma_f=1.0, gamma_beta=1.0, g=G):
    """
    Calcule les paramètres de la distribution du run-up
    
    Le run-up suit une distribution de Rayleigh :
    P(Ru > z) = exp(-(z / a)²)
    
    où a est le paramètre d'échelle
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    alpha_deg : float
        Angle de pente (degrés)
    gamma_f : float, optional
        Facteur de rugosité
    gamma_beta : float, optional
        Facteur d'obliquité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Dictionnaire avec :
        - 'Ru2' : Run-up 2%
        - 'a' : Paramètre d'échelle de Rayleigh
        - 'Ru_mean' : Run-up moyen
        - 'Ru_max' : Run-up maximum (théorique)
    
    References
    ----------
    EurOtop (2018) - Section 6.3
    """
    # Ru2%
    Ru2 = run_up_2percent_rough_slope(Hm0, Tm_10, alpha_deg, gamma_f, gamma_beta, g=g)
    
    # Paramètre d'échelle de Rayleigh
    # Ru2% correspond au quantile 2% : P(Ru > Ru2%) = 0.02
    # Pour Rayleigh : exp(-(Ru2/a)²) = 0.02
    # Donc : a = Ru2 / sqrt(-ln(0.02))
    a = Ru2 / np.sqrt(-np.log(0.02))
    
    # Run-up moyen pour distribution de Rayleigh
    Ru_mean = a * np.sqrt(np.pi / 2)
    
    # Run-up maximum théorique (99.9%)
    Ru_max = a * np.sqrt(-np.log(0.001))
    
    return {
        'Ru2': Ru2,
        'a': a,
        'Ru_mean': Ru_mean,
        'Ru_max': Ru_max
    }


def run_up_exceedance_probability(z, Hm0, Tm_10, alpha_deg, gamma_f=1.0, gamma_beta=1.0, g=G):
    """
    Calcule la probabilité de dépassement d'un niveau de run-up donné
    
    P(Ru > z) = exp(-(z/a)²)
    
    Parameters
    ----------
    z : float or array_like
        Niveau de run-up à évaluer (m)
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    alpha_deg : float
        Angle de pente (degrés)
    gamma_f : float, optional
        Facteur de rugosité
    gamma_beta : float, optional
        Facteur d'obliquité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float or array_like
        Probabilité de dépassement P(Ru > z)
    
    Examples
    --------
    >>> # Probabilité que le run-up dépasse 3m
    >>> P = run_up_exceedance_probability(3.0, Hm0=2.5, Tm_10=6.0, alpha_deg=35.0)
    """
    params = run_up_distribution_parameters(Hm0, Tm_10, alpha_deg, gamma_f, gamma_beta, g)
    a = params['a']
    
    z = np.asarray(z)
    P = np.exp(-(z / a)**2)
    
    return P


def run_up_with_berm(Hm0, Tm_10, alpha_lower_deg, alpha_upper_deg, 
                     h_berm, B_berm, gamma_f=1.0, gamma_beta=1.0, g=G):
    """
    Calcul du run-up pour une structure avec berme
    
    La berme réduit le run-up selon sa largeur et sa hauteur.
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    alpha_lower_deg : float
        Angle de pente inférieure (degrés)
    alpha_upper_deg : float
        Angle de pente supérieure (degrés)
    h_berm : float
        Hauteur de la berme au-dessus du SWL (m)
    B_berm : float
        Largeur de la berme (m)
    gamma_f : float, optional
        Facteur de rugosité
    gamma_beta : float, optional
        Facteur d'obliquité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Run-up Ru2% (m)
    
    References
    ----------
    EurOtop (2018) - Section 6.4
    """
    # Run-up sans berme (pente inférieure)
    Ru2_no_berm = run_up_2percent_rough_slope(Hm0, Tm_10, alpha_lower_deg, 
                                              gamma_f, gamma_beta, g=g)
    
    # Si la berme est haute, elle arrête le run-up
    if h_berm >= Ru2_no_berm:
        return h_berm
    
    # Facteur de réduction dû à la berme
    # Largeur relative de la berme
    rdB = B_berm / Hm0
    
    if rdB < 2:
        # Berme étroite, peu d'effet
        gamma_b_runup = 1.0
    elif rdB <= 10:
        # Berme intermédiaire
        gamma_b_runup = 1.0 - 0.03 * (rdB - 2)
    else:
        # Berme large
        gamma_b_runup = 0.76
    
    # Run-up avec berme
    Ru2_with_berm = gamma_b_runup * Ru2_no_berm
    
    # Ne peut pas être inférieur à la hauteur de la berme
    Ru2_with_berm = max(Ru2_with_berm, h_berm)
    
    return Ru2_with_berm


def run_up_vertical_wall(Hm0, Tm_10, h, h_wall, g=G):
    """
    Calcul du run-up pour un mur vertical
    
    EurOtop 2018 - Section 6.5
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    h : float
        Profondeur d'eau au pied du mur (m)
    h_wall : float
        Hauteur du mur (m)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Run-up Ru2% (m)
    
    References
    ----------
    EurOtop (2018) - Section 6.5
    """
    # Pour mur vertical, le run-up dépend de la profondeur relative
    d_star = h / Hm0
    
    # Formule pour mur vertical (simplifiée)
    if d_star > 3.0:
        # Eau profonde
        Ru2_Hm0 = 1.5
    elif d_star > 0.5:
        # Eau intermédiaire
        Ru2_Hm0 = 1.5 - 0.3 * (3.0 - d_star)
    else:
        # Eau peu profonde
        Ru2_Hm0 = 0.9
    
    Ru2 = Ru2_Hm0 * Hm0
    
    # Limité par la hauteur du mur
    Ru2 = min(Ru2, h_wall)
    
    return Ru2


def run_up_composite_structure(Hm0, Tm_10, alpha_lower_deg, h_transition, 
                               h_wall, gamma_f_lower=1.0, gamma_beta=1.0, g=G):
    """
    Calcul du run-up pour une structure composite (talus + mur)
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    alpha_lower_deg : float
        Angle de pente inférieure (degrés)
    h_transition : float
        Hauteur de la transition (m au-dessus SWL)
    h_wall : float
        Hauteur totale de la structure (m)
    gamma_f_lower : float, optional
        Facteur de rugosité de la pente inférieure
    gamma_beta : float, optional
        Facteur d'obliquité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Run-up Ru2% (m)
    
    References
    ----------
    EurOtop (2018) - Section 6.6
    """
    # Run-up sur le talus seul
    Ru2_slope = run_up_2percent_rough_slope(Hm0, Tm_10, alpha_lower_deg, 
                                            gamma_f_lower, gamma_beta, g=g)
    
    # Si le run-up n'atteint pas la transition, pas d'effet du mur
    if Ru2_slope <= h_transition:
        return Ru2_slope
    
    # Sinon, le mur limite le run-up
    # Réduction due au mur (approximation)
    reduction_factor = 0.8  # Le mur réduit le run-up
    
    Ru2_composite = h_transition + reduction_factor * (Ru2_slope - h_transition)
    
    # Limité par la hauteur totale
    Ru2_composite = min(Ru2_composite, h_wall)
    
    return Ru2_composite


def run_down_2percent(Hm0, Tm_10, alpha_deg, gamma_f=1.0, g=G):
    """
    Calcul du run-down Rd2% (descente d'eau)
    
    Le run-down est généralement moins critique que le run-up mais peut
    être important pour la stabilité des blocs ou l'érosion.
    
    Formule empirique : Rd2% ≈ 0.33 · Ru2%
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    alpha_deg : float
        Angle de pente (degrés)
    gamma_f : float, optional
        Facteur de rugosité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Run-down Rd2% (m, valeur négative)
    
    References
    ----------
    EurOtop (2018) - Section 6.7
    """
    # Calcul du run-up
    Ru2 = run_up_2percent_rough_slope(Hm0, Tm_10, alpha_deg, gamma_f, 1.0, g=g)
    
    # Run-down empirique (environ 1/3 du run-up)
    Rd2 = -0.33 * Ru2
    
    return Rd2


def run_up_detailed(Hm0, Tm_10, alpha_deg, type_revetement="lisse", 
                   beta_deg=0.0, h_berm=None, B_berm=None, g=G):
    """
    Calcul détaillé du run-up avec calcul automatique des facteurs
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    alpha_deg : float
        Angle de pente (degrés)
    type_revetement : str, optional
        Type de revêtement (voir reduction_factors.gamma_f_roughness)
    beta_deg : float, optional
        Angle d'obliquité des vagues (degrés)
    h_berm : float, optional
        Hauteur de berme (m)
    B_berm : float, optional
        Largeur de berme (m)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Dictionnaire avec tous les résultats
    
    Examples
    --------
    >>> result = run_up_detailed(Hm0=2.5, Tm_10=6.0, alpha_deg=35.0, 
    ...                          type_revetement="enrochement_2couches")
    >>> print(f"Ru2% = {result['Ru2']:.2f} m")
    """
    from openeurotop.reduction_factors import gamma_f_roughness, gamma_beta_obliquity
    
    # Facteurs de réduction
    gamma_f = gamma_f_roughness(type_revetement)
    gamma_beta = gamma_beta_obliquity(beta_deg)
    
    # Nombre d'Iribarren
    xi = iribarren_number(alpha_deg, Hm0, Tm_10, g)
    
    # Run-up de base
    if h_berm is not None and B_berm is not None:
        # Avec berme (on suppose alpha_upper = alpha_lower)
        Ru2 = run_up_with_berm(Hm0, Tm_10, alpha_deg, alpha_deg, 
                              h_berm, B_berm, gamma_f, gamma_beta, g)
    else:
        # Sans berme
        Ru2 = run_up_2percent_rough_slope(Hm0, Tm_10, alpha_deg, 
                                          gamma_f, gamma_beta, g=g)
    
    # Distribution
    dist_params = run_up_distribution_parameters(Hm0, Tm_10, alpha_deg, 
                                                 gamma_f, gamma_beta, g)
    
    # Run-down
    Rd2 = run_down_2percent(Hm0, Tm_10, alpha_deg, gamma_f, g)
    
    return {
        'Ru2': Ru2,
        'Rd2': Rd2,
        'xi': xi,
        'gamma_f': gamma_f,
        'gamma_beta': gamma_beta,
        'gamma_total': gamma_f * gamma_beta,
        'Ru2_Hm0': Ru2 / Hm0,
        'Ru_mean': dist_params['Ru_mean'],
        'Ru_max': dist_params['Ru_max'],
        'rayleigh_a': dist_params['a']
    }

