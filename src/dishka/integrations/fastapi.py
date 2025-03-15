__all__ = [
    "DishkaRoute",
    "FastapiProvider",
    "FromDishka",
    "inject",
    "setup_dishka",
]

from collections.abc import Callable
from inspect import (
    Parameter,
    isasyncgenfunction,
    iscoroutinefunction,
    signature,
)
from typing import Annotated, Any, ParamSpec, TypeVar, get_type_hints

from fastapi import Depends, FastAPI, Request, WebSocket
from fastapi.routing import APIRoute

from dishka import (
    AsyncContainer,
    DependencyKey,
    FromDishka,
    Provider,
    Scope,
    from_context,
)
from .base import default_parse_dependency, wrap_injection
from .starlette import ContainerMiddleware

T = TypeVar("T")
P = ParamSpec("P")

def _async_depends(dependency: DependencyKey) -> Any:
    async def dishka_depends(request: Request) -> dependency:
        return await request.state.dishka_container.get(
            dependency.type_hint, component=dependency.component,
        )
    return Annotated[dependency.type_hint, Depends(dishka_depends)]


def _replace_depends(
    func: Callable[P, T],
        depends_factory: Callable[[DependencyKey],Any],
) -> Callable[P, T]:
    hints = get_type_hints(func, include_extras=True)
    func_signature = signature(func)

    new_params = []
    for name, param in func_signature.parameters.items():
        hint = hints.get(name, Any)
        dep = default_parse_dependency(param, hint)
        if dep is None:
            new_params.append(param)
            continue
        new_dep = depends_factory(dep)
        hints[name] = new_dep
        new_params.append(param.replace(annotation=new_dep))
    func.__signature__ = func_signature.replace(parameters=new_params)
    func.__annotations__ = hints
    return func


def inject(func: Callable[P, T]) -> Callable[P, T]:
    if not iscoroutinefunction(func) and not isasyncgenfunction(func):
        return _replace_depends(func, _async_depends)

    hints = get_type_hints(func)
    request_hint = next(
        (name for name, hint in hints.items() if hint is Request),
        None,
    )
    websocket_hint = next(
        (name for name, hint in hints.items() if hint is WebSocket),
        None,
    )
    if request_hint is None and websocket_hint is None:
        additional_params = [
            Parameter(
                name="___dishka_request",
                annotation=Request,
                kind=Parameter.KEYWORD_ONLY,
            ),
        ]
    else:
        additional_params = []
    param_name = request_hint or websocket_hint or "___dishka_request"
    return wrap_injection(
        func=func,
        is_async=True,
        additional_params=additional_params,
        container_getter=lambda _, p: p[param_name].state.dishka_container,
    )


class DishkaRoute(APIRoute):
    def __init__(
        self,
        path: str,
        endpoint: Callable[..., Any],
        **kwargs: Any,
    ) -> None:
        endpoint = inject(endpoint)
        super().__init__(path, endpoint, **kwargs)


class FastapiProvider(Provider):
    request = from_context(Request, scope=Scope.REQUEST)
    websocket = from_context(WebSocket, scope=Scope.SESSION)


def setup_dishka(container: AsyncContainer, app: FastAPI) -> None:
    app.add_middleware(ContainerMiddleware)
    app.state.dishka_container = container
