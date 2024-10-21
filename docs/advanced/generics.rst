Generic types
=====================

You can use dishka with TypeVars and Generic-classes.

.. note::

    Though generics are supported, there are some limitations:

    * You cannot use TypeVar bounded to a Generic type
    * Generic-decorators are only applied to concrete factories or factories with more narrow TypeVars

Creating objects with @provide
************************************

You can create generic factories, use ``type[T]`` to access resolved value of ``TypeVar``. Typevar can have bound or constraints, which are checked.
For example, here we have a factory providing instances of generic class ``A``. Note that ``A[int]`` and ``A[bool]`` are different types and cached separately.

.. literalinclude:: ./generics_examples/provide.py

Decorating objects with @decorate
***************************************

You can also make Generic decorator. Here it is used to decorate any type.

.. literalinclude:: ./generics_examples/decorate.py
