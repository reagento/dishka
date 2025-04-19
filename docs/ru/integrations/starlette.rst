.. _ru-starlette:

Starlette
===========================================

Хотя это не обязательно, вы можете использовать интеграцию ``dishka-starlette``. Она предоставляет следующие возможности:

* Автоматическое управление областями видимости (scope) *REQUEST* и *SESSION* с помощью middleware
* Передача объекта ``Request`` как контекстных данных в провайдеры для **WebSocket** и **HTTP** запросов
* Автоматическое внедрение зависимостей в функцию-обработчик

Как использовать
********************

1. Импорт

..  code-block:: python

    from dishka.integrations.starlette import (
        DishkaRoute,
        FromDishka,
        StarletteProvider,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Создайте провайдер. Вы можете использовать ``starlette.requests.Request`` как параметр фабрики для доступа в области *REQUEST*, и ``starlette.websockets.WebSocket`` — в области *SESSION*.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. Помечайте параметры обработчиков, которые нужно внедрить, с помощью ``FromDishka[]`` и декорируйте их ``@inject``.

.. code-block:: python

    @inject
    async def endpoint(
        request: Request,
        *,
        gateway: FromDishka[Gateway],
    ) -> ResponseModel:
        ...

4. *(опционально)* Используйте ``StarletteProvider()`` при создании контейнера, если планируете использовать ``starlette.Request`` или ``starlette.WebSocket`` в провайдерах.

.. code-block:: python

    container = make_async_container(YourProvider(), StarletteProvider())


5. Настройте интеграцию ``dishka``.

.. code-block:: python

    setup_dishka(container=container, app=app)


Веб-сокеты (Websockets)
*************************

.. include:: _websockets.rst

В Starlette ваша функция-обработчик вызывается один раз при подключении, а затем вы получаете сообщения в цикле.
Таким образом, декоратор ``@inject`` можно использовать только для получения объектов с областью видимости *SESSION*.
Для работы с областью *REQUEST* вы можете войти в неё вручную.

.. code-block:: python

    @inject
    async def get_with_request(
        websocket: WebSocket,
        a: FromDishka[A],  # object with Scope.SESSION
        container: FromDishka[AsyncContainer],  # container for Scope.SESSION
    ) -> None:
        await websocket.accept()
        while True:
            data = await websocket.receive_text()
            # enter the nested scope, which is Scope.REQUEST
            async with container() as request_container:
                b = await request_container.get(B)  # object with Scope.REQUEST

