Evolving Quantum Circuits
==========================

Use `DEAP <https://deap.readthedocs.io/en/master/overview.html>`_ to evolve gate
sequences and Qiskit to evaluate them. The reference expresses :math:`X=HZH`;
the search can discover a single X gate. Five slots drawn from I, H, Z, and X
keep the problem small, with identity slots excluded from gate count.

.. literalinclude:: examples/test_circuit_search.py
   :language: python
   :end-before: @given

Fitness minimises unitary error first, then correct circuits' gate count.
Every correct circuit beats every incorrect one; error distance guides the
remaining genomes toward correctness. Wrong or failed circuits have infinite
gate cost. Qiskit's `Operator
<https://quantum.cloud.ibm.com/docs/en/guides/operator-class>`_ checks the whole
unitary, preserving global phase: :math:`X` and :math:`-X` differ under this
contract. The error tolerance is :math:`10^{-12}`.

The reference seeds the population, and DEAP retains the best parents and
offspring. After searching, ``evolve`` registers its frozen winner in a fresh
alternatives set. Normal calls still use the reference; review the result before
selecting a new default. A bounded search need not find an optimum.

Run It
-------

With the :doc:`demo dependencies <applications>` installed:

.. code-block:: console

   $ python docs/examples/test_circuit_search.py
   $ pytest docs/examples/test_circuit_search.py

The :download:`complete module <examples/test_circuit_search.py>` prints costs
and gate sequences. Run it as a standalone, sequential example: DEAP uses
Python's seeded random generator. Hypothesis tests cancelling gate words;
other tests check the real search, phase errors, and reference preservation.
