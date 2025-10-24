# Bohr Atom Library 🔬⚛️

Una librería en Python para cálculos y visualizaciones del modelo atómico de Bohr para átomos hidrogenoides.

## 📋 Descripción

Esta librería implementa el modelo de Bohr para átomos hidrogenoides (hidrógeno y iones con un solo electrón). Permite:

- Calcular niveles de energía para cualquier número cuántico principal *n*
- Determinar radios orbitales
- Calcular transiciones electrónicas (energía, frecuencia, longitud de onda)
- Visualizar diagramas de niveles de energía
- Graficar órbitas electrónicas

## 🚀 Instalación

### Desde PyPI

```bash
pip install bohr-atom
```

### Desde el código fuente

```bash
git clone https://github.com/tu-usuario/bohr-atom.git
cd bohr-atom
pip install -e .
```

## 📖 Uso Básico

### Crear un átomo de hidrógeno

```python
from bohr_atom import BohrAtom

# Átomo de hidrógeno (Z=1)
hydrogen = BohrAtom(Z=1)

# Calcular energía del nivel fundamental
E1 = hydrogen.energy_level_eV(n=1)
print(f"E₁ = {E1:.2f} eV")  # -13.60 eV

# Calcular radio de Bohr
r1 = hydrogen.orbital_radius_angstrom(n=1)
print(f"r₁ = {r1:.3f} Å")  # 0.529 Å
```

### Transiciones electrónicas

```python
# Transición de n=3 a n=2 (línea H-alpha)
wavelength = hydrogen.transition_wavelength_nm(n_initial=3, n_final=2)
print(f"λ = {wavelength:.1f} nm")  # 656.3 nm

# Frecuencia del fotón emitido
frequency = hydrogen.transition_frequency(n_initial=3, n_final=2)
print(f"ν = {frequency:.2e} Hz")
```

### Átomos hidrogenoides

```python
# Ion He⁺ (Z=2)
helium_ion = BohrAtom(Z=2)

E1_he = helium_ion.energy_level_eV(n=1)
print(f"E₁(He⁺) = {E1_he:.2f} eV")  # -54.40 eV (4 veces H)
```

### Visualizaciones

```python
import matplotlib.pyplot as plt

# Diagrama de niveles de energía
hydrogen.plot_energy_levels(n_max=5, show_transitions=True, 
                           transitions=[(3,2), (4,2), (5,2)])
plt.show()

# Órbitas electrónicas
hydrogen.plot_orbits(n_max=5)
plt.show()
```

## 📊 Ejemplos Completos

Ver la carpeta `examples/` para notebooks y scripts con casos de uso:

- `example_basic.py`: Cálculos básicos
- `example_transitions.py`: Serie de Balmer y Lyman
- `example_visualizations.ipynb`: Gráficos interactivos

## 🧪 Ejecutar Pruebas

```bash
# Instalar dependencias de desarrollo
pip install -e ".[dev]"

# Ejecutar pruebas
pytest

# Con reporte de cobertura
pytest --cov=bohr_atom --cov-report=html
```

## 📐 Fórmulas Implementadas

### Energía de los niveles

$$E_n = -\frac{Z^2 R_y}{n^2}$$

Donde:
- *Z*: número atómico
- *R<sub>y</sub>*: constante de Rydberg (13.6 eV)
- *n*: número cuántico principal

### Radio orbital

$$r_n = \frac{n^2 a_0}{Z}$$

Donde:
- *a<sub>0</sub>*: radio de Bohr (0.529 Å)

### Transiciones

$$\lambda = \frac{hc}{|\Delta E|}$$

$$\nu = \frac{|\Delta E|}{h}$$

## 🤝 Contribuciones

Este proyecto fue desarrollado como parte de un taller colaborativo. Contribuciones:

- **[Maria Moreno, SolarPunk]**: Implementación de cálculos de energía
- **[SolarPunk ]**: Funciones de transición y visualizaciones
- **[Maria Moreno ]**: Pruebas unitarias y documentación

### Flujo de trabajo

1. Fork del repositorio
2. Crear una rama: `git checkout -b feature/nueva-caracteristica`
3. Commit de cambios: `git commit -am 'Añadir nueva característica'`
4. Push a la rama: `git push origin feature/nueva-caracteristica`
5. Crear Pull Request

## 📝 Estructura del Proyecto

```
bohr-atom/
├── bohr_atom/
│   ├── __init__.py
│   ├── bohr_atom.py
│   └── constants.py
├── tests/
│   └── test_bohr_atom.py
├── examples/
│   ├── example_basic.py
│   └── example_transitions.py
├── pyproject.toml
├── README.md
└── LICENSE
```

## 📄 Licencia

MIT License - ver archivo