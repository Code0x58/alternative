An Optimization Workflow
==========================

This complete example keeps a reference, candidates, startup imports, correctness
tests, and benchmarks in separate files. Its contract is to sum an iterable of
integers, including empty inputs and large integers, without changing its items.

Copy ``docs/examples/optimise_totals/`` from the checkout into your project.
The example is included in source distributions, and its tests run in the
project's normal pytest suite.

Reference and Candidate
-------------------------

``reference.py`` contains the implementation that remains the correctness oracle:

.. literalinclude:: examples/optimise_totals/reference.py
   :language: python

``candidates.py`` registers the rewrite and selects it as the default:

.. literalinclude:: examples/optimise_totals/candidates.py
   :language: python

Choose ``default=True`` after testing representative inputs and reviewing the
benchmark results for your environment. It is shown here to demonstrate the final
configuration, rather than assert a universal speed advantage for every input.

Startup Imports
-----------------

The package's ``__init__.py`` imports candidates before exposing the entry point:

.. literalinclude:: examples/optimise_totals/__init__.py
   :language: python

Application code can now use ``from optimise_totals import total``. Import the
package before test collection or application startup invokes ``total``. An
implementation imported after that point raises ``AddTooLateError`` instead of
silently escaping the already collected tests.

Test the Contract and Measure the Result
------------------------------------------

``test_totals.py`` checks independent expected results as well as equivalence.
Separate benchmark tests measure algorithms and the production entry point:

.. literalinclude:: examples/optimise_totals/test_totals.py
   :language: python

From this repository, run the example with:

.. code-block:: console

   $ uv run --dev pytest docs/examples/optimise_totals --verbosity=2

For an independent project, install ``alternative``, ``pytest``, and
``pytest-benchmark``, then run ``pytest optimise_totals``.

To promote a different candidate, move ``default=True`` to its registration in
source and rerun a fresh process. Collection and measurement already freeze the
current registry; they do not change its default. See :doc:`performance` for
dispatch costs and :doc:`testing-contracts` for mutations and errors.
