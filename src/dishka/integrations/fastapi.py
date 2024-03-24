__all__ = [
    "DishkaRoute",
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Callable
from inspect import Parameter
from typing import Any, get_type_hints

from fastapi import FastAPI, Request
from fastapi.routing import APIRoute

from dishka import AsyncContainer, FromDishka
from .base import wrap_injection
from .starlette import ContainerMiddleware


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


class DishkaRoute(APIRoute):
    def __init__(
            self, path: str, endpoint: Callable[..., Any], **kwargs,
    ):
        endpoint = inject(endpoint)
        super().__init__(path, endpoint, **kwargs)


def setup_dishka(container: AsyncContainer, app: FastAPI) -> None:
    app.add_middleware(ContainerMiddleware)
    app.state.dishka_container = container
