Case Studies EurOtop
====================

Les 12 case studies du Chapitre 8 d'EurOtop 2018.

Vue d'ensemble
--------------

OpenEurOtop implémente les 12 études de cas documentées dans le manuel EurOtop,
couvrant tous les types de structures côtières.

Utilisation
-----------

Exécuter tous les case studies
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openeurotop import case_studies
   
   all_cases = case_studies.run_all_case_studies()
   
   for cs_id, cs in all_cases.items():
       print(cs)

Exécuter un case study spécifique
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # Case Study 1: Zeebrugge
   cs1 = case_studies.case_study_1_zeebrugge()
   print(f"Location: {cs1.location}")
   print(f"Débit: {cs1.results['q_calculated']*1000:.3f} l/s/m")

Générer un rapport
~~~~~~~~~~~~~~~~~~

.. code-block:: python

   report = case_studies.generate_case_studies_report()
   
   # Sauvegarder
   with open('rapport_case_studies.txt', 'w') as f:
       f.write(report)

Ligne de commande
~~~~~~~~~~~~~~~~~

.. code-block:: bash

   # Tous les case studies
   python examples/case_studies_eurotop.py --all
   
   # Case study spécifique (1-12)
   python examples/case_studies_eurotop.py --case 1
   
   # Générer rapport
   python examples/case_studies_eurotop.py --report

Liste des 12 Case Studies
--------------------------

CS1: Zeebrugge Breakwater (Belgium)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Digue en enrochement avec berme

**Paramètres:**

* Hm0 = 4.5 m
* Enrochement 2 couches (Dn50 = 3.5 m)
* Berme submergée (15 m de large)
* Revanche = 5.5 m

**Enseignements:**

* Effet de la berme sur le franchissement
* Structures massives en haute mer

CS2: Oostende Seawall (Belgium)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Structure composite (talus + mur vertical)

**Paramètres:**

* Talus en enrochement jusqu'à +3.5m
* Mur vertical au-dessus
* Configuration urbaine typique

**Enseignements:**

* Calcul de structures composites
* Optimisation des hauteurs

CS3: Petten Sea Dike (Netherlands)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Digue lisse en asphalte

**Paramètres:**

* Revêtement asphalte
* Pente 1:2
* Mesures disponibles

**Enseignements:**

* Validation avec mesures réelles
* Run-up élevé sur surface lisse

CS4: Walcheren Grass Dike (Netherlands)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Digue avec revêtement en herbe

**Paramètres:**

* Pente douce 1:3
* Revêtement herbeux
* Configuration typique NL

**Enseignements:**

* Comportement des digues en herbe
* Érosion et stabilité

CS5: Dover Harbour Breakwater (UK)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Mur vertical avec parapet

**Paramètres:**

* Mur en béton
* Parapet de 1.5 m
* Conditions portuaires

**Enseignements:**

* Effet du parapet
* Réduction significative

CS6: Samphire Hoe (UK)
~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Enrochement à pente raide

**Paramètres:**

* Pente 1:1 (45°)
* Enrochement massif (Dn50 = 4.0 m)
* Haute énergie

**Enseignements:**

* Pentes raides
* Régime non-déferlant

CS7: Scheveningen Boulevard (Netherlands)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Promenade avec vagues obliques

**Paramètres:**

* Mur vertical
* Obliquité 30°
* Zone urbaine

**Enseignements:**

* Effet de l'obliquité
* Protection urbaine

CS8: Westkapelle with Berm (Netherlands)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Digue avec berme très large

**Paramètres:**

* Berme de 25 m
* Submergée -1.5 m
* Asphalte

**Enseignements:**

* Effet majeur de berme large
* Optimisation

CS9: Zoutkamp Multi-slope (Netherlands)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Structure à pentes multiples

**Paramètres:**

* 3 pentes (1:3, 1:2, 1:1)
* Rugosités variables
* Configuration complexe

**Enseignements:**

* Calcul multi-pentes
* Pente équivalente

CS10: Reykjavik Accropode (Iceland)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Blocs artificiels Accropode

**Paramètres:**

* Blocs Accropode
* Hm0 = 5.5 m (extrême)
* Eau profonde

**Enseignements:**

* Blocs artificiels
* Haute énergie

CS11: Gijón Caisson Breakwater (Spain)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Caisson vertical

**Paramètres:**

* Caissons béton
* h = 16 m (profond)
* Mesures disponibles

**Enseignements:**

* Murs massifs
* Validation

CS12: Alderney Extreme Conditions (UK)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Type:** Enrochement conditions extrêmes

**Paramètres:**

* Hm0 = 6.5 m (extrême)
* Tm-1,0 = 11 s
* Dn50 = 5.0 m

**Enseignements:**

* Limites de validité
* Incertitudes élevées

Comparaison avec mesures
-------------------------

3 case studies incluent des comparaisons avec des mesures réelles :

.. code-block:: python

   cs = case_studies.case_study_1_zeebrugge()
   comp = case_studies.compare_with_measurements(cs)
   
   if comp['comparison_available']:
       print(f"Calculé: {comp['calculated']*1000:.3f} l/s/m")
       print(f"Mesuré: {comp['measured']*1000:.3f} l/s/m")
       print(f"Erreur: {comp['relative_error_percent']:.1f}%")

Couverture des structures
--------------------------

Les 12 case studies couvrent :

* Digues en enrochement (CS1, CS6, CS10, CS12)
* Murs verticaux (CS5, CS7, CS11)
* Structures composites (CS2, CS9)
* Digues lisses (CS3, CS4)
* Avec berme (CS1, CS8)
* Multi-pentes (CS9)
* Blocs artificiels (CS10)
* Obliquité (CS7)
* Conditions extrêmes (CS12)

Références
----------

**EurOtop (2018)** - Chapter 8: Case Studies
Sections 8.1 à 8.12

