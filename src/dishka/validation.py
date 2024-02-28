from collections.abc import Sequence

from dishka.dependency_source import Factory
from dishka.entities.key import DependencyKey
from dishka.exceptions import NoFactoryError, InvalidGraphError, \
    CycleDependenciesError
from dishka.registry import Registry
from .error_rendering import PathRenderer


class GraphValidator:
    def __init__(self, registries: Sequence[Registry]) -> None:
        self.registries = registries
        self.valid_keys = {}
        self.path = {}

    def _validate_key(
            self, key: DependencyKey, registry_index: int,
    ) -> None:
        if key in self.valid_keys:
            return
        if key in self.path:
            keys = list(self.path)
            factories = list(self.path.values())[keys.index(key):]
            raise CycleDependenciesError(factories)
        for index in range(registry_index + 1):
            registry = self.registries[index]
            factory = registry.get_factory(key)
            if factory:
                self._validate_factory(factory, registry_index)
                return
        raise NoFactoryError(requested=key)

    def _validate_factory(
            self, factory: Factory, registry_index: int,
    ):
        self.path[factory.provides] = factory
        try:
            for dep in factory.dependencies:
                self._validate_key(dep, registry_index)
        except NoFactoryError as e:
            e.add_path(factory)
            raise
        finally:
            self.path.pop(factory.provides)
        self.valid_keys[factory.provides] = True

    def validate(self):
        for registry_index, registry in enumerate(self.registries):
            for factory in registry._factories.values():
                self.path = {}
                try:
                    self._validate_factory(factory, registry_index)
                except NoFactoryError as e:
                    raise InvalidGraphError(str(e)) from None
                except CycleDependenciesError as e:
                    raise InvalidGraphError(str(e)) from None
