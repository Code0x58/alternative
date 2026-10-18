"""Exercise pytest helper callables with class and instance binding."""

import pytest

import alternative


def parameter_values(decorated, name: str):
    """Extract a named parameter list from a decorated test."""
    return next(mark.args[1] for mark in decorated.pytestmark if mark.args[0] == name)


@pytest.mark.parametrize("only_default", [False, True])
@pytest.mark.parametrize("double_reference", [False, True])
@pytest.mark.parametrize("explicit_default", [False, True])
@pytest.mark.parametrize("n_cache", [0, None])
def test_classmethod_pairs_bind_subclass_and_cache(
    only_default: bool,
    double_reference: bool,
    explicit_default: bool,
    n_cache: int | None,
) -> None:
    """Class method parameters use the accessed subclass and a callable cache."""
    calls = []

    class Factory:
        """Provide equivalent class methods."""

        marker = "base"

        @alternative.reference
        @classmethod
        def build(cls, value: str) -> str:
            """Record reference calls and include the class marker."""
            calls.append(value)
            return cls.marker + value

        @build.add(default=explicit_default)
        @classmethod
        def build_extra(cls, value: str) -> str:
            """Produce the same result without recording the call."""
            return cls.marker + value

    class Child(Factory):
        """Use a different marker to check inherited descriptor binding."""

        marker = "child"

    def pair_test(reference, implementation):
        """Compare already bound implementations."""
        assert reference("a") == implementation("a") == "childa"

    decorated = Child.build.pytest_parametrize_pairs(
        n_cache=n_cache,
        only_default=only_default,
        double_reference=double_reference,
    )(pair_test)
    reference = parameter_values(decorated, "reference")[0]
    assert reference("a") == reference("a") == "childa"
    assert len(calls) == (1 if n_cache is None else 2)
    for implementation in parameter_values(decorated, "implementation"):
        decorated(reference, implementation)


def test_bound_helpers_accept_direct_and_decorator_syntax() -> None:
    """Both helpers preserve an instance receiver and execute their test body."""

    class Counter:
        """Provide an instance method with per-instance data."""

        def __init__(self, value: int) -> None:
            """Store the value used by both implementations."""
            self.value = value

        @alternative.reference
        def total(self) -> int:
            """Return this instance's value."""
            return self.value

        @total.add
        def total_extra(self) -> int:
            """Return the same value."""
            return self.value

    def single_test(implementation):
        """Invoke an already bound implementation."""
        assert implementation() == 3

    def pair_test(reference, implementation):
        """Invoke an already bound reference and candidate."""
        assert reference() == implementation() == 3

    counter = Counter(3)
    for decorated in (
        counter.total.pytest_parametrize(single_test),
        counter.total.pytest_parametrize()(single_test),
    ):
        for implementation in parameter_values(decorated, "implementation"):
            decorated(implementation)
    decorated_pairs = counter.total.pytest_parametrize_pairs(pair_test)
    reference = parameter_values(decorated_pairs, "reference")[0]
    for implementation in parameter_values(decorated_pairs, "implementation"):
        decorated_pairs(reference, implementation)


@pytest.mark.parametrize("method_name", ["build", "parse"])
def test_raw_descriptor_helpers_accept_explicit_receivers(method_name: str) -> None:
    """Helpers used before owner binding expose callable underlying functions."""

    class Factory:
        """Supply class and static descriptors before binding to an owner."""

        @alternative.reference
        @classmethod
        def build(cls, value: str) -> str:
            """Return the provided value."""
            return value

        @alternative.reference
        @staticmethod
        def parse(value: str) -> str:
            """Return the provided value without a receiver."""
            return value

    descriptor = Factory.__dict__[method_name]
    arguments = (Factory, "a") if method_name == "build" else ("a",)

    def pair_test(reference, implementation):
        """Invoke callable parameters with explicit arguments."""
        assert reference(*arguments) == implementation(*arguments) == "a"

    pairs = descriptor.pytest_parametrize_pairs(
        pair_test, only_default=True, double_reference=True
    )
    reference = parameter_values(pairs, "reference")[0]
    for implementation in parameter_values(pairs, "implementation"):
        pairs(reference, implementation)
