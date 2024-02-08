import pytest

from .common import AppProvider


@pytest.fixture
def app_provider():
    return AppProvider()
