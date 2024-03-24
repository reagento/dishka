from sqlite3 import Connection
from typing import Annotated

from fastapi import FastAPI, APIRouter

from dishka.integrations.fastapi import FromDishka, inject

router = APIRouter()


@router.get("/")
@inject
async def index(connection: FromDishka[Connection]) -> str:
    connection.execute("select 1")
    return "Ok"


app = FastAPI()
app.include_router(router)
