import inspect
from typing import Any, List

from .dependency_source import Alias, Decorator, DependencySource, Factory
from .exceptions import InvalidGraphError


def is_dependency_source(attribute: Any) -> bool:
    return isinstance(attribute, DependencySource)


class Provider:
    """
    A collection of dependency sources.

    Inherit this class and add attributes using
    `provide`, `alias` or `decorate`.

    You can use `__init__`, regular methods and attributes as usual,
    they won't be analyzed when creating a container

    The only intended usage of providers is to pass them when
    creating a container
    """

    def __init__(self):
        self.factories: List[Factory] = []
        self.aliases: List[Alias] = []
        self.decorators: List[Decorator] = []
        self._init_dependency_sources()

    def _init_dependency_sources(self) -> None:
        processed_types = {}

        source: DependencySource
        for name, source in inspect.getmembers(self, is_dependency_source):
            if source.provides in processed_types:
                raise InvalidGraphError(
                    f"Type {source.provides} is registered multiple times "
                    f"in the same {Provider} by attributes "
                    f"{processed_types[source.provides]!r} and {name!r}",
                )
            if isinstance(source, Alias):
                self.aliases.append(source)
            if isinstance(source, Factory):
                self.factories.append(source)
            if isinstance(source, Decorator):
                self.decorators.append(source)
            processed_types[source.provides] = name
