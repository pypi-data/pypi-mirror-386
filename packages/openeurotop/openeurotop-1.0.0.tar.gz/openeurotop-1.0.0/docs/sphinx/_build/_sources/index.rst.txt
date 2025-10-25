OpenEurOtop Documentation
=========================

**OpenEurOtop v0.2.0** - Implémentation Python complète du guide EurOtop (2018)

OpenEurOtop est un package Python qui implémente les méthodes de calcul du manuel 
EurOtop 2018 pour l'ingénierie côtière et le franchissement par les vagues.

.. image:: https://img.shields.io/badge/version-0.2.0-blue.svg
   :alt: Version 0.2.0

.. image:: https://img.shields.io/badge/python-3.8%2B-blue.svg
   :alt: Python 3.8+

.. image:: https://img.shields.io/badge/license-MIT-green.svg
   :alt: License MIT

Caractéristiques principales
-----------------------------

✅ **Franchissement** (Chapitre 5) - 95% implémenté

✅ **Run-up** (Chapitre 6) - 90% implémenté

✅ **12 Case Studies** - Basés sur EurOtop Chapitre 8

✅ **Analyses probabilistes** - Complètes

✅ **Cas spécifiques** - Multi-pentes, pentes extrêmes

✅ **Validation automatique** - Complète

Installation rapide
-------------------

.. code-block:: bash

   pip install -e .

Exemple d'utilisation
---------------------

.. code-block:: python

   from openeurotop import overtopping
   
   # Calcul du franchissement pour une digue à talus
   q = overtopping.digue_talus(
       Hm0=2.5,        # Hauteur significative (m)
       Tm_10=6.0,      # Période spectrale (s)
       h=10.0,         # Profondeur d'eau (m)
       Rc=3.0,         # Revanche (m)
       alpha_deg=35.0  # Pente (°)
   )
   
   print(f"Débit de franchissement : {q*1000:.3f} l/s/m")

Table des matières
==================

.. toctree::
   :maxdepth: 2
   :caption: Guide utilisateur

   installation
   quickstart
   user_guide
   case_studies

.. toctree::
   :maxdepth: 2
   :caption: Référence API

   api/overtopping
   api/run_up
   api/probabilistic
   api/special_cases
   api/validation
   api/case_studies
   api/wave_parameters
   api/reduction_factors
   api/constants

.. toctree::
   :maxdepth: 1
   :caption: Informations

   changelog
   contributing
   license

Indices et tables
=================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

