.. _alias:

@alias
****************

``alias`` is used to allow retrieving of the same object by different type hints. E.g. you have configure how to provide ``A`` object and want to use it as AProtocol: ``container.get(A)==container.get(AProtocol)``.

.. code-block:: python

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> A:
            return A()

        a_proto = alias(source=A, provides=AProtocol)

Additionally, alias has own setting for caching: it caches by default regardless if source is cached. You can disable it providing ``cache=False`` argument.