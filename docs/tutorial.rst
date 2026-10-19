An Optimization Workflow
========================

The ``optimise_totals`` example sums integer iterables without changing their
items. It separates the reference, candidates, startup imports, and tests:

.. code-block:: text

   optimise_totals/
       __init__.py
       reference.py
       candidates.py
       test_totals.py

The `example directory
<https://github.com/Code0x58/alternative/tree/master/docs/examples/optimise_totals>`_
contains all four files.

Reference and Candidate
-----------------------

.. literalinclude:: examples/optimise_totals/reference.py
   :language: python
   :caption: optimise_totals/reference.py

.. literalinclude:: examples/optimise_totals/candidates.py
   :language: python
   :caption: optimise_totals/candidates.py

``default=True`` selects the candidate for application calls; the reference
remains available for equivalence tests.

Startup Imports
---------------

Import candidates before exposing the entry point:

.. literalinclude:: examples/optimise_totals/__init__.py
   :language: python
   :caption: optimise_totals/__init__.py

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
   :caption: optimise_totals/test_totals.py

From the parent directory of ``optimise_totals/``:

.. code-block:: console

   $ pip install "alternative[dev]"
   $ pytest optimise_totals/test_totals.py

To promote a different candidate, move ``default=True`` to its registration in
source and start a fresh process. See :doc:`performance` for dispatch costs and
:doc:`testing-contracts` for mutations and errors.
