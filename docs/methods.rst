Methods and Descriptors
=======================

Use the same registration and selection workflow for instance, class, and static
methods. This page assumes you have followed :doc:`quickstart`; the examples
illustrate binding, rather than claim a speed improvement.

Decorator Order
---------------

Decorate instance methods directly. For class and static methods, put
``@alternative.reference`` and ``.add`` outside the built-in descriptor
decorator:

.. code-block:: python

   import alternative


   class Parser:
       def __init__(self, value: str = ""):
           """Store the text used to construct this parser."""
           self.value = value

       @alternative.reference
       def parse(self, value: str) -> int:
           """Parse a decimal integer after stripping whitespace."""
           return int(value.strip())

       @parse.add
       def parse_decimal(self, value: str) -> int:
           """Let int handle whitespace with an explicit decimal base."""
           return int(value, 10)

       @alternative.reference
       @classmethod
       def from_text(cls, value: str) -> "Parser":
           """Construct the accessed class from stripped text."""
           return cls(value.strip())

       @from_text.add
       @classmethod
       def from_text_trimmed(cls, value: str) -> "Parser":
           """Trim each end separately before constructing the class."""
           return cls(value.lstrip().rstrip())

       @alternative.reference
       @staticmethod
       def is_valid(value: str) -> bool:
           """Check for a nonempty string of Unicode digits."""
           return value.strip().isdigit()

       @is_valid.add
       @staticmethod
       def is_valid_characters(value: str) -> bool:
           """Check the same digit contract one character at a time."""
           stripped = value.strip()
           return bool(stripped) and all(char.isdigit() for char in stripped)

Imported Static Candidates
--------------------------

Adding a plain function to a static-method reference preserves static binding:

.. code-block:: python

   def accepts_digits(value: str) -> bool:
       """Apply the same validation without an implicit receiver."""
       return str.isdigit(value.strip())


   registered = Parser.is_valid.add(accepts_digits, default=True)

Register imported candidates before calling or inspecting the alternatives set.
``default=True`` selects this candidate for normal calls to ``Parser.is_valid``.
Registration happens before any of the calls below.

Call Through a Class or Instance
--------------------------------

.. code-block:: python

   parser = Parser.from_text(" 1 ")
   assert parser.value == "1"
   assert parser.parse(" 1 ") == parser.parse_decimal(" 1 ") == 1
   assert Parser.from_text_trimmed(" 2 ").value == "2"
   for value in ("", " 123 ", "²", "a"):
       assert Parser.is_valid(value) == parser.is_valid_characters(value)
       assert Parser.is_valid(value) == registered(value) == parser.is_valid(value)

Calling through an instance or class binds ``self`` and ``cls`` normally.
Direct candidate calls bind the same way: ``parser.parse_decimal("1")`` calls
that candidate, while ``Parser.from_text_trimmed("1")`` supplies ``Parser`` as
``cls``. Access through a subclass supplies the subclass. Static methods receive
no implicit receiver through either a class or an instance.

Testing and Measuring
---------------------

See :ref:`testing-methods` for pytest examples using explicit or bound receivers.
For result scoring, ``instance.method.measure(operator, ...)`` supplies the
instance and ``Class.class_method.measure(operator, ...)`` supplies the accessed
class. Accessing an ordinary method through its class leaves the receiver
explicit: ``Class.method.measure(operator, instance, ...)``. Static methods never
receive an implicit receiver. See :ref:`measure-implementations` for the scoring
contract and :doc:`performance` for elapsed-time measurement.
