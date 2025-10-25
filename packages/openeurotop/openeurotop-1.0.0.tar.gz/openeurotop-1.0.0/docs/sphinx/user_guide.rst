Guide utilisateur complet
=========================

Ce guide détaillé couvre toutes les fonctionnalités d'OpenEurOtop.

Vue d'ensemble
--------------

OpenEurOtop implémente les méthodes de calcul du manuel EurOtop 2018 :

* **Chapitre 5** : Franchissement par les vagues
* **Chapitre 6** : Run-up et run-down
* **Chapitre 8** : Case studies (12 études de cas)
* **Section 5.8** : Incertitudes et probabilités

Modules disponibles
-------------------

Le package est organisé en 10 modules :

1. ``overtopping`` - Calculs de franchissement
2. ``run_up`` - Calculs de run-up
3. ``probabilistic`` - Analyses probabilistes
4. ``special_cases`` - Cas spécifiques
5. ``validation`` - Validation automatique
6. ``case_studies`` - 12 case studies EurOtop
7. ``neural_network`` - Infrastructure neuronale
8. ``wave_parameters`` - Paramètres de vagues
9. ``reduction_factors`` - Facteurs de réduction
10. ``constants`` - Constantes EurOtop

Franchissement (overtopping)
-----------------------------

Formules principales
~~~~~~~~~~~~~~~~~~~~

**Formule 5.1 et 5.2** - Digues à talus :

.. math::

   \\frac{q}{\\sqrt{g H_{m0}^3}} = \\frac{0.023}{\\sqrt{\\tan\\alpha}} \\gamma_b \\xi_{m-1,0} \\exp\\left[-\\left(2.7\\frac{R_c}{\\xi_{m-1,0}H_{m0}\\gamma_b\\gamma_f\\gamma_{\\beta}\\gamma_v}\\right)^{1.3}\\right]

**Formule 5.12** - Murs verticaux :

.. math::

   q = 0.05 \\exp\\left(-2.78\\frac{R_c}{H_{m0}}\\right) \\sqrt{g H_{m0}^3}

Exemples d'utilisation
~~~~~~~~~~~~~~~~~~~~~~~

Digue lisse :

.. code-block:: python

   from openeurotop import overtopping
   
   q = overtopping.digue_talus(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=3.0,
       alpha_deg=35.0,
       type_revetement='asphalte'
   )

Digue rugueuse :

.. code-block:: python

   q = overtopping.digue_talus(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=3.0,
       alpha_deg=35.0,
       type_revetement='enrochement_2couches'
   )

Avec tous les facteurs :

.. code-block:: python

   from openeurotop import reduction_factors
   
   # Facteur de rugosité
   gamma_f = reduction_factors.gamma_f_roughness('enrochement_2couches')
   
   # Facteur d'obliquité
   gamma_beta = reduction_factors.gamma_beta_obliquity(beta_deg=30.0)
   
   # Facteur de berme
   gamma_b = reduction_factors.gamma_b_berm(
       Rc=3.0, Hm0=2.5, B=20.0, h_berm=-1.0, gamma_f=gamma_f
   )
   
   q = overtopping.digue_talus(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=3.0,
       alpha_deg=35.0,
       gamma_f=gamma_f,
       gamma_beta=gamma_beta,
       gamma_b=gamma_b
   )

Run-up
------

Le module ``run_up`` calcule la montée maximale de l'eau sur une structure.

Run-up 2%
~~~~~~~~~

.. code-block:: python

   from openeurotop import run_up
   
   # Pente lisse
   Ru2 = run_up.run_up_2percent_smooth_slope(2.5, 6.0, 35.0)
   
   # Pente rugueuse
   Ru2 = run_up.run_up_2percent_rough_slope(2.5, 6.0, 35.0, gamma_f=0.5)

Run-up avec berme
~~~~~~~~~~~~~~~~~

.. code-block:: python

   Ru2 = run_up.run_up_bermed_slope(
       Hm0=2.5,
       Tm_10=6.0,
       alpha_deg=35.0,
       gamma_f=0.5,
       B_berm=15.0,
       h_berm=-1.0
   )

Run-up structure composite
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   Ru2 = run_up.run_up_composite_slope(
       Hm0=2.5,
       Tm_10=6.0,
       alpha_lower_deg=26.6,
       alpha_upper_deg=90.0,
       h_transition=2.0,
       gamma_f_lower=0.5,
       gamma_f_upper=1.0
   )

Analyses probabilistes
----------------------

