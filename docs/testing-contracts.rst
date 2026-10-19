Testing Observable Behavior
===========================

Equivalence can include exceptions, input mutation, receiver state, ordering,
and numerical tolerances.

Fresh Inputs for Mutating Functions
-----------------------------------

Neither parametrization nor ``measure()`` copies inputs. Use independent inputs
when comparing mutating implementations, fresh instances for stateful methods,
and fresh iterators for single-use inputs.

.. code-block:: python

   import alternative


   @alternative.reference
   def sort_values(values: list[int]) -> None:
       """Sort the provided list in place."""
       values.sort()


   @sort_values.add
   def sort_values_copy(values: list[int]) -> None:
       """Replace its contents with a sorted copy."""
       values[:] = sorted(values)


   @sort_values.pytest_parametrize_pairs()
   def test_sort_state(reference, implementation):
       """Compare independently initialized mutable inputs."""
       left, right = [3, 1, 2], [3, 1, 2]
       assert reference(left) is implementation(right) is None
       assert left == right == [1, 2, 3]


.. invisible-code-block: python

   left, right = [3, 1, 2], [3, 1, 2]
   assert sort_values.reference(left) is sort_values_copy(right) is None
   assert left == right == [1, 2, 3]

For nested mutable inputs, construct independent nested data or copy it to the
depth required by the contract. Reference caching is disabled in this example;
caching mutable results can cause one test case to change another case's oracle.

Exceptions Are Part of the Contract
-----------------------------------

Compare exception classes, and compare messages only when their wording is part
of the API contract:

.. code-block:: python

   import pytest


   @alternative.reference
   def parse_decimal(value: str) -> int:
       """Parse a stripped decimal integer or raise ValueError."""
       return int(value.strip())


   @parse_decimal.add
   def parse_decimal_explicit(value: str) -> int:
       """Use an explicit decimal base with the same failure contract."""
       return int(value.strip(), 10)


   @parse_decimal.pytest_parametrize_pairs()
   def test_parser_errors(reference, implementation):
       """Both implementations reject invalid decimal input."""
       for function in (reference, implementation):
           with pytest.raises(ValueError):
               function("not a number")


.. invisible-code-block: python

   for function in (parse_decimal.reference, parse_decimal_explicit):
       with pytest.raises(ValueError):
           function("not a number")

Numerical Comparisons
---------------------

Choose ``pytest.approx`` tolerances from your application's error budget.
Cover boundary values relevant to its domain, including cancellation, overflow,
NaN, infinity, signed zero, and empty inputs.

For example, these vector-length implementations use different floating-point
operations. The test chooses a relative tolerance of ``1e-12`` and an absolute
tolerance of ``1e-15`` for small, finite vectors:

.. code-block:: python

   import math


   @alternative.reference
   def vector_length(values: tuple[float, ...]) -> float:
       """Calculate length by squaring and summing components."""
       return math.sqrt(sum(value * value for value in values))


   @vector_length.add
   def vector_length_hypot(values: tuple[float, ...]) -> float:
       """Use hypot for the same vector-length contract."""
       return math.hypot(*values)


   @vector_length.pytest_parametrize_pairs()
   @pytest.mark.parametrize(
       ("values", "expected"), [((), 0.0), ((3.0, 4.0), 5.0), ((0.3, 0.4), 0.5)]
   )
   def test_vector_lengths(reference, implementation, values, expected):
       """Check expected lengths and compare within the chosen error budget."""
       reference_result = reference(values)
       assert reference_result == pytest.approx(expected, rel=1e-12, abs=1e-15)
       assert implementation(values) == pytest.approx(
           reference_result, rel=1e-12, abs=1e-15
       )

Squaring can overflow for large components where ``hypot`` remains finite.
If such inputs are supported, extend the contract and tests accordingly.

Different but Valid Outputs
---------------------------

Some algorithms produce different representations of an equivalent result.
Check their meaning or invariants separately from cost. For compression, compare
decoded bytes with the original input, then use ``measure(len, data)`` to compare
compressed sizes. For query plans or circuits, validate the result before
measuring estimated cost, depth, or gate count. ``measure()`` orders scores; it
does not establish semantic validity or automatically select a default.

The compression example in :ref:`measure-implementations` demonstrates validation
before scoring. Use separate benchmarks when elapsed time is also part of the
tradeoff.
