import asyncio
from collections.abc import Iterable
from inspect import isasyncgen, iscoroutine, isgenerator
from unittest.mock import Mock

import pytest

from dishka import FromDishka, make_async_container, make_container
from dishka.integrations.base import wrap_injection
from tests.integrations.common import AppMock


def raises_multiple_values(obj):
    with pytest.raises(TypeError, match="multiple values for"):  # noqa: PT012
        if isgenerator(obj):
            list(obj)
        elif callable(obj):
            obj()
        else:
            pytest.fail("Object is neither a generator nor callable")


async def raises_multiple_values_async(obj):
    with pytest.raises(TypeError, match="multiple values for"):  # noqa: PT012
        if isasyncgen(obj):
            async for _ in obj:
                pass
        elif iscoroutine(obj):
            await obj
        else:
            pytest.fail("Object is neither a generator nor callable")


def sync_func(i: int, dep: FromDishka[AppMock], j: int = 0):
    return dep(i, j)


def sync_gen(data: Iterable[int], dep: FromDishka[AppMock], j: int = 0):
    for i in data:
        yield dep(i, j)


async def async_func(i: int, dep: FromDishka[AppMock], j: int = 0):
    await asyncio.sleep(0)
    return dep(i, j)


async def async_gen(
    data: Iterable[int],
    dep: FromDishka[AppMock],
    j: int = 0,
):
    for i in data:
        await asyncio.sleep(0)
        yield dep(i, j)


@pytest.mark.parametrize("remove_depends", [True, False])
def test_sync_func(remove_depends, app_provider):
    container = make_container(app_provider)
    wrapped_func = wrap_injection(
        func=sync_func,
        container_getter=lambda *_: container,
        remove_depends=remove_depends,
        is_async=False,
    )

    wrapped_func(1)
    app_provider.app_mock.assert_called_with(1, 0)
    wrapped_func(2, j=3)
    app_provider.app_mock.assert_called_with(2, 3)

    app_provider.app_mock.reset_mock()
    new_dep = AppMock(Mock())
    if remove_depends:
        raises_multiple_values(lambda: wrapped_func(1, new_dep))
        raises_multiple_values(lambda: wrapped_func(2, dep=new_dep))
        raises_multiple_values(lambda: wrapped_func(3, new_dep, 9))
        raises_multiple_values(lambda: wrapped_func(4, new_dep, j=9))
        raises_multiple_values(lambda: wrapped_func(5, dep=new_dep, j=9))
    else:
        wrapped_func(1, new_dep)
        new_dep.assert_called_with(1, 0)
        wrapped_func(2, dep=new_dep)
        new_dep.assert_called_with(2, 0)
        wrapped_func(3, new_dep, 9)
        new_dep.assert_called_with(3, 9)
        wrapped_func(4, new_dep, j=9)
        new_dep.assert_called_with(4, 9)
        wrapped_func(5, dep=new_dep, j=9)
        new_dep.assert_called_with(5, 9)
    app_provider.app_mock.assert_not_called()


@pytest.mark.parametrize("remove_depends", [True, False])
def test_sync_gen(remove_depends, app_provider):
    container = make_container(app_provider)
    wrapped_func = wrap_injection(
        func=sync_gen,
        container_getter=lambda *_: container,
        remove_depends=remove_depends,
        is_async=False,
    )

    list(wrapped_func([1]))
    app_provider.app_mock.assert_called_with(1, 0)
    list(wrapped_func([2], j=3))
    app_provider.app_mock.assert_called_with(2, 3)

    app_provider.app_mock.reset_mock()
    new_dep = AppMock(Mock())
    if remove_depends:
        raises_multiple_values(wrapped_func([1], new_dep))
        raises_multiple_values(wrapped_func([2], dep=new_dep))
        raises_multiple_values(wrapped_func([3], new_dep, 9))
        raises_multiple_values(wrapped_func([4], new_dep, j=9))
        raises_multiple_values(wrapped_func([5], dep=new_dep, j=9))
    else:
        list(wrapped_func([1], new_dep))
        new_dep.assert_called_with(1, 0)
        list(wrapped_func([2], dep=new_dep))
        new_dep.assert_called_with(2, 0)
        list(wrapped_func([3], new_dep, 9))
        new_dep.assert_called_with(3, 9)
        list(wrapped_func([4], new_dep, j=9))
        new_dep.assert_called_with(4, 9)
        list(wrapped_func([5], dep=new_dep, j=9))
        new_dep.assert_called_with(5, 9)
    app_provider.app_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("async_container", [True, False])
