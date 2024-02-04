__all__ = [
    'Depends', "inject", "DishkaApp",
]

from inspect import Parameter
from typing import get_type_hints

from fastapi import Request

from dishka import AsyncContainer
from ..async_container import AsyncContextWrapper
from .asgi import BaseDishkaApp
from .base import Depends, wrap_injection


def inject(func):
    hints = get_type_hints(func)
    request_param = next(
        (name for name, hint in hints.items() if hint is Request),
        None,
    )
    if request_param:
        additional_params = []
    else:
        request_param = "____dishka_request"
        additional_params = [Parameter(
            name=request_param,
            annotation=Request,
            kind=Parameter.KEYWORD_ONLY,
        )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda _, p: p[request_param].state.dishka_container,
        additional_params=additional_params,
        is_async=True,
    )


async def add_request_container_middleware(request: Request, call_next):
    async with request.app.state.dishka_container(
            {Request: request},
    ) as request_container:
        request.state.dishka_container = request_container
        return await call_next(request)


class DishkaApp(BaseDishkaApp):
    def _init_request_middleware(
            self, app, container_wrapper: AsyncContextWrapper,
    ):
        app.middleware("http")(add_request_container_middleware)

    def _app_startup(self, app, container: AsyncContainer):
        app.state.dishka_container = container
