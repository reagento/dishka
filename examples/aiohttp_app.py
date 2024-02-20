from typing import Annotated, Protocol

from aiohttp.web import run_app
from aiohttp.web_app import Application
from aiohttp.web_response import Response
from aiohttp.web_routedef import RouteTableDef

from dishka import (
    AsyncContainer,
    Provider,
    Scope,
    make_async_container,
    provide,
)
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


def shutdown(container: AsyncContainer):
    async def wrapper(app: Application) -> None:
        await container.close()

    return wrapper


app = Application()
app.add_routes(router)

container = make_async_container(GatewayProvider())
setup_dishka(container=container, app=app)
app.on_shutdown.append(shutdown(container))
run_app(app)
