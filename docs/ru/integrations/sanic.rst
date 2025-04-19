.. _ru-sanic:

Sanic
===========================================

Хотя это не обязательно, вы можете использовать интеграцию ``dishka-sanic``. Она предоставляет следующие возможности:

* автоматическое управление областью видимости *REQUEST* с помощью middleware
* передачу объекта ``Request`` как контекстных данных в провайдеры для **HTTP**-запросов
* автоматическое внедрение зависимостей в функцию-обработчик

Как использовать
********************

1. Импорт

..  code-block:: python

    from dishka.integrations.sanic import (
        FromDishka,
        SanicProvider,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Создайте провайдер. Вы можете использовать ``sanic.Request`` как параметр фабрики для доступа в области видимости *REQUEST*

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. Пометьте параметры ваших обработчиков, которые должны быть внедрены, с помощью ``FromDishka[]``

.. code-block:: python

    @app.get('/')
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...

3a. *(опционально)* Декорируйте их с помощью ``@inject``, если не используете авто-внедрение

.. code-block:: python

    @app.get('/')
    @inject
    async def endpoint(
        gateway: FromDishka[Gateway],
    ) -> ResponseModel:
        ...

4. *(опционально)* Используйте ``SanicProvider()`` при создании контейнера, если планируете использовать ``sanic.Request`` в провайдерах.

.. code-block:: python

    container = make_async_container(YourProvider(), SanicProvider())

5. Настройте интеграцию ``dishka``. Параметр ``auto_inject=True`` обязателен, если вы не используете декоратор ``@inject`` явно.

.. code-block:: python

    setup_dishka(container=container, app=app, auto_inject=True)


Веб-сокеты (Websockets)
**************************

Ещё не поддерживается
