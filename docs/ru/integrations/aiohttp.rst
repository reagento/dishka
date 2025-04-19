.. _ru-aiohttp:

aiohttp
===========================================

Хотя это и не обязательно, вы можете использовать интеграцию ``dishka-aiohttp``. Она предоставляет следующие возможности:

* Автоматическое управление областями видимости *REQUEST* и *SESSION* с помощью middleware.
* Передача объекта ``Request`` как контекстных данных в провайдеры для *WebSocket* и *HTTP*-запросов.
* Автоматическое внедрение зависимостей в функцию-обработчик.

Как использовать
*******************

1. Импорт

..  code-block:: python

    from dishka.integrations.aiohttp import (
        DISHKA_CONTAINER_KEY,
        FromDishka,
        inject,
        setup_dishka,
        AiohttpProvider,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Создание провайдера. Можно использовать ``aiohttp.web.Request`` в качестве параметра фабрики для доступа к HTTP или Websocket запросу.
Доступно для областей видимости (scopes) ``SESSION`` и ``REQUEST``.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. Помечайте параметры ваших обработчиков, которые должны быть внедрены, с помощью ``FromDishka[]``.

.. code-block:: python

    @router.get('/')
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...

3a. *(опционально)* Декорируйте их с помощью ``@inject``.

.. code-block:: python

    @router.get('/')
    @inject
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...

4. *(опционально)* Используйте ``AiohttpProvider()`` при создании контейнера, если вы собираетесь использовать ``aiohttp.web.Request`` в провайдерах.

.. code-block:: python

    container = make_async_container(YourProvider(), AiohttpProvider())

5. Настройте интеграцию ``dishka``. ``auto_inject=True`` требуется, если вы не используете декоратор ``@inject`` явно.

.. code-block:: python

    setup_dishka(container=container, app=app, auto_inject=True)

6. *(опционально)* Закройте контейнер при завершении работы приложения.

.. code-block:: python

    async def on_shutdown(app: Application):
        await app[DISHKA_CONTAINER_KEY].close()

    app.on_shutdown.append(on_shutdown)

Веб-сокеты (Websockets)
**************************

.. include:: _websockets.rst

В aiohttp ваша функция представления вызывается один раз per соединение, а затем вы получаете сообщения в цикле.
Таким образом, декоратор ``inject`` можно использовать только для получения объектов с областью видимости SESSION.
Чтобы добиться области видимости *REQUEST*, вы можете войти в неё вручную.

.. code-block:: python

    @inject
    async def get_with_request(
        request: Request,
        a: FromDishka[A],  # some object with Scope.SESSION
        container: FromDishka[AsyncContainer],  # container for Scope.SESSION
    ) -> web.WebsocketResponse:
        websocket = web.WebsocketResponse()
        await websocket.prepare(request)

        async for message in websocket:
            # enter the nested scope, which is Scope.REQUEST
            async with container() as request_container:
                b = await request_container.get(B)  # object with Scope.REQUEST
