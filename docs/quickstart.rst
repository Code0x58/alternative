Quickstart
==========

``alternative`` gives one function a set of named implementations. The first
implementation is the reference. Extra implementations are registered from the
reference object or from any registered implementation.

Register Implementations
------------------------

Use :func:`alternative.reference` on the implementation you trust most.

.. code-block:: python

   import alternative


   @alternative.reference
   def normalise_name(name: str) -> str:
       return " ".join(part.capitalize() for part in name.split())


   @normalise_name.add
   def normalise_name_title(name: str) -> str:
       return name.title()

``normalise_name`` is now an :class:`alternative.Alternatives` object, and
``normalise_name_title`` is an :class:`alternative.Implementation` object.
Both are callable:

.. code-block:: python

   assert normalise_name("ada lovelace") == "Ada Lovelace"
   assert normalise_name_title("ada lovelace") == "Ada Lovelace"

Choose a Default
----------------

If no explicit default is registered, calling the reference object uses the
reference implementation. Use ``default=True`` to make a candidate the normal
runtime implementation:

.. code-block:: python

   @normalise_name.add(default=True)
   def normalise_name_fast(name: str) -> str:
       return name.title()


   assert normalise_name("grace hopper") == "Grace Hopper"

Only one explicit default can be registered. This catches accidental import
order changes where two modules both try to choose the active implementation.

Use Decorator or Direct Call Syntax
-----------------------------------

All registration helpers support decorator and direct-call forms:

.. code-block:: python

   @alternative.reference
   def reference_impl() -> int:
       return 1


   def candidate_impl() -> int:
       return int(True)


   candidate = reference_impl.add(candidate_impl)

Use the decorator style when defining implementations together. Use direct calls
when importing a candidate from another module.

Add Through an Implementation
-----------------------------

An :class:`alternative.Implementation` forwards ``.add(...)`` to its parent
alternatives set. This makes chained registration convenient:

.. code-block:: python

   @alternative.reference
   def parse_count(text: str) -> int:
       return int(text.strip())


   @parse_count.add
   def parse_count_decimal(text: str) -> int:
       return int(text, 10)


   @parse_count_decimal.add(default=True)
   def parse_count_fast(text: str) -> int:
       return int(text)

The three implementations still belong to the same alternatives set.
