.. _aiogram:

aiogram
===========================================

Though it is not required, you can use *dishka-aiogram* integration. It features:

* automatic *REQUEST* scope management using middleware
* passing ``TelegramObject`` object and ``AiogramMiddlewareData`` dict as a context data to providers for telegram events (update object fields)
* automatic injection of dependencies into handler function.

Only async handlers are supported.

How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.aiogram import (
        AiogramProvider,
        FromDishka,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``aiogram.types.TelegramObject`` and ``dishka.integrations.aiogram.AiogramMiddlewareData`` as a factory parameter to access on *REQUEST*-scope

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, event: TelegramObject, middleware_data: AiogramMiddlewareData) -> X:
             ...


3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    @dp.message()
    async def start(
        message: Message,
        gateway: FromDishka[Gateway],
    ):


3a. *(optional)* decorate them using ``@inject`` if you are not using auto-injection

.. code-block:: python

    @dp.message()
    @inject
    async def start(
        message: Message,
        gateway: FromDishka[Gateway],
    ):


4. *(optional)* Use ``AiogramProvider()`` when creating container if you are going to use ``aiogram.types.TelegramObject`` or ``dishka.integrations.aiogram.AiogramMiddlewareData`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), AiogramProvider())


5. Setup ``dishka`` integration. ``auto_inject=True`` is required unless you explicitly use ``@inject`` decorator

.. code-block:: python

    setup_dishka(container=container, router=dp, auto_inject=True)


6. *(optional)* Close container on dispatcher shutdown

.. code-block:: python

    dispatcher.shutdown.register(container.close)

