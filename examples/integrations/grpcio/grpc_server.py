from collections.abc import Iterable
from concurrent.futures import ThreadPoolExecutor
from contextlib import suppress

from grpc import ServicerContext, server as make_server

from dishka import Container
from dishka.container import make_container
from dishka.integrations.grpcio import inject, FromDishka, setup_dishka

from grpcio.di import service_provider
from grpcio.services.uuid_service import UUIDService
from grpcio.pb2.service_pb2 import RequestMessage, ResponseMessage
from grpcio.pb2.service_pb2_grpc import (
    ExampleServiceServicer,
    add_ExampleServiceServicer_to_server,
)


class ExampleService(ExampleServiceServicer):
    @inject
    def UnaryUnary(
        self,
        request: RequestMessage,
        context: ServicerContext,
        service: FromDishka[UUIDService],
    ) -> ResponseMessage:

        return ResponseMessage(message=f"UnaryUnary: {service.generate_uuid()}!")

    @inject
    def UnaryStream(
        self,
        request: RequestMessage,
        context: ServicerContext,
        container: FromDishka[Container],
    ) -> Iterable[ResponseMessage]:
        for i in range(5):
            with container() as request_container:
                service = request_container.get(UUIDService)
                yield ResponseMessage(
                    message=f"UnaryStream {i}: {service.generate_uuid()}!"
                )

    @inject
    def StreamUnary(
        self,
        request_iterator: Iterable[RequestMessage],
        context: ServicerContext,
        container: FromDishka[Container],
    ) -> ResponseMessage:
        messages = []
        for request in request_iterator:
            messages.append(request.message)
        with container() as request_container:
            service = request_container.get(UUIDService)
            return ResponseMessage(
                message=f"StreamUnary: {service.generate_uuid()}! messages: {', '.join(messages)}"
            )

    @inject
    def StreamStream(
        self,
        request_iterator: Iterable[RequestMessage],
        context: ServicerContext,
        container: FromDishka[Container],
    ) -> Iterable[ResponseMessage]:
        for request in request_iterator:
            with container() as request_container:
                service = request_container.get(UUIDService)
                yield ResponseMessage(
                    message=f"StreamStream: {service.generate_uuid()}!, message: {request.message}"
                )


def main() -> None:
    server = make_server(ThreadPoolExecutor(10))

    setup_dishka(make_container(service_provider()), server)

    add_ExampleServiceServicer_to_server(ExampleService(), server)

    server.add_insecure_port("[::]:50051")
    server.start()

    server.wait_for_termination()


if __name__ == "__main__":
    with suppress(KeyboardInterrupt):
        main()
