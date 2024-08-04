__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Callable, Iterator
from typing import Any, ParamSpec, TypeAlias, TypeVar

import grpc._interceptor
from google.protobuf import message

from dishka import Container, FromDishka, Scope
from dishka.integrations.base import wrap_injection

P = ParamSpec("P")
RT = TypeVar("RT")


InjectFunc: TypeAlias = Callable[P, RT]


def getter(args: tuple, _: dict) -> Container | None:
    iterator = (
        arg._dishka_container  # noqa: SLF001
        for arg in args
        if isinstance(arg, grpc.ServicerContext)
    )

    return next(iterator, None)


def inject(func: InjectFunc) -> InjectFunc:
    return wrap_injection(
        func=func,
        container_getter=getter,
        remove_depends=True,
        is_async=False,
    )


class ContainerInterceptor(grpc.ServerInterceptor):
    def __init__(self, container: Container) -> None:
        self._container = container

    def intercept_service(
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails],
            grpc.RpcMethodHandler,
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        rpc_handler = continuation(handler_call_details)

        def unary_unary_behavior(
            request: message.Message,
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {
                message.Message: request,
                grpc.ServicerContext: context,
            }
            with self._container(context=context_) as container:
                context._dishka_container = container  # noqa: SLF001
                return rpc_handler.unary_unary(request, context)

        def stream_unary_behavior(
            request_iterator: Iterator[message.Message],
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {grpc.ServicerContext: context}
            with self._container(
                context=context_,
                scope=Scope.SESSION,
            ) as container:
                context._dishka_container = container  # noqa: SLF001
                return rpc_handler.stream_unary(request_iterator, context)

        def unary_stream_behavior(
            request: message.Message,
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {
                message.Message: request,
                grpc.ServicerContext: context,
            }
            with self._container(
                context=context_,
                scope=Scope.SESSION,
            ) as container:
                context._dishka_container = container  # noqa: SLF001
                return rpc_handler.unary_stream(request, context)

        def stream_stream_behavior(
            request_iterator: Iterator[message.Message],
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {grpc.ServicerContext: context}
            with self._container(
                context=context_,
                scope=Scope.SESSION,
            ) as container:
                context._dishka_container = container  # noqa: SLF001
                return rpc_handler.stream_stream(request_iterator, context)

        if rpc_handler.unary_unary:
            return grpc.unary_unary_rpc_method_handler(
                unary_unary_behavior,
                rpc_handler.request_deserializer,
                rpc_handler.response_serializer,
            )
        elif rpc_handler.stream_unary:
            return grpc.stream_unary_rpc_method_handler(
                stream_unary_behavior,
                rpc_handler.request_deserializer,
                rpc_handler.response_serializer,
            )
        elif rpc_handler.unary_stream:
            return grpc.unary_stream_rpc_method_handler(
                unary_stream_behavior,
                rpc_handler.request_deserializer,
                rpc_handler.response_serializer,
            )
        elif rpc_handler.stream_stream:
            return grpc.stream_stream_rpc_method_handler(
                stream_stream_behavior,
                rpc_handler.request_deserializer,
                rpc_handler.response_serializer,
            )

        return rpc_handler


def setup_dishka(container: Container, server: grpc.Server) -> None:
    interceptor = ContainerInterceptor(container)

    interceptor_pipeline = server._state.interceptor_pipeline  # noqa: SLF001

    if interceptor_pipeline is None:
        interceptor_pipeline = grpc._interceptor._ServicePipeline(  # noqa: SLF001
            [interceptor],
        )

    else:
        interceptors = [interceptor, *interceptor_pipeline.interceptors]
        interceptor_pipeline = grpc._interceptor._ServicePipeline(  # noqa: SLF001
            interceptors,
        )

    server._state.interceptor_pipeline = interceptor_pipeline  # noqa: SLF001
