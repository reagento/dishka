.. _aiohttp:

aiohttp
===========================================

Though it is not required, you can use dishka-aiohttp integration. It features:

* automatic REQUEST and SESSION scope management using middleware
* passing ``Request`` object as a context data to providers for both **Websockets** and **HTTP** requests
* automatic injection of dependencies into handler function


How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.aiohttp import (
        DISHKA_CONTAINER_KEY,
        FromDishka,
        inject,
        setup_dishka,
        AiohttpProvider,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``aiohttp.web.Request`` as a factory parameter to access HTTP or Websocket request.
It is available on ``SESSION`` and ``REQUEST`` scopes.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    @router.get('/')
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...

3a. *(optional)* decorate them using ``@inject``

.. code-block:: python

    @router.get('/')
    @inject
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...


4. *(optional)* Use ``AiohttpProvider()`` when creating container if you are going to use ``aiohttp.web.Request`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), AiohttpProvider())

5. Setup dishka integration. ``auto_inject=True`` is required unless you explicitly use ``@inject`` decorator

.. code-block:: python

    setup_dishka(container=container, app=app, auto_inject=True)


6. *(optional)* Close container on app termination

.. code-block:: python

    async def on_shutdown(app: Application):
        await app[DISHKA_CONTAINER_KEY].close()

    app.on_shutdown.append(on_shutdown)

Websockets
**********************

.. include:: _websockets.rst

In aiohttp your view function is called once per connection and then you retrieve messages in loop.
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

        async for message in weboscket:
            # enter the nested scope, which is Scope.REQUEST
            async with container() as request_container:
                b = await request_container.get(B)  # object with Scope.REQUEST
