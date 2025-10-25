# OpenEurOtop

[![PyPI version](https://badge.fury.io/py/openeurotop.svg)](https://badge.fury.io/py/openeurotop)
[![Python versions](https://img.shields.io/pypi/pyversions/openeurotop.svg)](https://pypi.org/project/openeurotop/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Documentation Status](https://readthedocs.org/projects/openeurotop/badge/?version=latest)](https://openeurotop.readthedocs.io/en/latest/?badge=latest)
[![CI/CD](https://github.com/Pavlishenku/OpenEurOtop/workflows/CI%2FCD%20Pipeline/badge.svg)](https://github.com/Pavlishenku/OpenEurOtop/actions)

Implémentation Python des méthodes de calcul du guide EurOtop pour l'évaluation du franchissement de vagues sur les ouvrages côtiers.

> 🎉 **Version 1.0.0** - Première version stable de production !

## Description

Ce package fournit une implémentation complète des formules et méthodes décrites dans le manuel EurOtop (2018) pour le calcul :
- Du débit de franchissement moyen (mean wave overtopping discharge)
- Des facteurs de réduction pour différentes caractéristiques de structures
- Des paramètres de vagues et conditions hydrauliques

## Installation

### Installation stable depuis PyPI

```bash
pip install openeurotop
```

### Installation avec fonctionnalités Machine Learning

```bash
pip install openeurotop[ml]
```

### Installation pour développement

```bash
git clone https://github.com/Pavlishenku/OpenEurOtop.git
cd OpenEurOtop
pip install -e .[dev]
```

## Utilisation

### Calcul du franchissement pour une digue lisse

```python
from openeurotop import overtopping

# Paramètres
Hm0 = 2.5  # Hauteur significative des vagues (m)
Tm_10 = 6.0  # Période moyenne (s)
h = 10.0  # Profondeur d'eau (m)
Rc = 3.0  # Revanche (m)
alpha = 30.0  # Pente du talus (degrés)
gamma_b = 1.0  # Facteur de berme
gamma_f = 1.0  # Facteur de rugosité
gamma_beta = 1.0  # Facteur d'obliquité

# Calcul
q = overtopping.digue_talus(
    Hm0=Hm0,
    Tm_10=Tm_10,
    h=h,
    Rc=Rc,
    alpha_deg=alpha,
    gamma_b=gamma_b,
    gamma_f=gamma_f,
    gamma_beta=gamma_beta
)

print(f"Débit de franchissement : {q:.6f} m³/s/m")
```

### Calcul pour un mur vertical

```python
from openeurotop import overtopping

q = overtopping.mur_vertical(
    Hm0=2.5,
    Tm_10=6.0,
    h=10.0,
    Rc=3.0,
    h_structure=12.0
)
```

## Modules

- `openeurotop.overtopping` : Calculs de franchissement pour différents types de structures
- `openeurotop.wave_parameters` : Calcul des paramètres de vagues
- `openeurotop.reduction_factors` : Facteurs de réduction (rugosité, berme, obliquité, etc.)
- `openeurotop.constants` : Constantes physiques et coefficients

## Références

EurOtop (2018). Manual on wave overtopping of sea defences and related structures. 
An overtopping manual largely based on European research, but for worldwide application.
Van der Meer, J.W., Allsop, N.W.H., Bruce, T., De Rouck, J., Kortenhaus, A., Pullen, T., 
Schüttrumpf, H., Troch, P. and Zanuttigh, B.
www.overtopping-manual.com

## Fonctionnalités

- ✅ Implémentation complète des formules EurOtop 2018
- ✅ Support digues à talus (lisses, rugueuses, avec bermes)
- ✅ Support murs verticaux et structures composites
- ✅ Modèles de Machine Learning (Neural Networks, XGBoost)
- ✅ Analyses probabilistes et statistiques
- ✅ >100 tests unitaires avec >95% de couverture
- ✅ Documentation complète avec exemples
- ✅ Notebooks Jupyter interactifs

## Documentation

- 📚 [Documentation complète](https://openeurotop.readthedocs.io/)
- 📖 [Guide utilisateur](docs/GUIDE_UTILISATEUR.md)
- 🔧 [Guide de contribution](CONTRIBUTING.md)
- 📝 [Changelog](CHANGELOG.md)
- 💻 [Exemples et notebooks](examples/)

## Contribution

Les contributions sont les bienvenues ! Consultez le [guide de contribution](CONTRIBUTING.md) pour plus d'informations.

### Développeurs

Pour configurer l'environnement de développement :

```bash
git clone https://github.com/Pavlishenku/OpenEurOtop.git
cd OpenEurOtop
pip install -e .[dev]
pytest  # Exécuter les tests
```

## Citation

Si vous utilisez OpenEurOtop dans vos recherches, veuillez citer :

```bibtex
@software{openeurotop2025,
  title = {OpenEurOtop: Python Implementation of EurOtop Wave Overtopping Manual},
  author = {OpenEurOtop Contributors},
  year = {2025},
  url = {https://github.com/Pavlishenku/OpenEurOtop},
  version = {1.0.0}
}
```

## Liens

- 🐍 [PyPI](https://pypi.org/project/openeurotop/)
- 📦 [GitHub](https://github.com/Pavlishenku/OpenEurOtop)
- 📚 [Documentation](https://openeurotop.readthedocs.io/)
- 🐛 [Issues](https://github.com/Pavlishenku/OpenEurOtop/issues)

## Licence

MIT License

