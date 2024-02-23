from typing import Any

try:
    from builtins import ExceptionGroup
except ImportError:
    from exceptiongroup import ExceptionGroup


class DishkaError(Exception):
    pass


class InvalidGraphError(DishkaError):
    pass


class ExitError(ExceptionGroup, DishkaError):
    pass


class UnsupportedFactoryError(DishkaError):
    pass


class NoFactoryError(DishkaError):
    def __init__(self, requested: Any):
        self.requested = requested
        self.path = []

    def add_path(self, requested_by: Any):
        self.path.insert(0, requested_by)

    def __str__(self):
        if self.path:
            path = self.path[-1]
            return (
                f"Cannot find factory for {self.requested} "
                f"requested by {path}. "
                f"It is missing or has invalid scope."
            )
        else:
            return (
                f"Cannot find factory for {self.requested}. "
                f"Check scopes in your providers. "
                f"It is missing or has invalid scope."
            )
