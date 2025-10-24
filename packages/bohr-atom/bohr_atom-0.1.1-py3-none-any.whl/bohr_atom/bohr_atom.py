"""
Clase principal para el modelo del átomo de Bohr.
"""

import numpy as np
import matplotlib.pyplot as plt
from .constants import PhysicalConstants as pc


class BohrAtom:
    """
    Clase que representa un átomo hidrogenoide según el modelo de Bohr.
    
    Parámetros
    ----------
    Z : int
        Número atómico (carga nuclear). Por defecto 1 (hidrógeno).
    
    Atributos
    ---------
    Z : int
        Número atómico del átomo
    """
    
    def __init__(self, Z=1):
        """
        Inicializa un átomo hidrogenoide con número atómico Z.
        
        Parámetros
        ----------
        Z : int
            Número atómico (por defecto 1 para hidrógeno)
        """
        if Z < 1:
            raise ValueError("El número atómico debe ser mayor o igual a 1")
        self.Z = Z
    
    def energy_level(self, n):
        """
        Calcula la energía del nivel n según el modelo de Bohr.
        
        E_n = -Z² × Ry / n²
        
        Parámetros
        ----------
        n : int
            Número cuántico principal (n ≥ 1)
        
        Retorna
        -------
        float
            Energía del nivel n en Joules
        """
        if n < 1:
            raise ValueError("n debe ser mayor o igual a 1")
        
        return -(self.Z**2 * pc.Ry) / (n**2)
    
    def energy_level_eV(self, n):
        """
        Calcula la energía del nivel n en electronvoltios (eV).
        
        Parámetros
        ----------
        n : int
            Número cuántico principal
        
        Retorna
        -------
        float
            Energía del nivel n en eV
        """
        return self.energy_level(n) / pc.eV
    
    def orbital_radius(self, n):
        """
        Calcula el radio de la órbita del nivel n.
        
        r_n = n² × a₀ / Z
        
        Parámetros
        ----------
        n : int
            Número cuántico principal
        
        Retorna
        -------
        float
            Radio de la órbita en metros
        """
        if n < 1:
            raise ValueError("n debe ser mayor o igual a 1")
        
        return (n**2 * pc.a_0) / self.Z
    
    def orbital_radius_angstrom(self, n):
        """
        Calcula el radio de la órbita en Ångströms.
        
        Parámetros
        ----------
        n : int
            Número cuántico principal
        
        Retorna
        -------
        float
            Radio de la órbita en Ångströms
        """
        return self.orbital_radius(n) * 1e10
    
    def transition_energy(self, n_initial, n_final):
        """
        Calcula la diferencia de energía en una transición electrónica.
        
        ΔE = E_final - E_initial
        
        Parámetros
        ----------
        n_initial : int
            Nivel inicial
        n_final : int
            Nivel final
        
        Retorna
        -------
        float
            Diferencia de energía en Joules (positivo si absorbe, negativo si emite)
        """
        return self.energy_level(n_final) - self.energy_level(n_initial)
    
    def transition_wavelength(self, n_initial, n_final):
        """
        Calcula la longitud de onda del fotón en una transición.
        
        λ = h × c / |ΔE|
        
        Parámetros
        ----------
        n_initial : int
            Nivel inicial
        n_final : int
            Nivel final
        
        Retorna
        -------
        float
            Longitud de onda en metros
        """
        delta_E = abs(self.transition_energy(n_initial, n_final))
        return (pc.h * pc.c) / delta_E
    
    def transition_wavelength_nm(self, n_initial, n_final):
        """
        Calcula la longitud de onda del fotón en nanómetros.
        
        Parámetros
        ----------
        n_initial : int
            Nivel inicial
        n_final : int
            Nivel final
        
        Retorna
        -------
        float
            Longitud de onda en nanómetros
        """
        return self.transition_wavelength(n_initial, n_final) * 1e9
    
    def transition_frequency(self, n_initial, n_final):
        """
        Calcula la frecuencia del fotón en una transición.
        
        ν = |ΔE| / h
        
        Parámetros
        ----------
        n_initial : int
            Nivel inicial
        n_final : int
            Nivel final
        
        Retorna
        -------
        float
            Frecuencia en Hz
        """
        delta_E = abs(self.transition_energy(n_initial, n_final))
        return delta_E / pc.h
    
    def plot_energy_levels(self, n_max=6, show_transitions=True, transitions=None):
        """
        Grafica los niveles de energía y transiciones opcionales.
        
        Parámetros
        ----------
        n_max : int
            Nivel máximo a mostrar
        show_transitions : bool
            Si se muestran las transiciones
        transitions : list of tuples
            Lista de tuplas (n_initial, n_final) para mostrar transiciones específicas
        
        Retorna
        -------
        matplotlib.figure.Figure
            Figura de matplotlib con el diagrama
        """
        fig, ax = plt.subplots(figsize=(10, 8))
        
        # Calcular energías en eV
        levels = [(n, self.energy_level_eV(n)) for n in range(1, n_max + 1)]
        
        # Dibujar niveles de energía
        for n, E in levels:
            ax.hlines(E, 0, 1, colors='black', linewidth=2)
            ax.text(1.05, E, f'n={n}', verticalalignment='center', fontsize=10)
            ax.text(-0.05, E, f'{E:.2f} eV', verticalalignment='center', 
                   horizontalalignment='right', fontsize=9)
        
        # Dibujar transiciones si se solicita
        if show_transitions and transitions:
            colors = plt.cm.rainbow(np.linspace(0, 1, len(transitions)))
            for idx, (n_i, n_f) in enumerate(transitions):
                E_i = self.energy_level_eV(n_i)
                E_f = self.energy_level_eV(n_f)
                wavelength = self.transition_wavelength_nm(n_i, n_f)
                
                # Flecha de transición
                ax.annotate('', xy=(0.5, E_f), xytext=(0.5, E_i),
                           arrowprops=dict(arrowstyle='<->', color=colors[idx], 
                                         lw=2, alpha=0.7))
                
                # Etiqueta con longitud de onda
                mid_E = (E_i + E_f) / 2
                ax.text(0.55, mid_E, f'{wavelength:.1f} nm', 
                       color=colors[idx], fontsize=8)
        
        ax.set_xlim(-0.2, 1.3)
        ax.set_ylabel('Energía (eV)', fontsize=12)
        ax.set_title(f'Niveles de Energía - Átomo con Z={self.Z}', fontsize=14)
        ax.set_xticks([])
        ax.grid(True, axis='y', alpha=0.3)
        ax.axhline(y=0, color='red', linestyle='--', alpha=0.5, label='E = 0 (ionización)')
        ax.legend()
        
        plt.tight_layout()
        return fig
    
    def plot_orbits(self, n_max=5):
        """
        Dibuja las órbitas electrónicas en un diagrama 2D.
        
        Parámetros
        ----------
        n_max : int
            Nivel máximo a mostrar
        
        Retorna
        -------
        matplotlib.figure.Figure
            Figura de matplotlib con las órbitas
        """
        fig, ax = plt.subplots(figsize=(8, 8))
        
        # Núcleo
        ax.plot(0, 0, 'ro', markersize=15, label='Núcleo')
        
        # Órbitas
        colors = plt.cm.viridis(np.linspace(0, 1, n_max))
        for n in range(1, n_max + 1):
            r = self.orbital_radius_angstrom(n)
            circle = plt.Circle((0, 0), r, fill=False, color=colors[n-1], 
                               linewidth=2, label=f'n={n} (r={r:.2f} Å)')
            ax.add_patch(circle)
            
            # Electrón en la órbita (posición arbitraria)
            angle = np.pi / 4 * n
            x = r * np.cos(angle)
            y = r * np.sin(angle)
            ax.plot(x, y, 'o', color=colors[n-1], markersize=8)
        
        # Configurar ejes
        max_r = self.orbital_radius_angstrom(n_max) * 1.1
        ax.set_xlim(-max_r, max_r)
        ax.set_ylim(-max_r, max_r)
        ax.set_aspect('equal')
        ax.set_xlabel('x (Å)', fontsize=12)
        ax.set_ylabel('y (Å)', fontsize=12)
        ax.set_title(f'Órbitas del Modelo de Bohr (Z={self.Z})', fontsize=14)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def __repr__(self):
        """Representación en string del átomo."""
        return f"BohrAtom(Z={self.Z})"
