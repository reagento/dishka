__all__ = [
    "DishkaRoute",
    "FastapiProvider",
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Callable
from inspect import Parameter
from typing import Any, ParamSpec, TypeVar, get_type_hints

from fastapi import FastAPI, Request, WebSocket
from fastapi.routing import APIRoute

from dishka import AsyncContainer, FromDishka, Provider, Scope, from_context
from .base import wrap_injection
from .starlette import ContainerMiddleware

T = TypeVar("T")
P = ParamSpec("P")


def inject(func: Callable[P, T]) -> Callable[P, T]:
    hints = get_type_hints(func)
    request_hint = next(
        (name for name, hint in hints.items() if hint is Request),
        None,
    )
    websocket_hint = next(
        (name for name, hint in hints.items() if hint is WebSocket),
        None,
    )
    if request_hint is None and websocket_hint is None:
        additional_params = [
            Parameter(
                name="___dishka_request",
                annotation=Request,
                kind=Parameter.KEYWORD_ONLY,
            ),
        ]
    else:
        additional_params = []
    param_name = request_hint or websocket_hint or "___dishka_request"
    return wrap_injection(
        func=func,
        is_async=True,
        additional_params=additional_params,
        container_getter=lambda _, p: p[param_name].state.dishka_container,
    )


class DishkaRoute(APIRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        **kwargs: Any,
    ) -> None:
        endpoint = inject(endpoint)
        super().__init__(path, endpoint, **kwargs)


class FastapiProvider(Provider):
    request = from_context(Request, scope=Scope.REQUEST)
    websocket = from_context(WebSocket, scope=Scope.SESSION)


def setup_dishka(container: AsyncContainer, app: FastAPI) -> None:
    app.add_middleware(ContainerMiddleware)
    app.state.dishka_container = container
