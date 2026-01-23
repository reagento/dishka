__all__ = [
    "PyramidProvider",
    "inject",
    "setup_dishka",
]


from collections.abc import Callable
from typing import Final, ParamSpec, TypeVar

from pyramid.config import Configurator
from pyramid.registry import Registry
from pyramid.request import Request
from pyramid.response import Response

from dishka import Container, Provider, Scope, from_context
from dishka.integrations.base import wrap_injection

CONTAINER_WRAPPER_NAME: Final[str] = "dishka_container_wrapper"
CONTAINER_NAME: Final[str] = "dishka_container"


T = TypeVar("T")
P = ParamSpec("P")


class PyramidProvider(Provider):
    request = from_context(provides=Request, scope=Scope.REQUEST)


def inject(func: Callable[P, T]) -> Callable[P, T]:
    return wrap_injection(
        func=func,
        is_async=False,
        container_getter=lambda args, kwargs: getattr(args[0], CONTAINER_NAME),
    )


def dishka_middleware(handler: Callable[P, T], registry: Registry) -> Callable:
    def wrapper(request: Request) -> Response:
        app_container: Container = registry[CONTAINER_WRAPPER_NAME]

        with app_container(context={Request: request}) as request_container:
            setattr(request, CONTAINER_NAME, request_container)
            return handler(request)

    return wrapper


def setup_dishka(container: Container, config: Configurator) -> None:
    config.registry[CONTAINER_WRAPPER_NAME] = container
    config.add_tween("dishka.integrations.pyramid.dishka_middleware")

    def close_dishka_container():
        container.close()

    config.action(None, close_dishka_container, order=999999)
