import pytest
from aiogram import Bot


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
