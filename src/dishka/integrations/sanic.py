__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Awaitable, Callable, Iterable

from sanic import HTTPResponse, Request, Sanic
from sanic_routing import Route

from dishka import AsyncContainer, FromDishka
from dishka.integrations.base import is_dishka_injected, wrap_injection


def inject(func: Callable) -> Awaitable:
    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda args, _: args[0].ctx.dishka_container,
        is_async=True,
    )


class ContainerMiddleware:
    def __init__(self, container: AsyncContainer) -> None:
        self.container = container

    async def on_request(self, request: Request) -> None:
        request.ctx.container_wrapper = self.container({Request: request})
        request.ctx.dishka_container = await request.ctx.container_wrapper.__aenter__()  # noqa: E501

    async def on_response(self, request: Request, _: HTTPResponse) -> None:
        await request.ctx.dishka_container.close()


def _inject_routes(routes: Iterable[Route]) -> None:
    for route in routes:
        if not is_dishka_injected(route.handler):
            route.handler = inject(route.handler)


def setup_dishka(
    container: AsyncContainer,
    app: Sanic,
    *,
    auto_inject: bool = False,
) -> None:
    middleware = ContainerMiddleware(container)
    app.on_request(middleware.on_request)
    app.on_response(middleware.on_response)

    if auto_inject:
        _inject_routes(app.router.routes)
        for blueprint in app.blueprints.values():
            _inject_routes(blueprint.routes)
