from inspect import signature
from unittest.mock import Mock

import pytest

from dishka import FromDishka
from dishka.integrations.base import ParameterDependencyResolver
from tests.integrations.common import AppMock

Dep1 = FromDishka[Mock]
Dep2 = FromDishka[AppMock]


def pos_or_kw(i: int, d1: Dep1, d2: Dep2, j: int = 0): ...


def kw_only(i: int, *, d1: Dep1, d2: Dep2, j: int = 0): ...


def mixed(i: int, d1: Dep1, *, d2: Dep2, j: int = 0): ...


def pos_only(i: int, d1: Dep1, d2: Dep2, /, j: int = 0): ...


def pos_only_d1(i: int, d1: Dep1, /, d2: Dep2, j: int = 0): ...


def var_args(i: int, d1: Dep1, *d2: Dep2, j: int = 0): ...


def var_kwargs(i: int, d1: Dep1, j: int = 0, **d2: Dep2): ...


def var_args_kwargs(i: int, *d1: Dep1, j: int = 0, **d2: Dep2): ...


def get_injected_names_factory(func):
    params = list(signature(func).parameters.values())
    deps = {"d1": Mock(), "d2": AppMock(Mock())}
    resolver = ParameterDependencyResolver(params, deps)

    def get_injected_names(*args, **kw):
        resolver.bind(*args, **kw)
        return [name for name, _ in resolver.items()]

    return get_injected_names


@pytest.mark.parametrize("func", [pos_or_kw, kw_only, mixed])
def test_dont_pass_dependencies(func):
    get_injected_names = get_injected_names_factory(func)
    # Both dependencies injected
    assert get_injected_names(1) == ["d1", "d2"]
    assert get_injected_names(2, j=9) == ["d1", "d2"]


@pytest.mark.parametrize("func", [pos_or_kw, kw_only, mixed])
def test_pass_dependencies_by_name(func):
    get_injected_names = get_injected_names_factory(func)
    # d1 passed by name, d2 injected
    assert get_injected_names(1, d1=Mock()) == ["d2"]
    assert get_injected_names(2, d1=Mock(), j=9) == ["d2"]
    # d2 passed by name, d1 injected
    assert get_injected_names(3, d2=Mock()) == ["d1"]
    assert get_injected_names(4, d2=Mock(), j=9) == ["d1"]
    # Both dependencies passed by name, no injection
    assert get_injected_names(1, d1=Mock(), d2=Mock()) == []
    assert get_injected_names(2, d1=Mock(), d2=Mock(), j=9) == []


@pytest.mark.parametrize("func", [pos_or_kw, mixed])
def test_pass_dependencies_by_position(func):
    get_injected_names = get_injected_names_factory(func)
    # d1 passed positionally, d2 injected
    assert get_injected_names(1, Mock()) == ["d2"]
    assert get_injected_names(2, Mock(), j=9) == ["d2"]
    # d1 passed positionally, d2 passed by name, no injection
    assert get_injected_names(2, Mock(), d2=Mock()) == []
    assert get_injected_names(3, Mock(), d2=Mock(), j=9) == []
    if func is pos_or_kw:
        # d1 and d2 passed positionally, no injection
        assert get_injected_names(3, Mock(), Mock()) == []
        assert get_injected_names(3, Mock(), Mock(), j=9) == []


@pytest.mark.parametrize(
    "func", [pos_only, pos_only_d1, var_args, var_kwargs, var_args_kwargs],
)
def test_not_implemented_parameter_kinds(func):
    with pytest.raises(NotImplementedError):
        get_injected_names_factory(func)
