# Formules techniques - OpenEurOtop

Ce document détaille les formules mathématiques implémentées dans le package OpenEurOtop, basées sur le manuel EurOtop (2018).

## 1. Digues à talus (Sloping structures)

### 1.1 Formules principales

Le franchissement pour les digues à talus dépend du régime de déferlement. Le débit adimensionnel est donné par les deux formules suivantes :

#### Conditions non-déferlantes (plunging/breaking)

```
q / √(g·Hm0³) = 0.067 / √(tan α) · γb · ξm-1,0 · exp(-4.75 · Rc / (ξm-1,0 · γb · γf · γβ · Hm0))
```

Ou de manière simplifiée :

```
q / √(g·Hm0³) = 0.067 · exp(-4.75 · Rc / (γ · Hm0))
```

où γ = γb · γf · γβ

#### Conditions déferlantes (surging)

```
q / √(g·Hm0³) = 0.2 · exp(-2.6 · Rc / (ξm-1,0 · γb · γf · γβ · Hm0))
```

**Sélection de la formule** : On prend le minimum des deux formules.

### 1.2 Nombre d'Iribarren (Surf similarity parameter)

```
ξm-1,0 = tan α / √(s0m-1,0)
```

où :
- α = angle de la pente
- s0m-1,0 = Hm0 / L0m-1,0 (cambrure de la vague)
- L0m-1,0 = g·Tm-1,0² / (2π) (longueur d'onde en eau profonde)

### 1.3 Coefficients

D'après EurOtop 2018 :

| Paramètre | Valeur | Description |
|-----------|--------|-------------|
| a (non-déf.) | 0.067 | Coefficient pour conditions non-déferlantes |
| b (non-déf.) | 4.75 | Exposant pour conditions non-déferlantes |
| a (déf.) | 0.2 | Coefficient pour conditions déferlantes |
| b (déf.) | 2.6 | Exposant pour conditions déferlantes |

## 2. Murs verticaux et composites

### 2.1 Mur vertical simple

Pour un mur vertical :

```
q / √(g·Hm0³) = 0.047 · exp(-2.35 · Rc/Hm0)
```

Cette formule est valable pour :
- 0.1 < Rc/Hm0 < 3.5
- Conditions non-impulsives

### 2.2 Conditions impulsives

Pour des conditions impulsives (h/Hm0 < 0.3), un facteur multiplicateur peut être appliqué :

```
q_impulsive ≈ 1.5 · q_non-impulsive
```

### 2.3 Structures composites

Pour une structure composite (talus + mur vertical), une approche par superposition est utilisée :

```
q = q_talus(Rc_transition) · exp(-2.0 · Rc_vertical/Hm0)
```

où :
- Rc_transition = hauteur de la transition
- Rc_vertical = hauteur du mur vertical au-dessus de la transition

## 3. Facteurs de réduction

### 3.1 Facteur de rugosité γf

Le facteur de rugosité dépend du type de revêtement :

| Type de revêtement | γf | Référence |
|-------------------|-----|-----------|
| Lisse (béton, asphalte) | 1.00 | Table 5.2 |
| Béton rugueux | 0.90 | Table 5.2 |
| Béton avec colonnes | 0.85 | Table 5.2 |
| Enrochement 1 couche | 0.55 | Table 5.2 |
| Enrochement 2 couches | 0.50 | Table 5.2 |
| Enrochement imperméable | 0.45 | Table 5.2 |
| Cubes | 0.47 | Table 5.2 |
| Tétrapodes | 0.38 | Table 5.2 |
| Accropode | 0.46 | Table 5.2 |

### 3.2 Facteur d'obliquité γβ

Pour des vagues obliques :

```
γβ = 1 - 0.0033 · |β|    pour 10° ≤ |β| ≤ 80°
γβ = 1.0                  pour |β| < 10°
```

où β est l'angle entre la direction des vagues et la normale à l'ouvrage.

### 3.3 Facteur de berme γb

Pour une berme, le facteur de réduction dépend de :
- rdB = B/Hm0 (largeur relative de la berme)
- rdh = h_berme/Hm0 (hauteur relative de la berme)

Formule simplifiée :

```
γb = 1.0                          si rdB < 2
γb = 1.0 - 0.04 · (rdB - 2)      si 2 ≤ rdB ≤ 10
γb = 0.6                          si rdB > 10
```

Limite inférieure : γb ≥ 0.6

### 3.4 Facteur de profondeur γh

Pour des profondeurs faibles (shallow water) :

```
γh = 1.0              si h/L0 ≥ 0.3
γh = (h/L0) / 0.3    si h/L0 < 0.3
```

avec γh ≥ 0.5

## 4. Paramètres de vagues

### 4.1 Longueur d'onde

#### Eau profonde

```
L0 = g·T² / (2π)
```

#### Profondeur finie

Relation de dispersion :

```
L = (g·T²)/(2π) · tanh(k·h)
```

où k = 2π/L (résolution itérative)

### 4.2 Cambrure (Wave steepness)

```
s0m-1,0 = Hm0 / L0m-1,0
```

### 4.3 Conversion entre périodes spectrales

Relations approximatives :

```
Tm-1,0 ≈ 1.1 · Tm0,1
Tp ≈ 1.2 · Tm-1,0
Tp ≈ 1.32 · Tm0,1
```

où :
- Tp = période de pic
- Tm-1,0 = période spectrale m-1,0
- Tm0,1 = période spectrale m0,1

## 5. Volumes de franchissement

### 5.1 Volume total

```
V = q · Δt
```

où :
- V = volume par mètre linéaire (m³/m)
- q = débit moyen (m³/s/m)
- Δt = durée de la tempête (s)

### 5.2 Volume par vague

```
V_wave = q · Tm-1,0
```

### 5.3 Proportion de vagues franchissantes

Estimation empirique :

```
P_ow = exp(-0.5 · Rc/Hm0)    si Rc/Hm0 > 1
P_ow = 1.0                    si Rc/Hm0 ≤ 1
```

### 5.4 Volume moyen par vague franchissante

```
V_overtopping = V_wave / P_ow
```

## 6. Domaines de validité

### 6.1 Digues à talus

- 0.5 ≤ Rc/Hm0 ≤ 3.5
- 10° ≤ α ≤ 90°
- 1 ≤ ξm-1,0 ≤ 7
- Revanche positive (Rc > 0)

### 6.2 Murs verticaux

- 0.1 ≤ Rc/Hm0 ≤ 3.5
- h/Hm0 > 0.2 (pour conditions non-impulsives)
- Vagues non-déferlantes à la structure

### 6.3 Structures composites

- Combinaison des limites pour talus et murs
- Transition située entre le niveau d'eau et la crête

## 7. Incertitudes

D'après EurOtop 2018, les incertitudes typiques sont :

- **Digues lisses** : ±30% (écart-type du logarithme ≈ 0.13)
- **Digues rugueuses** : ±40% (écart-type du logarithme ≈ 0.15)
- **Murs verticaux** : ±35% (écart-type du logarithme ≈ 0.14)

Ces incertitudes s'appliquent dans les domaines de validité.

## 8. Formules dérivées

### 8.1 Revanche requise pour un débit cible

Pour une digue à talus, inversement :

```
Rc = -(γ · Hm0 / b) · ln(q / (a · √(g·Hm0³)))
```

où a et b dépendent du régime de déferlement.

### 8.2 Hauteur de vague critique

Pour un débit limite q_lim :

```
Hm0_crit = f(q_lim, Rc, autres paramètres)
```

(résolution numérique requise)

## Références

1. EurOtop (2018). Manual on wave overtopping of sea defences and related structures. 
   Van der Meer, J.W., Allsop, N.W.H., Bruce, T., De Rouck, J., Kortenhaus, A., 
   Pullen, T., Schüttrumpf, H., Troch, P. and Zanuttigh, B.
   www.overtopping-manual.com

2. EurOtop (2018) - Sections spécifiques :
   - Section 5.2 : Sloping structures
   - Section 5.3 : Vertical walls
   - Section 5.4 : Composite structures
   - Table 5.2 : Influence factors

## Notes d'implémentation

### Précision numérique

- Longueur d'onde : résolution itérative avec tolérance 10⁻⁶
- Convergence garantie en < 100 itérations

### Valeurs par défaut

- g = 9.81 m/s²
- γb = 1.0 (pas de berme)
- γf = 1.0 (surface lisse)
- γβ = 1.0 (vagues perpendiculaires)

### Limitations du code

- Pas de correction pour setup/setdown
- Pas de correction pour vent (sauf γcf optionnel)
- Pas de prise en compte du run-up
- Distribution de Weibull non implémentée pour volumes individuels

