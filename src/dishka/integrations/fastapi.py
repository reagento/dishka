__all__ = [
    "Depends",
    "FromDishka",
    "inject",
    "setup_dishka",
]

from inspect import Parameter
from typing import get_type_hints

from fastapi import FastAPI, Request

from dishka import AsyncContainer, FromDishka
from .base import Depends, wrap_injection
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


def setup_dishka(container: AsyncContainer, app: FastAPI) -> None:
    app.add_middleware(ContainerMiddleware)
    app.state.dishka_container = container
