"""
Script d'entraînement avancé avec :
- K-fold cross-validation
- XGBoost
- Optuna pour optimisation des hyperparamètres
- Comparaison de modèles
"""

import pandas as pd
import numpy as np
import sys
import json
sys.path.insert(0, '.')

from openeurotop.neural_network_clash import CLASHNeuralNetwork
from sklearn.model_selection import KFold
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error

print("="*80)
print("ENTRAÎNEMENT AVANCÉ - CLASH DATABASE")
print("="*80)

# ==============================================================================
# 1. CHARGEMENT DES DONNÉES
# ==============================================================================

print("\n[1/7] Chargement données CLASH...")
df = pd.read_excel('Data/Database_20050101.xls')

# Sauter la première ligne (unités)
df = df.iloc[1:].reset_index(drop=True)

# Convertir colonnes numériques
numeric_cols = ['Hm0 deep', 'Tp deep', 'Tm deep', 'Tm-1,0 deep', 'h deep', 
                'm', 'b', 'h', 'Hm0 toe', 'Tp toe', 'Tm toe', 'Tm-1,0 toe',
                'ht', 'Bt', 'gf', 'cotad', 'cotau', 'cotaexcl', 'cotaincl',
                'Rc', 'B', 'hb', 'tanaB', 'Bh', 'Ac', 'Gc', 'RF', 'CF', 'q', 'Pow']

for col in numeric_cols:
    if col in df.columns:
        df[col] = pd.to_numeric(df[col], errors='coerce')

print(f"   - {len(df)} tests charges")

# ==============================================================================
# 2. PRÉPARATION DES DONNÉES
# ==============================================================================

print("\n[2/7] Preparation des donnees...")

feature_cols = [
    'Hm0 toe', 'Tm-1,0 toe', 'h', 'Rc', 'cotad', 
    'gf', 'B', 'hb', 'Ac', 'Gc'
]
target_col = 'q'

# Nettoyage
df_clean = df[feature_cols + [target_col]].copy()
df_clean = df_clean.dropna()
df_clean = df_clean[df_clean['q'] > 0]
df_clean = df_clean[df_clean['Hm0 toe'] > 0]
df_clean = df_clean[df_clean['Tm-1,0 toe'] > 0]
df_clean = df_clean[df_clean['h'] > 0]

print(f"   - {len(df_clean)} tests valides")

# Features et target
X = df_clean[feature_cols].values
y_q = df_clean[target_col].values
y = np.log10(y_q + 1e-10)

print(f"   - X shape: {X.shape}")
print(f"   - y shape: {y.shape}")

# ==============================================================================
# 3. K-FOLD CROSS-VALIDATION AVEC RÉSEAU DE NEURONES
# ==============================================================================

print("\n[3/7] K-fold cross-validation (Neural Network)...")

n_folds = 5
kf = KFold(n_splits=n_folds, shuffle=True, random_state=42)

print(f"   - {n_folds}-fold cross-validation")

nn_scores = {
    'r2': [],
    'rmse': [],
    'mae': []
}

for fold, (train_idx, val_idx) in enumerate(kf.split(X), 1):
    print(f"\n   Fold {fold}/{n_folds}:")
    
    X_train, X_val = X[train_idx], X[val_idx]
    y_train, y_val = y[train_idx], y[val_idx]
    
    # Entraîner modèle
    model = CLASHNeuralNetwork(architecture=[10, 20, 15, 1])
    history = model.train(
        X_train, y_train,
        epochs=300,
        learning_rate=0.005,
        batch_size=64,
        validation_split=0.2,
        verbose=False
    )
    
    # Prédire sur validation
    y_pred = model.predict(X_val)
    
    # Métriques
    r2 = r2_score(y_val, y_pred)
    rmse = np.sqrt(mean_squared_error(y_val, y_pred))
    mae = mean_absolute_error(y_val, y_pred)
    
    nn_scores['r2'].append(r2)
    nn_scores['rmse'].append(rmse)
    nn_scores['mae'].append(mae)
    
    print(f"      R2={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f}")

print(f"\n   RÉSULTATS K-FOLD (Neural Network):")
print(f"   - R2   : {np.mean(nn_scores['r2']):.4f} +/- {np.std(nn_scores['r2']):.4f}")
print(f"   - RMSE : {np.mean(nn_scores['rmse']):.4f} +/- {np.std(nn_scores['rmse']):.4f}")
print(f"   - MAE  : {np.mean(nn_scores['mae']):.4f} +/- {np.std(nn_scores['mae']):.4f}")

