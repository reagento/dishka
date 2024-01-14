from contextlib import contextmanager
from enum import auto
from inspect import signature, Signature
from typing import Annotated, get_type_hints, get_origin, get_args, Any

from dishka import Container, Provider, provide, Scope
from fastapi import Request, APIRouter, FastAPI


# framework level

class Depends:
    def __init__(self, param: Any = None):
        self.param = param


def inject(func):
    hints = get_type_hints(func, include_extras=True)
    func_signature = signature(func)

    dependencies = {}
    for name, hint in hints.items():
        if get_origin(hint) is not Annotated:
            continue
        dep = next(
            (arg for arg in get_args(hint) if isinstance(arg, Depends)),
            None,
        )
        if not dep:
            continue
        if dep.param is None:
            dependencies[name] = get_args(hint)[0]
        else:
            dependencies[name] = dep.param

    request_name = next(
        name
        for name, hint in hints.items()
        if hint is Request
    )

    def autoinjected_func(**kwargs):
        request = kwargs[request_name]
        container = request.state.container
        solved = {
            name: container.get(dep)
            for name, dep in dependencies.items()
        }
        return func(**kwargs, **solved)

    autoinjected_func.__annotations__ = {
        name: hint
        for name, hint in hints.items()
        if name not in dependencies
    }
    autoinjected_func.__name__ = func.__name__
    autoinjected_func.__doc__ = func.__doc__
    new_params = [
        param
        for name, param in func_signature.parameters.items()
        if name not in dependencies
    ]
    autoinjected_func.__signature__ = Signature(
        parameters=new_params,
        return_annotation=func_signature.return_annotation,
    )

    return autoinjected_func


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
        request: Request,
        value: Annotated[int, Depends()],
) -> int:
    return value


def create_app() -> FastAPI:
    container = Container(MyProvider(123456), scope=MyScope.APP)

    app = FastAPI()
    app.middleware("http")(container_middleware(container))
    app.include_router(router)
    return app


app = create_app()
