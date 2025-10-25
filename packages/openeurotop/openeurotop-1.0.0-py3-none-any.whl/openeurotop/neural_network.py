"""
Méthodes neuronales pour le franchissement (début d'implémentation)

EurOtop 2018 - Annexe C

Note : Implémentation de base sans réseau pré-entraîné.
Pour une utilisation complète, un réseau neuronal devrait être entraîné
sur une base de données d'essais physiques.
"""

import numpy as np


class NeuralNetworkOvertoppingPredictor:
    """
    Classe de base pour prédiction neuronale du franchissement
    
    Cette implémentation fournit la structure pour une méthode neuronale,
    mais nécessiterait un entraînement sur des données réelles pour être opérationnelle.
    
    EurOtop 2018 propose l'utilisation de réseaux de neurones comme alternative
    aux formules empiriques, particulièrement pour des géométries complexes.
    
    References
    ----------
    EurOtop (2018) - Annexe C
    Van Gent et al. (2007) - Neural Network Modelling of Wave Overtopping
    """
    
    def __init__(self, architecture=[6, 10, 10, 1]):
        """
        Initialise le réseau de neurones
        
        Parameters
        ----------
        architecture : list
            Architecture du réseau [n_input, n_hidden1, n_hidden2, ..., n_output]
            Par défaut : [6, 10, 10, 1]
            - 6 entrées : Hm0, Tm-1,0, h, Rc, tan(α), γf
            - 2 couches cachées de 10 neurones
            - 1 sortie : log10(q)
        """
        self.architecture = architecture
        self.weights = []
        self.biases = []
        self.is_trained = False
        
        # Initialisation aléatoire des poids (pour démonstration uniquement)
        # Dans une vraie implémentation, ces poids seraient appris
        np.random.seed(42)
        for i in range(len(architecture) - 1):
            w = np.random.randn(architecture[i], architecture[i+1]) * 0.1
            b = np.random.randn(architecture[i+1]) * 0.1
            self.weights.append(w)
            self.biases.append(b)
    
    def sigmoid(self, x):
        """Fonction d'activation sigmoïde"""
        return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
    
    def tanh(self, x):
        """Fonction d'activation tanh"""
        return np.tanh(x)
    
    def normalize_inputs(self, Hm0, Tm_10, h, Rc, tan_alpha, gamma_f):
        """
        Normalise les entrées du réseau
        
        La normalisation est cruciale pour les réseaux de neurones
        
        Parameters
        ----------
        Hm0, Tm_10, h, Rc : float
            Paramètres de vague et structure
        tan_alpha : float
            Tangente de l'angle de pente
        gamma_f : float
            Facteur de rugosité
        
        Returns
        -------
        np.ndarray
            Vecteur d'entrées normalisées
        """
        # Normalisation basée sur des plages typiques
        # Ces valeurs devraient être calculées sur la base d'entraînement réelle
        inputs = np.array([
            (Hm0 - 2.0) / 2.0,          # Hm0 typique 0-4m
            (Tm_10 - 6.0) / 3.0,        # Tm-1,0 typique 3-9s
            (h - 5.0) / 5.0,            # h typique 0-10m
            (Rc - 2.0) / 2.0,           # Rc typique 0-4m
            (tan_alpha - 0.5) / 0.5,    # tan(α) typique 0-1
            (gamma_f - 0.7) / 0.3       # γf typique 0.4-1.0
        ])
        return inputs
    
    def forward(self, x):
        """
        Propagation avant dans le réseau
        
        Parameters
        ----------
        x : np.ndarray
            Vecteur d'entrées normalisées
        
        Returns
        -------
        float
            Sortie du réseau (log10(q))
        """
        a = x
        for i in range(len(self.weights)):
            z = np.dot(a, self.weights[i]) + self.biases[i]
            if i < len(self.weights) - 1:
                a = self.tanh(z)  # Couches cachées
            else:
                a = z  # Couche de sortie (linéaire)
        return a[0]
    
    def predict(self, Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=1.0):
        """
        Prédit le débit de franchissement avec le réseau de neurones
        
        ATTENTION : Cette implémentation est une démonstration uniquement.
        Les poids ne sont PAS entraînés sur des données réelles.
        Pour une utilisation réelle, le réseau doit être entraîné.
        
        Parameters
        ----------
        Hm0, Tm_10, h, Rc : float
            Paramètres standard
        alpha_deg : float
            Angle de pente (degrés)
        gamma_f : float, optional
            Facteur de rugosité
        
        Returns
        -------
        dict
            Prédiction avec warnings
        """
        # Convertir angle en tangente
        from openeurotop.constants import DEG_TO_RAD
        tan_alpha = np.tan(alpha_deg * DEG_TO_RAD)
        
        # Normaliser les entrées
        x_norm = self.normalize_inputs(Hm0, Tm_10, h, Rc, tan_alpha, gamma_f)
        
        # Prédiction
        log_q = self.forward(x_norm)
        q_pred = 10**log_q
        
        return {
            'q': q_pred,
            'log_q': log_q,
            'warning': 'Réseau NON entraîné - résultat démonstratif uniquement',
            'is_trained': self.is_trained,
            'recommendation': 'Utiliser les formules empiriques pour des calculs réels'
        }
    
    def load_pretrained_weights(self, weights_file):
        """
        Charge des poids pré-entraînés depuis un fichier
        
        Parameters
        ----------
        weights_file : str
            Chemin vers le fichier de poids (format .npz ou .h5)
        
        Notes
        -----
        Cette fonction serait utilisée pour charger un réseau entraîné.
        Un tel réseau nécessiterait :
        - Base de données d'essais physiques
        - Entraînement supervisé
        - Validation croisée
        """
        raise NotImplementedError(
            "Chargement de poids pré-entraînés non implémenté. "
            "Un réseau entraîné nécessite une base de données d'essais physiques."
        )


