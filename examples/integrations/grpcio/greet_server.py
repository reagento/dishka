from concurrent import futures

import grpc
from di import ServicesProvider
from pb2 import greet_pb2, greet_pb2_grpc
from services.uuid_service import UUIDService

from dishka import make_container
from dishka.integrations.grpcio import FromDishka, inject, setup_dishka


class GreeterServicer(greet_pb2_grpc.GreeterServicer):
    @inject
    def SayHello(  # noqa: N802
        self,
        request,
        context,
        service: FromDishka[UUIDService],
    ):
        hello_reply = greet_pb2.HelloReply()
        hello_reply.message = (
            f"{request.greeting} {request.name} {service.generate_uuid()}"
        )

        return hello_reply


def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    greet_pb2_grpc.add_GreeterServicer_to_server(GreeterServicer(), server)
    server.add_insecure_port("[::]:50051")
    setup_dishka(make_container(ServicesProvider()), server)

    server.start()
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
