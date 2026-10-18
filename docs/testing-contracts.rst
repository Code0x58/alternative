Testing Observable Behavior
=============================

Equivalence is the contract your tests define. Besides return values, consider
exceptions, input mutation, receiver state, ordering, and numerical tolerances.
Use independent expected results to check the reference itself, as in
:doc:`tutorial`; agreement alone does not prove either implementation correct.

Fresh Inputs for Mutating Functions
-------------------------------------

Both implementations receive the same argument objects if you pass them the
same objects. Neither pytest parametrization nor ``measure()`` copies inputs.
Create independent inputs and compare the resulting state as well as the return
values. Use fresh instances for stateful methods, and fresh iterators for
single-use iterable inputs.

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


   left, right = [3, 1, 2], [3, 1, 2]
   assert sort_values.reference(left) is sort_values_copy(right) is None
   assert left == right == [1, 2, 3]

For nested mutable inputs, construct independent nested data or copy it to the
depth required by the contract. Reference caching is disabled in this example;
caching mutable results can cause one test case to change another case's oracle.

Exceptions Are Part of the Contract
-------------------------------------

Check success and failure cases separately. Compare exception classes and only
compare messages when the API promises their exact wording:

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


   for function in (parse_decimal.reference, parse_decimal_explicit):
       with pytest.raises(ValueError):
           function("not a number")

Numerical Comparisons
-----------------------

Choose absolute and relative tolerances from the application's error budget and
input domain, then compare using ``pytest.approx``. Decide explicitly how to
handle NaN, infinity, overflow, signed zero, and empty inputs. A tolerance should
not hide a semantic difference such as changed ordering, precision, or exception
behavior. Include cancellation and extreme-value cases relevant to the domain.

Different but Valid Outputs
-----------------------------

Some algorithms produce different representations of an equivalent result.
Check their meaning or invariants separately from cost. For compression, compare
decoded bytes with the original input, then use ``measure(len, data)`` to compare
compressed sizes. For query plans or circuits, validate the result before
measuring estimated cost, depth, or gate count. ``measure()`` orders scores; it
does not establish semantic validity or automatically select a default.
