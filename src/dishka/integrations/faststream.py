__all__ = (
    "FastStreamProvider",
    "FromDishka",
    "inject",
    "setup_dishka",
)

import warnings
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import (
    Any,
    ParamSpec,
    Protocol,
    TypeAlias,
    TypeVar,
    cast,
)

from faststream import BaseMiddleware, FastStream, context
from faststream.__about__ import (
    __version__ as FASTSTREAM_VERSION,  # noqa: N812
)
from faststream.broker.message import StreamMessage
from faststream.types import DecodedMessage
from faststream.utils.context import ContextRepo

from dishka import AsyncContainer, FromDishka, Provider, Scope, from_context
from dishka.integrations.base import wrap_injection


class FastStreamProvider(Provider):
    context = from_context(ContextRepo, scope=Scope.REQUEST)
    message = from_context(StreamMessage, scope=Scope.REQUEST)


FASTSTREAM_04 = FASTSTREAM_VERSION.startswith("0.4")
FASTSTREAM_05 = FASTSTREAM_VERSION.startswith("0.5")
FASTSTREAM_LATES = not FASTSTREAM_04 and not FASTSTREAM_05

if FASTSTREAM_04:
    warnings.warn(
        "FastStream 0.4 is deprecated and integration will be removed"
        " in the 1.6.0 dishka release.",
        category=DeprecationWarning,
        stacklevel=1,
    )

    from faststream.broker.core.abc import (  # type: ignore[attr-defined]
        BrokerUsecase as BrokerType,
    )

    Application: TypeAlias = FastStream

    try:
        from faststream.broker.fastapi import StreamRouter
    except ImportError:
        pass
    else:
        Application |= StreamRouter  # type: ignore[assignment]

elif FASTSTREAM_05:
    from faststream.broker.core.usecase import BrokerUsecase as BrokerType

    if FASTSTREAM_VERSION < "0.5.16":
        warnings.warn(
            "FastStream < 0.5.16 is deprecated and integration will be removed"
            " in the 1.7.0 dishka release.",
            category=DeprecationWarning,
            stacklevel=1,
        )

        Application: TypeAlias = FastStream  # type: ignore[no-redef,misc]

    else:
        from faststream.asgi import AsgiFastStream

        Application: TypeAlias = FastStream | AsgiFastStream  # type: ignore[no-redef,misc]

    try:
        from faststream.broker.fastapi import StreamRouter
    except ImportError:
        pass
    else:
        Application |= StreamRouter  # type: ignore[assignment]

else:
    from faststream._internal.broker.broker import BrokerUsecase as BrokerType
    from faststream.asgi import AsgiFastStream

    Application: TypeAlias = FastStream | AsgiFastStream  # type: ignore[no-redef,misc]

    try:
        from faststream._internal.fastapi import (  # type: ignore[no-redef]
            StreamRouter,
        )
    except ImportError:
        pass
    else:
        Application |= StreamRouter  # type: ignore[assignment]


class ApplicationLike(Protocol):
    broker: BrokerType[Any, Any]


