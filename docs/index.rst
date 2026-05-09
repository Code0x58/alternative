alternative
===========

``alternative`` is a tiny, dependency-free Python library for managing multiple
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

A First Example
---------------

.. code-block:: python

   import alternative


   @alternative.reference
   def total(values: list[int]) -> int:
       result = 0
       for value in values:
           result += value
       return result


   @total.add(default=True)
   def total_builtin(values: list[int]) -> int:
       return sum(values)


   assert total([1, 2, 3]) == 6
   assert total_builtin([1, 2, 3]) == 6

Calling ``total`` uses the selected default implementation. Calling
``total_builtin`` directly still calls that implementation by itself, which is
useful in tests and benchmarks.

Contents
--------

.. toctree::
   :maxdepth: 2

   quickstart
   workflow
   pytest
   api

Project Links
-------------

* `PyPI package <https://pypi.org/project/alternative/>`__
* `Source repository <https://github.com/Code0x58/alternative>`__

Indices
-------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
