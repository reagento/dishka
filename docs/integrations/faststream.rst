.. _faststream:

FastStream
===========================================

Though it is not required, you can use dishka-faststream integration. It features:

* automatic REQUEST scope management using middleware
* passing ``StreamMessage`` and ``ContextRepo`` object as a context data to providers
* automatic injection of dependencies into message handler

You can use auto-injection for FastStream 0.5.0 and higher. For older version you need to specify ``@inject`` manually.

.. note::

    If you are using **FastAPI plugin** of **FastStream** you need to use both dishka integrations, but you can share the same container.

    * Call ``dishka.integrations.faststream.setup_dishka`` on faststream broker or router
    * Call ``dishka.integrations.fastapi.setup_dishka`` on fastapi app.



How to use
****************

1. Import

..  code-block:: python

    from dishka.integrations.faststream import (
        FromDishka,
        inject,
        setup_dishka,
        FastStreamProvider,
    )
    from dishka import make_async_container, Provider, provide, Scope

2. Create provider. You can use ``faststream.types.StreamMessage`` and ``faststream.ContextRepo`` as a factory parameter to access on REQUEST-scope

.. code-block:: python

    class YourProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def create_x(self, event: StreamMessage) -> X:
             ...


3. Mark those of your handlers parameters which are to be injected with ``FromDishka[]``

.. code-block:: python

    @broker.subscriber("test")
    async def start(
        gateway: FromDishka[Gateway],
    ):
        ...


3a. *(optional)* decorate them using ``@inject`` if you are not using auto-injection

.. code-block:: python

    @broker.subscriber("test")
    @inject
    async def start(
        gateway: FromDishka[Gateway],
    ):
        ...


4. *(optional)* Use ``FastStreamProvider()`` when creating container if you are going to use  ``faststream.types.StreamMessage`` or ``faststream.ContextRepo``  in providers.

.. code-block:: python

    container = make_async_container(YourProvider(), FastStreamProvider())


5. Setup dishka integration.  ``auto_inject=True`` is required unless you explicitly use ``@inject`` decorator.

.. code-block:: python

    setup_dishka(container=container, broker=broker, auto_inject=True)


FastStream - Litestar/FastAPI - dishka integration
****************

1. Running RabbitMQ

.. code-block:: shell

    docker run -d --name rabbitmq \
      -p 5672:5672 -p 15672:15672 \
      -e RABBITMQ_DEFAULT_USER=guest \
      -e RABBITMQ_DEFAULT_PASS=guest \
      rabbitmq:management

2. Example of usage FastStream + Litestar

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

3. Example of usage FastStream + FastAPI

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


Testing FastStream with dishka
****************

1. Simple example

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
