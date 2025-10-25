"""
OpenEurOtop - Cas Pratique : Digues à Talus
===========================================

Design complet d'une digue de protection portuaire
avec comparaison des 3 méthodes de calcul.

Objectifs :
- Dimensionner une digue à talus
- Optimiser la revanche
- Analyser l'influence de la rugosité
- Comparer EurOtop, Neural Network et XGBoost
"""

# %% [markdown]
# # Cas Pratique : Digues à Talus
# 
# ## Objectif
# Dimensionner une digue à talus et comparer les prédictions
# 
# ## Cas d'étude
# Digue de protection d'un port sur la côte atlantique

# %% [code]
import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, '..')

from openeurotop import overtopping, wave_parameters, reduction_factors
from openeurotop.neural_network_clash import predict_with_clash
from openeurotop.xgboost_model import predict_with_xgboost

print("Modules charges!")

# %% [markdown]
# ## 1. Données de Base
# 
# ### Conditions de houle (tempête centenale)

# %% [code]
# Houle au large
Hm0_deep = 5.5  # m - hauteur significative au large
Tp_deep = 12.0  # s - période de pic

# Conditions au pied de l'ouvrage (après déferlement)
Hm0 = 3.0  # m
Tm_10 = 7.5  # s
h = 12.0  # m - profondeur

# Géométrie de la digue
alpha_deg = 30.0  # degrés - pente du talus (1V:1.73H)
Rc_initial = 2.5  # m - revanche initiale

# Rugosité
gamma_f = 0.5  # enrochements naturels

print("CONDITIONS DE HOULE:")
print(f"  Hm0 au pied = {Hm0} m")
print(f"  Tm-1,0 = {Tm_10} s")
print(f"  Profondeur h = {h} m")
print(f"\nGEOMETRIE DIGUE:")
print(f"  Pente alpha = {alpha_deg} deg (1V:{1/np.tan(np.radians(alpha_deg)):.2f}H)")
print(f"  Revanche Rc = {Rc_initial} m")
print(f"  Rugosite gamma_f = {gamma_f}")

# %% [markdown]
# ## 2. Calcul du Nombre d'Iribarren

# %% [code]
# Calculer le nombre d'Iribarren
xi = wave_parameters.iribarren_number(alpha_deg, Hm0, Tm_10, h)

print(f"Nombre d'Iribarren xi = {xi:.3f}")
print()

if xi < 2.0:
    regime = "DEFERLEMENT PLONGEANT (plunging)"
    description = "Vagues déferlent sur le talus - Fort franchissement attendu"
elif xi < 3.5:
    regime = "DEFERLEMENT GONFLANT (surging)"
    description = "Vagues montent sur le talus - Franchissement modéré"
else:
    regime = "PAS DE DEFERLEMENT"
    description = "Vagues réfléchies - Franchissement faible"

print(f"Regime: {regime}")
print(f"  -> {description}")

# %% [markdown]
# ## 3. Comparaison des 3 Méthodes - Revanche Initiale

# %% [code]
# Méthode 1: Formule EurOtop
q_eurotop = overtopping.digue_talus(Hm0, Tm_10, h, Rc_initial, alpha_deg, gamma_f=gamma_f)

# Méthode 2: Neural Network
result_nn = predict_with_clash(Hm0, Tm_10, h, Rc_initial, alpha_deg, gamma_f=gamma_f)
q_neural = result_nn['q']

# Méthode 3: XGBoost
result_xgb = predict_with_xgboost(Hm0, Tm_10, h, Rc_initial, alpha_deg, gamma_f=gamma_f)
q_xgboost = result_xgb['q']

print("\n" + "="*70)
print(f"DEBITS DE FRANCHISSEMENT (Rc = {Rc_initial:.1f} m)")
print("="*70)
print(f"EurOtop (reference):    q = {q_eurotop:.6f} m3/s/m")
print(f"Neural Network:         q = {q_neural:.6f} m3/s/m  (x{q_neural/q_eurotop:.2f})")
print(f"XGBoost optimise:       q = {q_xgboost:.6f} m3/s/m  (x{q_xgboost/q_eurotop:.2f})")
print("="*70)

# Débit admissible typique
q_max = 0.01  # m3/s/m - limite pour protection zone urbaine

