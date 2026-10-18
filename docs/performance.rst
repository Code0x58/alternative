Performance and When to Use It
==============================

Use ``alternative`` to keep a trusted reference, test candidate implementations
consistently, and choose a default without changing application callers. Each
call through the alternatives object adds some dispatch work. Include that cost
when deciding whether a candidate improves performance.

A Rough Overhead Budget
-----------------------

Functions doing tens of microseconds or more of work per call are a useful
starting point: dispatch is usually a small part of their total time. For
functions taking only a few microseconds, compare the full application call
before adopting a rewrite. The savings may be smaller than the added dispatch.

The following rounded costs illustrate the scale, based on warmed calls to a
trivial integer function in one CPython run:

.. list-table:: Approximate added cost per call
   :header-rows: 1

   * - Application call pattern
     - Added cost
     - Work per call for roughly 5% overhead
   * - Function, or a bound method saved before a loop
     - 0.4 microseconds
     - 10 microseconds
   * - Method looked up on the instance for every call
     - 2–3 microseconds
     - 50 microseconds

These are planning estimates, not guarantees for another interpreter, machine,
or workload. The :download:`example measurements <benchmarks/dispatch-example.json>`
include the environment and raw timings. They exclude registration and first-use
setup. Measure startup separately if it matters to your application.

For a 5% overhead budget, aim for the implementation's own work to take at least
20 times the extra call cost. For a speed improvement, the candidate's time plus
dispatch must be less than the original call's time. For example, reducing
50 microseconds of work to 40 microseconds leaves room for 0.4 microseconds of
dispatch. Reducing 1 microsecond to 0.8 microseconds does not.

The registration and test helpers can still be useful for comparing very small
functions. Choose the production call path separately if every fraction of a
microsecond matters.

Benchmark Your Application
--------------------------

Use realistic inputs and benchmark both the underlying implementations and the
public decorated callable. The pytest helpers supply underlying implementations,
so their timings compare algorithms. A separate benchmark of the decorated
entry point includes dispatch and shows what application callers experience.
See :doc:`tutorial` for both tests in a runnable example.

For repeated method calls, save ``call = instance.method`` before the loop and
invoke ``call(...)`` inside it to avoid repeated lookup. For a module function,
``call = function.callable`` gives direct access to the selected implementation.
Read it after registering all candidates: doing so freezes registration and
keeps that selection stable. For methods, save the bound method so Python still
supplies the receiver normally.

:meth:`alternative.Alternatives.measure` scores returned results, such as
compressed output sizes. Use a timing tool such as ``pytest-benchmark`` to
measure elapsed time.

Measure Dispatch in Your Environment
------------------------------------

The source checkout includes a small dispatch benchmark. With ``alternative``
installed in your Python environment, run:

.. code-block:: console

   $ python scripts/benchmark_call_overhead.py --number 100000 --repeat 7

Add ``--json`` for environment details and minimum and median nanoseconds per
call. The script times the same integer increment through ordinary and
decorated call paths, with registration and first-use setup completed before
timing. It measures saved bound methods separately from method lookup on every
call. These small-call measurements help estimate overhead; application
benchmarks determine whether the library fits your workload.
