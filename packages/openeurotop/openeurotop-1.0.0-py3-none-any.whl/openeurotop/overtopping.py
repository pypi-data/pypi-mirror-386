"""
Méthodes de calcul du franchissement de vagues selon EurOtop (2018)
"""

import numpy as np
from openeurotop.constants import (
    G, DEG_TO_RAD,
    A_TALUS_NON_DEFERLEMENT, B_TALUS_NON_DEFERLEMENT, C_TALUS_NON_DEFERLEMENT,
    A_TALUS_DEFERLEMENT, B_TALUS_DEFERLEMENT,
    A_MUR_VERTICAL, B_MUR_VERTICAL,
    XI_TRANSITION
)
from openeurotop.wave_parameters import iribarren_number, wave_length_deep_water
from openeurotop.reduction_factors import (
    gamma_f_roughness, gamma_beta_obliquity, gamma_b_berm
)


def digue_talus(Hm0, Tm_10, h, Rc, alpha_deg, 
                gamma_b=1.0, gamma_f=1.0, gamma_beta=1.0, 
                method="auto", g=G):
    """
    Calcul du débit de franchissement moyen pour une digue à talus
    
    Formules principales d'EurOtop 2018 :
    - Conditions non-déferlantes (plunging) : q proportionnel à exp(-b*Rc/Hm0)
    - Conditions déferlantes (surging) : q proportionnel à exp(-c*Rc/(Hm0*ξ))
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale moyenne Tm-1,0 (s)
    h : float
        Profondeur d'eau au pied de l'ouvrage (m)
    Rc : float
        Revanche (freeboard) - hauteur de crête au-dessus du SWL (m)
    alpha_deg : float
        Angle de pente du talus (degrés)
    gamma_b : float, optional
        Facteur de réduction pour berme (défaut: 1.0)
    gamma_f : float, optional
        Facteur de réduction pour rugosité (défaut: 1.0)
    gamma_beta : float, optional
        Facteur de réduction pour obliquité (défaut: 1.0)
    method : str, optional
        Méthode de calcul : "auto", "non_deferlement", "deferlement", "both"
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float or dict
        Débit de franchissement moyen q (m³/s/m)
        Si method="both", retourne dict avec les deux valeurs
    
    References
    ----------
    EurOtop (2018) - Equations 5.1 et 5.2
    """
    # Calcul du nombre d'Iribarren
    xi = iribarren_number(alpha_deg, Hm0, Tm_10, g)
    
    # Facteur de réduction combiné
    gamma = gamma_b * gamma_f * gamma_beta
    
    # Revanche adimensionnelle
    Rc_star = Rc / (Hm0 * gamma)
    
    # Formule pour conditions non-déferlantes (plunging/breaking waves)
    # q / sqrt(g*Hm0³) = a * exp(-b * Rc/(γ*Hm0))
    q_plunging = (A_TALUS_NON_DEFERLEMENT * 
                  np.sqrt(g * Hm0**3) * 
                  np.exp(-B_TALUS_NON_DEFERLEMENT * Rc_star))
    
    # Formule pour conditions déferlantes (surging waves)
    # q / sqrt(g*Hm0³) = a * ξ * exp(-c * Rc/(ξ*γ*Hm0))
    if xi > 0:
        Rc_star_surging = Rc / (Hm0 * gamma * xi)
        q_surging = (A_TALUS_DEFERLEMENT * xi * 
                     np.sqrt(g * Hm0**3) * 
                     np.exp(-B_TALUS_DEFERLEMENT * Rc_star_surging))
    else:
        q_surging = 0.0
    
    # Sélection de la méthode
    if method == "non_deferlement":
        return q_plunging
    elif method == "deferlement":
        return q_surging
    elif method == "both":
        return {
            "q_plunging": q_plunging,
            "q_surging": q_surging,
            "q_min": min(q_plunging, q_surging),
            "xi": xi
        }
    else:  # method == "auto"
        # Prendre le minimum des deux formules
        return min(q_plunging, q_surging)


