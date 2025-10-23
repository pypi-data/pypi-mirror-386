# Main (Metropolis V5.0)

#Admite argumentos en línea de comandos

from metropolis.core import simulated_annealing
import random
import argparse
import inspect

def neighbor_fn(x):  # Perturbación aleatoria
    return x + random.uniform(-1, 1)

def main():

    parser = argparse.ArgumentParser(description="Execute Metropolis annealing with different energy landscapes and scheduling types")
    
    parser.add_argument(
        "energy",
        choices=["square", "abs", "cube","bimodal"],
        help="Energy landscape"
    )
    
    
    parser.add_argument(
        "--schedule",
        choices=["linear", "exponential", "logarithmic"],
        default="exponential",
        help="Type of scheduling to be used (default: exponential)"
    )

    
    parser.add_argument(
        "--plot",
        action="store_true",
        help="Plotted Metropolis epochs"
    )
    args = parser.parse_args()

    initial_state = random.uniform(-10, 10)

    energy_fn,final_state, final_energy, history = simulated_annealing(
        initial_state,
        energyfun=args.energy,
        neighbor_fn=neighbor_fn,
        T0=100.0,
        cooling_rate=0.98,
        steps=500,
        schedule=args.schedule,
        plot=args.plot
        )
    print("Metropolis Algorithm v5.0")
    print("(Simmulated Annealing, SA)")
    print("--------------------------")
    print("Energy Function:")
    print(inspect.getsource(energy_fn))
    print(f"Final State: {final_state:.4f}")
    print(f"Final Energy: {final_energy:.6f}")

if __name__ == "__main__":
    main()

   

    