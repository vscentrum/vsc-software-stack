"""
Optimization algorithms for pymemembed.

Implements genetic algorithm, grid search, and direct search methods
for finding optimal membrane protein orientation.
"""

import numpy as np
from numba import jit, prange
import numba
from .core import orientate


@jit(nopython=True, parallel=True, fastmath=True, cache=True)
def evaluate_population(population, backbone_x, backbone_y, backbone_z,
                       backbone_res, mempot, force_span):
    """
    Evaluate GA population in parallel.

    Uses Numba's automatic parallelization via prange to evaluate
    multiple genomes simultaneously (one per thread).

    Args:
        population: 2D array of genomes (n_pop × 3)
        backbone_x/y/z: Backbone coordinate arrays
        backbone_res: Residue type indices
        mempot: Membrane potential array
        force_span: Membrane spanning constraint

    Returns:
        1D array of energies (n_pop,)
    """
    n_pop = len(population)
    energies = np.empty(n_pop, dtype=np.float64)

    for i in prange(n_pop):  # Numba parallelizes this loop
        xrt = population[i, 0]
        yrt = population[i, 1]
        z_trans = population[i, 2]
        energies[i] = orientate(backbone_x, backbone_y, backbone_z,
                               backbone_res, xrt, yrt, z_trans,
                               mempot, force_span)
    return energies


@jit(nopython=True, fastmath=True, cache=True)
def batch_rank_selection(population, energies, n_select):
    """
    Batch rank-based selection for entire new population.

    Matches C++ MEMEMBED gaselect() - performs rank-based roulette wheel
    selection n_select times efficiently in a single JIT-compiled function.

    Args:
        population: 2D array of genomes (n_pop × n_genes)
        energies: 1D array of energies (n_pop,)
        n_select: Number of individuals to select

    Returns:
        2D array of selected genomes (n_select × n_genes)
    """
    n_pop = len(population)
    n_genes = population.shape[1]
    selected = np.empty((n_select, n_genes), dtype=np.float64)

    # Sort indices by energy (best first)
    sorted_indices = np.argsort(energies)

    # Assign selection values based on rank (poolsize - rank)
    # Best gets n_pop, worst gets 1
    selection_values = np.empty(n_pop, dtype=np.float64)
    for i in range(n_pop):
        selection_values[sorted_indices[i]] = n_pop - i

    # Calculate total fitness sum
    fitsum = np.sum(selection_values)

    # Perform n_select roulette wheel selections
    for sel_idx in range(n_select):
        ptr = np.random.random() * fitsum
        cumsum = 0.0

        for i in range(n_pop):
            cumsum += selection_values[i]
            if cumsum >= ptr:
                selected[sel_idx] = population[i].copy()
                break

    return selected


@jit(nopython=True, fastmath=True, cache=True)
def batch_crossover(population, crossover_rate):
    """
    Batch crossover operation on entire population.

    Matches C++ MEMEMBED crossovr() - multi-point crossover with crossover rate.

    Args:
        population: 2D array of genomes (n_pop × n_genes)
        crossover_rate: Probability of crossover per pair

    Returns:
        Modified population (in-place, but also returned)
    """
    n_pop = population.shape[0]
    n_genes = population.shape[1]

    # Process pairs
    for i in range(0, n_pop - 1, 2):
        if np.random.random() < crossover_rate:
            # Save original genomes
            child1 = population[i].copy()
            child2 = population[i + 1].copy()

            # Multi-point uniform crossover
            for j in range(n_genes):
                if np.random.random() < 0.5:
                    population[i, j] = child2[j]
                    population[i + 1, j] = child1[j]

    return population


@jit(nopython=True, fastmath=True, cache=True)
def batch_mutate(population, mutation_rate, bounds, best_idx):
    """
    Batch mutation operation on entire population.

    Matches C++ MEMEMBED mutate() - Gaussian mutation with elitism
    (best individual is not mutated).

    Args:
        population: 2D array of genomes (n_pop × n_genes)
        mutation_rate: Probability of mutation per gene
        bounds: 2D array of (min, max) for each parameter
        best_idx: Index of best individual (not mutated)

    Returns:
        Modified population (in-place, but also returned)
    """
    n_pop = population.shape[0]
    n_genes = population.shape[1]

    for i in range(n_pop):
        # Skip best individual (elitism)
        if i == best_idx:
            continue

        for j in range(n_genes):
            if np.random.random() < mutation_rate:
                # Gaussian mutation: sigma = 25% of parameter range
                sigma = (bounds[j, 1] - bounds[j, 0]) * 0.25
                population[i, j] += np.random.randn() * sigma

                # Clamp to bounds
                if population[i, j] < bounds[j, 0]:
                    population[i, j] = bounds[j, 0]
                elif population[i, j] > bounds[j, 1]:
                    population[i, j] = bounds[j, 1]

    return population