# ==============================================================================
# 4. XGBOOST AVEC K-FOLD
# ==============================================================================

print("\n[4/7] K-fold cross-validation (XGBoost)...")

try:
    import xgboost as xgb
    
    xgb_scores = {
        'r2': [],
        'rmse': [],
        'mae': []
    }
    
    for fold, (train_idx, val_idx) in enumerate(kf.split(X), 1):
        print(f"\n   Fold {fold}/{n_folds}:")
        
        X_train, X_val = X[train_idx], X[val_idx]
        y_train, y_val = y[train_idx], y[val_idx]
        
        # Entraîner XGBoost
        xgb_model = xgb.XGBRegressor(
            n_estimators=200,
            learning_rate=0.05,
            max_depth=6,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbosity=0
        )
        
        xgb_model.fit(X_train, y_train)
        
        # Prédire
        y_pred = xgb_model.predict(X_val)
        
        # Métriques
        r2 = r2_score(y_val, y_pred)
        rmse = np.sqrt(mean_squared_error(y_val, y_pred))
        mae = mean_absolute_error(y_val, y_pred)
        
        xgb_scores['r2'].append(r2)
        xgb_scores['rmse'].append(rmse)
        xgb_scores['mae'].append(mae)
        
        print(f"      R2={r2:.4f}, RMSE={rmse:.4f}, MAE={mae:.4f}")
    
    print(f"\n   RÉSULTATS K-FOLD (XGBoost):")
    print(f"   - R2   : {np.mean(xgb_scores['r2']):.4f} +/- {np.std(xgb_scores['r2']):.4f}")
    print(f"   - RMSE : {np.mean(xgb_scores['rmse']):.4f} +/- {np.std(xgb_scores['rmse']):.4f}")
    print(f"   - MAE  : {np.mean(xgb_scores['mae']):.4f} +/- {np.std(xgb_scores['mae']):.4f}")
    
    xgboost_available = True
    
except ImportError:
    print("\n   [INFO] XGBoost non installé. Installation : pip install xgboost")
    xgboost_available = False
    xgb_scores = None

# ==============================================================================
# 5. OPTIMISATION AVEC OPTUNA (XGBoost)
# ==============================================================================

print("\n[5/7] Optimisation hyperparametres avec Optuna (XGBoost)...")

if xgboost_available:
    try:
        import optuna
        
        def objective(trial):
            """Fonction objectif pour Optuna"""
            params = {
                'n_estimators': trial.suggest_int('n_estimators', 100, 500),
                'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                'max_depth': trial.suggest_int('max_depth', 3, 10),
                'subsample': trial.suggest_float('subsample', 0.5, 1.0),
                'colsample_bytree': trial.suggest_float('colsample_bytree', 0.5, 1.0),
                'min_child_weight': trial.suggest_int('min_child_weight', 1, 10),
                'gamma': trial.suggest_float('gamma', 0, 1),
                'random_state': 42,
                'verbosity': 0
            }
            
            # Cross-validation
            scores = []
            for train_idx, val_idx in kf.split(X):
                X_train, X_val = X[train_idx], X[val_idx]
                y_train, y_val = y[train_idx], y[val_idx]
                
                model = xgb.XGBRegressor(**params)
                model.fit(X_train, y_train)
                
                y_pred = model.predict(X_val)
                r2 = r2_score(y_val, y_pred)
                scores.append(r2)
            
            return np.mean(scores)
        
        # Créer étude Optuna
        study = optuna.create_study(
            direction='maximize',
            sampler=optuna.samplers.TPESampler(seed=42)
        )
        
        print("   - Lancement optimisation (30 trials)...")
        study.optimize(objective, n_trials=30, show_progress_bar=False)
        
        print(f"\n   MEILLEURS HYPERPARAMÈTRES:")
        for key, value in study.best_params.items():
            print(f"   - {key}: {value}")
        
        print(f"\n   Meilleur R2 : {study.best_value:.4f}")
        
        # Entraîner modèle final avec meilleurs params
        best_params = study.best_params
        best_params['random_state'] = 42
        best_params['verbosity'] = 0
        
        best_model = xgb.XGBRegressor(**best_params)
        best_model.fit(X, y)
        
        # Sauvegarder modèle optimisé
        import pickle
        with open('Data/xgboost_optimized_model.pkl', 'wb') as f:
            pickle.dump(best_model, f)
        
        # Sauvegarder params
        with open('Data/xgboost_best_params.json', 'w') as f:
            json.dump(study.best_params, f, indent=2)
        
        print(f"\n   Modèle sauvegardé : Data/xgboost_optimized_model.pkl")
        
        optuna_available = True
        
    except ImportError:
        print("\n   [INFO] Optuna non installé. Installation : pip install optuna")
        optuna_available = False
