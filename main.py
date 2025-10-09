from fastapi import FastAPI, WebSocket
from fastapi.testclient import TestClient

from dishka.async_container import make_async_container
from dishka.entities.depends_marker import FromDishka
from dishka.entities.scope import Scope
from dishka.integrations.fastapi import inject, setup_dishka
from dishka.provider.provider import Provider

app = FastAPI()


p = Provider(scope=Scope.APP)
p.provide(lambda: 42, provides=int)
p.provide(lambda: "Hello, Dishka!", provides=str)
c = make_async_container(p)
setup_dishka(c, app)


@app.websocket("/")
@inject
async def websocket_endpoint(
    ws: FromDishka[WebSocket],
    a: FromDishka[int],
    b: FromDishka[str],
):
    await ws.accept()
    print(a)
    print(b)
    print("Здарова")


with TestClient(app=app) as client, client.websocket_connect("/") as websocket:
    print("подключаемся")
