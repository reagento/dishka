__all__ = [
    "FromDishka",
    "RapidyProvider",
    "inject",
    "setup_dishka",
]

from collections.abc import Callable
from inspect import Parameter
from typing import (
    Annotated,
    Final,
    ParamSpec,
    TypeAlias,
    TypeVar,
    get_type_hints,
)

from aiohttp.web_app import Application
from aiohttp.web_response import StreamResponse
from rapidy.enums import HeaderName
from rapidy.http import Header, Request, middleware
from rapidy.typedefs import CallNext
from rapidy.version import AIOHTTP_VERSION_TUPLE

from dishka import AsyncContainer, FromDishka, Provider, Scope, from_context
from dishka.integrations.base import wrap_injection

if AIOHTTP_VERSION_TUPLE >= (3, 9, 0):
    from aiohttp.web import AppKey

    DISHKA_CONTAINER_KEY: Final[AppKey[AsyncContainer]] = AppKey(
        "dishka_container", AsyncContainer)

else:
    DISHKA_CONTAINER_KEY: Final[str] = "dishka_container"

UpgradeHeader: TypeAlias = Annotated[
    str | None,
    Header(alias=HeaderName.upgrade),
]
ConnectionHeader: TypeAlias = Annotated[
    str | None,
    Header(alias=HeaderName.connection),
]


P = ParamSpec("P")
T = TypeVar("T")


def inject(func: Callable[P, T]) -> Callable[P, T]:
    # WebSocket support will be added later
    return _inject_wrapper(func, "request", Request)


def _inject_wrapper(
        func: Callable[P, T],
        param_name: str,
        param_annotation: type[Request],
) -> Callable[P, T]:
    hints = get_type_hints(
        func,
        # necessary because `rapidy` uses `if TYPE_CHECKING:`
        globalns={"Request": param_annotation},
    )

    request_exists = any(value is Request for value in hints.values())

    if request_exists:
        additional_params = []
    else:
        additional_params = [
            Parameter(
                name=param_name,
                annotation=Request,
                kind=Parameter.KEYWORD_ONLY,
            ),
        ]

    return wrap_injection(
        func=func,
        is_async=True,
        additional_params=additional_params,
        container_getter=lambda _, r: r[param_name][DISHKA_CONTAINER_KEY],
    )


class RapidyProvider(Provider):
    request = from_context(Request, scope=Scope.SESSION)
    # # WebSocket support will be added later.


@middleware
async def _middleware(
    request: Request,
    call_next: CallNext,
    *,
    upgrade_header: UpgradeHeader = None,
    connection_header: ConnectionHeader = None,
) -> StreamResponse:
    container = request.app[DISHKA_CONTAINER_KEY]

    if upgrade_header == "websocket" and connection_header == "Upgrade":
        scope = Scope.SESSION
    else:
        scope = Scope.REQUEST

    context = {Request: request}

    async with container(context=context, scope=scope) as request_container:
        request[DISHKA_CONTAINER_KEY] = request_container
        return await call_next(request)


def setup_dishka(container: AsyncContainer, app: Application) -> None:
    app[DISHKA_CONTAINER_KEY] = container
    app.middlewares.append(_middleware)
