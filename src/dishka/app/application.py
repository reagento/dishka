from types import TracebackType

from dishka.async_container import AsyncContainer
from dishka.container import Container
from .context import AppContext
from .exceptions import AsyncAppRequiredError
from .module import DishkaModule


class DishkaApp(DishkaModule):
    """Own a container and activate injection during a context manager block.

    The container is closed on exit. Each app instance can be entered once.
    Modules can be shared by independent applications.
    """

    def __init__(self, container: Container | AsyncContainer) -> None:
        self.container = container
        self._context = AppContext(container)
        self.include(self)

    def include(self, module: DishkaModule) -> None:
        """Make a module's entry points available in this application."""
        self._context.modules.add(module)

    def __enter__(self) -> "DishkaApp":
        if isinstance(self.container, AsyncContainer):
            raise AsyncAppRequiredError
        self._context.enter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._context.start_exit(exc_value)
        self._context.close_sync()

    async def __aenter__(self) -> "DishkaApp":
        self._context.enter()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self._context.start_exit(exc_value)
        await self._context.close_async()
