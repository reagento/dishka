import asyncio
import logging
from collections.abc import AsyncIterable, Callable
from typing import Annotated, NewType

import uvicorn
from fastapi import APIRouter, FastAPI
from fastapi import Depends as FastapiDepends

from dishka import Provider, Scope, make_async_container, provide
from dishka.integrations.fastapi import Depends, inject


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
    async def get_b(self) -> AsyncIterable[B]:
        await asyncio.sleep(0.000001)
        yield B(1)

    @provide(scope=Scope.REQUEST)
    async def get_c(self) -> AsyncIterable[C]:
        await asyncio.sleep(0.0000001)
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


async def get_b() -> AsyncIterable[B]:
    await asyncio.sleep(0.000001)
    yield B(1)


async def get_c() -> AsyncIterable[C]:
    await asyncio.sleep(0.0000001)
    yield C(1)


def create_app() -> FastAPI:
    logging.basicConfig(level=logging.WARNING)

    app = FastAPI()
    app.dependency_overrides[A] = new_a
    app.dependency_overrides[B] = get_b
    app.dependency_overrides[C] = get_c
    app.include_router(router)
    c = make_async_container(MyProvider())
    # setup_dishka(container=c, app=app)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
