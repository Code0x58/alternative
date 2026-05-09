API Reference
=============

This page documents the public API exported by ``alternative``.

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
