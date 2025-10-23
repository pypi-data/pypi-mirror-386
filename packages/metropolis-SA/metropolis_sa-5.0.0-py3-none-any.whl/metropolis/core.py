# Módulo principal
# metropolis/core.py (versión V5.0)

import math
import random
from metropolis.schedule import SCHEDULES
from metropolis.energies import ENERGY
from metropolis.visualization import plot_history

def simulated_annealing(initial_state, energyfun, neighbor_fn,
                        T0=100.0, cooling_rate=0.99, steps=1000,
                        schedule="exponential", plot=False):
    """
    Metropolis / Simulated Annealing robusto.
    - schedule: "exponential", "linear", "logarithmic"
    - protección contra T<=0, uso de math.exp

    En el código actual solo se define una temperatura inicial (T0), y la “final” está implícita  
    """
    schedule_fn = SCHEDULES.get(schedule)
    if schedule_fn is None:
        raise ValueError(f"Schedule not supported: {schedule}")

    energy_fn = ENERGY.get(energyfun)
    if energy_fn is None:
        raise ValueError(f"Energy not supported: {energyfun}")

    # Estado y energía inicial
    state = initial_state
    energy= energy_fn(state)
    history = [energy]

    for step in range(1, steps + 1):
        # obtener temperatura, protegiendo firma schedule(T0, step, cooling_rate)
        T = schedule_fn(T0, cooling_rate, step)

        # proteger contra T <= 0
        if T <= 0:
            T = 1e-12

        candidate = neighbor_fn(state)
        candidate_energy = energy_fn(candidate)
        delta = candidate_energy - energy

        if delta <= 0:
            # aceptamos mejora
            state, energy = candidate, candidate_energy
        else:
            # probabilidad de aceptar subida
            p = math.exp(-delta / T)
            if random.random() < p:
                state, energy = candidate, candidate_energy

        history.append(energy)

    if plot:
        plot_history(history)

    return energy_fn,state, energy, history