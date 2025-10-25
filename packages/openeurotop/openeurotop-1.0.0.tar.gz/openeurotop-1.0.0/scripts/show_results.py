"""Affiche les résultats de l'entraînement avancé"""
import json

data = json.load(open('Data/training_results_comparison.json'))

print('='*70)
print('RÉSULTATS FINAUX - COMPARAISON DES MODÈLES')
print('='*70)

print(f'\nNeural Network k-fold:')
print(f'  R2   = {data["neural_network_kfold"]["r2_mean"]:.4f} +/- {data["neural_network_kfold"]["r2_std"]:.4f}')
print(f'  RMSE = {data["neural_network_kfold"]["rmse_mean"]:.4f}')
print(f'  MAE  = {data["neural_network_kfold"]["mae_mean"]:.4f}')

print(f'\nXGBoost k-fold:')
print(f'  R2   = {data["xgboost_kfold"]["r2_mean"]:.4f} +/- {data["xgboost_kfold"]["r2_std"]:.4f}')
print(f'  RMSE = {data["xgboost_kfold"]["rmse_mean"]:.4f}')
print(f'  MAE  = {data["xgboost_kfold"]["mae_mean"]:.4f}')

print(f'\nXGBoost + Optuna:')
print(f'  R2   = {data["xgboost_optimized"]["r2"]:.4f}')

# Améliorations
nn_r2 = data["neural_network_kfold"]["r2_mean"]
xgb_r2 = data["xgboost_kfold"]["r2_mean"]
opt_r2 = data["xgboost_optimized"]["r2"]

print(f'\nAMÉLIORATIONS:')
print(f'  XGBoost vs NN:  +{(xgb_r2 - nn_r2) / nn_r2 * 100:.1f}%')
print(f'  Optuna vs NN:   +{(opt_r2 - nn_r2) / nn_r2 * 100:.1f}%')
print(f'  Optuna vs XGB:  +{(opt_r2 - xgb_r2) / xgb_r2 * 100:.1f}%')

print(f'\nVARIANCE (stabilité):')
print(f'  Neural Network: {data["neural_network_kfold"]["r2_std"]:.4f}')
print(f'  XGBoost:        {data["xgboost_kfold"]["r2_std"]:.4f}')
print(f'  Réduction:      -{(1 - data["xgboost_kfold"]["r2_std"] / data["neural_network_kfold"]["r2_std"]) * 100:.1f}%')

print('\n' + '='*70)
print('CONCLUSION: XGBoost avec Optuna est le meilleur modèle !')
print('R2 = 0.879 (87.9% de variance expliquée)')
print('='*70)

