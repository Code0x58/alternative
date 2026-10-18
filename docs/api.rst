API Reference
=============

This page documents the public API exported by ``alternative``.

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
the public contracts described above.

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

Typing and IDEs
---------------

The stubs preserve parameter names, defaults, keyword-only arguments, and
return types in mypy, Pyright, and Pyrefly. Instance and class access bind method
receivers; an ordinary function accepting ``type[T]`` still requires that argument.

Runtime wrappers preserve the original name, documentation, annotations, and
``__wrapped__`` link. :func:`inspect.signature` follows that link, including
receiver binding on method access. Inspecting metadata does not freeze
registration. The alternatives object describes the reference's public contract;
each candidate wrapper describes its own implementation.

Wrapper types now carry both the bound and complete parameter lists:
``Alternatives[S, P, R, Q]`` and ``Implementation[S, P, R, Q]``. For explicit
annotations, append the original signature as ``Q``. For example,
``Alternatives[int, [str], str, [int, str]]`` wraps a function taking an integer
and a string. Inferred decorator types need no annotations.

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

``typing_tests/pycharm_xfails.json`` records each affected assertion and its exact
expected diagnostics. These expected failures apply only to the headless PyCharm
check; all assertions remain active for mypy, Pyright, and Pyrefly, and runtime
tests execute the same call shapes. New diagnostics and unexpected passes fail
the check so that fixed cases can be removed from the manifest.

The standalone ``typing_tests/pycharm_paramspec_repro.py`` reproduces callback
inference without importing this library. Related JetBrains reports cover
`ParamSpec matching outside Callable
<https://youtrack.jetbrains.com/issue/PY-77541>`_ and `decorated method binding
<https://youtrack.jetbrains.com/issue/PY-85027>`_.
