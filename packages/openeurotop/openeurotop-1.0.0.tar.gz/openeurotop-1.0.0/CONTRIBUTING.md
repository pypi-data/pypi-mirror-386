# Guide de contribution

Merci de votre intérêt pour contribuer à OpenEurOtop !

## Comment contribuer

### Rapporter des bugs

Si vous trouvez un bug :

1. Vérifiez qu'il n'a pas déjà été rapporté dans les issues
2. Créez une nouvelle issue avec :
   - Description claire du problème
   - Étapes pour reproduire
   - Résultat attendu vs résultat obtenu
   - Version de Python et du package
   - Code minimal pour reproduire

### Proposer des améliorations

Pour proposer une nouvelle fonctionnalité :

1. Ouvrez une issue pour discuter de l'idée
2. Expliquez le cas d'usage
3. Proposez une implémentation si possible

### Soumettre du code

1. Forkez le projet
2. Créez une branche pour votre fonctionnalité (`git checkout -b feature/ma-fonctionnalite`)
3. Commitez vos changements (`git commit -m 'Ajout de ma fonctionnalité'`)
4. Pushez vers la branche (`git push origin feature/ma-fonctionnalite`)
5. Ouvrez une Pull Request

## Standards de code

### Style Python

- Suivre PEP 8
- Utiliser des noms de variables descriptifs
- Ajouter des docstrings pour toutes les fonctions publiques
- Commenter le code complexe

### Exemple de docstring

```python
def ma_fonction(param1, param2, param3=None):
    """
    Description courte de la fonction
    
    Description plus détaillée si nécessaire, expliquant
    le contexte et les détails d'implémentation.
    
    Parameters
    ----------
    param1 : float
        Description du paramètre 1
    param2 : str
        Description du paramètre 2
    param3 : int, optional
        Description du paramètre optionnel
    
    Returns
    -------
    float
        Description de ce qui est retourné
    
    References
    ----------
    EurOtop (2018) - Section X.X
    """
    # Implémentation
    pass
```

### Tests

- Ajouter des tests pour toute nouvelle fonctionnalité
- S'assurer que tous les tests passent avant de soumettre
- Viser une couverture de code > 80%

```bash
# Exécuter les tests
python tests/test_overtopping.py

# Ou avec pytest
pytest
```

### Documentation

- Mettre à jour le README si nécessaire
- Ajouter des exemples dans `examples/` pour les nouvelles fonctionnalités
- Mettre à jour `CHANGELOG.md`

## Structure du projet

```
OpenEurOtop/
├── openeurotop/              # Code source principal
│   ├── __init__.py
│   ├── constants.py          # Constantes et coefficients
│   ├── overtopping.py        # Calculs de franchissement
│   ├── wave_parameters.py    # Paramètres de vagues
│   └── reduction_factors.py  # Facteurs de réduction
├── examples/                 # Exemples d'utilisation
├── tests/                    # Tests unitaires
├── docs/                     # Documentation
└── setup.py                  # Configuration du package
```

## Domaines d'amélioration

### Fonctionnalités souhaitées

- [ ] Calcul du run-up
- [ ] Distribution de Weibull pour volumes individuels
- [ ] Prise en compte du setup/setdown
- [ ] Calcul d'incertitudes
- [ ] Optimisation inverse (calcul de Rc pour q donné)
- [ ] Export de résultats vers Excel/CSV
- [ ] Interface graphique simple
- [ ] Validation avec cas tests EurOtop

### Améliorations techniques

- [ ] Optimisation des performances
- [ ] Ajout de type hints complets
- [ ] Documentation API complète avec Sphinx
- [ ] Tests de performance (benchmarks)
- [ ] Intégration continue (CI/CD)

## Références

- [Manuel EurOtop 2018](http://www.overtopping-manual.com)
- [PEP 8 - Style Guide](https://www.python.org/dev/peps/pep-0008/)
- [NumPy Docstring Guide](https://numpydoc.readthedocs.io/en/latest/format.html)

## Licence

En contribuant, vous acceptez que vos contributions soient sous licence MIT.

## Questions

Si vous avez des questions, n'hésitez pas à ouvrir une issue ou à contacter les mainteneurs.

