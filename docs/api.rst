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

PyCharm 2026.2.3 still reports false diagnostics for some valid keyword,
variadic, and descriptor calls. The headless probes record this outstanding
compatibility issue; the three CI type checkers cover these call shapes.
``typing_tests/pycharm_paramspec_repro.py`` contains a minimal callback-protocol
reproduction that does not import this library. It passes the three CI checkers
but PyCharm infers ``Any`` for the keyword call's result. Related JetBrains
reports track `ParamSpec matching outside Callable
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
