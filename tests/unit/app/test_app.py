import asyncio
from collections.abc import AsyncIterator, Iterator
from concurrent.futures import ThreadPoolExecutor
from contextlib import aclosing, closing
from inspect import (
    isasyncgenfunction,
    iscoroutinefunction,
    isgeneratorfunction,
    signature,
)
from threading import Barrier
from typing import Annotated

import pytest

from dishka import (
    BaseScope,
    DishkaApp,
    DishkaModule,
    FromComponent,
    FromDishka,
    Provider,
    Scope,
    make_async_container,
    make_container,
    new_scope,
    provide,
)
from dishka.app.exceptions import (
    ActiveAppScopesError,
    AppAlreadyEnteredError,
    AppScopeClosedError,
    AsyncAppRequiredError,
    ModuleNotIncludedError,
    NoActiveAppError,
)
from dishka.integrations.exceptions import InvalidInjectedFuncTypeError


class Resource:
    def __init__(self) -> None:
        self.closed = False


class AppResource(Resource):
    pass


class Resources(Provider):
    @provide(scope=Scope.APP)
    def app_resource(self) -> Iterator[AppResource]:
        resource = AppResource()
        try:
            yield resource
        finally:
            resource.closed = True

    @provide(scope=Scope.REQUEST)
    def resource(self, app: AppResource) -> Iterator[Resource]:
        resource = Resource()
        try:
            yield resource
        finally:
            resource.closed = True


handlers = DishkaModule()


@handlers.inject
def get_resource(resource: FromDishka[Resource]) -> Resource:
    """Return the injected resource."""
    assert not resource.closed
    return resource


class Commands:
    @handlers.inject
    def report(self, filename: str, resource: FromDishka[Resource]):
        return filename, resource

    @staticmethod
    @handlers.inject
    def static_report(resource: FromDishka[Resource]):
        return resource

    @classmethod
    @handlers.inject
    def class_report(cls, resource: FromDishka[Resource]):
        return cls, resource


def test_direct_calls_and_lifecycle():
    container = make_container(Resources())
    with DishkaApp(container) as app:
        app.include(handlers)
        app.include(handlers)
        root = container.get(AppResource)
        first = get_resource()
        second = get_resource()
        assert first is not second
        assert first.closed
        assert second.closed
        assert not root.closed
        name, resource = Commands().report("input.txt")
        assert name == "input.txt"
        assert resource.closed
        assert Commands.static_report().closed
        cls, resource = Commands.class_report()
        assert cls is Commands
        assert resource.closed
    assert root.closed
    with pytest.raises(NoActiveAppError):
        get_resource()


def test_signature():
    assert list(signature(get_resource).parameters) == []
    assert list(signature(Commands().report).parameters) == ["filename"]
    assert get_resource.__name__ == "get_resource"
    assert get_resource.__doc__ == "Return the injected resource."


def test_wrapper_function_types():
    module = DishkaModule()

    @module.inject
    def synchronous(resource: FromDishka[Resource]):
        return resource

    @module.inject
    async def asynchronous(resource: FromDishka[Resource]):
        return resource

    @module.inject
    def generator(resource: FromDishka[Resource]):
        yield resource

    @module.inject
    async def async_generator(resource: FromDishka[Resource]):
        yield resource

    assert not iscoroutinefunction(synchronous)
    assert not isgeneratorfunction(synchronous)
    assert iscoroutinefunction(asynchronous)
    assert isgeneratorfunction(generator)
    assert isasyncgenfunction(async_generator)
    for function in (synchronous, asynchronous, generator, async_generator):
        assert list(signature(function).parameters) == []


def test_nested_entry_without_dependencies():
    @handlers.inject
    def outer():
        first = get_resource()
        second = get_resource()
        assert first is second
        assert not first.closed
        return first

    with DishkaApp(make_container(Resources())) as app:
        app.include(handlers)
        assert outer().closed


