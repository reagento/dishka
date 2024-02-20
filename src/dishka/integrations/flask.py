__all__ = [
    "inject", "setup_dishka", "Depends",
]

from flask import Flask, Request, g, request

from dishka import Container
from .base import Depends, wrap_injection


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


def setup_dishka(container: Container, app: Flask) -> Container:
    middleware = ContainerMiddleware(container)
    app.before_request(middleware.enter_request)
    app.teardown_appcontext(middleware.exit_request)
