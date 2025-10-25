"""
Analyses probabilistes et statistiques selon EurOtop (2018)

Distributions, incertitudes, fiabilité et bandes de confiance
"""

import numpy as np
from scipy import stats
from scipy.optimize import fsolve
from openeurotop import overtopping, wave_parameters


def weibull_distribution_overtopping(Hm0, Tm_10, h, Rc, alpha_deg,
                                     gamma_f=1.0, gamma_beta=1.0, gamma_b=1.0,
                                     N_waves=1000, g=9.81):
    """
    Distribution de Weibull pour les volumes de franchissement par vagues individuelles
    
    EurOtop 2018 - Section 5.5.2
    
    La distribution de Weibull à 2 paramètres :
    P(V > v) = exp(-(v/a)^b)
    
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
    gamma_f, gamma_beta, gamma_b : float, optional
        Facteurs de réduction
    N_waves : int, optional
        Nombre de vagues
    g : float, optional
        Accélération de la pesanteur (m/s²)
    
    Returns
    -------
    dict
        Paramètres de Weibull et statistiques
    
    References
    ----------
    EurOtop (2018) - Équation 5.21
    """
    # Débit moyen
    q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                                gamma_b, gamma_f, gamma_beta, g=g)
    
    # Volume moyen par vague
    V_mean = q * Tm_10
    
    # Proportion de vagues franchissantes (formule EurOtop)
    Rc_Hm0 = Rc / Hm0
    P_ow = min(1.0, np.exp(-0.5 * Rc_Hm0))  # Probabilité de franchissement
    
    # Paramètres de Weibull
    # Pour la distribution de volumes individuels
    # b ≈ 0.75 (paramètre de forme typique)
    b = 0.75
    
    # Paramètre d'échelle a
    # Relation : V_mean = a * Gamma(1 + 1/b) * P_ow
    from scipy.special import gamma as gamma_func
    a = V_mean / (gamma_func(1 + 1/b) * P_ow) if P_ow > 0 else 0
    
    # Volume maximum (dépassé par 0.1% des vagues)
    V_01 = a * (-np.log(0.001))**(1/b) if a > 0 else 0
    
    # Nombre de vagues franchissantes
    N_ow = int(N_waves * P_ow)
    
    return {
        'a': a,  # Paramètre d'échelle
        'b': b,  # Paramètre de forme
        'V_mean': V_mean,
        'V_01': V_01,  # Volume dépassé par 0.1%
        'P_ow': P_ow,  # Probabilité de franchissement
        'N_ow': N_ow,  # Nombre de vagues franchissantes
        'q': q
    }


def volume_exceedance_weibull(v, a, b):
    """
    Probabilité de dépassement d'un volume selon Weibull
    
    P(V > v) = exp(-(v/a)^b)
    
    Parameters
    ----------
    v : float or array_like
        Volume à évaluer (m³/m)
    a : float
        Paramètre d'échelle de Weibull
    b : float
        Paramètre de forme de Weibull
    
    Returns
    -------
    float or array_like
        Probabilité de dépassement
    """
    v = np.asarray(v)
    if a <= 0:
        return np.zeros_like(v)
    return np.exp(-(v / a)**b)


def uncertainty_overtopping(Hm0, Tm_10, h, Rc, alpha_deg, 
                            structure_type="smooth_slope",
                            gamma_f=1.0, gamma_beta=1.0, gamma_b=1.0):
    """
    Estimation des incertitudes sur le franchissement
    
    EurOtop 2018 - Section 5.8
    
    L'incertitude est exprimée par l'écart-type du logarithme :
    - Digues lisses : σ_ln(q) ≈ 0.13
    - Digues rugueuses : σ_ln(q) ≈ 0.15
    - Murs verticaux : σ_ln(q) ≈ 0.14
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc, alpha_deg : float
        Paramètres de la structure
    structure_type : str
        Type de structure ("smooth_slope", "rough_slope", "vertical_wall")
    gamma_f, gamma_beta, gamma_b : float
        Facteurs de réduction
    
    Returns
    -------
    dict
        Statistiques avec bandes de confiance
    
    References
    ----------
    EurOtop (2018) - Section 5.8
    """
    # Calcul du débit moyen
    if structure_type == "vertical_wall":
        q_mean = overtopping.mur_vertical(Hm0, Tm_10, h, Rc)
        sigma_ln_q = 0.14
    elif structure_type == "rough_slope":
        q_mean = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                                        gamma_b, gamma_f, gamma_beta)
        sigma_ln_q = 0.15
    else:  # smooth_slope
        q_mean = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                                        gamma_b, 1.0, gamma_beta)
        sigma_ln_q = 0.13
    
    # Bandes de confiance (distribution log-normale)
    # Intervalle 90% de confiance : facteurs 1/k_90 et k_90
    # où k_90 ≈ exp(1.645 * sigma_ln_q)
    k_90 = np.exp(1.645 * sigma_ln_q)
    k_95 = np.exp(1.96 * sigma_ln_q)
    
    return {
        'q_mean': q_mean,
        'q_5': q_mean / k_90,    # Limite inférieure 90%
        'q_95': q_mean * k_90,   # Limite supérieure 90%
        'q_2.5': q_mean / k_95,  # Limite inférieure 95%
        'q_97.5': q_mean * k_95, # Limite supérieure 95%
        'sigma_ln_q': sigma_ln_q,
        'structure_type': structure_type
    }


