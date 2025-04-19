.. _ru-faststream:

FastStream
===========================================

Хотя это не обязательно, вы можете использовать интеграцию ``dishka-faststream``. Она предоставляет следующие возможности:

* Автоматическое управление областью видимости *REQUEST* через middleware.
* Передача объектов ``StreamMessage`` и ``ContextRepo`` в качестве контекстных данных для провайдеров.
* Автоматическое внедрение зависимостей в обработчики сообщений.

Автоматическое внедрение доступно для FastStream 0.5.0 и выше. Для более старых версий нужно вручную указывать ``@inject``.

.. note::

    Если вы используете **плагин FastAPI** в **FastStream**, вам потребуются обе интеграции ``dishka``, но можно использовать один контейнер.

    * Вызовите ``dishka.integrations.faststream.setup_dishka`` для брокера или роутера FastStream.
    * Вызовите ``dishka.integrations.fastapi.setup_dishka`` для FastAPI-приложения.


Как использовать
********************

1. Импорт

..  code-block:: python

    from dishka.integrations.faststream import (
        FromDishka,
        inject,
        setup_dishka,
        FastStreamProvider,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Создайте провайдер. Вы можете использовать ``faststream.types.StreamMessage`` и ``faststream.ContextRepo`` в качестве параметров фабрики для доступа в области *REQUEST*

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, event: StreamMessage) -> X:
             ...

3. Пометьте параметры обработчика, которые должны быть внедрены, с помощью ``FromDishka[]``

.. code-block:: python

    @broker.subscriber("test")
    async def start(
        gateway: FromDishka[Gateway],
    ):
        ...

3a. *(опционально)* Декорируйте обработчик ``@inject``, если не используете авто-внедрение:

.. code-block:: python

    @broker.subscriber("test")
    @inject
    async def start(
        gateway: FromDishka[Gateway],
    ):
        ...

4 *(опционально)*  Используйте ``FastStreamProvider()`` при создании контейнера, если планируете использовать ``faststream.types.StreamMessage`` или ``faststream.ContextRepo`` в провайдерах.

.. code-block:: python

    container = make_async_container(YourProvider(), FastStreamProvider())

