.. _ru-aiogram:

aiogram
===========================================

Хотя это и необязательно, вы можете использовать интеграцию dishka-aiogram. Она предоставляет следующие возможности:

* Автоматическое управление областью видимости *REQUEST* с помощью middleware.
* Передача объекта ``TelegramObject`` и словаря ``AiogramMiddlewareData`` как контекстных данных в провайдеры для обработки Telegram-событий (поля объекта update).
* Автоматическое внедрение зависимостей в функцию-обработчик.

Поддерживаются только асинхронные обработчики.

Как использовать
******************

1. Импортировать

..  code-block:: python

    from dishka.integrations.aiogram import (
        AiogramProvider,
        FromDishka,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Создать провайдер. Вы можете использовать ``aiogram.types.TelegramObject`` и ``dishka.integrations.aiogram.AiogramMiddlewareData`` в качестве параметров фабрики, чтобы получить доступ к данным в области видимости *REQUEST*

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, event: TelegramObject, middleware_data: AiogramMiddlewareData) -> X:
             ...

3. Помечайте параметры ваших обработчиков, которые должны быть внедрены, с помощью ``FromDishka[]``

.. code-block:: python

    @dp.message()
    async def start(
        message: Message,
        gateway: FromDishka[Gateway],
    ):

3a. *(опционально)* Декорируйте их с помощью ``@inject``, если не используете авто-внедрение.

.. code-block:: python

    @dp.message()
    @inject
    async def start(
        message: Message,
        gateway: FromDishka[Gateway],
    ):

4. *(опционально)* Используйте ``AiogramProvider()`` при создании контейнера, если планируете использовать ``aiogram.types.TelegramObject`` или ``dishka.integrations.aiogram.AiogramMiddlewareData`` в провайдерах.
.. code-block:: python

    container = make_async_container(YourProvider(), AiogramProvider())

5. Настройте интеграцию ``dishka``. ``auto_inject=True`` требуется, если вы не используете декоратор ``@inject`` явно.

.. code-block:: python

    setup_dishka(container=container, router=dp, auto_inject=True)

6. *(опционально)* Закрывайте контейнер при завершении работы диспетчера

.. code-block:: python

    dispatcher.shutdown.register(container.close)

