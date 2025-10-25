# Guide Utilisateur - OpenEurOtop

## Introduction

OpenEurOtop est une implémentation Python du guide EurOtop (2018) pour le calcul du franchissement de vagues sur les ouvrages côtiers. Ce guide vous aidera à utiliser le package pour vos calculs d'ingénierie côtière.

## Installation

```bash
# Installation depuis le répertoire local
cd OpenEurOtop
pip install -e .

# Ou installation des dépendances uniquement
pip install -r requirements.txt
```

## Concepts de base

### Débit de franchissement moyen

Le débit de franchissement moyen `q` (en m³/s/m) représente le volume d'eau franchissant la crête d'un ouvrage par unité de temps et par mètre linéaire.

### Paramètres principaux

- **Hm0** : Hauteur significative spectrale des vagues (m)
- **Tm-1,0** : Période spectrale moyenne (s)
- **h** : Profondeur d'eau au pied de l'ouvrage (m)
- **Rc** : Revanche (freeboard) - hauteur de crête au-dessus du niveau d'eau (m)
- **α** : Angle de pente du talus (degrés)

### Facteurs de réduction

- **γf** : Facteur de rugosité (rugosité du revêtement)
- **γβ** : Facteur d'obliquité (angle d'incidence des vagues)
- **γb** : Facteur de berme (présence d'une berme)

## Exemples d'utilisation

### 1. Cas simple : Digue à talus lisse

```python
from openeurotop import overtopping

# Calcul du franchissement
q = overtopping.digue_talus(
    Hm0=2.5,      # Hauteur significative (m)
    Tm_10=6.0,    # Période moyenne (s)
    h=10.0,       # Profondeur d'eau (m)
    Rc=3.0,       # Revanche (m)
    alpha_deg=35.0,  # Pente (degrés)
    gamma_f=1.0,  # Surface lisse
    gamma_beta=1.0,  # Vagues perpendiculaires
    gamma_b=1.0   # Pas de berme
)

print(f"Débit de franchissement : {q:.6f} m³/s/m")
print(f"Débit de franchissement : {q*1000:.3f} l/s/m")
```

### 2. Digue en enrochement

```python
from openeurotop import overtopping

# Méthode 1 : Avec calcul automatique des facteurs
result = overtopping.digue_talus_detailed(
    Hm0=3.0,
    Tm_10=7.0,
    h=12.0,
    Rc=4.0,
    alpha_deg=33.7,
    type_revetement="enrochement_2couches"
)

print(f"Débit : {result['q']*1000:.3f} l/s/m")
print(f"Facteur de rugosité : {result['gamma_f']:.2f}")
print(f"Nombre d'Iribarren : {result['xi']:.3f}")

# Méthode 2 : Fonction spécialisée
q = overtopping.digue_en_enrochement(
    Hm0=3.0,
    Tm_10=7.0,
    h=12.0,
    Rc=4.0,
    alpha_deg=33.7,
    Dn50=1.5,  # Diamètre nominal des blocs
    n_layers=2,
    permeability="permeable"
)
```

### 3. Mur vertical

```python
from openeurotop import overtopping

q = overtopping.mur_vertical(
    Hm0=2.0,
    Tm_10=5.5,
    h=8.0,
    Rc=2.5
)

print(f"Débit : {q*1000:.3f} l/s/m")
```

### 4. Structure composite (talus + mur)

```python
from openeurotop import overtopping

q = overtopping.structure_composite(
    Hm0=2.8,
    Tm_10=6.5,
    h=10.0,
    Rc=5.0,
    alpha_lower_deg=30.0,
    h_transition=2.0,  # Hauteur de transition
    gamma_f_lower=0.9,  # Béton rugueux en partie basse
    gamma_f_upper=1.0   # Mur lisse en partie haute
)
```

### 5. Prise en compte de l'obliquité

```python
from openeurotop import overtopping, reduction_factors

# Calcul du facteur d'obliquité
beta = 30  # Angle d'obliquité (degrés)
gamma_beta = reduction_factors.gamma_beta_obliquity(beta)

# Calcul avec obliquité
q = overtopping.digue_talus(
    Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0,
    gamma_beta=gamma_beta
)

print(f"Obliquité : {beta}°")
print(f"Facteur γβ : {gamma_beta:.3f}")
print(f"Débit : {q*1000:.3f} l/s/m")
```

### 6. Calcul de volumes

```python
from openeurotop import overtopping

# D'abord calculer le débit
q = overtopping.digue_talus(
    Hm0=2.5, Tm_10=6.0, h=10.0, Rc=3.0, alpha_deg=35.0
)

# Puis calculer les volumes pour une tempête de 4 heures
volumes = overtopping.calcul_volumes_franchissement(q, duree_tempete_heures=4.0)

print(f"Volume total : {volumes['volume_total_m3_per_m']:.2f} m³/m")
print(f"Volume total : {volumes['volume_liters_per_m']:.0f} litres/m")
```

## Types de revêtements disponibles

Le facteur de rugosité `gamma_f` peut être obtenu automatiquement pour les types suivants :

```python
from openeurotop import reduction_factors

types_disponibles = [
    "lisse",                    # γf = 1.00 - Béton lisse, asphalte
    "beton_rugueux",           # γf = 0.90 - Béton avec rugosité
    "beton_colonne",           # γf = 0.85 - Béton avec colonnes
    "enrochement_1couche",     # γf = 0.55 - Enrochement 1 couche
    "enrochement_2couches",    # γf = 0.50 - Enrochement 2 couches
    "enrochement_impermeable", # γf = 0.45 - Enrochement sur noyau imperméable
    "cubes",                   # γf = 0.47 - Cubes de béton
    "tetrapodes",              # γf = 0.38 - Tétrapodes
    "accropode",               # γf = 0.46 - Accropode
    "xbloc",                   # γf = 0.45 - X-bloc
    "core_loc",                # γf = 0.44 - Core-Loc
]

# Utilisation
gamma_f = reduction_factors.gamma_f_roughness("tetrapodes")
print(f"γf pour tétrapodes : {gamma_f}")
```

## Paramètres de vagues

```python
from openeurotop import wave_parameters

# Longueur d'onde en eau profonde
L0 = wave_parameters.wave_length_deep_water(T=6.0)

# Longueur d'onde pour une profondeur donnée
L = wave_parameters.wave_length(T=6.0, h=10.0)

# Cambrure de la vague
s0 = wave_parameters.wave_steepness(Hm0=2.5, Tm_10=6.0)

# Nombre d'Iribarren
xi = wave_parameters.iribarren_number(alpha_deg=35.0, Hm0=2.5, Tm_10=6.0)

# Conversion entre périodes spectrales
periodes = wave_parameters.spectral_period_conversion(Tp=7.2)
print(f"Tp = {periodes['Tp']:.1f} s")
print(f"Tm-1,0 = {periodes['Tm_10']:.1f} s")
print(f"Tm0,1 = {periodes['Tm01']:.1f} s")
```

## Statistiques par vagues individuelles

```python
from openeurotop import overtopping

# Estimation du franchissement par vagues individuelles
stats = overtopping.discharge_individual_waves(
    Hm0=2.5, Tm_10=6.0, h=10.0, Rc=2.0, alpha_deg=35.0,
    N_waves=2400  # Nombre de vagues pendant la tempête
)

print(f"Débit moyen : {stats['q_mean']*1000:.3f} l/s/m")
print(f"Proportion de vagues franchissantes : {stats['P_overtopping']*100:.1f}%")
print(f"Nombre de vagues franchissantes : {stats['N_overtopping_waves']}")
print(f"Volume moyen par vague franchissante : {stats['V_per_overtopping_wave']:.3f} m³/m")
```

## Limites et validité

### Domaines de validité

Les formules EurOtop sont valides dans les plages suivantes :

- **Rc/Hm0** : 0.5 à 3.5 (recommandé)
- **Pente α** : 10° à 90°
- **Nombre d'Iribarren ξ** : 1 à 7 (selon le type de structure)

### Précautions

1. **Extrapolation** : Soyez prudent en dehors des domaines de validité
2. **Structures complexes** : Les structures très complexes peuvent nécessiter des études spécifiques
3. **Conditions extrêmes** : Pour des conditions extrêmes, validez avec des essais physiques
4. **Incertitudes** : Les résultats ont une incertitude intrinsèque (voir EurOtop 2018)

## Bonnes pratiques

### 1. Vérification des résultats

Toujours vérifier la cohérence physique des résultats :

```python
# Vérifier que le débit diminue avec la revanche
q1 = overtopping.digue_talus(Hm0=2.5, Tm_10=6.0, h=10.0, Rc=2.0, alpha_deg=35.0)
q2 = overtopping.digue_talus(Hm0=2.5, Tm_10=6.0, h=10.0, Rc=4.0, alpha_deg=35.0)
assert q2 < q1, "Plus de revanche devrait donner moins de franchissement"
```

### 2. Études paramétriques

Pour une étude paramétrique :

```python
import numpy as np
import matplotlib.pyplot as plt

revanches = np.linspace(1.0, 5.0, 20)
debits = []

for Rc in revanches:
    q = overtopping.digue_talus(
        Hm0=2.5, Tm_10=6.0, h=10.0, Rc=Rc, alpha_deg=35.0
    )
    debits.append(q * 1000)  # Conversion en l/s/m

plt.figure(figsize=(10, 6))
plt.plot(revanches, debits, 'b-', linewidth=2)
plt.xlabel('Revanche Rc (m)')
plt.ylabel('Débit de franchissement q (l/s/m)')
plt.grid(True)
plt.title('Franchissement en fonction de la revanche')
plt.show()
```

### 3. Documentation des calculs

Toujours documenter vos calculs :

```python
import json

calcul = {
    "projet": "Digue de protection",
    "date": "2025-10-23",
    "parametres": {
        "Hm0": 2.5,
        "Tm_10": 6.0,
        "h": 10.0,
        "Rc": 3.0,
        "alpha_deg": 35.0,
        "type_revetement": "enrochement_2couches"
    },
    "resultats": {}
}

result = overtopping.digue_talus_detailed(**calcul["parametres"])
calcul["resultats"] = result

# Sauvegarder
with open("calcul_franchissement.json", "w") as f:
    json.dump(calcul, f, indent=2, default=float)
```

## Références

- EurOtop (2018). Manual on wave overtopping of sea defences and related structures. 
  www.overtopping-manual.com

## Support

Pour des questions ou des problèmes :
- Consultez les exemples dans le dossier `examples/`
- Exécutez les tests dans le dossier `tests/`
- Référez-vous au manuel EurOtop original pour plus de détails théoriques

