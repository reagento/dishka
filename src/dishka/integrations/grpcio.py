__all__ = [
    "FromDishka",
    "inject",
    "DishkaAioInterceptor",
    "DishkaAioInterceptor",
]

from collections.abc import Awaitable, Callable, Iterator
from contextvars import ContextVar
from inspect import isasyncgenfunction, iscoroutinefunction
from typing import Any, ParamSpec, TypeVar

import grpc
from google.protobuf import message

from dishka import AsyncContainer, Container, FromDishka, Scope
from dishka.integrations.base import wrap_injection

P = ParamSpec("P")
RT = TypeVar("RT")

_dishka_scoped_container = ContextVar("_dishka_scoped_container")


def inject(func: Callable[P, RT]) -> Callable[P, RT]:
    return wrap_injection(
        func=func,
        is_async=iscoroutinefunction(func) or isasyncgenfunction(func),
        container_getter=lambda _, __: _dishka_scoped_container.get(),
    )


class DishkaInterceptor(grpc.ServerInterceptor):  # type: ignore[misc]
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
                _dishka_scoped_container.set(container)
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
                _dishka_scoped_container.set(container)
                return rpc_handler.stream_unary(
                    request_iterator, context,
                )

        def unary_stream_behavior(
            request: message.Message,
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {
                message.Message: request,
                grpc.ServicerContext: context,
            }
            with self._container(context=context_) as container:
                _dishka_scoped_container.set(container)
                yield from rpc_handler.unary_stream(request, context)

        def stream_stream_behavior(
            request_iterator: Iterator[message.Message],
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {grpc.ServicerContext: context}
            with self._container(
                context=context_,
                scope=Scope.SESSION,
            ) as container:
                _dishka_scoped_container.set(container)
                yield from rpc_handler.stream_stream(request_iterator, context)

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


class DishkaAioInterceptor(grpc.aio.ServerInterceptor):  # type: ignore[misc]
    def __init__(self, container: AsyncContainer) -> None:
        self._container = container

    async def intercept_service(  # noqa: C901
        self,
        continuation: Callable[
            [grpc.HandlerCallDetails],
            Awaitable[grpc.RpcMethodHandler],
        ],
        handler_call_details: grpc.HandlerCallDetails,
    ) -> grpc.RpcMethodHandler:
        rpc_handler = await continuation(handler_call_details)

        async def unary_unary_behavior(
            request: message.Message,
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {
                message.Message: request,
                grpc.ServicerContext: context,
            }
            async with self._container(context=context_) as container:
                _dishka_scoped_container.set(container)
                return await rpc_handler.unary_unary(request, context)

        async def stream_unary_behavior(
            request_iterator: Iterator[message.Message],
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {grpc.ServicerContext: context}
            async with self._container(
                context=context_,
                scope=Scope.SESSION,
            ) as container:
                _dishka_scoped_container.set(container)
                return await rpc_handler.stream_unary(
                    request_iterator, context,
                )

        async def unary_stream_behavior(
            request: message.Message,
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {
                message.Message: request,
                grpc.ServicerContext: context,
            }
            async with self._container(
                context=context_,
                scope=Scope.REQUEST,
            ) as container:
                _dishka_scoped_container.set(container)
                stream = rpc_handler.unary_stream(request, context)
                async for result in stream:
                    yield result

        async def stream_stream_behavior(
            request_iterator: Iterator[message.Message],
            context: grpc.ServicerContext,
        ) -> Any:
            context_ = {grpc.ServicerContext: context}
            async with self._container(
                context=context_,
                scope=Scope.SESSION,
            ) as container:
                _dishka_scoped_container.set(container)
                stream = rpc_handler.stream_stream(request_iterator, context)
                async for result in stream:
                    yield result

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
