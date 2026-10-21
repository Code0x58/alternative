NumPy optimisation
==================

Cyclic symmetry can turn a dense matrix calculation into one FFT. Consider
:math:`\operatorname{tr}(C^p)` for a **circulant matrix**: every column is a cyclic
shift of the first. These matrices arise in periodic convolution and random
walks on a ring.

The NumPy reference constructs and powers the matrix. Its specialised candidate
needs only an FFT:

.. literalinclude:: examples/test_circulant.py
   :language: python
   :start-at: @alternative.reference
   :end-before: @circulant_trace.pytest_parametrize()

Every circulant is a polynomial in the cyclic shift matrix :math:`S`:
:math:`C=\sum_j c_j S^j`. The Fourier basis diagonalises :math:`S` and hence
:math:`C`, with eigenvalues :math:`\lambda=\operatorname{FFT}(c)`. Therefore

.. math::

   \operatorname{tr}(C^p)=\sum_k\lambda_k^p.

For a fixed power of two or more, cubic dense work becomes
:math:`O(n\log n)` work, and storage drops from :math:`O(n^2)` to :math:`O(n)`.
This is the same Fourier-space structure used in
`circulant linear solvers
<https://docs.scipy.org/doc/scipy/reference/generated/scipy.linalg.solve_circulant.html>`_.
Real coefficients give conjugate-paired eigenvalues, so the trace is real.

Compare with Alternative
--------------------------

``pytest_parametrize_pairs()`` supplies the reference and each candidate to the
same generated equivalence test:

.. literalinclude:: examples/test_circulant.py
   :language: python
   :pyobject: test_equivalent_traces

``.measure()`` scores returned values. Here the score is numerical error against
an independent answer; smaller is better:

.. literalinclude:: examples/test_circulant.py
   :language: python
   :pyobject: test_measure_error

For elapsed time, ``pytest_parametrize()`` runs a shared benchmark against every
registered implementation:

.. literalinclude:: examples/test_circulant.py
   :language: python
   :pyobject: test_benchmark

With the :doc:`demo dependencies <applications>` installed:

.. code-block:: console

   $ pytest docs/examples/test_circulant.py
   $ pytest docs/examples/test_circulant.py -k benchmark

The :download:`complete module <examples/test_circulant.py>` assumes a nonempty
real column and a nonnegative integer power. Its tests cover cyclic shifts,
singular matrices, zero powers, and generated coefficients. They bound powers
to 0–8 and the coefficients' absolute sum to one to keep rounding error small,
then compare answers within absolute and relative tolerances of :math:`10^{-10}`.
The benchmark includes construction, uses one BLAS thread, and measures several
sizes. One Ryzen 2700X run at 512×512 took about 47 ms for dense powers and 38 µs
for the FFT version, roughly 1,200× faster. Measure your own workload and machine.

An LLM agent task:

.. code-block:: text

   Keep circulant_trace as the readable reference. Add a faster candidate,
   explain its algebraic assumptions, and check independent and generated
   answers, including singular matrices and zero powers. Benchmark complete
   calls at several sizes before proposing the default.
