API Reference
=============

This page documents the public API exported by ``alternative``.

The stubs preserve parameter names, defaults, keyword-only arguments, and
return types in mypy, Pyright, and Pyrefly. Instance and class access bind method
receivers; an ordinary function accepting ``type[T]`` still requires that argument.

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

Decorator
---------

.. autofunction:: alternative.reference

Alternatives
------------

.. autoclass:: alternative.Alternatives
   :members:
   :special-members: __call__

Implementation
--------------

.. autoclass:: alternative.Implementation
   :members:
   :special-members: __call__

Exceptions
----------

.. autoexception:: alternative.AlternativeError

.. autoexception:: alternative.AddTooLateError

.. autoexception:: alternative.MultipleDefaultsError

.. autoexception:: alternative.CrossAlternativesImplementationError
