__all__ = [
    "AnyOf",
    "make_async_container", "AsyncContainer",
    "DEFAULT_COMPONENT", "Component",
    "make_container", "Container", "FromComponent",
    "Provider",
    "alias", "decorate", "from_context", "provide", "provide_all",
    "DependencyKey",
    "FromDishka",
    "BaseScope", "Scope", "new_scope",
]

from .async_container import AsyncContainer, make_async_container
from .container import Container, make_container
from .dependency_source import (
    alias,
    decorate,
    from_context,
    provide,
    provide_all,
)
from .entities.component import DEFAULT_COMPONENT, Component
from .entities.depends_marker import FromDishka
from .entities.key import DependencyKey, FromComponent
from .entities.provides_marker import AnyOf
from .entities.scope import BaseScope, Scope, new_scope
from .provider import Provider
