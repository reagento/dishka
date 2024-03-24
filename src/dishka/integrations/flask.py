__all__ = [
    "FromDishka",
    "inject",
    "setup_dishka",
]

from flask import Flask, Request, g, request
from flask.sansio.scaffold import Scaffold

from dishka import Container, FromDishka
from .base import is_dishka_injected, wrap_injection


def inject(func):
    return wrap_injection(
        func=func,
        remove_depends=True,
        container_getter=lambda _, p: g.dishka_container,
        additional_params=[],
        is_async=False,
    )


class ContainerMiddleware:
    def __init__(self, container):
        self.container = container

    def enter_request(self):
        g.dishka_container_wrapper = self.container({Request: request})
        g.dishka_container = g.dishka_container_wrapper.__enter__()

    def exit_request(self, *_args, **_kwargs):
        g.dishka_container.close()


def _inject_routes(scaffold: Scaffold):
    for key, func in scaffold.view_functions.items():
        if not is_dishka_injected(func):
            scaffold.view_functions[key] = inject(func)


def setup_dishka(
        container: Container,
        app: Flask,
        *,
        auto_inject: bool = False,
) -> None:
    middleware = ContainerMiddleware(container)
    app.before_request(middleware.enter_request)
    app.teardown_appcontext(middleware.exit_request)
    if auto_inject:
        _inject_routes(app)
        for blueprint in app.blueprints.values():
            _inject_routes(blueprint)
