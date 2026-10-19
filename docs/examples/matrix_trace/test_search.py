"""Check the search boundary, quantum equivalence, and generated circuits."""

from math import inf, isfinite

import pytest
from hypothesis import given
from hypothesis import strategies as st

from .circuit_search import (
    GATES,
    Circuit,
    rank_candidates,
    score_candidate,
    synthesise_x,
)


@pytest.mark.parametrize(
    ("program", "expected"),
    [
        (("X",), 1),
        (("H", "Z", "H"), 3),
        (("H", "H", "X"), 3),
        (("H", "H", "Z"), inf),
        (("Z", "X", "Z"), inf),
        ((), inf),
        (("unknown",), inf),
        (("X",) * 17, inf),
    ],
)
def test_circuit_objective(program: Circuit, expected: float) -> None:
    """Gate order, global phase, invalid gates, and resource limits affect fitness."""

    def build() -> Circuit:
        """Return one candidate program for evaluation."""
        return program

    assert score_candidate(build) == expected


def test_search_population() -> None:
    """A valid shorter circuit wins while wrong and failed candidates rank last."""
    scores = rank_candidates()
    assert list(scores) == ["direct_x", "synthesise_x", "wrong_x", "broken_x"]
    assert scores["direct_x"] == 1 < scores["synthesise_x"] == 3
    assert scores["wrong_x"] == scores["broken_x"] == inf
    assert isfinite(scores["synthesise_x"])
    assert synthesise_x() == ("H", "Z", "H")


@given(prefix=st.lists(st.sampled_from(("H", "X", "Z")), max_size=6).map(tuple))
def test_generated_valid_circuits(prefix: Circuit) -> None:
    """Self-inverse gate pairs cancel even across generated noncommuting words."""

    def build() -> Circuit:
        """Construct an identity followed by X from a generated gate word."""
        return prefix + tuple(reversed(prefix)) + ("X",)

    assert score_candidate(build) == 2 * len(prefix) + 1


def test_reference_failure_is_visible(monkeypatch: pytest.MonkeyPatch) -> None:
    """An invalid oracle stops the search even when another candidate is valid."""
    monkeypatch.setitem(GATES, "Z", GATES["X"])
    with pytest.raises(ValueError, match="reference circuit failed validation"):
        rank_candidates()
