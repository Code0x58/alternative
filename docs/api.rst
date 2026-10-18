API Reference
=============

This page documents the public API exported by ``alternative``.

.. py:module:: alternative

Decorator
---------

.. autofunction:: alternative.reference(implementation=..., *, default=False)

Alternatives
------------

.. autoclass:: alternative.Alternatives
   :members:
   :exclude-members: add, pytest_parametrize, pytest_parametrize_pairs
   :special-members: __call__

.. automethod:: alternative.Alternatives.add(implementation=..., *, default=False)

.. automethod:: alternative.Alternatives.pytest_parametrize(test=..., *, only_default=False)

.. automethod:: alternative.Alternatives.pytest_parametrize_pairs(test=..., *, n_cache=0, double_reference=False, only_default=False)

The ellipsis in these signatures means the implementation or test may be omitted for
decorator-factory syntax. It is not a value to pass to the API. Runtime
registration does not validate signature compatibility; type checkers validate
the registration contracts in :ref:`typing-and-ides`.

Implementation
--------------

.. autoclass:: alternative.Implementation
   :members:
   :exclude-members: add
   :special-members: __call__

.. automethod:: alternative.Implementation.add(implementation=..., *, default=False)

Exceptions
----------

.. autoexception:: alternative.AlternativeError

.. autoexception:: alternative.AddTooLateError

.. autoexception:: alternative.MultipleDefaultsError

.. autoexception:: alternative.CrossAlternativesImplementationError

.. _typing-and-ides:

Typing and IDEs
---------------

Decorated functions keep their declared parameter and return types, including
parameter names, defaults, and keyword-only arguments. You can register
candidates and select a default in registration code while callers keep the
same typed interface and code completion. Keep using ordinary function
annotations.

Candidates must accept all calls permitted by the reference and return a
compatible type. Mypy, Pyright, and Pyrefly check these requirements; runtime
registration does not validate signatures. Annotations describe accepted calls,
while your tests establish behavioral equivalence.

Methods keep normal receiver binding. An instance supplies ``self``, and a class
method supplies ``cls``; ordinary function arguments remain explicit. See
:doc:`methods` for examples.

Runtime tools such as :func:`inspect.signature` also see the original signature,
name, and documentation. The alternatives object describes the reference's
public contract, and each candidate describes its own implementation. Inspecting
this metadata does not freeze registration.

Some IDEs can report incorrect warnings for decorated keyword calls or bound
methods. If your IDE and type checker disagree, `report a minimal example
<https://github.com/Code0x58/alternative/issues>`_. These diagnostic limitations
do not change runtime calls.
