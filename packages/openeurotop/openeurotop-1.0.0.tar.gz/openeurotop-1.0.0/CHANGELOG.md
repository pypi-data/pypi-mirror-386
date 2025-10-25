# Changelog

Toutes les modifications notables de ce projet seront documentées dans ce fichier.

Le format est basé sur [Keep a Changelog](https://keepachangelog.com/fr/1.0.0/),
et ce projet adhère au [Semantic Versioning](https://semver.org/lang/fr/).

## [1.0.0] - 2025-10-24

### Nouveautés majeures
- 🎉 **Première version stable de production !**
- Implémentation complète des méthodes EurOtop 2018
- Suite de tests exhaustive avec >95% de couverture de code
- Documentation Sphinx complète avec guides utilisateur et API
- Modèles de Machine Learning pour la prédiction de franchissement
- Exemples et cas d'études pratiques

### Modules ajoutés
- `neural_network.py` : Réseau de neurones pour prédiction de franchissement
- `neural_network_clash.py` : Modèle neural spécialisé basé sur la base CLASH
- `xgboost_model.py` : Modèle XGBoost optimisé pour franchissement
- `probabilistic.py` : Analyses probabilistes et statistiques
- `special_cases.py` : Cas spéciaux (bermes, structures composites)
- `case_studies.py` : Cas d'études documentés du guide EurOtop
- `validation.py` : Outils de validation des paramètres d'entrée

### Fonctionnalités
- Support complet des digues à talus (lisses, rugueuses, avec bermes)
- Support des murs verticaux et structures composites
- Calculs de run-up et franchissement individuel par vague
- Facteurs de réduction pour >15 types de revêtements
- Analyses d'influence paramétrique
- Export des résultats et visualisations

### Documentation
- Guide utilisateur complet en français
- Documentation API Sphinx avec exemples
- 5+ notebooks Jupyter interactifs
- Cas d'études détaillés du manuel EurOtop
- Formules techniques documentées

### Tests et qualité
- 100+ tests unitaires
- Tests d'intégration pour validation physique
- Couverture de code >95%
- Validation contre cas de référence EurOtop

### Performances
- Modèles ML pré-entraînés inclus
- Optimisation des calculs numériques
- Support batch pour calculs multiples

### Infrastructure
- Configuration PyPI complète
- Documentation ReadTheDocs prête
- CI/CD configuré
- Gestion sémantique des versions

## [0.1.0] - 2025-10-23

### Ajouté
- Implémentation initiale du package OpenEurOtop
- Module `overtopping` avec les fonctions principales :
  - `digue_talus()` : Calcul pour digues à talus
  - `digue_talus_detailed()` : Calcul détaillé avec facteurs automatiques
  - `mur_vertical()` : Calcul pour murs verticaux
  - `structure_composite()` : Calcul pour structures composites
  - `digue_en_enrochement()` : Calcul spécialisé pour enrochements
  - `promenade_avec_parapet()` : Calcul pour promenades avec parapets
  - `rubble_mound_breakwater()` : Calcul pour digues à talus avec différentes carapaces
  - `calcul_volumes_franchissement()` : Calcul des volumes
  - `discharge_individual_waves()` : Statistiques par vagues individuelles
  
- Module `wave_parameters` avec les fonctions :
  - `wave_length_deep_water()` : Longueur d'onde en eau profonde
  - `wave_length()` : Longueur d'onde avec relation de dispersion
  - `wave_steepness()` : Cambrure de la vague
  - `iribarren_number()` : Nombre d'Iribarren
  - `spectral_period_conversion()` : Conversion entre périodes spectrales
  - `relative_water_depth()` : Profondeur relative
  
- Module `reduction_factors` avec les facteurs :
  - `gamma_f_roughness()` : Facteur de rugosité (>15 types de revêtements)
  - `gamma_beta_obliquity()` : Facteur d'obliquité
  - `gamma_b_berm()` : Facteur de berme
  - `gamma_v_vertical_wall()` : Facteur pour parapet
  - `gamma_star_composite()` : Facteur pour structures composites
  - `gamma_h_water_depth()` : Facteur de profondeur
  - `gamma_cf_wind()` : Facteur de vent
  
- Module `constants` avec les constantes et coefficients EurOtop
- Fichiers d'exemples complets dans `examples/exemple_basic.py`
- Tests unitaires dans `tests/test_overtopping.py`
- Documentation complète dans README.md
- Configuration du package avec setup.py

### Références
- EurOtop (2018). Manual on wave overtopping of sea defences and related structures.
  www.overtopping-manual.com

