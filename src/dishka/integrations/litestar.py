__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from inspect import Parameter
from typing import get_type_hints

from litestar import Litestar, Request
from litestar.enums import ScopeType
from litestar.types import ASGIApp, Receive, Scope, Send

from dishka import AsyncContainer, FromDishka
from dishka.integrations.base import wrap_injection


def inject(func):
    hints = get_type_hints(func)
    request_param = next(
        (name for name in hints if name == "request"),
        None,
    )
    if request_param:
        additional_params = []
    else:
        request_param = "request"
        additional_params = [Parameter(
            name=request_param,
            annotation=Request | None,
            kind=Parameter.KEYWORD_ONLY,
        )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda _, r: r[request_param].state.dishka_container,
        additional_params=additional_params,
        is_async=True,
    )


def make_add_request_container_middleware(app: ASGIApp):
    async def middleware(scope: Scope, receive: Receive, send: Send) -> None:
        if scope.get("type") != ScopeType.HTTP:
            await app(scope, receive, send)
            return

        request = Request(scope)
        async with request.app.state.dishka_container(
                {Request: request},
        ) as request_container:
            request.state.dishka_container = request_container
            await app(scope, receive, send)

    return middleware


def setup_dishka(container: AsyncContainer, app: Litestar) -> None:
    app.asgi_handler = make_add_request_container_middleware(
        app.asgi_handler,
    )
    app.state.dishka_container = container
