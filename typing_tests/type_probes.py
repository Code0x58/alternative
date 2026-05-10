"""Type-level probes for decorator transparency.

This module is intentionally not a pytest test. It is exercised by the CI
type-checking stages, which run mypy and pyrefly over the whole repository.
"""

from typing_extensions import assert_type

import alternative


@alternative.reference
def normal_function(count: int, label: str) -> str:
    """Return a labelled value repeated a requested number of times."""
    return label * count


assert_type(normal_function(2, "a"), str)


class NormalMethods:
    """Container for instance method typing probes."""

    @alternative.reference
    def method(self, count: int, label: str) -> str:
        """Return a labelled value repeated a requested number of times."""
        return label * count

    @method.add
    def method_extra(self, count: int, label: str) -> str:
        """Return an upper-case labelled value repeated a requested number of times."""
        return label.upper() * count


normal_methods = NormalMethods()
assert_type(normal_methods.method(2, "a"), str)
assert_type(normal_methods.method_extra(2, "a"), str)


class DescriptorMethods:
    """Container for classmethod and staticmethod typing probes."""

    @alternative.reference
    @classmethod
    def build(cls, count: int, label: str) -> str:
        """Return a labelled value repeated a requested number of times."""
        return label * count

    @build.add
    @classmethod
    def build_extra(cls, count: int, label: str) -> str:
        """Return an upper-case labelled value repeated a requested number of times."""
        return label.upper() * count

    @alternative.reference
    @staticmethod
    def parse(count: int, label: str) -> str:
        """Return a labelled value repeated a requested number of times."""
        return label * count

    @parse.add
    @staticmethod
    def parse_extra(count: int, label: str) -> str:
        """Return an upper-case labelled value repeated a requested number of times."""
        return label.upper() * count


assert_type(DescriptorMethods.build(2, "a"), str)
assert_type(DescriptorMethods().build(2, "a"), str)
assert_type(DescriptorMethods.build_extra(2, "a"), str)

assert_type(DescriptorMethods.parse(2, "a"), str)
assert_type(DescriptorMethods().parse(2, "a"), str)
assert_type(DescriptorMethods.parse_extra(2, "a"), str)
