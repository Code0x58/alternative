[![PyPi Package](https://badge.fury.io/py/alternative.svg)](https://pypi.org/project/alternative/) [![Build Status](https://github.com/Code0x58/alternative/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Code0x58/alternative/actions/workflows/ci.yml) [![Coverage Report](https://codecov.io/gh/Code0x58/alternative/branch/master/graph/badge.svg)](https://codecov.io/gh/Code0x58/alternative) [![Documentation Status](https://readthedocs.org/projects/alternative/badge/?version=latest)](https://alternative.readthedocs.io/en/latest/?badge=latest)

# alternative

Keep a trusted Python implementation alongside candidate rewrites, test them with pytest, and choose which one normal callers use. `alternative` supports functions and methods, preserves their type signatures, and has no runtime dependencies. It requires Python 3.10 or newer.

Use it when optimizing an existing function or comparing algorithms with the same public contract. You provide the correctness tests and benchmarks; the library registers implementations and keeps the selected default stable.

## Install

```console
pip install alternative pytest pytest-benchmark
```

Only `alternative` is needed at runtime. The other packages provide the testing and timing tools used below.

## Register and call implementations

```python
import alternative


@alternative.reference
def total(values: list[int]) -> int:
    """Keep a straightforward implementation as the reference."""
    result = 0
    for value in values:
        result += value
    return result


@total.add
def total_builtin(values: list[int]) -> int:
    """Register a candidate with the same contract."""
    return sum(values)


assert total([1, 2, 3]) == 6
assert total_builtin([1, 2, 3]) == 6
```

`total(...)` uses the reference until you select an explicit default. `total_builtin(...)` always calls that candidate directly.

## Test and benchmark

In the same file, or in a test module that imports `total`, add:

```python
import pytest


@total.pytest_parametrize()
@pytest.mark.parametrize(("values", "expected"), [([], 0), ([1, -2, 3], 2)])
def test_expected_totals(implementation, values, expected):
    """Check every implementation against independent expected results."""
    assert implementation(values) == expected


@total.pytest_parametrize_pairs()
def test_equivalent_totals(reference, implementation):
    """Compare each candidate with the reference."""
    values = [1, 2, 3]
    assert implementation(values) == reference(values)


@total.pytest_parametrize()
def test_total_benchmark(benchmark, implementation):
    """Time each implementation on the same input."""
    assert benchmark(implementation, list(range(1_000))) == 499_500
```

Save the combined example as `test_totals.py` and run `pytest test_totals.py`. The helpers supply `implementation` and `reference`; they are callable test parameters, not fixtures you need to write.

After checking correctness and measuring representative inputs, edit the candidate registration to `@total.add(default=True)` and run a fresh process. Normal calls to `total(...)` will then use that candidate. The library does not choose a winner automatically.

Register every candidate before calling the alternatives object or applying a pytest helper. Those operations freeze registration, as do reading `.callable` or `.implementations` and calling `.measure(...)`. This prevents collected tests from silently missing later imports. Set `ALTERNATIVE_DEBUG=1` to include the earlier registration or inspection location in relevant errors.

## Next steps

- [Quickstart](https://alternative.readthedocs.io/en/latest/quickstart.html): register, test, benchmark, and select a default.
- [Complete workflow](https://alternative.readthedocs.io/en/latest/tutorial.html): separate implementation, startup, and test files.
- [Potential applications](https://alternative.readthedocs.io/en/latest/applications.html): algebraic matrix optimisation and evolving quantum circuits.
- [Pytest integration](https://alternative.readthedocs.io/en/latest/pytest.html) and [testing contracts](https://alternative.readthedocs.io/en/latest/testing-contracts.html): expected results, mutation, exceptions, async tests, and reference caching.
- [Methods](https://alternative.readthedocs.io/en/latest/methods.html): instance, class, and static methods and decorator order.
- [Runtime workflow](https://alternative.readthedocs.io/en/latest/workflow.html): registration rules, debugging, and scoring returned results with `.measure(...)`.
- [Performance and when to use it](https://alternative.readthedocs.io/en/latest/performance.html): rough overhead budgets and timing the production call path.
- [API and IDE compatibility](https://alternative.readthedocs.io/en/latest/api.html) and [contributing](https://alternative.readthedocs.io/en/latest/contributing.html).
