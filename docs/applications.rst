Potential Applications
======================

``alternative`` gives you a stable reference, a registry of candidate rewrites,
and shared tests and benchmarks. A human, a search algorithm, or an LLM agent
can propose the candidates. You keep the readable specification while testing
optimisations that look very different from it.

.. list-table:: Choosing an objective
   :header-rows: 1

   * - Application
     - Correctness contract
     - Cost to minimise
   * - Numerical algorithm rewrites
     - Independent answers and bounded numerical error
     - Elapsed time and memory
   * - Quantum circuit synthesis
     - The required unitary action
     - Gate count, depth, or a device-specific cost
   * - Encoders and query-plan generators
     - Decoded data or query results
     - Output size or execution cost

The first two applications below have executable examples. You supply the agent
or search loop; the library keeps implementation choice and comparison explicit.

A Matrix Calculation That Becomes a Product of Cosines
------------------------------------------------------

Suppose a quantum model applies independent single-qubit rotations, repeats that
layer, and asks for its trace. Traces of powers describe spectral moments: they
summarise the eigenphases of the evolution. The direct calculation is easy to
review, but the matrix has :math:`2^q` rows and columns for :math:`q` qubits.

For this example each rotation is about :math:`(1,1,1)/\sqrt{3}`:

.. math::

   P = (X+Y+Z)/\sqrt{3}, \qquad P^2=I,
   \qquad R(\theta)=\cos(\theta/2)I-i\sin(\theta/2)P.

Here :math:`X,Y,Z` are the Pauli matrices. The task is

.. math::

   U=R(\theta_1)\otimes\cdots\otimes R(\theta_q),
   \qquad T(\boldsymbol\theta,m)=\operatorname{tr}(U^m).

This is a **separable layer**. Entangling gates between qubits would require a
different argument; the shortcut below does not apply to an arbitrary circuit.

Run the Optional Demo
~~~~~~~~~~~~~~~~~~~~~

From a source checkout, install the ``demo`` extra and run its tests:

.. code-block:: console

   $ pip install -e '.[demo]'
   $ pytest docs/examples/matrix_trace

The extra installs NumPy, Hypothesis, DEAP, Qiskit, and the benchmark tools. The
ordinary library installation keeps its dependency-free runtime. The
`example directory
<https://github.com/Code0x58/alternative/tree/master/docs/examples/matrix_trace>`_
contains the complete package; the snippets here embed those files directly.

The demo accepts up to eight angles in :math:`[-\pi,\pi]` and integer repetition
counts from -16 to 16. The size limit keeps the dense oracle affordable. It is a
demo contract, not a limit imposed by ``alternative``. Empty input represents the
one-dimensional identity and has trace 1, including for negative powers.

Keep the Matrix Definition as the Reference
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

``model.py`` defines the rotations and checks the shared input domain:

.. literalinclude:: examples/matrix_trace/model.py
   :language: python

``reference.py`` follows the mathematical definition. NumPy's
`matrix_power <https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_power.html>`_
already uses repeated squaring for positive powers; the reference is not made
artificially slow by multiplying the layer in a Python repetition loop.

.. literalinclude:: examples/matrix_trace/reference.py
   :language: python

Change the Representation, Then Eliminate the Matrices
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tensor-product identities

.. math::

   (A\otimes B)^m=A^m\otimes B^m, \qquad
   \operatorname{tr}(A\otimes B)=\operatorname{tr}(A)\operatorname{tr}(B)

reduce the problem to powers of individual :math:`2\times2` matrices. Negative
integer powers work because these rotations are invertible. You can verify both
identities from the block definition of the
`Kronecker product <https://numpy.org/doc/stable/reference/generated/numpy.kron.html>`_.

There is another transformation: :math:`P` has eigenvalues :math:`+1,-1`, so
:math:`R(\theta)` has eigenvalues :math:`e^{-i\theta/2},e^{i\theta/2}`. Consequently,

.. math::

   \operatorname{tr}(R(\theta)^m)=2\cos(m\theta/2), \qquad
   T(\boldsymbol\theta,m)=\prod_{j=1}^q 2\cos(m\theta_j/2).

The local trace is the character of SU(2)'s two-dimensional representation.
For independent rotations the tensor-product trace is the product of these local
characters. The final implementation needs neither a matrix nor an
eigendecomposition. The dense reference stores :math:`4^q` complex entries;
the character formula performs :math:`O(q)` scalar work with constant auxiliary
storage. The usual dense matrix multiplications instead grow cubically in the
matrix dimension, with the number of multiplications depending on :math:`m`.

``candidates.py`` registers both steps so that each transformation can be checked
and benchmarked separately:

.. literalinclude:: examples/matrix_trace/candidates.py
   :language: python

``default=True`` shows the final, reviewed selection. The reference remains
available as ``layer_trace.reference``. Package startup imports every candidate
before exposing ``layer_trace`` to callers:

.. literalinclude:: examples/matrix_trace/__init__.py
   :language: python

For more on the rotation convention, see IBM's
`Pauli evolution documentation
<https://quantum.cloud.ibm.com/docs/en/api/qiskit/qiskit.circuit.library.PauliEvolutionGate>`_.
The half-angle matters: a :math:`2\pi` spinor rotation is :math:`-I`, not
:math:`I`. Replacing SU(2) with an ordinary three-dimensional rotation formula
would give the wrong sign.

Protect the Meaning of the Shortcut
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The tests combine independent expected answers with Hypothesis-generated inputs
and pairwise comparisons. They cover negative powers, empty products, small
angles, and the spinor sign. The explicit absolute tolerance handles traces near
zero, where relative error alone is unsuitable.

.. literalinclude:: examples/matrix_trace/test_correctness.py
   :language: python
   :pyobject: test_generated_traces

The :download:`complete test file <examples/matrix_trace/test_correctness.py>`
also checks unitarity, determinant 1, input rejection, and invariance under
reordering independent qubits. Generated tests support the
algebraic argument; finite testing alone does not prove the identity. Changing
the domain to huge angles or repetition counts needs a fresh numerical error
analysis, even though the exact symbolic identity still holds.

Benchmark the Actual Algorithms
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The benchmark includes matrix construction and domain validation on every call.
At each size, all implementations use the same angles and seven layer repetitions. BLAS runs
on one thread, with one warmup and nine measured rounds of ten calls per case.
A separate production benchmark includes dispatch through the selected default:

.. literalinclude:: examples/matrix_trace/test_benchmark.py
   :language: python

Run the benchmark file with JSON output to record your environment and timings:

.. code-block:: console

   $ pytest docs/examples/matrix_trace/test_benchmark.py --benchmark-json=matrix-trace.json

.. csv-table:: Example median microseconds per call
   :file: benchmarks/matrix-trace.csv
   :header-rows: 1

These are example measurements, not a guaranteed speedup. The
:download:`measurement details <benchmarks/matrix-trace.json>` record the CPU,
Python, NumPy, BLAS configuration, and sample timings. The useful change is the
scaling: the matrix grows exponentially with qubit count while the final formula
grows linearly. There is no machine-specific speed assertion in the tests.

Asking an Agent to Improve the Algorithm
----------------------------------------

The matrix example makes a concrete agent task. Keep ``reference.py`` and the
input contract under human control, and ask for a candidate with an explanation:

.. code-block:: text

   Improve layer_trace without changing the reference or its input domain.
   Add a candidate with the same typed signature. Explain each mathematical
   identity and the conditions under which it is valid. Preserve complex
   phase, negative powers, empty input, and the numerical error budget.
   Run independent-answer tests and generated equivalence tests. Keep any
   counterexample as a regression case. Report algorithm and production-call
   benchmarks at several sizes, including allocations and setup in the timed
   call. Propose the default only after reviewing correctness and timings.

This permits a substantial representation change while leaving a readable
oracle for future reviewers. Keep additional evaluation cases outside the
agent's optimisation feedback, and review the proof assumptions as well as the
benchmark. An optimisation can agree on a training corpus and still violate the
contract elsewhere.

Evolutionary Search and Quantum Circuit Synthesis
-------------------------------------------------

Use `DEAP <https://deap.readthedocs.io/en/master/overview.html>`_ to evolve a
population of circuits, and Qiskit to evaluate their unitary action. DEAP
provides selection, crossover, mutation, and a hall of fame. Hypothesis supplies
generated correctness tests for the evaluator and the resulting candidates.

The task is to implement a CNOT controlled by qubit 1 and targeting qubit 0.
The readable reference reverses a CNOT in the other direction by conjugating
both qubits with Hadamards:

.. literalinclude:: examples/matrix_trace/circuit_search.py
   :language: python
   :pyobject: reference_program

The allowed vocabulary includes Hadamards, Pauli gates, and CNOTs in either
direction. A genome has seven integer slots; an identity token represents an
empty slot. DEAP can therefore replace gates or remove them without requiring
variable-length genetic operators. The search may discover the single reverse
CNOT, but it is not given a handwritten winning candidate. This small vocabulary
demonstrates the workflow; practical synthesis needs a cost and gate set that
reflect the target device.

Correctness Before Cost
~~~~~~~~~~~~~~~~~~~~~~~