def digue_talus_detailed(Hm0, Tm_10, h, Rc, alpha_deg,
                        type_revetement="lisse",
                        beta_deg=0.0,
                        B_berm=0.0, h_berm=0.0,
                        g=G):
    """
    Calcul détaillé du franchissement pour digue à talus avec calcul automatique
    des facteurs de réduction
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale moyenne Tm-1,0 (s)
    h : float
        Profondeur d'eau (m)
    Rc : float
        Revanche (m)
    alpha_deg : float
        Angle de pente (degrés)
    type_revetement : str, optional
        Type de revêtement (voir gamma_f_roughness)
    beta_deg : float, optional
        Angle d'obliquité des vagues (degrés)
    B_berm : float, optional
        Largeur de berme (m)
    h_berm : float, optional
        Hauteur de berme (m)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Dictionnaire avec q et tous les paramètres calculés
    """
    # Calcul des facteurs de réduction
    gamma_f = gamma_f_roughness(type_revetement)
    gamma_beta = gamma_beta_obliquity(beta_deg)
    gamma_b = gamma_b_berm(Rc, Hm0, B_berm, h_berm, gamma_f)
    
    # Calcul du débit
    q = digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                   gamma_b, gamma_f, gamma_beta, "auto", g)
    
    # Nombre d'Iribarren
    xi = iribarren_number(alpha_deg, Hm0, Tm_10, g)
    
    return {
        "q": q,
        "Hm0": Hm0,
        "Tm_10": Tm_10,
        "Rc": Rc,
        "alpha_deg": alpha_deg,
        "xi": xi,
        "gamma_f": gamma_f,
        "gamma_beta": gamma_beta,
        "gamma_b": gamma_b,
        "gamma_total": gamma_f * gamma_beta * gamma_b,
        "Rc_Hm0": Rc / Hm0
    }


def mur_vertical(Hm0, Tm_10, h, Rc, h_structure=None, 
                 impulsive=True, g=G):
    """
    Calcul du franchissement pour un mur vertical
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    h : float
        Profondeur d'eau au pied du mur (m)
    Rc : float
        Revanche (m)
    h_structure : float, optional
        Hauteur totale de la structure (m). Si None, h_structure = h + Rc
    impulsive : bool, optional
        Si True, considère les conditions impulsives
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Débit de franchissement q (m³/s/m)
    
    References
    ----------
    EurOtop (2018) - Section 5.3
    """
    if h_structure is None:
        h_structure = h + Rc
    
    # Paramètres adimensionnels
    d_star = h / Hm0
    hm0_Lm_10 = Hm0 / wave_length_deep_water(Tm_10, g)
    
    # Revanche relative
    Rc_Hm0 = Rc / Hm0
    
    # Formule générale pour mur vertical
    # q / sqrt(g*Hm0³) = a * exp(-b * Rc/Hm0)
    q = (A_MUR_VERTICAL * 
         np.sqrt(g * Hm0**3) * 
         np.exp(-B_MUR_VERTICAL * Rc_Hm0))
    
    # Correction pour faible profondeur
    if d_star < 3.0:
        # Réduction pour faible profondeur
        factor = max(0.5, d_star / 3.0)
        q *= factor
    
    # Correction pour conditions impulsives
    if impulsive and d_star < 0.3:
        # Augmentation pour impacts impulsifs
        q *= 1.5
    
    return q


