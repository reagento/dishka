.. _ru-litestar:

Litestar
===========================================

Хотя это и не обязательно, вы можете использовать интеграцию ``dishka-litestar``. Она предоставляет следующие возможности:

* автоматическое управление областью *REQUEST* с помощью middleware
* передача объекта Request в качестве контекстных данных провайдерам для **HTTP**-запросов
* внедрение зависимостей в функцию-обработчик с помощью декоратора

Как использовать
********************

1. Импорт

..  code-block:: python

    from dishka.integrations.litestar import (
        FromDishka,
        LitestarProvider,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Создайте провайдер. Вы можете использовать ``litestar.Request`` как параметр фабрики для доступа в области *REQUEST*

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

3. Помечайте параметры ваших обработчиков, которые должны быть внедрены, с помощью ``FromDishka[]`` и декорируйте их с помощью ``@inject``

.. code-block:: python

    @router.get('/')
    @inject
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...

4. *(опционально)* Используйте ``LitestarProvider()`` при создании контейнера, если вы планируете использовать ``litestar.Request`` в провайдерах.

.. code-block:: python

    container = make_async_container(YourProvider(), LitestarProvider())

5. *(опционально)* Настройте lifespan для закрытия контейнера при завершении работы приложения

.. code-block:: python

    @asynccontextmanager
    async def lifespan(app: Litestar):
        yield
        await app.state.dishka_container.close()

    app = Litestar([endpoint], lifespan=[lifespan])


6. Настройте интеграцию ``dishka``.

.. code-block:: python

    setup_dishka(container=container, app=app)


Веб-сокеты (Websockets)
*************************

.. include:: _websockets.rst

В litestar ваша функция-обработчик вызывается один раз для каждого события,
и нет возможности определить, является ли это HTTP- или websocket-обработчик.
Поэтому для websocket-обработчиков следует использовать специальный декоратор ``inject_websocket``.
Также декоратор может использоваться только для получения объектов с областью *SESSION*.
Для достижения области *REQUEST* вы можете войти в неё вручную:

.. code-block:: python

    @websocket_listener("/")
    @inject_websocket
    async def get_with_request(
        a: FromDishka[A],  # object with Scope.SESSION
        container: FromDishka[AsyncContainer],  # container for Scope.SESSION
        data: dict[str, str]
    ) -> dict[str, str]:
        # enter the nested scope, which is Scope.REQUEST
        async with container() as request_container:
            b = await request_container.get(B)  # object with Scope.REQUEST
        return {"key": "value"}

или с классом-обработчиком:

.. code-block:: python

    class Handler(WebsocketListener):
        path = "/"

        @inject_websocket
        async def on_receive(
            a: FromDishka[A],  # object with Scope.SESSION
            container: FromDishka[AsyncContainer],  # container for Scope.SESSION
            data: dict[str, str]
        ) -> dict[str, str]:
            async with container() as request_container:
                b = await request_container.get(B)  # object with Scope.REQUEST
            return {"key": "value"}
