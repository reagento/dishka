__all__ = [
    "Depends", "inject", "setup_dishka",
]

from typing import Callable, Final

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse

from dishka.async_container import AsyncContainer
from dishka.integrations.base import Depends, wrap_injection

CONTAINER_KEY: Final = web.AppKey('dishka_container', AsyncContainer)


def inject(func: Callable) -> Callable:
    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda p, _: p[0][CONTAINER_KEY],
        is_async=True,
    )


@web.middleware
async def container_middleware(
    request: Request, handler: Handler,
) -> StreamResponse:
    container = request.app[CONTAINER_KEY]
    async with container(context={Request: request}) as request_container:
        request[CONTAINER_KEY] = request_container
        res = await handler(request)
    return res


def setup_dishka(container: AsyncContainer, app: Application) -> None:
    app[CONTAINER_KEY] = container
    app.middlewares.append(container_middleware)
