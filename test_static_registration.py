"""Keep imported static method candidates independent of instance receivers."""

import pytest

import alternative


def parameter_values(decorated):
    """Read pytest's dynamically attached implementation parameters."""
    return decorated.pytestmark[0].args[1]


@pytest.mark.parametrize("default", [False, True])
@pytest.mark.parametrize("bound_registration", [False, True])
def test_plain_static_candidate_preserves_binding(
    default: bool, bound_registration: bool
) -> None:
    """Plain candidates work directly, through classes, instances, and test helpers."""

    class Parser:
        """Expose a static integer parser."""

        @alternative.reference
        @staticmethod
        def parse(value: str) -> int:
            """Parse using the reference implementation."""
            return int(value)

    def candidate(value: str) -> int:
        """Provide an imported-function-style candidate."""
        return int(value, 10)

    parser = Parser()
    target = parser.parse if bound_registration else Parser.parse
    registered = target.add(candidate, default=default)
    assert registered("3") == Parser.parse("3") == parser.parse("3") == 3

    class RegisteredParser(Parser):
        """Expose the registered implementation directly as a descriptor."""

        candidate = registered

    assert RegisteredParser.candidate("4") == RegisteredParser().candidate("4") == 4

    def placeholder(implementation):
        """Check each already-bound static implementation."""
        assert implementation("5") == 5

    decorated = parser.parse.pytest_parametrize(placeholder)
    for implementation in parameter_values(decorated):
        decorated(implementation)
