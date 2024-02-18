from typing import Annotated, Protocol

from aiohttp.web import run_app
from aiohttp.web_app import Application
from aiohttp.web_response import Response
from aiohttp.web_routedef import RouteTableDef

from dishka import Provider, Scope, provide
from dishka.integrations.aiohttp import inject, setup_dishka
from dishka.integrations.base import Depends


class Gateway(Protocol):
    async def get(self) -> int: ...


class MockGateway(Gateway):
    async def get(self) -> int:
        return hash(self)


class GatewayProvider(Provider):
    get_gateway = provide(MockGateway, scope=Scope.REQUEST, provides=Gateway)


GatewayDepends = Annotated[Gateway, Depends()]
router = RouteTableDef()


@router.get('/')
@inject
async def endpoint(request: str, gateway: GatewayDepends) -> Response:
    data = await gateway.get()
    return Response(text=f'gateway data: {data}')

app = Application()
app.add_routes(router)
setup_dishka(providers=[GatewayProvider()], app=app)
run_app(app)