print(f"\nDebit admissible: q_max = {q_max} m3/s/m")
print(f"Status EurOtop: {'[OK]' if q_eurotop < q_max else '[DEPASSEMENT]'}")
print(f"Status XGBoost: {'[OK]' if q_xgboost < q_max else '[DEPASSEMENT]'}")

# %% [markdown]
# ## 4. Optimisation de la Revanche

# %% [code]
# Tester différentes revanches
Rc_range = np.linspace(1.0, 5.0, 30)

q_eurotop_range = []
q_neural_range = []
q_xgboost_range = []

print("Calcul en cours...")
for Rc in Rc_range:
    q_e = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=gamma_f)
    q_n = predict_with_clash(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=gamma_f)['q']
    q_x = predict_with_xgboost(Hm0, Tm_10, h, Rc, alpha_deg, gamma_f=gamma_f)['q']
    
    q_eurotop_range.append(q_e)
    q_neural_range.append(q_n)
    q_xgboost_range.append(q_x)

print("Calcul termine!")

# %% [code]
# Graphique
fig, ax = plt.subplots(figsize=(14, 8))

ax.plot(Rc_range, q_eurotop_range, 'o-', linewidth=2.5, markersize=6,
        color='#2E7D32', label='EurOtop (reference)', alpha=0.8)
ax.plot(Rc_range, q_xgboost_range, 's-', linewidth=2.5, markersize=6,
        color='#1976D2', label='XGBoost (R2=0.88)', alpha=0.8)
ax.plot(Rc_range, q_neural_range, '^-', linewidth=2, markersize=5,
        color='#FF6F00', label='Neural Network (R2=0.67)', alpha=0.7)

# Ligne limite
ax.axhline(y=q_max, color='red', linestyle='--', linewidth=2.5, 
           label=f'Debit admissible ({q_max} m3/s/m)', alpha=0.8)

# Revanche initiale
ax.axvline(x=Rc_initial, color='gray', linestyle=':', linewidth=2,
           label=f'Revanche initiale ({Rc_initial} m)', alpha=0.6)

ax.set_xlabel('Revanche Rc (m)', fontsize=13, fontweight='bold')
ax.set_ylabel('Debit de franchissement q (m3/s/m)', fontsize=13, fontweight='bold')
ax.set_title(f'Optimisation de la revanche\nHm0={Hm0}m, Tm-1,0={Tm_10}s, alpha={alpha_deg}deg, gamma_f={gamma_f}',
             fontsize=15, fontweight='bold')
ax.legend(fontsize=11, loc='upper right')
ax.grid(True, alpha=0.3, linestyle='--')
ax.set_yscale('log')
ax.set_ylim([1e-5, 1])

plt.tight_layout()
plt.savefig('optimisation_revanche.png', dpi=150, bbox_inches='tight')
plt.show()

# Trouver Rc optimal
idx_eurotop = np.where(np.array(q_eurotop_range) < q_max)[0]
if len(idx_eurotop) > 0:
    Rc_optimal_eurotop = Rc_range[idx_eurotop[0]]
    print(f"\nRevanche optimale (EurOtop): Rc = {Rc_optimal_eurotop:.2f} m")
else:
    print("\nAucune revanche ne permet de respecter q_max !")
    Rc_optimal_eurotop = None

idx_xgb = np.where(np.array(q_xgboost_range) < q_max)[0]
if len(idx_xgb) > 0:
    Rc_optimal_xgb = Rc_range[idx_xgb[0]]
    print(f"Revanche optimale (XGBoost): Rc = {Rc_optimal_xgb:.2f} m")
    if Rc_optimal_eurotop:
        print(f"Difference: {abs(Rc_optimal_eurotop - Rc_optimal_xgb):.2f} m")

# %% [markdown]
# ## 5. Influence de la Rugosité

# %% [code]
# Tester différentes rugosités
rugosites = {
    'Beton lisse': 1.0,
    'Beton rugueux': 0.9,
    'Gabions': 0.7,
    'Enrochements': 0.5,
    'Tetrapodes': 0.4
}

results_rugosity = []

