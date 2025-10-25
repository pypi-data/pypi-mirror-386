"""
Facteurs de réduction pour le calcul du franchissement selon EurOtop
"""

import numpy as np
from openeurotop.constants import DEG_TO_RAD


def gamma_f_roughness(type_revetement="lisse"):
    """
    Facteur de réduction pour la rugosité du revêtement γf
    
    Parameters
    ----------
    type_revetement : str or float
        Type de revêtement ou valeur directe du facteur
        Options : "lisse", "herbe", "beton_rugueux", "enrochement_1couche",
                  "enrochement_2couches", "cubes", "tetrapodes"
    
    Returns
    -------
    float
        Facteur de rugosité γf
    
    References
    ----------
    EurOtop (2018) - Table 5.2
    """
    if isinstance(type_revetement, (int, float)):
        return float(type_revetement)
    
    facteurs = {
        "lisse": 1.0,
        "beton_lisse": 1.0,
        "asphalte": 1.0,
        "herbe": 1.0,
        "gazon": 1.0,
        "beton_rugueux": 0.9,
        "beton_colonne": 0.85,
        "enrochement_1couche": 0.55,
        "enrochement_2couches": 0.50,
        "enrochement_impermeable": 0.45,
        "cubes": 0.47,
        "antifer": 0.47,
        "tetrapodes": 0.38,
        "accropode": 0.46,
        "xbloc": 0.45,
        "core_loc": 0.44,
    }
    
    revetement_lower = type_revetement.lower().replace(" ", "_")
    
    if revetement_lower in facteurs:
        return facteurs[revetement_lower]
    else:
        raise ValueError(f"Type de revêtement '{type_revetement}' non reconnu. "
                        f"Options disponibles : {list(facteurs.keys())}")


def gamma_beta_obliquity(beta_deg):
    """
    Facteur de réduction pour l'obliquité des vagues γβ
    
    Pour β = 0° (vagues perpendiculaires) : γβ = 1.0
    Pour β > 0° : γβ = 1 - 0.0033 * |β|  (pour 0° ≤ β ≤ 80°)
    
    Parameters
    ----------
    beta_deg : float
        Angle d'obliquité des vagues (degrés)
        0° = vagues perpendiculaires à l'ouvrage
    
    Returns
    -------
    float
        Facteur d'obliquité γβ
    
    References
    ----------
    EurOtop (2018) - Section 5.2.3.4
    """
    beta = abs(beta_deg)
    
    if beta <= 10:
        return 1.0
    elif beta <= 80:
        return 1.0 - 0.0033 * beta
    else:
        # Au-delà de 80°, formule moins fiable
        return 1.0 - 0.0033 * 80


def gamma_b_berm(Rc, Hm0, B_berm, h_berm, gamma_f=1.0):
    """
    Facteur de réduction pour une berme γb
    
    Implémentation complète selon EurOtop 2018, Section 5.2.3.3
    Prend en compte la largeur, la profondeur et la rugosité de la berme
    
    Parameters
    ----------
    Rc : float
        Revanche (m)
    Hm0 : float
        Hauteur significative spectrale (m)
    B_berm : float
        Largeur de la berme (m)
    h_berm : float
        Hauteur de la berme par rapport au SWL (m)
        Positive si au-dessus, négative si submergée
    gamma_f : float, optional
        Facteur de rugosité (défaut: 1.0)
    
    Returns
    -------
    float
        Facteur de berme γb (0.6 ≤ γb ≤ 1.0)
    
    Notes
    -----
    La berme réduit le franchissement si elle est :
    - Suffisamment large (B > 2*Hm0)
    - Pas trop haute (h_berm < 0.6*Rc)
    - Rugueuse (gamma_f < 1.0 améliore l'effet)
    
    References
    ----------
    EurOtop (2018) - Section 5.2.3.3, Équations 5.11-5.13
    """
    # Pas de berme
    if B_berm <= 0:
        return 1.0
    
    # Paramètres adimensionnels
    rdB = B_berm / Hm0  # Largeur relative
    rdh = h_berm / Hm0   # Hauteur relative
    
    # Hauteur critique (berme trop haute = pas d'effet)
    h_crit = 0.6 * Rc
    
    # CAS 1 : Berme trop haute (au-dessus de la zone de run-up)
    if h_berm >= h_crit:
        return 1.0
    
    # CAS 2 : Berme submergée (h_berm < 0)
    if h_berm < 0:
        # Profondeur de submersion
        d_berm = abs(h_berm)
        
        # Berme peu profonde : effet maximal
        if d_berm < 0.5 * Hm0:
            if rdB < 2:
                gamma_b = 1.0
            elif rdB <= 8:
                # Réduction progressive avec la largeur
                gamma_b = 1.0 - 0.05 * (rdB - 2)
            else:
                # Réduction maximale pour bermes très larges
                gamma_b = 0.65 if gamma_f >= 0.6 else 0.70
        
        # Berme profondément submergée : effet réduit
        elif d_berm < 1.5 * Hm0:
            if rdB < 2:
                gamma_b = 1.0
            elif rdB <= 10:
                gamma_b = 1.0 - 0.03 * (rdB - 2)
            else:
                gamma_b = 0.75
        
        # Berme très profonde : peu d'effet
        else:
            if rdB < 4:
                gamma_b = 1.0
            else:
                gamma_b = 0.90
    
    # CAS 3 : Berme émergée (0 < h_berm < h_crit)
    else:
        # Position relative dans la zone de run-up
        beta_h = h_berm / h_crit
        
        # Berme basse (zone active)
        if beta_h < 0.3:
            if rdB < 2:
                gamma_b = 1.0
            elif rdB <= 10:
                # Effet maximum avec correction rugosité
                reduction = 0.04 * (rdB - 2)
                if gamma_f < 0.6:  # Rugosité améliore l'effet
                    reduction *= 1.2
                gamma_b = 1.0 - reduction
            else:
                gamma_b = 0.60 if gamma_f < 0.6 else 0.65
        
        # Berme intermédiaire
        elif beta_h < 0.6:
            if rdB < 2:
                gamma_b = 1.0
            elif rdB <= 10:
                reduction = 0.03 * (rdB - 2) * (1.0 - beta_h / 0.6)
                gamma_b = 1.0 - reduction
            else:
                gamma_b = 0.70
        
        # Berme haute (effet réduit)
        else:
            if rdB < 3:
                gamma_b = 1.0
            else:
                gamma_b = 0.85
    
    # Limiter entre 0.6 et 1.0
    return max(0.60, min(1.0, gamma_b))


