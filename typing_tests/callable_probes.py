"""Type-level probes for assigning alternative wrappers to Callable types."""

from collections.abc import Callable

from typing_extensions import assert_type

import alternative


@alternative.reference
def normal_function(count: int, label: str) -> str:
    """Return a labelled value repeated a requested number of times."""
    return label * count


normal_function_callable: Callable[[int, str], str] = normal_function


class NormalMethods:
    """Container for instance method callable assignment probes."""

    @alternative.reference
    def method(self, count: int, label: str) -> str:
        """Return a labelled value repeated a requested number of times."""
        return label * count


normal_methods = NormalMethods()
bound_method_callable: Callable[[int, str], str] = normal_methods.method
unbound_method_callable: Callable[[NormalMethods, int, str], str] = NormalMethods.method


class DescriptorMethods:
    """Container for classmethod and staticmethod callable assignment probes."""

    @alternative.reference
    @classmethod
    def build(cls, count: int, label: str) -> str:
        """Return a labelled value repeated a requested number of times."""
        return label * count

    @alternative.reference
    @staticmethod
    def parse(count: int, label: str) -> str:
        """Return a labelled value repeated a requested number of times."""
        return label * count


classmethod_callable: Callable[[int, str], str] = DescriptorMethods.build
bound_classmethod_callable: Callable[[int, str], str] = DescriptorMethods().build

staticmethod_callable: Callable[[int, str], str] = DescriptorMethods.parse
bound_staticmethod_callable: Callable[[int, str], str] = DescriptorMethods().parse


class ImportedStatic:
    """Preserve static calls when registering an ordinary imported function."""

    @alternative.reference
    @staticmethod
    def parse(value: str) -> int:
        """Parse a decimal integer."""
        return int(value)


def imported_parse(value: str) -> int:
    """Accept the same public signature without a receiver."""
    return int(value, 10)


ImportedStatic.parse.add(imported_parse, default=True)
assert_type(ImportedStatic.parse("3"), int)
assert_type(ImportedStatic().parse("3"), int)
