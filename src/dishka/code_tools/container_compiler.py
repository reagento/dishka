from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import Any, cast

from dishka.code_tools.code_builder import CodeBuilder
from dishka.exceptions import NoActiveFactoryError, NoFactoryError
from dishka.registry import COMPILED_MISSING, Registry


def _compile_resolver(  # noqa: PLR0915
    *,
    registry: Registry,
    is_async: bool,
) -> Callable[..., Any]:
    builder = CodeBuilder(is_async=is_async)
    compiled_map = registry.compiled_async if is_async else registry.compiled
    get_compiled = (
        registry.get_compiled_async if is_async else registry.get_compiled
    )

    compiled_map_name = builder.global_(compiled_map, "compiled_map")
    get_compiled_name = builder.global_(get_compiled, "get_compiled")
    get_factory_name = builder.global_(registry.get_factory, "get_factory")
    get_more_abstract_name = builder.global_(
        registry.get_more_abstract_factories,
        "get_more_abstract_factories",
    )
    get_more_concrete_name = builder.global_(
        registry.get_more_concrete_factories,
        "get_more_concrete_factories",
    )
    no_factory_name = builder.global_(NoFactoryError)
    no_active_factory_name = builder.global_(NoActiveFactoryError)

    function_name = "resolve_async" if is_async else "resolve"
    with builder.def_(
        function_name,
        [
            "getter",
            "exits",
            "cache",
            "context",
            "key",
            "parent_get",
            "fallback_keys",
        ],
    ):
        with builder.if_("parent_get is not None and key in fallback_keys"):
            call_parent = builder.call("parent_get", "key")
            if is_async:
                builder.assign_local("solved", builder.await_(call_parent))
            else:
                builder.assign_local("solved", call_parent)
            builder.assign_expr("cache[key]", "solved")
            builder.return_("solved")

        missing_name = builder.global_(COMPILED_MISSING, "compiled_missing")
        builder.assign_local("compiled", f"{compiled_map_name}.get(key)")
        with builder.if_(f"compiled is None or compiled is {missing_name}"):
            builder.assign_local(
                "compiled",
                builder.call(get_compiled_name, "key"),
            )
            with builder.if_("compiled is None"):
                with builder.if_("parent_get is None"):
                    abstract_call = builder.call(get_more_abstract_name, "key")
                    concrete_call = builder.call(get_more_concrete_name, "key")
                    error_call = builder.call(
                        no_factory_name,
                        "key",
                        suggest_abstract_factories=abstract_call,
                        suggest_concrete_factories=concrete_call,
                    )
                    builder.raise_(error_call)
                with builder.else_():
                    builder.statement("try:")
                    with builder.block():
                        builder.statement("fallback_keys.add(key)")
                        call_parent = builder.call("parent_get", "key")
                        if is_async:
                            builder.assign_local(
                                "solved",
                                builder.await_(call_parent),
                            )
                        else:
                            builder.assign_local("solved", call_parent)
                        builder.assign_expr("cache[key]", "solved")
                        builder.return_("solved")
                    builder.statement(f"except {no_factory_name} as e:")
                    with builder.block():
                        abstract_call = builder.call(
                            get_more_abstract_name,
                            "key",
                        )
                        concrete_call = builder.call(
                            get_more_concrete_name,
                            "key",
                        )
                        builder.statement(
                            f"e.suggest_abstract_factories.extend({abstract_call})",
                        )
                        builder.statement(
                            f"e.suggest_concrete_factories.extend({concrete_call})",
                        )
                        builder.statement("raise")

        builder.statement("try:")
        with builder.block():
            call_compiled = builder.call(
                "compiled",
                "getter",
                "exits",
                "cache",
                "context",
            )
            if is_async:
                builder.return_(builder.await_(call_compiled))
            else:
                builder.return_(call_compiled)
        builder.statement(f"except {no_factory_name} as e:")
        with builder.block():
            builder.statement(
                f"e.add_path({builder.call(get_factory_name, 'key')})",
            )
            builder.statement("raise")
        builder.statement(f"except {no_active_factory_name} as e:")
        with builder.block():
            builder.statement(
                f"e.add_path({builder.call(get_factory_name, 'key')})",
            )
            builder.statement("raise")

    compiled = builder.compile(f"<{function_name}>")
    return cast(Callable[..., Any], compiled[function_name])


