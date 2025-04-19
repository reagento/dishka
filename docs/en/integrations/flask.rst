.. _flask:

Flask
===========================================

Though it is not required, you can use ``dishka-flask`` integration. It features:

* automatic *REQUEST* scope management using middleware
* passing ``Request`` object as a context data to providers for **HTTP** requests
* automatic injection of dependencies into handler function


How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.flask import (
        FlaskProvider,
        FromDishka,
        inject,
        setup_dishka,
    )
    from dishka import make_container, Provider, provide, Scope

2. Create provider. You can use ``flask.Request`` as a factory parameter to access HTTP or Websocket request.
It is available on ``REQUEST`` scope.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    @router.get('/')
    async def endpoint(
        gateway: FromDishka[Gateway],
    ):
        ...

3a. *(optional)* decorate them using ``@inject``

.. code-block:: python

    @router.get('/')
    @inject
    async def endpoint(
        gateway: FromDishka[Gateway],
    ) -> Response:
        ...


4. *(optional)* Use ``FlaskProvider()`` when creating container if you are going to use ``flask.Request`` in providers.

.. code-block:: python

    container = make_container(YourProvider(), FlaskProvider())

5. Setup dishka integration. ``auto_inject=True`` is required unless you explicitly use ``@inject`` decorator. It is important here to call it after registering all views and blueprints.

.. code-block:: python

    setup_dishka(container=container, app=app, auto_inject=True)
