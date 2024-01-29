__all__ = [
    'Depends', "inject", "setup_container", "setup_container_middleware",
]

from inspect import Parameter
from typing import get_type_hints

from fastapi import Request, FastAPI

from dishka import AsyncContainer
from .base import Depends, wrap_injection


def inject(func):
    hints = get_type_hints(func)
    requests_param = next(
        (name for name, hint in hints.items() if hint is Request),
        None,
    )
    if requests_param:
        getter = lambda kwargs: kwargs[requests_param].state.dishka_container
        additional_params = []
    else:
        getter = lambda kwargs: kwargs["___r___"].state.dishka_container
        additional_params = [Parameter(
            name="___r___",
            annotation=Request,
            kind=Parameter.KEYWORD_ONLY,
        )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=getter,
        additional_params=additional_params,
        is_async=True,
    )


async def add_request_container_middleware(request: Request, call_next):
    async with request.app.state.dishka_container(
            {Request: request}
    ) as request_container:
        request.state.dishka_container = request_container
        return await call_next(request)


def setup_container(app: FastAPI, container: AsyncContainer):
    app.state.dishka_container = container


def setup_container_middleware(app: FastAPI):
    app.middleware("http")(add_request_container_middleware)
