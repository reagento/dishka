Quickstart
********************

1. **Install dishka**

.. code-block:: shell

    pip install dishka

2. **Define classes with type hints.** Let's have the ``Service`` class (business logic) that has
two infrastructure dependencies: ``APIClient`` and ``UserDAO``. ``UserDAO`` is implemented in
``SQLiteUserDAO`` that has its own dependency - ``sqlite3.Connection``.

We want to create an ``APIClient`` instance once during the application's lifetime
and create ``UserDAO`` implementation instances on every request (event) our application handles.

.. code-block:: python

    from sqlite3 import Connection
    from typing import Protocol


    class APIClient:
        ...


    class UserDAO(Protocol):
        ...


    class SQLiteUserDAO(UserDAO):
        def __init__(self, connection: Connection):
            ...


    class Service:
        def __init__(self, client: APIClient, user_dao: UserDAO):
            ...

3. **Create providers** and specify how to provide dependencies.

Providers are used to set up factories for your objects.
To learn more about providers, see :ref:`provider`.

Use ``Scope.APP`` for dependencies that should be created once for the entire application lifetime,
and ``Scope.REQUEST`` for those that should be created for each request, event, etc.
To learn more about scopes, see :ref:`scopes`.

There are multiple options for registering dependencies. We will use:

* class (for ``Service`` and ``APIClient``)
* specific interface implementation (for ``UserDAO``)
* custom factory with finalization (for ``Connection``, as we want to make it releasable)

.. code-block:: python

    import sqlite3
    from collections.abc import Iterable
    from sqlite3 import Connection

    from dishka import Provider, Scope, provide

    service_provider = Provider(scope=Scope.REQUEST)
    service_provider.provide(Service)
    service_provider.provide(SQLiteUserDAO, provides=UserDAO)
    service_provider.provide(APIClient, scope=Scope.APP)  # override provider's scope


    class ConnectionProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def new_connection(self) -> Iterable[Connection]:
            connection = sqlite3.connect(":memory:")
            yield connection
            connection.close()

4. **Create a container**, passing providers. You can combine as many providers as needed.

Containers hold a cache of dependencies and are used to retrieve them.
To learn more about containers, see :ref:`container`.

.. code-block:: python

    from dishka import make_container


    container = make_container(service_provider, ConnectionProvider())

5. **Access dependencies using the container.**

Use the ``.get()`` method to access *APP*-scoped dependencies.
It is safe to request the same dependency multiple times.

.. code-block:: python

    # APIClient is bound to Scope.APP, so it can be accessed here
    # or from any scope inside including Scope.REQUEST
    client = container.get(APIClient)
    client = container.get(APIClient)  # the same APIClient instance as above

To access the *REQUEST* scope (sub-container) and its dependencies, use a context manager.
Higher level scoped dependencies are also available from sub-containers, e.g. ``APIClient``.

.. code-block:: python

    # A sub-container to access shorter-living objects
    with container() as request_container:
        # Service, UserDAO implementation, and Connection are bound to Scope.REQUEST,
        # so they are accessible here. APIClient can also be accessed here
        service = request_container.get(Service)
        service = request_container.get(Service)  # the same Service instance as above

    # Since we exited the context manager, the sqlite3 connection is now closed

    # A new sub-container has a new lifespan for request processing
    with container() as request_container:
        service = request_container.get(Service)  # a new Service instance

6. **Close the container** when done.

.. code-block:: python

    container.close()

.. dropdown:: Full example

   .. literalinclude:: ./quickstart_example.py
      :language: python

7. **(optional) Integrate with your framework.** If you are using a supported framework, add decorators and middleware for it.
   For more details, see :ref:`integrations`.

.. code-block:: python

    from fastapi import APIRouter, FastAPI
    from dishka import make_async_container
    from dishka.integrations.fastapi import (
        FastapiProvider,
        FromDishka,
        inject,
        setup_dishka,
    )

    app = FastAPI()
    router = APIRouter()
    app.include_router(router)
    container = make_async_container(
        service_provider,
        ConnectionProvider(),
        FastapiProvider(),
    )
    setup_dishka(container, app)


    @router.get("/")
    @inject
    async def index(service: FromDishka[Service]) -> str:
        ...
