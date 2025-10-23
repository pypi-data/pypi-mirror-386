# Funciones de energía disponibles
# metropolis/energies.py (V5.0)

def energy_square(x):
    return x**2

def energy_abs(x):
    return abs(x)

def energy_cube(x):
    return x**3

def energy_bimodal(x):
    return x**4-2*x**2

ENERGY={
    "square": energy_square,
    "abs": energy_abs,
    "cube": energy_cube,
    "bimodal": energy_bimodal
}