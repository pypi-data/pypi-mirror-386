# Tests

Ce dossier contient les tests unitaires pour le package OpenEurOtop.

## Exécution des tests

### Avec pytest (recommandé)

```bash
pip install pytest
pytest
```

### Sans pytest

```bash
cd tests
python test_overtopping.py
```

## Tests inclus

Le fichier `test_overtopping.py` contient 12 tests :

1. `test_digue_talus_basic` - Test basique pour digue à talus
2. `test_digue_talus_revanche_elevee` - Test avec différentes revanches
3. `test_effet_rugosite` - Vérification de l'effet de la rugosité
4. `test_mur_vertical` - Test pour mur vertical
5. `test_structure_composite` - Test pour structure composite
6. `test_iribarren_number` - Calcul du nombre d'Iribarren
7. `test_gamma_f_roughness` - Facteurs de rugosité
8. `test_gamma_beta_obliquity` - Facteur d'obliquité
9. `test_wave_length` - Calcul de longueur d'onde
10. `test_volumes_franchissement` - Calcul de volumes
11. `test_digue_en_enrochement` - Test pour enrochement
12. `test_coherence_methodes` - Cohérence entre méthodes

## Ajout de nouveaux tests

Pour ajouter de nouveaux tests, créez des fonctions commençant par `test_` dans un fichier `test_*.py`.

Exemple :

```python
def test_ma_nouvelle_fonction():
    result = ma_fonction(param1, param2)
    assert result > 0, "Le résultat doit être positif"
    print(f"✓ test_ma_nouvelle_fonction: result = {result}")
```

