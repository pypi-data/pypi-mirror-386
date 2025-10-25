"""
Calcul des paramètres de vagues selon EurOtop
"""

import numpy as np
from openeurotop.constants import G, DEG_TO_RAD


def wave_length_deep_water(T, g=G):
    """
    Calcule la longueur d'onde en eau profonde
    
    Parameters
    ----------
    T : float
        Période de vague (s)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Longueur d'onde en eau profonde L0 (m)
    """
    return (g * T**2) / (2 * np.pi)


def wave_length(T, h, g=G, max_iter=100, tol=1e-6):
    """
    Calcule la longueur d'onde pour une profondeur donnée
    en résolvant la relation de dispersion
    
    Parameters
    ----------
    T : float
        Période de vague (s)
    h : float
        Profondeur d'eau (m)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    max_iter : int, optional
        Nombre maximum d'itérations
    tol : float, optional
        Tolérance pour la convergence
    
    Returns
    -------
    float
        Longueur d'onde L (m)
    """
    L0 = wave_length_deep_water(T, g)
    L = L0  # Initialisation
    
    omega = 2 * np.pi / T
    
    for _ in range(max_iter):
        k = 2 * np.pi / L
        L_new = (g * T**2) / (2 * np.pi) * np.tanh(k * h)
        
        if abs(L_new - L) < tol:
            return L_new
        
        L = L_new
    
    return L


def wave_steepness(Hm0, Tm_10, g=G):
    """
    Calcule la cambrure de la vague (wave steepness)
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période moyenne spectrale (s)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Cambrure s0m-1,0 = Hm0 / L0m-1,0
    """
    L0 = wave_length_deep_water(Tm_10, g)
    return Hm0 / L0


def iribarren_number(alpha_deg, Hm0, Tm_10, g=G):
    """
    Calcule le nombre d'Iribarren (surf similarity parameter)
    
    ξm-1,0 = tan(α) / sqrt(s0m-1,0)
    
    Parameters
    ----------
    alpha_deg : float
        Angle de la pente (degrés)
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période moyenne spectrale (s)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Nombre d'Iribarren ξm-1,0
    """
    alpha_rad = alpha_deg * DEG_TO_RAD
    tan_alpha = np.tan(alpha_rad)
    s0 = wave_steepness(Hm0, Tm_10, g)
    
    return tan_alpha / np.sqrt(s0)


def breaker_parameter(alpha_deg, Hm0, Lm_10):
    """
    Calcule le paramètre de déferlement
    
    Parameters
    ----------
    alpha_deg : float
        Angle de la pente (degrés)
    Hm0 : float
        Hauteur significative spectrale (m)
    Lm_10 : float
        Longueur d'onde (m)
    
    Returns
    -------
    float
        Paramètre de déferlement ξm-1,0
    """
    alpha_rad = alpha_deg * DEG_TO_RAD
    tan_alpha = np.tan(alpha_rad)
    s0 = Hm0 / Lm_10
    
    return tan_alpha / np.sqrt(s0)


def dimensionless_freeboard(Rc, Hm0):
    """
    Calcule la revanche adimensionnelle
    
    Parameters
    ----------
    Rc : float
        Revanche (m)
    Hm0 : float
        Hauteur significative spectrale (m)
    
    Returns
    -------
    float
        Revanche adimensionnelle Rc/Hm0
    """
    return Rc / Hm0


def spectral_period_conversion(Tp=None, Tm_10=None, Tm01=None):
    """
    Conversion entre différentes périodes spectrales
    
    Relations approximatives :
    Tm-1,0 ≈ 1.1 * Tm0,1
    Tp ≈ 1.2 * Tm-1,0
    
    Parameters
    ----------
    Tp : float, optional
        Période de pic (s)
    Tm_10 : float, optional
        Période spectrale Tm-1,0 (s)
    Tm01 : float, optional
        Période spectrale Tm0,1 (s)
    
    Returns
    -------
    dict
        Dictionnaire avec les périodes calculées
    """
    result = {}
    
    if Tp is not None:
        result['Tp'] = Tp
        result['Tm_10'] = Tp / 1.2
        result['Tm01'] = Tp / (1.1 * 1.2)
    elif Tm_10 is not None:
        result['Tm_10'] = Tm_10
        result['Tp'] = Tm_10 * 1.2
        result['Tm01'] = Tm_10 / 1.1
    elif Tm01 is not None:
        result['Tm01'] = Tm01
        result['Tm_10'] = Tm01 * 1.1
        result['Tp'] = Tm01 * 1.1 * 1.2
    
    return result


def relative_water_depth(h, Tm_10, g=G):
    """
    Calcule la profondeur relative h/L
    
    Parameters
    ----------
    h : float
        Profondeur d'eau (m)
    Tm_10 : float
        Période spectrale (s)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Profondeur relative h/L
    """
    L = wave_length(Tm_10, h, g)
    return h / L

