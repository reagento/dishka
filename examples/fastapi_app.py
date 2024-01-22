import logging
from contextlib import asynccontextmanager
from inspect import Parameter
from typing import Annotated, get_type_hints, NewType, Callable, Iterable

import uvicorn
from fastapi import Request, APIRouter, FastAPI, Depends as FastapiDepends

from dishka import Provider, provide, Scope, make_async_container
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


def container_middleware():
    async def add_request_container(request: Request, call_next):
        async with request.app.state.container({Request: request}) as subcontainer:
            request.state.container = subcontainer
            return await call_next(request)

    return add_request_container


class Stub:
    def __init__(self, dependency: Callable, **kwargs):
        self._dependency = dependency
        self._kwargs = kwargs

    def __call__(self):
        raise NotImplementedError

    def __eq__(self, other) -> bool:
        if isinstance(other, Stub):
            return (
                    self._dependency == other._dependency
                    and self._kwargs == other._kwargs
            )
        else:
            if not self._kwargs:
                return self._dependency == other
            return False

    def __hash__(self):
        if not self._kwargs:
            return hash(self._dependency)
        serial = (
            self._dependency,
            *self._kwargs.items(),
        )
        return hash(serial)


# app dependency logic

Host = NewType("Host", str)


class B:
    def __init__(self, x: int):
        pass


class C:
    def __init__(self, x: int):
        pass


class A:
    def __init__(self, b: B, c: C):
        pass


MyInt = NewType("MyInt", int)


class MyProvider(Provider):
    @provide(scope=Scope.REQUEST)
    async def get_a(self, b: B, c: C) -> A:
        return A(b, c)

    @provide(scope=Scope.REQUEST)
    async def get_b(self) -> Iterable[B]:
        yield B(1)

    @provide(scope=Scope.REQUEST)
    async def get_c(self) -> Iterable[C]:
        yield C(1)


# app
router = APIRouter()


@router.get("/")
@inject
async def index(
        *,
        value: Annotated[A, Depends()],
        value2: Annotated[A, Depends()],
) -> str:
    return f"{value} {value is value2}"


@router.get("/f")
async def index(
        *,
        value: Annotated[A, FastapiDepends(Stub(A))],
        value2: Annotated[A, FastapiDepends(Stub(A))],
) -> str:
    return f"{value} {value is value2}"


def new_a(b: B = FastapiDepends(Stub(B)), c: C = FastapiDepends(Stub(C))):
    return A(b, c)


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with make_async_container(MyProvider(), with_lock=True) as container:
        app.state.container = container
        yield


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.WARNING)

    app = FastAPI(lifespan=lifespan)
    app.middleware("http")(container_middleware())
    app.dependency_overrides[A] = new_a
    app.dependency_overrides[B] = lambda: B(1)
    app.dependency_overrides[C] = lambda: C(1)
    app.include_router(router)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
