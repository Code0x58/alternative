"""Check independent answers, group identities, and generated bounded inputs."""

from math import pi, sqrt

import numpy as np
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from . import layer_trace
from .model import AXIS, rotation


@layer_trace.pytest_parametrize()
@pytest.mark.parametrize(
    ("angles", "repeats", "expected"),
    [
        ((), 0, 1),
        ((), -7, 1),
        ((0.0,) * 8, 16, 256),
        ((pi,), 1, 0),
        ((pi,), 2, -2),
        ((pi,), -2, -2),
        ((pi,), 4, 2),
        ((pi, pi), 2, 4),
        ((pi / 2,), 1, sqrt(2)),
        ((pi / 2, pi / 2), 1, 2),
        ((1e-12, -1e-12), 16, 4),
    ],
)
def test_known_traces(implementation, angles, repeats, expected) -> None:
    """Pin empty products, spinor signs, negative powers, and small angles."""
    assert implementation(angles, repeats) == pytest.approx(expected, abs=1e-10)


@layer_trace.pytest_parametrize_pairs()
@settings(max_examples=40)
@given(
    angles=st.lists(
        st.floats(min_value=-pi, max_value=pi, allow_nan=False, allow_infinity=False),
        max_size=4,
    ).map(tuple),
    repeats=st.integers(min_value=-16, max_value=16),
)
def test_generated_traces(reference, implementation, angles, repeats) -> None:
    """Compare both rewrites against the matrix oracle on generated inputs."""
    assert implementation(angles, repeats) == pytest.approx(
        reference(angles, repeats), rel=1e-10, abs=1e-10
    )


@layer_trace.pytest_parametrize()
@pytest.mark.parametrize(
    ("angles", "repeats"),
    [
        ((0.0,) * 9, 1),
        ((float("nan"),), 1),
        ((float("inf"),), 1),
        ((pi + 0.1,), 1),
        ((-pi - 0.1,), 1),
        ((), 17),
        ((), -17),
        ((), 1.5),
    ],
)
def test_invalid_domain(implementation, angles, repeats) -> None:
    """Every implementation rejects inputs outside the documented demo domain."""
    with pytest.raises(ValueError):
        implementation(angles, repeats)


@given(angle=st.floats(min_value=-pi, max_value=pi))
def test_rotation_is_special_unitary(angle: float) -> None:
    """Check the model independently of the trace shortcut."""
    matrix = rotation(angle)
    np.testing.assert_allclose(AXIS @ AXIS, np.eye(2), atol=1e-12)
    np.testing.assert_allclose(matrix.conj().T @ matrix, np.eye(2), atol=1e-12)
    assert np.linalg.det(matrix) == pytest.approx(1, abs=1e-12)


@layer_trace.pytest_parametrize()
def test_permutation_and_inverse(implementation) -> None:
    """Factor order and reversing time preserve this real-valued character."""
    angles = (0.125, -0.25, 0.375, -0.5)
    expected = implementation(angles, 7)
    assert implementation(tuple(reversed(angles)), 7) == pytest.approx(expected)
    assert implementation(angles, -7) == pytest.approx(expected, abs=1e-10)