def _compile_activation_resolver(
    *,
    registry: Registry,
    is_async: bool,
) -> Callable[..., Any]:
    builder = CodeBuilder(is_async=is_async)
    compiled_map = (
        registry.compiled_activation_async
        if is_async
        else registry.compiled_activation
    )
    get_compiled = (
        registry.get_compiled_activation_async
        if is_async
        else registry.get_compiled_activation
    )

    compiled_map_name = builder.global_(compiled_map, "compiled_map")
    get_compiled_name = builder.global_(get_compiled, "get_compiled")

    function_name = (
        "resolve_activation_async"
        if is_async
        else "resolve_activation"
    )
    with builder.def_(
        function_name,
        ["getter", "exits", "cache", "context", "key", "parent_has"],
    ):
        missing_name = builder.global_(COMPILED_MISSING, "compiled_missing")
        builder.assign_local("compiled", f"{compiled_map_name}.get(key)")
        with builder.if_(f"compiled is None or compiled is {missing_name}"):
            builder.assign_local(
                "compiled",
                builder.call(get_compiled_name, "key"),
            )
            with builder.if_("compiled is None"):
                with builder.if_("parent_has is None"):
                    builder.return_(builder.global_(False))
                with builder.else_():
                    call_parent = builder.call("parent_has", "key")
                    if is_async:
                        builder.return_(builder.await_(call_parent))
                    else:
                        builder.return_(call_parent)

        call_compiled = builder.call(
            "compiled",
            "getter",
            "exits",
            "cache",
            "context",
        )
        if is_async:
            call_compiled = builder.await_(call_compiled)
        builder.return_(builder.call("bool", call_compiled))

    compiled = builder.compile(f"<{function_name}>")
    return cast(Callable[..., Any], compiled[function_name])


def compile_resolvers(registry: Registry) -> None:
    if registry.resolver is None:
        registry.resolver = _compile_resolver(
            registry=registry,
            is_async=False,
        )
    if registry.resolver_async is None:
        registry.resolver_async = _compile_resolver(
            registry=registry,
            is_async=True,
        )
    if registry.resolver_activation is None:
        registry.resolver_activation = _compile_activation_resolver(
            registry=registry,
            is_async=False,
        )
    if registry.resolver_activation_async is None:
        registry.resolver_activation_async = _compile_activation_resolver(
            registry=registry,
            is_async=True,
        )


def _compile_enter_chain(
    *,
    container_cls: type[Any],
    chain: Sequence[tuple[Registry, tuple[Registry, ...]]],
    name: str,
) -> Callable[..., Any]:
    builder = CodeBuilder(is_async=False)
    container_name = builder.global_(container_cls, "Container")
    registry_names: list[str] = []
    children_names: list[str] = []
    for idx, (registry, children) in enumerate(chain):
        registry_names.append(builder.global_(registry, f"reg_{idx}"))
        children_names.append(builder.global_(children, f"children_{idx}"))

    with builder.def_(name, ["parent", "context", "lock_factory"]):
        if not chain:
            builder.raise_(
                builder.call(builder.global_(RuntimeError), "No chain"),
            )
        builder.assign_local(
            "child",
            (
                f"{container_name}({registry_names[0]}, "
                f"*{children_names[0]}, "
                "parent_container=parent, "
                "context=context, "
                "lock_factory=lock_factory)"
            ),
        )
        for idx in range(1, len(chain)):
            builder.assign_local(
                "child",
                (
                    f"{container_name}({registry_names[idx]}, "
                    f"*{children_names[idx]}, "
                    "parent_container=child, "
                    "context=context, "
                    "lock_factory=lock_factory, "
                    "close_parent=True)"
                ),
            )
        builder.return_("child")

    compiled = builder.compile(f"<{name}>")
    return cast(Callable[..., Any], compiled[name])


def compile_scope_enters(
    *,
    registries: Sequence[Registry],
    container_cls: type[Any],
) -> None:
    if not registries:
        return

    children_map: dict[Registry, tuple[Registry, ...]] = {}
    for idx, registry in enumerate(registries):
        children_map[registry] = tuple(registries[idx + 1 :])

    for idx, registry in enumerate(registries):
        registry.enter_scope_fns = {}
        registry.enter_default = None
        if idx >= len(registries) - 1:
            continue

        for target_idx in range(idx + 1, len(registries)):
            target_registry = registries[target_idx]
            chain = [
                (registries[chain_idx], children_map[registries[chain_idx]])
                for chain_idx in range(idx + 1, target_idx + 1)
            ]
            name = (
                f"enter_{registry.scope.name}_"
                f"to_{target_registry.scope.name}"
            )
            enter_fn = _compile_enter_chain(
                container_cls=container_cls,
                chain=chain,
                name=name,
            )
            registry.enter_scope_fns[target_registry.scope] = enter_fn

        for target_idx in range(idx + 1, len(registries)):
            target_registry = registries[target_idx]
            if target_registry.scope.skip:
                continue
            chain = [
                (registries[chain_idx], children_map[registries[chain_idx]])
                for chain_idx in range(idx + 1, target_idx + 1)
            ]
            name = f"enter_{registry.scope.name}_default"
            registry.enter_default = _compile_enter_chain(
                container_cls=container_cls,
                chain=chain,
                name=name,
            )
            break
