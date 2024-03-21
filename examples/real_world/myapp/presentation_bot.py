from typing import Annotated

from aiogram import Router
from aiogram.types import Message

from dishka.integrations.aiogram import FromDishka, inject
from .use_cases import AddProductsInteractor

router = Router()


@router.message()
@inject
async def start(
        message: Message,
        interactor: FromDishka[AddProductsInteractor],
):
    interactor(user_id=1)
    await message.answer("Products added!")
