import logging
from typing import Annotated, Callable, Iterable, NewType

import uvicorn
from fastapi import APIRouter
from fastapi import Depends as FastapiDepends
from fastapi import FastAPI

from dishka import Provider, Scope, provide
from dishka.integrations.fastapi import Depends, DishkaApp, inject


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


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.WARNING)

    app = FastAPI()
    app.dependency_overrides[A] = new_a
    app.dependency_overrides[B] = lambda: B(1)
    app.dependency_overrides[C] = lambda: C(1)
    app.include_router(router)
    return DishkaApp(providers=[MyProvider()], app=app)


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
