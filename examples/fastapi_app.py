import logging
from abc import abstractmethod
from contextlib import asynccontextmanager
from typing import Annotated, Protocol

import uvicorn
from fastapi import APIRouter
from fastapi import FastAPI

from dishka import (
    Provider, Scope, make_async_container, provide,
)
from dishka.integrations.fastapi import (
    Depends, inject, setup_container, setup_container_middleware,
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
        interactor: Annotated[Interactor, Depends()],
) -> str:
    result = interactor()
    return result


# app configuration
@asynccontextmanager
async def lifespan(app: FastAPI):
    async with make_async_container(
            AdaptersProvider(), InteractorProvider(),
            with_lock=True,
    ) as container:
        setup_container(app, container)
        yield


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.WARNING)

    app = FastAPI(lifespan=lifespan)
    setup_container_middleware(app)
    app.include_router(router)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
