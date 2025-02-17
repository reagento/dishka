from collections.abc import Callable
from typing import Any

from dishka.exceptions.base import DishkaError
from dishka.text_rendering import get_name


class IndependentDecoratorError(ValueError, DishkaError):
    def __init__(self, source: Callable[..., Any] | type) -> None:
        self.source = source

    def __str__(self) -> str:
        name = get_name(self.source, include_module=True)
        return (
            f"Decorator {name} does not depends on provided type.\n"
            f"Did you mean @provide instead of @decorate?"
        )