def test_errors_and_reentry():
    with pytest.raises(NoActiveAppError):
        get_resource()
    app = DishkaApp(make_container(Resources()))
    with app:
        with pytest.raises(ModuleNotIncludedError):
            get_resource()
        with pytest.raises(AppAlreadyEnteredError):
            app.__enter__()
    with pytest.raises(AppAlreadyEnteredError):
        app.__enter__()


def test_nested_app_restores_context():
    @handlers.inject
    def outer():
        first = get_resource()
        with DishkaApp(make_container(Resources())) as other:
            other.include(handlers)
            second = get_resource()
            assert second is not first
            assert second.closed
        assert get_resource() is first
        return first

    with DishkaApp(make_container(Resources())) as app:
        app.include(handlers)
        assert outer().closed


def test_exception_cleanup():
    resources = []

    @handlers.inject
    def fail(resource: FromDishka[Resource]):
        resources.append(resource)
        raise ValueError("failure")

    container = make_container(Resources())
    with DishkaApp(container) as app:
        app.include(handlers)
        root = container.get(AppResource)
        with pytest.raises(ValueError, match="failure"):
            fail()
        assert not root.closed
    assert root.closed
    assert resources[0].closed
    with pytest.raises(NoActiveAppError):
        get_resource()


def test_custom_scope_and_context():
    provider = Provider()
    provider.from_context(int, scope=Scope.ACTION)
    provider.provide(Resource, scope=Scope.REQUEST)

    @handlers.inject(
        scope=Scope.ACTION,
        provide_context=lambda args, kwargs: {int: args[0]},
    )
    def action(value: int, injected: FromDishka[int]):
        return injected

    @handlers.inject
    def outer(resource: FromDishka[Resource]):
        return action(42)

    with DishkaApp(make_container(provider)) as app:
        app.include(handlers)
        assert outer() == 42


def test_component():
    module = DishkaModule()
    provider = Provider(component="named")
    provider.provide(Resource, scope=Scope.REQUEST)

    @module.inject
    def handle(resource: Annotated[Resource, FromComponent("named")]):
        return resource

    with DishkaApp(make_container(provider)) as app:
        app.include(module)
        assert isinstance(handle(), Resource)


def test_app_inject():
    with DishkaApp(make_container(Resources())) as app:
        @app.inject
        def handle(resource: FromDishka[Resource]):
            return resource

        assert handle().closed


def test_thread_isolation():
    barrier = Barrier(2, timeout=5)

    def run():
        with DishkaApp(make_container(Resources())) as app:
            app.include(handlers)
            barrier.wait()
            resource = get_resource()
            barrier.wait()
            return resource

    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(lambda _: run(), range(4)))
    assert len({id(resource) for resource in results}) == 4
    assert all(resource.closed for resource in results)


def test_generator_scope_and_protocol():
    @handlers.inject
    def generate(resource: FromDishka[Resource]):
        try:
            value = yield resource
            assert value == "sent"
            assert get_resource() is resource
            yield resource
        except ValueError:
            yield resource
        return "done"

    with DishkaApp(make_container(Resources())) as app:
        app.include(handlers)
        with closing(generate()) as iterator:
            resource = next(iterator)
            assert not resource.closed
            assert get_resource() is not resource
            assert iterator.send("sent") is resource
            assert iterator.throw(ValueError) is resource
            with pytest.raises(StopIteration) as error:
                next(iterator)
            assert error.value.value == "done"
        assert resource.closed
        with closing(generate()) as iterator:
            resource = next(iterator)
        assert resource.closed


class AsyncResources(Provider):
    @provide(scope=Scope.APP)
    async def app_resource(self) -> AsyncIterator[AppResource]:
        resource = AppResource()
        try:
            yield resource
        finally:
            resource.closed = True

    @provide(scope=Scope.REQUEST)
    async def resource(self, app: AppResource) -> AsyncIterator[Resource]:
        resource = Resource()
        try:
            yield resource
        finally:
            resource.closed = True


@handlers.inject
async def async_resource(resource: FromDishka[Resource]) -> Resource:
    assert not resource.closed
    await asyncio.sleep(0)
    return resource


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_async_calls(asynchronous):
    container = (
        make_async_container(AsyncResources()) if asynchronous
        else make_container(Resources())
    )
    async with DishkaApp(container) as app:
        app.include(handlers)
        first, second = await asyncio.gather(
            async_resource(), async_resource(),
        )
        assert first is not second
        assert first.closed
        assert second.closed


