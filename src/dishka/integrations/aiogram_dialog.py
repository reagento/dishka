__all__ = ["inject"]

from dishka.integrations.base import wrap_injection

TWO = 2
CONTAINER_NAME = "dishka_container"

def _container_getter(args, kwargs):
    if len(args) == 0:
        return kwargs[CONTAINER_NAME]
    elif len(args) == TWO:
        return args[-1].middleware_data[CONTAINER_NAME]
    else:
        return args[2].middleware_data[CONTAINER_NAME]


def inject(func):
    return wrap_injection(
        func=func,
        is_async=True,
        remove_depends=True,
        container_getter=_container_getter,
    )
