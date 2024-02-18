from typing import Callable, Final

from aiohttp import web
from aiohttp.typedefs import Handler
from aiohttp.web_app import Application
from aiohttp.web_request import Request
from aiohttp.web_response import StreamResponse

from dishka import Provider, make_async_container
from dishka.async_container import AsyncContextWrapper
from dishka.integrations.base import wrap_injection

CONTAINER_KEY: Final = 'dishka_container'


def inject(func: Callable) -> Callable:
    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda p, _: p[0].app[CONTAINER_KEY],
        is_async=True,
    )


@web.middleware
async def container_middleware(
    request: Request, handler: Handler,
) -> StreamResponse:
    container = request.app['__container__']
    async with container() as container_:
        request.app[CONTAINER_KEY] = container_
        res = await handler(request)
    return res


def startup(wrapper_container: AsyncContextWrapper):
    async def wrapper(app: Application) -> None:
        app['__container__'] = await wrapper_container.__aenter__()
    return wrapper


def shutdown(wrapper_container: AsyncContextWrapper):
    async def wrapper(app: Application) -> None:
        await wrapper_container.__aexit__(None, None, None)
    return wrapper


def setup_dishka(*provides: Provider, app: Application) -> None:
    wrapper_container = make_async_container(*provides)
    app.middlewares.append(container_middleware)
    app.on_startup.append(startup(wrapper_container))
    app.on_shutdown.append(shutdown(wrapper_container))