@pytest.mark.asyncio
async def test_async_nested_and_cleanup():
    @handlers.inject
    async def outer():
        first = await async_resource()
        second = await async_resource()
        assert first is second
        assert not first.closed
        return first

    container = make_async_container(AsyncResources())
    async with DishkaApp(container) as app:
        app.include(handlers)
        root = await container.get(AppResource)
        assert (await outer()).closed
        assert not root.closed
        with pytest.raises(InvalidInjectedFuncTypeError):
            get_resource()
    assert root.closed


@pytest.mark.asyncio
async def test_wrong_context_manager():
    app = DishkaApp(make_async_container(AsyncResources()))
    with pytest.raises(AsyncAppRequiredError):
        app.__enter__()
    async with app:
        app.include(handlers)
        assert (await async_resource()).closed


@pytest.mark.asyncio
async def test_async_generator_early_close():
    finalized = []

    @handlers.inject
    async def generate(resource: FromDishka[Resource]):
        try:
            assert await async_resource() is resource
            yield resource
        finally:
            assert not resource.closed
            finalized.append(resource)

    async with DishkaApp(make_async_container(AsyncResources())) as app:
        app.include(handlers)
        async with aclosing(generate()) as iterator:
            resource = await anext(iterator)
            assert not resource.closed
            assert await async_resource() is not resource
        assert resource.closed
        assert finalized == [resource]


@pytest.mark.asyncio
async def test_async_generator_protocol():
    @handlers.inject
    async def generate(resource: FromDishka[Resource]):
        try:
            value = yield resource
            assert value == "sent"
            assert await async_resource() is resource
            yield value
        except ValueError:
            yield "handled"

    async with DishkaApp(make_async_container(AsyncResources())) as app:
        app.include(handlers)
        async with aclosing(generate()) as iterator:
            resource = await anext(iterator)
            assert await iterator.asend("sent") == "sent"
            assert await iterator.athrow(ValueError) == "handled"
        assert resource.closed


@pytest.mark.asyncio
async def test_cancellation():
    started = asyncio.Event()
    resources = []

    @handlers.inject
    async def wait(resource: FromDishka[Resource]):
        resources.append(resource)
        started.set()
        await asyncio.Event().wait()

    async with DishkaApp(make_async_container(AsyncResources())) as app:
        app.include(handlers)
        task = asyncio.create_task(wait())
        await started.wait()
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert resources[0].closed
        assert (await async_resource()).closed


@pytest.mark.asyncio
async def test_inherited_closed_scope():
    proceed = asyncio.Event()

    async def background():
        await proceed.wait()
        return await async_resource()

    @handlers.inject
    async def outer():
        return asyncio.create_task(background())

    async with DishkaApp(make_async_container(AsyncResources())) as app:
        app.include(handlers)
        task = await outer()
        proceed.set()
        with pytest.raises(AppScopeClosedError):
            await task


@pytest.mark.asyncio
async def test_parallel_apps():
    async def run(value):
        provider = Provider()
        provider.from_context(int, scope=Scope.APP)

        @handlers.inject
        async def handle(injected: FromDishka[int]):
            await asyncio.sleep(0)
            return injected

        container = make_async_container(provider, context={int: value})
        async with DishkaApp(container) as app:
            app.include(handlers)
            return await handle()

    assert await asyncio.gather(run(1), run(2)) == [1, 2]


@pytest.mark.asyncio
async def test_parallel_nested_calls_share_scope():
    created = 0
    release = asyncio.Event()

    class ParallelProvider(Provider):
        @provide(scope=Scope.REQUEST)
        async def resource(self) -> Resource:
            nonlocal created
            created += 1
            await release.wait()
            return Resource()

    @handlers.inject
    async def nested(resource: FromDishka[Resource]):
        return resource

    @handlers.inject
    async def outer():
        first = asyncio.create_task(nested())
        second = asyncio.create_task(nested())
        await asyncio.sleep(0)
        release.set()
        return await asyncio.gather(first, second)

    async with DishkaApp(make_async_container(ParallelProvider())) as app:
        app.include(handlers)
        first, second = await outer()
        assert first is second
        assert created == 1


