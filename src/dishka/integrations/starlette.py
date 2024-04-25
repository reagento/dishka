__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.websockets import WebSocket

from dishka import AsyncContainer, FromDishka
from dishka import Scope as DIScope
from .base import wrap_injection


def inject(func):
    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda r, _: r[0].scope["state"]["dishka_container"],
        additional_params=[],
        is_async=True,
    )


class ContainerMiddleware:
    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
            self, scope: Scope, receive: Receive, send: Send,
    ) -> None:
        if scope["type"] not in ("http", "websocket"):
            return await self.app(scope, receive, send)

        if scope["type"] == "http":
            request = Request(scope)
            context = {Request: request}
            di_scope = DIScope.REQUEST

        else:
            request = WebSocket(scope, receive, send)
            context = {WebSocket: request}
            di_scope = DIScope.SESSION

        async with request.app.state.dishka_container(
            context, scope=di_scope,
        ) as request_container:
            request.state.dishka_container = request_container
            return await self.app(scope, receive, send)


def setup_dishka(container: AsyncContainer, app: Starlette) -> None:
    app.add_middleware(ContainerMiddleware)
    app.state.dishka_container = container
