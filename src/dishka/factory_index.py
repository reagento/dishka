from __future__ import annotations

from dataclasses import dataclass

from dishka.dependency_source.factory import Factory
from dishka.entities.factory_type import FactoryType
from dishka.entities.key import DependencyKey
from dishka.entities.scope import BaseScope


@dataclass(frozen=True, slots=True)
class FactoryIndex:
    factories_by_key: dict[DependencyKey, Factory]
    context_keys_at_root: frozenset[DependencyKey]

    @classmethod
    def from_processed_factories(
        cls,
        processed_factories: dict[DependencyKey, list[Factory]],
        root_scope: BaseScope,
    ) -> FactoryIndex:
        factories_by_key: dict[DependencyKey, Factory] = {}
        context_keys: set[DependencyKey] = set()

        for key, factory_list in processed_factories.items():
            if factory_list:
                factory = factory_list[-1]  # Last wins (override order)
                factories_by_key[key] = factory
                if (
                    factory.type == FactoryType.CONTEXT
                    and factory.scope == root_scope
                ):
                    context_keys.add(key)

        return cls(
            factories_by_key=factories_by_key,
            context_keys_at_root=frozenset(context_keys),
        )

    def __contains__(self, key: DependencyKey) -> bool:
        return key in self.factories_by_key

    def get(self, key: DependencyKey) -> Factory | None:
        return self.factories_by_key.get(key)
