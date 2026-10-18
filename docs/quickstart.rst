Quickstart
==========

This guide assumes you know Python decorators and basic pytest tests. It uses a
name-formatting function to show the full cycle: register a candidate, check its
contract, benchmark it, and select the default used by application code.

Install the library and test tools:

.. code-block:: console

   $ pip install alternative pytest pytest-benchmark

Register Implementations
------------------------

Save the following in ``test_names.py``. Use :func:`alternative.reference` on the
implementation you trust most, then register a candidate with ``.add``:

.. code-block:: python

   import alternative
   import pytest


   @alternative.reference
   def normalise_name(name: str) -> str:
       """Collapse whitespace and capitalize each word."""
       return " ".join(part.capitalize() for part in name.split())


   @normalise_name.add
   def normalise_name_mapped(name: str) -> str:
       """Apply the same word transformation with map."""
       return " ".join(map(str.capitalize, name.split()))

``normalise_name`` is an :class:`alternative.Alternatives` object. Calling it
uses the reference unless you select another default. ``normalise_name_mapped``
is an :class:`alternative.Implementation` object; calling it always runs that
candidate directly. Both retain their Python call signatures.

Test the Contract
-----------------

Add expected results to check every implementation, including the reference.
Then compare candidates against the reference on the same inputs:

.. code-block:: python

   CASES = [
       ("", ""),
       ("  ada   lovelace  ", "Ada Lovelace"),
       ("o'neill", "O'neill"),
       ("élise müller", "Élise Müller"),
   ]


   @normalise_name.pytest_parametrize()
   @pytest.mark.parametrize(("value", "expected"), CASES)
   def test_expected_names(implementation, value, expected):
       """Check independent expected results for every implementation."""
       assert implementation(value) == expected


   @normalise_name.pytest_parametrize_pairs()
   @pytest.mark.parametrize(("value", "expected"), CASES)
   def test_equivalent_names(reference, implementation, value, expected):
       """Compare each candidate with the reference."""
       assert implementation(value) == reference(value)

The helpers supply the callable parameters named ``implementation`` and
``reference``. You do not need to define fixtures with these names. Run the tests:

.. code-block:: console

   $ pytest test_names.py

The contract here includes whitespace normalization and apostrophe handling.
Using ``name.title()`` would change those rules. Agreement with the reference
also needs independent expected results: two implementations can share a bug.

Benchmark Representative Inputs
-------------------------------

Add a benchmark using the ``benchmark`` fixture from ``pytest-benchmark``:

.. code-block:: python

   @normalise_name.pytest_parametrize()
   def test_name_benchmark(benchmark, implementation):
       """Time each algorithm on the same name."""
       assert benchmark(implementation, "  ada   lovelace  ") == "Ada Lovelace"

Run ``pytest test_names.py`` again to see timing results for both implementations.
Try inputs representative of your application before deciding that a candidate
is faster. The helper times underlying implementations; also time the decorated
entry point to account for dispatch cost, as shown in :doc:`tutorial` and
:doc:`performance`.

Choose a Default
----------------

After reviewing correctness and timing results, edit the candidate's decorator
in ``test_names.py`` to ``@normalise_name.add(default=True)`` and run a fresh
process. Calls such as ``normalise_name("ada lovelace")`` will then use that
candidate. Direct calls to ``normalise_name_mapped`` still use the candidate.

Only one explicit default can be registered, including an explicitly selected
reference. The library does not choose the fastest implementation automatically.

Register all candidates before applying test decorators, calling the alternatives
object, reading ``.callable`` or ``.implementations``, or calling ``.measure()``.
Each operation freezes registration. Choosing the default is a source change
made before those operations in the next run, rather than an update to the
already tested alternatives object.

Use Methods
-----------

The same workflow supports instance, class, and static methods. See :doc:`methods`
for decorator order, receiver binding, and imported static candidates.

Next Steps
----------

See :doc:`tutorial` to split this workflow across application and test files.
Use :doc:`pytest` for helper options and :doc:`testing-contracts` for mutation
and errors.
:doc:`workflow` covers direct-call registration, chained registration, and runtime
inspection.
