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

Candidates must accept all calls permitted by the reference and return a
compatible type. Runtime registration does not enforce this contract; use a
type checker to validate candidates.

The stubs preserve parameter names, defaults, keyword-only arguments, and
return types in mypy, Pyright, and Pyrefly. Instance and class access bind method
receivers; an ordinary function accepting ``type[T]`` still requires that argument.

Runtime wrappers preserve the original name, documentation, annotations, and
``__wrapped__`` link. :func:`inspect.signature` follows that link, including
receiver binding on method access. Inspecting metadata does not freeze
registration. The alternatives object describes the reference's public contract;
each candidate wrapper describes its own implementation.

Normally, let the decorators infer wrapper types; no extra annotations are
needed at call sites. For explicit wrapper annotations and the generic parameter
model, see :ref:`typing-model`.

PyCharm compatibility
---------------------

PyCharm 2026.2.3 has three known ParamSpec-related gaps:

.. list-table:: Recognised PyCharm gaps
   :header-rows: 1
   :widths: 35 65

   * - Call shape
     - Incorrect IDE behaviour
   * - Keyword calls through decorator objects
     - Widens a concrete return type with ``Any``.
   * - ``*args`` and ``**kwargs``
     - Checks individual arguments against tuple or dictionary container types.
   * - Instance and class methods
     - Retains a bound ``self`` or ``cls`` parameter.

These are IDE diagnostic limitations; they do not change runtime binding.
Mypy, Pyright, and Pyrefly check the affected call shapes. See
:ref:`pycharm-typing-checks` for reproductions, related JetBrains reports, and the
contributor workflow for tracking expected diagnostics.