def structure_composite(Hm0, Tm_10, h, Rc, alpha_lower_deg, h_transition,
                       gamma_f_lower=1.0, gamma_f_upper=1.0,
                       gamma_beta=1.0, g=G):
    """
    Calcul du franchissement pour une structure composite
    (talus en partie basse + mur vertical en partie haute)
    
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
    alpha_lower_deg : float
        Angle de pente de la partie basse (degrés)
    h_transition : float
        Hauteur de transition entre talus et mur (m au-dessus du SWL)
    gamma_f_lower : float, optional
        Facteur de rugosité partie basse
    gamma_f_upper : float, optional
        Facteur de rugosité partie haute (mur)
    gamma_beta : float, optional
        Facteur d'obliquité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Débit de franchissement q (m³/s/m)
    
    References
    ----------
    EurOtop (2018) - Section 5.4
    """
    # Calcul du nombre d'Iribarren pour la pente inférieure
    xi = iribarren_number(alpha_lower_deg, Hm0, Tm_10, g)
    
    # Hauteur de la partie verticale
    Rc_vertical = Rc - h_transition
    
    if Rc_vertical <= 0:
        # Pas de partie verticale, structure entièrement en talus
        return digue_talus(Hm0, Tm_10, h, Rc, alpha_lower_deg,
                          1.0, gamma_f_lower, gamma_beta, "auto", g)
    
    # Facteur de réduction combiné pour partie basse
    gamma_lower = gamma_f_lower * gamma_beta
    
    # Formule composite (approximation)
    # Utilise une approche pondérée entre talus et mur vertical
    
    # Contribution de la partie en talus jusqu'à la transition
    Rc_talus_equiv = h_transition
    if Rc_talus_equiv > 0:
        q_talus = digue_talus(Hm0, Tm_10, h, Rc_talus_equiv, alpha_lower_deg,
                             1.0, gamma_f_lower, gamma_beta, "auto", g)
    else:
        q_talus = np.sqrt(g * Hm0**3)  # Valeur de référence élevée
    
    # Contribution du mur vertical
    # Réduction supplémentaire due à la hauteur du mur
    Rc_vert_star = Rc_vertical / Hm0
    q_reduction = np.exp(-2.0 * Rc_vert_star)
    
    q = q_talus * q_reduction
    
    return q


def digue_en_enrochement(Hm0, Tm_10, h, Rc, alpha_deg,
                        Dn50, n_layers=2, permeability="permeable",
                        gamma_beta=1.0, g=G):
    """
    Calcul du franchissement pour digue en enrochement
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    h : float
        Profondeur d'eau (m)
    Rc : float
        Revanche (m)
    alpha_deg : float
        Angle de pente (degrés)
    Dn50 : float
        Diamètre nominal médian des enrochements (m)
    n_layers : int, optional
        Nombre de couches (1 ou 2)
    permeability : str, optional
        Perméabilité du noyau : "permeable", "impermeable"
    gamma_beta : float, optional
        Facteur d'obliquité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Débit de franchissement q (m³/s/m)
    """
    # Facteur de rugosité selon le nombre de couches et la perméabilité
    if n_layers == 1:
        gamma_f = 0.55
    elif n_layers == 2:
        if permeability == "permeable":
            gamma_f = 0.50
        else:
            gamma_f = 0.45
    else:
        gamma_f = 0.50
    
    # Calcul standard
    q = digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                   1.0, gamma_f, gamma_beta, "auto", g)
    
    return q


def promenade_avec_parapet(Hm0, Tm_10, h, Rc_promenade, h_parapet, 
                          alpha_deg=90.0, gamma_f=1.0, g=G):
    """
    Calcul du franchissement pour une promenade avec parapet
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    h : float
        Profondeur d'eau (m)
    Rc_promenade : float
        Hauteur de la promenade au-dessus du SWL (m)
    h_parapet : float
        Hauteur du parapet (m)
    alpha_deg : float, optional
        Pente éventuelle avant la promenade (degrés)
    gamma_f : float, optional
        Facteur de rugosité
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Débit de franchissement q (m³/s/m)
    """
    # Revanche totale
    Rc_total = Rc_promenade + h_parapet
    
    if alpha_deg >= 80:
        # Structure quasi-verticale
        q_sans_parapet = mur_vertical(Hm0, Tm_10, h, Rc_promenade, g=g)
    else:
        # Structure en talus
        q_sans_parapet = digue_talus(Hm0, Tm_10, h, Rc_promenade, alpha_deg,
                                     1.0, gamma_f, 1.0, "auto", g)
    
    # Réduction due au parapet
    # Le parapet réduit le franchissement de manière exponentielle
    if h_parapet > 0:
        h_parapet_star = h_parapet / Hm0
        reduction = np.exp(-1.5 * h_parapet_star)
        q = q_sans_parapet * reduction
    else:
        q = q_sans_parapet
    
    return q


