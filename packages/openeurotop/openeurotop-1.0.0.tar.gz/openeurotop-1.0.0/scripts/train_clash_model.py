"""
Script pour entraîner un réseau de neurones sur la base de données CLASH
"""

import pandas as pd
import numpy as np
import sys
sys.path.insert(0, '.')

from openeurotop.neural_network_clash import CLASHNeuralNetwork
import matplotlib.pyplot as plt

print("="*70)
print("ENTRAÎNEMENT RÉSEAU NEURONAL - BASE CLASH")
print("="*70)

# 1. Charger les données
print("\n[1/6] Chargement données CLASH...")
df = pd.read_excel('Data/Database_20050101.xls')

# La première ligne réelle contient les unités, on la saute
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

# 2. Nettoyage et sélection des colonnes
print("\n[2/6] Nettoyage et selection...")

# Colonnes d'intérêt (selon CLASH standard)
feature_cols = [
    'Hm0 toe',      # Hauteur significative au pied
    'Tm-1,0 toe',   # Période spectrale
    'h',            # Profondeur
    'Rc',           # Revanche
    'cotad',        # cot(alpha) = 1/tan(alpha) - pente aval
    'gf',           # Gamma_f - facteur rugosité
    'B',            # Largeur berme
    'hb',           # Hauteur berme
    'Ac',           # Armour crest
    'Gc'            # Crest width
]

target_col = 'q'

# Supprimer les lignes avec valeurs manquantes
df_clean = df[feature_cols + [target_col]].copy()
df_clean = df_clean.dropna()

# Filtrer valeurs aberrantes
df_clean = df_clean[df_clean['q'] > 0]  # q positif
df_clean = df_clean[df_clean['Hm0 toe'] > 0]
df_clean = df_clean[df_clean['Tm-1,0 toe'] > 0]
df_clean = df_clean[df_clean['h'] > 0]

print(f"   - {len(df_clean)} tests valides apres nettoyage")
print(f"   - Features: {len(feature_cols)}")

# 3. Préparer X et y
print("\n[3/6] Preparation features et target...")

X = df_clean[feature_cols].values
y_q = df_clean[target_col].values

# Transformer q en log10(q) pour meilleure distribution
y = np.log10(y_q + 1e-10)  # +epsilon pour éviter log(0)

print(f"   - X shape: {X.shape}")
print(f"   - y shape: {y.shape}")
print(f"   - q range: [{y_q.min():.2e}, {y_q.max():.2e}] m3/s/m")
print(f"   - log10(q) range: [{y.min():.2f}, {y.max():.2f}]")

# 4. Créer et entraîner le modèle
print("\n[4/6] Création et entraînement du réseau...")

# Architecture adaptée au nombre de features
n_features = X.shape[1]
model = CLASHNeuralNetwork(architecture=[n_features, 20, 15, 10, 1])

print(f"   - Architecture: {model.architecture}")

# Entraînement
history = model.train(
    X, y,
    epochs=500,
    learning_rate=0.005,
    batch_size=64,
    validation_split=0.2,
    verbose=True
)

# 5. Évaluation
print("\n[5/6] Evaluation du modele...")

X_norm = (X - model.scaler_params['mean']) / model.scaler_params['std']
y_pred = model.forward(X_norm)

# Calcul R²
ss_res = np.sum((y - y_pred)**2)
ss_tot = np.sum((y - np.mean(y))**2)
r2 = 1 - (ss_res / ss_tot)

# RMSE
rmse = np.sqrt(np.mean((y - y_pred)**2))

# MAE
mae = np.mean(np.abs(y - y_pred))

print(f"\n   PERFORMANCES:")
print(f"   - R² : {r2:.4f}")
print(f"   - RMSE (log10): {rmse:.4f}")
print(f"   - MAE (log10): {mae:.4f}")

# Performances sur échelle originale
q_pred_original = 10**y_pred
q_true_original = 10**y
rmse_original = np.sqrt(np.mean((q_true_original - q_pred_original)**2))
print(f"   - RMSE (m3/s/m): {rmse_original:.6f}")

# 6. Sauvegarder le modèle
print("\n[6/6] Sauvegarde du modele...")

model.save_model('Data/clash_model.pkl')

# Sauvegarder aussi les métadonnées
metadata = {
    'n_training_samples': len(df_clean),
    'feature_columns': feature_cols,
    'r2_score': r2,
    'rmse_log10': rmse,
    'mae_log10': mae,
    'rmse_original': rmse_original,
    'q_range': [float(y_q.min()), float(y_q.max())],
    'architecture': model.architecture
}

import json
with open('Data/clash_model_metadata.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print(f"   - Modele: Data/clash_model.pkl")
print(f"   - Metadata: Data/clash_model_metadata.json")

# 7. Visualisation (optionnel)
try:
    print("\n[Bonus] Generation graphiques...")
    
    fig, axes = plt.subplots(2, 2, figsize=(12, 10))
    
    # Learning curves
    ax = axes[0, 0]
    ax.plot(history['epoch'], history['train_loss'], label='Train')
    ax.plot(history['epoch'], history['val_loss'], label='Validation')
    ax.set_xlabel('Epoch')
    ax.set_ylabel('Loss (MSE)')
    ax.set_title('Learning Curves')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    # Prédictions vs mesures (log scale)
    ax = axes[0, 1]
    ax.scatter(y, y_pred, alpha=0.3, s=1)
    ax.plot([y.min(), y.max()], [y.min(), y.max()], 'r--', lw=2)
    ax.set_xlabel('log10(q) mesure')
    ax.set_ylabel('log10(q) predit')
    ax.set_title(f'Predictions vs Mesures (R2={r2:.3f})')
    ax.grid(True, alpha=0.3)
    
    # Résidus
    ax = axes[1, 0]
    residuals = y - y_pred
    ax.scatter(y_pred, residuals, alpha=0.3, s=1)
    ax.axhline(0, color='r', linestyle='--', lw=2)
    ax.set_xlabel('log10(q) predit')
    ax.set_ylabel('Residus')
    ax.set_title('Analyse des residus')
    ax.grid(True, alpha=0.3)
    
    # Distribution résidus
    ax = axes[1, 1]
    ax.hist(residuals, bins=50, edgecolor='black', alpha=0.7)
    ax.set_xlabel('Residus')
    ax.set_ylabel('Frequence')
    ax.set_title('Distribution des residus')
    ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.savefig('Data/clash_training_results.png', dpi=150)
    print(f"   - Graphiques: Data/clash_training_results.png")
    
except Exception as e:
    print(f"   - Graphiques non generes: {e}")

print("\n" + "="*70)
print("ENTRAÎNEMENT TERMINÉ AVEC SUCCÈS!")
print("="*70)
print(f"\nModele pret à l'emploi avec R² = {r2:.4f}")
print(f"Base sur {len(df_clean)} tests CLASH")

