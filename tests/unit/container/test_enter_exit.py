import pytest

from dishka import (
    Provider,
    Scope,
    make_async_container,
    make_container,
    provide,
)
from ..sample_providers import (
    ClassA,
    sync_gen_a,
)


@pytest.mark.parametrize(
    ("provide_scope", "start_scope", "expected_scope"),
    [
        (Scope.RUNTIME, Scope.APP, Scope.APP),
        (Scope.APP, Scope.APP, Scope.APP),
        (Scope.APP, None, Scope.APP),
    ],
)
def test_sync_create(provide_scope, start_scope, expected_scope):
    class MyProvider(Provider):
        a = provide(sync_gen_a, scope=provide_scope)

        @provide(scope=provide_scope)
        def get_int(self) -> int:
            return 100

    container = make_container(MyProvider(), start_scope=start_scope)
    assert container.registry.scope is expected_scope
    a = container.get(ClassA)
    assert a
    assert a.dep == 100
    container.close()
    assert a.closed


@pytest.mark.parametrize(
    ("provide_scope", "start_scope", "expected_scope"),
    [
        (Scope.RUNTIME, Scope.APP, Scope.APP),
        (Scope.APP, Scope.APP, Scope.APP),
        (Scope.APP, None, Scope.APP),
    ],
)
@pytest.mark.asyncio
async def test_async_create(provide_scope, start_scope, expected_scope):
    class MyProvider(Provider):
        a = provide(sync_gen_a, scope=provide_scope)

        @provide(scope=provide_scope)
        def get_int(self) -> int:
            return 100

    container = make_async_container(MyProvider(), start_scope=start_scope)
    assert container.registry.scope is expected_scope
    a = await container.get(ClassA)
    assert a
    assert a.dep == 100
    await container.close()
    assert a.closed


@pytest.mark.parametrize(
    ("provide_scope", "start_scope", "expected_scope"),
    [
        (Scope.SESSION, Scope.REQUEST, Scope.REQUEST),
        (Scope.REQUEST, Scope.REQUEST, Scope.REQUEST),
        (Scope.REQUEST, Scope.STEP, Scope.STEP),
        (Scope.REQUEST, None, Scope.REQUEST),
    ],
)
def test_sync_enter(provide_scope, start_scope, expected_scope):
    class MyProvider(Provider):
        a = provide(sync_gen_a, scope=provide_scope)

        @provide(scope=provide_scope)
        def get_int(self) -> int:
            return 100

    base_container = make_container(MyProvider())
    with base_container(scope=start_scope) as container:
        assert container.registry.scope is expected_scope
        a = container.get(ClassA)
        assert a
        assert a.dep == 100
    assert a.closed


@pytest.mark.parametrize(
    ("provide_scope", "start_scope", "expected_scope"),
    [
        (Scope.SESSION, Scope.REQUEST, Scope.REQUEST),
        (Scope.REQUEST, Scope.REQUEST, Scope.REQUEST),
        (Scope.REQUEST, Scope.STEP, Scope.STEP),
        (Scope.REQUEST, None, Scope.REQUEST),
    ],
)
@pytest.mark.asyncio
async def test_async_enter(provide_scope, start_scope, expected_scope):
    class MyProvider(Provider):
        a = provide(sync_gen_a, scope=provide_scope)

        @provide(scope=provide_scope)
        def get_int(self) -> int:
            return 100

    base_container = make_async_container(MyProvider())
    async with base_container(scope=start_scope) as container:
        assert container.registry.scope is expected_scope
        a = await container.get(ClassA)
        assert a
        assert a.dep == 100
    assert a.closed


def test_sync_exit_one():
    class MyProvider(Provider):
        a = provide(sync_gen_a, scope=Scope.RUNTIME)

        @provide(scope=Scope.RUNTIME)
        def get_int(self) -> int:
            return 100

    base_container = make_container(MyProvider(), start_scope=Scope.RUNTIME)
    with base_container() as container:
        a = container.get(ClassA)
    assert not a.closed


@pytest.mark.asyncio
async def test_async_exit_one():
    class MyProvider(Provider):
        a = provide(sync_gen_a, scope=Scope.RUNTIME)

        @provide(scope=Scope.RUNTIME)
        def get_int(self) -> int:
            return 100

    base_container = make_async_container(MyProvider(),
                                          start_scope=Scope.RUNTIME)
    async with base_container() as container:
        a = await container.get(ClassA)
    assert not a.closed