def rubble_mound_breakwater(Hm0, Tm_10, h, Rc, alpha_deg, 
                            armor_unit="enrochement", Dn50=None,
                            crest_width=None, g=G):
    """
    Calcul du franchissement pour digue à talus (rubble mound breakwater)
    avec différents types de carapace
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    h : float
        Profondeur d'eau (m)
    Rc : float
        Revanche (m)
    alpha_deg : float
        Angle de pente (degrés)
    armor_unit : str, optional
        Type d'unité de carapace
    Dn50 : float, optional
        Diamètre nominal (m)
    crest_width : float, optional
        Largeur de crête (m)
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    float
        Débit de franchissement q (m³/s/m)
    """
    # Facteur de rugosité selon le type d'armure
    gamma_f = gamma_f_roughness(armor_unit)
    
    # Facteur de berme si largeur de crête significative
    if crest_width is not None and crest_width > 0:
        # La crête agit comme une berme
        gamma_b = gamma_b_berm(Rc, Hm0, crest_width, Rc, gamma_f)
    else:
        gamma_b = 1.0
    
    # Calcul standard
    q = digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                   gamma_b, gamma_f, 1.0, "auto", g)
    
    return q


def calcul_volumes_franchissement(q, duree_tempete_heures):
    """
    Calcule les volumes de franchissement à partir du débit moyen
    
    Parameters
    ----------
    q : float
        Débit de franchissement moyen (m³/s/m)
    duree_tempete_heures : float
        Durée de la tempête (heures)
    
    Returns
    -------
    dict
        Volumes en différentes unités
    """
    duree_secondes = duree_tempete_heures * 3600
    
    # Volume total par mètre linéaire
    V_total = q * duree_secondes  # m³/m
    
    # Volume par mètre de longueur d'ouvrage
    V_per_m = V_total  # m³/m
    
    # Convertions pratiques
    V_liters_per_m = V_total * 1000  # litres/m
    
    return {
        "volume_total_m3_per_m": V_total,
        "volume_liters_per_m": V_liters_per_m,
        "debit_moyen_m3_s_m": q,
        "duree_heures": duree_tempete_heures,
        "duree_secondes": duree_secondes
    }


def discharge_individual_waves(Hm0, Tm_10, h, Rc, alpha_deg, 
                               gamma_f=1.0, gamma_beta=1.0, 
                               N_waves=1000, g=G):
    """
    Estime la distribution du franchissement par vague individuelle
    
    Parameters
    ----------
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    h : float
        Profondeur d'eau (m)
    Rc : float
        Revanche (m)
    alpha_deg : float
        Angle de pente (degrés)
    gamma_f : float, optional
        Facteur de rugosité
    gamma_beta : float, optional
        Facteur d'obliquité
    N_waves : int, optional
        Nombre de vagues pendant la tempête
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Statistiques sur le franchissement par vagues
    """
    # Débit moyen
    q_mean = digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                        1.0, gamma_f, gamma_beta, "auto", g)
    
    # Volume moyen par vague
    V_mean = q_mean * Tm_10  # m³/m par vague
    
    # Proportion de vagues franchissantes (formule empirique)
    Rc_Hm0 = Rc / Hm0
    if Rc_Hm0 <= 1.0:
        P_ow = 1.0  # Toutes les vagues franchissent
    else:
        P_ow = np.exp(-0.5 * Rc_Hm0)  # Proportion décroissante
    
    # Nombre de vagues franchissantes
    N_overtopping = int(N_waves * P_ow)
    
    # Volume moyen par vague franchissante
    if P_ow > 0:
        V_per_overtopping_wave = V_mean / P_ow
    else:
        V_per_overtopping_wave = 0.0
    
    return {
        "q_mean": q_mean,
        "V_mean_per_wave": V_mean,
        "P_overtopping": P_ow,
        "N_waves_total": N_waves,
        "N_overtopping_waves": N_overtopping,
        "V_per_overtopping_wave": V_per_overtopping_wave
    }

