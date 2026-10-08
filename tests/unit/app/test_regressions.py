from collections.abc import AsyncGenerator, Generator
from contextlib import closing

import pytest

from dishka import (
    DishkaApp,
    DishkaModule,
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)
from .forward_annotations import (
    Dependency,
    generate,
    generate_async,
    module,
)


def test_generator_throw_preserves_exception_and_traceback():
    handlers = DishkaModule()
    received = []

    @handlers.inject
    def generate_values():
        try:
            yield "ready"
        except ValueError as error:
            received.append(error)
            yield error.__traceback__

    error = ValueError("failure")
    try:
        raise error
    except ValueError:
        original_traceback = error.__traceback__

    with DishkaApp(make_container()) as app:
        app.include(handlers)
        with closing(generate_values()) as iterator:
            assert next(iterator) == "ready"
            traceback = iterator.throw(error)
            while (
                traceback is not None and traceback is not original_traceback
            ):
                traceback = traceback.tb_next
            assert traceback is original_traceback
            assert received == [error]


def test_generator_forward_annotations():
    provider = Provider()
    provider.provide(Dependency, scope=Scope.REQUEST)
    with DishkaApp(make_container(provider)) as app:
        app.include(module)
        values = list(generate())
        assert len(values) == 1
        assert isinstance(values[0], Dependency)


@pytest.mark.asyncio
async def test_async_generator_forward_annotations():
    provider = Provider()
    provider.provide(Dependency, scope=Scope.REQUEST)
    async with DishkaApp(make_async_container(provider)) as app:
        app.include(module)
        values = [value async for value in generate_async()]
        assert isinstance(values[0], Dependency)


def test_exit_exception_reaches_provider():
    received = []

    class Resources(Provider):
        @provide(scope=Scope.APP)
        def resource(self) -> Generator[int, BaseException | None, None]:
            received.append((yield 1))

    error = ValueError("application failure")
    container = make_container(Resources())
    container.get(int)

    def run():
        with DishkaApp(container):
            raise error

    with pytest.raises(ValueError, match="application failure"):
        run()
    assert received == [error]


@pytest.mark.asyncio
async def test_async_exit_exception_reaches_provider():
    received = []

    class Resources(Provider):
        @provide(scope=Scope.APP)
        async def resource(self) -> AsyncGenerator[int, BaseException | None]:
            received.append((yield 1))

    error = ValueError("application failure")
    container = make_async_container(Resources())
    await container.get(int)

    async def run():
        async with DishkaApp(container):
            raise error

    with pytest.raises(ValueError, match="application failure"):
        await run()
    assert received == [error]
