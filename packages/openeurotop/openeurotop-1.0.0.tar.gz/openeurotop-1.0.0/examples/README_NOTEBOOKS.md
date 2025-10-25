# Notebooks et Exemples - OpenEurOtop

## 📚 Suite Complète d'Exemples pour Ingénieurs

Cette collection de notebooks compare systématiquement les **3 méthodes** de calcul disponibles dans OpenEurOtop :

1. **Formules empiriques EurOtop** (référence scientifique) ✅
2. **Neural Network CLASH** (R² = 0.67) ⚠️
3. **XGBoost optimisé** (R² = 0.88) 🏆

---

## 🎯 Liste des Notebooks

### 01. Introduction Comparative
**Fichier** : `notebook_01_introduction_comparative.py`

**Contenu** :
- Exemple simple sur digue à talus
- Variation de la revanche
- Comparaison sur plusieurs scénarios
- Graphiques comparatifs
- Interprétation des résultats

**Pour qui** : Débutants, découverte du package

**Durée** : ~10 minutes

---

### 02. Digues à Talus - Cas Complet
**Fichier** : `notebook_02_digues_talus_complete.py`

**Contenu** :
- Design complet d'une digue portuaire
- Calcul du nombre d'Iribarren
- Optimisation de la revanche
- Influence de la rugosité (5 types)
- Recommandations de design

**Pour qui** : Ingénieurs en conception

**Durée** : ~20 minutes

---

### 03. Murs Verticaux
**Fichier** : `notebook_03_murs_verticaux.py`

**Contenu** :
- Calcul pour ouvrages verticaux
- Comparaison mur vertical vs talus
- Variation de la revanche
- Limites pour différentes zones

**Pour qui** : Design de quais et digues verticales

**Durée** : ~15 minutes

---

## 🚀 Utilisation

### Option 1 : Exécuter comme script Python
```bash
cd examples
python notebook_01_introduction_comparative.py
```

Les graphiques seront sauvegardés automatiquement !

### Option 2 : Convertir en Jupyter Notebook
```bash
# Installer jupytext si nécessaire
pip install jupytext

# Convertir en notebook
jupytext --to notebook notebook_01_introduction_comparative.py

# Ou convertir tous les fichiers
jupytext --to notebook notebook_*.py
```

### Option 3 : Ouvrir directement dans Jupyter
Jupyter Lab et VSCode peuvent ouvrir les fichiers `.py` avec le format "percent" comme des notebooks !

---

## 📊 Résultats Attendus

### Graphiques Générés

Chaque notebook génère des graphiques PNG de haute qualité :

1. **Comparaison des 3 méthodes** (barres)
2. **Influence de la revanche** (courbes)
3. **Scénarios multiples** (barres groupées)
4. **Influence de la rugosité** (2 panels)
5. **Optimisation** (courbes avec seuils)

### Tableaux Comparatifs

Tableaux pandas avec :
- Débits pour chaque méthode
- Écarts en %
- Recommandations

---

## 📈 Performances Comparées

| Méthode | R² | RMSE | Stabilité | Recommandation |
|---------|-----|------|-----------|----------------|
| **EurOtop** | - | - | ✅ | **DESIGN** |
| **XGBoost** | 0.88 | 0.46 | ✅ | Vérification |
| **Neural Network** | 0.67 | 0.69 | ⚠️ | Recherche |

---

## 💡 Conseils d'Utilisation

### Pour le Design
✅ **Toujours utiliser les formules EurOtop**
- Validées scientifiquement
- Domaine de validité connu
- Recommandées par normes

### Pour la Vérification
✅ **XGBoost acceptable**
- Rapide pour tester plusieurs variants
- Écart moyen < 20% vs EurOtop
- Toujours valider avec EurOtop

### Pour la Recherche
⚠️ **Comparer les 3 méthodes**
- Identifier les cas limites
- Analyser les divergences
- Améliorer les modèles

---

## 🎓 Cas d'Usage Typiques

### 1. Étude de Pré-Dimensionnement
```python
# Tester rapidement plusieurs configurations
for Rc in [1.0, 2.0, 3.0, 4.0]:
    q_xgb = predict_with_xgboost(Hm0, Tm_10, h, Rc, alpha)['q']
    print(f"Rc={Rc}m : q={q_xgb:.6f}")

# Puis affiner avec EurOtop
q_final = overtopping.digue_talus(Hm0, Tm_10, h, Rc_optimal, alpha)
```