@pytest.mark.parametrize("remove_depends", [True, False])
async def test_async_func(async_container, remove_depends, app_provider):
    if async_container:
        container = make_async_container(app_provider)
    else:
        container = make_container(app_provider)
    wrapped_func = wrap_injection(
        func=async_func,
        container_getter=lambda *_: container,
        remove_depends=remove_depends,
        is_async=async_container,
    )

    await wrapped_func(1)
    app_provider.app_mock.assert_called_with(1, 0)
    await wrapped_func(2, j=3)
    app_provider.app_mock.assert_called_with(2, 3)

    app_provider.app_mock.reset_mock()
    new_dep = AppMock(Mock())
    if remove_depends:
        await raises_multiple_values_async(wrapped_func(1, new_dep))
        await raises_multiple_values_async(wrapped_func(2, dep=new_dep))
        await raises_multiple_values_async(wrapped_func(3, new_dep, 9))
        await raises_multiple_values_async(wrapped_func(4, new_dep, j=9))
        await raises_multiple_values_async(wrapped_func(5, dep=new_dep, j=9))
    else:
        await wrapped_func(1, new_dep)
        new_dep.assert_called_with(1, 0)
        await wrapped_func(2, dep=new_dep)
        new_dep.assert_called_with(2, 0)
        await wrapped_func(3, new_dep, 9)
        new_dep.assert_called_with(3, 9)
        await wrapped_func(4, new_dep, j=9)
        new_dep.assert_called_with(4, 9)
        await wrapped_func(5, dep=new_dep, j=9)
        new_dep.assert_called_with(5, 9)
    app_provider.app_mock.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize("async_container", [True, False])
@pytest.mark.parametrize("remove_depends", [True, False])
async def test_async_gen(async_container, remove_depends, app_provider):
    if async_container:
        container = make_async_container(app_provider)
    else:
        container = make_container(app_provider)
    wrapped_func = wrap_injection(
        func=async_gen,
        container_getter=lambda *_: container,
        remove_depends=remove_depends,
        is_async=async_container,
    )

    async for _ in wrapped_func([1]):
        pass
    app_provider.app_mock.assert_called_with(1, 0)
    async for _ in wrapped_func([2], j=3):
        pass
    app_provider.app_mock.assert_called_with(2, 3)

    app_provider.app_mock.reset_mock()
    new_dep = AppMock(Mock())
    if remove_depends:
        await raises_multiple_values_async(wrapped_func([1], new_dep))
        await raises_multiple_values_async(wrapped_func([2], dep=new_dep))
        await raises_multiple_values_async(wrapped_func([3], new_dep, 9))
        await raises_multiple_values_async(wrapped_func([4], new_dep, j=9))
        await raises_multiple_values_async(wrapped_func([5], dep=new_dep, j=9))
    else:
        async for _ in wrapped_func([1], new_dep):
            pass
        new_dep.assert_called_with(1, 0)
        async for _ in wrapped_func([2], dep=new_dep):
            pass
        new_dep.assert_called_with(2, 0)
        async for _ in wrapped_func([3], new_dep, 9):
            pass
        new_dep.assert_called_with(3, 9)
        async for _ in wrapped_func([4], new_dep, j=9):
            pass
        new_dep.assert_called_with(4, 9)
        async for _ in wrapped_func([5], dep=new_dep, j=9):
            pass
        new_dep.assert_called_with(5, 9)
    app_provider.app_mock.assert_not_called()
