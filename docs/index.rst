alternative
===========

``alternative`` is a dependency-free Python library for managing multiple
implementations of the same function.

It is designed for a common optimisation workflow:

* keep a trusted reference implementation;
* register faster, clearer, or more specialised candidate implementations;
* run equivalence tests across every implementation;
* select the implementation that normal callers should use.

The library keeps those choices explicit. The selected implementation cannot be
changed after it has been used, and the implementation list cannot be extended
after it has been inspected by test helpers.

Install
-------

.. code-block:: console

   $ pip install alternative

``alternative`` supports Python 3.10 and newer.

The runtime has no dependencies. Install ``pytest`` to use the test helpers
and ``pytest-benchmark`` for the benchmark fixture:

.. code-block:: console

   $ pip install alternative pytest pytest-benchmark

For async tests, also install ``pytest-asyncio`` or another async pytest plugin;
see :ref:`async-tests`.

Decorated functions retain their typed call signatures and return types, so
callers keep normal type checking and code completion while you register and
select implementations. No extra typing configuration is needed.

A First Example
---------------

.. code-block:: python

   import alternative


   @alternative.reference
   def total(values: list[int]) -> int:
       """Sum integers with a straightforward reference loop."""
       result = 0
       for value in values:
           result += value
       return result


   @total.add(default=True)
   def total_builtin(values: list[int]) -> int:
       """Use the built-in sum with the same integer contract."""
       return sum(values)


   assert total([1, 2, 3]) == 6
   assert total_builtin([1, 2, 3]) == 6

Calling ``total`` uses the selected default implementation. Calling
``total_builtin`` directly still calls that implementation by itself, which is
useful in tests and benchmarks. This shows a selected default; choose it after
checking correctness and measuring representative inputs.

Start with :doc:`quickstart` to add tests and benchmarks. If your implementations
live in separate modules, follow :doc:`tutorial` for startup imports and a
complete runnable package.

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Start Here

   quickstart
   tutorial

.. toctree::
   :maxdepth: 2
   :caption: Guides

   pytest
   testing-contracts
   workflow
   methods
   performance

.. toctree::
   :maxdepth: 2
   :caption: Reference and Development

   api
   contributing

Project Links
-------------

* `PyPI package <https://pypi.org/project/alternative/>`__
* `Source repository <https://github.com/Code0x58/alternative>`__

Indices
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
