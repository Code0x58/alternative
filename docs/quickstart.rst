Quickstart
==========

.. code-block:: console

   $ pip install "alternative[dev]"

Register Implementations
------------------------

In ``test_names.py``, register a reference with :func:`alternative.reference` and
a candidate with ``.add``:

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

``normalise_name(...)`` calls the reference until another default is selected.
``normalise_name_mapped(...)`` calls the candidate directly.

Test the Contract
-----------------

Append the tests to ``test_names.py``. ``.pytest_parametrize()`` supplies every
implementation, including the reference; ``.pytest_parametrize_pairs()`` pairs
each candidate with the reference:

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

The helpers supply callable ``implementation`` and ``reference`` parameters.
The expected results specify whitespace and apostrophe handling;
``name.title()`` would change those results.

Benchmark Representative Inputs
-------------------------------

The ``benchmark`` fixture times each parametrized implementation:

.. code-block:: python

   @normalise_name.pytest_parametrize()
   def test_name_benchmark(benchmark, implementation):
       """Time each algorithm on the same name."""
       assert benchmark(implementation, "  ada   lovelace  ") == "Ada Lovelace"

.. code-block:: console

   $ pytest test_names.py

These timings exclude dispatch through the alternatives object. See
:doc:`performance` for benchmarking the application entry point.

Choose a Default
----------------

Change the candidate's decorator in ``test_names.py`` to
``@normalise_name.add(default=True)`` for normal calls to use it on the next run.

Only one explicit default can be registered, including an explicitly selected
reference.

Register all candidates before applying test decorators, calling the alternatives
object, reading ``.callable`` or ``.implementations``, or calling ``.measure()``.
Each operation freezes registration, so select the default before them.

Next Steps
----------

See :doc:`tutorial` to split this workflow across application and test files.
Use :doc:`pytest` for helper options and :doc:`testing-contracts` for mutation
and errors. :doc:`methods` covers instance, class, and static methods.
:doc:`workflow` covers direct-call registration, chained registration, and runtime
inspection.
