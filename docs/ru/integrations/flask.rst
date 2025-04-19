.. _ru-flask:

Flask
===========================================

Хотя это не обязательно, вы можете использовать интеграцию ``dishka-flask``. Она предоставляет следующие возможности:

* автоматическое управление областью видимости *REQUEST* с помощью middleware
* передачу объекта ``Request`` как контекстных данных в провайдеры для **HTTP**-запросов
* автоматическое внедрение зависимостей в обработчики (handler functions)

Как использовать
********************

1. Импорт

..  code-block:: python

    from dishka.integrations.flask import (
        FlaskProvider,
        FromDishka,
        inject,
        setup_dishka,
    )
    from dishka import make_container, Provider, provide, Scope

2. Создайте провайдер. Вы можете использовать ``flask.Request`` как параметр фабрики, чтобы получить доступ к HTTP-запросу.
Он доступен в области видимости ``REQUEST``.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. Помечайте параметры ваших обработчиков, которые должны быть внедрены, с помощью ``FromDishka[]``

.. code-block:: python

    @router.get('/')
    async def endpoint(
        gateway: FromDishka[Gateway],
    ):
        ...

3a. *(опционально)* Декорируйте их с помощью ``@inject``

.. code-block:: python

    @router.get('/')
    @inject
    async def endpoint(
        gateway: FromDishka[Gateway],
    ) -> Response:
        ...

4. *(опционально)* Используйте ``FlaskProvider()`` при создании контейнера, если вы собираетесь использовать ``flask.Request`` в провайдерах.

.. code-block:: python

    container = make_container(YourProvider(), FlaskProvider())

5. Настройте интеграцию ``dishka``. Параметр ``auto_inject=True`` обязателен, если вы не используете декоратор ``@inject`` явно.
Важно вызвать эту функцию после регистрации всех представлений (views) и blueprint'ов.

.. code-block:: python

    setup_dishka(container=container, app=app, auto_inject=True)
