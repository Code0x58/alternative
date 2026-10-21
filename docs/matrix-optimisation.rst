Matrix Optimisation with Cyclic Symmetry
========================================

Keep a short NumPy definition as the reference, then exploit the structure of
the matrix to eliminate expensive work. This example uses ordinary classical
linear algebra. Its complete implementation, correctness tests, and benchmark
are in :download:`one module <examples/test_circulant.py>`.

The task is to compute :math:`\operatorname{tr}(C^p)` for a circulant matrix:
each column is a cyclic shift of its predecessor. Such matrices describe
periodic convolution; when their coefficients are probabilities, the trace of
a power sums return probabilities for a random walk on a ring.

The Direct Definition and the Shortcut
---------------------------------------

The reference constructs the matrix from its first column, uses NumPy's
``matrix_power``, and takes the trace. The candidate computes its eigenvalues
with an FFT and sums their powers:

.. literalinclude:: examples/test_circulant.py
   :language: python
   :start-at: @alternative.reference
   :end-before: @circulant_trace.pytest_parametrize()

The cyclic shift matrix :math:`S` generates the cyclic group, and every
circulant has the form :math:`C=\sum_j c_j S^j`. The discrete Fourier basis
diagonalises :math:`S`, so it diagonalises :math:`C` too:

.. math::

   \lambda_k=\sum_{j=0}^{n-1} c_j e^{-2\pi i jk/n}
             =\operatorname{FFT}(c)_k,
   \qquad \operatorname{tr}(C^p)=\sum_{k=0}^{n-1}\lambda_k^p.

This removes both the :math:`n\times n` allocation and the dense matrix
multiplications. For fixed powers of two or more, work changes from :math:`O(n^3)` to
:math:`O(n\log n)`, and storage from :math:`O(n^2)` to :math:`O(n)`. NumPy's
`matrix_power <https://numpy.org/doc/stable/reference/generated/numpy.linalg.matrix_power.html>`_
already uses repeated squaring; the gain comes from changing the mathematics.
SciPy uses the same
`Fourier-space structure for circulant linear systems
<https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_circulant.html>`_.

The demo accepts 1–512 real coefficients with absolute sum at most one and
integer powers 0–8. These bounds keep the dense reference affordable and all
eigenvalue magnitudes at most one. Zero powers include singular matrices and
return :math:`n`. Real coefficients give conjugate-paired eigenvalues, which
justify taking the real part of the final sum. The shortcut requires cyclic
symmetry; a general dense matrix needs a different argument.

Tests and a Real Benchmark
---------------------------

From a checkout, install the optional dependencies and run this module:

.. code-block:: console

   $ pip install -e '.[demo]'
   $ pytest docs/examples/test_circulant.py
   $ pytest docs/examples/test_circulant.py -k benchmark --benchmark-json=circulant-trace.json

The same file checks independent answers for identity matrices, cyclic shifts,
zero powers, and rank-one matrices, then uses generated signed coefficients to
compare both implementations. Comparisons allow absolute and relative error
of :math:`10^{-10}`. These tests support the algebraic argument; they do not
replace it.

.. literalinclude:: examples/test_circulant.py
   :language: python
   :pyobject: test_benchmark

.. csv-table:: Example median microseconds per call
   :file: benchmarks/circulant-trace.csv
   :header-rows: 1

Both implementations include validation and all construction in the timed call,
with the same coefficients and power seven. BLAS uses one thread; there is one
warmup and nine measured calls. The :download:`measurement details
<benchmarks/circulant-trace.json>` include the environment and samples. Timings
depend on the machine; the improvement grows with matrix size. CI checks
correctness without asserting a speed ratio.

An Agent Task
--------------

This also makes a focused task for an LLM agent:

.. code-block:: text

   Keep circulant_trace and its input contract as the readable reference.
   Add a faster candidate and explain the identities and assumptions used.
   Check independent answers and generated equivalence, including zero powers
   and singular matrices. Benchmark complete calls at several matrix sizes.
   Propose a default after reviewing correctness and measured performance.

Keep additional correctness cases outside the optimisation feedback and review
the proof assumptions. ``default=True`` in this example represents the reviewed
selection; the direct definition remains available as ``circulant_trace.reference``.