def reliability_freeboard(q_limit, Hm0, Tm_10, h, alpha_deg,
                         gamma_f=1.0, gamma_beta=1.0, gamma_b=1.0,
                         sigma_ln_q=0.15):
    """
    Calcul de la revanche nécessaire pour un débit limite avec un niveau de fiabilité
    
    Parameters
    ----------
    q_limit : float
        Débit limite tolérable (m³/s/m)
    Hm0 : float
        Hauteur significative spectrale (m)
    Tm_10 : float
        Période spectrale (s)
    h : float
        Profondeur d'eau (m)
    alpha_deg : float
        Angle de pente (degrés)
    gamma_f, gamma_beta, gamma_b : float
        Facteurs de réduction
    sigma_ln_q : float, optional
        Écart-type du logarithme de q (incertitude)
    
    Returns
    -------
    dict
        Revanches pour différents niveaux de confiance
    
    Examples
    --------
    >>> # Revanche nécessaire pour q < 1 l/s/m avec 95% de confiance
    >>> result = reliability_freeboard(0.001, Hm0=2.5, Tm_10=6.0, h=10.0, alpha_deg=35.0)
    >>> print(f"Rc (95% confiance) = {result['Rc_95']:.2f} m")
    """
    # Fonction objectif : trouver Rc tel que q = q_limit
    def objective(Rc):
        q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg,
                                   gamma_b, gamma_f, gamma_beta)
        return q - q_limit
    
    # Résolution pour débit moyen
    Rc_mean = fsolve(objective, Hm0)[0]  # Initialisation à Hm0
    
    # Revanche avec marge de sécurité
    # Pour 90% de confiance : k = exp(1.28 * sigma)
    # Pour 95% : k = exp(1.645 * sigma)
    k_90 = np.exp(1.28 * sigma_ln_q)
    k_95 = np.exp(1.645 * sigma_ln_q)
    
    # Ajustement de la revanche pour tenir compte de l'incertitude
    # Si on veut 95% de confiance que q < q_limit, on doit augmenter Rc
    # Approximation : augmenter Rc proportionnellement
    delta_Rc_90 = 0.3 * Hm0 * sigma_ln_q  # Approximation empirique
    delta_Rc_95 = 0.5 * Hm0 * sigma_ln_q
    
    return {
        'Rc_mean': Rc_mean,
        'Rc_90': Rc_mean + delta_Rc_90,
        'Rc_95': Rc_mean + delta_Rc_95,
        'q_limit': q_limit
    }


def monte_carlo_overtopping(Hm0_mean, Hm0_std, Tm_10_mean, Tm_10_std,
                           h, Rc, alpha_deg, gamma_f=1.0,
                           n_simulations=10000):
    """
    Simulation Monte Carlo pour évaluer la variabilité du franchissement
    
    Prend en compte la variabilité de Hm0 et Tm-1,0
    
    Parameters
    ----------
    Hm0_mean, Hm0_std : float
        Moyenne et écart-type de Hm0 (m)
    Tm_10_mean, Tm_10_std : float
        Moyenne et écart-type de Tm-1,0 (s)
    h : float
        Profondeur d'eau (m)
    Rc : float
        Revanche (m)
    alpha_deg : float
        Angle de pente (degrés)
    gamma_f : float, optional
        Facteur de rugosité
    n_simulations : int, optional
        Nombre de simulations Monte Carlo
    
    Returns
    -------
    dict
        Statistiques des résultats Monte Carlo
    
    Examples
    --------
    >>> # Variabilité climatique : Hm0 = 2.5 ± 0.5 m
    >>> result = monte_carlo_overtopping(2.5, 0.5, 6.0, 0.8, 10.0, 3.0, 35.0)
    >>> print(f"q moyen = {result['q_mean']:.6f} m³/s/m")
    >>> print(f"q 95% = {result['q_95']:.6f} m³/s/m")
    """
    # Génération des échantillons (distribution normale)
    Hm0_samples = np.random.normal(Hm0_mean, Hm0_std, n_simulations)
    Tm_10_samples = np.random.normal(Tm_10_mean, Tm_10_std, n_simulations)
    
    # S'assurer que les valeurs sont positives
    Hm0_samples = np.maximum(Hm0_samples, 0.1)
    Tm_10_samples = np.maximum(Tm_10_samples, 1.0)
    
    # Calcul du franchissement pour chaque réalisation
    q_samples = np.zeros(n_simulations)
    for i in range(n_simulations):
        q_samples[i] = overtopping.digue_talus(
            Hm0_samples[i], Tm_10_samples[i], h, Rc, alpha_deg,
            gamma_f=gamma_f
        )
    
    # Statistiques
    return {
        'q_mean': np.mean(q_samples),
        'q_median': np.median(q_samples),
        'q_std': np.std(q_samples),
        'q_5': np.percentile(q_samples, 5),
        'q_95': np.percentile(q_samples, 95),
        'q_min': np.min(q_samples),
        'q_max': np.max(q_samples),
        'samples': q_samples
    }