def test_open_generator_prevents_app_close():
    container = make_container(Resources())
    app = DishkaApp(container)
    app.__enter__()
    app.include(handlers)
    root = container.get(AppResource)

    @handlers.inject
    def generate(resource: FromDishka[Resource]):
        yield resource

    iterator = generate()
    resource = next(iterator)
    with pytest.raises(ActiveAppScopesError):
        app.__exit__(None, None, None)
    assert not resource.closed
    assert not root.closed
    with pytest.raises(NoActiveAppError):
        get_resource()
    iterator.close()
    assert resource.closed
    assert root.closed
    with pytest.raises(NoActiveAppError):
        app.__exit__(None, None, None)


@pytest.mark.asyncio
async def test_running_call_prevents_app_close():
    started = asyncio.Event()
    release = asyncio.Event()

    @handlers.inject
    async def wait(resource: FromDishka[Resource]):
        started.set()
        await release.wait()
        return resource

    container = make_async_container(AsyncResources())
    app = DishkaApp(container)
    await app.__aenter__()
    app.include(handlers)
    root = await container.get(AppResource)
    task = asyncio.create_task(wait())
    await started.wait()
    with pytest.raises(ActiveAppScopesError):
        await app.__aexit__(None, None, None)
    assert not root.closed
    with pytest.raises(NoActiveAppError):
        await async_resource()
    release.set()
    resource = await task
    assert resource.closed
    assert root.closed
    with pytest.raises(NoActiveAppError):
        await app.__aexit__(None, None, None)


def test_root_cleanup_on_exception():
    container = make_container(Resources())

    def run():
        with DishkaApp(container) as app:
            app.include(handlers)
            resource = container.get(AppResource)
            assert not resource.closed
            raise ValueError("failure")

    resource = container.get(AppResource)
    with pytest.raises(ValueError, match="failure"):
        run()
    assert resource.closed


class CustomScope(BaseScope):
    APP = new_scope("APP")
    CALL = new_scope("CALL")


def test_custom_scope_hierarchy():
    provider = Provider()
    provider.provide(Resource, scope=CustomScope.CALL)

    @handlers.inject(scope=CustomScope.CALL)
    def handle(resource: FromDishka[Resource]):
        return resource

    container = make_container(provider, scopes=CustomScope)
    with DishkaApp(container) as app:
        app.include(handlers)
        assert isinstance(handle(), Resource)


@pytest.mark.asyncio
async def test_async_custom_scope_and_context():
    provider = Provider()
    provider.from_context(int, scope=Scope.ACTION)

    @handlers.inject(
        scope=Scope.ACTION,
        provide_context=lambda args, kwargs: {int: kwargs["value"]},
    )
    async def action(*, value: int, injected: FromDishka[int]):
        return injected

    @handlers.inject
    async def outer():
        return await action(value=42)

    async with DishkaApp(make_async_container(provider)) as app:
        app.include(handlers)
        assert await outer() == 42


@pytest.mark.asyncio
async def test_async_root_cleanup_on_exception():
    container = make_async_container(AsyncResources())
    resource = await container.get(AppResource)

    async def run():
        async with DishkaApp(container):
            raise ValueError("failure")

    with pytest.raises(ValueError, match="failure"):
        await run()
    assert resource.closed


@pytest.mark.asyncio
@pytest.mark.parametrize("asynchronous", [False, True])
async def test_async_generator_exhaustion(asynchronous):
    @handlers.inject
    async def generate(resource: FromDishka[Resource]):
        yield resource

    container = (
        make_async_container(AsyncResources()) if asynchronous
        else make_container(Resources())
    )
    async with DishkaApp(container) as app:
        app.include(handlers)
        resources = [resource async for resource in generate()]
        assert len(resources) == 1
        assert resources[0].closed
