"""Check genetic search, quantum equivalence, and the candidate boundary."""

import random
from math import inf

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st
from qiskit.exceptions import QiskitError

from . import circuit_search
from .circuit_search import (
    GATES,
    SLOTS,
    TARGET,
    VOCABULARY,
    Circuit,
    CircuitFitness,
    Individual,
    circuit_fitness,
    compare_winner,
    decode,
    evaluate,
    evolve,
    reference_program,
    score_candidate,
    simulate,
)


@pytest.mark.parametrize(
    ("program", "expected"),
    [
        (("CX10",), 1),
        (reference_program(), 5),
        (("I", "H0", "H0", "CX10"), 3),
        (("CX01",), inf),
        (("X0", "Z0", "X0", "Z0", "CX10"), inf),
        ((), inf),
        (("unknown",), inf),
        (("CX10",) * (SLOTS + 1), inf),
    ],
)
def test_circuit_objective(program: Circuit, expected: float) -> None:
    """Gate order, global phase, invalid gates, and resource limits affect fitness."""

    def build() -> Circuit:
        """Return one candidate program for evaluation."""
        return program

    assert score_candidate(build) == expected


@pytest.mark.parametrize("error", [ValueError, ArithmeticError, KeyError, QiskitError])
def test_failed_construction(error: type[Exception]) -> None:
    """Expected candidate construction failures receive infinite cost."""

    def broken() -> Circuit:
        """Represent a generated circuit that cannot be constructed."""
        raise error("invalid generated circuit")

    assert score_candidate(broken) == inf


def test_phase_sensitive_contract() -> None:
    """A global minus sign fails even though uncontrolled probabilities agree."""
    program = ("X0", "Z0", "X0", "Z0", "CX10")
    np.testing.assert_allclose(simulate(program), -TARGET, atol=1e-12)
    assert circuit_fitness(program)[0] > 0
    assert score_candidate(lambda: program) == inf


def test_fitness_prioritises_correctness() -> None:
    """Incorrect cheap circuits lose to every correct circuit under DEAP ordering."""
    correct = CircuitFitness(circuit_fitness(reference_program()))
    short = CircuitFitness(circuit_fitness(("CX10",)))
    wrong = CircuitFitness(circuit_fitness(()))
    failed = CircuitFitness(circuit_fitness(("unknown",)))
    assert short > correct > wrong > failed


@settings(max_examples=40)
@given(prefix=st.lists(st.sampled_from(tuple(GATES)), max_size=3).map(tuple))
def test_generated_valid_circuits(prefix: Circuit) -> None:
    """Self-inverse gate pairs cancel even across generated noncommuting words."""

    def build() -> Circuit:
        """Construct an identity followed by reverse CNOT from a gate word."""
        return prefix + tuple(reversed(prefix)) + ("CX10",)

    assert score_candidate(build) == 2 * len(prefix) + 1


@given(
    genes=st.lists(st.integers(0, len(VOCABULARY) - 1), min_size=SLOTS, max_size=SLOTS)
)
def test_genome_decoding(genes: list[int]) -> None:
    """Any genome the genetic operators can produce builds a bounded unitary."""
    program = decode(genes)
    matrix = simulate(program)
    assert len(program) <= SLOTS
    assert "I" not in program
    np.testing.assert_allclose(matrix.conj().T @ matrix, np.eye(4), atol=1e-12)
    assert evaluate(Individual(genes)) == circuit_fitness(program)


@pytest.mark.parametrize("generations", [0, 6])
def test_evolution_retains_valid_incumbent(generations: int) -> None:
    """Real genetic evolution cannot lose the seeded reference or change randomness."""
    state = random.getstate()
    result = evolve(seed=7, population_size=24, generations=generations)
    assert random.getstate() == state
    assert len(result.best_costs) == generations + 1
    assert all(cost <= 5 for cost in result.best_costs)
    assert all(a >= b for a, b in zip(result.best_costs, result.best_costs[1:]))
    assert score_candidate(lambda: result.program) == min(result.best_costs)
    np.testing.assert_allclose(simulate(result.program), TARGET, atol=1e-12)


def test_reviewed_winner_registration() -> None:
    """Only completed, valid finalists enter a fresh alternatives registry."""
    comparison = compare_winner(("CX10",))
    assert comparison() == reference_program()
    scores = comparison.measure(lambda program: circuit_fitness(program)[1])
    assert list(scores.values()) == [1, 5]
    for implementation in comparison.implementations:
        np.testing.assert_allclose(simulate(implementation()), TARGET, atol=1e-12)
    with pytest.raises(ValueError, match="only register a correct circuit"):
        compare_winner(("CX01",))


@pytest.mark.parametrize(("population_size", "generations"), [(1, 5), (8, -1)])
def test_invalid_search_budget(population_size: int, generations: int) -> None:
    """Reject configurations outside the bounded evolutionary demo contract."""
    with pytest.raises(ValueError, match="at least two individuals"):
        evolve(population_size=population_size, generations=generations)


def test_reference_failure_is_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """An invalid oracle stops the search even when another candidate is valid."""
    monkeypatch.setitem(GATES, "CX01", GATES["CX10"])
    with pytest.raises(ValueError, match="reference circuit failed validation"):
        evolve(population_size=2, generations=0)


def test_nonfinite_simulation_is_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """NaN from a faulty evaluator never reaches DEAP's fitness comparison."""
    monkeypatch.setattr(
        circuit_search,
        "simulate",
        lambda program: np.full((4, 4), np.nan, dtype=np.complex128),
    )
    assert circuit_fitness(("H0",)) == (inf, inf)
