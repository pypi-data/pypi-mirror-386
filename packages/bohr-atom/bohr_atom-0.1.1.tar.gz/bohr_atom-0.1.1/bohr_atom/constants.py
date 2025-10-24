"""
Constantes físicas fundamentales para el modelo de Bohr.
"""

import math


class PhysicalConstants:
    """
    Constantes físicas en unidades del SI.
    """
    
    # Constante de Planck (J·s)
    h = 6.62607015e-34
    h_bar = h / (2 * math.pi)
    
    # Masa del electrón (kg)
    m_e = 9.1093837015e-31
    
    # Carga elemental (C)
    e = 1.602176634e-19
    
    # Permitividad del vacío (F/m)
    epsilon_0 = 8.8541878128e-12
    
    # Velocidad de la luz (m/s)
    c = 299792458
    
    # Constante de Coulomb (N·m²/C²)
    k_e = 1 / (4 * math.pi * epsilon_0)
    
    # Constante de Rydberg (J)
    Ry = (m_e * e**4) / (8 * epsilon_0**2 * h**2)
    
    # Radio de Bohr (m)
    a_0 = (epsilon_0 * h**2) / (math.pi * m_e * e**2)
    
    # Factor de conversión de Joules a eV
    eV = e