Distribution de Weibull
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openeurotop import probabilistic
   
   # Paramètres de Weibull
   params = probabilistic.weibull_parameters(q_mean=0.001)
   
   # Volume individuel dépassé par 2% des vagues
   V2 = probabilistic.individual_overtopping_volume(
       q_mean=0.001,
       Tm_10=6.0,
       prob_exceedance=0.02
   )

Incertitudes
~~~~~~~~~~~~

.. code-block:: python

   unc = probabilistic.uncertainty_overtopping(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=3.0,
       alpha_deg=35.0,
       structure_type='rough_slope'
   )
   
   print(f"Valeur moyenne : {unc['q_mean']*1000:.3f} l/s/m")
   print(f"Intervalle 90% : [{unc['q_5']*1000:.1f}, {unc['q_95']*1000:.1f}] l/s/m")

Monte Carlo
~~~~~~~~~~~

.. code-block:: python

   results = probabilistic.monte_carlo_overtopping(
       Hm0_mean=2.5,
       Tm_10_mean=6.0,
       h=10.0,
       Rc=3.0,
       alpha_deg=35.0,
       n_simulations=10000,
       structure_type='smooth_slope'
   )

Cas spécifiques
---------------

Structures multi-pentes
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openeurotop import special_cases
   
   slopes = [
       {'alpha_deg': 20, 'h_start': -5, 'h_end': 0},
       {'alpha_deg': 30, 'h_start': 0, 'h_end': 2},
       {'alpha_deg': 45, 'h_start': 2, 'h_end': 5}
   ]
   
   result = special_cases.multi_slope_structure(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=4.0,
       slopes_config=slopes
   )

Pentes extrêmes
~~~~~~~~~~~~~~~

.. code-block:: python

   # Pente très douce
   q = special_cases.very_gentle_slope(
       Hm0=2.0,
       Tm_10=5.5,
       h=8.0,
       Rc=2.0,
       alpha_deg=8.0
   )
   
   # Pente très raide
   q = special_cases.very_steep_slope(
       Hm0=3.0,
       Tm_10=7.0,
       h=12.0,
       Rc=5.0,
       alpha_deg=65.0
   )

Validation
----------

Validation automatique
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openeurotop import validation
   
   result = validation.validate_slope_structure(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=3.0,
       alpha_deg=35.0
   )
   
   if result['valid']:
       print("Paramètres valides")
   else:
       print("Attention :", result['warnings'])

Rapport de validation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   report = validation.validation_report(
       Hm0=2.5,
       Tm_10=6.0,
       h=10.0,
       Rc=3.0,
       alpha_deg=35.0,
       structure_type='digue_talus'
   )
   print(report)

Facteurs de réduction
----------------------

Facteur de rugosité γf
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   from openeurotop import reduction_factors
   
   gamma_f = reduction_factors.gamma_f_roughness('enrochement_2couches')
   # gamma_f = 0.50

Types de revêtements disponibles :

* ``asphalte`` : γf = 1.0
* ``beton_lisse`` : γf = 1.0
* ``enrochement_1couche`` : γf = 0.60
* ``enrochement_2couches`` : γf = 0.50
* ``accropode`` : γf = 0.46
* ``tetrapode`` : γf = 0.38
* ``herbe`` : γf = 0.90

Facteur d'obliquité γβ
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   gamma_beta = reduction_factors.gamma_beta_obliquity(beta_deg=30.0)
   # Réduction due à l'angle d'attaque

Facteur de berme γb
~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   gamma_b = reduction_factors.gamma_b_berm(
       Rc=3.0,
       Hm0=2.5,
       B=20.0,      # Largeur berme (m)
       h_berm=-1.0, # Berme submergée de 1m
       gamma_f=0.5
   )

Paramètres de vagues
--------------------

.. code-block:: python

   from openeurotop import wave_parameters
   
   # Nombre d'Iribarren
   xi = wave_parameters.iribarren_number(
       alpha_deg=35.0,
       Hm0=2.5,
       Tm_10=6.0
   )
   
   # Longueur d'onde
   L = wave_parameters.wave_length(Tm_10=6.0, h=10.0)
   
   # Nombre d'onde
   k = wave_parameters.wave_number(Tm_10=6.0, h=10.0)

Types de structures
-------------------

Digues à talus
~~~~~~~~~~~~~~

* Lisses (asphalte, béton)
* Rugueuses (enrochement, blocs)
* Avec berme
* Multi-pentes

Murs verticaux
~~~~~~~~~~~~~~

* Murs simples
* Caissons
* Avec promenade
* Avec parapet

Structures composites
~~~~~~~~~~~~~~~~~~~~~

* Talus + mur vertical
* Berme + talus + mur

Références
----------

**EurOtop (2018)**
Manual on wave overtopping of sea defences and related structures
www.overtopping-manual.com

