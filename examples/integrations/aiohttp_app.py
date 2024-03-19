from typing import Annotated, Protocol

from aiohttp.web import run_app
from aiohttp.web_app import Application
from aiohttp.web_response import Response
from aiohttp.web_routedef import RouteTableDef

from dishka import (
    Provider,
    Scope,
    make_async_container,
    provide,
)
from dishka.integrations.aiohttp import (
    DISHKA_CONTAINER_KEY,
    FromDishka,
    inject,
    setup_dishka,
)


class Gateway(Protocol):
    async def get(self) -> int: ...


class MockGateway(Gateway):
    async def get(self) -> int:
        return hash(self)


class GatewayProvider(Provider):
    get_gateway = provide(MockGateway, scope=Scope.REQUEST, provides=Gateway)


router = RouteTableDef()


@router.get('/')
@inject
async def endpoint(
        request: str, gateway: Annotated[Gateway, FromDishka()],
) -> Response:
    data = await gateway.get()
    return Response(text=f'gateway data: {data}')


async def on_shutdown(app: Application):
    await app[DISHKA_CONTAINER_KEY].close()


app = Application()
app.add_routes(router)

container = make_async_container(GatewayProvider())
setup_dishka(container=container, app=app)
app.on_shutdown.append(on_shutdown)
run_app(app)
