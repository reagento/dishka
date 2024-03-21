import logging
from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import Annotated, Protocol

import uvicorn
from fastapi import APIRouter, FastAPI

from dishka import (
    Provider,
    Scope,
    make_async_container,
    provide,
)
from dishka.integrations.fastapi import (
    DishkaRoute,
    FromDishka,
    inject,
    setup_dishka,
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


# presentation layer
router = APIRouter()


@router.get("/")
@inject
async def index(
        *,
        interactor: FromDishka[Interactor],
) -> str:
    result = interactor()
    return result


# with this router you do not need `@inject` on each view
second_router = APIRouter(route_class=DishkaRoute)


@second_router.get("/auto")
async def auto(
        *,
        interactor: FromDishka[Interactor],
) -> str:
    result = interactor()
    return result


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.dishka_container.close()


def create_app():
    logging.basicConfig(
        level=logging.WARNING,
        format='%(asctime)s  %(process)-7s %(module)-20s %(message)s',
    )

    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    app.include_router(second_router)
    container = make_async_container(AdaptersProvider(), InteractorProvider())
    setup_dishka(container, app)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000, lifespan="on")
