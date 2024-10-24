__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
    "LitestarProvider",
]

from collections.abc import Callable
from inspect import Parameter
from typing import ParamSpec, TypeVar, get_type_hints

from litestar import Litestar, Request, WebSocket
from litestar.enums import ScopeType
from litestar.types import ASGIApp, Receive, Scope, Send

from dishka import AsyncContainer, FromDishka, Provider, from_context
from dishka import Scope as DIScope
from dishka.integrations.base import wrap_injection

P = ParamSpec("P")
T = TypeVar("T")

def inject(func: Callable[P, T] | None = None, websocket: bool = False):
    def wrapper(func: Callable[P, T]) -> Callable[P, T]:
        hints = get_type_hints(func)

        request_param_name = "request" if not websocket else "socket"
        request_param = next(
            (name for name in hints if name == request_param_name),
            None,
        )

        if request_param:
            additional_params = []
        else:
            request_param = request_param_name
            request_annotation = Request | None if not websocket else WebSocket | None
            additional_params = [Parameter(
                name=request_param,
                annotation=request_annotation,
                kind=Parameter.KEYWORD_ONLY,
            )]

        return wrap_injection(
            func=func,
            is_async=True,
            additional_params=additional_params,
            container_getter=lambda _, r: r[request_param].state.dishka_container,
        )
    return wrapper if func is None else wrapper(func)


class LitestarProvider(Provider):
    request = from_context(Request, scope=DIScope.REQUEST)
    socket = from_context(WebSocket, scope=DIScope.SESSION)


def make_add_request_container_middleware(app: ASGIApp) -> ASGIApp:
    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") not in (ScopeType.HTTP, ScopeType.WEBSOCKET):
            await app(scope, receive, send)
            return

        if scope.get("type") == ScopeType.HTTP:
            request = Request(scope)  # type: ignore[var-annotated]
            context = {Request: request}
            di_scope = DIScope.REQUEST

        else:
            request = WebSocket(scope)
            context = {WebSocket: request}
            di_scope = DIScope.SESSION

        async with request.app.state.dishka_container(
            context, scope=di_scope,
        ) as request_container:
            request.state.dishka_container = request_container
            await app(scope, receive, send)

    return middleware


def setup_dishka(container: AsyncContainer, app: Litestar) -> None:
    app.asgi_handler = make_add_request_container_middleware(
        app.asgi_handler,
    )
    app.state.dishka_container = container
