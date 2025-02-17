from collections.abc import AsyncIterable
from pathlib import Path
from unittest.mock import Mock

import grpc.aio
import pytest
import pytest_asyncio

from dishka import AsyncContainer
from dishka.integrations.grpcio import (
    DishkaAioInterceptor,
    FromDishka,
    inject,
)
from ..common import (
    REQUEST_DEP_VALUE,
    AppProvider,
    RequestDep,
)

code_dir = Path(__file__).parent / "my_grpc_service.proto"
myprotos, myservices = grpc.protos_and_services(
    str(code_dir.relative_to(Path.cwd())),
)


@pytest_asyncio.fixture
async def dishka_grpc_app(async_container):
    server = grpc.aio.server(interceptors=[
        DishkaAioInterceptor(async_container),
    ])
    myservices.add_MyServiceServicer_to_server(MyService(), server)
    server.add_insecure_port("localhost:50051")
    await server.start()
    yield server
    await server.stop(0)


@pytest_asyncio.fixture
async def client(dishka_grpc_app):
    async with (
        grpc.aio.insecure_channel("localhost:50051") as channel,
    ):
        yield myservices.MyServiceStub(channel)


class MyService(myservices.MyServiceServicer):
    @inject
    async def MyMethod(  # noqa: N802
            self,
            request: myprotos.MyRequest,
            context: grpc.ServicerContext,
            a: FromDishka[RequestDep],
            mock: FromDishka[Mock],
    ) -> myprotos.MyResponse:
        mock(a)

        return myprotos.MyResponse(message="Hello")

    @inject
    async def MyUnaryStreamMethod(  # noqa: N802
            self,
            request: myprotos.MyRequest,
            context: grpc.ServicerContext,
            mock: FromDishka[Mock],
            request_dep: FromDishka[RequestDep],
    ) -> AsyncIterable[myprotos.MyResponse]:
        mock(request_dep)
        for i in range(5):
            await context.write(myprotos.MyResponse(message=f"Hello {i}"))

    @inject
    async def MyUnaryStreamMethodGen(  # noqa: N802
            self,
            request: myprotos.MyRequest,
            context: grpc.ServicerContext,
            mock: FromDishka[Mock],
            request_dep: FromDishka[RequestDep],
    ) -> AsyncIterable[myprotos.MyResponse]:
        mock(request_dep)
        for i in range(5):
            yield myprotos.MyResponse(message=f"Hello {i}")

    @inject
    async def MyStreamStreamMethodGen(  # noqa: N802
            self,
            request_iterator: AsyncIterable[myprotos.MyRequest],
            context: grpc.ServicerContext,
            container: FromDishka[AsyncContainer],
    ) -> AsyncIterable[myprotos.MyResponse]:
        async with container() as ctr:
            (await ctr.get(Mock))(await ctr.get(RequestDep))
            async for _ in request_iterator:
                yield myprotos.MyResponse(message="Hello")

    @inject
    async def MyStreamStreamMethod(  # noqa: N802
            self,
            request_iterator: AsyncIterable[myprotos.MyRequest],
            context: grpc.ServicerContext,
            container: FromDishka[AsyncContainer],
    ) -> None:
        async with container() as ctr:
            (await ctr.get(Mock))(await ctr.get(RequestDep))
            async for _ in request_iterator:
                await context.write(myprotos.MyResponse(message="Hello"))

    @inject
    async def MyStreamUnaryMethod(  # noqa: N802
            self,
            request_iterator: AsyncIterable[myprotos.MyRequest],
            context: grpc.ServicerContext,
            container: FromDishka[AsyncContainer],
    ) -> myprotos.MyResponse:
        async with container() as ctr:
            (await ctr.get(Mock))(await ctr.get(RequestDep))

            messages = [response.name async for response in request_iterator]
            return myprotos.MyResponse(message=" ".join(messages))


@pytest.mark.asyncio
async def test_grpc_unary_unary(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    response = await client.MyMethod(myprotos.MyRequest(name="Test"))
    assert response.message == "Hello"
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_grpc_unary_stream(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    responses = client.MyUnaryStreamMethod(myprotos.MyRequest(name="Test"))
    messages = [response.message async for response in responses]
    assert messages == [
        "Hello 0",
        "Hello 1",
        "Hello 2",
        "Hello 3",
        "Hello 4",
    ]
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()

@pytest.mark.asyncio
async def test_grpc_unary_stream_gen(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    responses = client.MyUnaryStreamMethodGen(myprotos.MyRequest(name="Test"))
    messages = [response.message async for response in responses]
    assert messages == [
        "Hello 0",
        "Hello 1",
        "Hello 2",
        "Hello 3",
        "Hello 4",
    ]
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_grpc_stream_unary_request_dependency(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    request_iterator = (myprotos.MyRequest(name="Test") for _ in range(5))
    response = await client.MyStreamUnaryMethod(request_iterator)
    assert response.message == "Test Test Test Test Test"
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_grpc_stream_stream_request_dependency(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    request_iterator = iter([
        myprotos.MyRequest(name="Test")
        for _ in range(5)
    ])
    responses = client.MyStreamStreamMethod(request_iterator)
    messages = [response.message async for response in responses]
    assert messages == ["Hello"] * 5
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()


@pytest.mark.asyncio
async def test_grpc_stream_stream_gen_request_dependency(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    request_iterator = iter([
        myprotos.MyRequest(name="Test")
        for _ in range(5)
    ])
    responses = client.MyStreamStreamMethodGen(request_iterator)
    messages = [response.message async for response in responses]
    assert messages == ["Hello"] * 5
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()
