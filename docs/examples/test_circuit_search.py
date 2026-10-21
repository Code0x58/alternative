"""Evolve a small quantum circuit, then compare the winner with its reference."""

import random
from math import inf

import numpy as np
import pytest
from deap import algorithms, base, creator, tools
from hypothesis import given
from hypothesis import strategies as st
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import HGate, IGate, XGate, ZGate
from qiskit.exceptions import QiskitError
from qiskit.quantum_info import Operator

import alternative

GATES = (IGate(), HGate(), ZGate(), XGate())
TARGET = np.array([[0, 1], [1, 0]], dtype=np.complex128)
creator.create("CircuitDemoFitness", base.Fitness, weights=(-1.0, -1.0))
creator.create("CircuitDemoIndividual", list, fitness=creator.CircuitDemoFitness)


def reference_program() -> tuple[int, ...]:
    """Express X as H Z H, followed by two empty gate slots."""
    return (1, 2, 1, 0, 0)


def fitness(program) -> tuple[float, float]:
    """Minimise phase-sensitive unitary error, then correct circuits' gate count."""
    try:
        if len(program) > 5 or any(gene not in range(len(GATES)) for gene in program):
            raise ValueError("invalid genome")
        circuit = QuantumCircuit(1)
        for gene in program:
            circuit.append(GATES[gene], [0])
        error = float(np.linalg.norm(Operator(circuit).data - TARGET))
    except (ValueError, QiskitError):
        return inf, inf
    if not np.isfinite(error):
        return inf, inf
    if error > 1e-12:
        return error, inf
    return 0.0, float(sum(gene != 0 for gene in program))


def evolve(*, seed: int = 7, generations: int = 30):
    """Evolve a circuit, then register the winner alongside the readable reference."""
    reference = reference_program()
    if fitness(reference)[0] != 0:
        raise ValueError("invalid reference")
    random.seed(seed)
    toolbox = base.Toolbox()
    toolbox.register("evaluate", fitness)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt, low=0, up=3, indpb=0.2)
    toolbox.register("select", tools.selBest)
    individual = creator.CircuitDemoIndividual
    population = [individual(random.choices(range(4), k=5)) for _ in range(63)]
    population.append(individual(reference))
    population, _ = algorithms.eaMuPlusLambda(
        population,
        toolbox,
        mu=64,
        lambda_=64,
        cxpb=0.5,
        mutpb=0.5,
        ngen=generations,
        verbose=False,
    )
    winner = tuple(tools.selBest(population, 1)[0])
    comparison = alternative.reference(reference_program)

    @comparison.add
    def evolved_x() -> tuple[int, ...]:
        """Return the frozen search result."""
        return winner

    return comparison


@given(prefix=st.lists(st.integers(1, 3), max_size=2))
def test_cancelled_gate_words(prefix: list[int]) -> None:
    """All available nonidentity gates are self-inverse, even when noncommuting."""
    assert fitness(prefix + prefix[::-1] + [3]) == (0, 2 * len(prefix) + 1)


@pytest.mark.parametrize("generations", [0, 5])
def test_search_and_registration(generations: int) -> None:
    """Evolution retains a valid incumbent and registration preserves the default."""
    comparison = evolve(generations=generations)
    assert comparison() == reference_program()
    costs = list(comparison.measure(lambda program: fitness(program)[1]).values())
    assert 1 <= min(costs) <= max(costs) == 3


@pytest.mark.parametrize("program", [(), (2, 3, 2), (4,), (3,) * 6])
def test_invalid_candidates(program: tuple[int, ...]) -> None:
    """Wrong action, global minus signs, unknown gates, and oversized circuits lose."""
    assert fitness(program)[1] == inf


if __name__ == "__main__":
    for implementation, cost in evolve().measure(lambda p: fitness(p)[1]).items():
        print(cost, [GATES[gene].name for gene in implementation() if gene])
