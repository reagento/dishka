__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from dishka import AsyncContainer, FromDishka
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
        if scope["type"] != "http":
            return await self.app(scope, receive, send)

        request = Request(scope)
        async with request.app.state.dishka_container(
                {Request: request},
        ) as request_container:
            request.state.dishka_container = request_container
            return await self.app(scope, receive, send)


def setup_dishka(container: AsyncContainer, app: Starlette) -> None:
    app.add_middleware(ContainerMiddleware)
    app.state.dishka_container = container
