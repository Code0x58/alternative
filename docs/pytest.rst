Pytest Integration
==================

Use the pytest helpers to run one test body across registered implementations.
This guide builds on :doc:`quickstart` and assumes you know basic pytest tests
and parametrization. Install the tools used in the synchronous examples with:

.. code-block:: console

   $ pip install alternative pytest pytest-benchmark

The code blocks below can be combined in a single test file. Register every
candidate before applying a helper to a test function.

Equivalence Tests
-----------------

Use :meth:`alternative.Alternatives.pytest_parametrize_pairs` when each
candidate implementation should match the reference:

.. code-block:: python

   from collections.abc import Iterable

   import alternative
   import pytest


   @alternative.reference
   def total_loop(values: Iterable[int]) -> int:
       """Sum integers with a straightforward reference loop."""
       result = 0
       for value in values:
           result += value
       return result


   @total_loop.add(default=True)
   def total_sum(values: Iterable[int]) -> int:
       """Apply the same contract with the built-in sum."""
       return sum(values)


   @total_loop.pytest_parametrize_pairs()
   def test_totals_are_equivalent(reference, implementation):
       """Every implementation returns the same total as the reference."""
       values = [1, 2, 3]
       assert implementation(values) == reference(values)

The helper supplies the callable arguments named ``reference`` and
``implementation``; do not define fixtures for them. ``reference`` calls the
reference implementation, and ``implementation`` takes each candidate in turn.
Reference caching is disabled by default.

The reference is not paired with itself unless you set ``double_reference=True``
to check the test's own assumptions. With no candidates, ordinary pairwise
parametrization has no cases. Keep independent expected-result tests for the
reference as well as equivalence tests.

Check Expected Results
----------------------

Use :meth:`alternative.Alternatives.pytest_parametrize` to run against every
implementation, including the reference:

.. code-block:: python

   @total_loop.pytest_parametrize()
   @pytest.mark.parametrize(("values", "expected"), [((), 0), ((1, -2, 3), 2)])
   def test_expected_totals(implementation, values, expected):
       """Check all implementations against independent expected results."""
       assert implementation(values) == expected

This checks the reference itself, which pairwise agreement alone cannot do.

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

If the reference is also the selected default, it appears only once, whether
selected implicitly or with ``@alternative.reference(default=True)``. Pairwise
``only_default=True`` similarly compares the reference with itself once;
``double_reference=True`` does not duplicate that pair.

.. _testing-methods:

Testing Methods
---------------

Method alternatives can be tested with the same helpers by passing an explicit
instance to the parametrized implementation:

.. code-block:: python

   class Counter:
       def __init__(self, value: int):
           """Store the integer used by the method examples."""
           self.value = value

       @alternative.reference
       def total(self) -> int:
           """Return the integer through a text round trip."""
           return int(str(self.value))

       @total.add(default=True)
       def total_direct(self) -> int:
           """Return the stored integer directly."""
           return self.value


   @Counter.total.pytest_parametrize_pairs()
   def test_method_totals_are_equivalent(reference, implementation):
       """Every method implementation returns the same total."""
       counter = Counter(3)
       assert implementation(counter) == reference(counter)

The pytest helpers parametrize callables. They do not change the selected
default implementation for each test parameter; the library still keeps the
active implementation stable once it has been used.

For class methods, access the helper through the class. The parameters bind to
that class, including when accessed through a subclass:

.. code-block:: python

   class Factory:
       marker = "base"

       @alternative.reference
       @classmethod
       def build(cls, value: str) -> str:
           """Prefix the text with the accessed class marker."""
           return cls.marker + ":" + value

       @build.add
       @classmethod
       def build_extra(cls, value: str) -> str:
           """Format the same marker and text with an f-string."""
           return f"{cls.marker}:{value}"


   @Factory.build.pytest_parametrize_pairs()
   def test_factories_are_equivalent(reference, implementation):
       """Class method parameters already have their class receiver."""
       assert reference("a") == implementation("a") == "base:a"

Helpers accessed through an instance also bind instance methods to that
instance. When a helper is used on a raw descriptor inside a class body, pass
the receiver explicitly, as for the unbound instance-method example above.

.. _async-tests:

Async Tests
-----------

The helpers preserve ``async def`` tests for async pytest plugins. For
``pytest-asyncio``, install the plugin and mark each async test:

.. code-block:: console

   $ pip install pytest-asyncio

.. code-block:: python

   @alternative.reference
   async def normalise_async(text: str) -> str:
       """Return normalized text from an async callable."""
       return text.strip().lower()


   @normalise_async.add
   async def normalise_async_lower(text: str) -> str:
       """Apply the same text contract with a direct str call."""
       return str.lower(text.strip())


   @pytest.mark.asyncio
   @normalise_async.pytest_parametrize_pairs()
   async def test_async_names(reference, implementation):
       """Await both implementations before comparing their results."""
       assert await reference(" Ada ") == await implementation(" Ada ") == "ada"

``@pytest.mark.asyncio`` can appear in either order relative to either helper.
Leave reference caching disabled. Ordinary runtime calls also return awaitables
for asynchronous implementations; the library does not run an event loop on the
caller's behalf.

Reference Caching
-----------------

Use ``n_cache`` to reuse reference results across pairwise comparisons when the
reference is expensive and its results are safe to share:

.. code-block:: python

   @total_loop.pytest_parametrize_pairs(n_cache=None)
   def test_with_unbounded_reference_cache(reference, implementation):
       """The reference result may be reused across implementations."""
       assert implementation((1, 2, 3)) == reference((1, 2, 3))

The default, ``n_cache=0``, disables caching. Use a positive integer for a bounded
cache, or ``None`` for an unbounded cache, when the reference is expensive and
arguments are hashable.

Caching coroutine, generator, or async-generator reference functions raises
``ValueError`` during test decoration. Keep ``n_cache=0`` for these functions so
each call creates a fresh awaitable or iterator. Callable instances with an
asynchronous or generator ``__call__`` follow the same rule. For synchronous
factories, only enable caching when their results can safely be reused.

The cache belongs to the decorated test and can reuse results across input cases
and candidate parameters. Arguments must be hashable, and the reference must be
safe to call fewer times. Cached mutable results are shared objects: changing
one can contaminate later comparisons. Use ``n_cache=0`` for mutation, state,
randomness, or single-use input. See :doc:`testing-contracts` for examples.

Collection Order
----------------

Applying a helper to a test function snapshots the implementation list and
freezes registration. This normally happens while pytest imports the test module,
before test execution. Import all candidates before these decorators run.
Reading ``.implementations`` or ``.callable``, calling the alternatives object,
or calling ``.measure()`` also freezes registration. Further additions raise
:class:`alternative.AddTooLateError`.

That rule is deliberate. It prevents a test module from collecting a partial
implementation list and then silently missing an implementation imported later.
