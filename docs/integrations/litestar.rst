.. _litestar:

Litestar
===========================================

Though it is not required, you can use dishka-litestar integration. It features:

* automatic REQUEST and SESSION scope management using middleware
* passing ``Request`` object as a context data to providers for both **Websockets** and **HTTP** requests
* automatic injection of dependencies into handler function


How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.litestar import (
        DishkaRoute,
        FromDishka,
        LitestarProvider,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``litestar.Request`` as a factory parameter to access on REQUEST-scope

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. *(optional)* Set route class to each of your litestar routers to enable autoinjection (it works only for HTTP, not for websockets).

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


4. *(optional)* Use ``LitestarProvider()`` when creating container if you are going to use ``litestar.Request`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), LitestarProvider())


5. *(optional)* Setup lifespan to close container on app termination

.. code-block:: python

    @asynccontextmanager
    async def lifespan(app: Litestar):
        yield
        await app.state.dishka_container.close()

    app = Litestar(lifespan=lifespan)

5. Setup dishka integration. ``autoinject=True`` is required unless you explicitly use ``@inject`` decorator

.. code-block:: python

    setup_dishka(container=container, app=app)


Websockets
**********************

Not supported yet
