import random
from contextlib import asynccontextmanager
from enum import auto
from inspect import Parameter
from typing import Annotated, get_type_hints, NewType

import uvicorn
from fastapi import Request, APIRouter, FastAPI

from dishka import AsyncContainer, Provider, provide, Scope
from dishka.inject import wrap_injection, Depends


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


def container_middleware(container):
    async def add_request_container(request: Request, call_next):
        async with container({Request: request}) as subcontainer:
            request.state.container = subcontainer
            return await call_next(request)

    return add_request_container


# app dependency logic

Host = NewType("Host", str)


class MyScope(Scope):
    APP = auto()
    REQUEST = auto()


class MyProvider(Provider):
    @provide(MyScope.APP)
    @asynccontextmanager
    async def get_int(self) -> int:
        print("solve int")
        yield random.randint(0, 10000)

    @provide(MyScope.REQUEST)
    @asynccontextmanager
    async def get_host(self, request: Request) -> Host:
        yield request.client.host


# app
router = APIRouter()


@router.get("/")
@inject
async def index(
        *,
        value: Annotated[int, Depends()],
        host: Annotated[Host, Depends()],
) -> str:
    return f"{value} {host}"


@router.get("/other")
@inject
async def other(
        *,
        request: Request,
        host: Annotated[Host, Depends()],
) -> str:
    return f"{request.client.host} - {host}"


def create_app() -> FastAPI:
    container = AsyncContainer(
        MyProvider(), scope=MyScope.APP, with_lock=True,
    )

    app = FastAPI()
    app.middleware("http")(container_middleware(container))
    app.include_router(router)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
