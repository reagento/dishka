.. _provide:

provide
******************

``provide`` function is used to declare a factory providing a dependency. It can be used with some class or as a method decorator (either sync or async). It supports finalization of dependency if you make it a generator.

Provider object has also a ``.provide`` method with the same logic.

If it is used with class, it analyzes its ``__init__`` typehints to detect its dependencies. If it is used with a method, it checks its parameters typehints and a result type. Last one describes what this method is used to create.

``scope`` argument is required to define the lifetime of the created object.
By default the result is cached within scope. You can disable it providing ``cache=False`` argument.

* For simple case add method and mark it with ``@provide`` decorator:

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_service(self) -> Service:
            return Service()

* Want some finalization when exiting the scope? Make that method a generator:

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_db_session(self) -> Iterable[Session]:
            session = create_session()
            yield session
            session.close()

Also, if an error occurs during process handling (inside the ``with`` block), it will be sent to the generator:

.. code-block:: python

  class MyProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def get_connection(self) -> Iterable[Connection]:
            conn = create_connection()
            exc = yield conn
            # exc will be None if an exception has not occurred
            if exc:
                conn.rollback()
                print("Some exception while process handling: ", exc)
            conn.close()  # finally

* Haven't got any specific logic and just want to create class using its ``__init__``? Then add a provider attribute using ``provide`` as function passing that class.

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
        service = provide(Service, scope=Scope.REQUEST)

* Want to create a child class instance when parent is requested? Add a ``source`` attribute to ``provide`` function with a parent class while passing child as a source

.. code-block:: python

    from dishka import provide, Provider, Scope

    class UserGateway(Protocol): ...
    class UserGatewayImpl(UserGateway): ...

    class MyProvider(Provider):
        a = provide(source=UserGatewayImpl, scope=Scope.REQUEST, provides=UserGateway)


* Want to go ``async``? Make provide methods asynchronous, create async container and then use ``async with`` and await ``get`` calls:

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
       @provide(scope=Scope.APP)
       async def get_connection(self) -> Connection:
          return await create_connection()

    container = make_async_container(MyProvider())
    conn = await container.get(Connection)

* Tired of providing ``scope=`` for each dependency? Set it inside your ``Provider`` class and all factories with no scope will use it:

.. code-block:: python

    from dishka import provide, Provider, Scope

    class MyProvider(Provider):
       scope = Scope.APP

       @provide  # uses provider scope
       def get_id_generator(self) -> IDGenerator:
          return create_uuid_generator()

       @provide(scope=Scope.REQUEST)  # has own scope
       def get_user_gateway(self) -> UserGateway:
          return UserGatewayImpl()

* Having multiple interfaces which can be created as a same class? Use ``AnyOf`` as a result hint:

.. code-block:: python

    from dishka import AnyOf, provide, Provider, Scope

    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_user_gateway(self) -> AnyOf[UserGateway, UserGatewayImpl]:
            return UserGatewayImpl()

It works similar to :ref:`alias`.

* Do you want to get dependencies by parent classes too? Use ``WithParents`` as a result hint:

.. code-block:: python

    from dishka import WithParents, provide, Provider, Scope, make_container

    class UserReader(Protocol): ...
    class UserWriter(Protocol): ...
    class UserGatewayImpl(UserReader, UserWriter): ...

    class MyProvider(Provider):
        @provide(scope=Scope.APP)  # should be REQUEST, but set to APP for the sake of simplicity
        def get_user_gateway(self) -> WithParents[UserGatewayImpl]:
            return UserGatewayImpl()

    container = make_container(MyProvider())
    reader = container.get(UserReader)
    writer = container.get(UserWriter)
    impl = container.get(UserGatewayImpl)
    reader is impl and writer is impl  # True


WithParents generates only one factory and many aliases and is equivalent to ``AnyOf[AImpl, A]``. The following parents are ignored: ``type``, ``object``, ``Enum``, ``ABC``, ``ABCMeta``, ``Generic``, ``Protocol``, ``Exception``, ``BaseException``.

* Your object's dependencies (and their dependencies) can be simply created by calling their constructors. You do not need to register them manually. Use ``recursive=True`` to register them automatically:

.. code-block:: python

    @dataclass
    class APISettings:
        api_key: str
        rate_limit: int

    class ExternalAPIClient(Protocol): ...
    class ExternalAPIClientImpl(UserGateway):
        def __init__(self, settings: APISettings): ...

    class MyProvider(Provider):
        external_api_client = provide(
            ExternalAPIClientImpl,
            provides=ExternalAPIClient,
            scope=Scope.REQUEST,
            recursive=True
        )


* Do you want to override the factory? To do this, specify the parameter ``override=True``. This can be checked when passing proper ``validation_settings`` when creating container:

.. code-block:: python

    from dishka import provide, Provider, Scope, make_container

    class UserGateway(Protocol): ...
    class UserGatewayImpl(UserGateway): ...
    class UserGatewayMock(UserGateway): ...

    class MyProvider(Provider):
        scope = Scope.APP

        user_gateway = provide(UserGatewayImpl, provides=UserGateway)
        user_gateway_mock = provide(
            UserGatewayMock, provides=UserGateway, override=True
        )

    container = make_container(MyProvider())
    gateway = container.get(UserGateway)  # UserGatewayMock


* You can use factory with Generic classes:

.. code-block:: python

    class MyProvider(Provider):
        @provide
        def make_a(self, type_: type[T]) -> A[T]:
            ...

