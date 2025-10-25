"""
Module XGBoost pour prédiction du franchissement basé sur CLASH

Alternative au réseau de neurones utilisant XGBoost (Gradient Boosting)
"""

import numpy as np
import pickle
from pathlib import Path


class XGBoostOvertoppingPredictor:
    """
    Prédicteur de franchissement utilisant XGBoost
    
    XGBoost est souvent plus performant que les réseaux de neurones
    sur des données tabulaires comme CLASH.
    
    Attributes
    ----------
    model : xgboost.XGBRegressor
        Modèle XGBoost entraîné
    feature_names : list
        Noms des features
    is_trained : bool
        Indicateur d'entraînement
    """
    
    def __init__(self):
        """Initialise le prédicteur XGBoost"""
        self.model = None
        self.feature_names = [
            'Hm0_toe', 'Tm_10_toe', 'h', 'Rc', 'cotad',
            'gf', 'B', 'hb', 'Ac', 'Gc'
        ]
        self.is_trained = False
        self.training_info = {}
    
    def load_model(self, filepath='Data/xgboost_optimized_model.pkl'):
        """
        Charge un modèle XGBoost entraîné
        
        Parameters
        ----------
        filepath : str
            Chemin vers le fichier pickle du modèle
        """
        with open(filepath, 'rb') as f:
            self.model = pickle.load(f)
        
        self.is_trained = True
        print(f"Modèle XGBoost chargé: {filepath}")
    
    def predict(self, Hm0, Tm_10, h, Rc, alpha_deg, 
                gamma_f=1.0, B=0, hb=0, Ac=0, Gc=0):
        """
        Prédit le débit de franchissement avec XGBoost
        
        Parameters
        ----------
        Hm0 : float
            Hauteur significative au pied (m)
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
        B, hb, Ac, Gc : float, optional
            Paramètres géométriques additionnels
        
        Returns
        -------
        dict
            Résultat de la prédiction
        """
        if not self.is_trained:
            return {
                'error': 'Modèle non entraîné',
                'recommendation': 'Charger un modèle avec load_model()'
            }
        
        # Convertir angle en cotangente
        from openeurotop.constants import DEG_TO_RAD
        tan_alpha = np.tan(alpha_deg * DEG_TO_RAD)
        cotad = 1.0 / tan_alpha if tan_alpha > 0 else 999
        
        # Préparer features
        X = np.array([[Hm0, Tm_10, h, Rc, cotad, gamma_f, B, hb, Ac, Gc]])
        
        # Prédire
        log_q = self.model.predict(X)[0]
        q = 10**log_q
        
        return {
            'q': q,
            'log_q': log_q,
            'is_trained': self.is_trained,
            'method': 'XGBoost',
            'features_used': self.feature_names
        }
    
    def save_model(self, filepath='Data/xgboost_model.pkl'):
        """Sauvegarde le modèle"""
        if self.model is None:
            raise ValueError("Aucun modèle à sauvegarder")
        
        with open(filepath, 'wb') as f:
            pickle.dump(self.model, f)
        
        print(f"Modèle XGBoost sauvegardé: {filepath}")


def predict_with_xgboost(Hm0, Tm_10, h, Rc, alpha_deg,
                         gamma_f=1.0, model_path='Data/xgboost_optimized_model.pkl'):
    """
    Fonction utilitaire pour prédiction rapide avec XGBoost
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc, alpha_deg : float
        Paramètres standard
    gamma_f : float, optional
        Facteur de rugosité
    model_path : str, optional
        Chemin vers le modèle
    
    Returns
    -------
    dict
        Prédiction
    """
    predictor = XGBoostOvertoppingPredictor()
    
    try:
        predictor.load_model(model_path)
        return predictor.predict(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f)
    except FileNotFoundError:
        return {
            'error': f'Modèle non trouvé: {model_path}',
            'recommendation': 'Entraîner le modèle avec scripts/train_advanced_models.py'
        }


def compare_all_methods(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=1.0):
    """
    Compare toutes les méthodes disponibles
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc, alpha_deg : float
        Paramètres de la structure
    gamma_f : float, optional
        Facteur de rugosité
    
    Returns
    -------
    dict
        Comparaison des méthodes
    """
    from openeurotop import overtopping
    from openeurotop.neural_network_clash import predict_with_clash
    
    results = {}
    
    # 1. Formule empirique (référence)
    try:
        q_emp = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=gamma_f)
        results['empirical'] = {
            'q': q_emp,
            'method': 'Formule EurOtop',
            'status': 'success',
            'recommended': True
        }
    except Exception as e:
        results['empirical'] = {'error': str(e)}
    
    # 2. Neural Network CLASH
    try:
        nn_result = predict_with_clash(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f)
        results['neural_network'] = nn_result
        results['neural_network']['recommended'] = False
    except Exception as e:
        results['neural_network'] = {'error': str(e)}
    
    # 3. XGBoost
    try:
        xgb_result = predict_with_xgboost(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f)
        results['xgboost'] = xgb_result
        results['xgboost']['recommended'] = False
    except Exception as e:
        results['xgboost'] = {'error': str(e)}
    
    return results

