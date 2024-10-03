from __future__ import annotations

import sys
from collections.abc import Sequence
from typing import Any, ForwardRef, TypeVar, get_args, get_origin

from dishka._adaptix.type_tools.basic_utils import eval_forward_ref
from dishka.entities.component import Component
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope
from .factory import Factory


def eval_maybe_forward(t: Any, wrapper: Any) -> Any:
    if not isinstance(t, ForwardRef):
        return t
    return eval_forward_ref(
        vars(sys.modules[wrapper.__module__]),
        t,
    )


def eval_maybe_forward_many(args: Sequence[Any], wrapper: Any) -> list[type]:
    return [
        eval_maybe_forward(t, wrapper) for t in args
    ]


def _is_broader_or_same_generic(t1: Any, t2: Any) -> bool:
    origin1 = eval_maybe_forward(get_origin(t1), t1)
    origin2 = eval_maybe_forward(get_origin(t2), t2)
    if origin1 is not origin2:
        return False
    args1 = eval_maybe_forward_many(get_args(t1), t1)
    args2 = eval_maybe_forward_many(get_args(t2), t2)
    if len(args1) != len(args2):
        return False
    for a1, a2 in zip(args1, args2, strict=False):
        if not is_broader_or_same_type(a1, a2):
            return False
    return True


def _is_broader_or_same_type_var(t1: TypeVar, t2: Any) -> bool:
    if get_origin(t2) is not None:
        return False  # generic
    if not t1.__bound__ and not t1.__constraints__:
        return True
    elif t1.__bound__:
        bound1 = eval_maybe_forward(t1.__bound__, t1)
        if not isinstance(t2, TypeVar):
            return issubclass(t2, bound1)
        if t2.__bound__:
            bound2 = eval_maybe_forward(t2.__bound__, t2)
            return issubclass(bound2, bound1)
    elif t1.__constraints__:
        constraints1 = eval_maybe_forward_many(t1.__constraints__, t1)
        if not isinstance(t2, TypeVar):
            return t2 in constraints1
        if t2.__constraints__:
            constraints2 = eval_maybe_forward_many(t2.__constraints__, t2)
            return set(constraints1) >= set(constraints2)
    return False


def is_broader_or_same_type(t1: Any, t2: Any) -> bool:
    if t1 == t2:
        return True
    if get_origin(t1) is not None:
        return _is_broader_or_same_generic(t1, t2)
    elif isinstance(t1, TypeVar):
        return _is_broader_or_same_type_var(t1, t2)
    return False


class Decorator:
    __slots__ = ("provides", "factory")

    def __init__(
            self,
            factory: Factory,
            provides: DependencyKey | None = None,
    ) -> None:
        self.factory = factory
        if provides:
            self.provides = provides
        else:
            self.provides = factory.provides

    def is_generic(self):
        return (
            isinstance(self.provides.type_hint, TypeVar)
            or get_origin(self.provides.type_hint) is not None
        )

    def match_type(self, type_: Any) -> bool:
        return is_broader_or_same_type(self.provides.type_hint, type_)

    def as_factory(
            self, *,
            scope: BaseScope,
            new_dependency: DependencyKey,
            cache: bool,
            component: Component,
    ) -> Factory:
        return Factory(
            scope=scope,
            source=self.factory.source,
            provides=self.factory.provides.with_component(component),
            is_to_bind=self.factory.is_to_bind,
            dependencies=[
                (
                    new_dependency
                    if dep.type_hint == self.provides.type_hint
                    else dep
                ).with_component(component)
                for dep in self.factory.dependencies
            ],
            kw_dependencies={
                name: (
                    new_dependency
                    if dep.type_hint == self.provides.type_hint
                    else dep
                ).with_component(component)
                for name, dep in self.factory.kw_dependencies.items()
            },
            type_=self.factory.type,
            cache=cache,
            override=False,
        )

    def __get__(self, instance: Any, owner: Any) -> Decorator:
        return Decorator(self.factory.__get__(instance, owner))
