.. _faststream:

FastStream
===========================================

Though it is not required, you can use dishka-faststream integration. It features:

* automatic REQUEST scope management using middleware
* passing ``StreamMessage`` and ``ContextRepo`` object as a context data to providers
* automatic injection of dependencies into message handler

You can use auto-injection for FastStream 0.5.0 and higher. For older version you need to specify ``@inject`` manually.

.. note::

    If you are using **FastAPI plugin** of **FastStream** you need to use both dishka integrations, but you can share the same container.

    * Call ``dishka.integrations.faststream.setup_dishka`` on faststream broker or router
    * Call ``dishka.integrations.fastapi.setup_dishka`` on fastapi app.



How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.faststream import (
        FromDishka,
        inject,
        setup_dishka,
        FastStreamProvider,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``faststream.types.StreamMessage`` and ``faststream.ContextRepo`` as a factory parameter to access on REQUEST-scope

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, event: StreamMessage) -> X:
             ...


3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    @broker.subscriber("test")
    async def start(
        gateway: FromDishka[Gateway],
    ):
        ...


3a. *(optional)* decorate them using ``@inject`` if you are not using auto-injection

.. code-block:: python

    @broker.subscriber("test")
    @inject
    async def start(
        gateway: FromDishka[Gateway],
    ):
        ...


4. *(optional)* Use ``FastStreamProvider()`` when creating container if you are going to use  ``faststream.types.StreamMessage`` or ``faststream.ContextRepo``  in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), FastStreamProvider())


5. Setup dishka integration.  ``auto_inject=True`` is required unless you explicitly use ``@inject`` decorator.

.. code-block:: python

    setup_dishka(container=container, app=app, auto_inject=True)

