.. _sanic:

Sanic
===========================================

Though it is not required, you can use dishka-sanic integration. It features:

* automatic REQUEST scope management using middleware
* passing ``Request`` object as a context data to providers for **HTTP** requests
* automatic injection of dependencies into handler function


How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.sanic import (
        FromDishka,
        SanicProvider,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``sanic.Request`` as a factory parameter to access on REQUEST-scope

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...


3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    @app.get('/')
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...

3a. *(optional)* decorate them using ``@inject`` if you are not using auto-injection

.. code-block:: python

    @app.get('/')
    @inject
    async def endpoint(
        gateway: FromDishka[Gateway],
    ) -> ResponseModel:
        ...


4. *(optional)* Use ``SanicProvider()`` when creating container if you are going to use ``sanic.Request`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), SanicProvider())


6. Setup dishka integration. ``auto_inject=True`` is required unless you explicitly use ``@inject`` decorator

.. code-block:: python

    setup_dishka(container=container, app=app, auto_inject=True)


Websockets
**********************

Not supported yet
