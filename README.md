[![PyPi Package](https://badge.fury.io/py/alternative.svg)](https://pypi.org/project/alternative/) [![Build Status](https://github.com/Code0x58/alternative/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Code0x58/alternative/actions/workflows/ci.yml) [![Coverage Report](https://codecov.io/gh/Code0x58/alternative/branch/master/graph/badge.svg)](https://codecov.io/gh/Code0x58/alternative)

# alternative

A tiny, dependency-free library for managing multiple implementations of the same function — especially when you're iterating toward faster or cleaner versions and want those choices to stay explicit, testable, and safe.

## Why use this?

When optimizing a hot path, it’s common to accumulate:

- a trusted reference implementation
- one or more candidate rewrites
- tests to keep them equivalent
- benchmarks to validate wins

`alternative` keeps that workflow tidy by making implementation registration and selection first-class.

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

## Pytest features

The examples directory includes practical pytest patterns that make this library shine.

### Pairwise equivalence checks

Use `pytest_parametrize_pairs(...)` to compare the reference against each candidate implementation.

- Basic pairwise checks: [`examples/test_measure.py`](examples/test_measure.py)
- More configurable pairwise checks: [`examples/test_equivalence.py`](examples/test_equivalence.py)

### Single-implementation parametrization

Use `pytest_parametrize(...)` to run one test body across all implementations.

- Great for benchmark workflows with [`pytest-benchmark`](https://pypi.org/project/pytest-benchmark/): [`examples/test_benchmark.py`](examples/test_benchmark.py)
- Useful for validating that every implementation passes one shared test suite

## Safety guarantees

The library tries to avoid unpleasant surprises caused by import order or accidental state changes:

- The selected implementation cannot be changed once it has been used.
- Implementations cannot be added once they have been inspected, reducing the chance that tests only covered a subset.

## Debug mode

Set `ALTERNATIVE_DEBUG=1` to record where critical state changes happened (like selecting defaults or inspecting implementations). These locations are surfaced in error messages to make stateful issues easier to track down.

When debug mode is enabled, each `Implementation` also captures a label with its registration call-site. This label appears in `repr(...)` and selected debug errors, making it easier to disambiguate implementation instances.
