from typing import Any

from dishka import AsyncContainer, BaseScope, Container, DependencyKey
from dishka._adaptix.type_tools import is_protocol
from dishka.dependency_source import Factory
from dishka.entities.factory_type import FactoryType
from dishka.registry import Registry
from dishka.text_rendering import get_name
from .model import Group, GroupType, Node, NodeType


class Transformer:
    def __init__(self):
        self.nodes: dict[tuple[DependencyKey, BaseScope], Node] = {}
        self.groups: dict[Any, Group] = {}
        self._counter = 0

    def count(self, prefix: str) -> str:
        self._counter += 1
        return f"{prefix}{self._counter}"

    def _is_empty(self, registry: Registry) -> bool:
        for factory in registry.factories.values():
            if factory.provides.type_hint not in (Container, AsyncContainer):
                return False
        return True

    def _node_type(self, factory: Factory) -> NodeType:
        if factory.type is FactoryType.ALIAS:
            return NodeType.ALIAS
        elif factory.type is FactoryType.CONTEXT:
            return NodeType.CONTEXT
        else:
            return NodeType.FACTORY

    def _make_factories(
            self, scope: BaseScope, group: Group, registry: Registry,
    ) -> None:
        for key, factory in registry.factories.items():
            group_key = (scope, key.component)
            if group_key in self.groups:
                component_group = self.groups[group_key]
            else:
                component_group = self.groups[group_key] = Group(
                    id=self.count("component"),
                    name=str(key.component),
                    children=[],
                    nodes=[],
                    type=GroupType.COMPONENT,
                )
                group.children.append(component_group)
            node_name = get_name(key.type_hint, include_module=False)
            if key.component:
                node_name += " " + str(key.component)

            if factory.type in (FactoryType.CONTEXT, FactoryType.ALIAS):
                source_name = ""
            else:
                source_name = get_name(factory.source, include_module=False)
            node = Node(
                id=self.count("factory"),
                name=node_name,
                dependencies=[],
                type=self._node_type(factory),
                is_protocol=is_protocol(factory.provides),
                source_name=source_name,
            )
            self.nodes[key, scope] = node
            component_group.nodes.append(node)

    def _fill_dependencies(
            self, registry: Registry, parent_registries: list[Registry],
    ) -> None:
        # parent registries are passed from current scope to outer one
        for key, factory in registry.factories.items():
            node = self.nodes[key, registry.scope]
            all_deps = (
                    list(factory.dependencies)
                    + list(factory.kw_dependencies.values())
            )
            for dep in all_deps:
                for dep_registry in parent_registries:
                    if dep in dep_registry.factories:
                        break
                else:
                    continue
                dep_node = self.nodes[dep, dep_registry.scope]
                node.dependencies.append(dep_node.id)

    def transform(self, container: Container|AsyncContainer) -> list[Group]:
        registries = [container.registry, *container.child_registries]
        result = []
        for registry in registries:
            if self._is_empty(registry):
                continue
            scope = registry.scope
            group = self.groups[scope] = Group(
                id=self.count("scope"),
                name=str(scope),
                children=[],
                nodes=[],
                type=GroupType.SCOPE,
            )
            result.append(group)
            self._make_factories(scope, group, registry)

        for n, registry in enumerate(registries):
            if self._is_empty(registry):
                continue
            self._fill_dependencies(registry, registries[n::-1])
        return result