Qiskit's `Operator
<https://quantum.cloud.ibm.com/docs/en/guides/operator-class>`_ computes a circuit's
whole unitary locally, without an account or simulator backend. The example
compares it with an independent matrix for the required basis-state permutation:

.. literalinclude:: examples/matrix_trace/circuit_search.py
   :language: python
   :pyobject: simulate

Checking only the all-zero input would miss this operation's behavior on other
states. Comparing matrices also preserves global phase. For this contract,
:math:`U` and :math:`-U` are different: the phase can become observable when the
operation is controlled. Qiskit's ``Operator.equiv`` allows global phase, so it
would express a different contract.

The fitness has two objectives, compared **lexicographically**: first minimise
unitary error, then minimise the gate count of correct circuits. Errors within
the explicit numerical tolerance count as zero:

.. literalinclude:: examples/matrix_trace/circuit_search.py
   :language: python
   :pyobject: circuit_fitness

Every correct circuit beats every incorrect circuit, even a cheaper one.
Incorrect circuits still have an error distance that can guide evolution toward
correctness. Giving every incorrect genome the same infinity fitness would
discard that guidance. Failed construction and nonfinite error values rank last.
The separate gate-cost objective is :math:`+\infty` for every incorrect or failed
candidate, so it cannot displace the finite-cost reference on cost alone.

Run the Evolution
~~~~~~~~~~~~~~~~~~

``evolve`` seeds the population with the validated reference and random genomes.
It registers DEAP's two-point crossover and integer mutation, then uses its
:math:`(\mu+\lambda)` algorithm. Selecting the best parents and offspring retains
the best valid circuit, and the hall of fame records the winner:

.. literalinclude:: examples/matrix_trace/circuit_search.py
   :language: python
   :pyobject: evolve

Run it from the checkout with the same ``demo`` extra installed:

.. code-block:: console

   $ python -m docs.examples.matrix_trace.circuit_search

The command prints the discovered circuit, the best valid gate count at each
generation, and the finalists' costs. The default run uses 64 individuals and
40 generations. For example, a run found ``('H0', 'H0', 'CX10')`` after starting
with the five-gate reference. Its three gates have the required action because
the two Hadamards cancel. Some runs reach the one-gate ``('CX10',)``; some retain
the reference. A seed helps reproduce a run in the same environment, but the
search budget does not guarantee improvement or an optimum.

The :download:`complete example <examples/matrix_trace/circuit_search.py>` includes
the genome representation and DEAP adapters. It is a bounded, sequential search:
the seven-slot, two-qubit limit keeps full-unitary evaluation affordable. Larger
unitaries require exponentially more memory. The demo saves and restores Python's
random state because DEAP's standard operators use it; concurrent searches need
separate worker processes.

Review and Register the Winner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Keep evolution outside the alternatives registry. Once the search finishes,
validate the frozen finalist and create a fresh reference/candidate set:

.. literalinclude:: examples/matrix_trace/circuit_search.py
   :language: python
   :pyobject: compare_winner

Normal calls still use the readable reference. The command uses ``.measure()``
to compare the finalists' gate counts; it does not select a default. After
reviewing the result and its tests, register the chosen candidate with
``default=True`` at application startup and validate it in a fresh run.

For fallible generators, put the exception boundary around both construction and
evaluation:

.. literalinclude:: examples/matrix_trace/circuit_search.py
   :language: python
   :pyobject: score_candidate

Passing an operator to ``.measure()`` cannot catch an implementation that raises
before returning its result. Catch expected candidate failures at the external
objective, while allowing reference or search-harness failures to stop the run.
Enforce execution budgets in the search runner for attempts that may not
terminate. See :doc:`workflow` for registration and :doc:`testing-contracts` for
observable behavior beyond return values.

Use Hypothesis to Challenge the Results
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

`Hypothesis <https://hypothesis.readthedocs.io/en/latest/tutorial/introduction.html>`_
finds and shrinks counterexamples to claimed properties. Here it tests generated
genomes for unitarity, and challenges the fitness evaluator with known-valid
circuits constructed by cancelling self-inverse gate words:

.. literalinclude:: examples/matrix_trace/test_search.py
   :language: python
   :pyobject: test_generated_valid_circuits

Its ``target()`` feature can guide adaptive test generation, but an explicit
genetic search benefits from DEAP's population and genetic operators. Keep
correctness assertions in the tests: a counterexample should remain a test
failure, rather than being hidden by an optimisation score. The
:download:`search tests <examples/matrix_trace/test_search.py>` also cover the
phase contract, construction failures, reference validation, and retaining a
valid incumbent. They assert correctness and bounded cost, without requiring a
stochastic search to find a particular optimum.