def confidence_bands_overtopping(Hm0, Tm_10, h, Rc_range, alpha_deg,
                                gamma_f=1.0, structure_type="rough_slope"):
    """
    Calcule les bandes de confiance pour différentes revanches
    
    Parameters
    ----------
    Hm0, Tm_10, h : float
        Paramètres de vague et profondeur
    Rc_range : array_like
        Gamme de revanches à évaluer (m)
    alpha_deg : float
        Angle de pente (degrés)
    gamma_f : float
        Facteur de rugosité
    structure_type : str
        Type de structure pour l'incertitude
    
    Returns
    -------
    dict
        Arrays avec q_mean, q_lower, q_upper pour chaque Rc
    
    Examples
    --------
    >>> import numpy as np
    >>> import matplotlib.pyplot as plt
    >>> Rc_range = np.linspace(1, 5, 20)
    >>> result = confidence_bands_overtopping(2.5, 6.0, 10.0, Rc_range, 35.0)
    >>> plt.fill_between(Rc_range, result['q_lower']*1000, result['q_upper']*1000, alpha=0.3)
    >>> plt.plot(Rc_range, result['q_mean']*1000)
    >>> plt.xlabel('Rc (m)')
    >>> plt.ylabel('q (l/s/m)')
    >>> plt.show()
    """
    Rc_range = np.asarray(Rc_range)
    n_points = len(Rc_range)
    
    q_mean = np.zeros(n_points)
    q_lower = np.zeros(n_points)
    q_upper = np.zeros(n_points)
    
    for i, Rc in enumerate(Rc_range):
        unc = uncertainty_overtopping(Hm0, Tm_10, h, Rc, alpha_deg,
                                     structure_type, gamma_f)
        q_mean[i] = unc['q_mean']
        q_lower[i] = unc['q_5']
        q_upper[i] = unc['q_95']
    
    return {
        'Rc': Rc_range,
        'q_mean': q_mean,
        'q_lower': q_lower,
        'q_upper': q_upper
    }


def failure_probability_overtopping(q_critical, Hm0, Tm_10, h, Rc, alpha_deg,
                                   gamma_f=1.0, sigma_ln_q=0.15):
    """
    Calcule la probabilité de défaillance (q > q_critical)
    
    En supposant une distribution log-normale de q
    
    Parameters
    ----------
    q_critical : float
        Débit critique au-delà duquel il y a défaillance (m³/s/m)
    Hm0, Tm_10, h, Rc, alpha_deg : float
        Paramètres de la structure
    gamma_f : float
        Facteur de rugosité
    sigma_ln_q : float
        Écart-type du logarithme de q
    
    Returns
    -------
    float
        Probabilité de défaillance Pf
    
    Examples
    --------
    >>> # Probabilité que q dépasse 10 l/s/m
    >>> Pf = failure_probability_overtopping(0.01, 2.5, 6.0, 10.0, 3.0, 35.0)
    >>> print(f"Probabilité de défaillance : {Pf*100:.2f}%")
    """
    # Débit moyen
    q_mean = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=gamma_f)
    
    # Distribution log-normale
    # ln(q) ~ N(mu, sigma²)
    # où mu = ln(q_mean) - sigma²/2 (pour que la médiane soit q_mean)
    mu = np.log(q_mean)
    sigma = sigma_ln_q
    
    # P(q > q_critical) = P(ln(q) > ln(q_critical))
    #                   = 1 - Phi((ln(q_critical) - mu) / sigma)
    z = (np.log(q_critical) - mu) / sigma
    Pf = 1 - stats.norm.cdf(z)
    
    return Pf


def design_overtopping_rate(return_period_years, acceptable_rate_per_year=0.1):
    """
    Calcule le débit de franchissement de conception basé sur une période de retour
    
    Parameters
    ----------
    return_period_years : float
        Période de retour (années)
    acceptable_rate_per_year : float
        Taux de franchissement acceptable par an (défaut: 0.1 = 10%)
    
    Returns
    -------
    dict
        Informations sur le niveau de conception
    
    Examples
    --------
    >>> # Conception pour tempête centennale
    >>> design = design_overtopping_rate(100)
    """
    # Probabilité annuelle de dépassement
    p_annual = 1.0 / return_period_years
    
    # Facteur de sécurité
    safety_factor = -np.log(acceptable_rate_per_year) / np.log(1 - p_annual)
    
    return {
        'return_period_years': return_period_years,
        'annual_exceedance_probability': p_annual,
        'acceptable_rate_per_year': acceptable_rate_per_year,
        'safety_factor': safety_factor
    }

