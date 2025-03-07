import pytest

from dishka import make_async_container, make_container
from .common import AppProvider, WebSocketAppProvider


@pytest.fixture
def app_provider() -> AppProvider:
    return AppProvider()


@pytest.fixture
def ws_app_provider() -> WebSocketAppProvider:
    return WebSocketAppProvider()

@pytest.fixture
def async_container(app_provider: AppProvider) -> AppProvider:
    return make_async_container(app_provider)


@pytest.fixture
def container(app_provider: AppProvider) -> AppProvider:
    return make_container(app_provider)
