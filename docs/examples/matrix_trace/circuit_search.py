"""Evolve two-qubit circuits with DEAP and evaluate them with Qiskit."""

import random
from collections.abc import Callable, Iterable
from dataclasses import dataclass
from math import inf

import numpy as np
from deap import algorithms, base, tools
from numpy.typing import NDArray
from qiskit.circuit import QuantumCircuit
from qiskit.circuit.library import CXGate, HGate, XGate, ZGate
from qiskit.exceptions import QiskitError
from qiskit.quantum_info import Operator

import alternative

Circuit = tuple[str, ...]
GATES = {
    "H0": (HGate(), (0,)),
    "H1": (HGate(), (1,)),
    "CX01": (CXGate(), (0, 1)),
    "CX10": (CXGate(), (1, 0)),
    "X0": (XGate(), (0,)),
    "Z0": (ZGate(), (0,)),
}
VOCABULARY = ("I", *GATES)
SLOTS = 7
# Qiskit orders basis states as |q1 q0>: flip q0 exactly when q1 is one.
TARGET = np.array(
    [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 0, 1], [0, 0, 1, 0]],
    dtype=np.complex128,
)


def reference_program() -> Circuit:
    """Reverse a CNOT's direction by conjugating both qubits with Hadamards."""
    return ("H0", "H1", "CX01", "H0", "H1")


def simulate(program: Circuit) -> NDArray[np.complex128]:
    """Compute the whole unitary of a bounded circuit without a backend service."""
    if len(program) > SLOTS:
        raise ValueError("the search demo limits circuits to seven slots")
    circuit = QuantumCircuit(2)
    for name in program:
        if name != "I":
            gate, qubits = GATES[name]
            circuit.append(gate, qubits)
    return np.asarray(Operator(circuit).data, dtype=np.complex128)


def circuit_fitness(program: Circuit) -> tuple[float, float]:
    """Minimise unitary error first, then gate count among correct circuits."""
    try:
        error = float(np.linalg.norm(simulate(program) - TARGET))
    except (ArithmeticError, KeyError, ValueError, QiskitError):
        return inf, inf
    if not np.isfinite(error):
        return inf, inf
    if error > 1e-12:
        return error, inf
    return 0.0, float(sum(name != "I" for name in program))


def score_candidate(build: Callable[[], Circuit]) -> float:
    """Give failed or incorrect candidates infinite cost outside the search."""
    try:
        program = build()
    except (ArithmeticError, KeyError, ValueError, QiskitError):
        return inf
    return circuit_fitness(program)[1]


class CircuitFitness(base.Fitness):
    """Compare objectives lexicographically, keeping correctness ahead of cost."""

    weights = (-1.0, -1.0)


class Individual(list[int]):
    """Encode a fixed number of gate slots, including removable identity slots."""

    def __init__(self, genes: Iterable[int]) -> None:
        """Keep each genome's fitness separate, including after DEAP clones it."""
        super().__init__(genes)
        self.fitness = CircuitFitness()


def decode(genes: Iterable[int]) -> Circuit:
    """Translate integer genes into a circuit, dropping empty slots."""
    return tuple(VOCABULARY[gene] for gene in genes if gene != 0)


def evaluate(individual: Individual) -> tuple[float, float]:
    """Adapt the Qiskit objective to DEAP's integer genome representation."""
    return circuit_fitness(decode(individual))


@dataclass(frozen=True)
class SearchResult:
    """Keep the winning program and the best valid gate count by generation."""

    program: Circuit
    best_costs: tuple[float, ...]


def evolve(
    *, seed: int = 7, population_size: int = 64, generations: int = 40
) -> SearchResult:
    """Run bounded genetic evolution, retaining the validated reference as fallback."""
    if population_size < 2 or generations < 0:
        raise ValueError("use at least two individuals and nonnegative generations")
    reference = reference_program()
    if score_candidate(lambda: reference) == inf:
        raise ValueError("reference circuit failed validation")

    # DEAP's standard operators use Python's random module. Restore its state so
    # this sequential demo does not change unrelated application randomness.
    state = random.getstate()
    random.seed(seed)
    try:
        toolbox = base.Toolbox()
        toolbox.register("mate", tools.cxTwoPoint)
        toolbox.register(
            "mutate", tools.mutUniformInt, low=0, up=len(VOCABULARY) - 1, indpb=0.2
        )
        toolbox.register("select", tools.selBest)
        toolbox.register("evaluate", evaluate)
        population = [
            Individual(random.choices(range(len(VOCABULARY)), k=SLOTS))
            for _ in range(population_size - 1)
        ]
        population.append(
            Individual(
                [VOCABULARY.index(name) for name in reference]
                + [0] * (SLOTS - len(reference))
            )
        )
        winners = tools.HallOfFame(1)
        statistics = tools.Statistics(lambda individual: individual.fitness.values[1])
        statistics.register("best_cost", min)
        _, log = algorithms.eaMuPlusLambda(
            population,
            toolbox,
            mu=population_size,
            lambda_=population_size,
            cxpb=0.5,
            mutpb=0.5,
            ngen=generations,
            stats=statistics,
            halloffame=winners,
            verbose=False,
        )
        winner = decode(winners[0])
        if score_candidate(lambda: winner) == inf:
            raise ValueError("search returned an invalid winner")
        return SearchResult(winner, tuple(log.select("best_cost")))
    finally:
        random.setstate(state)


def compare_winner(program: Circuit):
    """Register a reviewed finalist after evolution, keeping the reference default."""
    if score_candidate(lambda: program) == inf:
        raise ValueError("only register a correct circuit")

    @alternative.reference
    def synthesise_cnot() -> Circuit:
        """Keep the readable direction-reversal identity as the reference."""
        return reference_program()

    @synthesise_cnot.add
    def evolved_cnot() -> Circuit:
        """Return the frozen winner of the completed search."""
        return program

    return synthesise_cnot


if __name__ == "__main__":
    result = evolve()
    print(f"Best circuit: {result.program}")
    print(f"Best valid gate counts: {result.best_costs}")
    comparison = compare_winner(result.program)
    print(comparison.measure(lambda program: circuit_fitness(program)[1]))