### 2. Analyse de Sensibilité
```python
# Varier plusieurs paramètres
import itertools
Hm0_list = [2.0, 2.5, 3.0]
Rc_list = [2.0, 3.0, 4.0]

for Hm0, Rc in itertools.product(Hm0_list, Rc_list):
    q_e = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha)
    q_x = predict_with_xgboost(Hm0, Tm_10, h, Rc, alpha)['q']
    print(f"Hm0={Hm0}, Rc={Rc}: EurOtop={q_e:.6f}, XGB={q_x:.6f}")
```

### 3. Comparaison de Variantes
```python
# Comparer différentes rugosités
rugosites = [('Beton', 1.0), ('Enrochements', 0.5), ('Tetrapodes', 0.4)]

for name, gf in rugosites:
    results = compare_all_methods(Hm0, Tm_10, h, Rc, alpha, gamma_f=gf)
    print(f"\n{name} (gamma_f={gf}):")
    print(f"  EurOtop: {results['empirical']['q']:.6f}")
    print(f"  XGBoost: {results['xgboost']['q']:.6f}")
```

---

## 🔧 Personnalisation

### Ajouter vos Propres Paramètres
```python
# Au début du notebook, définir vos valeurs
MES_CONDITIONS = {
    'Hm0': 3.2,
    'Tm_10': 7.8,
    'h': 11.5,
    'Rc': 2.8,
    'alpha_deg': 32.0,
    'gamma_f': 0.55
}

# Puis utiliser partout
q = overtopping.digue_talus(**MES_CONDITIONS)
```

### Modifier les Graphiques
```python
# Changer les couleurs
COLORS = {
    'eurotop': '#FF5722',  # Orange
    'xgboost': '#4CAF50',  # Vert
    'neural': '#9C27B0'    # Violet
}

# Ajuster la taille
plt.figure(figsize=(16, 10))
```

---

## 📖 Références

### Guide EurOtop 2018
- Chapitre 5 : Digues à talus
- Chapitre 6 : Murs verticaux
- Chapitre 7 : Structures composites

### Base CLASH
- Van der Meer et al. (2005)
- 10,533 tests physiques
- Source pour Neural Network et XGBoost

### Documentation OpenEurOtop
- `../docs/` : Documentation Sphinx complète
- `ADVANCED_MODELS_RESULTS.md` : Résultats détaillés
- `FINAL_IMPLEMENTATION_SUMMARY.md` : Vue d'ensemble

---

## ⚡ Quick Start

```bash
# Cloner et installer
git clone <repo>
cd OpenEurOtop
pip install -e .

# Installer dépendances notebooks
pip install matplotlib pandas jupytext

# Lancer un exemple
cd examples
python notebook_01_introduction_comparative.py

# Les images sont générées dans le répertoire courant !
```

---

## 🆘 Support

### Questions Fréquentes

**Q: XGBoost donne des résultats très différents d'EurOtop ?**
R: C'est normal pour certains cas extrêmes. XGBoost est entraîné sur CLASH qui a ses limites. Toujours valider avec EurOtop pour le design.

**Q: Puis-je utiliser XGBoost pour le design final ?**
R: Non. Les formules EurOtop sont la référence scientifique. XGBoost sert de vérification rapide.

**Q: Le Neural Network donne de mauvais résultats ?**
R: Normal, R²=0.67 seulement. Préférer XGBoost (R²=0.88) ou EurOtop.

**Q: Comment ajouter l'obliquité des vagues ?**
R: Utiliser le paramètre `gamma_beta` :
```python
q = overtopping.digue_talus(Hm0, Tm_10, h, Rc, alpha, gamma_beta=0.9)
```

---

## 🎉 Contributions

Vos retours sont les bienvenus !

- Signaler des bugs
- Proposer de nouveaux exemples
- Partager vos cas d'usage
- Améliorer la documentation

---

**OpenEurOtop v0.3.0-beta**  
*Développé pour les ingénieurs côtiers*  
*Base CLASH : 9,324 tests physiques*  
*XGBoost optimisé : R² = 0.88*