for name, gf in rugosites.items():
    q_e = overtopping.digue_talus(Hm0, Tm_10, h, Rc_initial, alpha_deg, gamma_f=gf)
    q_x = predict_with_xgboost(Hm0, Tm_10, h, Rc_initial, alpha_deg, gamma_f=gf)['q']
    
    results_rugosity.append({
        'Type': name,
        'gamma_f': gf,
        'q_EurOtop': q_e,
        'q_XGBoost': q_x,
        'Ecart_%': abs(q_x - q_e) / q_e * 100
    })

# %% [code]
# Graphique comparatif
import pandas as pd
df_rug = pd.DataFrame(results_rugosity)

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))

# Graphique 1: Débits
x = np.arange(len(df_rug))
width = 0.35

ax1.bar(x - width/2, df_rug['q_EurOtop'], width, label='EurOtop', 
        color='#2E7D32', alpha=0.8)
ax1.bar(x + width/2, df_rug['q_XGBoost'], width, label='XGBoost',
        color='#1976D2', alpha=0.8)

ax1.set_xlabel('Type de revetement', fontsize=12, fontweight='bold')
ax1.set_ylabel('Debit q (m3/s/m)', fontsize=12, fontweight='bold')
ax1.set_title('Influence de la rugosite', fontsize=13, fontweight='bold')
ax1.set_xticks(x)
ax1.set_xticklabels(df_rug['Type'], rotation=20, ha='right')
ax1.legend()
ax1.grid(axis='y', alpha=0.3)

# Graphique 2: Écarts
ax2.bar(x, df_rug['Ecart_%'], color='#FF6F00', alpha=0.7)
ax2.set_xlabel('Type de revetement', fontsize=12, fontweight='bold')
ax2.set_ylabel('Ecart XGBoost vs EurOtop (%)', fontsize=12, fontweight='bold')
ax2.set_title('Precision de XGBoost', fontsize=13, fontweight='bold')
ax2.set_xticks(x)
ax2.set_xticklabels(df_rug['Type'], rotation=20, ha='right')
ax2.grid(axis='y', alpha=0.3)

plt.tight_layout()
plt.savefig('influence_rugosite.png', dpi=150, bbox_inches='tight')
plt.show()

print("\nTABLEAU COMPARATIF:")
print(df_rug.to_string(index=False))

# %% [markdown]
# ## 6. Recommandations pour le Design Final

# %% [code]
# Design final basé sur EurOtop
Rc_design = Rc_optimal_eurotop if Rc_optimal_eurotop else 3.5
q_design = overtopping.digue_talus(Hm0, Tm_10, h, Rc_design, alpha_deg, gamma_f=gamma_f)

# Vérification avec XGBoost
q_design_xgb = predict_with_xgboost(Hm0, Tm_10, h, Rc_design, alpha_deg, gamma_f=gamma_f)['q']

print("="*70)
print("DESIGN FINAL - DIGUE A TALUS")
print("="*70)
print(f"\nCONDITIONS DE CALCUL:")
print(f"  Houle centenale: Hm0 = {Hm0} m, Tm-1,0 = {Tm_10} s")
print(f"  Profondeur: h = {h} m")
print(f"\nGEOMETRIE OPTIMISEE:")
print(f"  Pente: alpha = {alpha_deg} deg")
print(f"  Revanche: Rc = {Rc_design:.2f} m")
print(f"  Revetement: gamma_f = {gamma_f} (enrochements)")
print(f"\nDEBITS DE FRANCHISSEMENT:")
print(f"  EurOtop (design):   q = {q_design:.6f} m3/s/m")
print(f"  XGBoost (verif):    q = {q_design_xgb:.6f} m3/s/m")
print(f"  Limite admissible:  q = {q_max:.6f} m3/s/m")
print(f"\nSTATUT: {'[OK - CONFORME]' if q_design < q_max else '[NON CONFORME]'}")
if q_design < q_max:
    print(f"Marge de securite: {(1 - q_design/q_max)*100:.1f}%")
print("="*70)

print("\nRECOMMANDATIONS:")
print("1. Utiliser le calcul EurOtop pour le design definitif")
print("2. XGBoost peut servir de verification rapide")
print("3. Prevoir une marge de securite de 20-30%")
print("4. Verifier l'influence de l'obliquite des vagues")
print("5. Considerer l'effet des bermes si necessaire")

print("\n" + "="*70)
print("SCRIPT TERMINE - Images sauvegardees")
print("="*70)

