__all__ = ["DishkaContainer", "setup_dishka"]

import inspect
from typing import Any, TypeVar

from blacksheep import Application as Blacksheep

from dishka import AsyncContainer, Container, Scope, provide

T = TypeVar("T")


class DishkaContainer:
    def __init__(self, container: AsyncContainer | Container) -> None:
        self._container = container

    def register(
        self,
        obj_type,
        scope: Scope = Scope.APP,
        provides: Any = None,
    ) -> None:
        factory = provide(obj_type, provides=provides).dependency_sources[0]
        self._container.registry.add_factory(factory)

    async def resolve(self, obj_type, *args) -> T:
        if isinstance(self._container, AsyncContainer):
            return await self._container.get(obj_type)
        else:
            return self._container.get(obj_type)

    def __contains__(self, item) -> bool:
        for registry in (
            self._container.registry,
            *self._container.child_registries,
        ):
            for factory in registry.factories:
                if item is factory.type_hint:
                    return True
        return False


def setup_dishka(
    container: AsyncContainer | Container,
    app: Blacksheep,
) -> None:
    _temp_monkey_patch()

    app._services = DishkaContainer(container)


# FIXME: temp monkey patching. Fixes in https://github.com/Neoteroi/BlackSheep/pull/497
def _temp_monkey_patch() -> None:
    from blacksheep import Request
    from blacksheep.server.bindings import ServiceBinder
    from rodi import CannotResolveTypeException

    async def _get_value(self, request: Request) -> Any:
        try:
            scope = request._di_scope  # type: ignore
        except AttributeError:
            # no support for scoped services
            # (across parameters and middlewares)
            scope = None
        assert self.services is not None
        try:
            if inspect.iscoroutinefunction(self.services.resolve):
                return await self.services.resolve(self.expected_type, scope)
            else:
                return self.services.resolve(self.expected_type, scope)
        except CannotResolveTypeException:
            return None

    ServiceBinder.get_value = _get_value