def neural_network_comparison(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=1.0):
    """
    Compare la prédiction neuronale avec les formules empiriques
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc, alpha_deg : float
        Paramètres de la structure
    gamma_f : float, optional
        Facteur de rugosité
    
    Returns
    -------
    dict
        Comparaison entre méthodes
    
    Examples
    --------
    >>> result = neural_network_comparison(2.5, 6.0, 10.0, 3.0, 35.0)
    >>> print(f"Formule empirique : {result['q_empirical']:.6f} m³/s/m")
    >>> print(f"Réseau neuronal : {result['q_neural']:.6f} m³/s/m (non fiable)")
    """
    from openeurotop import overtopping
    
    # Prédiction avec formule empirique (fiable)
    q_empirical = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=gamma_f)
    
    # Prédiction avec réseau neuronal (démonstratif)
    nn = NeuralNetworkOvertoppingPredictor()
    nn_result = nn.predict(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f)
    
    return {
        'q_empirical': q_empirical,
        'q_neural': nn_result['q'],
        'method_used': 'empirical',
        'recommendation': (
            'Pour des calculs réels, utiliser les formules empiriques. '
            'Le réseau neuronal nécessite un entraînement préalable.'
        ),
        'neural_warning': nn_result['warning']
    }


def prepare_training_data_structure():
    """
    Fournit un template pour préparer des données d'entraînement
    
    Cette fonction montre comment structurer des données pour entraîner
    un réseau neuronal sur des essais physiques.
    
    Returns
    -------
    dict
        Structure de données pour entraînement
    
    Notes
    -----
    Pour entraîner un réseau neuronal efficace, il faudrait :
    
    1. **Base de données** : Minimum 500-1000 essais physiques
    2. **Variables d'entrée** :
       - Hm0, Tm-1,0, Tp, h, Rc
       - α (angle de pente)
       - γf (rugosité)
       - γβ (obliquité)
       - Configuration de bermes
    3. **Variable de sortie** : log10(q)
    4. **Validation** : Split 80% entraînement, 20% test
    5. **Architecture** : Optimiser par validation croisée
    
    References
    ----------
    Van Gent et al. (2007) - Neural Network Modelling of Wave Overtopping at Coastal Structures
    """
    template = {
        'description': 'Template pour données d\'entraînement de réseau neuronal',
        'inputs': {
            'Hm0': 'Hauteur significative spectrale (m)',
            'Tm_10': 'Période spectrale Tm-1,0 (s)',
            'h': 'Profondeur d\'eau (m)',
            'Rc': 'Revanche (m)',
            'tan_alpha': 'Tangente de l\'angle de pente',
            'gamma_f': 'Facteur de rugosité',
            'gamma_beta': 'Facteur d\'obliquité (optionnel)',
            'B_berm': 'Largeur de berme (optionnel)',
        },
        'output': {
            'log_q': 'log10(débit de franchissement en m³/s/m)'
        },
        'data_format': {
            'format': 'numpy array ou pandas DataFrame',
            'shape': '(n_samples, n_features)',
            'example_size': 'Minimum 500 échantillons recommandés'
        },
        'preprocessing': {
            'normalization': 'Obligatoire - mean centering et scaling',
            'outliers': 'À détecter et traiter',
            'missing_data': 'Imputation ou suppression'
        },
        'training': {
            'validation': '80/20 split ou k-fold cross-validation',
            'optimization': 'Adam ou SGD avec momentum',
            'loss': 'MSE (Mean Squared Error)',
            'epochs': '100-1000 selon convergence'
        }
    }
    
    return template


