from typing import Literal

import pytest

from dishka.code_tools.factory_compiler import _is_sync_dep
from dishka.dependency_source.factory import Factory
from dishka.entities.component import DEFAULT_COMPONENT
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.scope import Scope
from dishka.registry import Registry


def _make_key(type_hint, component=DEFAULT_COMPONENT):
    return DependencyKey(type_hint, component)


def _make_factory(
    provides,
    dependencies=None,
    kw_dependencies=None,
    *,
    cache=True,
):
    return Factory(
        source=lambda: None,
        provides=provides,
        dependencies=dependencies or [],
        kw_dependencies=kw_dependencies or {},
        scope=Scope.APP,
        type_=FactoryType.ASYNC_FACTORY,
        is_to_bind=False,
        cache=cache,
        when_override=None,
        when_active=None,
        when_component=None,
        when_dependencies=[],
    )


@pytest.fixture
def container_key():
    return _make_key(object)


@pytest.fixture
def registry(container_key):
    return Registry(
        scope=Scope.APP,
        has_fallback=False,
        container_key=container_key,
    )


# --- _is_sync_dep ---


def test_is_sync_dep_const(container_key):
    dep = DependencyKey(Literal[42], DEFAULT_COMPONENT)
    assert _is_sync_dep(dep, {}, container_key) is True


def test_is_sync_dep_dependency_key_type(container_key):
    dep = DependencyKey(DependencyKey, DEFAULT_COMPONENT)
    assert _is_sync_dep(dep, {}, container_key) is True


def test_is_sync_dep_container_key(container_key):
    assert _is_sync_dep(container_key, {}, container_key) is True


def test_is_sync_dep_regular(container_key):
    dep = _make_key(int)
    assert _is_sync_dep(dep, {}, container_key) is False


# --- _get_transitive_dep_keys ---


def test_transitive_no_deps(registry):
    key_a = _make_key(int)
    registry.add_factory(_make_factory(key_a))

    assert registry._get_transitive_dep_keys(key_a) == {key_a}


def test_transitive_chain(registry):
    key_a = _make_key(int)
    key_b = _make_key(float)
    key_c = _make_key(str)

    registry.add_factory(_make_factory(key_c))
    registry.add_factory(_make_factory(key_b, dependencies=[key_c]))
    registry.add_factory(_make_factory(key_a, dependencies=[key_b]))

    assert registry._get_transitive_dep_keys(key_a) == {key_a, key_b, key_c}


def test_transitive_cycle(registry):
    key_a = _make_key(int)
    key_b = _make_key(float)

    registry.add_factory(_make_factory(key_a, dependencies=[key_b]))
    registry.add_factory(_make_factory(key_b, dependencies=[key_a]))

    assert registry._get_transitive_dep_keys(key_a) == {key_a, key_b}


def test_transitive_missing_factory(registry):
    assert registry._get_transitive_dep_keys(_make_key(int)) == set()


def test_transitive_diamond(registry):
    key_a = _make_key(int)
    key_b = _make_key(float)
    key_c = _make_key(str)
    key_d = _make_key(bytes)

    registry.add_factory(_make_factory(key_d))
    registry.add_factory(_make_factory(key_b, dependencies=[key_d]))
    registry.add_factory(_make_factory(key_c, dependencies=[key_d]))
    registry.add_factory(_make_factory(key_a, dependencies=[key_b, key_c]))

    assert registry._get_transitive_dep_keys(key_a) == {
        key_a,
        key_b,
        key_c,
        key_d,
    }


def test_transitive_kw_dependencies(registry):
    key_a = _make_key(int)
    key_b = _make_key(float)

    registry.add_factory(_make_factory(key_b))
    registry.add_factory(_make_factory(key_a, kw_dependencies={"x": key_b}))

    assert registry._get_transitive_dep_keys(key_a) == {key_a, key_b}


# --- _can_gather_deps ---


def test_can_gather_independent(registry):
    key_a = _make_key(int)
    key_b = _make_key(float)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_a))
    registry.add_factory(_make_factory(key_b))
    factory = _make_factory(key_target, dependencies=[key_a, key_b])
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is True


