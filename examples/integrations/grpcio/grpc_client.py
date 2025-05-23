import grpc
from grpcio.pb2.service_pb2 import RequestMessage
from grpcio.pb2.service_pb2_grpc import ExampleServiceStub


def run():
    with grpc.insecure_channel("localhost:50051") as channel:
        stub = ExampleServiceStub(channel)

        # Unary-Unary
        response = stub.UnaryUnary(RequestMessage(message="Hello UnaryUnary"))
        print("UnaryUnary response:", response.message)

        # Unary-Stream
        responses = stub.UnaryStream(RequestMessage(message="Hello UnaryStream"))
        for response in responses:
            print("UnaryStream response:", response.message)

        # Stream-Unary
        requests = [
            RequestMessage(message="Hello StreamUnary 1"),
            RequestMessage(message="Hello StreamUnary 2"),
        ]
        response = stub.StreamUnary(iter(requests))
        print("StreamUnary response:", response.message)

        # Stream-Stream
        requests = [
            RequestMessage(message="Hello StreamStream 1"),
            RequestMessage(message="Hello StreamStream 2"),
        ]
        responses = stub.StreamStream(iter(requests))
        for response in responses:
            print("StreamStream response:", response.message)


if __name__ == "__main__":
    run()
