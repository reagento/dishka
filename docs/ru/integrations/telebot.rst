.. _ru-telebot:

pyTelegramBotAPI
===========================================

Несмотря на то, что это не является обязательным, вы можете использовать интеграцию ``dishka-pyTelegramBotAPI``. Она включает следующие возможности:

* автоматическое управление областью видимости *REQUEST* с помощью middleware
* передачу объекта ``dishka.integrations.telebot.TelebotEvent`` в качестве контекстных данных провайдерам для событий Telegram (поля объекта update)
* внедрение зависимостей в функции обработчиков с помощью декоратора

Поддерживаются только синхронные обработчики.

Как использовать
********************

1. Импорт

..  code-block:: python

    from dishka.integrations.telebot import (
        FromDishka,
        inject,
        setup_dishka,
        TelebotProvider,
        TelebotEvent,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Создайте провайдер. Вы можете использовать ``dishka.integrations.telebot.TelebotEvent`` как параметр фабрики для доступа к данным в области видимости *REQUEST*.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, event: TelebotEvent) -> X:
             ...

3. Пометьте те параметры ваших обработчиков, которые должны быть внедрены, используя ``FromDishka[]``, и примените к ним декоратор ``@inject``

.. code-block:: python

    @bot.message()
    @inject
    def start(
        message: Message,
        gateway: FromDishka[Gateway],
    ):

4. *(опционально)* Используйте ``TelebotProvider()`` при создании контейнера, если вы планируете использовать ``dishka.integrations.telebot.TelebotEvent`` в провайдерах.

.. code-block:: python

    container = make_async_container(YourProvider(), TelebotProvider())


5. Настройте интеграцию ``dishka``.

.. code-block:: python

    setup_dishka(container=container, bot=bot)

