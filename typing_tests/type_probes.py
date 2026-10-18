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
assert_type(normal_function(count=2, label="a"), str)
assert_type(normal_function(2, label="a"), str)


@alternative.reference()
def default_arguments(count: int = 2, *, label: str = "a") -> str:
    """Preserve defaults and keyword-only parameters."""
    return label * count


assert_type(default_arguments(), str)
assert_type(default_arguments(count=3, label="b"), str)


@alternative.reference
def make_number(kind: type[int], value: str) -> int:
    """Keep an explicit type argument in ordinary factory functions."""
    return kind(value)


assert_type(make_number(int, "3"), int)
assert_type(make_number(kind=int, value="3"), int)


@alternative.reference
def collect_values(*values: int, **options: int) -> int:
    """Preserve variadic arguments and arbitrary keyword names."""
    return sum(values) + sum(options.values())


assert_type(collect_values(1, 2, self=3), int)


class NormalMethods:
    """Container for instance method typing probes."""

    @alternative.reference
    def method(self, count: int, label: str) -> str:
        """Return a labelled value repeated a requested number of times."""
        return label * count

    @method.add(default=True)
    def method_default(self, count: int, label: str) -> str:
        """Keep the signature when selecting the default implementation."""
        return label * count

    @method.add
    def method_extra(self, count: int, label: str) -> str:
        """Return an upper-case labelled value repeated a requested number of times."""
        return label.upper() * count


normal_methods = NormalMethods()
assert_type(normal_methods.method(2, "a"), str)
assert_type(normal_methods.method_extra(2, "a"), str)
assert_type(normal_methods.method(count=2, label="a"), str)
assert_type(normal_methods.method_extra(count=2, label="a"), str)
assert_type(NormalMethods.method(self=normal_methods, count=2, label="a"), str)


class DescriptorMethods:
    """Container for classmethod and staticmethod typing probes."""

    @alternative.reference
    @classmethod
    def build(cls, count: int, label: str) -> str:
        """Return a labelled value repeated a requested number of times."""
        return label * count

    @build.add(default=True)
    @classmethod
    def build_default(cls, count: int, label: str) -> str:
        """Type check classmethod registration through a decorator factory."""
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

    @parse.add(default=True)
    @staticmethod
    def parse_default(count: int, label: str) -> str:
        """Type check staticmethod registration through a decorator factory."""
        return label * count

    @parse.add
    @staticmethod
    def parse_extra(count: int, label: str) -> str:
        """Return an upper-case labelled value repeated a requested number of times."""
        return label.upper() * count

    @alternative.reference
    @staticmethod
    def self_keyword(**options: int) -> int:
        """Use a keyword that must not collide with the callable wrapper."""
        return options["self"]

    @self_keyword.add
    @staticmethod
    def self_keyword_extra(**options: int) -> int:
        """Preserve the keyword in a directly callable candidate too."""
        return options["self"]


assert_type(DescriptorMethods.build(2, "a"), str)
assert_type(DescriptorMethods().build(2, "a"), str)
assert_type(DescriptorMethods.build_extra(2, "a"), str)

assert_type(DescriptorMethods.parse(2, "a"), str)
assert_type(DescriptorMethods().parse(2, "a"), str)
assert_type(DescriptorMethods.parse_extra(2, "a"), str)
assert_type(DescriptorMethods.build(count=2, label="a"), str)
assert_type(DescriptorMethods().build(count=2, label="a"), str)
assert_type(DescriptorMethods.build_extra(count=2, label="a"), str)
assert_type(DescriptorMethods.parse(count=2, label="a"), str)
assert_type(DescriptorMethods().parse(count=2, label="a"), str)
assert_type(DescriptorMethods.parse_extra(count=2, label="a"), str)
assert_type(DescriptorMethods.self_keyword(self=1), int)
assert_type(DescriptorMethods().self_keyword(self=1), int)
assert_type(DescriptorMethods.self_keyword_extra(self=1), int)
assert_type(DescriptorMethods().self_keyword_extra(self=1), int)

assert_type(normal_methods.method_default(count=2, label="a"), str)
assert_type(DescriptorMethods.build_default(count=2, label="a"), str)
assert_type(DescriptorMethods.parse_default(count=2, label="a"), str)
