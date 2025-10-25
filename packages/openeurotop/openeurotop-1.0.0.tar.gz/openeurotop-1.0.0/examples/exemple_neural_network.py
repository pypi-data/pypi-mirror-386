"""
Exemple d'utilisation du module neural_network avec la base CLASH

Ce script démontre :
1. Utilisation du réseau neuronal de base (démo)
2. Comparaison avec formules empiriques
3. Utilisation du modèle CLASH entraîné
4. Analyse de plusieurs scénarios
"""

import numpy as np
import sys
import os

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.abspath('.'))

from openeurotop import neural_network, overtopping
from openeurotop.neural_network_clash import predict_with_clash, CLASHNeuralNetwork

print("="*80)
print("DÉMONSTRATION - MODULE NEURAL NETWORK")
print("="*80)

# ==============================================================================
# 1. UTILISATION DU RÉSEAU NEURONAL DE BASE (DEMO)
# ==============================================================================

print("\n[1] RÉSEAU NEURONAL DE BASE (non entraîné - démo uniquement)")
print("-"*80)

nn = neural_network.NeuralNetworkOvertoppingPredictor()

print(f"Architecture : {nn.architecture}")
print(f"Entraîné : {nn.is_trained}")

# Prédiction démo
result = nn.predict(
    Hm0=2.5,
    Tm_10=6.0,
    h=10.0,
    Rc=3.0,
    alpha_deg=35.0,
    gamma_f=1.0
)

print(f"\nPrédiction (DEMO) : q = {result['q']:.6f} m3/s/m")
print(f"Warning : {result['warning']}")
print(f"Recommandation : {result['recommendation']}")

# ==============================================================================
# 2. COMPARAISON AVEC FORMULES EMPIRIQUES
# ==============================================================================

print("\n[2] COMPARAISON : Neural Network vs Formules Empiriques")
print("-"*80)

# Calculer avec formule empirique (fiable)
q_empirical = overtopping.digue_talus(
    Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0
)

# Calculer avec neural network (démo)
result_nn = nn.predict(2.5, 6.0, 10.0, 3.0, 35.0)

print(f"Formule empirique (EurOtop) : q = {q_empirical:.6f} m3/s/m  [Recommandé]")
print(f"Neural Network (non entraîné): q = {result_nn['q']:.6f} m3/s/m  [Démo]")
print(f"\nRAPPEL : Pour des calculs de conception, toujours utiliser les formules empiriques.")

# ==============================================================================
# 3. UTILISATION DU MODÈLE CLASH ENTRAÎNÉ
# ==============================================================================

print("\n[3] MODÈLE CLASH ENTRAÎNÉ (9,324 tests réels)")
print("-"*80)

# Vérifier si le modèle existe
if os.path.exists('Data/clash_model.pkl'):
    print("[OK] Modele CLASH disponible")
    
    # Charger le modèle
    model = CLASHNeuralNetwork()
    model.load_model('Data/clash_model.pkl')
    
    print(f"Architecture : {model.architecture}")
    print(f"Training samples : {model.training_info.get('n_training_samples', 'N/A')}")
    print(f"Validation loss : {model.training_info.get('final_val_loss', 'N/A'):.4f}")
    
    # Prédiction avec le modèle CLASH
    result_clash = predict_with_clash(
        Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0
    )
    
    print(f"\nPrédiction CLASH : q = {result_clash['q']:.6f} m3/s/m")
    print(f"log10(q) = {result_clash['log_q']:.4f}")
    print(f"Méthode : {result_clash['method']}")
    
    # Comparaison triple
    print("\n" + "-"*80)
    print("COMPARAISON DES TROIS MÉTHODES :")
    print("-"*80)
    print(f"Formule EurOtop : {q_empirical:.6f} m3/s/m")
    print(f"NN non entraîné : {result_nn['q']:.6f} m3/s/m")
    print(f"NN CLASH (R2=0.78): {result_clash['q']:.6f} m3/s/m")
    
else:
    print("[INFO] Modèle CLASH non trouvé")
    print("Pour entraîner le modèle : python scripts/train_clash_model.py")

# ==============================================================================
# 4. ANALYSE DE PLUSIEURS SCÉNARIOS
# ==============================================================================

print("\n[4] ANALYSE DE PLUSIEURS SCÉNARIOS")
print("-"*80)

scenarios = [
    {
        'name': 'Faible franchissement',
        'params': {'Hm0': 1.5, 'Tm_10': 5.0, 'h': 8.0, 'Rc': 4.0, 'alpha_deg': 40.0}
    },
    {
        'name': 'Franchissement modéré',
        'params': {'Hm0': 2.5, 'Tm_10': 6.5, 'h': 10.0, 'Rc': 2.5, 'alpha_deg': 30.0}
    },
    {
        'name': 'Fort franchissement',
        'params': {'Hm0': 3.5, 'Tm_10': 8.0, 'h': 12.0, 'Rc': 1.0, 'alpha_deg': 25.0}
    },
    {
        'name': 'Structure submergée',
        'params': {'Hm0': 3.0, 'Tm_10': 7.0, 'h': 10.0, 'Rc': -0.5, 'alpha_deg': 35.0}
    }
]

