"""
OpenEurOtop - Cas Pratique : Murs Verticaux
===========================================

Analyse comparative pour les ouvrages verticaux (quais, digues verticales)
avec les 3 méthodes de calcul.
"""

# %% [markdown]
# # Murs Verticaux - Comparaison des Méthodes
#
# Cas d'étude : Quai portuaire avec parement vertical

# %% [code]
import numpy as np
import matplotlib.pyplot as plt
import sys
sys.path.insert(0, '..')

from openeurotop import overtopping
from openeurotop.neural_network_clash import predict_with_clash
from openeurotop.xgboost_model import predict_with_xgboost

print("Modules charges!")

# %% [markdown]
# ## 1. Conditions de Base

# %% [code]
# Conditions de houle
Hm0 = 2.8  # m
Tm_10 = 6.5  # s
h = 15.0  # m - grande profondeur
Rc = 2.0  # m

print("CONDITIONS:")
print(f"  Hm0 = {Hm0} m")
print(f"  Tm-1,0 = {Tm_10} s")
print(f"  Profondeur h = {h} m (mur vertical)")
print(f"  Revanche Rc = {Rc} m")

# %% [markdown]
# ## 2. Calcul pour Mur Vertical Lisse

# %% [code]
# EurOtop
q_eurotop = overtopping.mur_vertical(Hm0, Tm_10, h, Rc)

print("\n" + "="*60)
print("MURS VERTICAUX")
print("="*60)
print(f"EurOtop (reference):    q = {q_eurotop:.6f} m3/s/m")
print("="*60)

print("\nNote: Neural Network et XGBoost sont entraines sur base CLASH")
print("qui inclut aussi des structures verticales")

# %% [markdown]
# ## 3. Comparaison avec Talus Équivalent
#
# Pour voir la différence entre mur vertical et digue à talus

# %% [code]
# Comparaison avec différentes pentes
angles = [90, 60, 45, 30, 20]  # 90 = vertical
q_values = []

for alpha in angles:
    if alpha == 90:
        q = overtopping.mur_vertical(Hm0, Tm_10, h, Rc)
    else:
        q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha)
    q_values.append(q)
    
# Graphique
fig, ax = plt.subplots(figsize=(12, 7))

ax.plot(angles, q_values, 'o-', linewidth=3, markersize=10,
        color='#1976D2', label='Debit de franchissement')

ax.set_xlabel('Angle de pente (deg)', fontsize=13, fontweight='bold')
ax.set_ylabel('Debit q (m3/s/m)', fontsize=13, fontweight='bold')
ax.set_title(f'Influence de la pente\nHm0={Hm0}m, Rc={Rc}m',
             fontsize=15, fontweight='bold')
ax.axvline(x=90, color='red', linestyle='--', linewidth=2, label='Mur vertical', alpha=0.7)
ax.grid(True, alpha=0.3, linestyle='--')
ax.legend(fontsize=12)
ax.set_yscale('log')

plt.tight_layout()
plt.savefig('mur_vertical_vs_talus.png', dpi=150)
plt.show()

print("\nOBSERVATION:")
print("Le franchissement diminue quand la pente augmente (talus plus raide)")

# %% [markdown]
# ## 4. Variation de la Revanche

# %% [code]
Rc_range = np.linspace(0.5, 4.0, 25)
q_vertical = []

for Rc_var in Rc_range:
    q = overtopping.mur_vertical(Hm0, Tm_10, h, Rc_var)
    q_vertical.append(q)

fig, ax = plt.subplots(figsize=(12, 7))
ax.plot(Rc_range, q_vertical, 'o-', linewidth=3, markersize=8,
        color='#2E7D32', label='Mur vertical (EurOtop)')

# Limites typiques
q_limits = {
    'Zone urbaine': 0.002,
    'Zone industrielle': 0.01,
    'Zone portuaire': 0.05
}

for name, q_lim in q_limits.items():
    ax.axhline(y=q_lim, linestyle='--', linewidth=2, label=f'{name} (q={q_lim})', alpha=0.7)

ax.set_xlabel('Revanche Rc (m)', fontsize=13, fontweight='bold')
ax.set_ylabel('Debit q (m3/s/m)', fontsize=13, fontweight='bold')
ax.set_title(f'Mur vertical - Influence revanche\nHm0={Hm0}m, Tm-1,0={Tm_10}s',
             fontsize=15, fontweight='bold')
ax.legend(fontsize=11, loc='upper right')
ax.grid(True, alpha=0.3)
ax.set_yscale('log')

plt.tight_layout()
plt.savefig('mur_vertical_revanche.png', dpi=150)
plt.show()

# Trouver revanches nécessaires
for name, q_lim in q_limits.items():
    idx = np.where(np.array(q_vertical) < q_lim)[0]
    if len(idx) > 0:
        Rc_needed = Rc_range[idx[0]]
        print(f"{name}: Rc >= {Rc_needed:.2f} m (pour q < {q_lim})")

print("\n" + "="*60)
print("SCRIPT TERMINE")
print("="*60)

