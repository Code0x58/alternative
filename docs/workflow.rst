Runtime Workflow
================

``alternative`` is most useful when you want implementation choice to be visible
in code review instead of hidden behind conditionals or environment-specific
imports.

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

Measure Implementations
-----------------------

:meth:`alternative.Alternatives.measure` calls every implementation with the
same arguments and then applies an operator to each result.

.. code-block:: python

   import alternative


   @alternative.reference
   def make_four() -> str:
       return "1 + 1 + 1 + 1"


   @make_four.add
   def make_four_factor() -> str:
       return "2 * 2"


   @make_four.add
   def make_four_literal() -> str:
       return "4"


   measurements = make_four.measure(len)

The result is a dictionary keyed by :class:`alternative.Implementation` objects.
If the measurement values are sortable, the dictionary is returned in ascending
measurement order. If values cannot be sorted, registration order is preserved.

Safety Rules
------------

The library intentionally freezes registration after either of these events:

* the alternatives object is called;
* the implementations list is inspected.

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

Copying Implementations
-----------------------

An :class:`alternative.Alternatives` object can be added to another alternatives
set, which copies its underlying reference implementation:

.. code-block:: python

   target.add(source_alternatives)

An :class:`alternative.Implementation` from a different alternatives set cannot
be added directly. Pass ``implementation.implementation`` if you deliberately
want to clone the raw callable:

.. code-block:: python

   target.add(source_implementation.implementation)

This distinction avoids accidentally wiring one alternatives set into another.