print(f"\n{'Scénario':<25} {'EurOtop':<15} {'CLASH NN':<15} {'Ratio':<10}")
print("-"*80)

for scenario in scenarios:
    name = scenario['name']
    p = scenario['params']
    
    # Formule empirique
    q_emp = overtopping.digue_talus(**p)
    
    # CLASH (si disponible)
    if os.path.exists('Data/clash_model.pkl'):
        result_clash = predict_with_clash(**p)
        q_clash = result_clash['q']
        ratio = q_clash / q_emp if q_emp > 1e-10 else np.inf
        
        print(f"{name:<25} {q_emp:.6f}      {q_clash:.6f}      {ratio:.2f}x")
    else:
        print(f"{name:<25} {q_emp:.6f}      N/A             N/A")

# ==============================================================================
# 5. INFORMATIONS SUR LES RÉSEAUX NEURONAUX
# ==============================================================================

print("\n[5] GUIDE D'UTILISATION DES RÉSEAUX NEURONAUX")
print("-"*80)

print("""
AVANTAGES des réseaux neuronaux :
  - Géométries très complexes (multi-pentes, multi-bermes)
  - Interpolation dans un espace multi-dimensionnel
  - Pas besoin de sélectionner la formule appropriée
  - Peut capturer des interactions non-linéaires complexes

INCONVÉNIENTS :
  - Nécessite une base de données d'entraînement importante (>500 essais)
  - "Boîte noire" - moins de compréhension physique
  - Extrapolation dangereuse hors du domaine d'entraînement
  - Nécessite expertise en machine learning

RECOMMANDATION :
  [OK] Pour des calculs de conception, utiliser les FORMULES EMPIRIQUES
  [!] Ne PAS utiliser les prédictions neuronales non entraînées pour des calculs réels

POUR ALLER PLUS LOIN :
  - Consulter la base de données CLASH (>10,000 essais de franchissement)
  - Étudier Van Gent et al. (2007) pour la méthodologie
  - Utiliser des frameworks comme TensorFlow ou PyTorch pour l'entraînement
""")

# ==============================================================================
# 6. DONNÉES D'ENTRAÎNEMENT (SYNTHÉTIQUES)
# ==============================================================================

print("\n[6] GÉNÉRATION DE DONNÉES SYNTHÉTIQUES (EXEMPLE)")
print("-"*80)

data = neural_network.generate_synthetic_training_example(n_samples=20)

print(f"Nombre d'échantillons : {data['n_samples']}")
print(f"Features : {data['feature_names']}")
print(f"Shape X : {data['X'].shape}")
print(f"Shape y : {data['y'].shape}")
print(f"\nPremier échantillon :")
print(f"  Hm0 = {data['X'][0, 0]:.2f} m")
print(f"  Tm-1,0 = {data['X'][0, 1]:.2f} s")
print(f"  h = {data['X'][0, 2]:.2f} m")
print(f"  Rc = {data['X'][0, 3]:.2f} m")
print(f"  tan(alpha) = {data['X'][0, 4]:.3f}")
print(f"  gamma_f = {data['X'][0, 5]:.2f}")
print(f"  => log10(q) = {data['y'][0]:.3f}")
print(f"  => q = {10**data['y'][0]:.6f} m3/s/m")

print(f"\n{data['warning']}")

# ==============================================================================
# CONCLUSION
# ==============================================================================

print("\n" + "="*80)
print("CONCLUSION")
print("="*80)

if os.path.exists('Data/clash_model.pkl'):
    print("[OK] Module neural_network entièrement fonctionnel avec modèle CLASH entraîné")
    print("\nPERFORMANCES DU MODÈLE CLASH :")
    print("  - Base : 9,324 tests physiques")
    print("  - R² : 0.7772 (77.72%% de variance expliquée)")
    print("  - RMSE (log10) : 0.5707")
    print("\nRECOMMANDATION :")
    print("  - Pour design/conception : Utiliser formules empiriques (overtopping.digue_talus)")
    print("  - Pour recherche/analyse : Le modèle CLASH peut être utilisé avec précaution")
    print("  - Toujours comparer les deux méthodes")
else:
    print("[INFO] Module neural_network disponible en mode démo")
    print("\nPour entraîner le modèle CLASH :")
    print("  python scripts/train_clash_model.py")
    print("\nRECOMMANDATION :")
    print("  - Pour design/conception : Toujours utiliser formules empiriques")

print("\n" + "="*80)