def setup_dishka(
    container: AsyncContainer,
    app: "Application | ApplicationLike | None" = None,
    broker: "BrokerType[Any, Any] | None" = None,
    *,
    finalize_container: bool = True,
    auto_inject: bool = False,
) -> None:
    """
    Setup dishka integration with FastStream.
    You must provide either app or broker.

    Args:
        container: AsyncContainer instance.
        app: FastStream Application or StreamRouter instance.
        broker: FastStream broker instance.
        finalize_container: bool. Can be used only with app.
        auto_inject: bool.
    """
    if (app and broker) or (not app and not broker):
        raise ValueError(  # noqa: TRY003
            "You must provide either app or broker "
            "to setup dishka integration.",
        )

    if finalize_container:
        if getattr(app, "after_shutdown", None):
            app.after_shutdown(container.close)  # type: ignore[union-attr]

        else:
            warnings.warn(
                "For use `finalize_container=True` "
                "you must provide `app: FastStream | AsgiFastStream` "
                "argument.",
                category=RuntimeWarning,
                stacklevel=2,
            )

    broker = broker or getattr(app, "broker", None)
    assert broker  # noqa: S101

    if FASTSTREAM_04:
        # FastStream 0.4 - 0.5
        broker.middlewares = (
            DishkaMiddleware(container),
            *broker.middlewares,
        )

        if auto_inject:
            warnings.warn(
                """
Auto injection is not supported for FastStream version less than 0.5.0
Please, update your FastStream installation
or use @inject at each subscriber manually.
            """,
                category=RuntimeWarning,
                stacklevel=2,
            )

        return

    elif getattr(broker, "add_middleware", None):
        # FastStream 0.5.6 and higher
        broker.add_middleware(DishkaMiddleware(container))

    else:
        # FastStream 0.5 - 0.5.6
        warnings.warn(
            "FastStream < 0.5.6 is deprecated and integration will be removed"
            " in the 1.7.0 dishka release.",
            category=DeprecationWarning,
            stacklevel=2,
        )

        broker._middlewares = (  # noqa: SLF001
            DishkaMiddleware(container),
            *broker._middlewares,  # noqa: SLF001
        )

        for subscriber in broker._subscribers.values():  # noqa: SLF001
            subscriber._broker_middlewares = (  # noqa: SLF001
                DishkaMiddleware(container),
                *subscriber._broker_middlewares,  # noqa: SLF001
            )

        for publisher in broker._publishers.values():  # noqa: SLF001
            publisher._broker_middlewares = (  # noqa: SLF001
                DishkaMiddleware(container),
                *publisher._broker_middlewares,  # noqa: SLF001
            )

    if auto_inject:
        broker._call_decorators = (  # noqa: SLF001
            inject,
            *broker._call_decorators,  # noqa: SLF001
        )


T = TypeVar("T")
P = ParamSpec("P")


def inject(func: Callable[P, T]) -> Callable[P, T]:
    return wrap_injection(
        func=func,
        is_async=True,
        container_getter=lambda *_: context.get_local("dishka"),
    )


class _DishkaMiddleware(BaseMiddleware):
    def __init__(
        self,
        container: AsyncContainer,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.container = container
        super().__init__(*args, **kwargs)

    if FASTSTREAM_04:

        @asynccontextmanager
        async def consume_scope(  # type: ignore[override]
            self,
            *args: Any,
            **kwargs: Any,
        ) -> AsyncIterator[DecodedMessage]:
            async with self.container({
                ContextRepo: context,
            }) as request_container:
                with context.scope("dishka", request_container):
                    async with super().consume_scope(  # type: ignore[attr-defined]
                        *args,
                        **kwargs,
                    ) as result:
                        yield result

    elif FASTSTREAM_05:

        async def consume_scope(  # type: ignore[misc]
            self,
            call_next: Callable[[Any], Awaitable[Any]],
            msg: StreamMessage[Any],
        ) -> AsyncIterator[DecodedMessage]:
            async with self.container(
                {
                    StreamMessage: msg,
                    ContextRepo: context,
                    type(msg): msg,
                },
            ) as request_container:
                with context.scope("dishka", request_container):
                    return cast(
                        AsyncIterator[DecodedMessage],
                        await call_next(msg),
                    )

    else:
        async def consume_scope(  # type: ignore[misc]
            self,
            call_next: Callable[[Any], Awaitable[Any]],
            msg: StreamMessage[Any],
        ) -> AsyncIterator[DecodedMessage]:
            async with self.container(
                {
                    StreamMessage: msg,
                    ContextRepo: context,
                    type(msg): msg,
                },
            ) as request_container:
                with self.context.scope("dishka", request_container):  # type: ignore[attr-defined]
                    return cast(
                        AsyncIterator[DecodedMessage],
                        await call_next(msg),
                    )


class DishkaMiddleware:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    def __call__(self, *args: Any, **kwargs: Any) -> "_DishkaMiddleware":
        return _DishkaMiddleware(self.container, *args, **kwargs)