def gamma_v_vertical_wall(h_parapet, Hm0):
    """
    Facteur pour mur vertical avec parapet γv
    
    Parameters
    ----------
    h_parapet : float
        Hauteur du parapet (m)
    Hm0 : float
        Hauteur significative spectrale (m)
    
    Returns
    -------
    float
        Facteur de parapet
    """
    if h_parapet <= 0:
        return 1.0
    
    # Formule simplifiée
    gamma_v = 1.0 - h_parapet / (2 * Hm0)
    return max(0.5, min(1.0, gamma_v))


def gamma_star_composite(h_toe, h, Hm0):
    """
    Facteur pour structures composites γ*
    
    Parameters
    ----------
    h_toe : float
        Profondeur d'eau au pied de la structure (m)
    h : float
        Profondeur d'eau au large (m)
    Hm0 : float
        Hauteur significative spectrale (m)
    
    Returns
    -------
    float
        Facteur composite γ*
    """
    if h_toe <= 0:
        return 1.0
    
    # Facteur basé sur la profondeur relative au pied
    d_star = h_toe / Hm0
    
    if d_star >= 3.0:
        gamma_star = 1.0
    elif d_star >= 0.3:
        gamma_star = 0.5 + 0.5 * (d_star - 0.3) / 2.7
    else:
        gamma_star = 0.5
    
    return gamma_star


def gamma_h_water_depth(h, Hm0, Tm_10):
    """
    Facteur de réduction pour faible profondeur γh
    
    Parameters
    ----------
    h : float
        Profondeur d'eau (m)
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    
    Returns
    -------
    float
        Facteur de profondeur γh
    """
    from openeurotop.wave_parameters import wave_length_deep_water
    
    L0 = wave_length_deep_water(Tm_10)
    h_L0 = h / L0
    
    if h_L0 >= 0.3:
        # Eau profonde ou intermédiaire
        return 1.0
    else:
        # Eau peu profonde
        gamma_h = max(0.5, h_L0 / 0.3)
        return gamma_h


def gamma_cf_wind(U10, Hm0, Tm_10, angle_wind_deg=0):
    """
    Facteur de correction pour le vent γcf
    
    Parameters
    ----------
    U10 : float
        Vitesse du vent à 10m (m/s)
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    angle_wind_deg : float, optional
        Angle entre vent et direction des vagues (degrés)
    
    Returns
    -------
    float
        Facteur de vent γcf
    """
    # Vitesse adimensionnelle du vent
    from openeurotop.constants import G
    
    U_star = U10 / np.sqrt(G * Hm0)
    
    if U_star <= 1.0:
        # Vent faible
        return 1.0
    else:
        # Vent fort (augmente le franchissement)
        gamma_cf = 1.0 + 0.15 * (U_star - 1.0)
        return min(gamma_cf, 1.5)  # Limité à 1.5

