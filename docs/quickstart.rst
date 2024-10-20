Quickstart
********************

1. Install dishka

.. code-block:: shell

    pip install dishka

2. Write your classes, fill type hints. Imagine, you have two classes: Service (kind of business logic) and DAO (kind of data access) and some external api client:

.. code-block:: python

    class DAO(Protocol):
        ...

    class Service:
        def __init__(self, dao: DAO):
            ...

    class DAOImpl(DAO):
        def __init__(self, connection: Connection):
            ...

    class SomeClient:
        ...

4. Create Provider instance. It is only used to setup all factories providing your objects.

.. code-block:: python

    from dishka import Provider

    provider = Provider()


5. Setup how to provide dependencies.

We use ``scope=Scope.APP`` for dependencies which are created only once in application lifetime,
and ``scope=Scope.REQUEST`` for those which should be recreated for each processing request/event/etc.
To read more about scopes, refer :ref:`scopes`

.. code-block:: python

    from dishka import Provider, Scope

    service_provider = Provider(scope=Scope.REQUEST)
    service_provider.provide(Service)
    service_provider.provide(DAOImpl, provides=DAO)
    service_provider.provide(SomeClient, scope=Scope.APP)  # override provider scope

To provide connection we might need to write some custom code:

.. code-block:: python

    from dishka import Provider, provide, Scope

    class ConnectionProvider(Provider):
        @provide(Scope=Scope.REQUEST)
        def new_connection(self) -> Connection:
            conn = sqlite3.connect()
            yield conn
            conn.close()


6. Create main ``Container`` instance passing providers, and step into ``APP`` scope.

.. code-block:: python

   from dishka import make_container

    container = make_container(service_provider, ConnectionProvider())

7. Container holds dependencies cache and is used to retrieve them. Here, you can use ``.get`` method to access APP-scoped dependencies:

.. code-block:: python

   client = container.get(SomeClient)  # `SomeClient` has Scope.APP, so it is accessible here
   client = container.get(SomeClient)  # same instance of `SomeClient`


8. You can enter and exit ``REQUEST`` scope multiple times after that using context manager:

.. code-block:: python

   # subcontainer to access more short-living objects
    with container() as request_container:
        service = request_container.get(Service)
        service = request_container.get(Service)  # same service instance
    # at this point connection will be closed as we exited context manager

    # new subcontainer to have a new lifespan for request processing
    with container() as request_container:
        service = request_container.get(Service)  # new service instance


9. Close container in the end:

.. code-block:: python

   container.close()


10. If you are using supported framework add decorators and middleware for it.
For more details see :ref:`integrations`

.. code-block:: python

    from dishka.integrations.fastapi import (
        FromDishka, inject, setup_dishka,
    )

    @router.get("/")
    @inject
    async def index(service: FromDishka[Service]) -> str:
        ...

    ...
    setup_dishka(container, app)