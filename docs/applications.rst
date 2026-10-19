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

The extra installs NumPy, Hypothesis, and the benchmark tools. The ordinary
library installation keeps its dependency-free runtime. The
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

A search loop can mutate gate sequences, simulate them, and retain cheaper valid
circuits. Here the reference spells out :math:`HZH=X`; a candidate uses a single
:math:`X` gate. The example also includes a wrong circuit and a constructor that
raises, as a real generator may produce either.

For a cost to **minimise**, invalid candidates get :math:`+\infty`. They rank
after every finite valid reference score. A maximisation objective would use
:math:`-\infty` instead. Reject NaN scores rather than expecting sorting to place
them reliably.

.. literalinclude:: examples/matrix_trace/circuit_search.py
   :language: python

The objective checks the whole unitary before counting gates. It distinguishes
:math:`X` from :math:`-X`: global phase is part of this contract, as it matters
when the operation is controlled. A search with a different equivalence notion
must state that explicitly. Gate count is the example cost; a device-aware
objective could assign weights or measure circuit depth.

The ``try`` block sits around **candidate construction and evaluation**. Passing
an operator to ``.measure()`` cannot catch an implementation that raises before
returning its result. Use an external objective such as ``score_candidate`` for
fallible search attempts; use ``.measure()`` to score successfully returned
objects. Catch expected candidate failures at that boundary, and let errors in
the reference or search harness remain visible. Enforce execution budgets in the
search runner for attempts that may not terminate.

The population ranks as ``direct_x: 1``, ``synthesise_x: 3``, then the two invalid
attempts at infinity. Scoring does not change the default: calling
``synthesise_x()`` still returns the human-readable reference circuit. Keep this
exploratory population separate from the validated implementations you promote
for application calls.

Where Hypothesis Fits
~~~~~~~~~~~~~~~~~~~~~

Hypothesis strategies can generate bounded programs as data, as well as inputs
to numerical algorithms. This generated test constructs longer but valid
circuits by cancelling a gate word with its reverse:

.. literalinclude:: examples/matrix_trace/test_search.py
   :language: python
   :pyobject: test_generated_valid_circuits

Use `Hypothesis <https://hypothesis.readthedocs.io/en/latest/tutorial/introduction.html>`_
to find and shrink counterexamples to a candidate's claimed equivalence. You
still supply evolutionary selection, mutation, and crossover. If you experiment
with `target()
<https://hypothesis.readthedocs.io/en/latest/reference/api.html#hypothesis.target>`_,
it maximises **finite** observations: an external infinity penalty cannot be
passed directly to it. Use a finite metric on valid cases, and retain correctness
assertions so counterexamples remain failures rather than being hidden by a
fitness score.

Each generation needs a complete population before inspection or scoring freezes
registration. Create a fresh alternatives set or worker process for the next
generation. After the search, register the reviewed winner with ``default=True``
in application startup and validate it in a fresh run. See :doc:`workflow` for
that lifecycle and :doc:`testing-contracts` for observable behavior beyond return
values.
