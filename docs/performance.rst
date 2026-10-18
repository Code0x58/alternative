Call Overhead
=============

Implementation choice adds dispatch work to each call. Benchmark realistic input
sizes as well as individual calls: a faster implementation must save more time
than the wrapper adds. :meth:`alternative.Alternatives.measure` scores returned
results; use a timing tool such as ``pytest-benchmark`` to measure elapsed time.

Benchmark Your Application
--------------------------

Keep equivalence tests and production-path benchmarks separate. Pytest helpers
inject underlying implementations to compare algorithm costs. Also benchmark
the public decorated callable when assessing the end-to-end production benefit.

For a repeated method call, keep ``call = instance.method`` outside the loop to
avoid constructing another view for every iteration. For module functions,
holding ``function.callable`` bypasses the alternatives wrapper; accessing it
freezes registration. For methods, hold the bound method view so its receiver
continues to bind normally.

Reproduce the Dispatch Benchmark
--------------------------------

From a development checkout, run:

.. code-block:: console

   $ uv run --dev python scripts/benchmark_call_overhead.py --number 50000 --repeat 7

Add ``--json`` for machine-readable minimum and median nanoseconds per call.
Each case performs the same integer increment. Registration and first-call
selection happen before timing. ``timeit`` disables garbage collection during
each repeat. Held bound views and attribute lookup followed by a call are
separate cases, because lookup constructs a new descriptor view.

Recorded Dispatch Measurements
------------------------------

This historical comparison records the dispatch optimization in
`PR #36 <https://github.com/Code0x58/alternative/pull/36>`_. Minimum times were
measured on 18 October 2026 with CPython 3.12.7 on Linux x86-64, using seven
sequential repeats of 50,000 calls per case. The baseline is revision
``3549e52``; the optimized column uses the implementation accompanying that PR.
These values describe one environment, rather than guarantee current timings
on other Python versions or machines. Run the script above for your checkout.

.. list-table:: Microseconds per warmed call
   :header-rows: 1

   * - Case
     - Original ``3549e52``
     - Optimized
   * - Raw function
     - 0.037
     - 0.037
   * - Implicit default
     - 1.886
     - 0.379
   * - Explicit default
     - 0.992
     - 0.374
   * - Held bound instance method
     - 3.642
     - 0.352
   * - Instance method lookup and call
     - 4.210
     - 2.496

The complete environment details and case measurements are available as
:download:`JSON <benchmarks/call-overhead-20261018.json>`.

The JSON also preserves an intermediate development revision. See
:ref:`dispatch-implementation-notes` for implementation details of the
optimization.
