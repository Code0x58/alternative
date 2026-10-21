Potential Applications
======================

Keep a readable reference while a human, an LLM agent, or an automated search
proposes better implementations. These independent examples show two approaches:

.. toctree::
   :maxdepth: 1

   matrix-optimisation
   circuit-evolution

Each example is one module with its own tests. From a checkout, install their
optional dependencies with:

.. code-block:: console

   $ pip install -e '.[demo]'

The same pattern suits encoders that minimise output size or query planners
that minimise execution cost. Define correctness before comparing costs;
see :doc:`testing-contracts` and :doc:`workflow`.
