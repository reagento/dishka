from contextlib import contextmanager
from enum import auto
from inspect import Parameter
from typing import Annotated, get_type_hints

from dishka import Container, Provider, provide, Scope
from dishka.inject import wrap_injection, Depends
from fastapi import Request, APIRouter, FastAPI


# framework level
def inject(func):
    hints = get_type_hints(func)
    requests_param = next(
        (name for name, hint in hints.items() if hint is Request),
        None,
    )
    if requests_param:
        getter = lambda kwargs: kwargs[requests_param].state.container
        additional_params = []
    else:
        getter = lambda kwargs: kwargs["___r___"].state.container
        additional_params = [Parameter(
            name="___r___",
            annotation=Request,
            kind=Parameter.KEYWORD_ONLY,
        )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=getter,
        additional_params=additional_params,
    )


def container_middleware(container):
    async def add_request_container(request: Request, call_next):
        with container as subcontainer:
            request.state.container = subcontainer
            return await call_next(request)

    return add_request_container


# app dependency logic

class MyScope(Scope):
    APP = auto()
    REQUEST = auto()


class MyProvider(Provider):
    def __init__(self, a: int):
        self.a = a

    @provide(MyScope.APP)
    @contextmanager
    def get_int(self) -> int:
        print("solve int")
        yield self.a

    @provide(MyScope.REQUEST)
    @contextmanager
    def get_str(self, dep: int) -> str:
        print("solve str")
        yield f">{dep}<"


# app
router = APIRouter()


@router.get("/")
@inject
def index(
        *,
        value: Annotated[int, Depends()],
        value2: Annotated[str, Depends()],
) -> str:
    return f"{value} {value2}"


@router.get("/other")
@inject
def index(
        *,
        request: Request,
        value2: Annotated[str, Depends()],
) -> str:
    return f"{value2} {request!r}"


def create_app() -> FastAPI:
    container = Container(MyProvider(123456), scope=MyScope.APP)

    app = FastAPI()
    app.middleware("http")(container_middleware(container))
    app.include_router(router)
    return app


app = create_app()