5. Настройте интеграцию ``dishka`. Параметр ``auto_inject=True`` обязателен, если вы не используете декоратор ``@inject`` явно.

.. code-block:: python

    setup_dishka(container=container, broker=broker, auto_inject=True)


FastStream - Litestar/FastAPI - интеграция с dishka
*************************************************************

1. Запуск RabbitMQ

.. code-block:: shell

    docker run -d --name rabbitmq \
      -p 5672:5672 -p 15672:15672 \
      -e RABBITMQ_DEFAULT_USER=guest \
      -e RABBITMQ_DEFAULT_PASS=guest \
      rabbitmq:management

2. Пример использования FastStream + Litestar

.. code-block:: python

    import uvicorn
    from dishka import Provider, Scope, provide
    from dishka import make_async_container
    from dishka.integrations import faststream as faststream_integration
    from dishka.integrations import litestar as litestar_integration
    from dishka.integrations.base import FromDishka as Depends
    from dishka.integrations.faststream import inject as faststream_inject
    from dishka.integrations.litestar import inject as litestar_inject
    from faststream import FastStream
    from faststream.rabbit import RabbitBroker, RabbitRouter, RabbitRoute
    from litestar import Litestar, route, HttpMethod


    class SomeDependency:
        async def do_something(self) -> int:
            print("Hello world")
            return 42


    class SomeProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def some_dependency(self) -> SomeDependency:
            return SomeDependency()


    @route(http_method=HttpMethod.GET, path="/", status_code=200)
    @litestar_inject
    async def http_handler(some_dependency: Depends[SomeDependency]) -> None:
        await some_dependency.do_something()


    @faststream_inject
    async def amqp_handler(data: str, some_dependency: Depends[SomeDependency]) -> None:
        print(f"{data=}")
        await some_dependency.do_something()


    def create_app():
        container = make_async_container(SomeProvider())

        broker = RabbitBroker(
            url="amqp://guest:guest@localhost:5672/",
        )
        amqp_routes = RabbitRouter(
            handlers=(
                RabbitRoute(amqp_handler, "test-queue"),
            )
        )
        broker.include_router(amqp_routes)
        faststream_integration.setup_dishka(container, FastStream(broker))

        http = Litestar(
            route_handlers=[http_handler],
            on_startup=[broker.start],
            on_shutdown=[broker.close],
        )
        litestar_integration.setup_dishka(container, http)
        return http


    if __name__ == "__main__":
        uvicorn.run(create_app(), host="0.0.0.0", port=8000)

3. Пример использования FastStream + FastAPI

.. code-block:: python

    import uvicorn
    from dishka import Provider, Scope, provide
    from dishka import make_async_container
    from dishka.integrations import fastapi as fastapi_integration
    from dishka.integrations import faststream as faststream_integration
    from dishka.integrations.base import FromDishka as Depends
    from dishka.integrations.fastapi import DishkaRoute
    from dishka.integrations.faststream import inject as faststream_inject
    from fastapi import FastAPI, APIRouter
    from faststream import FastStream
    from faststream.rabbit import RabbitBroker, RabbitRouter, RabbitRoute


    class SomeDependency:
        async def do_something(self) -> int:
            print("Hello world")
            return 42


    class SomeProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def some_dependency(self) -> SomeDependency:
            return SomeDependency()


    router = APIRouter(
        route_class=DishkaRoute,
    )


    @router.get("/")
    async def http_handler(some_dependency: Depends[SomeDependency]) -> None:
        await some_dependency.do_something()


    @faststream_inject
    async def amqp_handler(data: str, some_dependency: Depends[SomeDependency]) -> None:
        print(f"{data=}")
        await some_dependency.do_something()


    def create_app():
        container = make_async_container(SomeProvider())

        broker = RabbitBroker(
            url="amqp://guest:guest@localhost:5672/",
        )
        amqp_routes = RabbitRouter(
            handlers=(
                RabbitRoute(amqp_handler, "test-queue"),
            )
        )
        broker.include_router(amqp_routes)
        faststream_integration.setup_dishka(container, FastStream(broker))

        http = FastAPI(
            on_startup=[broker.start],
            on_shutdown=[broker.close],
        )
        http.include_router(router)
        fastapi_integration.setup_dishka(container, http)
        return http


    if __name__ == "__main__":
        uvicorn.run(create_app(), host="0.0.0.0", port=8000)


Тестирование FastStream с dishka
*******************************************

Простой пример

.. code-block:: python

    from collections.abc import AsyncIterator

    import pytest
    from dishka import AsyncContainer, make_async_container
    from dishka import Provider, Scope, provide
    from dishka.integrations import faststream as faststream_integration
    from dishka.integrations.base import FromDishka as Depends
    from faststream import FastStream, TestApp
    from faststream.rabbit import RabbitBroker, TestRabbitBroker, RabbitRouter

    router = RabbitRouter()


    @router.subscriber("test-queue")
    async def handler(msg: str, some_dependency: Depends[int]) -> int:
        print(f"{msg=}")
        return some_dependency


    @pytest.fixture
    async def broker() -> RabbitBroker:
        broker = RabbitBroker()
        broker.include_router(router)
        return broker


    @pytest.fixture
    def mock_provider() -> Provider:
        class MockProvider(Provider):
            @provide(scope=Scope.REQUEST)
            async def get_some_dependency(self) -> int:
                return 42

        return MockProvider()


    @pytest.fixture
    def container(mock_provider: Provider) -> AsyncContainer:
        return make_async_container(mock_provider)


    @pytest.fixture
    async def app(broker: RabbitBroker, container: AsyncContainer) -> FastStream:
        app = FastStream(broker)
        faststream_integration.setup_dishka(container, app, auto_inject=True)
        return FastStream(broker)


    @pytest.fixture
    async def client(app: FastStream) -> AsyncIterator[RabbitBroker]:
        async with TestRabbitBroker(app.broker) as br, TestApp(app):
            yield br


    @pytest.mark.asyncio
    async def test_handler(client: RabbitBroker) -> None:
        result = await client.request("hello", "test-queue")
        assert await result.decode() == 42
