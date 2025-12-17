from collections.abc import Callable
from typing import Any

from ..entities.component import DEFAULT_COMPONENT
from ..entities.key import DependencyKey
from ..entities.activation import BaseMarker, AndMarker, OrMarker, NotMarker
from ..exceptions import NoFactoryError


class FactorySelector:
    def __init__(self, dependencies: dict[BaseMarker | None, DependencyKey]):
        self.dependencies = dependencies

    def get(self, container_getter: Callable[[DependencyKey], Any]) -> Any:
        for marker, dependency_key in self.dependencies.items():
            if self.eval(marker, container_getter):
                return container_getter(dependency_key)
        raise NoFactoryError

    def eval(self, marker: BaseMarker | None, container_getter: Callable[[DependencyKey], Any]) -> bool:
        if not marker:
            return True
        if isinstance(marker, AndMarker):
            return self.eval(marker.left, container_getter) and self.eval(marker.right, container_getter)
        if isinstance(marker, OrMarker):
            return self.eval(marker.left, container_getter) or self.eval(marker.right, container_getter)
        if isinstance(marker, NotMarker):
            return not self.eval(marker.marker, container_getter)
        return container_getter(DependencyKey(marker, DEFAULT_COMPONENT))


class AsyncFactorySelector:
    def __init__(self, dependencies: dict[BaseMarker | None, DependencyKey]):
        self.dependencies = dependencies

    async def get(self, container_getter: Callable[[DependencyKey], Any]) -> Any:
        for marker, dependency_key in self.dependencies.items():
            if await self.eval(marker, container_getter):
                return await container_getter(dependency_key)
        raise NoFactoryError

    async def eval(self, marker: BaseMarker | None, container_getter: Callable[[DependencyKey], Any]) -> bool:
        if not marker:
            return True
        if isinstance(marker, AndMarker):
            return await self.eval(marker.left, container_getter) and await self.eval(marker.right, container_getter)
        if isinstance(marker, OrMarker):
            return await self.eval(marker.left, container_getter) or await self.eval(marker.right, container_getter)
        if isinstance(marker, NotMarker):
            return not await self.eval(marker.marker, container_getter)
        return await container_getter(DependencyKey(marker, DEFAULT_COMPONENT))

