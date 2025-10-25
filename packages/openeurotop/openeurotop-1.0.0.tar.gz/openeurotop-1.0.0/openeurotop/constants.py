"""
Constantes physiques et coefficients utilisés dans les calculs EurOtop
"""

import math

# Constantes physiques
G = 9.81  # Accélération de la pesanteur (m/s²)

# Coefficients pour les formules de franchissement
# Digues à talus (slope structures)
A_TALUS_NON_DEFERLEMENT = 0.067  # Coefficient a pour conditions non-déferlantes
B_TALUS_NON_DEFERLEMENT = 4.75   # Coefficient b pour conditions non-déferlantes
C_TALUS_NON_DEFERLEMENT = 2.6    # Coefficient c pour conditions non-déferlantes

A_TALUS_DEFERLEMENT = 0.2        # Coefficient a pour conditions déferlantes
B_TALUS_DEFERLEMENT = 2.6        # Coefficient b pour conditions déferlantes
C_TALUS_DEFERLEMENT = None       # Pas utilisé

# Murs verticaux et composites
A_MUR_VERTICAL = 0.047           # Coefficient pour murs verticaux
B_MUR_VERTICAL = 2.35            # Coefficient pour murs verticaux

# Seuils de transition
XI_TRANSITION = 2.0              # Valeur de transition du nombre d'Iribarren
XI_M_CRITICAL = 1.8              # Nombre d'Iribarren critique

# Limites de validité
MAX_RC_HM0 = 3.5                 # Rc/Hm0 max recommandé
MIN_RC_HM0 = 0.5                 # Rc/Hm0 min pour validité

# Angles
MIN_SLOPE_ANGLE = 10.0           # Angle de pente minimum (degrés)
MAX_SLOPE_ANGLE = 90.0           # Angle de pente maximum (degrés)

# Conversion
DEG_TO_RAD = math.pi / 180.0
RAD_TO_DEG = 180.0 / math.pi

