from contextlib import AbstractContextManager
from typing import Any

from dishka.code_tools.code_builder import CodeBuilder
from dishka.container_objects import CompiledFactory, Exit
from dishka.dependency_source import Factory
from dishka.entities.component import Component
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.marker import AndMarker, BaseMarker, NotMarker, OrMarker
from dishka.exceptions import NoContextValueError, UnsupportedFactoryError
from dishka.text_rendering import get_name


class FactoryBuilder(CodeBuilder):
    def __init__(self, is_async: bool, getter_prefix: str):
        super().__init__(is_async)
        self.provides_name = ""
        self.getter_name = ""
        self.getter_prefix = getter_prefix

    def global_(self, obj: Any, preferred_name: str | None = None) -> str:
        if preferred_name is None and isinstance(obj, DependencyKey):
            type_name = get_name(obj.type_hint, include_module=False)
            preferred_name = f"key_{type_name}"
            if obj.component:
                preferred_name += f"_{obj.component}"
        return super().global_(obj, preferred_name)

    def register_provides(self, provides: DependencyKey) -> None:
        self.provides_name = self.global_(provides)

    def make_getter(self) -> AbstractContextManager:
        self.getter_name = self.getter_prefix+self.provides_name.removeprefix("key_")
        return self.def_(self.getter_name, ["getter", "exits", "cache", "context"])

    def getter(self, obj: DependencyKey) -> str:
        if obj.is_const():
            return self.global_(obj.get_const_value())
        return self.await_(self.call("getter", self.global_(obj)))

    def cache(self) -> None:
        self.assign_expr(f"cache[{self.provides_name}]", "solved")

    def assign_solved(self, expr: str) -> None:
        self.assign_local("solved", expr)

    def when(self, marker: BaseMarker, component: Component) -> str:
        match marker:
            case None:
                return ""
            case AndMarker():
                return self.and_(self.when(marker.left, component), self.when(marker.right, component))
            case OrMarker():
                return self.or_(self.when(marker.left, component), self.when(marker.right, component))
            case NotMarker():
                return self.not_(self.when(marker.marker, component))
            case _:
                # TODO component
                return self.getter(DependencyKey(marker, component))

    def build_getter(self) -> CompiledFactory:
        name = f"<{self.getter_name}{'_async' if self.async_str else ''}>"
        return self.compile(name)[self.getter_name]


def compile_factory(*, factory: Factory, is_async: bool) -> CompiledFactory:
    builder = FactoryBuilder(is_async=is_async, getter_prefix="get_")
    builder.register_provides(factory.provides)

    with builder.make_getter():
        source_call = builder.call(
            builder.global_(factory.source),
            *(builder.getter(dep) for dep in factory.dependencies),
            **{name: builder.getter(dep) for name, dep in
               factory.kw_dependencies.items()},
        )

        match factory.type:
            case FactoryType.FACTORY:
                builder.assign_solved(source_call)
            case FactoryType.ASYNC_FACTORY:
                builder.assign_solved(builder.await_(source_call))
            case FactoryType.GENERATOR:
                builder.assign_local("generator", source_call)
                builder.assign_solved(builder.call("next", "generator"))
                builder.statement(builder.call(
                    "exits.append",
                    builder.call(
                        builder.global_(Exit),
                        builder.global_(factory.type, "factory_type"),
                        "generator",
                    ),
                ))
            case FactoryType.ASYNC_GENERATOR:
                builder.assign_local("generator", source_call)
                builder.assign_solved(
                    builder.await_(builder.call("anext", "generator")),
                )
                builder.statement(builder.call(
                    "exits.append",
                    builder.call(
                        builder.global_(Exit),
                        builder.global_(factory.type, "factory_type"),
                        "generator",
                    ),
                ))
            case FactoryType.VALUE:
                builder.assign_solved(builder.global_(factory.source))

            case FactoryType.ALIAS:
                builder.assign_solved(builder.getter(factory.dependencies[0]))
            case FactoryType.CONTEXT:
                provides_hint = builder.global_(factory.provides.type_hint)
                with builder.try_():
                    builder.assign_solved(f"context[{provides_hint}]")
                with builder.except_(KeyError):
                    builder.raise_(
                        builder.call(
                            builder.global_(NoContextValueError),
                            provides_hint,
                        ),
                    )
            case FactoryType.SELECTOR:
                first = True
                for key, marker in factory.when_dependencies.items():
                    # TODO what component?
                    condition = builder.when(marker, factory.when_component)
                    solved_value = builder.getter(key)
                    if first and not condition:
                        builder.assign_solved(solved_value)
                    elif first:
                        with builder.if_(condition):
                            builder.assign_solved(solved_value)
                        first = False
                    elif not condition:
                        with builder.else_():
                            builder.assign_solved(solved_value)
                        first = True
                    else:
                        with builder.elif_(condition):
                            builder.assign_solved(solved_value)

            case _:
                raise UnsupportedFactoryError(f"Unsupported factory type {factory.type}.")
        if factory.cache:
            builder.cache()
        builder.return_("solved")

    return builder.build_getter()


def compile_activation(*, factory: Factory, is_async: bool) -> CompiledFactory:
    builder = FactoryBuilder(is_async=is_async, getter_prefix="is_active_")
    builder.register_provides(factory.provides)
    with builder.make_getter():
        condition = builder.when(factory.when, factory.when_component)
        if not condition:
            builder.return_(builder.global_(True))
        else:
            with builder.if_(condition):
                builder.return_(builder.global_(True))
            builder.return_(builder.global_(False))

    return builder.build_getter()
