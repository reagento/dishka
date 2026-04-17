from collections.abc import Callable
from typing import Any, overload

from dishka.dependency_source import (
    CompositeDependencySource,
    Decorator,
    ensure_composite,
)
from dishka.entities.marker import BaseMarker
from dishka.entities.scope import BaseScope
from .exceptions import IndependentDecoratorError
from .make_factory import make_factory
from .norm_type import normalize_sources_self
from .unpack_provides import unpack_decorator


def _decorate(
        source: Callable[..., Any] | type,
        provides: Any,
        scope: BaseScope | None,
        *,
        is_in_class: bool = True,
        when: BaseMarker | None = None,
) -> CompositeDependencySource:
    composite = ensure_composite(source)
    decorator = Decorator(
        make_factory(
            provides=provides,
            scope=None,
            source=source,
            cache=False,
            is_in_class=is_in_class,
            override=False,
            when=None,
        ),
        scope=scope,
        when=when,
    )
    sources = normalize_sources_self(
        decorator.factory.source,
        unpack_decorator(decorator),
    )
    for decorator in sources:
        if (
            decorator.provides not in decorator.factory.kw_dependencies.values()
            and decorator.provides not in decorator.factory.dependencies
        ):
            raise IndependentDecoratorError(source)

    composite.dependency_sources.extend(sources)
    return composite


@overload
def decorate(
        *,
        provides: Any = None,
        scope: BaseScope | None = None,
        when: BaseMarker | None = None,
) -> Callable[
    [Callable[..., Any]], CompositeDependencySource,
]:
    ...


@overload
def decorate(
        source: Callable[..., Any] | type,
        *,
        provides: Any = None,
        scope: BaseScope | None = None,
        when: BaseMarker | None = None,
) -> CompositeDependencySource:
    ...


def decorate(
        source: Callable[..., Any] | type | None = None,
        provides: Any = None,
        scope: BaseScope | None = None,
        when: BaseMarker | None = None,
) -> CompositeDependencySource | Callable[
    [Callable[..., Any]], CompositeDependencySource,
]:
    if source is not None:
        return _decorate(
            source,
            provides,
            scope=scope,
            is_in_class=True,
            when=when,
        )

    def scoped(func: Callable[..., Any]) -> CompositeDependencySource:
        return _decorate(
            func,
            provides,
            scope=scope,
            is_in_class=True,
            when=when,
        )

    return scoped


def decorate_on_instance(
        source: Callable[..., Any] | type,
        provides: Any,
        scope: BaseScope | None,
        when: BaseMarker | None = None,
) -> CompositeDependencySource:
    return _decorate(
        source,
        provides,
        scope=scope,
        is_in_class=False,
        when=when,
    )
