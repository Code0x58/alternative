alternative
===========

``alternative`` is a dependency-free Python library for managing multiple
implementations of the same function.

It is designed for a common optimisation workflow:

* keep a trusted reference implementation;
* register faster, clearer, or more specialised candidate implementations;
* run equivalence tests across every implementation;
* select the implementation that normal callers should use.

Install
-------

Python 3.10 or newer:

.. code-block:: console

   $ pip install alternative

For the tests and benchmarks in these guides:

.. code-block:: console

   $ pip install "alternative[dev]"

The ``dev`` extra includes pytest and its benchmark and async plugins.
Decorated functions retain their typed call signatures for type checking and
code completion.

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

``total(...)`` calls the selected default; ``total_builtin(...)`` calls the
candidate directly.

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

   applications
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
