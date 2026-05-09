Pytest Integration
==================

The pytest helpers are the main reason to register implementations explicitly.
They let one test body cover every implementation without hand-maintained
parametrize lists.

Equivalence Tests
-----------------

Use :meth:`alternative.Alternatives.pytest_parametrize_pairs` when each
candidate implementation should match the reference:

.. code-block:: python

   import alternative


   @alternative.reference
   def total_loop(values: list[int]) -> int:
       result = 0
       for value in values:
           result += value
       return result


   @total_loop.add(default=True)
   def total_sum(values: list[int]) -> int:
       return sum(values)


   @total_loop.pytest_parametrize_pairs()
   def test_totals_are_equivalent(reference, implementation):
       """Every implementation returns the same total as the reference."""
       values = [1, 2, 3]
       assert implementation(values) == reference(values)

The helper parametrizes ``reference`` with a cached wrapper around the reference
implementation and parametrizes ``implementation`` with each candidate.

Reference Caching
-----------------

The ``n_cache`` argument is passed to :func:`functools.lru_cache` for the
reference callable used in pairwise tests:

.. code-block:: python

   @total_loop.pytest_parametrize_pairs(n_cache=None)
   def test_with_unbounded_reference_cache(reference, implementation):
       """The reference result may be reused across implementations."""
       assert implementation((1, 2, 3)) == reference((1, 2, 3))

Use ``n_cache=0`` when you do not want effective caching. Use ``None`` for an
unbounded cache when the reference is expensive and arguments are hashable.

Only the Default Implementation
-------------------------------

Set ``only_default=True`` to limit parametrization to the reference and selected
default implementation:

.. code-block:: python

   @total_loop.pytest_parametrize(only_default=True)
   def test_selected_implementation_accepts_input(implementation):
       """The reference and default implementation both accept list input."""
       assert implementation([1, 2, 3]) == 6

This is useful for expensive test suites where exhaustive coverage happens in a
smaller equivalence test.

Benchmark All Implementations
-----------------------------

Use :meth:`alternative.Alternatives.pytest_parametrize` with
``pytest-benchmark`` to benchmark every implementation:

.. code-block:: python

   @total_loop.pytest_parametrize()
   def test_total_benchmark(benchmark, implementation):
       """Benchmark each registered implementation."""
       assert benchmark(implementation, [1, 2, 3]) == 6

Pytest generates readable parameter names from the underlying function names.

Collection Order
----------------

Register implementations before tests inspect the alternatives set. Once
``.implementations`` is read, further additions raise
:class:`alternative.AddTooLateError`.

That rule is deliberate. It prevents a test module from collecting a partial
implementation list and then silently missing an implementation imported later.
