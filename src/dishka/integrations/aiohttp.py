__all__ = [
    "DISHKA_CONTAINER_KEY",
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Callable
from typing import Final

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse

from dishka import AsyncContainer, FromDishka
from dishka.integrations.base import wrap_injection

DISHKA_CONTAINER_KEY: Final = web.AppKey("dishka_container", AsyncContainer)


def inject(func: Callable) -> Callable:
    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda p, _: p[0][DISHKA_CONTAINER_KEY],
        is_async=True,
    )


@web.middleware
async def container_middleware(
    request: Request, handler: Handler,
) -> StreamResponse:
    container = request.app[DISHKA_CONTAINER_KEY]
    async with container(context={Request: request}) as request_container:
        request[DISHKA_CONTAINER_KEY] = request_container
        return await handler(request)


def setup_dishka(container: AsyncContainer, app: Application) -> None:
    app[DISHKA_CONTAINER_KEY] = container
    app.middlewares.append(container_middleware)
