"""Evolve a small quantum circuit, then compare the winner with its reference."""

import random
from math import inf

import numpy as np
import pytest
from deap import algorithms, base, tools
from hypothesis import given
from hypothesis import strategies as st
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import HGate, IGate, XGate, ZGate
from qiskit.exceptions import QiskitError
from qiskit.quantum_info import Operator

import alternative

GATES = (IGate(), HGate(), ZGate(), XGate())
TARGET = np.array([[0, 1], [1, 0]], dtype=np.complex128)


@alternative.reference
def synthesise_x() -> tuple[int, ...]:
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
    return (
        (0.0, float(sum(gene != 0 for gene in program)))
        if error <= 1e-12
        else (error, inf)
    )


class CircuitFitness(base.Fitness):
    """Keep correctness ahead of cost with lexicographic minimisation."""

    weights = (-1.0, -1.0)


class Individual(list[int]):
    """Give each DEAP genome its own fitness record."""

    def __init__(self, genes) -> None:
        """Initialise a five-slot gate sequence."""
        super().__init__(genes)
        self.fitness = CircuitFitness()


def evolve(*, seed: int = 7, generations: int = 30) -> tuple[int, ...]:
    """Run a small, sequential DEAP search with the valid reference as fallback."""
    reference = synthesise_x.reference()
    if fitness(reference)[0] != 0:
        raise ValueError("invalid reference")
    random.seed(seed)
    toolbox = base.Toolbox()
    toolbox.register("evaluate", fitness)
    toolbox.register("mate", tools.cxTwoPoint)
    toolbox.register("mutate", tools.mutUniformInt, low=0, up=3, indpb=0.2)
    toolbox.register("select", tools.selBest)
    population = [Individual(random.choices(range(4), k=5)) for _ in range(63)]
    population.append(Individual(reference))
    winners = tools.HallOfFame(1)
    algorithms.eaMuPlusLambda(
        population,
        toolbox,
        mu=64,
        lambda_=64,
        cxpb=0.5,
        mutpb=0.5,
        ngen=generations,
        halloffame=winners,
        verbose=False,
    )
    return tuple(winners[0])


def compare_winner(program: tuple[int, ...]):
    """Register a completed finalist in a fresh set, retaining the reference default."""
    if fitness(program)[0] != 0:
        raise ValueError("invalid winner")
    comparison = alternative.reference(synthesise_x.reference.implementation)

    @comparison.add
    def evolved_x() -> tuple[int, ...]:
        """Return the frozen search result."""
        return program

    return comparison


@given(prefix=st.lists(st.integers(1, 3), max_size=2))
def test_cancelled_gate_words(prefix: list[int]) -> None:
    """All available nonidentity gates are self-inverse, even when noncommuting."""
    assert fitness(prefix + prefix[::-1] + [3]) == (0, 2 * len(prefix) + 1)


def test_search_and_registration() -> None:
    """Evolution retains a valid incumbent and registration preserves the default."""
    winner = evolve(generations=5)
    assert fitness(winner)[0] == 0
    assert fitness(winner)[1] <= 3
    comparison = compare_winner(winner)
    assert comparison() == synthesise_x.reference()
    assert all(
        np.isfinite(cost)
        for cost in comparison.measure(lambda p: fitness(p)[1]).values()
    )


@pytest.mark.parametrize("program", [(), (2, 3, 2), (4,), (3,) * 6])
def test_invalid_candidates(program: tuple[int, ...]) -> None:
    """Wrong action, global minus signs, unknown gates, and oversized circuits lose."""
    assert fitness(program)[1] == inf
    with pytest.raises(ValueError, match="invalid winner"):
        compare_winner(program)


if __name__ == "__main__":
    winner = evolve()
    print(tuple(GATES[gene].name for gene in winner if gene))
    print(compare_winner(winner).measure(lambda program: fitness(program)[1]))
