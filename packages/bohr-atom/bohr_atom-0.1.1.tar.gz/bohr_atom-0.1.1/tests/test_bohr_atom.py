"""
Pruebas unitarias para la librería Bohr Atom.
"""

import pytest
import numpy as np
from bohr_atom import BohrAtom
from bohr_atom.constants import PhysicalConstants as pc


class TestBohrAtom:
    """Tests para la clase BohrAtom."""
    
    def test_initialization(self):
        """Verifica la inicialización correcta."""
        atom = BohrAtom(Z=1)
        assert atom.Z == 1
        
        atom_he = BohrAtom(Z=2)
        assert atom_he.Z == 2
    
    def test_invalid_Z(self):
        """Verifica que Z inválido lance excepción."""
        with pytest.raises(ValueError):
            BohrAtom(Z=0)
        
        with pytest.raises(ValueError):
            BohrAtom(Z=-1)
    
    def test_energy_level_hydrogen(self):
        """Verifica el cálculo de energía para hidrógeno."""
        atom = BohrAtom(Z=1)
        
        # Energía del nivel fundamental (n=1)
        E1 = atom.energy_level(1)
        E1_eV = atom.energy_level_eV(1)
        
        # Debe ser aproximadamente -13.6 eV
        assert abs(E1_eV + 13.6) < 0.1
        
        # Energía del nivel n=2
        E2_eV = atom.energy_level_eV(2)
        assert abs(E2_eV + 3.4) < 0.1
    
    def test_energy_scaling_with_Z(self):
        """Verifica que la energía escala con Z²."""
        atom_h = BohrAtom(Z=1)
        atom_he = BohrAtom(Z=2)
        
        E1_h = atom_h.energy_level(1)
        E1_he = atom_he.energy_level(1)
        
        # Para He+ la energía debe ser 4 veces mayor
        assert abs(E1_he / E1_h - 4.0) < 0.01
    
    def test_energy_scaling_with_n(self):
        """Verifica que la energía escala con 1/n²."""
        atom = BohrAtom(Z=1)
        
        E1 = atom.energy_level(1)
        E2 = atom.energy_level(2)
        E3 = atom.energy_level(3)
        
        # E2 debe ser E1/4
        assert abs(E2 / E1 - 0.25) < 0.01
        
        # E3 debe ser E1/9
        assert abs(E3 / E1 - 1/9) < 0.01
    
    def test_invalid_n(self):
        """Verifica que n inválido lance excepción."""
        atom = BohrAtom(Z=1)
        
        with pytest.raises(ValueError):
            atom.energy_level(0)
        
        with pytest.raises(ValueError):
            atom.orbital_radius(-1)
    
    def test_orbital_radius_hydrogen(self):
        """Verifica el cálculo del radio orbital."""
        atom = BohrAtom(Z=1)
        
        # Radio de Bohr (n=1)
        r1 = atom.orbital_radius(1)
        assert abs(r1 - pc.a_0) < 1e-15
        
        # n=2 debe ser 4 veces mayor
        r2 = atom.orbital_radius(2)
        assert abs(r2 / r1 - 4.0) < 0.01
    
    def test_orbital_radius_scaling(self):
        """Verifica que el radio escala con n²/Z."""
        atom = BohrAtom(Z=1)
        
        r1 = atom.orbital_radius(1)
        r2 = atom.orbital_radius(2)
        r3 = atom.orbital_radius(3)
        
        assert abs(r2 / r1 - 4.0) < 0.01
        assert abs(r3 / r1 - 9.0) < 0.01
    
    def test_transition_energy(self):
        """Verifica el cálculo de transición de energía."""
        atom = BohrAtom(Z=1)
        
        # Transición n=2 -> n=1 (emisión)
        delta_E = atom.transition_energy(2, 1)
        assert delta_E < 0  # Emisión
        
        # Transición n=1 -> n=2 (absorción)
        delta_E_abs = atom.transition_energy(1, 2)
        assert delta_E_abs > 0  # Absorción
        
        # Deben ser iguales en magnitud
        assert abs(delta_E + delta_E_abs) < 1e-20
    
    def test_transition_wavelength(self):
        """Verifica el cálculo de longitud de onda."""
        atom = BohrAtom(Z=1)
        
        # Transición Lyman alpha (n=2 -> n=1)
        wavelength_nm = atom.transition_wavelength_nm(2, 1)
        
        # Debe ser aproximadamente 121.5 nm
        assert abs(wavelength_nm - 121.5) < 1.0
    
    def test_transition_frequency(self):
        """Verifica el cálculo de frecuencia."""
        atom = BohrAtom(Z=1)
        
        # Transición n=2 -> n=1
        freq = atom.transition_frequency(2, 1)
        wavelength = atom.transition_wavelength(2, 1)
        
        # Verificar relación c = λ × ν
        assert abs(pc.c - wavelength * freq) < 1e3
    
    def test_rydberg_formula(self):
        """Verifica que se cumple la fórmula de Rydberg."""
        atom = BohrAtom(Z=1)
        
        # Para la serie de Balmer (transiciones a n=2)
        for n in [3, 4, 5]:
            delta_E = abs(atom.transition_energy(n, 2))
            expected = pc.Ry * (1/4 - 1/n**2)
            assert abs(delta_E - expected) < 1e-25
    
    def test_repr(self):
        """Verifica la representación en string."""
        atom = BohrAtom(Z=1)
        assert repr(atom) == "BohrAtom(Z=1)"
        
        atom_he = BohrAtom(Z=2)
        assert repr(atom_he) == "BohrAtom(Z=2)"


class TestPhysicalConstants:
    """Tests para las constantes físicas."""
    
    def test_bohr_radius(self):
        """Verifica que el radio de Bohr sea correcto."""
        # a₀ ≈ 0.529 Å
        assert abs(pc.a_0 * 1e10 - 0.529) < 0.001
    
    def test_rydberg_constant(self):
        """Verifica la constante de Rydberg."""
        # Ry ≈ 13.6 eV
        Ry_eV = pc.Ry / pc.eV
        assert abs(Ry_eV - 13.6) < 0.1
    
    def test_planck_constant(self):
        """Verifica la constante de Planck."""
        assert pc.h == 6.62607015e-34
        assert abs(pc.h_bar * 2 * np.pi - pc.h) < 1e-40


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
