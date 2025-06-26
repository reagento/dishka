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

    class UserDAO(Protocol): ...
    class UserDAOImpl(UserDAO): ...

    class MyProvider(Provider):
        user_dao = provide(source=UserDAOImpl, scope=Scope.REQUEST, provides=UserDAO)


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
       def get_user_dao(self) -> UserDAO:
          return UserDAOImpl()

* Having multiple interfaces which can be created as a same class? Use ``AnyOf`` as a result hint:

.. code-block:: python

    from dishka import AnyOf, provide, Provider, Scope

    class MyProvider(Provider):
        scope = Scope.APP

        @provide
        def get_user_dao(self) -> AnyOf[UserDAO, UserDAOImpl]:
            return UserDAOImpl()

It works similar to :ref:`alias`.

* Do you want to get dependencies by parent classes too? Use ``WithParents`` as a result hint:

.. code-block:: python

    from dishka import WithParents, provide, Provider, Scope, make_container

    class UserReader(Protocol): ...
    class UserWriter(Protocol): ...
    class UserDAOImpl(UserReader, UserWriter): ...

    class MyProvider(Provider):
        @provide(scope=Scope.APP)  # should be REQUEST, but set to APP for the sake of simplicity
        def get_user_dao(self) -> WithParents[UserDAOImpl]:
            return UserDAOImpl()

    container = make_container(MyProvider())
    reader = container.get(UserReader)
    writer = container.get(UserWriter)
    impl = container.get(UserDAOImpl)
    reader is impl and writer is impl  # True


WithParents generates only one factory and many aliases and is equivalent to ``AnyOf[AImpl, A]``. The following parents are ignored: ``type``, ``object``, ``Enum``, ``ABC``, ``ABCMeta``, ``Generic``, ``Protocol``, ``Exception``, ``BaseException``.

* Your object's dependencies (and their dependencies) can be simply created by calling their constructors. You do not need to register them manually. Use ``recursive=True`` to register them automatically:

.. code-block:: python

    @dataclass
    class APISettings:
        api_key: str
        rate_limit: int

    class ExternalAPIClient(Protocol): ...
    class ExternalAPIClientImpl(UserDAO):
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

    class UserDAO(Protocol): ...
    class UserDAOImpl(UserDAO): ...
    class UserDAOMock(UserDAO): ...

    class MyProvider(Provider):
        scope = Scope.APP

        user_dao = provide(UserDAOImpl, provides=UserDAO)
        user_dao_mock = provide(
            UserDAOMock, provides=UserDAO, override=True
        )

    container = make_container(MyProvider())
    dao = container.get(UserDAO)  # UserDAOMock


* You can use factory with Generic classes:

.. code-block:: python

    class MyProvider(Provider):
        @provide
        def make_a(self, type_: type[T]) -> A[T]:
            ...

