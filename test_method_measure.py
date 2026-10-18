"""Measure method implementations with the same binding rules as pytest helpers."""

import pytest

import alternative


@pytest.mark.parametrize("method_name", ["instance", "factory", "static"])
@pytest.mark.parametrize("through_instance", [False, True])
def test_measure_preserves_method_receivers(
    method_name: str, through_instance: bool
) -> None:
    """Class, subclass, instance, and raw descriptor measurements keep their receiver."""

    class Example:
        """Build strings using each supported descriptor style."""

        marker = "base"

        @alternative.reference
        def instance(self, value: str, *, suffix: str = "") -> str:
            """Include the instance's marker."""
            return self.marker + value + suffix

        @instance.add(default=True)
        def instance_candidate(self, value: str, *, suffix: str = "") -> str:
            """Build the same instance result."""
            return f"{self.marker}{value}{suffix}"

        @alternative.reference
        @classmethod
        def factory(cls, value: str, *, suffix: str = "") -> str:
            """Include the accessed class's marker."""
            return cls.marker + value + suffix

        @factory.add(default=True)
        @classmethod
        def factory_candidate(cls, value: str, *, suffix: str = "") -> str:
            """Build the same class result."""
            return f"{cls.marker}{value}{suffix}"

        @alternative.reference
        @staticmethod
        def static(value: str, *, suffix: str = "") -> str:
            """Build a result without a receiver."""
            return value + suffix

        @static.add(default=True)
        @staticmethod
        def static_candidate(value: str, *, suffix: str = "") -> str:
            """Build the same static result."""
            return f"{value}{suffix}"

    class Child(Example):
        """Make incorrect class binding observable."""

        marker = "child"

    child = Child()
    receiver = child if through_instance else Child
    target = getattr(receiver, method_name)
    arguments = (
        (child, "a") if method_name == "instance" and not through_instance else ("a",)
    )
    measured = target.measure(len, *arguments, suffix="b")
    expected = 2 if method_name == "static" else 7
    assert list(measured.values()) == [expected, expected]
    assert tuple(measured) == target.implementations
    assert len(target(*arguments, suffix="b")) == expected
    with pytest.raises(alternative.AddTooLateError):
        target.add(target.reference.implementation)


@pytest.mark.parametrize("method_name", ["factory", "static"])
def test_measure_raw_descriptor_accepts_explicit_receiver(method_name: str) -> None:
    """Raw class descriptors use explicit receivers, just like pytest helpers."""

    class Example:
        """Expose descriptors before binding them to an owner."""

        @alternative.reference
        @classmethod
        def factory(cls, value: str) -> str:
            """Return a string through a class method."""
            return value

        @alternative.reference
        @staticmethod
        def static(value: str) -> str:
            """Return a string through a static method."""
            return value

    target = Example.__dict__[method_name]
    arguments = (Example, "abc") if method_name == "factory" else ("abc",)
    assert list(target.measure(len, *arguments).values()) == [3]