def test_can_gather_shared_transitive_cached(registry):
    key_shared = _make_key(bytes)
    key_a = _make_key(int)
    key_b = _make_key(float)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_shared))
    registry.add_factory(_make_factory(key_a, dependencies=[key_shared]))
    registry.add_factory(_make_factory(key_b, dependencies=[key_shared]))
    factory = _make_factory(key_target, dependencies=[key_a, key_b])
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is True


def test_can_gather_shared_transitive_uncached(registry):
    key_shared = _make_key(bytes)
    key_a = _make_key(int)
    key_b = _make_key(float)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_shared, cache=False))
    registry.add_factory(_make_factory(key_a, dependencies=[key_shared]))
    registry.add_factory(_make_factory(key_b, dependencies=[key_shared]))
    factory = _make_factory(key_target, dependencies=[key_a, key_b])
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is True


def test_can_gather_single_dep(registry):
    key_a = _make_key(int)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_a))
    factory = _make_factory(key_target, dependencies=[key_a])
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is False


def test_can_gather_no_deps(registry):
    key_target = _make_key(str)
    factory = _make_factory(key_target)
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is False


def test_can_gather_const_excluded(registry):
    key_a = _make_key(int)
    const_dep = DependencyKey(Literal[42], DEFAULT_COMPONENT)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_a))
    factory = _make_factory(key_target, dependencies=[key_a, const_dep])
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is False


def test_can_gather_container_key_excluded(container_key):
    key_a = _make_key(int)
    key_target = _make_key(str)

    reg = Registry(
        scope=Scope.APP,
        has_fallback=False,
        container_key=container_key,
    )
    reg.add_factory(_make_factory(key_a))
    factory = _make_factory(key_target, dependencies=[key_a, container_key])
    reg.add_factory(factory)

    assert reg._can_gather_deps(factory) is False


def test_can_gather_dependency_key_excluded(registry):
    key_a = _make_key(int)
    dk_dep = DependencyKey(DependencyKey, DEFAULT_COMPONENT)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_a))
    factory = _make_factory(key_target, dependencies=[key_a, dk_dep])
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is False


def test_can_gather_three_independent(registry):
    key_a = _make_key(int)
    key_b = _make_key(float)
    key_c = _make_key(bytes)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_a))
    registry.add_factory(_make_factory(key_b))
    registry.add_factory(_make_factory(key_c))
    factory = _make_factory(
        key_target,
        dependencies=[key_a, key_b, key_c],
    )
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is True


def test_can_gather_kw_deps(registry):
    key_a = _make_key(int)
    key_b = _make_key(float)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_a))
    registry.add_factory(_make_factory(key_b))
    factory = _make_factory(
        key_target,
        dependencies=[key_a],
        kw_dependencies={"b": key_b},
    )
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is True


def test_can_gather_mixed_pos_kw_shared_transitive_cached(registry):
    key_shared = _make_key(bytes)
    key_a = _make_key(int)
    key_b = _make_key(float)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_shared))
    registry.add_factory(_make_factory(key_a, dependencies=[key_shared]))
    registry.add_factory(_make_factory(key_b, dependencies=[key_shared]))
    factory = _make_factory(
        key_target,
        dependencies=[key_a],
        kw_dependencies={"b": key_b},
    )
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is True


def test_can_gather_mixed_pos_kw_shared_transitive_uncached(registry):
    key_shared = _make_key(bytes)
    key_a = _make_key(int)
    key_b = _make_key(float)
    key_target = _make_key(str)

    registry.add_factory(_make_factory(key_shared, cache=False))
    registry.add_factory(_make_factory(key_a, dependencies=[key_shared]))
    registry.add_factory(_make_factory(key_b, dependencies=[key_shared]))
    factory = _make_factory(
        key_target,
        dependencies=[key_a],
        kw_dependencies={"b": key_b},
    )
    registry.add_factory(factory)

    assert registry._can_gather_deps(factory) is True
