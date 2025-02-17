from collections.abc import AsyncIterable, Iterable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import Mock

import grpc.aio
import pytest
import pytest_asyncio

from dishka import Container
from dishka.integrations.grpcio import (
    DishkaInterceptor,
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
async def dishka_grpc_app(container):
    server = grpc.server(
        ThreadPoolExecutor(max_workers=10),
        interceptors=[
            DishkaInterceptor(container),
        ],
    )
    myservices.add_MyServiceServicer_to_server(MyService(), server)
    server.add_insecure_port("localhost:50051")
    server.start()
    yield server
    server.stop(0)


@pytest.fixture
def client(dishka_grpc_app):
    with (
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        yield myservices.MyServiceStub(channel)


class MyService(myservices.MyServiceServicer):
    @inject
    def MyMethod(  # noqa: N802
            self,
            request: myprotos.MyRequest,
            context: grpc.ServicerContext,
            a: FromDishka[RequestDep],
            mock: FromDishka[Mock],
    ) -> myprotos.MyResponse:
        mock(a)

        return myprotos.MyResponse(message="Hello")

    @inject
    def MyUnaryStreamMethod(  # noqa: N802
            self,
            request: myprotos.MyRequest,
            context: grpc.ServicerContext,
            mock: FromDishka[Mock],
            a: FromDishka[RequestDep],
    ) -> AsyncIterable[myprotos.MyResponse]:
        # unsupported on sync version
        raise NotImplementedError

    @inject
    def MyUnaryStreamMethodGen(  # noqa: N802
            self,
            request: myprotos.MyRequest,
            context: grpc.ServicerContext,
            mock: FromDishka[Mock],
            a: FromDishka[RequestDep],
    ) -> AsyncIterable[myprotos.MyResponse]:
        mock(a)

        for i in range(5):
            yield myprotos.MyResponse(message=f"Hello {i}")

    @inject
    def MyStreamStreamMethodGen(  # noqa: N802
            self,
            request_iterator: Iterable[myprotos.MyRequest],
            context: grpc.ServicerContext,
            container: FromDishka[Container],
    ) -> AsyncIterable[myprotos.MyResponse]:
        with container() as ctr:
            ctr.get(Mock)(ctr.get(RequestDep))
            for _ in request_iterator:
                yield myprotos.MyResponse(message="Hello")

    @inject
    def MyStreamStreamMethod(  # noqa: N802
            self,
            request_iterator: Iterable[myprotos.MyRequest],
            context: grpc.ServicerContext,
            container: FromDishka[Container],
    ) -> None:
        # unsupported on sync version
        raise NotImplementedError

    @inject
    def MyStreamUnaryMethod(  # noqa: N802
            self,
            request_iterator: Iterable[myprotos.MyRequest],
            context: grpc.ServicerContext,
            container: FromDishka[Container],
    ) -> myprotos.MyResponse:
        with container() as ctr:
            ctr.get(Mock)(ctr.get(RequestDep))

            messages = [response.name for response in request_iterator]
            return myprotos.MyResponse(message=" ".join(messages))


def test_grpc_unary_unary(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    response = client.MyMethod(myprotos.MyRequest(name="Test"))
    assert response.message == "Hello"
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()


def test_grpc_unary_stream(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    responses = client.MyUnaryStreamMethodGen(myprotos.MyRequest(name="Test"))
    messages = [response.message for response in responses]
    assert messages == [
        "Hello 0",
        "Hello 1",
        "Hello 2",
        "Hello 3",
        "Hello 4",
    ]
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()


def test_grpc_stream_unary_request_dependency(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    request_iterator = (myprotos.MyRequest(name="Test") for _ in range(5))
    response = client.MyStreamUnaryMethod(request_iterator)
    assert response.message == "Test Test Test Test Test"
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()


def test_grpc_stream_stream_request_dependency(
        client: myservices.MyServiceStub, app_provider: AppProvider,
):
    request_iterator = iter([
        myprotos.MyRequest(name="Test")
        for _ in range(5)
    ])
    responses = client.MyStreamStreamMethodGen(request_iterator)
    messages = [response.message for response in responses]
    assert messages == ["Hello"] * 5
    app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
    app_provider.request_released.assert_called_once()
