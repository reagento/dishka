.. _rapidy:

Rapidy
===========================================

Though it is not required, you can use dishka-rapidy integration. It features:

* automatic REQUEST scope management using middleware
* passing ``Request`` object as a context data to providers for **HTTP** requests
* injection of dependencies into handler function using decorator


How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.rapidy import (
        DISHKA_CONTAINER_KEY,
        FromDishka,
        LitestarProvider,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``rapidy.http.Request`` as a factory parameter to access on REQUEST-scope

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...


3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]`` and decorate them using ``@inject``

.. code-block:: python

    @router.get('/')
    @inject
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...


4. *(optional)* Use ``RapidyProvider()`` when creating container if you are going to use ``rapidy.http.Request`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), RapidyProvider())


5. *(optional)* Setup lifespan to close container on app termination

.. code-block:: python
    from dishka.integrations.rapidy import DISHKA_CONTAINER_KEY

    @asynccontextmanager
    async def lifespan(app: Rapidy):
        yield
        app[DISHKA_CONTAINER_KEY].close()

    app = Rapidy(..., lifespan=[lifespan])


6. Setup dishka integration.

.. code-block:: python

    setup_dishka(container=container, app=app)


Websockets
**********************

.. include:: _websockets.rst

Currently, the web socket logic in `Rapidy` is identical to `aiohttp`.

In rapidy your view function is called once per connection and then you retrieve messages in loop.
So, ``inject`` decorator can be only used to retrieve SESSION-scoped objects.
To achieve REQUEST-scope you can enter in manually:

.. code-block:: python

    @inject
    async def get_with_request(
        request: Request,
        a: FromDishka[A],  # some object with Scope.SESSION
        container: FromDishka[AsyncContainer],  # container for Scope.SESSION
    ) -> web.WebsocketResponse:
        websocket = web.WebsocketResponse()
        await websocket.prepare(request)

        async for message in websocket:
            # enter the nested scope, which is Scope.REQUEST
            async with container() as request_container:
                b = await request_container.get(B)  # object with Scope.REQUEST
