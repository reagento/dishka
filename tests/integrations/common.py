from collections.abc import Iterable
from typing import NewType
from unittest.mock import Mock

from dishka import Provider, Scope, provide

AppDep = NewType("AppDep", str)
APP_DEP_VALUE = "APP"

RequestDep = NewType("RequestDep", str)
REQUEST_DEP_VALUE = "REQUEST"

WebSocketDep = NewType("WebSocketDep", str)
WS_DEP_VALUE = "WS"

AppMock = NewType("AppMock", Mock)


class AppProvider(Provider):
    def __init__(self):
        super().__init__()
        self.app_released = Mock()
        self.request_released = Mock()
        self.websocket_released = Mock()
        self.mock = Mock()
        self.app_mock = AppMock(Mock())

    @provide(scope=Scope.APP)
    def app(self) -> Iterable[AppDep]:
        yield APP_DEP_VALUE
        self.app_released()

    @provide(scope=Scope.REQUEST)
    def request(self) -> Iterable[RequestDep]:
        yield REQUEST_DEP_VALUE
        self.request_released()

    @provide(scope=Scope.REQUEST)
    def websocket(self) -> Iterable[WebSocketDep]:
        yield WS_DEP_VALUE
        self.websocket_released()

    @provide(scope=Scope.REQUEST)
    def mock(self) -> Mock:
        return self.mock

    @provide(scope=Scope.APP)
    def app_mock(self) -> AppMock:
        return self.app_mock


class WebSocketAppProvider(Provider):
    def __init__(self):
        super().__init__()
        self.app_released = Mock()
        self.request_released = Mock()
        self.websocket_released = Mock()
        self.mock = Mock()

    @provide(scope=Scope.APP)
    def app(self) -> Iterable[AppDep]:
        yield APP_DEP_VALUE
        self.app_released()

    @provide(scope=Scope.SESSION)
    def request(self) -> Iterable[RequestDep]:
        yield REQUEST_DEP_VALUE
        self.request_released()

    @provide(scope=Scope.SESSION)
    def websocket(self) -> Iterable[WebSocketDep]:
        yield WS_DEP_VALUE
        self.websocket_released()

    @provide(scope=Scope.SESSION)
    def mock(self) -> Mock:
        return self.mock
