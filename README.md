[![PyPi Package](https://badge.fury.io/py/alternative.svg)](https://pypi.org/project/alternative/) [![Build Status](https://github.com/Code0x58/alternative/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Code0x58/alternative/actions/workflows/ci.yml) [![Coverage Report](https://codecov.io/gh/Code0x58/alternative/branch/master/graph/badge.svg)](https://codecov.io/gh/Code0x58/alternative) [![Documentation Status](https://readthedocs.org/projects/alternative/badge/?version=latest)](https://alternative.readthedocs.io/en/latest/?badge=latest)

# alternative

A tiny, dependency-free library for managing multiple implementations of the same function — especially when you're iterating toward faster or cleaner versions and want those choices to stay explicit, testable, and safe.

Full documentation is available on [Read the Docs](https://alternative.readthedocs.io/en/latest/). The documentation source lives in [`docs/`](docs/).

## Why use this?

When optimizing a hot path, it’s common to accumulate:

- a trusted reference implementation
- one or more candidate rewrites
- tests to keep them equivalent
- benchmarks to validate wins

`alternative` keeps that workflow tidy by making implementation registration and selection first-class.

The same model works for module functions, instance methods, class methods, and static methods. Public typing is shipped in [`alternative.pyi`](alternative.pyi), so type checkers and IDEs can see the original call signatures instead of losing them behind the decorator objects.

## Quick example

```python
import alternative


@alternative.reference
def constant_number():
    return 1


@constant_number.add(default=True)
def alternative_constant_number():
    return 2


@constant_number.add
def unused_alternative_constant_number():
    return 3


# the default=True implementation is used if specified;
# otherwise, the reference is the implicit default
assert constant_number() == 2
# alternative implementations still act like themselves
assert unused_alternative_constant_number() == 3
```

See the [quickstart](https://alternative.readthedocs.io/en/latest/quickstart.html) for registration patterns, defaults, and method examples.

## Methods and descriptors

Decorate instance methods directly. For `@classmethod` and `@staticmethod`, put `@alternative.reference` and `.add(...)` outside the built-in descriptor decorator:

```python
import alternative


class Parser:
    def __init__(self, value: str = ""):
        self.value = value

    @alternative.reference
    def parse(self, value: str) -> int:
        return int(value.strip())

    @parse.add(default=True)
    def parse_fast(self, value: str) -> int:
        return int(value)

    @alternative.reference
    @classmethod
    def from_text(cls, value: str) -> "Parser":
        return cls(value.strip())

    @from_text.add(default=True)
    @classmethod
    def from_text_fast(cls, value: str) -> "Parser":
        return cls(value)

    @alternative.reference
    @staticmethod
    def is_valid(value: str) -> bool:
        return value.strip().isdigit()

    @is_valid.add(default=True)
    @staticmethod
    def is_valid_fast(value: str) -> bool:
        return value.isdigit()
```

Calling through an instance or class follows normal Python binding rules, and direct implementation calls bind the same way. The full descriptor examples are in [Use Methods](https://alternative.readthedocs.io/en/latest/quickstart.html#use-methods) and [Testing Methods](https://alternative.readthedocs.io/en/latest/pytest.html#testing-methods).

## Pytest features

The pytest helpers are documented in the [pytest integration guide](https://alternative.readthedocs.io/en/latest/pytest.html).

### Pairwise equivalence checks

Use `pytest_parametrize_pairs(...)` to compare the reference against each candidate implementation.

- [Equivalence Tests](https://alternative.readthedocs.io/en/latest/pytest.html#equivalence-tests)
- [Reference Caching](https://alternative.readthedocs.io/en/latest/pytest.html#reference-caching)

### Single-implementation parametrization

Use `pytest_parametrize(...)` to run one test body across all implementations.

- [Only the Default Implementation](https://alternative.readthedocs.io/en/latest/pytest.html#only-the-default-implementation)
- [Benchmark All Implementations](https://alternative.readthedocs.io/en/latest/pytest.html#benchmark-all-implementations) with [`pytest-benchmark`](https://pypi.org/project/pytest-benchmark/)

## Runtime tools

`Alternatives.measure(...)` runs every implementation with the same arguments and measures the results with a callable you provide. See [Measure Implementations](https://alternative.readthedocs.io/en/latest/workflow.html#measure-implementations).

## Safety guarantees

The library tries to avoid unpleasant surprises caused by import order or accidental state changes:

- The selected implementation cannot be changed once it has been used.
- Implementations cannot be added once they have been inspected, reducing the chance that tests only covered a subset.

## Debug mode

Set `ALTERNATIVE_DEBUG=1` to record where critical state changes happened (like selecting defaults or inspecting implementations). These locations are surfaced in error messages to make stateful issues easier to track down.

When debug mode is enabled, each `Implementation` also captures a label with its registration call-site. This label appears in `repr(...)` and selected debug errors, making it easier to disambiguate implementation instances.

## Typing and IDEs

`alternative` ships a top-level stub file, [`alternative.pyi`](alternative.pyi), for the public typing surface. It includes overloads for descriptor binding, transparent method/classmethod/staticmethod decoration, and the pytest helpers, while [`alternative.py`](alternative.py) stays focused on runtime behavior.

The typing probes are checked with mypy, pyright, pyrefly, and a headless PyCharm inspection script: [`scripts/pycharm-type-probes.sh`](scripts/pycharm-type-probes.sh). The PyCharm probe covers type assertions, unresolved references, and type checker warnings in [`typing_tests/type_probes.py`](typing_tests/type_probes.py).

Known PyCharm caveat: JetBrains `PyNestedDecoratorsInspection` currently reports a false-positive for correctly typed decorators stacked outside `@classmethod` or `@staticmethod`. Runtime behavior and type resolution are correct, and the project does not require `# noinspection PyTypeChecker` call-site suppressions for these examples.
