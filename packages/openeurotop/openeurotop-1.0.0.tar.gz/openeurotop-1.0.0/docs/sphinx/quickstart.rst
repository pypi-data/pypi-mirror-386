Démarrage rapide
================

Ce guide vous permet de démarrer rapidement avec OpenEurOtop.

Premier exemple
---------------

Calcul du franchissement pour une digue à talus :

.. code-block:: python

   from openeurotop import overtopping
   
   q = overtopping.digue_talus(
       Hm0=2.5,        # Hauteur significative (m)
       Tm_10=6.0,      # Période spectrale (s)
       h=10.0,         # Profondeur d'eau (m)
       Rc=3.0,         # Revanche (m)
       alpha_deg=35.0  # Pente (°)
   )
   
   print(f"Débit : {q*1000:.3f} l/s/m")

Exemples par type de structure
-------------------------------

Digue en enrochement
~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openeurotop import overtopping
   
   q = overtopping.digue_en_enrochement(
       Hm0=3.0,
       Tm_10=7.0,
       h=12.0,
       Rc=4.0,
       alpha_deg=30.0,
       Dn50=2.5,        # Diamètre nominal (m)
       n_layers=2       # Nombre de couches
   )

Mur vertical
~~~~~~~~~~~~

.. code-block:: python

   q = overtopping.mur_vertical(
       Hm0=2.0,
       Tm_10=5.5,
       h=8.0,
       Rc=3.5
   )

Structure composite
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   q = overtopping.structure_composite(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=4.0,
       alpha_lower_deg=26.6,  # Pente talus 1:2
       h_transition=2.0,       # Hauteur transition (m)
       gamma_f_lower=0.50,     # Facteur rugosité talus
       gamma_f_upper=1.0       # Facteur rugosité mur
   )

Run-up
------

Calcul du run-up :

.. code-block:: python

   from openeurotop import run_up
   
   # Run-up 2% pour pente lisse
   Ru2 = run_up.run_up_2percent_smooth_slope(
       Hm0=2.5,
       Tm_10=6.0,
       alpha_deg=35.0
   )
   
   print(f"Run-up Ru2% : {Ru2:.2f} m")

Validation
----------

Valider automatiquement vos paramètres :

.. code-block:: python

   from openeurotop import validation
   
   result = validation.validate_slope_structure(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=3.0,
       alpha_deg=35.0
   )
   
   print(result['summary'])

Analyses probabilistes
----------------------

Calculer les incertitudes :

.. code-block:: python

   from openeurotop import probabilistic
   
   unc = probabilistic.uncertainty_overtopping(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=3.0,
       alpha_deg=35.0,
       structure_type='rough_slope'
   )
   
   print(f"Intervalle 90% : [{unc['q_5']*1000:.1f}, {unc['q_95']*1000:.1f}] l/s/m")

Case Studies
------------

Accéder aux 12 case studies EurOtop :

.. code-block:: python

   from openeurotop import case_studies
   
   # Case Study 1 : Zeebrugge
   cs = case_studies.case_study_1_zeebrugge()
   print(cs)
   
   # Tous les case studies
   all_cases = case_studies.run_all_case_studies()

Exemples complets
-----------------

Des exemples complets sont disponibles dans le dossier ``examples/`` :

.. code-block:: bash

   # Exemples de base
   python examples/exemple_basic.py
   
   # Exemples avancés
   python examples/exemple_avance.py
   
   # Case studies
   python examples/case_studies_eurotop.py --all

Prochaines étapes
-----------------

* Consultez le :doc:`user_guide` pour plus de détails
* Explorez les :doc:`case_studies` 
* Consultez la :doc:`api/overtopping` pour la référence complète

