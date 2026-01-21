from unittest.mock import Mock

import pytest
from aiogram import Dispatcher
from aiogram.filters import CommandStart
from aiogram.fsm.state import State, StatesGroup
from aiogram_dialog import Dialog, StartMode, Window, setup_dialogs
from aiogram_dialog.test_tools import BotClient, MockMessageManager
from aiogram_dialog.test_tools.keyboard import InlineButtonTextLocator
from aiogram_dialog.widgets.kbd import Cancel, Start
from aiogram_dialog.widgets.text import Const

from dishka import FromDishka, make_async_container
from dishka.integrations.aiogram import setup_dishka
from dishka.integrations.aiogram_dialog import inject
from .conftest import AppProvider, RequestDep


class MainSG(StatesGroup):
    start = State()


class SubSG(StatesGroup):
    start = State()


async def start(message, dialog_manager):
    await dialog_manager.start(MainSG.start, mode=StartMode.RESET_STACK)


@inject
async def on_click(
    event,
    widget,
    manager,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
):
    mock(a)


@inject
async def on_start(
    data,
    manager,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
):
    mock(a)


@inject
async def on_close(
    data,
    manager,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
):
    mock(a)


@inject
async def on_process_result(
    _, __, manager,
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
):
    mock(a)


@inject
async def getter(
    a: FromDishka[RequestDep],
    mock: FromDishka[Mock],
    **kwargs,
):
    mock(a)
    return {}


dialog = Dialog(
    Window(
        Const("test"),
        Start(
            Const("test"),
            id="sub",
            state=SubSG.start,
            on_click=on_click,
        ),
        getter=getter,
        state=MainSG.start,
    ),
    on_start=on_start,
    on_close=on_close,
    on_process_result=on_process_result,
)
sub_dialog = Dialog(
    Window(
        Const("test"),
        Cancel(),
        state=SubSG.start,
    ),
)


@pytest.fixture
def message_manager() -> MockMessageManager:
    return MockMessageManager()


@pytest.fixture
def dp(message_manager):
    dp = Dispatcher()
    dp.message.register(start, CommandStart())
    dp.include_routers(dialog, sub_dialog)
    setup_dialogs(dp, message_manager=message_manager)
    setup_dishka(make_async_container(AppProvider()), dp)
    return dp


@pytest.fixture
def bot(dp):
    return BotClient(dp)


@pytest.mark.asyncio
async def test_dialog(
    bot: BotClient,
    message_manager: MockMessageManager,
):
    await bot.send("/start")
    first_message = message_manager.one_message()
    assert first_message.text == "test"
    assert first_message.reply_markup

    await bot.click(first_message, InlineButtonTextLocator("test"))
    last_message = message_manager.last_message()
    await bot.click(last_message, InlineButtonTextLocator("Cancel"))
