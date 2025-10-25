"""
Module de réseau de neurones entraîné sur la base de données CLASH
pour la prédiction du franchissement des ouvrages côtiers

CLASH Database: Crest Level Assessment of coastal Structures by full scale 
monitoring, neural network prediction and Hazard analysis on permissible 
wave overtopping

References
----------
Van der Meer et al. (2005) - CLASH database
Van Gent et al. (2007) - Neural Network Modelling of Wave Overtopping
EurOtop (2018) - Annexe C
"""

import numpy as np
import pandas as pd
import pickle
from pathlib import Path
import warnings


class CLASHNeuralNetwork:
    """
    Réseau de neurones entraîné sur la base de données CLASH
    
    Architecture optimisée pour la prédiction du franchissement
    basée sur plus de 10,000 essais physiques
    
    Attributes
    ----------
    architecture : list
        Architecture du réseau [n_inputs, n_hidden1, ..., n_output]
    weights : list of np.ndarray
        Poids entraînés
    biases : list of np.ndarray
        Biais entraînés
    scaler_params : dict
        Paramètres de normalisation (mean, std)
    is_trained : bool
        Indicateur d'entraînement
    """
    
    def __init__(self, architecture=[10, 20, 15, 1]):
        """
        Initialise le réseau de neurones CLASH
        
        Parameters
        ----------
        architecture : list, optional
            Architecture du réseau
            Par défaut: [10, 20, 15, 1]
            - 10 entrées: paramètres CLASH
            - 2 couches cachées (20, 15 neurones)
            - 1 sortie: log10(q)
        """
        self.architecture = architecture
        self.weights = []
        self.biases = []
        self.scaler_params = {}
        self.is_trained = False
        self.training_info = {}
        
        # Initialiser les poids
        self._initialize_weights()
    
    def _initialize_weights(self):
        """Initialise les poids avec Xavier/He initialization"""
        np.random.seed(42)
        for i in range(len(self.architecture) - 1):
            n_in = self.architecture[i]
            n_out = self.architecture[i + 1]
            
            # Xavier initialization
            limit = np.sqrt(6.0 / (n_in + n_out))
            w = np.random.uniform(-limit, limit, (n_in, n_out))
            b = np.zeros(n_out)
            
            self.weights.append(w)
            self.biases.append(b)
    
    def _activation(self, x, activation='tanh'):
        """Fonction d'activation"""
        if activation == 'tanh':
            return np.tanh(x)
        elif activation == 'relu':
            return np.maximum(0, x)
        elif activation == 'sigmoid':
            return 1 / (1 + np.exp(-np.clip(x, -500, 500)))
        else:
            return x  # Linear
    
    def _activation_derivative(self, x, activation='tanh'):
        """Dérivée de la fonction d'activation"""
        if activation == 'tanh':
            return 1 - np.tanh(x)**2
        elif activation == 'relu':
            return (x > 0).astype(float)
        elif activation == 'sigmoid':
            s = self._activation(x, 'sigmoid')
            return s * (1 - s)
        else:
            return np.ones_like(x)
    
    def forward(self, X):
        """
        Propagation avant
        
        Parameters
        ----------
        X : np.ndarray
            Matrice d'entrées normalisées (n_samples, n_features)
        
        Returns
        -------
        np.ndarray
            Prédictions (n_samples,)
        """
        activations = [X]
        
        for i in range(len(self.weights)):
            z = np.dot(activations[-1], self.weights[i]) + self.biases[i]
            
            if i < len(self.weights) - 1:
                # Couches cachées: tanh
                a = self._activation(z, 'tanh')
            else:
                # Couche de sortie: linéaire
                a = z
            
            activations.append(a)
        
        return activations[-1].flatten()
    
    def normalize_features(self, X):
        """
        Normalise les features (Z-score normalization)
        
        Parameters
        ----------
        X : np.ndarray
            Features brutes
        
        Returns
        -------
        np.ndarray
            Features normalisées
        """
        if not self.scaler_params:
            # Calculer mean et std
            self.scaler_params['mean'] = np.mean(X, axis=0)
            self.scaler_params['std'] = np.std(X, axis=0) + 1e-8  # Éviter division par 0
        
        X_norm = (X - self.scaler_params['mean']) / self.scaler_params['std']
        return X_norm
    
    def denormalize_output(self, y_norm):
        """Dénormalise la sortie si nécessaire"""
        return y_norm
    
    def train(self, X, y, epochs=1000, learning_rate=0.01, batch_size=32, 
              validation_split=0.2, verbose=True):
        """
        Entraîne le réseau avec backpropagation
        
        Parameters
        ----------
        X : np.ndarray
            Features (n_samples, n_features)
        y : np.ndarray
            Targets (n_samples,)
        epochs : int
            Nombre d'époques
        learning_rate : float
            Taux d'apprentissage
        batch_size : int
            Taille des mini-batches
        validation_split : float
            Fraction pour validation
        verbose : bool
            Affichage des progrès
        
        Returns
        -------
        dict
            Historique d'entraînement
        """
        # Split train/validation
        n_samples = X.shape[0]
        n_val = int(n_samples * validation_split)
        indices = np.random.permutation(n_samples)
        
        X_train, y_train = X[indices[n_val:]], y[indices[n_val:]]
        X_val, y_val = X[indices[:n_val]], y[indices[:n_val]]
        
        # Normaliser
        X_train_norm = self.normalize_features(X_train)
        X_val_norm = (X_val - self.scaler_params['mean']) / self.scaler_params['std']
        
        # Historique
        history = {'train_loss': [], 'val_loss': [], 'epoch': []}
        
        n_train = X_train_norm.shape[0]
        
        for epoch in range(epochs):
            # Mini-batch training
            indices = np.random.permutation(n_train)
            
            for start_idx in range(0, n_train, batch_size):
                end_idx = min(start_idx + batch_size, n_train)
                batch_indices = indices[start_idx:end_idx]
                
                X_batch = X_train_norm[batch_indices]
                y_batch = y_train[batch_indices]
                
                # Forward pass
                activations = [X_batch]
                zs = []
                
                for i in range(len(self.weights)):
                    z = np.dot(activations[-1], self.weights[i]) + self.biases[i]
                    zs.append(z)
                    
                    if i < len(self.weights) - 1:
                        a = self._activation(z, 'tanh')
                    else:
                        a = z
                    
                    activations.append(a)
                
                # Backward pass
                delta = activations[-1].flatten() - y_batch
                delta = delta.reshape(-1, 1)
                
                nabla_w = [np.zeros_like(w) for w in self.weights]
                nabla_b = [np.zeros_like(b) for b in self.biases]
                
                # Couche de sortie
                nabla_w[-1] = np.dot(activations[-2].T, delta) / len(y_batch)
                nabla_b[-1] = np.mean(delta, axis=0)
                
                # Couches cachées
                for l in range(2, len(self.weights) + 1):
                    z = zs[-l]
                    sp = self._activation_derivative(z, 'tanh')
                    delta = np.dot(delta, self.weights[-l + 1].T) * sp
                    nabla_w[-l] = np.dot(activations[-l - 1].T, delta) / len(y_batch)
                    nabla_b[-l] = np.mean(delta, axis=0)
                
                # Update weights
                for i in range(len(self.weights)):
                    self.weights[i] -= learning_rate * nabla_w[i]
                    self.biases[i] -= learning_rate * nabla_b[i]
            
            # Calculer losses
            if epoch % 10 == 0:
                train_pred = self.forward(X_train_norm)
                train_loss = np.mean((train_pred - y_train)**2)
                
                val_pred = self.forward(X_val_norm)
                val_loss = np.mean((val_pred - y_val)**2)
                
                history['epoch'].append(epoch)
                history['train_loss'].append(train_loss)
                history['val_loss'].append(val_loss)
                
                if verbose and epoch % 100 == 0:
                    print(f"Epoch {epoch}/{epochs} - Train Loss: {train_loss:.6f} - Val Loss: {val_loss:.6f}")
        
        self.is_trained = True
        self.training_info = {
            'epochs': epochs,
            'final_train_loss': history['train_loss'][-1] if history['train_loss'] else None,
            'final_val_loss': history['val_loss'][-1] if history['val_loss'] else None,
            'n_training_samples': n_train,
            'n_validation_samples': n_val
        }
        
        return history
    
    def predict(self, X):
        """
        Prédit le débit de franchissement
        
        Parameters
        ----------
        X : np.ndarray
            Features (n_samples, n_features) ou (n_features,)
        
        Returns
        -------
        np.ndarray or float
            Prédictions log10(q)
        """
        if not self.is_trained:
            warnings.warn("Le réseau n'est pas entraîné. Résultats non fiables.")
        
        # Gérer input 1D
        if X.ndim == 1:
            X = X.reshape(1, -1)
            single_output = True
        else:
            single_output = False
        
        # Normaliser
        X_norm = (X - self.scaler_params['mean']) / self.scaler_params['std']
        
        # Prédire
        y_pred = self.forward(X_norm)
        
        if single_output:
            return y_pred[0]
        return y_pred
    
    def save_model(self, filepath):
        """Sauvegarde le modèle entraîné"""
        model_data = {
            'architecture': self.architecture,
            'weights': self.weights,
            'biases': self.biases,
            'scaler_params': self.scaler_params,
            'is_trained': self.is_trained,
            'training_info': self.training_info
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(model_data, f)
        
        print(f"Modèle sauvegardé: {filepath}")
    
    def load_model(self, filepath):
        """Charge un modèle entraîné"""
        with open(filepath, 'rb') as f:
            model_data = pickle.load(f)
        
        self.architecture = model_data['architecture']
        self.weights = model_data['weights']
        self.biases = model_data['biases']
        self.scaler_params = model_data['scaler_params']
        self.is_trained = model_data['is_trained']
        self.training_info = model_data.get('training_info', {})
        
        print(f"Modèle chargé: {filepath}")
        print(f"Entraîné: {self.is_trained}")
        if self.training_info:
            print(f"Samples d'entraînement: {self.training_info.get('n_training_samples', 'N/A')}")


def load_clash_database(filepath='Data/Database_20050101.xls'):
    """
    Charge la base de données CLASH
    
    Parameters
    ----------
    filepath : str
        Chemin vers le fichier Excel CLASH
    
    Returns
    -------
    pd.DataFrame
        Données CLASH nettoyées
    
    Notes
    -----
    La base CLASH contient > 10,000 tests de franchissement
    avec des configurations variées (digues, murs, etc.)
    """
    try:
        # Charger Excel
        df = pd.read_excel(filepath)
        
        print(f"Base CLASH chargée: {len(df)} tests")
        print(f"Colonnes: {list(df.columns)[:10]}...")  # Premières colonnes
        
        return df
    
    except FileNotFoundError:
        print(f"Erreur: Fichier non trouvé: {filepath}")
        print("Assurez-vous que le fichier CLASH est dans le dossier Data/")
        return None
    except Exception as e:
        print(f"Erreur lors du chargement: {e}")
        return None


def prepare_clash_features(df):
    """
    Prépare les features depuis la base CLASH
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame CLASH brute
    
    Returns
    -------
    tuple
        (X, y, feature_names) où X sont les features, y les targets
    
    Notes
    -----
    Features typiques CLASH:
    - Hm0: hauteur significative
    - Tm-1,0: période spectrale
    - h: profondeur
    - Rc: revanche
    - tan(α): pente
    - γf: rugosité
    - B: largeur berme
    - etc.
    """
    # Cette fonction sera adaptée selon les vraies colonnes CLASH
    # Exemple de structure:
    
    feature_columns = [
        'Hm0',  # ou équivalent dans CLASH
        'Tm_10',
        'h',
        'Rc',
        'tan_alpha',
        'gamma_f',
        'B_berm',
        'h_berm',
        'beta',
        'gamma_beta'
    ]
    
    # Nettoyer les données
    df_clean = df.dropna(subset=['q'])  # Supprimer lignes sans mesure q
    
    # Extraire features et target
    # À adapter selon vraies colonnes CLASH
    print("\nCOLONNES DISPONIBLES DANS CLASH:")
    print(list(df.columns))
    
    return None, None, None  # À implémenter avec vraies données


def train_clash_model(filepath='Data/Database_20050101.xls', 
                      save_path='Data/clash_model.pkl',
                      epochs=1000,
                      verbose=True):
    """
    Entraîne un modèle sur la base CLASH
    
    Parameters
    ----------
    filepath : str
        Chemin vers base CLASH
    save_path : str
        Où sauvegarder le modèle
    epochs : int
        Nombre d'époques
    verbose : bool
        Afficher progression
    
    Returns
    -------
    CLASHNeuralNetwork
        Modèle entraîné
    """
    print("="*70)
    print("ENTRAÎNEMENT RÉSEAU NEURONAL SUR BASE CLASH")
    print("="*70)
    
    # Charger données
    df = load_clash_database(filepath)
    if df is None:
        return None
    
    # Préparer features
    X, y, feature_names = prepare_clash_features(df)
    if X is None:
        print("\n⚠️ Préparation des features à implémenter selon colonnes CLASH réelles")
        return None
    
    # Créer et entraîner modèle
    model = CLASHNeuralNetwork()
    
    print(f"\nArchitecture: {model.architecture}")
    print(f"Training samples: {len(X)}")
    print(f"Features: {feature_names}")
    
    history = model.train(X, y, epochs=epochs, verbose=verbose)
    
    # Sauvegarder
    model.save_model(save_path)
    
    print("\n" + "="*70)
    print("ENTRAÎNEMENT TERMINÉ")
    print("="*70)
    
    return model, history


# Fonction utilitaire pour usage simplifié
def predict_with_clash(Hm0, Tm_10, h, Rc, alpha_deg, 
                       gamma_f=1.0, gamma_beta=1.0,
                       model_path='Data/clash_model.pkl'):
    """
    Prédit avec le modèle CLASH entraîné
    
    Parameters
    ----------
    Hm0, Tm_10, h, Rc, alpha_deg : float
        Paramètres standard
    gamma_f, gamma_beta : float
        Facteurs de réduction
    model_path : str
        Chemin vers modèle sauvegardé
    
    Returns
    -------
    dict
        Prédiction avec informations
    """
    from openeurotop.constants import DEG_TO_RAD
    
    # Charger modèle
    model = CLASHNeuralNetwork()
    try:
        model.load_model(model_path)
    except FileNotFoundError:
        return {
            'q': None,
            'error': f'Modèle non trouvé: {model_path}',
            'recommendation': 'Entraîner le modèle avec train_clash_model()'
        }
    
    # Préparer features
    tan_alpha = np.tan(alpha_deg * DEG_TO_RAD)
    X = np.array([Hm0, Tm_10, h, Rc, tan_alpha, gamma_f, 0, 0, 0, gamma_beta])
    
    # Prédire
    log_q = model.predict(X)
    q = 10**log_q
    
    return {
        'q': q,
        'log_q': log_q,
        'is_trained': model.is_trained,
        'method': 'CLASH Neural Network',
        'training_info': model.training_info
    }

