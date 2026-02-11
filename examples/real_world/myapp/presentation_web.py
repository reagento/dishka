from dishka.integrations.fastapi import (
    FromDishka,
    inject,
)
from fastapi import APIRouter

from myapp.use_cases import AddProductsInteractor

router = APIRouter()


@router.get("/")
@inject
async def add_product(
        *,
        interactor: FromDishka[AddProductsInteractor],
) -> str:
    interactor(user_id=1)
    return "Ok"
