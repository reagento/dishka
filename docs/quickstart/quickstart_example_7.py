from fastapi import FastAPI
from dishka import make_async_container
from dishka.integrations.fastapi import FastapiProvider, FromDishka, inject, setup_dishka

app = FastAPI()
container = make_async_container(YourProvider(), FastapiProvider())
setup_dishka(container, app)


@app.get("/")
@inject
async def index(service: FromDishka[Service]) -> str:
    ...
