Potential Applications
======================

``alternative`` keeps a readable reference alongside candidate implementations,
with shared correctness tests and benchmarks. Candidates can come from a human,
an LLM agent, or an automated search. Choosing the default remains explicit.

These two independent examples each fit in one module, including their tests:

.. toctree::
   :maxdepth: 1

   matrix-optimisation
   circuit-evolution

* :doc:`matrix-optimisation` starts with a direct NumPy matrix calculation and
  exploits cyclic symmetry to replace dense matrix powers with an FFT. It
  includes a real benchmark and a suggested optimisation task for an agent.
* :doc:`circuit-evolution` uses DEAP and Qiskit to evolve shorter gate sequences,
  then registers the validated winner alongside its reference. Hypothesis
  challenges correctness properties.

The examples share no application code or data. The matrix calculation uses
classical linear algebra; its implementation imports neither DEAP nor Qiskit.

Other applications follow the same pattern: an encoder can minimise output size
while preserving decoded data, or a query planner can minimise execution cost
while preserving query results. Define correctness before comparing costs; see
:doc:`testing-contracts` and :doc:`workflow`.
