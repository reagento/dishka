.. _ru-fastapi:

FastAPI
===========================================

Хотя это и не обязательно, вы можете использовать интеграцию ``dishka-fastapi``. Она предлагает следующие возможности:

* Автоматическое управление областями (scope) *REQUEST* и *SESSION* с помощью middleware.
* Передача объекта ``Request`` как контекстных данных в провайдеры для **WebSocket** и **HTTP** запросов.
* Автоматическое внедрение зависимостей в обработчики функций.

Как использовать
********************

.. note::
    Предполагается, что вы используете ``AsyncContainer`` вместе с FastAPI.
    Если это не так и вы используете синхронный ``Container``, общий подход остается тем же,
    но есть несколько отличий — см. :ref:`below<ru-fastapi_sync>`.


1. Импорт

..  code-block:: python

    from dishka.integrations.fastapi import (
        DishkaRoute,
        FromDishka,
        FastapiProvider,
        inject,
        setup_dishka,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Создание провайдера. Можно использовать ``fastapi.Request`` как параметр фабрики для доступа в рамках *REQUEST*-скоупа и ``fastapi.WebSocket`` для *SESSION*-скоупа.

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, request: Request) -> X:
             ...

2a. *(опционально)* Установйте класс маршрута (route class) для каждого из ваших FastAPI роутеров, чтобы включить автоматическую инъекцию (работает только для HTTP, не для WebSocket).

.. code-block:: python

    router = APIRouter(route_class=DishkaRoute)

3. Помечайте параметры ваших обработчиков, которые должны быть внедрены, с помощью ``FromDishka[]``.

.. code-block:: python

    @router.get('/')
    async def endpoint(
        request: str, gateway: FromDishka[Gateway],
    ) -> Response:
        ...

3a. *(опционально)* Декорируйте их с помощью ``@inject``, если вы не используете DishkaRoute или работаете с WebSocket.

.. code-block:: python

    @router.get('/')
    @inject
    async def endpoint(
        gateway: FromDishka[Gateway],
    ) -> ResponseModel:
        ...


4. *(опционально)* Используйте ``FastapiProvider()`` при создании контейнера, если вы планируете использовать ``fastapi.Request`` или ``fastapi.WebSocket`` в провайдерах.

.. code-block:: python

    container = make_async_container(YourProvider(), FastapiProvider())

5. *(опционально)* Настройте lifespan для закрытия контейнера при завершении работы приложения.

.. code-block:: python

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        await app.state.dishka_container.close()

    app = FastAPI(lifespan=lifespan)

6. Настройте интеграцию ``dishka``.

.. code-block:: python

    setup_dishka(container=container, app=app)


Веб-сокеты (Websockets)
**************************

.. include:: _websockets.rst

Во FastAPI ваша функция-обработчик вызывается один раз за соединение, а затем сообщения обрабатываются в цикле.
Поэтому декоратор ``inject`` можно использовать только для получения объектов с областью видимости *SESSION*.

Чтобы работать с областью *REQUEST*, можно вручную войти в контекст:

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


Автоматическое внедрение зависимостей для WebSockets недоступно.

.. _ru-fastapi_sync:

Использование с синхронным Container
*********************************************

Если вы используете синхронный ``Container`, созданный через ``make_container``, нужно учесть несколько изменений:

* Используйте ``inject_sync`` вместо ``inject``.
* Если задействовано автоматическое внедрение, замените ``DishkaRoute`` на ``DishkaSyncRoute``.
* В обработчике WebSocket используйте ``Container`` вместо ``AsyncContainer`` и обычный ``with`` вместо ``async with``.

..  code-block:: python

    from dishka.integrations.fastapi import (
        FromDishka,
        FastapiProvider,
        inject_sync,
        setup_dishka,
    )
    from dishka import make_container, Provider, provide, Scope


    router = APIRouter()


    @router.get('/')
    @inject_sync
    def endpoint(
        gateway: FromDishka[Gateway],
    ) -> ResponseModel:
        ...


    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield
        app.state.dishka_container.close()

    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    container = make_container(YourProvider(), FastapiProvider())
    setup_dishka(container=container, app=app)