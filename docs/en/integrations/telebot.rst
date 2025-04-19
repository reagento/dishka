.. _telebot:

pyTelegramBotAPI
===========================================

Though it is not required, you can use ``dishka-pyTelegramBotAPI`` integration. It features:

* automatic *REQUEST* scope management using middleware
* passing ``dishka.integrations.telebot.TelebotEvent`` object as a context data to providers for telegram events (update object fields)
* injection of dependencies into handler function using decorator

Only sync handlers are supported.

How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.telebot import (
        FromDishka,
        inject,
        setup_dishka,
        TelebotProvider,
        TelebotEvent,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``dishka.integrations.telebot.TelebotEvent`` as a factory parameter to access on *REQUEST*-scope

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, event: TelebotEvent) -> X:
             ...


3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]`` and decorate them using ``@inject``

.. code-block:: python

    @bot.message()
    @inject
    def start(
        message: Message,
        gateway: FromDishka[Gateway],
    ):


4. *(optional)* Use ``TelebotProvider()`` when creating container if you are going to use ``dishka.integrations.telebot.TelebotEvent`` in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), TelebotProvider())


5. Setup ``dishka`` integration.

.. code-block:: python

    setup_dishka(container=container, bot=bot)

