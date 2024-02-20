.. _decorate:

@decorate
*********************

``decorate`` is used to modify or wrap an object which is already configured in another ``Provider``.

Provider object has also a ``.decorate`` method with the same logic.

If you want to apply decorator pattern and do not want to alter existing provide method, then it is a place for ``decorate``. It will construct object using earlier defined provider and then pass it to your decorator before returning from the container.


.. code-block:: python

    class MyProvider(Provider):
        @decorate
        def decorate_a(self, a: A) -> A:
            return ADecorator(a)

Such decorator function can also have additional parameters.

.. code-block:: python

    class MyProvider(Provider):
        @decorate
        def decorate_a(self, a: A, b: B) -> A:
            return ADecorator(a)

The limitation is that you cannot use ``decorate`` in the same provider as you declare factory or alias for dependency. But you won't need it because you can update the factory code.

The idea of ``decorate`` is to postprocess dependencies provided by some external source, when you combine multiple ``Provider`` objects into one container