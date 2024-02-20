__all__ = [
    'Depends', "inject", "setup_dishka",
]

from inspect import Parameter
from typing import get_type_hints

from fastapi import FastAPI, Request

from dishka import AsyncContainer
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


def setup_dishka(container: AsyncContainer, app: FastAPI) -> None:
    app.middleware("http")(add_request_container_middleware)
    app.state.dishka_container = container
