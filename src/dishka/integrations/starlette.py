__all__ = ["Depends", "inject", "DishkaApp"]

from starlette.requests import Request
from starlette.types import ASGIApp, Receive, Scope, Send

from dishka import AsyncContainer
from ..async_container import AsyncContextWrapper
from .asgi import BaseDishkaApp
from .base import Depends, wrap_injection


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
            await self.app(scope, receive, send)


class DishkaApp(BaseDishkaApp):
    def _init_request_middleware(
            self, app, container_wrapper: AsyncContextWrapper,
    ):
        app.add_middleware(ContainerMiddleware)

    def _app_startup(self, app, container: AsyncContainer):
        app.state.dishka_container = container
