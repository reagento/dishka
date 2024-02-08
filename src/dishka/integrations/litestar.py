__all__ = [
    'Depends', "inject", "DishkaApp",
]


from inspect import Parameter
from typing import Optional, get_type_hints

from litestar import Request
from litestar.enums import ScopeType
from litestar.types import ASGIApp, Receive, Scope, Send

from dishka.async_container import AsyncContainer, AsyncContextWrapper
from dishka.integrations.asgi import BaseDishkaApp
from dishka.integrations.base import Depends, wrap_injection


def inject(func):
    hints = get_type_hints(func)
    request_param = next(
        (name for name, hint in hints.items() if hint is Request),
        None,
    )
    if request_param:
        additional_params = []
    else:
        request_param = "request"
        additional_params = [Parameter(
            name=request_param,
            annotation=Optional[Request],
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


class DishkaApp(BaseDishkaApp):
    def _init_request_middleware(
            self, app, container_wrapper: AsyncContextWrapper,
    ):
        app.asgi_handler = make_add_request_container_middleware(
            app.asgi_handler,
        )

    def _app_startup(self, app, container: AsyncContainer):
        app.state.dishka_container = container
