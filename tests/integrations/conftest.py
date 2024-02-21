import pytest

from dishka import make_async_container, make_container
from .common import AppProvider


@pytest.fixture
def app_provider():
    return AppProvider()


@pytest.fixture
def async_container(app_provider):
    return make_async_container(app_provider)


@pytest.fixture
def container(app_provider):
    return make_container(app_provider)
