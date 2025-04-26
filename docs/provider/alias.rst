.. _alias:

alias
****************

``alias`` is used to allow retrieving of the same object by different type hints. E.g. you have configured how to provide ``A`` object and want to use it as AProtocol: ``container.get(A)==container.get(AProtocol)``.

Provider object has also a ``.alias`` method with the same logic.

.. code-block:: python

    from dishka import alias, provide, Provider, Scope

    class UserGateway(Protocol): ...
    class UserGatewayImpl(UserGateway): ...

    class MyProvider(Provider):
        user_gateway = provide(UserGatewayImpl, scope=Scope.REQUEST)
        user_gateway_proto = alias(source=UserGatewayImpl, provides=UserGateway)

Additionally, alias has own setting for caching: it caches by default regardless if source is cached. You can disable it providing ``cache=False`` argument.

Do you want to override the alias? To do this, specify the parameter ``override=True``. This can be checked when passing proper ``validation_settings`` when creating container.

.. code-block:: python

    from dishka import provide, Provider, Scope, alias, make_container

    class UserGateway(Protocol): ...
    class UserGatewayImpl(UserGateway): ...
    class UserGatewayMock(UserGateway): ...

    class MyProvider(Provider):
        scope = Scope.APP  # should be REQUEST, but set to APP for the sake of simplicity

        user_gateway = provide(UserGatewayImpl)
        user_gateway_mock = provide(UserGatewayMock)

        user_gateway_proto = alias(UserGatewayImpl, provides=UserGateway)
        user_gateway_override = alias(
            UserGatewayMock, provides=UserGateway, override=True
        )

    container = make_container(MyProvider())
    gateway = container.get(UserGateway)  # UserGatewayMock
