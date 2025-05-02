"""TemporalIO integration with Dishka for dependency injection in activities."""
__all__ = [
    "FromDishka",
    "DishkaWorkerInterceptor",
    "DishkaActivityInboundInterceptor",
]

import inspect
from typing import Any, Callable, TypeVar, Union

from dishka import AsyncContainer, Scope, Container
from dishka.integrations.base import wrap_injection
from temporalio.worker import Interceptor, ActivityInboundInterceptor, ExecuteActivityInput

DishkaContainer = TypeVar("DishkaContainer", bound=Union[Container, AsyncContainer])

# noinspection PyShadowingBuiltins
class DishkaWorkerInterceptor(Interceptor):
    """Manages Dishka request scope for Temporal activities."""

    def __init__(self, container: DishkaContainer):
        """Initialize the interceptor with a Dishka container."""
        self.container = container

    def intercept_activity(self, next: ActivityInboundInterceptor) -> ActivityInboundInterceptor:
        """Intercepts activity execution to manage Dishka request scope."""
        return DishkaActivityInboundInterceptor(next, self.container)


# noinspection PyShadowingBuiltins
class DishkaActivityInboundInterceptor(ActivityInboundInterceptor):
    """Injects Dishka dependencies into Temporal activities."""

    def __init__(self, next: ActivityInboundInterceptor, container: DishkaContainer):
        """Initialize the interceptor with a Dishka container."""
        super().__init__(next)
        self.container = container

    async def execute_activity(self, input: ExecuteActivityInput) -> Any:
        """Execute the activity with Dishka dependencies injected."""
        is_async = inspect.iscoroutinefunction(input.fn)

        async def _run_async_activity():
            """Run the default async activity."""
            async with self.container(scope=Scope.REQUEST) as scoped_container:
                input.fn = self._wrap(input.fn, scoped_container, is_async=True)
                return await super(DishkaActivityInboundInterceptor, self).execute_activity(input)

        async def _run_sync_activity():
            """Run the sync activity used with ThreadPoolExecutor as activity_executor."""
            with self.container(scope=Scope.REQUEST) as scoped_container:
                input.fn = self._wrap(input.fn, scoped_container, is_async=False)
                return await super(DishkaActivityInboundInterceptor, self).execute_activity(input)

        return await _run_async_activity() if is_async else await _run_sync_activity()

    @staticmethod
    def _wrap(func: Callable, container: DishkaContainer, is_async: bool) -> Callable:
        """Wrap the activity function to inject dependencies."""
        return wrap_injection(
            func=func,
            container_getter=lambda args, kwargs: container,
            remove_depends=True,
            **({"is_async": True} if is_async else {})
        )
