Runtime Workflow
================

This guide explains registration and selection after the examples in
:doc:`quickstart` and :doc:`tutorial`. Implementation choice stays explicit in
registration code, so reviewers can see which candidate application calls use.

When to Use It
--------------

Use ``alternative`` when you have:

* one implementation you trust as correct;
* one or more implementations you want to compare against it;
* tests or benchmarks that should exercise every implementation;
* a single implementation that production callers should use.

It is not a plugin system. Implementations should usually have the same
signature and the same observable behaviour unless you are deliberately
measuring or comparing different outputs.

Selection Lifecycle
-------------------

1. Define the reference and import every candidate during application startup.
2. Choose the default in registration code, using ``default=True`` on exactly one
   implementation, or leave the reference as the implicit default.
3. Apply pytest helpers to equivalence tests and benchmarks, freezing registration.
4. Use test and benchmark results to change the selection in source, then run a
   fresh process to validate that choice.

Calling the alternatives object or ``measure()``, applying either pytest helper
to a test function, and reading ``callable`` or ``implementations`` all freeze the
set. Test decorators usually run while pytest imports test modules for
collection. You cannot measure candidates and then register the winner as a
default in that same set. Selecting a default from startup configuration is
possible if it is read before any of these operations. See :doc:`tutorial` for
a complete package split across files.

.. _measure-implementations:

Measure Implementations
-----------------------

:meth:`alternative.Alternatives.measure` scores returned results with a callable
you provide. It does not measure elapsed time. For example, compressors can
produce different bytes that decode to the same input. Validate that contract,
then compare output sizes:

.. code-block:: python

   import zlib

   import alternative


   @alternative.reference
   def compress(data: bytes) -> bytes:
       """Compress bytes with a low compression level."""
       return zlib.compress(data, level=1)


   @compress.add
   def compress_dense(data: bytes) -> bytes:
       """Use a higher compression level with the same decoding contract."""
       return zlib.compress(data, level=9)


   data = b"repeated content " * 1_000
   for implementation in compress.implementations:
       assert zlib.decompress(implementation(data)) == data

   sizes = compress.measure(len, data)
   assert sizes[compress.reference] == len(compress.reference(data))
   assert sizes[compress_dense] == len(compress_dense(data))
   assert list(sizes.values()) == sorted(sizes.values())

The result is a dictionary keyed by :class:`alternative.Implementation` objects.
Sortable scores are returned in ascending order; otherwise registration order
is preserved. A lower score is not necessarily the best choice for your
application: compression time may matter as well as size. The selected default
stays unchanged, and measurement freezes registration.

Arguments are passed to every implementation without copying. For mutation,
state, or single-use inputs, use tests that create independent inputs as described
in :doc:`testing-contracts`. For receiver binding, see :doc:`methods`. Use
:doc:`performance` for elapsed-time measurement.

Safety Rules
------------

The library intentionally freezes registration after either of these events:

* the alternatives object is called;
* the implementations list is inspected.

These rules also apply when Python runs with ``-O`` or ``PYTHONOPTIMIZE``.

``.implementations`` returns a tuple, and each ``Implementation`` is immutable.
The ``.reference`` property is read-only. Register candidates with ``.add(...)``
before inspecting or invoking the alternatives set.

``.callable`` returns the underlying selected implementation in both the implicit
reference-default and explicit-default cases. Reading it also freezes
registration.

This protects test runs from covering only the implementations that happened to
be imported before collection. It also prevents runtime callers from changing
the active implementation after part of the process has already used a previous
choice.

The relevant exceptions are:

* :class:`alternative.AddTooLateError` when adding after use or inspection;
* :class:`alternative.MultipleDefaultsError` when more than one explicit
  default is registered;
* :class:`alternative.CrossAlternativesImplementationError` when moving an
  implementation wrapper between unrelated alternatives sets.

Debug Mode
----------

Set ``ALTERNATIVE_DEBUG=1`` to record call-site information for important state
changes:

.. code-block:: console

   $ ALTERNATIVE_DEBUG=1 pytest

In debug mode, errors include where the first default was set or where the
implementations were first inspected. Implementation ``repr(...)`` output also
includes registration labels, which makes similarly named local functions easier
to distinguish.

Registration Forms
------------------

Use decorators when defining implementations together. Direct calls are useful
when registering an imported function:

.. code-block:: python

   @alternative.reference
   def parse_count(text: str) -> int:
       """Parse a stripped decimal integer."""
       return int(text.strip())


   def parse_count_decimal(text: str) -> int:
       """Let int handle whitespace with an explicit decimal base."""
       return int(text, 10)


   decimal = parse_count.add(parse_count_decimal)

An :class:`alternative.Implementation` forwards ``.add`` to its parent set, so a
further candidate can register through ``decimal``:

.. code-block:: python

   @decimal.add
   def parse_count_trimmed(text: str) -> int:
       """Trim each end before parsing the integer."""
       return int(text.lstrip().rstrip())

All three implementations belong to ``parse_count``. Normal calls still use its
reference because no explicit default was selected.

Copying Implementations
-----------------------

An :class:`alternative.Alternatives` object can be added to another alternatives
set. This copies its underlying reference implementation, independently of its
selected default. Using ``parse_count`` from the preceding example:

.. code-block:: python

   @alternative.reference
   def parse_other(text: str) -> int:
       """Parse decimal input in a separate alternatives set."""
       return int(text)


   copied = parse_other.add(parse_count)
   assert copied.implementation is parse_count.reference.implementation
   assert copied(" 2 ") == 2

Calling the copy does not freeze registration in the source set.

An :class:`alternative.Implementation` from a different alternatives set cannot
be added directly. To copy the ``decimal`` candidate registered above, pass its
raw callable:

.. code-block:: python

   cloned = parse_other.add(decimal.implementation)
   assert cloned(" 2 ") == 2

This distinction avoids accidentally wiring one alternatives set into another.

Typed Calls
-----------

Candidates must accept every call allowed by the reference and return a
compatible type. This applies to ``.add(candidate)``, ``@reference.add``, and
``@reference.add(default=True)``. Preserve parameter names and defaults when
callers use them; broader parameter types and additional optional arguments are
allowed. Your callers retain the reference's typed interface when you change
which implementation they use.

Run a type checker to catch incompatible candidates; runtime registration does
not validate signatures. See :ref:`typing-and-ides` for typing and IDE support.
