__all__ = ["DishkaContainer", "setup_dishka"]

import inspect
from typing import Any, TypeVar

from blacksheep import Application as Blacksheep

from dishka import AsyncContainer, Container, Scope, provide
from dishka.dependency_source.factory import Factory

T = TypeVar("T")


class DishkaContainer:
    def __init__(self, container: AsyncContainer | Container) -> None:
        self._container = container
        self._context = {}

    def register(
        self,
        obj_type,
        *args,
        scope: Scope = Scope.REQUEST,
        provides: Any = None,
    ) -> None:
        self._context[obj_type] = provide(
            obj_type,
            scope=scope,
            provides=provides,
        ).dependency_sources[0]

    async def resolve(self, obj_type: type[T], scope) -> T:
        resolved = None

        if isinstance(self._container, AsyncContainer):
            async with self._container(
                context=self._context,
            ) as request_container:
                resolved = await request_container.get(obj_type)

                if isinstance(resolved, Factory):
                    dependencies = [
                        await request_container.get(dependency.type_hint)
                        for dependency in resolved.dependencies
                    ]
                    resolved = resolved.source(*dependencies)
        else:
            with self._container(context=self._context) as request_container:
                resolved = request_container.get(obj_type)

                if isinstance(resolved, Factory):
                    dependencies = [
                        request_container.get(dependency.type_hint)
                        for dependency in resolved.dependencies
                    ]
                    resolved = resolved.source(*dependencies)

        return resolved

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

    app._services = DishkaContainer(container)  # noqa: SLF001


# TODO(edpyt): temp monkey patching.  # noqa: FIX002
# https://github.com/Neoteroi/BlackSheep/pull/497
def _temp_monkey_patch() -> None:
    from blacksheep import Request
    from blacksheep.server.bindings import ServiceBinder
    from rodi import CannotResolveTypeException

    async def _get_value(self, request: Request) -> Any:
        try:
            scope = request._di_scope  # type: ignore  # noqa: PGH003, SLF001
        except AttributeError:
            # no support for scoped services
            # (across parameters and middlewares)
            scope = None
        assert self.services is not None  # noqa: S101
        try:
            if inspect.iscoroutinefunction(self.services.resolve):
                return await self.services.resolve(self.expected_type, scope)
            else:
                return self.services.resolve(self.expected_type, scope)
        except CannotResolveTypeException:
            return None

    ServiceBinder.get_value = _get_value
