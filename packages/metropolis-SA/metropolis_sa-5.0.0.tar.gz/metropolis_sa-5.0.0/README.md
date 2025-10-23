# Metropolis

Implementación del **algoritmo de Metropolis** como núcleo del método de **Simulated Annealing**


## Instalación

En tu entorno de Anaconda (u otro entorno virtual):

```bash
pip install -e .
```
Esto instala el paquete localmente en modo editable.

Si se prefiere usar dependencias explícitas:

```bash
pip install -r requirements.txt
```

## Estructura Metropolis V5.0

```text
Metropolis/
├── README.md
├── LICENSE
├── requirements.txt
├── metropolis/
│   ├── __init__.py      # inicialización paquete
│   ├── core.py          # núcleo del algoritmo
│   ├── schedule.py      # funciones de temperatura (v2+)
│   ├── energies.py      # funciones de temperatura (v5+)
│   └── visualization.py # para plots de convergencia (v3+)
├── run/
│   └── anneal.py
└── tests/
``` 

## Ejecución

```
usage: anneal.py [-h] [--schedule {linear,exponential,logarithmic}] [--plot] {square,abs,cube,bimodal}

Execute Metropolis annealing with different energy landscapes and scheduling types

positional arguments:
  {square,abs,cube,bimodal}
                        Energy landscape

options:
  -h, --help            show this help message and exit
  --schedule {linear,exponential,logarithmic}
                        Type of scheduling to be used (default: exponential)
  --plot                Plotted Metropolis epochs

```

Ejemplos:

```bash
python -m run.anneal square --plot
python -m run.anneal bimodal --schedule exponential --plot
python -m run.anneal bimodal --schedule linear
```

## Historial

V1.0
Motor Monte Carlo básico
Ejemplo de uso

V2.0
Incorpora varios schedules  de enfriamiento

V3.0
- Añadido Módulo `visualization.py` para graficar convergencia.
- Corregido bug en orden de parámetros de llamada a la función scheduling
- Se evitan energías negativas
- Otros cambios menores.

V4.0
- Añadido soporte línea de comandos.

V5.0
- Versión final estable
- Posibilidad de indicar función paisaje-energético
- Cambiado 
- Salida en inglés
