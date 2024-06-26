import logging

import grpc
from grpcio.pb2 import greet_pb2, greet_pb2_grpc

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run() -> None:
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = greet_pb2_grpc.GreeterStub(channel)
        hello_request = greet_pb2.HelloRequest(
            greeting="Bonjour",
            name="YouTube",
        )
        hello_reply = stub.SayHello(hello_request)
        reply = f"Reply: {hello_reply.message}"

        logger.info(reply)


if __name__ == "__main__":
    run()