else:
    optuna_available = False

# ==============================================================================
# 6. ENTRAÎNEMENT MODÈLE FINAL (Neural Network)
# ==============================================================================

print("\n[6/7] Entrainement modele final (Neural Network)...")

final_model = CLASHNeuralNetwork(architecture=[10, 20, 15, 10, 1])
history = final_model.train(
    X, y,
    epochs=500,
    learning_rate=0.005,
    batch_size=64,
    validation_split=0.2,
    verbose=True
)

# Évaluation
y_pred = final_model.predict(X)
r2_final = r2_score(y, y_pred)
rmse_final = np.sqrt(mean_squared_error(y, y_pred))
mae_final = mean_absolute_error(y, y_pred)

print(f"\n   PERFORMANCES FINALES (Neural Network):")
print(f"   - R2   : {r2_final:.4f}")
print(f"   - RMSE : {rmse_final:.4f}")
print(f"   - MAE  : {mae_final:.4f}")

# Sauvegarder
final_model.save_model('Data/clash_neural_network_final.pkl')

# ==============================================================================
# 7. COMPARAISON DES MODÈLES
# ==============================================================================

print("\n[7/7] Comparaison des modeles...")

print(f"\n{'Modèle':<30} {'R2 (mean)':<12} {'RMSE (mean)':<12} {'MAE (mean)':<12}")
print("-"*80)

print(f"{'Neural Network (k-fold)':<30} {np.mean(nn_scores['r2']):>11.4f}  "
      f"{np.mean(nn_scores['rmse']):>11.4f}  {np.mean(nn_scores['mae']):>11.4f}")

if xgboost_available:
    print(f"{'XGBoost (k-fold)':<30} {np.mean(xgb_scores['r2']):>11.4f}  "
          f"{np.mean(xgb_scores['rmse']):>11.4f}  {np.mean(xgb_scores['mae']):>11.4f}")
    
    if optuna_available:
        print(f"{'XGBoost optimisé (Optuna)':<30} {study.best_value:>11.4f}  "
              f"{'N/A':>11}  {'N/A':>11}")

print(f"{'Neural Network (final)':<30} {r2_final:>11.4f}  "
      f"{rmse_final:>11.4f}  {mae_final:>11.4f}")

# Sauvegarder résultats
results = {
    'neural_network_kfold': {
        'r2_mean': float(np.mean(nn_scores['r2'])),
        'r2_std': float(np.std(nn_scores['r2'])),
        'rmse_mean': float(np.mean(nn_scores['rmse'])),
        'mae_mean': float(np.mean(nn_scores['mae']))
    },
    'neural_network_final': {
        'r2': float(r2_final),
        'rmse': float(rmse_final),
        'mae': float(mae_final)
    }
}

if xgboost_available:
    results['xgboost_kfold'] = {
        'r2_mean': float(np.mean(xgb_scores['r2'])),
        'r2_std': float(np.std(xgb_scores['r2'])),
        'rmse_mean': float(np.mean(xgb_scores['rmse'])),
        'mae_mean': float(np.mean(xgb_scores['mae']))
    }
    
    if optuna_available:
        results['xgboost_optimized'] = {
            'r2': float(study.best_value),
            'best_params': study.best_params
        }

with open('Data/training_results_comparison.json', 'w') as f:
    json.dump(results, f, indent=2)

print("\n" + "="*80)
print("ENTRAÎNEMENT TERMINÉ")
print("="*80)
print("\nMODÈLES SAUVEGARDÉS:")
print("  - Data/clash_neural_network_final.pkl")
if xgboost_available and optuna_available:
    print("  - Data/xgboost_optimized_model.pkl")
print("\nRÉSULTATS:")
print("  - Data/training_results_comparison.json")