def run_ga(backbone_x, backbone_y, backbone_z, backbone_res, mempot,
           max_calls=1000000, threads=4, force_span=False, verbose=True,
           max_c_dist=None):
    """
    Genetic algorithm optimizer.

    Uses tournament selection, uniform crossover, and Gaussian mutation
    to find optimal membrane protein orientation.

    Args:
        backbone_x/y/z: Backbone coordinate arrays
        backbone_res: Residue type indices
        mempot: Membrane potential array (20×34)
        max_calls: Maximum function evaluations
        threads: Number of parallel threads
        force_span: Enforce membrane spanning constraint
        verbose: Print progress messages

    Returns:
        tuple: (best_genome, best_energy, n_calls)
            best_genome: [xrt, yrt, z_trans] in radians/Angstroms
            best_energy: Final energy value
            n_calls: Actual number of function evaluations
    """
    # Set thread count
    numba.set_num_threads(threads)

    # GA parameters (matching C++ MEMEMBED)
    pop_size = 10000
    max_generations = max_calls // pop_size
    mutation_rate = 0.1  # C++ mutrate
    crossover_rate = 0.9  # C++ crosrate

    # Parameter bounds (matching C++ MEMEMBED: maxparam[2] = maxcdist + 15)
    max_z = (max_c_dist + 15.0) if max_c_dist is not None else (np.max(np.abs(backbone_z)) + 50.0)
    bounds = np.array([
        [0.0, 2.0 * np.pi],      # X rotation
        [0.0, 2.0 * np.pi],      # Y rotation
        [-15.0, max_z]           # Z translation
    ], dtype=np.float64)

    # Initialize population randomly
    population = np.empty((pop_size, 3), dtype=np.float64)
    for i in range(pop_size):
        for j in range(3):
            population[i, j] = np.random.uniform(bounds[j, 0], bounds[j, 1])

    best_energy = np.inf
    prev_best_energy = np.inf
    best_genome = None
    n_calls = 0
    last_improvement_gen = 0

    if verbose:
        print(f"\nRunning GA optimizer:")
        print(f"  Population size: {pop_size}")
        print(f"  Max generations: {max_generations}")
        print(f"  Threads: {threads}")
        print(f"  Max calls: {max_calls}\n")

    for generation in range(max_generations):
        # Evaluate population in parallel
        energies = evaluate_population(population, backbone_x, backbone_y,
                                       backbone_z, backbone_res, mempot,
                                       force_span)
        n_calls += pop_size

        # Calculate statistics (matching C++ MEMEMBED)
        gen_best_energy = np.min(energies)
        gen_worst_energy = np.max(energies)
        gen_best_idx = np.argmin(energies)

        # Update best solution if improved
        if gen_best_energy < prev_best_energy:
            prev_best_energy = gen_best_energy
            last_improvement_gen = generation

        if gen_best_energy < best_energy:
            best_energy = gen_best_energy
            best_genome = population[gen_best_idx].copy()

            if verbose:
                print(f"Generation {generation:4d}: Energy = {best_energy:.6f} "
                      f"(calls: {n_calls:,})")

        # Convergence criteria (matching C++ MEMEMBED ga.cpp:115)
        # 1. No improvement for 50 generations
        # 2. Population converged (worst == best)
        # 3. Max calls reached
        if generation - last_improvement_gen > 50:
            if verbose:
                print(f"\n*** Convergence detected: No improvement for 50 generations")
            break
        elif np.abs(gen_worst_energy - gen_best_energy) < 1e-10:
            if verbose:
                print(f"\n*** Convergence detected: Population converged")
            break
        elif n_calls >= max_calls:
            if verbose:
                print(f"\n*** Convergence detected: Max calls reached")
            break

        # Create next generation (matching C++ MEMEMBED)
        # All operations use batch JIT-compiled functions for speed

        # Selection: rank-based roulette wheel (matching C++ gaselect)
        new_population = batch_rank_selection(population, energies, pop_size)

        # Crossover: multi-point with crossover rate (matching C++ crossovr)
        new_population = batch_crossover(new_population, crossover_rate)

        # Mutation: Gaussian with mutation rate (matching C++ mutate)
        # Best individual is not mutated (elitism)
        best_idx = np.argmin(energies)
        new_population = batch_mutate(new_population, mutation_rate, bounds, best_idx)

        population = new_population

    if verbose:
        print(f"\nGA optimization complete:")
        print(f"  Final energy: {best_energy:.6f}")
        print(f"  Total calls: {n_calls:,}")
        print(f"  X rotation: {np.degrees(best_genome[0]):.2f}°")
        print(f"  Y rotation: {np.degrees(best_genome[1]):.2f}°")
        print(f"  Z translation: {best_genome[2]:.2f} Å\n")

    return best_genome, best_energy, n_calls


