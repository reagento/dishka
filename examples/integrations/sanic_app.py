from typing import Protocol

from sanic import Blueprint, HTTPResponse, Request, Sanic

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.sanic import FromDishka, inject, setup_dishka


class DbGateway(Protocol):
    def get(self) -> str:
        raise NotImplementedError


class FakeDbGateway(DbGateway):
    def get(self) -> str:
        return "Hello, world!"


class Interactor:
    def __init__(self, gateway: DbGateway) -> None:
        self.gateway = gateway

    def __call__(self) -> str:
        return self.gateway.get()


class AdaptersProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_db_gateway(self) -> DbGateway:
        return FakeDbGateway()


class InteractorsProvider(Provider):
    interactor = provide(Interactor, scope=Scope.REQUEST)


bp = Blueprint("example")


@bp.get("/")
@inject
async def index(
    _: Request,
    interactor: FromDishka[Interactor],
) -> HTTPResponse:
    return HTTPResponse(interactor())


@bp.get("/auto")
async def auto(
    _: Request,
    interactor: FromDishka[Interactor],
) -> HTTPResponse:
    return HTTPResponse(interactor())


if __name__ == "__main__":
    app = Sanic(__name__)

    app.blueprint(bp)
    container = make_async_container(AdaptersProvider(), InteractorsProvider())

    setup_dishka(container, app, auto_inject=True)

    app.run(host="127.0.0.1", port=8002, single_process=True)
