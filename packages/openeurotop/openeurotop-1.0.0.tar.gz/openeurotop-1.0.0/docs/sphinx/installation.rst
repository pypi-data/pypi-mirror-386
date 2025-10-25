Installation
============

Prérequis
---------

OpenEurOtop nécessite :

* Python 3.8 ou supérieur
* numpy >= 1.20.0
* scipy >= 1.7.0
* matplotlib >= 3.3.0 (optionnel, pour les graphiques)

Installation standard
---------------------

Depuis le code source
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   git clone https://github.com/votre-repo/OpenEurOtop.git
   cd OpenEurOtop
   pip install -e .

Vérification de l'installation
-------------------------------

.. code-block:: bash

   python verify_installation.py

Vous devriez voir :

.. code-block:: text

   ========================================
   VERIFICATION OPENEUROTOP
   ========================================
   
   [OK] Module openeurotop
   [OK] Module overtopping
   [OK] Module wave_parameters
   ...
   
   ========================================
   INSTALLATION REUSSIE !
   ========================================

Environnement virtuel (recommandé)
-----------------------------------

Il est recommandé d'utiliser un environnement virtuel :

.. code-block:: bash

   # Créer l'environnement virtuel
   python -m venv venv_openeurotop
   
   # Activer (Windows)
   venv_openeurotop\Scripts\activate
   
   # Activer (Linux/Mac)
   source venv_openeurotop/bin/activate
   
   # Installer
   pip install -e .

Dépendances optionnelles
-------------------------

Pour le développement
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install pytest pytest-cov

Pour la documentation
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   pip install sphinx sphinx-rtd-theme sphinx-autodoc-typehints

Désinstallation
---------------

.. code-block:: bash

   pip uninstall openeurotop

