import logging
from abc import abstractmethod
from typing import Annotated, Protocol

import uvicorn
from litestar import Controller, Litestar, get

from dishka import Provider, Scope, provide, make_async_container
from dishka.integrations.base import FromDishka
from dishka.integrations.litestar import inject, setup_dishka


# app core
class DbGateway(Protocol):
    @abstractmethod
    def get(self) -> str:
        raise NotImplementedError


class FakeDbGateway(DbGateway):
    def get(self) -> str:
        return "Hello123"


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
    async def index(
            self, *, interactor: FromDishka[Interactor],
    ) -> str:
        result = interactor()
        return result


def create_app():
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s  %(process)-7s %(module)-20s %(message)s',
    )
    app = Litestar(route_handlers=[MainController])
    container = make_async_container(InteractorProvider(), AdaptersProvider())
    setup_dishka(container, app)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
