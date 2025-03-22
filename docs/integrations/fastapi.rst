.. _fastapi:

FastAPI
===========================================

Though it is not required, you can use dishka-fastapi integration. It features:

* automatic REQUEST and SESSION scope management using middleware
* passing ``Request`` object as a context data to providers for both **Websockets** and **HTTP** requests
* automatic injection of dependencies into handler function


How to use
****************

.. note::
    We suppose that you are using ``AsyncContainer`` with FastAPI.
    If it is not right and you are using sync ``Container``, the overall approach is the same,
    but there are few corrections, see :ref:`below<fastapi_sync>`.


1. Import

..  code-block:: python

    from dishka.integrations.fastapi import (
        DishkaRoute,
        FromDishka,
        FastapiProvider,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``fastapi.Request`` as a factory parameter to access on REQUEST-scope , and ``fastapi.WebSocket`` on ``SESSION`` scope.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. *(optional)* Set route class to each of your fastapi routers to enable automatic injection (it works only for HTTP, not for websockets).

.. code-block:: python

    router = APIRouter(route_class=DishkaRoute)

3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    @router.get('/')
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...

3a. *(optional)* decorate them using ``@inject`` if you are not using DishkaRoute or use websockets.

.. code-block:: python

    @router.get('/')
    @inject
    async def endpoint(
        gateway: FromDishka[Gateway],
    ) -> ResponseModel:
        ...


4. *(optional)* Use ``FastapiProvider()`` when creating container if you are going to use ``fastapi.Request`` or ``fastapi.WebSocket`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), FastapiProvider())


5. *(optional)* Setup lifespan to close container on app termination

.. code-block:: python

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await app.state.dishka_container.close()

    app = FastAPI(lifespan=lifespan)

5. Setup dishka integration.

.. code-block:: python

    setup_dishka(container=container, app=app)


Websockets
**********************

.. include:: _websockets.rst

In fastapi your view function is called once per connection and then you retrieve messages in loop.
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


Auto-injection is not available for websockets.

.. _fastapi_sync:

Using with sync Container
**********************************

If you are using sync ``Container``, created using ``make_container`` function, you should change severla things:

* use ``inject_sync`` instead of ``inject`` function.
* use ``DishkaSyncRoute`` instead if ``DishkaRoute`` if you are using autoinjection
* use ``Container`` in websocket handler instead of ``AsyncContainer`` and normal ``with`` instead of ``async with``


..  code-block:: python

    from dishka.integrations.fastapi import (
        FromDishka,
        FastapiProvider,
        inject_sync,
        setup_dishka,
    )
    from dishka import make_container, Provider, provide, Scope


    router = APIRouter()


    @router.get('/')
    @inject_sync
    def endpoint(
        gateway: FromDishka[Gateway],
    ) -> ResponseModel:
        ...


    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        app.state.dishka_container.close()

    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    container = make_container(YourProvider(), FastapiProvider())
    setup_dishka(container=container, app=app)