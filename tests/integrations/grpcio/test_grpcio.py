from concurrent import futures
from contextlib import contextmanager
from unittest.mock import Mock

import grpc

from dishka import make_container
from dishka.integrations.grpcio import FromDishka, inject, setup_dishka
from ..common import (
    APP_DEP_VALUE,
    REQUEST_DEP_VALUE,
    AppDep,
    AppProvider,
    RequestDep,
)
from .my_grpc_service_pb2 import MyRequest, MyResponse
from .my_grpc_service_pb2_grpc import (
    MyServiceServicer,
    MyServiceStub,
    add_MyServiceServicer_to_server,
)


class MyService(MyServiceServicer):
    @inject
    def MyMethod(  # noqa: N802
        self,
        request: MyRequest,
        context,
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
    ) -> MyResponse:
        mock(a)
        return MyResponse(message="Hello")


@contextmanager
def dishka_grpc_app(servicer_class, provider, port=50051):
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    container = make_container(provider)
    setup_dishka(container=container, server=server)
    add_MyServiceServicer_to_server(servicer_class(), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    yield server
    server.stop(0)
    container.close()


def test_grpc_app_dependency(app_provider: AppProvider):
    with (
        dishka_grpc_app(MyService, app_provider),
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        stub = MyServiceStub(channel)
        response = stub.MyMethod(MyRequest(name="Test"))
        assert response.message == "Hello"
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


class MyRequestService(MyServiceServicer):
    @inject
    def MyMethod(  # noqa: N802
        self,
        request: MyRequest,
        context,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
    ) -> MyResponse:
        mock(a)
        return MyResponse(message="Hello")


def test_grpc_request_dependency(app_provider: AppProvider):
    with (
        dishka_grpc_app(MyRequestService, app_provider),
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        stub = MyServiceStub(channel)
        response = stub.MyMethod(MyRequest(name="Test"))
        assert response.message == "Hello"
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


def test_grpc_request_dependency2(app_provider: AppProvider):
    with (
        dishka_grpc_app(MyRequestService, app_provider),
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        stub = MyServiceStub(channel)
        response = stub.MyMethod(MyRequest(name="Test"))
        assert response.message == "Hello"
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()

        app_provider.mock.reset_mock()
        app_provider.request_released.reset_mock()

        response = stub.MyMethod(MyRequest(name="Test"))
        assert response.message == "Hello"
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
