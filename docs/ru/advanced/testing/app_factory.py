from fastapi import FastAPI

from dishka import make_async_container
from dishka.integrations.fastapi import setup_dishka


def create_app() -> FastAPI:
    app = FastAPI()
    app.include_router(router)
    return app


def create_production_app():
    app = create_app()
    container = make_async_container(ConnectionProvider("sqlite:///"))
    setup_dishka(container, app)
    return app
