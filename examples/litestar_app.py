import logging
from abc import abstractmethod
from typing import Protocol, Annotated

import uvicorn
from litestar import Controller, get, Litestar

from dishka import Provider, Scope, provide
from dishka.integrations.base import Depends
from dishka.integrations.litestar import (
    inject,
    setup_dishka,
    startup_dishka,
    make_dishka_container,
    shutdown_dishka
)


# app core
class DbGateway(Protocol):
    @abstractmethod
    def get(self) -> str:
        raise NotImplementedError


class FakeDbGateway(DbGateway):
    def get(self) -> str:
        return "Hello"


class Interactor:
    def __init__(self, db: DbGateway):
        self.db = db

    def __call__(self) -> str:
        return self.db.get()


# app dependency logic
class AdaptersProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_db(self) -> DbGateway:
        return FakeDbGateway()


class InteractorProvider(Provider):
    i1 = provide(Interactor, scope=Scope.REQUEST)


class MainController(Controller):
    path = '/'

    @get()
    @inject
    async def index(self, *, interactor: Annotated[Interactor, Depends()]) -> str:
        result = interactor()
        return result


def create_app():
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s  %(process)-7s %(module)-20s %(message)s',
    )
    app = Litestar(
        route_handlers=[MainController],
        on_startup=[startup_dishka],
        on_shutdown=[shutdown_dishka],
        before_request=make_dishka_container
    )
    return setup_dishka(app, [InteractorProvider(), AdaptersProvider()])


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
