.. _litestar:

Litestar
===========================================

Though it is not required, you can use dishka-litestar integration. It features:

* automatic REQUEST scope management using middleware
* passing ``Request`` object as a context data to providers for **HTTP** requests
* injection of dependencies into handler function using decorator


How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.litestar import (
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


3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]`` and decorate them using ``@inject``

.. code-block:: python

    @router.get('/')
    @inject
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
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

    app = Litestar([endpoint], lifespan=[lifespan])


6. Setup dishka integration. ``autoinject=True`` is required unless you explicitly use ``@inject`` decorator

.. code-block:: python

    setup_dishka(container=container, app=app)


Websockets
**********************

Not supported yet
