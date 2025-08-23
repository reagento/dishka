from collections.abc import Callable
from typing import ParamSpec, TypeVar

import pytest
from aiogram import Bot

from dishka.integrations.aiogram import inject

_ParamsP = ParamSpec("_ParamsP")
_ReturnT = TypeVar("_ReturnT")

class FakeBot(Bot):
    def __init__(self):
        pass  # do not call super, so it is invalid bot, used only as a stub

    @property
    def id(self):
        return 1

    def __call__(self, *args, **kwargs) -> None:
        raise RuntimeError("Fake bot should not be used to call telegram")

    def __hash__(self) -> int:
        return 1

    def __eq__(self, other) -> bool:
        return self is other


@pytest.fixture
def bot():
    return FakeBot()

def custom_inject(
    func: Callable[_ParamsP, _ReturnT],
) -> Callable[_ParamsP, _ReturnT]:
    func.__custom__ = True
    return inject(func)
