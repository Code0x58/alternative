An Optimization Workflow
========================

This complete example keeps a reference, candidates, startup imports, correctness
tests, and benchmarks in separate files. Its contract is to sum an iterable of
integers, including empty inputs and large integers, without changing its items.

After :doc:`quickstart`, use this layout when implementations and tests need
separate modules. Create an ``optimise_totals/`` directory containing the four
files below. You can also copy the `example directory from the source repository
<https://github.com/Code0x58/alternative/tree/master/docs/examples/optimise_totals>`_.
Each file is shown below, so a repository checkout is optional.

.. code-block:: text

   optimise_totals/
       __init__.py
       reference.py
       candidates.py
       test_totals.py

Reference and Candidate
-----------------------

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
---------------

The package's ``__init__.py`` imports candidates before exposing the entry point:

.. literalinclude:: examples/optimise_totals/__init__.py
   :language: python

Application code can now use ``from optimise_totals import total``. Importing
the package registers the candidates; import alone does not freeze registration.
Applying a pytest helper or calling ``total`` freezes the set, so all candidate
imports must happen first. Adding an implementation after either operation
raises :class:`alternative.AddTooLateError`. Reading ``.callable`` or
``.implementations`` and calling ``.measure()`` also freeze registration.

Test the Contract and Measure the Result
----------------------------------------

``test_totals.py`` checks independent expected results as well as equivalence.
Separate benchmark tests measure algorithms and the production entry point:

.. literalinclude:: examples/optimise_totals/test_totals.py
   :language: python

From the directory containing ``optimise_totals/``, install the library and test
tools, then run the tests:

.. code-block:: console

   $ pip install alternative pytest pytest-benchmark
   $ pytest optimise_totals

To promote a different candidate, move ``default=True`` to its registration in
source and rerun a fresh process. Collection and measurement already freeze the
current registry; they do not change its default. See :doc:`performance` for
dispatch costs and :doc:`testing-contracts` for mutations and errors.
