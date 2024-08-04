from collections.abc import Iterable
from concurrent import futures
from contextlib import contextmanager
from unittest.mock import Mock

import grpc

from dishka import make_container
from dishka.container import Container
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
        context: grpc.ServicerContext,
        a: FromDishka[AppDep],
        mock: FromDishka[Mock],
    ) -> MyResponse:
        mock(a)

        return MyResponse(message="Hello")

    @inject
    def MyUnaryStreamMethod(  # noqa: N802
        self,
        request: MyRequest,
        context: grpc.ServicerContext,
        a: FromDishka[AppDep],
        container: FromDishka[Container],
    ) -> Iterable[MyResponse]:
        with container() as ctr:
            ctr.get(Mock)(a)
            for i in range(5):
                yield MyResponse(message=f"Hello {i}")

    @inject
    def MyStreamUnaryMethod(  # noqa: N802
        self,
        request_iterator: Iterable[MyRequest],
        context: grpc.ServicerContext,
        a: FromDishka[AppDep],
        container: FromDishka[Container],
    ) -> MyResponse:
        for _ in request_iterator:
            with container() as ctr:
                ctr.get(Mock)(a)
        return MyResponse(message="Hello")

    @inject
    def MyStreamStreamMethod(  # noqa: N802
        self,
        request_iterator: Iterable[MyRequest],
        context: grpc.ServicerContext,
        a: FromDishka[AppDep],
        container: FromDishka[Container],
    ) -> Iterable[MyResponse]:
        for _ in request_iterator:
            with container() as ctr:
                ctr.get(Mock)(a)

            yield MyResponse(message="Hello")


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


def test_grpc_unary_stream_dependency(app_provider: AppProvider):
    with (
        dishka_grpc_app(MyService, app_provider),
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        stub = MyServiceStub(channel)
        responses = stub.MyUnaryStreamMethod(MyRequest(name="Test"))
        messages = [response.message for response in responses]
        assert messages == [
            "Hello 0",
            "Hello 1",
            "Hello 2",
            "Hello 3",
            "Hello 4",
        ]
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def test_grpc_stream_unary_dependency(app_provider: AppProvider):
    with (
        dishka_grpc_app(MyService, app_provider),
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        stub = MyServiceStub(channel)
        request_iterator = iter([MyRequest(name="Test") for _ in range(5)])
        response = stub.MyStreamUnaryMethod(request_iterator)
        assert response.message == "Hello"
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


def test_grpc_stream_stream_dependency(app_provider: AppProvider):
    with (
        dishka_grpc_app(MyService, app_provider),
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        stub = MyServiceStub(channel)
        request_iterator = iter([MyRequest(name="Test") for _ in range(5)])
        responses = stub.MyStreamStreamMethod(request_iterator)
        messages = [response.message for response in responses]
        assert messages == ["Hello"] * 5
        app_provider.mock.assert_called_with(APP_DEP_VALUE)
        app_provider.app_released.assert_not_called()
    app_provider.app_released.assert_called()


class MyRequestService(MyServiceServicer):
    @inject
    def MyMethod(  # noqa: N802
        self,
        request: MyRequest,
        context: grpc.ServicerContext,
        a: FromDishka[RequestDep],
        mock: FromDishka[Mock],
    ) -> MyResponse:
        mock(a)

        return MyResponse(message="Hello")

    @inject
    def MyUnaryStreamMethod(  # noqa: N802
        self,
        request: MyRequest,
        context: grpc.ServicerContext,
        container: FromDishka[Container],
    ) -> Iterable[MyResponse]:
        with container() as ctr:
            ctr.get(Mock)(ctr.get(RequestDep))
            for i in range(5):
                yield MyResponse(message=f"Hello {i}")

    @inject
    def MyStreamStreamMethod(  # noqa: N802
        self,
        request_iterator: Iterable[MyRequest],
        context: grpc.ServicerContext,
        container: FromDishka[Container],
    ) -> Iterable[MyResponse]:
        with container() as ctr:
            ctr.get(Mock)(ctr.get(RequestDep))
            for _ in request_iterator:
                yield MyResponse(message="Hello")

    @inject
    def MyStreamUnaryMethod(  # noqa: N802
        self,
        request_iterator: Iterable[MyRequest],
        context: grpc.ServicerContext,
        container: FromDishka[Container],
    ) -> MyResponse:
        with container() as ctr:
            ctr.get(Mock)(ctr.get(RequestDep))

            messages = [response.name for response in request_iterator]
            return MyResponse(message=" ".join(messages))


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


def test_grpc_unary_stream_request_dependency(app_provider: AppProvider):
    with (
        dishka_grpc_app(MyRequestService, app_provider),
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        stub = MyServiceStub(channel)
        responses = stub.MyUnaryStreamMethod(MyRequest(name="Test"))
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


def test_grpc_stream_unary_request_dependency(app_provider: AppProvider):
    with (
        dishka_grpc_app(MyRequestService, app_provider),
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        stub = MyServiceStub(channel)
        request_iterator = (MyRequest(name="Test") for _ in range(5))
        response = stub.MyStreamUnaryMethod(request_iterator)
        assert response.message == "Test Test Test Test Test"
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()


def test_grpc_stream_stream_request_dependency(app_provider: AppProvider):
    with (
        dishka_grpc_app(MyRequestService, app_provider),
        grpc.insecure_channel("localhost:50051") as channel,
    ):
        stub = MyServiceStub(channel)
        request_iterator = iter([MyRequest(name="Test") for _ in range(5)])
        responses = stub.MyStreamStreamMethod(request_iterator)
        messages = [response.message for response in responses]
        assert messages == ["Hello"] * 5
        app_provider.mock.assert_called_with(REQUEST_DEP_VALUE)
        app_provider.request_released.assert_called_once()
