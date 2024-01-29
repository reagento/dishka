import logging
from abc import abstractmethod
from contextlib import asynccontextmanager
from inspect import Parameter
from typing import (
    Annotated, get_type_hints, Protocol, Any, get_origin,
    get_args,
)

import uvicorn
from fastapi import APIRouter
from fastapi import FastAPI, Request

from dishka import (
    Depends, wrap_injection, Provider, Scope, make_async_container, provide,
)


# framework level
def inject(func):
    hints = get_type_hints(func)
    requests_param = next(
        (name for name, hint in hints.items() if hint is Request),
        None,
    )
    if requests_param:
        getter = lambda kwargs: kwargs[requests_param].state.container
        additional_params = []
    else:
        getter = lambda kwargs: kwargs["___r___"].state.container
        additional_params = [Parameter(
            name="___r___",
            annotation=Request,
            kind=Parameter.KEYWORD_ONLY,
        )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=getter,
        additional_params=additional_params,
        is_async=True,
    )


def container_middleware():
    async def add_request_container(request: Request, call_next):
        async with request.app.state.container(
                {Request: request}
        ) as subcontainer:
            request.state.container = subcontainer
            return await call_next(request)

    return add_request_container


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
    ) as container:
        app.state.container = container
        yield


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.WARNING)

    app = FastAPI(lifespan=lifespan)
    app.middleware("http")(container_middleware())
    app.include_router(router)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
