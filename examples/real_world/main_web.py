import logging
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from myapp.ioc import AdaptersProvider, InteractorProvider
from myapp.presentation_web import router

from dishka import make_async_container
from dishka.integrations.fastapi import (
    setup_dishka,
)


def create_fastapi_app() -> FastAPI:
    app = FastAPI(lifespan=lifespan)
    app.include_router(router)
    return app


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await app.state.dishka_container.close()


def create_app():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s  %(process)-7s %(module)-20s %(message)s',
    )
    app = create_fastapi_app()
    container = make_async_container(AdaptersProvider(), InteractorProvider())
    setup_dishka(container, app)
    return app


if __name__ == "__main__":
    uvicorn.run(create_app(), host="0.0.0.0", port=8000)