def run_grid(backbone_x, backbone_y, backbone_z, backbone_res, mempot,
             force_span=False, verbose=True, max_c_dist=None):
    """
    Exhaustive grid search optimizer.

    Samples orientation space on a coarse grid. Much slower than GA
    but more thorough (used for validation/testing).

    Args:
        backbone_x/y/z: Backbone coordinate arrays
        backbone_res: Residue type indices
        mempot: Membrane potential array
        force_span: Enforce membrane spanning constraint
        verbose: Print progress messages

    Returns:
        tuple: (best_genome, best_energy, n_calls)
    """
    # Grid parameters (coarse grid to keep runtime reasonable)
    x_steps = 36  # 10° increments
    y_steps = 36  # 10° increments
    z_steps = 100  # 1 Å increments (assuming ~100 Å range)

    max_z = (max_c_dist + 15.0) if max_c_dist is not None else (np.max(np.abs(backbone_z)) + 50.0)
    z_range = np.linspace(-15.0, max_z, z_steps)

    best_energy = np.inf
    best_genome = None
    n_calls = 0

    if verbose:
        total_calls = x_steps * y_steps * z_steps
        print(f"\nRunning grid search:")
        print(f"  Grid: {x_steps} × {y_steps} × {z_steps}")
        print(f"  Total evaluations: {total_calls:,}\n")

    for i, xrt in enumerate(np.linspace(0, 2*np.pi, x_steps)):
        for j, yrt in enumerate(np.linspace(0, 2*np.pi, y_steps)):
            for k, z_trans in enumerate(z_range):
                energy = orientate(backbone_x, backbone_y, backbone_z,
                                  backbone_res, xrt, yrt, z_trans,
                                  mempot, force_span)
                n_calls += 1

                if energy < best_energy:
                    best_energy = energy
                    best_genome = np.array([xrt, yrt, z_trans])

                    if verbose:
                        print(f"Grid [{i:2d},{j:2d},{k:3d}]: Energy = {best_energy:.6f}")

    if verbose:
        print(f"\nGrid search complete:")
        print(f"  Final energy: {best_energy:.6f}")
        print(f"  Total calls: {n_calls:,}")
        print(f"  X rotation: {np.degrees(best_genome[0]):.2f}°")
        print(f"  Y rotation: {np.degrees(best_genome[1]):.2f}°")
        print(f"  Z translation: {best_genome[2]:.2f} Å\n")

    return best_genome, best_energy, n_calls


def run_direct(backbone_x, backbone_y, backbone_z, backbone_res, mempot,
               max_calls=100000, force_span=False, verbose=True,
               max_c_dist=None):
    """
    Hooke-Jeeves direct search optimizer.

    Pattern search algorithm that doesn't require gradients.
    Good for local refinement after GA.

    Args:
        backbone_x/y/z: Backbone coordinate arrays
        backbone_res: Residue type indices
        mempot: Membrane potential array
        max_calls: Maximum function evaluations
        force_span: Enforce membrane spanning constraint
        verbose: Print progress messages

    Returns:
        tuple: (best_genome, best_energy, n_calls)
    """
    # Initialize at center of search space
    max_z = (max_c_dist + 15.0) if max_c_dist is not None else (np.max(np.abs(backbone_z)) + 50.0)
    current = np.array([np.pi, np.pi, max_z / 2.0])

    # Step sizes
    step_size = np.array([0.1, 0.1, 1.0])  # radians, radians, Angstroms
    reduction_factor = 0.5
    min_step_size = 1e-4

    best_energy = orientate(backbone_x, backbone_y, backbone_z,
                           backbone_res, current[0], current[1], current[2],
                           mempot, force_span)
    n_calls = 1

    if verbose:
        print(f"\nRunning direct search:")
        print(f"  Initial energy: {best_energy:.6f}\n")

    while np.any(step_size > min_step_size) and n_calls < max_calls:
        improved = False

        # Try each dimension
        for i in range(3):
            # Try positive step
            test = current.copy()
            test[i] += step_size[i]
            energy = orientate(backbone_x, backbone_y, backbone_z,
                             backbone_res, test[0], test[1], test[2],
                             mempot, force_span)
            n_calls += 1

            if energy < best_energy:
                current = test
                best_energy = energy
                improved = True
                if verbose:
                    print(f"Call {n_calls:6d}: Energy = {best_energy:.6f} (dim {i} +)")
                continue

            # Try negative step
            test = current.copy()
            test[i] -= step_size[i]
            energy = orientate(backbone_x, backbone_y, backbone_z,
                             backbone_res, test[0], test[1], test[2],
                             mempot, force_span)
            n_calls += 1

            if energy < best_energy:
                current = test
                best_energy = energy
                improved = True
                if verbose:
                    print(f"Call {n_calls:6d}: Energy = {best_energy:.6f} (dim {i} -)")

        # Reduce step size if no improvement
        if not improved:
            step_size *= reduction_factor
            if verbose and np.any(step_size > min_step_size):
                print(f"  Reducing step size to {step_size}")

    if verbose:
        print(f"\nDirect search complete:")
        print(f"  Final energy: {best_energy:.6f}")
        print(f"  Total calls: {n_calls:,}")
        print(f"  X rotation: {np.degrees(current[0]):.2f}°")
        print(f"  Y rotation: {np.degrees(current[1]):.2f}°")
        print(f"  Z translation: {current[2]:.2f} Å\n")

    return current, best_energy, n_calls
