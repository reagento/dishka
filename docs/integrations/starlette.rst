.. _starlette:

Starlette
===========================================

Though it is not required, you can use dishka-starlette integration. It features:

* automatic REQUEST and SESSION scope management using middleware
* passing ``Request`` object as a context data to providers for both **Websockets** and **HTTP** requests
* automatic injection of dependencies into handler function


How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.starlette import (
        DishkaRoute,
        FromDishka,
        StarletteProvider,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``starlette.requests.Request`` as a factory parameter to access on REQUEST-scope , and ``starlette.websockets.WebSocket`` on ``SESSION`` scope.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]`` and decorate them using ``@inject``.

.. code-block:: python

    @inject
    async def endpoint(
        request: Request,
        *,
        gateway: FromDishka[Gateway],
    ) -> ResponseModel:
        ...


4. *(optional)* Use ``StarletteProvider()`` when creating container if you are going to use ``starlette.Request`` or ``starlette.WebSocket`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), StarletteProvider())


5. Setup dishka integration.

.. code-block:: python

    setup_dishka(container=container, app=app)


Websockets
**********************

.. include:: _websockets.rst

In starlette your view function is called once per connection and then you retrieve messages in loop.
So, ``inject`` decorator can be only used to retrieve SESSION-scoped objects.
To achieve REQUEST-scope you can enter in manually:

.. code-block:: python

    @inject
    async def get_with_request(
        websocket: WebSocket,
        a: FromDishka[A],  # object with Scope.SESSION
        container: FromDishka[AsyncContainer],  # container for Scope.SESSION
    ) -> None:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            # enter the nested scope, which is Scope.REQUEST
            async with container() as request_container:
                b = await request_container.get(B)  # object with Scope.REQUEST

