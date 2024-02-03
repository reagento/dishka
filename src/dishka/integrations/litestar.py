from inspect import Parameter
from typing import get_type_hints, Sequence, Optional

from litestar import Request, Litestar

from dishka import make_async_container, Provider
from dishka.integrations.base import wrap_injection


def inject(func):
    hints = get_type_hints(func)
    request_param = next(
        (name for name, hint in hints.items() if hint is Request),
        None,
    )
    if request_param:
        additional_params = []
    else:
        request_param = "request"
        additional_params = [Parameter(
            name=request_param,
            annotation=Optional[Request],
            kind=Parameter.KEYWORD_ONLY,
        )]

    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda _, r: r[request_param].state.dishka_container,
        additional_params=additional_params,
        is_async=True,
    )


async def make_dishka_container(request: Request):
    request_container = await request.app.state.dishka_container().__aenter__()
    request.state.dishka_container = request_container


async def startup_dishka(app: Litestar):
    container = await app.state.dishka_container_wrapper.__aenter__()
    app.state.dishka_container = container


async def shutdown_dishka(app: Litestar):
    await app.state.dishka_container_wrapper.__aexit__(None, None, None)


def setup_dishka(app: Litestar, providers: Sequence[Provider]) -> Litestar:
    app.state.dishka_container_wrapper = make_async_container(*providers)
    return app