# Exemple de données fictives pour démonstration
def generate_synthetic_training_example(n_samples=100):
    """
    Génère des données synthétiques pour démonstration
    
    ATTENTION : Ces données sont générées artificiellement avec les formules
    empiriques. Un vrai entraînement nécessiterait des données d'essais réels.
    
    Parameters
    ----------
    n_samples : int
        Nombre d'échantillons à générer
    
    Returns
    -------
    dict
        Données synthétiques X (inputs) et y (outputs)
    """
    from openeurotop import overtopping
    
    np.random.seed(42)
    
    # Générer des paramètres aléatoires dans des plages réalistes
    Hm0 = np.random.uniform(0.5, 4.0, n_samples)
    Tm_10 = np.random.uniform(3.0, 10.0, n_samples)
    h = np.random.uniform(2.0, 15.0, n_samples)
    Rc = np.random.uniform(0.5, 5.0, n_samples)
    alpha_deg = np.random.uniform(15.0, 60.0, n_samples)
    gamma_f = np.random.choice([1.0, 0.9, 0.7, 0.5, 0.4], n_samples)
    
    # Calculer les sorties avec formules empiriques
    q_values = np.zeros(n_samples)
    for i in range(n_samples):
        q_values[i] = overtopping.digue_talus(
            Hm0[i], Tm_10[i], h[i], Rc[i], alpha_deg[i], gamma_f=gamma_f[i]
        )
    
    # Convertir en log10
    log_q = np.log10(q_values + 1e-10)  # +epsilon pour éviter log(0)
    
    # Préparer les features
    from openeurotop.constants import DEG_TO_RAD
    tan_alpha = np.tan(alpha_deg * DEG_TO_RAD)
    
    X = np.column_stack([Hm0, Tm_10, h, Rc, tan_alpha, gamma_f])
    y = log_q
    
    return {
        'X': X,
        'y': y,
        'feature_names': ['Hm0', 'Tm_10', 'h', 'Rc', 'tan_alpha', 'gamma_f'],
        'n_samples': n_samples,
        'warning': 'Données SYNTHÉTIQUES générées avec formules empiriques - pas réelles'
    }


def info_neural_network_usage():
    """
    Fournit des informations sur l'utilisation des réseaux neuronaux pour le franchissement
    
    Returns
    -------
    str
        Guide d'utilisation
    """
    info = """
    ================================================================================
    UTILISATION DES RÉSEAUX NEURONAUX POUR LE FRANCHISSEMENT
    ================================================================================
    
    Les réseaux neuronaux offrent une alternative aux formules empiriques,
    particulièrement pour :
    
    AVANTAGES :
    - Géométries très complexes (multi-pentes, multi-bermes)
    - Interpolation dans un espace multi-dimensionnel
    - Pas besoin de sélectionner la formule appropriée
    - Peut capturer des interactions non-linéaires complexes
    
    INCONVÉNIENTS :
    - Nécessite une base de données d'entraînement importante (>500 essais)
    - "Boîte noire" - moins de compréhension physique
    - Extrapolation dangereuse hors du domaine d'entraînement
    - Nécessite expertise en machine learning
    
    ÉTAT ACTUEL DE L'IMPLÉMENTATION :
    
    ⚠️ L'implémentation actuelle est une DÉMONSTRATION uniquement.
    
    Les poids du réseau ne sont PAS entraînés sur des données réelles.
    Pour une utilisation opérationnelle, il faudrait :
    
    1. Collecter une base de données d'essais physiques (CLASH, etc.)
    2. Entraîner le réseau avec ces données
    3. Valider sur des essais indépendants
    4. Sauvegarder les poids entraînés
    5. Charger ces poids dans l'application
    
    RECOMMANDATION :
    
    ✅ Pour des calculs de conception, utiliser les FORMULES EMPIRIQUES
       implémentées dans openeurotop.overtopping
    
    ❌ Ne PAS utiliser les prédictions neuronales non entraînées pour
       des calculs réels
    
    POUR ALLER PLUS LOIN :
    
    - Consulter la base de données CLASH (>10,000 essais de franchissement)
    - Étudier Van Gent et al. (2007) pour la méthodologie
    - Utiliser des frameworks comme TensorFlow ou PyTorch pour l'entraînement
    - Considérer des approches hybrides (formules + réseaux neuronaux)
    
    ================================================================================
    """
    return info

