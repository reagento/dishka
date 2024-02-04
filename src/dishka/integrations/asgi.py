__all__ = [
    'Depends',
]

from abc import ABC, abstractmethod
from typing import Sequence

from dishka import Provider, make_async_container
from dishka.async_container import AsyncContainer, AsyncContextWrapper
from .base import Depends


class BaseDishkaApp(ABC):
    def __init__(self, providers: Sequence[Provider], app):
        self.app = app
        self.container_wrapper = make_async_container(*providers)
        self._init_request_middleware(app, self.container_wrapper)

    @abstractmethod
    def _init_request_middleware(
            self, app, container_wrapper: AsyncContextWrapper,
    ):
        pass

    @abstractmethod
    def _app_startup(self, app, container: AsyncContainer):
        pass

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'lifespan':
            async def my_recv():
                message = await receive()
                if message['type'] == 'lifespan.startup':
                    container = await self.container_wrapper.__aenter__()
                    self._app_startup(self.app, container)
                elif message['type'] == 'lifespan.shutdown':
                    await self.container_wrapper.__aexit__(None, None, None)

            return await self.app(scope, my_recv, send)
        else:
            return await self.app(scope, receive, send)
