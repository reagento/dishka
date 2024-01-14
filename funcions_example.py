from contextlib import contextmanager
from typing import Annotated, get_type_hints, get_origin, get_args, Any

from dishka import Container, Provider, provide


class Depends:
    def __init__(self, param: Any = None):
        self.param = param


class Request:
    def __init__(self, container: Container):
        self.container = container


def inject(func):
    hints = get_type_hints(func, include_extras=True)

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
        container = request.container
        solved = {
            name: container.get(dep)
            for name, dep in dependencies.items()
        }
        func(**kwargs, **solved)

    return autoinjected_func


class MyProvider(Provider):
    @provide
    @contextmanager
    def get_int(self) -> int:
        yield 100


@inject
def func(r: Request, b: Annotated[int, Depends()], c: int):
    print(b + c)


container = Container(MyProvider())
request = Request(container)
func(r=request, c=2)  # 102
