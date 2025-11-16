[![PyPi Package](https://badge.fury.io/py/alternative.svg)](https://pypi.org/project/alternative/) [![Build Status](https://github.com/Code0x58/alternative/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/Code0x58/alternative/actions/workflows/ci.yml) [![Coverage Report](https://codecov.io/gh/Code0x58/alternative/branch/master/graph/badge.svg)](https://codecov.io/gh/Code0x58/alternative)

This is a library to help with the management of alternative implementations of functions, as you may have when
optimising.

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


# the reference implementation is substituted with the default implementation - if no default was specified, the reference would have been used
assert constant_number() == 2
# alternative implementations still act like themselves
assert unused_alternative_constant_number() == 3

# TODO: mash in measure + benchmark + equality tests from examples
```

The library tries to avoid unpleasant surprises that may come from import orders or maintenance issues:
 * the implementation that is used cannot be changed once it has been used
 * implementations cannot be added once they have been inspected: reduces the changes of tests only covering a subset of 

Running with `ALTERNATIVE_DEBUG=1` as an environment variable will result in the library recording which lines were
responsible for critical state changes like the point that a default implementation was selected or the implementations
were inspected. These are then used in error messages which can be used to resolve stateful issues.

For how this can tie in with equivalence checks and benchmarking in pytest, see the examples directory.