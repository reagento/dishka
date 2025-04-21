.. _alias:

alias
****************

``alias`` is used to allow retrieving of the same object by different type hints. E.g. you have configured how to provide ``A`` object and want to use it as AProtocol: ``container.get(A)==container.get(AProtocol)``.

Provider object has also a ``.alias`` method with the same logic.

.. code-block:: python

    from dishka import alias, provide, Provider, Scope

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_a(self) -> A:
            return A()

        a_proto = alias(source=A, provides=AProtocol)

Additionally, alias has own setting for caching: it caches by default regardless if source is cached. You can disable it providing ``cache=False`` argument.

Do you want to override the alias? To do this, specify the parameter ``override=True``. This can be checked when passing proper ``validation_settings`` when creating container.

.. code-block:: python

    from dishka import provide, Provider, Scope, alias, make_container

    class MyProvider(Provider):
        scope=Scope.APP
        get_int = provide(int)
        get_float = provide(float)

        a_alias = alias(int, provides=complex)
        a_alias_override = alias(float, provides=complex, override=True)

    container = make_container(MyProvider())
    a = container.get(complex)  # 0.0
