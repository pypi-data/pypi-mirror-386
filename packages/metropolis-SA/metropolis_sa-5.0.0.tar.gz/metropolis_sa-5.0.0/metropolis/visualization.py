#Módulo de visualización 
#metropolis/visualization.py V5.0

import matplotlib.pyplot as plt

def plot_history(history):
    """Energy evolution during annealing."""
    plt.figure(figsize=(8, 4))
    plt.plot(history, label="Energy", linewidth=1.5)
    plt.xlabel("Iter")
    plt.ylabel("Energy")
    plt.title("Energy evolution during annealing")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.show()