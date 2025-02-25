from typing import TypeVar

from dishka.exception_base import DishkaError


class UnsupportedGenericBoundsError(TypeError, DishkaError):
    def __init__(self, bounds: TypeVar) -> None:
        self.bounds = bounds

    def __str__(self) -> str:
        return f"Generic bounds are not supported: {self.bounds}"
